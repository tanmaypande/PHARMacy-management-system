"""
Design System and Theme Tokens for MediCare Pharmacy Management System.
Faithfully tailored to the Modern Healthcare Deep-Teal & Lime-Green Aesthetic.
Features:
- Clean off-white/mint canvas (#F2F6F5)
- Crisp white sidebar (#FFFFFF) with deep-teal active pill (#046166)
- Rich deep-teal hero banner (#046166 / #057275)
- Vibrant lime-green accent buttons (#C6EB67) with dark forest text (#0F2926)
- Soft mint-tinted card surfaces and table headers (#E8F2EF)
"""
from typing import Tuple


class Theme:
    # Surface & Backgrounds (Light mode, Dark mode)
    BG_APP = ("#F2F6F5", "#0B1716")            # Soft mint-tinted light canvas / Deep dark forest
    BG_SIDEBAR = ("#FFFFFF", "#0F201E")        # Clean white sidebar / Dark forest sidebar
    BG_CARD = ("#FFFFFF", "#142826")           # Pure white card / Forest card
    BG_CARD_HOVER = ("#F8FAFA", "#1B3330")     # Subtle hover surface
    BG_INPUT = ("#FFFFFF", "#0F201E")          # Clean input field surface
    BG_MUTED = ("#E8F2EF", "#18302E")          # Soft mint-grey accent surface
    BG_ROW_ALT = ("#F9FBFA", "#122523")        # Alternating table rows
    BG_ROW_HOVER = ("#EDF6F3", "#1B3734")      # Table row hover

    # Hero / Banner Surface (Deep Teal from Mockup 1)
    BG_BANNER = ("#046166", "#044E52")         # Deep medical teal banner
    BG_BANNER_ACCENT = ("#057275", "#066267")  # Secondary gradient tone

    # Borders & Dividers
    BORDER = ("#E0ECE8", "#20423E")            # Subtle mint-tinted border
    BORDER_FOCUS = ("#057275", "#10B981")      # Deep teal / emerald focus ring
    DIVIDER = ("#E8F2EF", "#18302E")

    # Primary Brand Colors (Deep Medical Teal)
    PRIMARY = ("#046166", "#057275")           # Deep teal
    PRIMARY_HOVER = ("#034E52", "#048E94")     # Darker / richer teal hover
    PRIMARY_LIGHT = ("#E6F4F1", "#133532")     # Very light teal tint
    PRIMARY_TEXT = ("#FFFFFF", "#FFFFFF")

    # Vibrant Lime-Green Accent (Mockup 2 Call-to-Action Buttons & Badges)
    ACCENT_LIME = ("#C6EB67", "#A3E635")       # Vibrant lime/pistachio green
    ACCENT_LIME_HOVER = ("#B5DF54", "#84CC16") # Deeper lime on hover
    ACCENT_LIME_TEXT = ("#0F2926", "#0A1F1D")  # Dark forest green text for high contrast

    # Secondary Button & Element Colors
    SECONDARY = ("#E8F2EF", "#18302E")
    SECONDARY_HOVER = ("#DCEAE5", "#22423E")
    SECONDARY_TEXT = ("#0F2926", "#E8F4F1")

    # Typography Colors
    TEXT_MAIN = ("#0F2926", "#F2F8F6")         # Rich dark slate-forest / Crisp light
    TEXT_MUTED = ("#5A7571", "#8FAFA9")        # Muted slate-mint text
    TEXT_LIGHT = ("#8B9E9B", "#627E79")        # Subdued helper text
    TEXT_NAV_ACTIVE = ("#FFFFFF", "#FFFFFF")   # High-contrast white on active teal pill
    TEXT_NAV_INACTIVE = ("#5A7571", "#8FAFA9") # Muted nav item

    # Status & TQM Alert Colors
    SUCCESS_BG = ("#DCFCE7", "#064E3B")        # Soft emerald mint
    SUCCESS_TEXT = ("#065F46", "#4ADE80")

    WARNING_BG = ("#FEF3C7", "#78350F")        # Soft amber
    WARNING_TEXT = ("#B45309", "#FCD34D")

    DANGER_BG = ("#FEE2E2", "#7F1D1D")         # Soft coral red
    DANGER_TEXT = ("#B91C1C", "#FCA5A5")

    INFO_BG = ("#E0F2FE", "#0C4A6E")           # Soft sky blue
    INFO_TEXT = ("#0284C7", "#38BDF8")

    # High Contrast Overrides (WCAG AAA)
    HC_CARD = "#000000"
    HC_TEXT = "#FFFFFF"
    HC_ACCENT = "#FACC15"                      # High-visibility yellow
    HC_BORDER = "#FACC15"

    # Shape & Geometry Tokens
    RADIUS_CARD = 14
    RADIUS_BUTTON = 10
    RADIUS_INPUT = 10
    RADIUS_BADGE = 8
    RADIUS_PILL = 20
