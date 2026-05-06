"""탭1: 상용구 · 스니펫"""
import uuid
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QLineEdit, QTextEdit, QComboBox, QFrame,
    QDialog, QDialogButtonBox, QMessageBox, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal

from app.utils import hotkey_to_str
from ui.widgets import HotkeyDialog, hotkey_button_text

try:
    import pyperclip
    import keyboard as _kb
    _COPY_PASTE_OK = True
except Exception:
    _COPY_PASTE_OK = False


def _copy_and_paste(text: str):
    try:
        pyperclip.copy(text)
        _kb.press_and_release("ctrl+v")
    except Exception:
        try:
            pyperclip.copy(text)
        except Exception:
            pass


# ── Item edit dialog ─────────────────────────────────────────────────────────

class PhraseEditDialog(QDialog):
    def __init__(self, parent=None, item: dict = None, item_type: str = "text", hotkey_manager=None):
        super().__init__(parent)
        self.setWindowTitle("상용구 편집" if item_type == "text" else "스니펫 편집")
        self.setMinimumWidth(340)
        self.setModal(True)
        self._hotkey_manager = hotkey_manager
        self._item_type = item_type

        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        # Name
        layout.addWidget(QLabel("이름"))
        self._name_edit = QLineEdit(item.get("name", "") if item else "")
        layout.addWidget(self._name_edit)

        # Language (code only)
        if item_type == "code":
            layout.addWidget(QLabel("언어"))
            self._lang_combo = QComboBox()
            self._lang_combo.addItems(["sql", "python", "기타"])
            lang = item.get("language", "sql") if item else "sql"
            self._lang_combo.setCurrentText(lang)
            layout.addWidget(self._lang_combo)

        # Content
        layout.addWidget(QLabel("내용"))
        self._text_edit = QTextEdit()
        self._text_edit.setPlainText(item.get("text", "") if item else "")
        if item_type == "code":
            self._text_edit.setFont(self._text_edit.font())
            self._text_edit.setStyleSheet("font-family: Consolas, 'Courier New', monospace;")
        self._text_edit.setMinimumHeight(80)
        layout.addWidget(self._text_edit)

        # Hotkey
        hk_layout = QHBoxLayout()
        hk_layout.addWidget(QLabel("단축키"))
        self._hotkey: dict | None = item.get("hotkey") if item else None
        self._hk_btn = QPushButton(hotkey_button_text(self._hotkey))
        self._hk_btn.clicked.connect(self._capture_hotkey)
        hk_layout.addWidget(self._hk_btn)
        layout.addLayout(hk_layout)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _capture_hotkey(self):
        dlg = HotkeyDialog(self, self._hotkey, self._hotkey_manager)
        if dlg.exec():
            self._hotkey = dlg.result_hotkey
            self._hk_btn.setText(hotkey_button_text(self._hotkey))

    def get_data(self) -> dict:
        data = {
            "name": self._name_edit.text().strip() or "새 항목",
            "text": self._text_edit.toPlainText(),
            "hotkey": self._hotkey,
            "type": self._item_type,
        }
        if self._item_type == "code":
            data["language"] = self._lang_combo.currentText()
        return data


# ── Phrase / Snippet row ─────────────────────────────────────────────────────

class PhraseRow(QFrame):
    edit_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    copy_requested = pyqtSignal(str)

    def __init__(self, item: dict, parent=None):
        super().__init__(parent)
        self._id = item["id"]
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("QFrame { border-radius: 4px; }")

        row = QHBoxLayout(self)
        row.setContentsMargins(8, 6, 8, 6)
        row.setSpacing(6)

        # Hotkey badge
        hk_label = QLabel(hotkey_to_str(item.get("hotkey")))
        hk_label.setFixedWidth(90)
        hk_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hk_label.setStyleSheet(
            "background: rgba(128,128,128,0.12); border-radius: 3px; "
            "padding: 2px 4px; font-size: 8pt; font-family: Consolas, monospace;"
        )
        row.addWidget(hk_label)

        # Name + preview
        info = QVBoxLayout()
        info.setSpacing(1)
        name_lbl = QLabel(item.get("name", ""))
        name_lbl.setStyleSheet("font-weight: bold;")
        info.addWidget(name_lbl)
        preview = item.get("text", "").replace("\n", " ")[:50]
        prev_lbl = QLabel(preview or "(내용 없음)")
        prev_lbl.setStyleSheet("color: grey; font-size: 8pt;")
        info.addWidget(prev_lbl)
        row.addLayout(info, 1)

        # Type badge for snippets
        if item.get("type") == "code":
            lang = item.get("language", "code").upper()
            lang_lbl = QLabel(lang)
            lang_lbl.setStyleSheet(
                "background: rgba(59,108,245,0.15); color: #3b6cf5; "
                "border-radius: 3px; padding: 1px 5px; font-size: 7pt; font-weight: bold;"
            )
            row.addWidget(lang_lbl)

        # Buttons
        copy_btn = QPushButton("복사")
        copy_btn.setFixedWidth(40)
        copy_btn.clicked.connect(lambda: self.copy_requested.emit(self._id))
        row.addWidget(copy_btn)

        edit_btn = QPushButton("편집")
        edit_btn.setFixedWidth(40)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self._id))
        row.addWidget(edit_btn)

        del_btn = QPushButton("−")
        del_btn.setObjectName("danger")
        del_btn.setFixedWidth(28)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self._id))
        row.addWidget(del_btn)


# ── Main tab widget ──────────────────────────────────────────────────────────

class PhraseTab(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, config, hotkey_manager, parent=None):
        super().__init__(parent)
        self._config = config
        self._hkm = hotkey_manager
        self._mode = "text"  # "text" or "code"
        self._rows: dict[str, PhraseRow] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(4)

        # Toggle
        toggle_row = QHBoxLayout()
        self._text_btn = QPushButton("일반 텍스트")
        self._text_btn.setCheckable(True)
        self._text_btn.setChecked(True)
        self._text_btn.clicked.connect(lambda: self._set_mode("text"))
        self._code_btn = QPushButton("코드 스니펫")
        self._code_btn.setCheckable(True)
        self._code_btn.clicked.connect(lambda: self._set_mode("code"))
        toggle_row.addWidget(self._text_btn)
        toggle_row.addWidget(self._code_btn)
        root.addLayout(toggle_row)

        # Scroll area
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

        # Add button
        add_btn = QPushButton("+ 추가")
        add_btn.setObjectName("accent")
        add_btn.clicked.connect(self._add_item)
        root.addWidget(add_btn)

        self.reload()

    def reload(self):
        self._clear_list()
        tmpl = self._config.get_active_template()
        key = "snippets" if self._mode == "code" else "phrases"
        for item in tmpl.get(key, []):
            self._add_row(item)
        self._register_hotkeys()

    def _set_mode(self, mode: str):
        self._mode = mode
        self._text_btn.setChecked(mode == "text")
        self._code_btn.setChecked(mode == "code")
        self.reload()

    def _clear_list(self):
        for row in list(self._rows.values()):
            self._list_layout.removeWidget(row)
            row.deleteLater()
        self._rows.clear()

    def _add_row(self, item: dict):
        row = PhraseRow(item, self._container)
        row.copy_requested.connect(self._copy_item)
        row.edit_requested.connect(self._edit_item)
        row.delete_requested.connect(self._delete_item)
        # Insert before stretch
        self._list_layout.insertWidget(self._list_layout.count() - 1, row)
        self._rows[item["id"]] = row

    def _register_hotkeys(self):
        tmpl = self._config.get_active_template()
        idx = self._config.get_active_index()

        def make_copy_cb(text, name):
            def cb():
                _copy_and_paste(text)
            return cb

        for section in ("phrases", "snippets"):
            for item in tmpl.get(section, []):
                hk = item.get("hotkey")
                if not hk:
                    continue
                cb = make_copy_cb(item.get("text", ""), item.get("name", ""))
                self._hkm.register(hk.get("modifiers", []), hk.get("key", ""), cb, item["id"])

    def _get_items(self) -> list:
        tmpl = self._config.get_active_template()
        key = "snippets" if self._mode == "code" else "phrases"
        return tmpl.get(key, [])

    def _save_items(self, items: list):
        idx = self._config.get_active_index()
        tmpl = self._config.load_template(idx)
        key = "snippets" if self._mode == "code" else "phrases"
        tmpl[key] = items
        self._config.save_template(idx, tmpl)
        self.data_changed.emit()

    def _add_item(self):
        dlg = PhraseEditDialog(self, item_type=self._mode, hotkey_manager=self._hkm)
        if dlg.exec():
            d = dlg.get_data()
            d["id"] = f"ph_{uuid.uuid4().hex[:8]}" if self._mode == "text" else f"sn_{uuid.uuid4().hex[:8]}"
            items = self._get_items()
            items.append(d)
            self._save_items(items)
            self._add_row(d)
            # Register hotkey
            if d.get("hotkey"):
                hk = d["hotkey"]
                self._hkm.register(hk.get("modifiers", []), hk.get("key", ""),
                                    lambda t=d["text"]: _copy_and_paste(t), d["id"])

    def _edit_item(self, item_id: str):
        items = self._get_items()
        item = next((x for x in items if x["id"] == item_id), None)
        if not item:
            return
        old_hk = item.get("hotkey")
        dlg = PhraseEditDialog(self, item=item, item_type=self._mode, hotkey_manager=self._hkm)
        if dlg.exec():
            d = dlg.get_data()
            d["id"] = item_id
            # Update hotkey registration
            if old_hk:
                self._hkm.unregister(old_hk.get("modifiers", []), old_hk.get("key", ""))
            if d.get("hotkey"):
                hk = d["hotkey"]
                if self._hkm.is_conflict(hk.get("modifiers", []), hk.get("key", ""), exclude_id=item_id):
                    QMessageBox.warning(self, "충돌", "이미 등록된 단축키입니다.")
                    d["hotkey"] = old_hk
                else:
                    self._hkm.register(hk.get("modifiers", []), hk.get("key", ""),
                                        lambda t=d["text"]: _copy_and_paste(t), item_id)
            for i, x in enumerate(items):
                if x["id"] == item_id:
                    items[i] = d
                    break
            self._save_items(items)
            # Refresh row
            old_row = self._rows.get(item_id)
            if old_row:
                pos = self._list_layout.indexOf(old_row)
                self._list_layout.removeWidget(old_row)
                old_row.deleteLater()
                new_row = PhraseRow(d, self._container)
                new_row.copy_requested.connect(self._copy_item)
                new_row.edit_requested.connect(self._edit_item)
                new_row.delete_requested.connect(self._delete_item)
                self._list_layout.insertWidget(pos, new_row)
                self._rows[item_id] = new_row

    def _delete_item(self, item_id: str):
        reply = QMessageBox.question(self, "삭제 확인", "이 항목을 삭제하시겠습니까?")
        if reply != QMessageBox.StandardButton.Yes:
            return
        items = self._get_items()
        item = next((x for x in items if x["id"] == item_id), None)
        if item and item.get("hotkey"):
            hk = item["hotkey"]
            self._hkm.unregister(hk.get("modifiers", []), hk.get("key", ""))
        items = [x for x in items if x["id"] != item_id]
        self._save_items(items)
        row = self._rows.pop(item_id, None)
        if row:
            self._list_layout.removeWidget(row)
            row.deleteLater()

    def _copy_item(self, item_id: str):
        items = self._get_items()
        item = next((x for x in items if x["id"] == item_id), None)
        if item:
            _copy_and_paste(item.get("text", ""))
