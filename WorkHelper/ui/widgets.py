"""Shared UI helpers used across tabs."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QComboBox, QDialogButtonBox,
)
from PyQt6.QtCore import Qt


# ── Hotkey capture dialog ────────────────────────────────────────────────────

_MODIFIER_KEYS = {Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_Shift, Qt.Key.Key_Meta}
_KEY_NAMES = {
    Qt.Key.Key_F1: "F1", Qt.Key.Key_F2: "F2", Qt.Key.Key_F3: "F3",
    Qt.Key.Key_F4: "F4", Qt.Key.Key_F5: "F5", Qt.Key.Key_F6: "F6",
    Qt.Key.Key_F7: "F7", Qt.Key.Key_F8: "F8", Qt.Key.Key_F9: "F9",
    Qt.Key.Key_F10: "F10", Qt.Key.Key_F11: "F11", Qt.Key.Key_F12: "F12",
}


class HotkeyDialog(QDialog):
    """Modal dialog for capturing a keyboard shortcut."""

    def __init__(self, parent=None, current: dict = None, hotkey_manager=None):
        super().__init__(parent)
        self.setWindowTitle("단축키 설정")
        self.setFixedSize(300, 180)
        self.setModal(True)
        self._hotkey_manager = hotkey_manager
        self.result_hotkey: dict | None = None

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        self._label = QLabel("단축키를 누르세요 (Esc = 취소)")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label)

        self._preview = QLabel("—")
        self._preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview.setStyleSheet("font-weight: bold; font-size: 13pt; padding: 8px;")
        layout.addWidget(self._preview)

        self._current_combo: dict | None = current

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        clear_btn = QPushButton("단축키 지우기")
        clear_btn.clicked.connect(self._clear)
        layout.addWidget(clear_btn)

        if current:
            self._show_combo(current)

        if hotkey_manager:
            hotkey_manager.pause()

    def _show_combo(self, combo: dict):
        mods = combo.get("modifiers", [])
        key = combo.get("key", "")
        label_map = {"ctrl": "Ctrl", "alt": "Alt", "shift": "Shift"}
        parts = [label_map.get(m, m.capitalize()) for m in mods] + [key.upper()]
        self._preview.setText(" + ".join(parts))
        self._current_combo = combo

    def _clear(self):
        self._current_combo = None
        self._preview.setText("—")

    def _accept(self):
        self.result_hotkey = self._current_combo
        self.accept()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self.reject()
            return
        if key in _MODIFIER_KEYS:
            return
        mods = []
        mod_flags = event.modifiers()
        if mod_flags & Qt.KeyboardModifier.ControlModifier:
            mods.append("ctrl")
        if mod_flags & Qt.KeyboardModifier.AltModifier:
            mods.append("alt")
        if mod_flags & Qt.KeyboardModifier.ShiftModifier:
            mods.append("shift")

        key_str = _KEY_NAMES.get(key)
        if key_str is None:
            text = event.text().strip()
            if text and text.isprintable():
                key_str = text.upper()
            else:
                return

        combo = {"modifiers": mods, "key": key_str}
        self._show_combo(combo)

    def closeEvent(self, event):
        if self._hotkey_manager:
            self._hotkey_manager.resume()
        super().closeEvent(event)

    def done(self, result):
        if self._hotkey_manager:
            self._hotkey_manager.resume()
        super().done(result)


def hotkey_button_text(hotkey: dict | None) -> str:
    if not hotkey:
        return "단축키 없음"
    mods = hotkey.get("modifiers", [])
    key = hotkey.get("key", "")
    label_map = {"ctrl": "Ctrl", "alt": "Alt", "shift": "Shift"}
    parts = [label_map.get(m, m.capitalize()) for m in mods] + [key.upper()]
    return " + ".join(parts)


# ── Simple card widget ────────────────────────────────────────────────────────

from PyQt6.QtWidgets import QFrame, QWidget


class CardWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("QFrame { border-radius: 4px; margin: 1px; padding: 2px; }")
