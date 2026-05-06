"""업무보조 프로그램 — 진입점"""
import sys
import os

# Ensure the project root is in sys.path when run as a script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer

from app.config import Config
from app.theme import apply_theme
from ui.main_window import MainWindow


def check_update(current_version: str):
    """Returns (latest_version, download_url) or (None, None)."""
    try:
        import requests
        owner = "your_github_owner"   # ← GitHub owner
        repo  = "WorkHelper"           # ← GitHub repo name
        url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            latest = data.get("tag_name", "").lstrip("v")
            assets = data.get("assets", [])
            dl_url = assets[0]["browser_download_url"] if assets else ""
            if latest and latest > current_version:
                return latest, dl_url
    except Exception:
        pass
    return None, None


def show_update_dialog(parent, latest: str, dl_url: str):
    reply = QMessageBox.question(
        parent, "업데이트 있음",
        f"새 버전 {latest}이 있습니다.\n지금 다운로드하시겠습니까?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    if reply == QMessageBox.StandardButton.Yes:
        import webbrowser
        webbrowser.open(dl_url)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("WorkHelper")
    app.setApplicationDisplayName("업무보조 프로그램")

    config = Config()
    settings = config.get_active_settings()

    apply_theme(
        app,
        settings.get("theme", "light"),
        settings.get("font_family", "맑은 고딕"),
        settings.get("font_size", 9),
    )

    window = MainWindow(config)
    window.show()

    # Deferred update check (non-blocking, 2 seconds after launch)
    version_path = os.path.join(os.path.dirname(__file__), "version.txt")
    try:
        with open(version_path) as f:
            current_version = f.read().strip()
    except Exception:
        current_version = "1.0.0"

    def _do_update_check():
        latest, dl_url = check_update(current_version)
        if latest:
            show_update_dialog(window, latest, dl_url)

    QTimer.singleShot(2000, _do_update_check)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
