from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

_BASE = """
QWidget { font-family: '{font}'; font-size: {size}pt; }
QScrollBar:vertical {{ width: 8px; border: none; border-radius: 4px; }}
QScrollBar::handle:vertical {{ border-radius: 4px; min-height: 20px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ height: 8px; border: none; border-radius: 4px; }}
QScrollBar::handle:horizontal {{ border-radius: 4px; min-width: 20px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QGroupBox {{ border-radius: 4px; margin-top: 10px; padding-top: 6px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 8px; padding: 0 4px; }}
QCheckBox::indicator {{ width: 14px; height: 14px; }}
QTabWidget::pane {{ border: none; }}
"""

THEMES = {
    "light": {
        "bg": "#F8F8F8", "bg2": "#EEEEEE", "fg": "#222222", "fg2": "#555555",
        "accent": "#4A90E2", "border": "#CCCCCC",
        "btn_bg": "#E0E0E0", "btn_hover": "#D0D0D0",
        "input_bg": "#FFFFFF", "card_bg": "#FFFFFF",
        "tab_bg": "#E8E8E8", "tab_sel": "#F8F8F8",
    },
    "dark": {
        "bg": "#1E1E2E", "bg2": "#181825", "fg": "#CDD6F4", "fg2": "#A6ADC8",
        "accent": "#89B4FA", "border": "#45475A",
        "btn_bg": "#313244", "btn_hover": "#45475A",
        "input_bg": "#181825", "card_bg": "#1E1E2E",
        "tab_bg": "#181825", "tab_sel": "#1E1E2E",
    },
    "blue": {
        "bg": "#F0F4FF", "bg2": "#DBEAFE", "fg": "#1E3A8A", "fg2": "#2563EB",
        "accent": "#1D4ED8", "border": "#93C5FD",
        "btn_bg": "#BFDBFE", "btn_hover": "#93C5FD",
        "input_bg": "#FFFFFF", "card_bg": "#FFFFFF",
        "tab_bg": "#DBEAFE", "tab_sel": "#F0F4FF",
    },
    "green": {
        "bg": "#F0FFF4", "bg2": "#DCFCE7", "fg": "#14532D", "fg2": "#166534",
        "accent": "#16A34A", "border": "#86EFAC",
        "btn_bg": "#BBF7D0", "btn_hover": "#86EFAC",
        "input_bg": "#FFFFFF", "card_bg": "#FFFFFF",
        "tab_bg": "#DCFCE7", "tab_sel": "#F0FFF4",
    },
    "warm": {
        "bg": "#FFF8F0", "bg2": "#FED7AA", "fg": "#7C2D12", "fg2": "#9A3412",
        "accent": "#EA580C", "border": "#FB923C",
        "btn_bg": "#FDBA74", "btn_hover": "#FB923C",
        "input_bg": "#FFFFFF", "card_bg": "#FFFFFF",
        "tab_bg": "#FED7AA", "tab_sel": "#FFF8F0",
    },
    "dark_red": {
        "bg": "#2B2B2B", "bg2": "#1F1F1F", "fg": "#FECACA", "fg2": "#FCA5A5",
        "accent": "#EF4444", "border": "#7F1D1D",
        "btn_bg": "#3F1515", "btn_hover": "#7F1D1D",
        "input_bg": "#1F1F1F", "card_bg": "#2B2B2B",
        "tab_bg": "#1F1F1F", "tab_sel": "#2B2B2B",
    },
}

THEME_LABELS = {
    "light": "라이트", "dark": "다크", "blue": "블루",
    "green": "그린", "warm": "웜", "dark_red": "다크 레드",
}


def build_qss(theme_name: str, font_family: str, font_size: int) -> str:
    c = THEMES.get(theme_name, THEMES["light"])
    base = _BASE.format(font=font_family, size=font_size)
    specific = f"""
QWidget {{ background-color: {c['bg']}; color: {c['fg']}; }}
QFrame {{ background-color: {c['bg']}; }}
QLabel {{ background-color: transparent; color: {c['fg']}; }}
QPushButton {{
    background-color: {c['btn_bg']}; color: {c['fg']};
    border: 1px solid {c['border']}; border-radius: 3px;
    padding: 3px 8px;
}}
QPushButton:hover {{ background-color: {c['btn_hover']}; }}
QPushButton:pressed {{ background-color: {c['border']}; }}
QPushButton#accent {{
    background-color: {c['accent']}; color: #FFFFFF; border: none;
}}
QPushButton#accent:hover {{ opacity: 0.85; }}
QPushButton#danger {{
    background-color: transparent; color: #E25C6C;
    border: 1px solid #E25C6C; border-radius: 3px; padding: 3px 8px;
}}
QPushButton#danger:hover {{ background-color: #FDF0F2; }}
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {c['input_bg']}; color: {c['fg']};
    border: 1px solid {c['border']}; border-radius: 3px; padding: 3px 6px;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {c['accent']};
}}
QComboBox {{
    background-color: {c['input_bg']}; color: {c['fg']};
    border: 1px solid {c['border']}; border-radius: 3px; padding: 3px 6px;
}}
QComboBox::drop-down {{ border: none; width: 16px; }}
QComboBox QAbstractItemView {{ background-color: {c['input_bg']}; color: {c['fg']}; }}
QListWidget {{
    background-color: {c['input_bg']}; color: {c['fg']};
    border: 1px solid {c['border']}; border-radius: 3px;
}}
QListWidget::item:selected {{ background-color: {c['accent']}; color: #FFFFFF; }}
QListWidget::item:hover {{ background-color: {c['bg2']}; }}
QTableWidget {{
    background-color: {c['input_bg']}; color: {c['fg']};
    border: 1px solid {c['border']}; gridline-color: {c['border']};
}}
QTableWidget::item:selected {{ background-color: {c['accent']}; color: #FFFFFF; }}
QHeaderView::section {{
    background-color: {c['bg2']}; color: {c['fg']};
    border: 1px solid {c['border']}; padding: 3px;
}}
QGroupBox {{
    background-color: transparent;
    border: 1px solid {c['border']};
    color: {c['fg2']};
}}
QTabWidget::tab-bar {{ alignment: center; }}
QTabBar {{
    background-color: {c['tab_bg']};
}}
QTabBar::tab {{
    background-color: {c['tab_bg']}; color: {c['fg2']};
    padding: 6px 4px; border: none; min-width: 50px;
}}
QTabBar::tab:selected {{
    background-color: {c['tab_sel']}; color: {c['fg']};
    border-top: 2px solid {c['accent']};
}}
QTabBar::tab:hover {{ background-color: {c['bg2']}; }}
QScrollBar:vertical {{ background-color: {c['bg2']}; }}
QScrollBar::handle:vertical {{ background-color: {c['border']}; }}
QScrollBar:horizontal {{ background-color: {c['bg2']}; }}
QScrollBar::handle:horizontal {{ background-color: {c['border']}; }}
QCheckBox {{ color: {c['fg']}; }}
QSpinBox, QDateTimeEdit {{
    background-color: {c['input_bg']}; color: {c['fg']};
    border: 1px solid {c['border']}; border-radius: 3px; padding: 3px;
}}
QSplitter::handle {{ background-color: {c['border']}; }}
QDialog {{ background-color: {c['bg']}; }}
QMessageBox {{ background-color: {c['bg']}; }}
"""
    return base + specific


def apply_theme(app: QApplication, theme: str, font_family: str, font_size: int):
    app.setStyleSheet(build_qss(theme, font_family, font_size))
    font = QFont(font_family, font_size)
    app.setFont(font)
