"""
Design System and Theme Tokens for MediCare Pharmacy Management System.
Tailored for a polished, modern Healthcare SaaS aesthetic with full CustomTkinter light/dark support.
"""

class Theme:
    # Surface & Backgrounds (Light mode, Dark mode)
    BG_APP = ("#F8FAFC", "#0B0F19")            # Slate-50 / Deep Dark Canvas
    BG_SIDEBAR = ("#0F172A", "#0A0E1A")        # Executive Deep Navy
    BG_CARD = ("#FFFFFF", "#1E293B")           # Pure White Card / Slate-800
    BG_CARD_HOVER = ("#F8FAFC", "#273549")     # Card Hover
    BG_INPUT = ("#FFFFFF", "#0F172A")          # Input Box Surface
    BG_MUTED = ("#F1F5F9", "#243248")          # Slate-100 / Slate-750

    # Borders & Dividers
    BORDER = ("#E2E8F0", "#334155")            # Slate-200 / Slate-700
    BORDER_FOCUS = ("#2563EB", "#60A5FA")      # Blue Focus Ring
    DIVIDER = ("#F1F5F9", "#1E293B")

    # Brand & Action Colors (Professional Navy & Royal Blue)
    PRIMARY = ("#2563EB", "#3B82F6")           # Medical Blue
    PRIMARY_HOVER = ("#1D4ED8", "#2563EB")
    PRIMARY_LIGHT = ("#EFF6FF", "#172554")
    PRIMARY_TEXT = ("#FFFFFF", "#FFFFFF")

    SECONDARY = ("#F1F5F9", "#334155")
    SECONDARY_HOVER = ("#E2E8F0", "#475569")
    SECONDARY_TEXT = ("#334155", "#F8FAFC")

    # Typography Colors
    TEXT_MAIN = ("#0F172A", "#F8FAFC")         # Slate-900 / Slate-50
    TEXT_MUTED = ("#64748B", "#94A3B8")        # Slate-500 / Slate-400
    TEXT_LIGHT = ("#94A3B8", "#64748B")
    TEXT_NAV_ACTIVE = ("#FFFFFF", "#FFFFFF")
    TEXT_NAV_INACTIVE = ("#94A3B8", "#64748B")

    # Status & TQM Alert Colors
    SUCCESS_BG = ("#DCFCE7", "#064E3B")        # Emerald
    SUCCESS_TEXT = ("#15803D", "#4ADE80")

    WARNING_BG = ("#FEF3C7", "#78350F")        # Amber (Near Expiry / Low Stock)
    WARNING_TEXT = ("#B45309", "#FCD34D")

    DANGER_BG = ("#FEE2E2", "#7F1D1D")         # Red (Expired / Error)
    DANGER_TEXT = ("#B91C1C", "#FCA5A5")

    INFO_BG = ("#E0F2FE", "#0C4A6E")           # Sky Blue
    INFO_TEXT = ("#0284C7", "#38BDF8")

    # High Contrast Overrides (used when accessibility mode is enabled)
    HC_CARD = "#000000"
    HC_TEXT = "#FFFFFF"
    HC_ACCENT = "#FACC15"                      # High-visibility yellow
    HC_BORDER = "#FACC15"
