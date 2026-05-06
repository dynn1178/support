"""탭3: 참조 이미지 뷰어"""
import os
import uuid
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QDialog, QDialogButtonBox, QLineEdit,
    QFileDialog, QCheckBox, QSlider, QSizePolicy,
)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, pyqtSignal

from app.utils import resolve_image_path, hotkey_to_str, get_base_dir
from ui.widgets import HotkeyDialog, hotkey_button_text


# ── Image viewer dialog ───────────────────────────────────────────────────────

class ImageViewerDialog(QDialog):
    def __init__(self, parent=None, item: dict = None):
        super().__init__(parent, Qt.WindowType.Window)
        self.setWindowTitle(item.get("name", "이미지") if item else "이미지")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        path = resolve_image_path(item.get("path", ""), get_base_dir()) if item else ""

        self._img_label = QLabel()
        self._img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        if path and os.path.isfile(path):
            pix = QPixmap(path)
            if not pix.isNull():
                pix = pix.scaled(1200, 900, Qt.AspectRatioMode.KeepAspectRatio,
                                  Qt.TransformationMode.SmoothTransformation)
                self._img_label.setPixmap(pix)
                self.resize(min(pix.width() + 20, 1200), min(pix.height() + 60, 940))
            else:
                self._img_label.setText(f"이미지를 불러올 수 없습니다:\n{path}")
                self.resize(400, 200)
        else:
            self._img_label.setText(f"파일을 찾을 수 없습니다:\n{path or '(경로 없음)'}")
            self.resize(400, 150)

        layout.addWidget(self._img_label, 1)

        footer = QHBoxLayout()
        aot_check = QCheckBox("항상 위")
        aot_check.toggled.connect(self._toggle_aot)
        footer.addWidget(aot_check)
        footer.addStretch()
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(self.close)
        footer.addWidget(close_btn)
        layout.addLayout(footer)

    def _toggle_aot(self, on: bool):
        flags = self.windowFlags()
        if on:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()


# ── Edit dialog ───────────────────────────────────────────────────────────────

class ImageEditDialog(QDialog):
    def __init__(self, parent=None, item: dict = None, hotkey_manager=None):
        super().__init__(parent)
        self.setWindowTitle("이미지 편집")
        self.setMinimumWidth(340)
        self.setModal(True)
        self._hkm = hotkey_manager
        self._hotkey: dict | None = item.get("hotkey") if item else None

        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        layout.addWidget(QLabel("이름"))
        self._name = QLineEdit(item.get("name", "") if item else "")
        layout.addWidget(self._name)

        layout.addWidget(QLabel("이미지 경로"))
        path_row = QHBoxLayout()
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
        path, _ = QFileDialog.getOpenFileName(self, "이미지 선택", "",
            "이미지 (*.png *.jpg *.jpeg *.bmp *.gif *.webp)")
        if path:
            self._path.setText(path)

    def _capture(self):
        dlg = HotkeyDialog(self, self._hotkey, self._hkm)
        if dlg.exec():
            self._hotkey = dlg.result_hotkey
            self._hk_btn.setText(hotkey_button_text(self._hotkey))

    def get_data(self) -> dict:
        return {
            "name": self._name.text().strip() or "새 이미지",
            "path": self._path.text().strip(),
            "hotkey": self._hotkey,
        }


# ── Image row ─────────────────────────────────────────────────────────────────

class ImageRow(QFrame):
    edit_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    view_requested = pyqtSignal(str)

    def __init__(self, item: dict, parent=None):
        super().__init__(parent)
        self._id = item["id"]
        self.setFrameShape(QFrame.Shape.StyledPanel)

        row = QHBoxLayout(self)
        row.setContentsMargins(8, 6, 8, 6)
        row.setSpacing(6)

        # Icon
        icon_lbl = QLabel("🖼")
        icon_lbl.setFixedWidth(24)
        row.addWidget(icon_lbl)

        # Hotkey
        hk_lbl = QLabel(hotkey_to_str(item.get("hotkey")))
        hk_lbl.setFixedWidth(90)
        hk_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hk_lbl.setStyleSheet(
            "background: rgba(128,128,128,0.12); border-radius: 3px; "
            "padding: 2px 4px; font-size: 8pt; font-family: Consolas, monospace;"
        )
        row.addWidget(hk_lbl)

        # Info
        info = QVBoxLayout()
        info.setSpacing(1)
        name_lbl = QLabel(item.get("name", ""))
        name_lbl.setStyleSheet("font-weight: bold;")
        info.addWidget(name_lbl)
        path = item.get("path", "경로 없음")
        path_lbl = QLabel(os.path.basename(path) if path else "경로 없음")
        path_lbl.setStyleSheet("color: grey; font-size: 8pt;")
        info.addWidget(path_lbl)
        row.addLayout(info, 1)

        view_btn = QPushButton("열기")
        view_btn.setObjectName("accent")
        view_btn.setFixedWidth(44)
        view_btn.clicked.connect(lambda: self.view_requested.emit(self._id))
        row.addWidget(view_btn)

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

class ImageTab(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, config, hotkey_manager, parent=None):
        super().__init__(parent)
        self._config = config
        self._hkm = hotkey_manager
        self._rows: dict[str, ImageRow] = {}
        self._viewers: list[QDialog] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(4)

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
        for item in tmpl.get("images", []):
            self._add_row(item)

    def _clear_list(self):
        for row in list(self._rows.values()):
            self._list_layout.removeWidget(row)
            row.deleteLater()
        self._rows.clear()

    def _add_row(self, item: dict):
        row = ImageRow(item, self._container)
        row.view_requested.connect(self._view_item)
        row.edit_requested.connect(self._edit_item)
        row.delete_requested.connect(self._delete_item)
        self._list_layout.insertWidget(self._list_layout.count() - 1, row)
        self._rows[item["id"]] = row

    def _get_items(self) -> list:
        return self._config.get_active_template().get("images", [])

    def _save_items(self, items: list):
        idx = self._config.get_active_index()
        tmpl = self._config.load_template(idx)
        tmpl["images"] = items
        self._config.save_template(idx, tmpl)
        self.data_changed.emit()

    def _add_item(self):
        dlg = ImageEditDialog(self, hotkey_manager=self._hkm)
        if dlg.exec():
            d = dlg.get_data()
            d["id"] = f"img_{uuid.uuid4().hex[:8]}"
            items = self._get_items()
            items.append(d)
            self._save_items(items)
            self._add_row(d)
            if d.get("hotkey"):
                hk = d["hotkey"]
                self._hkm.register(hk.get("modifiers", []), hk.get("key", ""),
                                    lambda item=d: self._view_item(item["id"]), d["id"])

    def _edit_item(self, item_id: str):
        items = self._get_items()
        item = next((x for x in items if x["id"] == item_id), None)
        if not item:
            return
        old_hk = item.get("hotkey")
        dlg = ImageEditDialog(self, item=item, hotkey_manager=self._hkm)
        if dlg.exec():
            d = dlg.get_data()
            d["id"] = item_id
            if old_hk:
                self._hkm.unregister(old_hk.get("modifiers", []), old_hk.get("key", ""))
            if d.get("hotkey"):
                hk = d["hotkey"]
                self._hkm.register(hk.get("modifiers", []), hk.get("key", ""),
                                    lambda iid=item_id: self._view_item(iid), item_id)
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
                new_row = ImageRow(d, self._container)
                new_row.view_requested.connect(self._view_item)
                new_row.edit_requested.connect(self._edit_item)
                new_row.delete_requested.connect(self._delete_item)
                self._list_layout.insertWidget(pos, new_row)
                self._rows[item_id] = new_row

    def _delete_item(self, item_id: str):
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "삭제 확인", "이 항목을 삭제하시겠습니까?")
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

    def _view_item(self, item_id: str):
        items = self._get_items()
        item = next((x for x in items if x["id"] == item_id), None)
        if not item:
            return
        dlg = ImageViewerDialog(self, item)
        dlg.show()
        self._viewers.append(dlg)
