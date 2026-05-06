import os
from datetime import datetime


def resolve_image_path(path: str, base_dir: str) -> str:
    if os.path.isabs(path):
        return path
    return os.path.join(base_dir, path)


def hotkey_to_str(hotkey: dict) -> str:
    if not hotkey:
        return "미지정"
    mods = hotkey.get("modifiers", [])
    key = hotkey.get("key", "")
    label_map = {"ctrl": "Ctrl", "alt": "Alt", "shift": "Shift"}
    parts = [label_map.get(m, m.capitalize()) for m in mods] + [key.upper()]
    return "+".join(parts)


def hotkey_to_keyboard_str(hotkey: dict) -> str:
    """Convert hotkey dict to keyboard library string (e.g. 'ctrl+alt+1')."""
    if not hotkey:
        return ""
    mods = hotkey.get("modifiers", [])
    key = hotkey.get("key", "").lower()
    return "+".join(sorted(mods) + [key])


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def get_base_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
