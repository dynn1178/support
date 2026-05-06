"""메인 창 — 400×700, 하단 탭바 7개"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QTabBar, QFrame,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon

from app.config import Config
from app.hotkey_manager import HotkeyManager
from app.clipboard_watcher import ClipboardWatcher

from ui.tab_phrase import PhraseTab
from ui.tab_launcher import LauncherTab
from ui.tab_image import ImageTab
from ui.tab_macro import MacroTab
from ui.tab_clipboard import ClipboardTab
from ui.tab_memo import MemoTab
from ui.tab_settings import SettingsTab

VERSION = "1.0.0"
try:
    import os
    _vpath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "version.txt")
    with open(_vpath) as _f:
        VERSION = _f.read().strip()
except Exception:
    pass


class MainWindow(QMainWindow):
    def __init__(self, config: Config):
        super().__init__()
        self._config = config
        self._hkm = HotkeyManager()
        self._clipboard_watcher = ClipboardWatcher()

        self._setup_window()
        self._build_ui()
        self._apply_window_settings()

        self._clipboard_watcher.start()

    # ── Window setup ──────────────────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowTitle("업무보조 프로그램")
        self.setFixedSize(400, 700)

    def _apply_window_settings(self):
        s = self._config.get_active_settings()
        aot = s.get("window", {}).get("always_on_top", False)
        flags = self.windowFlags()
        if aot:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Header ─────────────────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(40)
        header.setObjectName("header")
        header.setStyleSheet("#header { border-bottom: 1px solid rgba(0,0,0,0.1); }")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 0, 12, 0)

        title_lbl = QLabel("업무보조 프로그램")
        title_lbl.setStyleSheet("font-weight: bold; font-size: 10pt;")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()

        ver_lbl = QLabel(f"v{VERSION}")
        ver_lbl.setStyleSheet("color: grey; font-size: 8pt;")
        header_layout.addWidget(ver_lbl)
        layout.addWidget(header)

        # ── Tab widget ────────────────────────────────────────────────────
        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.TabPosition.South)
        self._tabs.setDocumentMode(True)
        self._tabs.tabBar().setExpanding(True)
        self._tabs.setStyleSheet("""
            QTabWidget::pane { border: none; }
            QTabBar { font-size: 7pt; }
            QTabBar::tab { min-height: 50px; padding: 4px 2px; }
        """)
        layout.addWidget(self._tabs, 1)

        # ── Tabs ──────────────────────────────────────────────────────────
        self._phrase_tab = PhraseTab(self._config, self._hkm)
        self._launcher_tab = LauncherTab(self._config, self._hkm)
        self._image_tab = ImageTab(self._config, self._hkm)
        self._macro_tab = MacroTab(self._config, self._hkm)
        self._clipboard_tab = ClipboardTab(self._config, self._clipboard_watcher)
        self._memo_tab = MemoTab(self._config)
        self._settings_tab = SettingsTab(self._config)

        self._tabs.addTab(self._phrase_tab,    "⌨\n상용구")
        self._tabs.addTab(self._launcher_tab,  "⊞\n바로가기")
        self._tabs.addTab(self._image_tab,     "🖼\n이미지")
        self._tabs.addTab(self._macro_tab,     "●\n매크로")
        self._tabs.addTab(self._clipboard_tab, "📋\n클립보드")
        self._tabs.addTab(self._memo_tab,      "📝\n메모")
        self._tabs.addTab(self._settings_tab,  "⚙\n설정")

        # Connect signals
        self._settings_tab.settings_changed.connect(self._on_settings_changed)
        self._phrase_tab.data_changed.connect(lambda: None)
        self._launcher_tab.data_changed.connect(lambda: None)
        self._image_tab.data_changed.connect(lambda: None)
        self._macro_tab.data_changed.connect(lambda: None)

    # ── Event handlers ────────────────────────────────────────────────────────

    def _on_settings_changed(self):
        self._apply_window_settings()
        self.show()  # re-apply window flags
        # Reload all tabs when template switches
        self._phrase_tab.reload()
        self._launcher_tab.reload()
        self._image_tab.reload()
        self._macro_tab.reload()
        self._memo_tab.reload()

    def closeEvent(self, event):
        self._clipboard_watcher.stop()
        self._hkm.clear_all()
        event.accept()
