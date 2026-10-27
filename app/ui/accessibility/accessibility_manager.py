import json
import os
from typing import Dict, Any, Callable, List
import customtkinter as ctk

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "accessibility_config.json")


class AccessibilityManager:
    """
    Singleton Manager for TQM Q12 Accessibility Standards.
    Manages:
    - Default Light mode with Dark mode and High-Contrast options
    - Dynamic font scaling across all UI elements
    - Focus indicators and readable color palettes
    - Persistent local configuration
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AccessibilityManager, cls).__new__(cls)
            cls._instance._init_manager()
        return cls._instance

    def _init_manager(self):
        self.listeners: List[Callable[..., None]] = []
        self._font_cache: Dict[tuple, ctk.CTkFont] = {}
        self.config: Dict[str, Any] = {
            "appearance_mode": "light",     # light by default, dark, high-contrast
            "font_scale": 1.0,              # 1.0 (normal), 1.15 (large), 1.3 (extra large)
            "high_contrast": False,
            "large_buttons": True
        }
        self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self.config.update(saved)
            except Exception:
                pass
        self._apply_ctk_mode()

    def save_config(self):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass

    def _apply_ctk_mode(self):
        mode = self.config.get("appearance_mode", "light")
        if mode == "high-contrast":
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
        else:
            ctk.set_appearance_mode(mode)
            ctk.set_default_color_theme("blue")

    def set_appearance_mode(self, mode: str):
        self.config["appearance_mode"] = mode
        self.config["high_contrast"] = (mode == "high-contrast")
        self._apply_ctk_mode()
        self.save_config()
        self.notify_listeners("theme")

    def toggle_mode(self):
        current = self.config.get("appearance_mode", "light")
        new_mode = "dark" if current == "light" else "light"
        self.set_appearance_mode(new_mode)

    def set_font_scale(self, scale: float):
        scale = round(float(scale), 2)
        self.config["font_scale"] = scale
        self.save_config()

        # Dynamically reconfigure all live shared CTkFont objects across the entire application
        for (family, base_size, weight, slant), font_obj in list(self._font_cache.items()):
            try:
                new_size = self.get_font_size(base_size)
                font_obj.configure(size=new_size)
            except Exception:
                pass

        self.notify_listeners("font_scale")

    def get_font_size(self, base_size: int) -> int:
        scale = self.config.get("font_scale", 1.0)
        return int(base_size * scale)

    def get_font(
        self,
        base_size: int = 14,
        weight: str = "normal",
        slant: str = "roman",
        family: str = "Segoe UI"
    ) -> ctk.CTkFont:
        key = (family, base_size, weight, slant)
        if key in self._font_cache:
            return self._font_cache[key]

        font_obj = ctk.CTkFont(
            family=family,
            size=self.get_font_size(base_size),
            weight=weight,
            slant=slant
        )
        self._font_cache[key] = font_obj
        return font_obj

    def get_card_fg(self):
        if self.config.get("appearance_mode") == "high-contrast":
            return "#0A0A0A"
        return ("#FFFFFF", "#142826")

    def get_accent_color(self):
        if self.config.get("appearance_mode") == "high-contrast":
            return "#FACC15"
        return ("#046166", "#057275")

    def subscribe(self, callback: Callable[[], None]):
        if callback not in self.listeners:
            self.listeners.append(callback)

    def unsubscribe(self, callback: Callable[[], None]):
        if callback in self.listeners:
            self.listeners.remove(callback)

    def notify_listeners(self, event: str = "general"):
        import inspect
        for listener in list(self.listeners):
            try:
                sig = inspect.signature(listener)
                if len(sig.parameters) > 0:
                    listener(event)
                else:
                    listener()
            except Exception:
                pass


accessibility_manager = AccessibilityManager()
