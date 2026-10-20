import json
import os
from typing import Dict, Any, Callable, List
import customtkinter as ctk

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "accessibility_config.json")


class AccessibilityManager:
    """
    Singleton Manager for TQM Q12 Accessibility Standards.
    Manages:
    - High contrast, dark mode, light mode
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
        self.listeners: List[Callable[[], None]] = []
        self.config: Dict[str, Any] = {
            "appearance_mode": "dark",      # dark, light, high-contrast
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
        mode = self.config.get("appearance_mode", "dark")
        if mode == "high-contrast":
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
        else:
            ctk.set_appearance_mode(mode)

    def set_appearance_mode(self, mode: str):
        self.config["appearance_mode"] = mode
        self.config["high_contrast"] = (mode == "high-contrast")
        self._apply_ctk_mode()
        self.save_config()
        self.notify_listeners()

    def set_font_scale(self, scale: float):
        self.config["font_scale"] = round(scale, 2)
        self.save_config()
        self.notify_listeners()

    def get_font_size(self, base_size: int) -> int:
        scale = self.config.get("font_scale", 1.0)
        return int(base_size * scale)

    def get_font(self, base_size: int = 14, weight: str = "normal", slant: str = "roman") -> ctk.CTkFont:
        return ctk.CTkFont(size=self.get_font_size(base_size), weight=weight, slant=slant)

    def get_card_fg(self) -> str:
        if self.config.get("appearance_mode") == "high-contrast":
            return "#0A0A0A"
        return "#1E293B" if self.config.get("appearance_mode") == "dark" else "#F1F5F9"

    def get_accent_color(self) -> str:
        if self.config.get("appearance_mode") == "high-contrast":
            return "#FACC15"  # High visibility yellow
        return "#3B82F6"      # Standard blue

    def subscribe(self, callback: Callable[[], None]):
        if callback not in self.listeners:
            self.listeners.append(callback)

    def unsubscribe(self, callback: Callable[[], None]):
        if callback in self.listeners:
            self.listeners.remove(callback)

    def notify_listeners(self):
        for listener in self.listeners:
            try:
                listener()
            except Exception:
                pass


accessibility_manager = AccessibilityManager()
