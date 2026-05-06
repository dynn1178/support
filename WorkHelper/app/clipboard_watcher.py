import time
from PyQt6.QtCore import QThread, pyqtSignal

try:
    import pyperclip as _pc
    _PYPERCLIP_OK = True
except Exception:
    _PYPERCLIP_OK = False


class ClipboardWatcher(QThread):
    new_item = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True

    def run(self):
        if not _PYPERCLIP_OK:
            return
        prev = ""
        while self._running:
            try:
                current = _pc.paste()
                if current and current != prev and current.strip():
                    prev = current
                    self.new_item.emit(current)
            except Exception:
                pass
            time.sleep(0.5)

    def stop(self):
        self._running = False
        self.wait(2000)
