"""탭6: 빠른 메모 + 일정"""
import uuid
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QTextEdit, QListWidget,
    QListWidgetItem, QDialog, QDialogButtonBox, QDateTimeEdit,
    QComboBox, QSpinBox, QTabWidget, QSlider, QSizePolicy,
    QSplitter, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer, QDateTime, pyqtSignal
from PyQt6.QtGui import QFont

from app.utils import now_iso

try:
    from plyer import notification as _notify
    _PLYER_OK = True
except Exception:
    _PLYER_OK = False


# ── Sticker window ────────────────────────────────────────────────────────────

class StickerWindow(QDialog):
    def __init__(self, parent=None, item: dict = None, config=None):
        super().__init__(parent, Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle(item.get("title", "메모") if item else "메모")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._config = config
        self._item = item or {}
        self.setMinimumSize(240, 180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        self._edit = QTextEdit()
        self._edit.setPlainText(self._item.get("content", ""))
        self._edit.setStyleSheet("background: #FFFDE7; color: #333;")
        layout.addWidget(self._edit, 1)

        footer = QHBoxLayout()
        opacity_lbl = QLabel("투명도")
        footer.addWidget(opacity_lbl)
        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(20, 100)
        self._opacity_slider.setValue(100)
        self._opacity_slider.setFixedWidth(80)
        self._opacity_slider.valueChanged.connect(lambda v: self.setWindowOpacity(v / 100))
        footer.addWidget(self._opacity_slider)
        footer.addStretch()
        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self._save)
        footer.addWidget(save_btn)
        layout.addLayout(footer)

        self.resize(260, 200)

    def _save(self):
        if self._config and self._item.get("id"):
            idx = self._config.get_active_index()
            tmpl = self._config.load_template(idx)
            for m in tmpl.get("memos", []):
                if m["id"] == self._item["id"]:
                    m["content"] = self._edit.toPlainText()
                    m["updated_at"] = now_iso()
                    break
            self._config.save_template(idx, tmpl)


# ── Memo tab ──────────────────────────────────────────────────────────────────

class MemoSubTab(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self._current_id: str | None = None

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)

        # List
        list_widget = QWidget()
        lw_layout = QVBoxLayout(list_widget)
        lw_layout.setContentsMargins(0, 0, 0, 0)
        lw_layout.setSpacing(4)

        list_top = QHBoxLayout()
        lw_layout.addLayout(list_top)
        self._memo_list = QListWidget()
        self._memo_list.currentRowChanged.connect(self._on_select)
        lw_layout.addWidget(self._memo_list)

        add_btn = QPushButton("+ 새 메모")
        add_btn.setObjectName("accent")
        add_btn.clicked.connect(self._add_memo)
        lw_layout.addWidget(add_btn)
        splitter.addWidget(list_widget)

        # Editor
        editor_widget = QWidget()
        ew_layout = QVBoxLayout(editor_widget)
        ew_layout.setContentsMargins(0, 0, 0, 0)
        ew_layout.setSpacing(4)

        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("제목")
        self._title_edit.textChanged.connect(self._auto_save)
        ew_layout.addWidget(self._title_edit)

        self._content_edit = QTextEdit()
        self._content_edit.setPlaceholderText("내용을 입력하세요…")
        self._content_edit.textChanged.connect(self._auto_save)
        ew_layout.addWidget(self._content_edit, 1)

        btn_row = QHBoxLayout()
        sticker_btn = QPushButton("📌 스티커 창으로 열기")
        sticker_btn.clicked.connect(self._open_sticker)
        btn_row.addWidget(sticker_btn)
        btn_row.addStretch()
        del_btn = QPushButton("삭제")
        del_btn.setObjectName("danger")
        del_btn.clicked.connect(self._delete_memo)
        btn_row.addWidget(del_btn)
        ew_layout.addLayout(btn_row)
        splitter.addWidget(editor_widget)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

        self.reload()

    def reload(self):
        self._memo_list.clear()
        memos = self._config.get_active_template().get("memos", [])
        for m in sorted(memos, key=lambda x: x.get("updated_at", ""), reverse=True):
            item = QListWidgetItem(f"{m['title']}  ({m.get('updated_at', '')[:10]})")
            item.setData(Qt.ItemDataRole.UserRole, m["id"])
            self._memo_list.addItem(item)
        self._clear_editor()

    def _clear_editor(self):
        self._current_id = None
        self._title_edit.blockSignals(True)
        self._content_edit.blockSignals(True)
        self._title_edit.setText("")
        self._content_edit.setPlainText("")
        self._title_edit.blockSignals(False)
        self._content_edit.blockSignals(False)

    def _on_select(self, row: int):
        if row < 0:
            return
        item = self._memo_list.item(row)
        if not item:
            return
        memo_id = item.data(Qt.ItemDataRole.UserRole)
        memos = self._config.get_active_template().get("memos", [])
        memo = next((m for m in memos if m["id"] == memo_id), None)
        if not memo:
            return
        self._current_id = memo_id
        self._title_edit.blockSignals(True)
        self._content_edit.blockSignals(True)
        self._title_edit.setText(memo.get("title", ""))
        self._content_edit.setPlainText(memo.get("content", ""))
        self._title_edit.blockSignals(False)
        self._content_edit.blockSignals(False)

    def _auto_save(self):
        if not self._current_id:
            return
        idx = self._config.get_active_index()
        tmpl = self._config.load_template(idx)
        for m in tmpl.get("memos", []):
            if m["id"] == self._current_id:
                m["title"] = self._title_edit.text()
                m["content"] = self._content_edit.toPlainText()
                m["updated_at"] = now_iso()
                break
        self._config.save_template(idx, tmpl)
        # Update list item label
        for i in range(self._memo_list.count()):
            li = self._memo_list.item(i)
            if li.data(Qt.ItemDataRole.UserRole) == self._current_id:
                li.setText(f"{self._title_edit.text()}  ({now_iso()[:10]})")
                break

    def _add_memo(self):
        memo = {"id": f"mm_{uuid.uuid4().hex[:8]}", "title": "새 메모",
                "content": "", "pinned": False, "created_at": now_iso(), "updated_at": now_iso()}
        idx = self._config.get_active_index()
        tmpl = self._config.load_template(idx)
        tmpl.setdefault("memos", []).insert(0, memo)
        self._config.save_template(idx, tmpl)
        self.reload()
        if self._memo_list.count() > 0:
            self._memo_list.setCurrentRow(0)

    def _delete_memo(self):
        if not self._current_id:
            return
        reply = QMessageBox.question(self, "삭제 확인", "이 메모를 삭제하시겠습니까?")
        if reply != QMessageBox.StandardButton.Yes:
            return
        idx = self._config.get_active_index()
        tmpl = self._config.load_template(idx)
        tmpl["memos"] = [m for m in tmpl.get("memos", []) if m["id"] != self._current_id]
        self._config.save_template(idx, tmpl)
        self.reload()

    def _open_sticker(self):
        if not self._current_id:
            return
        memos = self._config.get_active_template().get("memos", [])
        item = next((m for m in memos if m["id"] == self._current_id), None)
        if item:
            w = StickerWindow(self, item=item, config=self._config)
            w.show()


# ── Schedule sub-tab ──────────────────────────────────────────────────────────

class ScheduleSubTab(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config
        self._current_id: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        top = QHBoxLayout()
        add_btn = QPushButton("+ 새 일정")
        add_btn.setObjectName("accent")
        add_btn.clicked.connect(self._add_schedule)
        top.addWidget(add_btn)
        top.addStretch()
        layout.addLayout(top)

        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._on_select)
        layout.addWidget(self._list, 1)

        # Edit panel
        form = QFrame()
        form.setFrameShape(QFrame.Shape.StyledPanel)
        form_layout = QVBoxLayout(form)
        form_layout.setContentsMargins(8, 6, 8, 6)
        form_layout.setSpacing(4)

        form_layout.addWidget(QLabel("제목"))
        self._title = QLineEdit()
        form_layout.addWidget(self._title)

        dt_row = QHBoxLayout()
        dt_row.addWidget(QLabel("날짜/시간"))
        self._dt = QDateTimeEdit()
        self._dt.setDisplayFormat("yyyy-MM-dd HH:mm")
        self._dt.setDateTime(QDateTime.currentDateTime())
        self._dt.setCalendarPopup(True)
        dt_row.addWidget(self._dt)
        form_layout.addLayout(dt_row)

        rep_row = QHBoxLayout()
        rep_row.addWidget(QLabel("반복"))
        self._repeat = QComboBox()
        self._repeat.addItems(["없음", "매일", "매주"])
        rep_row.addWidget(self._repeat)
        form_layout.addLayout(rep_row)

        notify_row = QHBoxLayout()
        notify_row.addWidget(QLabel("알림 (분 전)"))
        self._notify_min = QSpinBox()
        self._notify_min.setRange(0, 1440)
        self._notify_min.setValue(30)
        notify_row.addWidget(self._notify_min)
        form_layout.addLayout(notify_row)

        form_layout.addWidget(QLabel("메모"))
        self._memo = QLineEdit()
        form_layout.addWidget(self._memo)

        btn_row = QHBoxLayout()
        save_btn = QPushButton("저장")
        save_btn.setObjectName("accent")
        save_btn.clicked.connect(self._save_current)
        btn_row.addWidget(save_btn)
        del_btn = QPushButton("삭제")
        del_btn.setObjectName("danger")
        del_btn.clicked.connect(self._delete_current)
        btn_row.addWidget(del_btn)
        btn_row.addStretch()
        form_layout.addLayout(btn_row)
        layout.addWidget(form)

        # Timer for notifications
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check_schedules)
        self._timer.start(60_000)  # every 1 minute

        self.reload()

    def reload(self):
        self._list.clear()
        schedules = self._config.get_active_template().get("schedules", [])
        for s in sorted(schedules, key=lambda x: x.get("datetime", "")):
            item = QListWidgetItem(f"{s['title']}  {s.get('datetime', '')[:16].replace('T', ' ')}")
            item.setData(Qt.ItemDataRole.UserRole, s["id"])
            self._list.addItem(item)

    def _on_select(self, row: int):
        if row < 0:
            return
        item = self._list.item(row)
        if not item:
            return
        sched_id = item.data(Qt.ItemDataRole.UserRole)
        schedules = self._config.get_active_template().get("schedules", [])
        s = next((x for x in schedules if x["id"] == sched_id), None)
        if not s:
            return
        self._current_id = sched_id
        self._title.setText(s.get("title", ""))
        dt_str = s.get("datetime", "")
        try:
            qdt = QDateTime.fromString(dt_str, Qt.DateFormat.ISODate)
            self._dt.setDateTime(qdt)
        except Exception:
            self._dt.setDateTime(QDateTime.currentDateTime())
        repeat_map = {"none": "없음", "daily": "매일", "weekly": "매주"}
        self._repeat.setCurrentText(repeat_map.get(s.get("repeat", "none"), "없음"))
        self._notify_min.setValue(s.get("notify_before_minutes", 30))
        self._memo.setText(s.get("memo", ""))

    def _add_schedule(self):
        sched = {
            "id": f"sc_{uuid.uuid4().hex[:8]}",
            "title": "새 일정",
            "datetime": datetime.now().isoformat(timespec="minutes"),
            "repeat": "none",
            "notify_before_minutes": 30,
            "memo": "",
        }
        idx = self._config.get_active_index()
        tmpl = self._config.load_template(idx)
        tmpl.setdefault("schedules", []).append(sched)
        self._config.save_template(idx, tmpl)
        self.reload()

    def _save_current(self):
        if not self._current_id:
            return
        repeat_map = {"없음": "none", "매일": "daily", "매주": "weekly"}
        idx = self._config.get_active_index()
        tmpl = self._config.load_template(idx)
        for s in tmpl.get("schedules", []):
            if s["id"] == self._current_id:
                s["title"] = self._title.text().strip() or "새 일정"
                s["datetime"] = self._dt.dateTime().toString(Qt.DateFormat.ISODate)
                s["repeat"] = repeat_map.get(self._repeat.currentText(), "none")
                s["notify_before_minutes"] = self._notify_min.value()
                s["memo"] = self._memo.text()
                break
        self._config.save_template(idx, tmpl)
        self.reload()

    def _delete_current(self):
        if not self._current_id:
            return
        reply = QMessageBox.question(self, "삭제 확인", "이 일정을 삭제하시겠습니까?")
        if reply != QMessageBox.StandardButton.Yes:
            return
        idx = self._config.get_active_index()
        tmpl = self._config.load_template(idx)
        tmpl["schedules"] = [s for s in tmpl.get("schedules", []) if s["id"] != self._current_id]
        self._config.save_template(idx, tmpl)
        self._current_id = None
        self.reload()

    def _check_schedules(self):
        now = datetime.now()
        schedules = self._config.get_active_template().get("schedules", [])
        for s in schedules:
            try:
                dt = datetime.fromisoformat(s.get("datetime", ""))
                diff = (dt - now).total_seconds() / 60
                notify_before = s.get("notify_before_minutes", 30)
                if 0 <= diff <= 1 or (notify_before > 0 and abs(diff - notify_before) <= 1):
                    msg = f"{s['title']} — {dt.strftime('%m/%d %H:%M')}"
                    if _PLYER_OK:
                        try:
                            _notify.notify(title="업무보조 — 일정 알림", message=msg, timeout=10)
                        except Exception:
                            pass
                    QMessageBox.information(None, "📅 일정 알림", msg)
            except Exception:
                pass


# ── Outer tab ─────────────────────────────────────────────────────────────────

class MemoTab(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(0)

        tabs = QTabWidget()
        self._memo_sub = MemoSubTab(config)
        self._sched_sub = ScheduleSubTab(config)
        tabs.addTab(self._memo_sub, "📝 메모")
        tabs.addTab(self._sched_sub, "📅 일정")
        layout.addWidget(tabs)

    def reload(self):
        self._memo_sub.reload()
        self._sched_sub.reload()
