"""탭5: 클립보드 히스토리"""
import uuid
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal

from app.utils import now_iso

try:
    import pyperclip
    _PYPERCLIP_OK = True
except Exception:
    _PYPERCLIP_OK = False


# ── Clipboard card ────────────────────────────────────────────────────────────

class ClipboardCard(QFrame):
    copy_requested = pyqtSignal(str)
    pin_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)

    def __init__(self, item: dict, parent=None):
        super().__init__(parent)
        self._id = item["id"]
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("QFrame { border-radius: 4px; margin: 1px; }")

        col = QVBoxLayout(self)
        col.setContentsMargins(8, 6, 8, 4)
        col.setSpacing(3)

        # Text preview (2 lines)
        text = item.get("text", "")
        lines = text.split("\n")
        preview = "\n".join(lines[:2])
        if len(lines) > 2 or len(preview) > 120:
            preview = preview[:120] + "…"
        text_lbl = QLabel(preview)
        text_lbl.setWordWrap(True)
        text_lbl.setStyleSheet("font-size: 8pt;")
        col.addWidget(text_lbl)

        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(4)

        time_lbl = QLabel(item.get("copied_at", "")[:16].replace("T", " "))
        time_lbl.setStyleSheet("color: grey; font-size: 7pt;")
        btn_row.addWidget(time_lbl)
        btn_row.addStretch()

        pin_text = "📌 고정 해제" if item.get("pinned") else "📌 고정"
        pin_btn = QPushButton(pin_text)
        pin_btn.setFixedWidth(70)
        pin_btn.clicked.connect(lambda: self.pin_requested.emit(self._id))
        btn_row.addWidget(pin_btn)

        copy_btn = QPushButton("복사")
        copy_btn.setObjectName("accent")
        copy_btn.setFixedWidth(44)
        copy_btn.clicked.connect(lambda: self.copy_requested.emit(self._id))
        btn_row.addWidget(copy_btn)

        del_btn = QPushButton("−")
        del_btn.setObjectName("danger")
        del_btn.setFixedWidth(28)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self._id))
        btn_row.addWidget(del_btn)

        col.addLayout(btn_row)

        if item.get("pinned"):
            self.setStyleSheet("QFrame { border-radius: 4px; border-left: 3px solid #3b6cf5; }")


# ── Main tab ──────────────────────────────────────────────────────────────────

class ClipboardTab(QWidget):
    def __init__(self, config, clipboard_watcher, parent=None):
        super().__init__(parent)
        self._config = config
        self._watcher = clipboard_watcher
        self._cards: dict[str, ClipboardCard] = {}
        self._history: list[dict] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(4)

        # Search
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍 검색…")
        self._search.textChanged.connect(self._filter)
        root.addWidget(self._search)

        # Scroll
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._container = QWidget()
        self._list_layout = QVBoxLayout(self._container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(3)
        self._list_layout.addStretch()
        self._scroll.setWidget(self._container)
        root.addWidget(self._scroll, 1)

        clear_btn = QPushButton("전체 삭제")
        clear_btn.setObjectName("danger")
        clear_btn.clicked.connect(self._clear_all)
        root.addWidget(clear_btn)

        # Connect watcher
        if clipboard_watcher:
            clipboard_watcher.new_item.connect(self._on_new_item)

        self._load_history()

    def _load_history(self):
        self._history = self._config.load_clipboard_history()
        self._rebuild_list()

    def _rebuild_list(self, filter_text: str = ""):
        # Clear UI
        for card in list(self._cards.values()):
            self._list_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()

        # Sort: pinned first
        history = sorted(self._history, key=lambda x: (not x.get("pinned", False), x.get("copied_at", "")))
        history.reverse()  # newest first within each group

        ft = filter_text.lower()
        for item in history:
            if ft and ft not in item.get("text", "").lower():
                continue
            card = ClipboardCard(item, self._container)
            card.copy_requested.connect(self._copy_item)
            card.pin_requested.connect(self._pin_item)
            card.delete_requested.connect(self._delete_item)
            self._list_layout.insertWidget(self._list_layout.count() - 1, card)
            self._cards[item["id"]] = card

    def _filter(self, text: str):
        self._rebuild_list(text)

    def _on_new_item(self, text: str):
        settings = self._config.get_active_settings()
        limit = settings.get("clipboard_history_limit", 50)
        item = {"id": f"cb_{uuid.uuid4().hex[:8]}", "text": text, "copied_at": now_iso(), "pinned": False}
        # Remove duplicates
        self._history = [x for x in self._history if x.get("text") != text]
        self._history.insert(0, item)
        # Enforce limit (preserve pinned)
        pinned = [x for x in self._history if x.get("pinned")]
        unpinned = [x for x in self._history if not x.get("pinned")]
        unpinned = unpinned[:max(0, limit - len(pinned))]
        self._history = pinned + unpinned
        self._config.save_clipboard_history(self._history)
        self._rebuild_list(self._search.text())

    def _copy_item(self, item_id: str):
        item = next((x for x in self._history if x["id"] == item_id), None)
        if item and _PYPERCLIP_OK:
            try:
                pyperclip.copy(item["text"])
            except Exception:
                pass

    def _pin_item(self, item_id: str):
        for item in self._history:
            if item["id"] == item_id:
                item["pinned"] = not item.get("pinned", False)
                break
        self._config.save_clipboard_history(self._history)
        self._rebuild_list(self._search.text())

    def _delete_item(self, item_id: str):
        self._history = [x for x in self._history if x["id"] != item_id]
        self._config.save_clipboard_history(self._history)
        card = self._cards.pop(item_id, None)
        if card:
            self._list_layout.removeWidget(card)
            card.deleteLater()

    def _clear_all(self):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "전체 삭제", "고정되지 않은 항목을 모두 삭제하시겠습니까?")
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._history = [x for x in self._history if x.get("pinned")]
        self._config.save_clipboard_history(self._history)
        self._rebuild_list()
