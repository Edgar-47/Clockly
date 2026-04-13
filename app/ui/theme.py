"""
Shared design tokens and small UI helpers for Fichaje Restaurante.

The palette is neutral-first with teal, green, amber and red accents. It keeps
the app professional without leaning on a flat blue theme.
"""

from __future__ import annotations

import customtkinter as ctk

# Backgrounds
BG_ROOT = "#0E100F"
BG_CARD = "#171A18"
BG_RAISED = "#202520"
BG_HOVER = "#29302A"
BG_FIELD = "#111412"

# Brand surfaces
BRAND_BG = "#101611"
BRAND_RING = "#28362D"
BRAND_TEXT = "#F8FAF7"
BRAND_SUB = "#A3AEA7"

# Accents
ACCENT = "#2DD4BF"
ACCENT_HOVER = "#14B8A6"
ACCENT_DIM = "#123D37"
ACCENT_SOFT = "#CFFCF4"

SUCCESS = "#22C55E"
SUCCESS_HOVER = "#16A34A"
SUCCESS_DIM = "#0F351E"
SUCCESS_TEXT = "#86EFAC"

DANGER = "#F43F5E"
DANGER_HOVER = "#E11D48"
DANGER_DIM = "#3B111B"
DANGER_TEXT = "#FDA4AF"

WARNING = "#F59E0B"
WARNING_HOVER = "#D97706"
WARNING_DIM = "#3B2A0B"
WARNING_TEXT = "#FCD34D"

# Text
T_PRIMARY = "#F4F7F2"
T_SECONDARY = "#B8C1BA"
T_MUTED = "#76837B"
T_DISABLED = "#59635D"

# Borders
BORDER = "#2A312C"
BORDER_LT = "#3A443D"
BORDER_FOCUS = "#5EEAD4"

# Compact, modern radii. Keep buttons and cards restrained.
R_SM = 5
R_MD = 7
R_LG = 8
R_XL = 8

# Layout
PAGE_PAD = 24
CARD_PAD = 18


# ── Font helpers ──────────────────────────────────────────────────────────────

def f(size: int, weight: str = "normal") -> ctk.CTkFont:
    """Return a CTkFont with Segoe UI at the given size and weight."""
    return ctk.CTkFont(family="Segoe UI", size=size, weight=weight)


def bold(size: int) -> ctk.CTkFont:
    return f(size, "bold")


# ── Common widget factory helpers ─────────────────────────────────────────────

def separator(parent, *, padx: int = 0, pady: tuple = (0, 0)) -> ctk.CTkFrame:
    """A 1-pixel horizontal rule."""
    line = ctk.CTkFrame(parent, height=1, fg_color=BORDER, corner_radius=0)
    line.pack(fill="x", padx=padx, pady=pady)
    return line


def card(parent, **kwargs) -> ctk.CTkFrame:
    """Create a consistent elevated surface."""
    defaults = {
        "fg_color": BG_CARD,
        "corner_radius": R_LG,
        "border_width": 1,
        "border_color": BORDER,
    }
    defaults.update(kwargs)
    return ctk.CTkFrame(parent, **defaults)


def primary_button_kwargs() -> dict:
    return {
        "fg_color": ACCENT,
        "hover_color": ACCENT_HOVER,
        "text_color": "#062421",
        "corner_radius": R_MD,
    }


def quiet_button_kwargs() -> dict:
    return {
        "fg_color": "transparent",
        "hover_color": BG_HOVER,
        "border_width": 1,
        "border_color": BORDER_LT,
        "text_color": T_SECONDARY,
        "corner_radius": R_MD,
    }


def entry_kwargs() -> dict:
    return {
        "fg_color": BG_FIELD,
        "border_color": BORDER_LT,
        "border_width": 1,
        "corner_radius": R_MD,
        "text_color": T_PRIMARY,
        "placeholder_text_color": T_MUTED,
    }
