"""탭4: 매크로 녹화/재생"""
import uuid
import time
import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QDialog, QDialogButtonBox, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QDoubleSpinBox, QSpinBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer

from app.utils import hotkey_to_str
from ui.widgets import HotkeyDialog, hotkey_button_text

try:
    from pynput import mouse as _pm, keyboard as _pk
    _PYNPUT_OK = True
except Exception:
    _PYNPUT_OK = False

try:
    import pyautogui as _pag
    _PAG_OK = True
except Exception:
    _PAG_OK = False


# ── Recorder thread ───────────────────────────────────────────────────────────

class RecorderThread(QThread):
    event_recorded = pyqtSignal(dict)
    stopped = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._events = []
        self._start_time = 0.0
        self._running = False
        self._mouse_listener = None
        self._keyboard_listener = None

    def run(self):
        if not _PYNPUT_OK:
            self.stopped.emit([])
            return
        self._events = []
        self._start_time = time.time()
        self._running = True

        def _elapsed():
            return round(time.time() - self._start_time, 3)

        def on_click(x, y, button, pressed):
            if not self._running:
                return False
            if pressed:
                ev = {"type": "click", "x": x, "y": y, "delay": _elapsed()}
                self._events.append(ev)
                self.event_recorded.emit(ev)

        def on_key_press(key):
            if not self._running:
                return False
            try:
                k = key.char or str(key)
            except AttributeError:
                k = str(key)
            ev = {"type": "key_press", "key": k, "delay": _elapsed()}
            self._events.append(ev)
            self.event_recorded.emit(ev)

        self._mouse_listener = _pm.Listener(on_click=on_click)
        self._keyboard_listener = _pk.Listener(on_press=on_key_press)
        self._mouse_listener.start()
        self._keyboard_listener.start()
        self._mouse_listener.join()

    def stop_recording(self):
        self._running = False
        if self._mouse_listener:
            self._mouse_listener.stop()
        if self._keyboard_listener:
            self._keyboard_listener.stop()
        self.stopped.emit(self._events)


# ── Player thread ──────────────────────────────────────────────────────────────

class PlayerThread(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, actions: list, loops: int = 1, speed: float = 1.0, parent=None):
        super().__init__(parent)
        self._actions = actions
        self._loops = loops
        self._speed = speed if speed > 0 else 1.0

    def run(self):
        if not _PAG_OK:
            self.error.emit("pyautogui 라이브러리가 없습니다.")
            return
        try:
            for _ in range(self._loops):
                for action in self._actions:
                    delay = action.get("delay", 0) / self._speed
                    if delay > 0:
                        time.sleep(delay)
                    atype = action.get("type")
                    if atype == "click":
                        _pag.click(action["x"], action["y"])
                    elif atype == "hotkey":
                        _pag.hotkey(*action.get("keys", []))
                    elif atype in ("type", "text"):
                        _pag.typewrite(action.get("text", ""), interval=0.05 / self._speed)
                    elif atype == "key_press":
                        key = action.get("key", "")
                        if key:
                            try:
                                _pag.press(key)
                            except Exception:
                                pass
        except Exception as e:
            self.error.emit(str(e))
        self.finished.emit()


# ── Edit dialog ───────────────────────────────────────────────────────────────

class MacroEditDialog(QDialog):
    def __init__(self, parent=None, item: dict = None, hotkey_manager=None):
        super().__init__(parent)
        self.setWindowTitle("매크로 편집")
        self.setMinimumWidth(460)
        self.setMinimumHeight(360)
        self.setModal(True)
        self._hkm = hotkey_manager
        self._hotkey: dict | None = item.get("hotkey") if item else None
        self._actions = list(item.get("actions", []) if item else [])

        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        top = QHBoxLayout()
        top.addWidget(QLabel("이름"))
        self._name = QLineEdit(item.get("name", "") if item else "")
        top.addWidget(self._name, 1)
        top.addWidget(QLabel("단축키"))
        self._hk_btn = QPushButton(hotkey_button_text(self._hotkey))
        self._hk_btn.clicked.connect(self._capture)
        top.addWidget(self._hk_btn)
        layout.addLayout(top)

        params = QHBoxLayout()
        params.addWidget(QLabel("반복"))
        self._loops = QSpinBox()
        self._loops.setRange(1, 999)
        self._loops.setValue(item.get("loops", 1) if item else 1)
        params.addWidget(self._loops)
        params.addWidget(QLabel("속도"))
        self._speed = QDoubleSpinBox()
        self._speed.setRange(0.1, 10.0)
        self._speed.setSingleStep(0.25)
        self._speed.setValue(item.get("speed", 1.0) if item else 1.0)
        params.addWidget(self._speed)
        params.addStretch()
        layout.addLayout(params)

        layout.addWidget(QLabel("액션 목록 (delay 더블클릭으로 편집)"))
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["타입", "파라미터", "delay(초)", ""])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._table, 1)

        tbl_btns = QHBoxLayout()
        del_row_btn = QPushButton("선택 행 삭제")
        del_row_btn.clicked.connect(self._delete_selected_row)
        tbl_btns.addWidget(del_row_btn)
        tbl_btns.addStretch()
        layout.addLayout(tbl_btns)

        self._populate_table()

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _populate_table(self):
        self._table.setRowCount(0)
        for action in self._actions:
            self._append_row(action)

    def _append_row(self, action: dict):
        r = self._table.rowCount()
        self._table.insertRow(r)
        atype = action.get("type", "")
        params = ""
        if atype == "click":
            params = f"({action.get('x', 0)}, {action.get('y', 0)})"
        elif atype in ("type", "text"):
            params = action.get("text", "")
        elif atype == "hotkey":
            params = "+".join(action.get("keys", []))
        elif atype == "key_press":
            params = action.get("key", "")
        self._table.setItem(r, 0, QTableWidgetItem(atype))
        self._table.setItem(r, 1, QTableWidgetItem(params))
        delay_item = QTableWidgetItem(str(action.get("delay", 0)))
        self._table.setItem(r, 2, delay_item)

    def _delete_selected_row(self):
        rows = sorted({i.row() for i in self._table.selectedItems()}, reverse=True)
        for row in rows:
            self._table.removeRow(row)

    def _capture(self):
        dlg = HotkeyDialog(self, self._hotkey, self._hkm)
        if dlg.exec():
            self._hotkey = dlg.result_hotkey
            self._hk_btn.setText(hotkey_button_text(self._hotkey))

    def get_data(self) -> dict:
        # Rebuild actions from table
        actions = []
        for r in range(self._table.rowCount()):
            atype_item = self._table.item(r, 0)
            params_item = self._table.item(r, 1)
            delay_item = self._table.item(r, 2)
            if not atype_item:
                continue
            atype = atype_item.text()
            params = params_item.text() if params_item else ""
            try:
                delay = float(delay_item.text()) if delay_item else 0.0
            except ValueError:
                delay = 0.0
            action: dict = {"type": atype, "delay": delay}
            if atype == "click":
                try:
                    coords = params.strip("()").split(",")
                    action["x"] = int(coords[0])
                    action["y"] = int(coords[1])
                except Exception:
                    action["x"] = 0
                    action["y"] = 0
            elif atype in ("type", "text"):
                action["text"] = params
            elif atype == "hotkey":
                action["keys"] = [k.strip() for k in params.split("+") if k.strip()]
            elif atype == "key_press":
                action["key"] = params
            actions.append(action)
        return {
            "name": self._name.text().strip() or "새 매크로",
            "hotkey": self._hotkey,
            "loops": self._loops.value(),
            "speed": self._speed.value(),
            "actions": actions,
        }


# ── Macro row ─────────────────────────────────────────────────────────────────

class MacroRow(QFrame):
    edit_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    play_requested = pyqtSignal(str)
    rec_requested = pyqtSignal(str)

    def __init__(self, item: dict, parent=None):
        super().__init__(parent)
        self._id = item["id"]
        self.setFrameShape(QFrame.Shape.StyledPanel)

        row = QHBoxLayout(self)
        row.setContentsMargins(8, 6, 8, 6)
        row.setSpacing(6)

        icon = QLabel("●")
        icon.setFixedWidth(16)
        icon.setStyleSheet("color: #e25c6c;")
        row.addWidget(icon)

        hk_lbl = QLabel(hotkey_to_str(item.get("hotkey")))
        hk_lbl.setFixedWidth(90)
        hk_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hk_lbl.setStyleSheet(
            "background: rgba(128,128,128,0.12); border-radius: 3px; "
            "padding: 2px 4px; font-size: 8pt; font-family: Consolas, monospace;"
        )
        row.addWidget(hk_lbl)

        info = QVBoxLayout()
        info.setSpacing(1)
        name_lbl = QLabel(item.get("name", ""))
        name_lbl.setStyleSheet("font-weight: bold;")
        info.addWidget(name_lbl)
        n_actions = len(item.get("actions", []))
        detail = f"{n_actions}개 액션  ·  {item.get('loops', 1)}회  ·  {item.get('speed', 1.0)}x"
        detail_lbl = QLabel(detail)
        detail_lbl.setStyleSheet("color: grey; font-size: 8pt;")
        info.addWidget(detail_lbl)
        row.addLayout(info, 1)

        rec_btn = QPushButton("● REC")
        rec_btn.setFixedWidth(60)
        rec_btn.setStyleSheet("color: #e25c6c;")
        rec_btn.clicked.connect(lambda: self.rec_requested.emit(self._id))
        row.addWidget(rec_btn)

        play_btn = QPushButton("▶ 재생")
        play_btn.setObjectName("accent")
        play_btn.setFixedWidth(56)
        play_btn.clicked.connect(lambda: self.play_requested.emit(self._id))
        row.addWidget(play_btn)

        edit_btn = QPushButton("편집")
        edit_btn.setFixedWidth(40)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self._id))
        row.addWidget(edit_btn)

        del_btn = QPushButton("−")
        del_btn.setObjectName("danger")
        del_btn.setFixedWidth(28)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self._id))
        row.addWidget(del_btn)


# ── Main tab ──────────────────────────────────────────────────────────────────

class MacroTab(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, config, hotkey_manager, parent=None):
        super().__init__(parent)
        self._config = config
        self._hkm = hotkey_manager
        self._rows: dict[str, MacroRow] = {}
        self._recorder: RecorderThread | None = None
        self._player: PlayerThread | None = None
        self._recording_id: str | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(4)

        # Recorder panel
        rec_frame = QFrame()
        rec_frame.setFrameShape(QFrame.Shape.StyledPanel)
        rec_layout = QHBoxLayout(rec_frame)
        rec_layout.setContentsMargins(8, 6, 8, 6)

        self._rec_btn = QPushButton("● 녹화 시작")
        self._rec_btn.setStyleSheet("color: #e25c6c; font-weight: bold;")
        self._rec_btn.setFixedWidth(100)
        self._rec_btn.clicked.connect(self._toggle_record_global)
        rec_layout.addWidget(self._rec_btn)

        self._rec_status = QLabel("대기 중")
        rec_layout.addWidget(self._rec_status, 1)

        self._event_count = QLabel("0개 이벤트")
        rec_layout.addWidget(self._event_count)
        root.addWidget(rec_frame)

        # List
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

        add_btn = QPushButton("+ 추가")
        add_btn.setObjectName("accent")
        add_btn.clicked.connect(self._add_item)
        root.addWidget(add_btn)

        self._event_total = 0
        self.reload()

    def reload(self):
        self._clear_list()
        for item in self._config.get_active_template().get("macros", []):
            self._add_row(item)

    def _clear_list(self):
        for row in list(self._rows.values()):
            self._list_layout.removeWidget(row)
            row.deleteLater()
        self._rows.clear()

    def _add_row(self, item: dict):
        row = MacroRow(item, self._container)
        row.play_requested.connect(self._play_item)
        row.rec_requested.connect(self._record_for_item)
        row.edit_requested.connect(self._edit_item)
        row.delete_requested.connect(self._delete_item)
        self._list_layout.insertWidget(self._list_layout.count() - 1, row)
        self._rows[item["id"]] = row

    def _get_items(self) -> list:
        return self._config.get_active_template().get("macros", [])

    def _save_items(self, items: list):
        idx = self._config.get_active_index()
        tmpl = self._config.load_template(idx)
        tmpl["macros"] = items
        self._config.save_template(idx, tmpl)
        self.data_changed.emit()

    # ── Recording ────────────────────────────────────────────────────────────

    def _toggle_record_global(self):
        if self._recorder and self._recorder.isRunning():
            self._stop_recording()
        else:
            # Create a new macro item
            item_id = f"mc_{uuid.uuid4().hex[:8]}"
            new_item = {"id": item_id, "name": "새 매크로", "hotkey": None,
                        "loops": 1, "speed": 1.0, "actions": []}
            items = self._get_items()
            items.append(new_item)
            self._save_items(items)
            self._add_row(new_item)
            self._start_recording(item_id)

    def _record_for_item(self, item_id: str):
        if self._recorder and self._recorder.isRunning():
            self._stop_recording()
        else:
            self._start_recording(item_id)

    def _start_recording(self, item_id: str):
        self._recording_id = item_id
        self._event_total = 0
        self._rec_btn.setText("■ 녹화 중지")
        self._rec_status.setText("녹화 중…")
        if not _PYNPUT_OK:
            self._rec_status.setText("pynput 없음 — 시뮬레이션 모드")
            return
        self._recorder = RecorderThread(self)
        self._recorder.event_recorded.connect(self._on_event)
        self._recorder.stopped.connect(self._on_recording_done)
        self._recorder.start()

    def _stop_recording(self):
        if self._recorder and self._recorder.isRunning():
            self._recorder.stop_recording()
        else:
            self._on_recording_done([])

    def _on_event(self, ev: dict):
        self._event_total += 1
        self._event_count.setText(f"{self._event_total}개 이벤트")

    def _on_recording_done(self, events: list):
        self._rec_btn.setText("● 녹화 시작")
        self._rec_status.setText(f"완료 · {len(events)}개 이벤트")
        item_id = self._recording_id
        self._recording_id = None
        if item_id:
            items = self._get_items()
            for item in items:
                if item["id"] == item_id:
                    item["actions"] = events
                    break
            self._save_items(items)
            # Refresh row
            old = self._rows.get(item_id)
            if old:
                item = next((x for x in items if x["id"] == item_id), None)
                if item:
                    pos = self._list_layout.indexOf(old)
                    self._list_layout.removeWidget(old)
                    old.deleteLater()
                    new_row = MacroRow(item, self._container)
                    new_row.play_requested.connect(self._play_item)
                    new_row.rec_requested.connect(self._record_for_item)
                    new_row.edit_requested.connect(self._edit_item)
                    new_row.delete_requested.connect(self._delete_item)
                    self._list_layout.insertWidget(pos, new_row)
                    self._rows[item_id] = new_row

    # ── Playback ─────────────────────────────────────────────────────────────

    def _play_item(self, item_id: str):
        items = self._get_items()
        item = next((x for x in items if x["id"] == item_id), None)
        if not item:
            return
        if self._player and self._player.isRunning():
            QMessageBox.information(self, "재생 중", "이미 재생 중입니다.")
            return
        self._player = PlayerThread(
            item.get("actions", []),
            item.get("loops", 1),
            item.get("speed", 1.0),
            self
        )
        self._player.finished.connect(lambda: self._rec_status.setText("재생 완료"))
        self._player.error.connect(lambda e: QMessageBox.warning(self, "오류", e))
        self._rec_status.setText(f"재생 중: {item['name']}")
        self._player.start()

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def _add_item(self):
        dlg = MacroEditDialog(self, hotkey_manager=self._hkm)
        if dlg.exec():
            d = dlg.get_data()
            d["id"] = f"mc_{uuid.uuid4().hex[:8]}"
            items = self._get_items()
            items.append(d)
            self._save_items(items)
            self._add_row(d)

    def _edit_item(self, item_id: str):
        items = self._get_items()
        item = next((x for x in items if x["id"] == item_id), None)
        if not item:
            return
        dlg = MacroEditDialog(self, item=item, hotkey_manager=self._hkm)
        if dlg.exec():
            d = dlg.get_data()
            d["id"] = item_id
            for i, x in enumerate(items):
                if x["id"] == item_id:
                    items[i] = d
                    break
            self._save_items(items)
            old = self._rows.get(item_id)
            if old:
                pos = self._list_layout.indexOf(old)
                self._list_layout.removeWidget(old)
                old.deleteLater()
                new_row = MacroRow(d, self._container)
                new_row.play_requested.connect(self._play_item)
                new_row.rec_requested.connect(self._record_for_item)
                new_row.edit_requested.connect(self._edit_item)
                new_row.delete_requested.connect(self._delete_item)
                self._list_layout.insertWidget(pos, new_row)
                self._rows[item_id] = new_row

    def _delete_item(self, item_id: str):
        reply = QMessageBox.question(self, "삭제 확인", "이 매크로를 삭제하시겠습니까?")
        if reply != QMessageBox.StandardButton.Yes:
            return
        items = self._get_items()
        item = next((x for x in items if x["id"] == item_id), None)
        if item and item.get("hotkey"):
            hk = item["hotkey"]
            self._hkm.unregister(hk.get("modifiers", []), hk.get("key", ""))
        self._save_items([x for x in items if x["id"] != item_id])
        row = self._rows.pop(item_id, None)
        if row:
            self._list_layout.removeWidget(row)
            row.deleteLater()
