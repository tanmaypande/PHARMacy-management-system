"""
Unit tests for UI Theme Tokens and Accessibility Manager (TQM Q12).
"""
import pytest
from app.ui.theme import Theme
from app.ui.accessibility.accessibility_manager import AccessibilityManager, accessibility_manager


def test_theme_tokens_structure():
    """Verify key theme tokens follow (light, dark) tuple convention for CustomTkinter."""
    tokens = [
        Theme.BG_APP,
        Theme.BG_SIDEBAR,
        Theme.BG_CARD,
        Theme.BG_INPUT,
        Theme.BG_MUTED,
        Theme.PRIMARY,
        Theme.PRIMARY_HOVER,
        Theme.TEXT_MAIN,
        Theme.TEXT_MUTED,
        Theme.SUCCESS_BG,
        Theme.SUCCESS_TEXT,
        Theme.WARNING_BG,
        Theme.WARNING_TEXT,
        Theme.DANGER_BG,
        Theme.DANGER_TEXT,
    ]
    for token in tokens:
        assert isinstance(token, tuple), f"Expected tuple for token, got {type(token)}"
        assert len(token) == 2, f"Expected 2 elements in token tuple, got {len(token)}"
        assert token[0].startswith("#"), f"Expected hex color, got {token[0]}"
        assert token[1].startswith("#"), f"Expected hex color, got {token[1]}"


def test_accessibility_manager_font_scaling():
    """Verify dynamic font scaling recalculation for Q12 standards."""
    initial_scale = accessibility_manager.config.get("font_scale", 1.0)
    
    # Base size 14 at scale 1.0
    accessibility_manager.set_font_scale(1.0)
    assert accessibility_manager.get_font_size(14) == 14

    # Scale 1.2
    accessibility_manager.set_font_scale(1.2)
    assert accessibility_manager.get_font_size(14) == 16  # int(14 * 1.2) = 16

    # Restore initial
    accessibility_manager.set_font_scale(initial_scale)


def test_accessibility_manager_theme_mode():
    """Verify theme switching and high contrast overrides."""
    initial_mode = accessibility_manager.config.get("appearance_mode", "light")
    
    accessibility_manager.set_appearance_mode("light")
    assert accessibility_manager.config["appearance_mode"] == "light"
    assert not accessibility_manager.config["high_contrast"]

    accessibility_manager.set_appearance_mode("dark")
    assert accessibility_manager.config["appearance_mode"] == "dark"

    accessibility_manager.set_appearance_mode("high-contrast")
    assert accessibility_manager.config["high_contrast"] is True
    assert accessibility_manager.get_card_fg() == "#0A0A0A"
    assert accessibility_manager.get_accent_color() == "#FACC15"

    # Restore to default light
    accessibility_manager.set_appearance_mode(initial_mode)
