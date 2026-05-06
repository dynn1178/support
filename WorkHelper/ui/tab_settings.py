"""탭7: 설정 · 테마 · 폰트"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QCheckBox, QGroupBox, QLineEdit,
    QFileDialog, QMessageBox, QScrollArea, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QApplication

from app.theme import THEMES, THEME_LABELS, apply_theme


FONT_SIZES = [7, 8, 9, 10, 11, 12, 13, 14]
FONTS = ["맑은 고딕", "나눔고딕", "굴림", "돋움", "Malgun Gothic", "Arial", "Segoe UI", "Tahoma"]


class SettingsTab(QWidget):
    settings_changed = pyqtSignal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self._config = config

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(10)
        scroll.setWidget(inner)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        # ── Template ──────────────────────────────────────────────────────────
        tmpl_box = QGroupBox("템플릿 (데이터 슬롯)")
        tmpl_layout = QVBoxLayout(tmpl_box)
        tmpl_layout.setSpacing(4)

        slot_row = QHBoxLayout()
        slot_row.addWidget(QLabel("활성 템플릿"))
        self._tmpl_combo = QComboBox()
        self._tmpl_combo.currentIndexChanged.connect(self._on_template_changed)
        slot_row.addWidget(self._tmpl_combo, 1)
        tmpl_layout.addLayout(slot_row)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("템플릿 이름"))
        self._tmpl_name = QLineEdit()
        name_row.addWidget(self._tmpl_name, 1)
        rename_btn = QPushButton("이름 저장")
        rename_btn.clicked.connect(self._rename_template)
        name_row.addWidget(rename_btn)
        tmpl_layout.addLayout(name_row)

        io_row = QHBoxLayout()
        export_btn = QPushButton("내보내기…")
        export_btn.clicked.connect(self._export_template)
        import_btn = QPushButton("가져오기…")
        import_btn.clicked.connect(self._import_template)
        io_row.addWidget(export_btn)
        io_row.addWidget(import_btn)
        io_row.addStretch()
        tmpl_layout.addLayout(io_row)
        root.addWidget(tmpl_box)

        # ── Theme ──────────────────────────────────────────────────────────────
        theme_box = QGroupBox("테마")
        theme_layout = QVBoxLayout(theme_box)
        swatch_row = QHBoxLayout()
        swatch_row.setSpacing(4)
        self._theme_btns: dict[str, QPushButton] = {}
        for key, label in THEME_LABELS.items():
            c = THEMES[key]
            btn = QPushButton(label)
            btn.setFixedHeight(32)
            btn.setStyleSheet(
                f"background: {c['bg']}; color: {c['fg']}; "
                f"border: 2px solid {c['border']}; border-radius: 4px;"
            )
            btn.clicked.connect(lambda _, k=key: self._apply_theme(k))
            swatch_row.addWidget(btn)
            self._theme_btns[key] = btn
        theme_layout.addLayout(swatch_row)
        root.addWidget(theme_box)

        # ── Font ───────────────────────────────────────────────────────────────
        font_box = QGroupBox("폰트")
        font_layout = QHBoxLayout(font_box)
        font_layout.addWidget(QLabel("글꼴"))
        self._font_combo = QComboBox()
        self._font_combo.addItems(FONTS)
        font_layout.addWidget(self._font_combo, 1)
        font_layout.addWidget(QLabel("크기"))
        self._font_size = QComboBox()
        self._font_size.addItems([str(s) for s in FONT_SIZES])
        self._font_size.setFixedWidth(60)
        font_layout.addWidget(self._font_size)
        apply_font_btn = QPushButton("적용")
        apply_font_btn.clicked.connect(self._apply_font)
        font_layout.addWidget(apply_font_btn)
        root.addWidget(font_box)

        # ── Window ────────────────────────────────────────────────────────────
        win_box = QGroupBox("창 설정")
        win_layout = QVBoxLayout(win_box)
        self._aot_check = QCheckBox("항상 위 (Always on Top)")
        self._aot_check.toggled.connect(self._toggle_aot)
        win_layout.addWidget(self._aot_check)
        root.addWidget(win_box)

        # ── Clipboard ─────────────────────────────────────────────────────────
        cb_box = QGroupBox("클립보드 히스토리")
        cb_layout = QHBoxLayout(cb_box)
        cb_layout.addWidget(QLabel("최대 개수"))
        self._cb_limit = QSpinBox()
        self._cb_limit.setRange(10, 500)
        self._cb_limit.setValue(50)
        cb_layout.addWidget(self._cb_limit)
        cb_save_btn = QPushButton("저장")
        cb_save_btn.clicked.connect(self._save_cb_limit)
        cb_layout.addWidget(cb_save_btn)
        cb_layout.addStretch()
        root.addWidget(cb_box)

        root.addStretch()
        self._load_settings()

    def _load_settings(self):
        names = self._config.get_template_names()
        active = self._config.get_active_index()
        self._tmpl_combo.blockSignals(True)
        self._tmpl_combo.clear()
        for i, name in enumerate(names):
            self._tmpl_combo.addItem(f"{i+1}. {name}", i + 1)
        self._tmpl_combo.setCurrentIndex(active - 1)
        self._tmpl_combo.blockSignals(False)
        self._tmpl_name.setText(names[active - 1])

        s = self._config.get_active_settings()
        font = s.get("font_family", "맑은 고딕")
        size = str(s.get("font_size", 9))
        if font in FONTS:
            self._font_combo.setCurrentText(font)
        if size in [str(x) for x in FONT_SIZES]:
            self._font_size.setCurrentText(size)
        self._aot_check.setChecked(s.get("window", {}).get("always_on_top", False))
        self._cb_limit.setValue(s.get("clipboard_history_limit", 50))

    def _save_settings(self, patch: dict):
        idx = self._config.get_active_index()
        tmpl = self._config.load_template(idx)
        tmpl.setdefault("settings", {}).update(patch)
        self._config.save_template(idx, tmpl)

    def _on_template_changed(self, index: int):
        new_idx = self._tmpl_combo.itemData(index)
        if new_idx is None:
            return
        self._config.set_active_index(new_idx)
        names = self._config.get_template_names()
        self._tmpl_name.setText(names[new_idx - 1])
        self.settings_changed.emit()

    def _rename_template(self):
        name = self._tmpl_name.text().strip()
        if not name:
            return
        idx = self._config.get_active_index()
        tmpl = self._config.load_template(idx)
        tmpl["meta"]["template_name"] = name
        self._config.save_template(idx, tmpl)
        self._load_settings()

    def _export_template(self):
        idx = self._config.get_active_index()
        path, _ = QFileDialog.getSaveFileName(self, "내보내기", f"template_{idx}.json", "JSON (*.json)")
        if path:
            self._config.export_template(idx, path)
            QMessageBox.information(self, "완료", "내보내기 완료 (비밀번호 제외)")

    def _import_template(self):
        path, _ = QFileDialog.getOpenFileName(self, "가져오기", "", "JSON (*.json)")
        if not path:
            return
        idx = self._config.get_active_index()
        try:
            self._config.import_template(path, idx)
            self.settings_changed.emit()
            QMessageBox.information(self, "완료", "가져오기 완료")
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))

    def _apply_theme(self, theme: str):
        self._save_settings({"theme": theme})
        s = self._config.get_active_settings()
        app = QApplication.instance()
        if app:
            apply_theme(app, theme, s.get("font_family", "맑은 고딕"), s.get("font_size", 9))

    def _apply_font(self):
        font = self._font_combo.currentText()
        size = int(self._font_size.currentText())
        self._save_settings({"font_family": font, "font_size": size})
        s = self._config.get_active_settings()
        app = QApplication.instance()
        if app:
            apply_theme(app, s.get("theme", "light"), font, size)

    def _toggle_aot(self, on: bool):
        self._save_settings({"window": {"always_on_top": on}})
        # Propagate to main window
        self.settings_changed.emit()

    def _save_cb_limit(self):
        self._save_settings({"clipboard_history_limit": self._cb_limit.value()})
