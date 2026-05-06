import os
import json
from datetime import datetime

from app.utils import get_base_dir, now_iso

BASE_DIR = get_base_dir()
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMPLATES_DIR = os.path.join(DATA_DIR, "templates")
CLIPBOARD_HISTORY_FILE = os.path.join(DATA_DIR, "clipboard_history.json")

DEFAULT_SETTINGS = {
    "theme": "light",
    "font_family": "맑은 고딕",
    "font_size": 9,
    "window": {"width": 400, "height": 700, "always_on_top": False},
    "clipboard_history_limit": 50,
    "active_template": 1,
}

DEFAULT_TEMPLATE = {
    "meta": {"template_name": "기본 설정", "version": "1.0.0", "saved_at": ""},
    "phrases": [
        {"id": "ph_001", "name": "인사말", "text": "안녕하세요.", "hotkey": {"modifiers": ["ctrl"], "key": "1"}, "type": "text"},
        {"id": "ph_002", "name": "감사 인사", "text": "감사합니다.", "hotkey": {"modifiers": ["ctrl"], "key": "2"}, "type": "text"},
        {"id": "ph_003", "name": "수고하셨습니다", "text": "수고하셨습니다.", "hotkey": {"modifiers": ["ctrl"], "key": "3"}, "type": "text"},
    ],
    "snippets": [
        {"id": "sn_001", "name": "기본 SELECT", "text": "SELECT * FROM table_name WHERE 1=1 LIMIT 100;", "language": "sql", "hotkey": {"modifiers": ["ctrl", "shift"], "key": "1"}, "type": "code"},
    ],
    "launchers": [
        {"id": "ln_001", "name": "Google", "description": "구글 검색", "type": "site", "url": "https://google.com", "username": "", "password": "", "browser_path": "", "hotkey": None},
        {"id": "ln_002", "name": "GitHub", "description": "소스 코드 저장소", "type": "site", "url": "https://github.com", "username": "", "password": "", "browser_path": "", "hotkey": None},
    ],
    "images": [],
    "macros": [],
    "memos": [],
    "schedules": [],
    "settings": dict(DEFAULT_SETTINGS),
}


class Config:
    def __init__(self):
        os.makedirs(TEMPLATES_DIR, exist_ok=True)
        os.makedirs(DATA_DIR, exist_ok=True)
        for i in range(1, 6):
            path = self._template_path(i)
            if not os.path.exists(path):
                t = json.loads(json.dumps(DEFAULT_TEMPLATE))
                t["meta"]["template_name"] = f"템플릿 {i}"
                t["meta"]["saved_at"] = now_iso()
                self._write(path, t)
        if not os.path.exists(CLIPBOARD_HISTORY_FILE):
            self._write(CLIPBOARD_HISTORY_FILE, {"history": []})

    # ── internal ──────────────────────────────────────────────
    def _template_path(self, index: int) -> str:
        return os.path.join(TEMPLATES_DIR, f"template_{index}.json")

    def _read(self, path: str) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write(self, path: str, data: dict):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ── templates ─────────────────────────────────────────────
    def load_template(self, index: int) -> dict:
        data = self._read(self._template_path(index))
        if not data:
            t = json.loads(json.dumps(DEFAULT_TEMPLATE))
            t["meta"]["template_name"] = f"템플릿 {index}"
            return t
        # Ensure all keys present
        for k, v in DEFAULT_TEMPLATE.items():
            data.setdefault(k, json.loads(json.dumps(v)))
        return data

    def save_template(self, index: int, data: dict):
        data.setdefault("meta", {})
        data["meta"]["saved_at"] = now_iso()
        self._write(self._template_path(index), data)

    def get_active_index(self) -> int:
        t1 = self.load_template(1)
        return t1.get("settings", {}).get("active_template", 1)

    def get_active_template(self) -> dict:
        return self.load_template(self.get_active_index())

    def get_active_settings(self) -> dict:
        s = self.get_active_template().get("settings", {})
        result = dict(DEFAULT_SETTINGS)
        result.update(s)
        return result

    def set_active_index(self, index: int):
        # Update all templates so the active pointer is consistent
        for i in range(1, 6):
            t = self.load_template(i)
            t.setdefault("settings", dict(DEFAULT_SETTINGS))
            t["settings"]["active_template"] = index
            self.save_template(i, t)

    def get_template_names(self) -> list:
        return [self.load_template(i).get("meta", {}).get("template_name", f"템플릿 {i}") for i in range(1, 6)]

    # ── clipboard history ─────────────────────────────────────
    def load_clipboard_history(self) -> list:
        return self._read(CLIPBOARD_HISTORY_FILE).get("history", [])

    def save_clipboard_history(self, history: list):
        self._write(CLIPBOARD_HISTORY_FILE, {"history": history})

    # ── import / export ───────────────────────────────────────
    def export_template(self, index: int, path: str):
        data = json.loads(json.dumps(self.load_template(index)))
        for ln in data.get("launchers", []):
            ln["password"] = ""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def import_template(self, import_path: str, target_index: int):
        with open(import_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        existing = self.load_template(target_index)
        for i, ln in enumerate(data.get("launchers", [])):
            ex_list = existing.get("launchers", [])
            if i < len(ex_list):
                ln["password"] = ex_list[i].get("password", "")
        self.save_template(target_index, data)
