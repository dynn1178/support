import logging

logger = logging.getLogger(__name__)

try:
    import keyboard as _kb
    _KEYBOARD_AVAILABLE = True
except Exception:
    _KEYBOARD_AVAILABLE = False
    logger.warning("keyboard library unavailable — global hotkeys disabled")


class HotkeyManager:
    def __init__(self):
        self._registered: dict[str, str] = {}  # hotkey_str -> item_id
        self._callbacks: dict[str, object] = {}
        self._paused = False

    def _make_key(self, modifiers: list, key: str) -> str:
        return "+".join(sorted(m.lower() for m in modifiers) + [key.lower()])

    def register(self, modifiers: list, key: str, callback, item_id: str) -> bool:
        if not _KEYBOARD_AVAILABLE:
            return True  # pretend success so UI doesn't break
        hotkey_str = self._make_key(modifiers, key)
        if hotkey_str in self._registered:
            return False  # conflict
        try:
            def _cb():
                if not self._paused:
                    callback()
            _kb.add_hotkey(hotkey_str, _cb)
            self._registered[hotkey_str] = item_id
            self._callbacks[hotkey_str] = _cb
            return True
        except Exception as e:
            logger.warning(f"Failed to register hotkey {hotkey_str}: {e}")
            return False

    def unregister(self, modifiers: list, key: str):
        if not _KEYBOARD_AVAILABLE:
            return
        hotkey_str = self._make_key(modifiers, key)
        if hotkey_str in self._registered:
            try:
                _kb.remove_hotkey(hotkey_str)
            except Exception:
                pass
            del self._registered[hotkey_str]
            self._callbacks.pop(hotkey_str, None)

    def unregister_by_id(self, item_id: str):
        keys_to_remove = [k for k, v in self._registered.items() if v == item_id]
        for hotkey_str in keys_to_remove:
            if _KEYBOARD_AVAILABLE:
                try:
                    _kb.remove_hotkey(hotkey_str)
                except Exception:
                    pass
            del self._registered[hotkey_str]
            self._callbacks.pop(hotkey_str, None)

    def is_conflict(self, modifiers: list, key: str, exclude_id: str = None) -> bool:
        hotkey_str = self._make_key(modifiers, key)
        if hotkey_str not in self._registered:
            return False
        if exclude_id and self._registered[hotkey_str] == exclude_id:
            return False
        return True

    def pause(self):
        """Temporarily disable all callbacks (e.g. during hotkey capture)."""
        self._paused = True

    def resume(self):
        self._paused = False

    def clear_all(self):
        if _KEYBOARD_AVAILABLE:
            for hs in list(self._registered.keys()):
                try:
                    _kb.remove_hotkey(hs)
                except Exception:
                    pass
        self._registered.clear()
        self._callbacks.clear()

    def reload(self, template: dict, callbacks: dict):
        """Re-register all hotkeys from template data.
        callbacks: {item_id: callable}
        """
        self.clear_all()
        for section in ("phrases", "snippets", "images", "macros", "launchers"):
            for item in template.get(section, []):
                hk = item.get("hotkey")
                if not hk:
                    continue
                item_id = item.get("id", "")
                cb = callbacks.get(item_id)
                if cb:
                    self.register(hk.get("modifiers", []), hk.get("key", ""), cb, item_id)
