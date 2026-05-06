"""탭2: 사이트 · 파일/폴더 바로가기"""
import os
import uuid
import webbrowser
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QLineEdit, QFrame, QDialog, QDialogButtonBox,
    QFileDialog, QMessageBox, QTabBar,
)
from PyQt6.QtCore import Qt, pyqtSignal

from app.utils import hotkey_to_str
from ui.widgets import HotkeyDialog, hotkey_button_text

try:
    import pyperclip
    _PYPERCLIP_OK = True
except Exception:
    _PYPERCLIP_OK = False


def _open_site(item: dict):
    url = item.get("url", "")
    if not url:
        return
    username = item.get("username", "")
    password = item.get("password", "")
    if username or password:
        text = f"{username}\t{password}" if username and password else (username or password)
        try:
            pyperclip.copy(text)
        except Exception:
            pass
    browser = item.get("browser_path", "").strip()
    if browser and os.path.isfile(browser):
        subprocess.Popen([browser, url])
    else:
        webbrowser.open(url)


def _open_file(item: dict):
    path = item.get("path", "").strip()
    if not path or not os.path.exists(path):
        QMessageBox.warning(None, "오류", f"경로를 찾을 수 없습니다:\n{path}")
        return
    if os.path.isdir(path):
        subprocess.Popen(["explorer", path])
    else:
        os.startfile(path)


# ── Edit dialogs ──────────────────────────────────────────────────────────────

class SiteEditDialog(QDialog):
    def __init__(self, parent=None, item: dict = None, hotkey_manager=None):
        super().__init__(parent)
        self.setWindowTitle("사이트 편집")
        self.setMinimumWidth(340)
        self.setModal(True)
        self._hkm = hotkey_manager
        self._hotkey: dict | None = item.get("hotkey") if item else None

        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        def _row(label: str, widget):
            layout.addWidget(QLabel(label))
            layout.addWidget(widget)
            return widget

        self._name = _row("이름", QLineEdit(item.get("name", "") if item else ""))
        self._desc = _row("설명", QLineEdit(item.get("description", "") if item else ""))
        self._url  = _row("URL", QLineEdit(item.get("url", "") if item else ""))
        self._url.setPlaceholderText("https://...")
        self._user = _row("계정 (아이디)", QLineEdit(item.get("username", "") if item else ""))
        self._pwd  = _row("비밀번호 (로컬 저장)", QLineEdit(item.get("password", "") if item else ""))
        self._pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self._browser = _row("브라우저 경로 (비워두면 기본 브라우저)", QLineEdit(item.get("browser_path", "") if item else ""))

        browse_btn = QPushButton("탐색…")
        browse_btn.clicked.connect(self._browse_browser)
        layout.addWidget(browse_btn)

        hk_row = QHBoxLayout()
        hk_row.addWidget(QLabel("단축키"))
        self._hk_btn = QPushButton(hotkey_button_text(self._hotkey))
        self._hk_btn.clicked.connect(self._capture)
        hk_row.addWidget(self._hk_btn)
        layout.addLayout(hk_row)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _browse_browser(self):
        path, _ = QFileDialog.getOpenFileName(self, "브라우저 선택", "", "실행 파일 (*.exe)")
        if path:
            self._browser.setText(path)

    def _capture(self):
        dlg = HotkeyDialog(self, self._hotkey, self._hkm)
        if dlg.exec():
            self._hotkey = dlg.result_hotkey
            self._hk_btn.setText(hotkey_button_text(self._hotkey))

    def get_data(self) -> dict:
        return {
            "name": self._name.text().strip() or "새 사이트",
            "description": self._desc.text().strip(),
            "type": "site",
            "url": self._url.text().strip(),
            "username": self._user.text().strip(),
            "password": self._pwd.text(),
            "browser_path": self._browser.text().strip(),
            "hotkey": self._hotkey,
        }


class FileEditDialog(QDialog):
    def __init__(self, parent=None, item: dict = None, hotkey_manager=None):
        super().__init__(parent)
        self.setWindowTitle("파일/폴더 편집")
        self.setMinimumWidth(340)
        self.setModal(True)
        self._hkm = hotkey_manager
        self._hotkey: dict | None = item.get("hotkey") if item else None

        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        layout.addWidget(QLabel("이름"))
        self._name = QLineEdit(item.get("name", "") if item else "")
        layout.addWidget(self._name)

        layout.addWidget(QLabel("설명"))
        self._desc = QLineEdit(item.get("description", "") if item else "")
        layout.addWidget(self._desc)

        path_row = QHBoxLayout()
        layout.addWidget(QLabel("경로"))
        self._path = QLineEdit(item.get("path", "") if item else "")
        path_row.addWidget(self._path)
        browse_btn = QPushButton("…")
        browse_btn.setFixedWidth(30)
        browse_btn.clicked.connect(self._browse)
        path_row.addWidget(browse_btn)
        layout.addLayout(path_row)

        hk_row = QHBoxLayout()
        hk_row.addWidget(QLabel("단축키"))
        self._hk_btn = QPushButton(hotkey_button_text(self._hotkey))
        self._hk_btn.clicked.connect(self._capture)
        hk_row.addWidget(self._hk_btn)
        layout.addLayout(hk_row)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "파일 선택")
        if not path:
            path = QFileDialog.getExistingDirectory(self, "폴더 선택")
        if path:
            self._path.setText(path)

    def _capture(self):
        dlg = HotkeyDialog(self, self._hotkey, self._hkm)
        if dlg.exec():
            self._hotkey = dlg.result_hotkey
            self._hk_btn.setText(hotkey_button_text(self._hotkey))

    def get_data(self) -> dict:
        return {
            "name": self._name.text().strip() or "새 파일",
            "description": self._desc.text().strip(),
            "type": "file",
            "path": self._path.text().strip(),
            "hotkey": self._hotkey,
        }


# ── Launcher row ──────────────────────────────────────────────────────────────

class LauncherRow(QFrame):
    edit_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    open_requested = pyqtSignal(str)

    def __init__(self, item: dict, parent=None):
        super().__init__(parent)
        self._id = item["id"]
        self._type = item.get("type", "site")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("QFrame { border-radius: 4px; }")

        row = QHBoxLayout(self)
        row.setContentsMargins(8, 6, 8, 6)
        row.setSpacing(6)

        # Icon letter
        icon = QPushButton((item.get("name", "?")[:1]).upper())
        icon.setFixedSize(28, 28)
        icon.setStyleSheet(
            "background: rgba(59,108,245,0.15); color: #3b6cf5; "
            "border: none; border-radius: 4px; font-weight: bold;"
        )
        icon.clicked.connect(lambda: self.open_requested.emit(self._id))
        row.addWidget(icon)

        # Info
        info = QVBoxLayout()
        info.setSpacing(1)
        name_row = QHBoxLayout()
        name_lbl = QLabel(item.get("name", ""))
        name_lbl.setStyleSheet("font-weight: bold;")
        name_row.addWidget(name_lbl)
        if item.get("username") or item.get("password"):
            auth = QLabel("AUTH")
            auth.setStyleSheet(
                "background: rgba(46,166,114,0.15); color: #2ea672; "
                "border-radius: 3px; padding: 0px 4px; font-size: 7pt; font-weight: bold;"
            )
            name_row.addWidget(auth)
        name_row.addStretch()
        info.addLayout(name_row)
        desc = item.get("description", item.get("path", item.get("url", "")))
        prev = QLabel(str(desc)[:60])
        prev.setStyleSheet("color: grey; font-size: 8pt;")
        info.addWidget(prev)
        row.addLayout(info, 1)

        # Hotkey
        hk = item.get("hotkey")
        if hk:
            hk_lbl = QLabel(hotkey_to_str(hk))
            hk_lbl.setStyleSheet(
                "background: rgba(128,128,128,0.12); border-radius: 3px; "
                "padding: 2px 4px; font-size: 7pt; font-family: Consolas, monospace;"
            )
            row.addWidget(hk_lbl)

        open_btn = QPushButton("열기")
        open_btn.setObjectName("accent")
        open_btn.setFixedWidth(44)
        open_btn.clicked.connect(lambda: self.open_requested.emit(self._id))
        row.addWidget(open_btn)

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

class LauncherTab(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, config, hotkey_manager, parent=None):
        super().__init__(parent)
        self._config = config
        self._hkm = hotkey_manager
        self._mode = "site"
        self._rows: dict[str, LauncherRow] = {}

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(4)

        toggle = QHBoxLayout()
        self._site_btn = QPushButton("🌐 사이트")
        self._site_btn.setCheckable(True)
        self._site_btn.setChecked(True)
        self._site_btn.clicked.connect(lambda: self._set_mode("site"))
        self._file_btn = QPushButton("📁 파일/폴더")
        self._file_btn.setCheckable(True)
        self._file_btn.clicked.connect(lambda: self._set_mode("file"))
        toggle.addWidget(self._site_btn)
        toggle.addWidget(self._file_btn)
        root.addLayout(toggle)

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

        self.reload()

    def reload(self):
        self._clear_list()
        tmpl = self._config.get_active_template()
        for item in tmpl.get("launchers", []):
            if item.get("type", "site") == self._mode:
                self._add_row(item)

    def _set_mode(self, mode: str):
        self._mode = mode
        self._site_btn.setChecked(mode == "site")
        self._file_btn.setChecked(mode == "file")
        self.reload()

    def _clear_list(self):
        for row in list(self._rows.values()):
            self._list_layout.removeWidget(row)
            row.deleteLater()
        self._rows.clear()

    def _add_row(self, item: dict):
        row = LauncherRow(item, self._container)
        row.open_requested.connect(self._open_item)
        row.edit_requested.connect(self._edit_item)
        row.delete_requested.connect(self._delete_item)
        self._list_layout.insertWidget(self._list_layout.count() - 1, row)
        self._rows[item["id"]] = row

    def _get_items(self) -> list:
        return self._config.get_active_template().get("launchers", [])

    def _save_items(self, items: list):
        idx = self._config.get_active_index()
        tmpl = self._config.load_template(idx)
        tmpl["launchers"] = items
        self._config.save_template(idx, tmpl)
        self.data_changed.emit()

    def _add_item(self):
        if self._mode == "site":
            dlg = SiteEditDialog(self, hotkey_manager=self._hkm)
        else:
            dlg = FileEditDialog(self, hotkey_manager=self._hkm)
        if dlg.exec():
            d = dlg.get_data()
            d["id"] = f"ln_{uuid.uuid4().hex[:8]}"
            items = self._get_items()
            items.append(d)
            self._save_items(items)
            if d.get("type", "site") == self._mode:
                self._add_row(d)

    def _edit_item(self, item_id: str):
        items = self._get_items()
        item = next((x for x in items if x["id"] == item_id), None)
        if not item:
            return
        if item.get("type", "site") == "site":
            dlg = SiteEditDialog(self, item=item, hotkey_manager=self._hkm)
        else:
            dlg = FileEditDialog(self, item=item, hotkey_manager=self._hkm)
        if dlg.exec():
            d = dlg.get_data()
            d["id"] = item_id
            for i, x in enumerate(items):
                if x["id"] == item_id:
                    items[i] = d
                    break
            self._save_items(items)
            old_row = self._rows.get(item_id)
            if old_row:
                pos = self._list_layout.indexOf(old_row)
                self._list_layout.removeWidget(old_row)
                old_row.deleteLater()
                if d.get("type", "site") == self._mode:
                    new_row = LauncherRow(d, self._container)
                    new_row.open_requested.connect(self._open_item)
                    new_row.edit_requested.connect(self._edit_item)
                    new_row.delete_requested.connect(self._delete_item)
                    self._list_layout.insertWidget(pos, new_row)
                    self._rows[item_id] = new_row
                else:
                    del self._rows[item_id]

    def _delete_item(self, item_id: str):
        reply = QMessageBox.question(self, "삭제 확인", "이 항목을 삭제하시겠습니까?")
        if reply != QMessageBox.StandardButton.Yes:
            return
        items = [x for x in self._get_items() if x["id"] != item_id]
        self._save_items(items)
        row = self._rows.pop(item_id, None)
        if row:
            self._list_layout.removeWidget(row)
            row.deleteLater()

    def _open_item(self, item_id: str):
        items = self._get_items()
        item = next((x for x in items if x["id"] == item_id), None)
        if not item:
            return
        if item.get("type", "site") == "site":
            _open_site(item)
        else:
            _open_file(item)
