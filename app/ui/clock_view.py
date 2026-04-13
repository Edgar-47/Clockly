"""
Employee clock-in / clock-out view — premium kiosk style.

Layout
──────
  • Fixed header bar: app badge (left) + employee name (right) + logout
  • Centred content: digital clock card → date → last-action badge → action buttons
  • Inline feedback label: errors from the service appear here; no modal popups.

The two action buttons are custom frames (not CTkButton) so they support
a bold main label + a smaller subtitle label with different visual weights.

ValueError raised by on_register() is caught here and displayed inline.
"""

from collections.abc import Callable
from datetime import datetime

import customtkinter as ctk

from app.models.employee import Employee
from app.services.time_clock_service import TimeClockService
from app.ui import theme as th
from app.utils.helpers import format_timestamp


class ClockView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        employee: Employee,
        time_clock_service: TimeClockService,
        on_register: Callable[[str], None],
        on_logout: Callable[[], None],
    ) -> None:
        super().__init__(master, corner_radius=0, fg_color=th.BG_ROOT)
        self.employee = employee
        self.time_clock_service = time_clock_service
        self.on_register = on_register
        self.on_logout = on_logout

        self._build()
        self._refresh_status()
        self._tick()

    # ═════════════════════════════════════════════════════════════════════════
    # Build
    # ═════════════════════════════════════════════════════════════════════════

    def _build(self) -> None:
        self._build_header()
        self._build_body()

    # ── Header bar ────────────────────────────────────────────────────────────

    def _build_header(self) -> None:
        bar = ctk.CTkFrame(self, height=58, corner_radius=0, fg_color=th.BG_CARD)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # Left: coloured dot + app name
        brand = ctk.CTkFrame(bar, fg_color="transparent")
        brand.pack(side="left", padx=20, pady=0)
        brand.pack_propagate(False)

        ctk.CTkFrame(
            brand, width=10, height=10, corner_radius=5, fg_color=th.ACCENT
        ).pack(side="left", padx=(0, 8), pady=24)

        ctk.CTkLabel(
            brand,
            text="FICHAJE RESTAURANTE",
            font=th.bold(11),
            text_color=th.T_SECONDARY,
        ).pack(side="left", pady=20)

        # Right: logout button
        ctk.CTkButton(
            bar,
            text="Cerrar sesión",
            width=140,
            height=34,
            font=th.f(12),
            fg_color="transparent",
            hover_color=th.BG_RAISED,
            border_width=1,
            border_color=th.BORDER_LT,
            text_color=th.T_SECONDARY,
            corner_radius=th.R_SM,
            command=self.on_logout,
        ).pack(side="right", padx=20, pady=12)

        # 1-px separator at bottom of header
        th.separator(self)

    # ── Main body ─────────────────────────────────────────────────────────────

    def _build_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # All content is centred in a fixed-width column
        col = ctk.CTkFrame(body, fg_color="transparent", width=560)
        col.place(relx=0.5, rely=0.5, anchor="center")
        col.pack_propagate(False)

        # ── Employee greeting ─────────────────────────────────────────────────
        self._greeting_lbl = ctk.CTkLabel(
            col,
            text="",
            font=th.f(16),
            text_color=th.T_SECONDARY,
        )
        self._greeting_lbl.pack(pady=(0, 4))

        ctk.CTkLabel(
            col,
            text=self.employee.name,
            font=th.bold(22),
            text_color=th.T_PRIMARY,
        ).pack(pady=(0, 24))

        # ── Digital clock card ────────────────────────────────────────────────
        clock_card = ctk.CTkFrame(
            col,
            fg_color=th.BG_CARD,
            corner_radius=th.R_LG,
            border_width=1,
            border_color=th.BORDER_LT,
        )
        clock_card.pack(fill="x", pady=(0, 10))

        self._clock_lbl = ctk.CTkLabel(
            clock_card,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=68, weight="bold"),
            text_color=th.T_PRIMARY,
        )
        self._clock_lbl.pack(pady=(22, 18))

        # ── Date ──────────────────────────────────────────────────────────────
        self._date_lbl = ctk.CTkLabel(
            col,
            text="",
            font=th.f(15),
            text_color=th.T_SECONDARY,
        )
        self._date_lbl.pack(pady=(0, 18))

        # ── Last-action badge ─────────────────────────────────────────────────
        self._badge_frame = ctk.CTkFrame(
            col,
            fg_color=th.BG_CARD,
            corner_radius=th.R_XL,
            border_width=1,
            border_color=th.BORDER,
        )
        self._badge_frame.pack(pady=(0, 32))

        self._badge_dot = ctk.CTkFrame(
            self._badge_frame,
            width=8, height=8,
            corner_radius=4,
            fg_color=th.T_MUTED,
        )
        self._badge_dot.pack(side="left", padx=(14, 6), pady=10)
        self._badge_dot.pack_propagate(False)

        self._badge_lbl = ctk.CTkLabel(
            self._badge_frame,
            text="Sin fichajes previos",
            font=th.f(13),
            text_color=th.T_SECONDARY,
        )
        self._badge_lbl.pack(side="left", padx=(0, 14), pady=10)

        # ── Action buttons ────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(col, fg_color="transparent")
        btn_row.pack(pady=(0, 16))

        self._btn_entrada = _ActionButton(
            btn_row,
            label="ENTRADA",
            sublabel="Registrar inicio de turno",
            bg=th.SUCCESS,
            bg_hover=th.SUCCESS_HOVER,
            sub_color="#A7F3D0",
            command=lambda: self._handle_action(TimeClockService.ENTRY),
        )
        self._btn_entrada.grid(row=0, column=0, padx=(0, 16))

        self._btn_salida = _ActionButton(
            btn_row,
            label="SALIDA",
            sublabel="Registrar fin de turno",
            bg=th.DANGER,
            bg_hover=th.DANGER_HOVER,
            sub_color="#FECACA",
            command=lambda: self._handle_action(TimeClockService.EXIT),
        )
        self._btn_salida.grid(row=0, column=1, padx=(16, 0))

        # ── Inline feedback ───────────────────────────────────────────────────
        self._feedback_lbl = ctk.CTkLabel(
            col,
            text="",
            font=th.f(13),
            text_color=th.DANGER_TEXT,
            wraplength=520,
        )
        self._feedback_lbl.pack()

    # ═════════════════════════════════════════════════════════════════════════
    # Clock tick
    # ═════════════════════════════════════════════════════════════════════════

    def _tick(self) -> None:
        now = datetime.now()
        self._clock_lbl.configure(text=now.strftime("%H:%M:%S"))
        self._date_lbl.configure(text=now.strftime("%A, %d de %B de %Y").capitalize())
        self._update_greeting(now.hour)
        self.after(1000, self._tick)

    def _update_greeting(self, hour: int) -> None:
        if hour < 12:
            greeting = "Buenos días,"
        elif hour < 20:
            greeting = "Buenas tardes,"
        else:
            greeting = "Buenas noches,"
        self._greeting_lbl.configure(text=greeting)

    # ═════════════════════════════════════════════════════════════════════════
    # Status badge
    # ═════════════════════════════════════════════════════════════════════════

    def _refresh_status(self) -> None:
        active = self.time_clock_service.get_active_session(self.employee.id)
        if active:
            self._badge_dot.configure(fg_color=th.SUCCESS)
            self._badge_lbl.configure(
                text=f"Turno activo desde {format_timestamp(active.clock_in_time)}",
                text_color=th.T_PRIMARY,
            )
            return

        latest = (
            self.time_clock_service.attendance_session_repository.get_latest_for_user(
                self.employee.id
            )
        )
        if latest and latest.clock_out_time:
            self._badge_dot.configure(fg_color=th.DANGER)
            self._badge_lbl.configure(
                text=f"Ultima salida: {format_timestamp(latest.clock_out_time)}",
                text_color=th.T_PRIMARY,
            )
            return

        self._badge_dot.configure(fg_color=th.T_MUTED)
        self._badge_lbl.configure(
            text="Sin fichajes previos",
            text_color=th.T_SECONDARY,
        )

    # ═════════════════════════════════════════════════════════════════════════
    # Button action
    # ═════════════════════════════════════════════════════════════════════════

    def _handle_action(self, entry_type: str) -> None:
        """Call the app-layer callback; catch service errors and show inline."""
        self._feedback_lbl.configure(text="")
        try:
            self.on_register(entry_type)
            # on success the app calls show_clock(), destroying this view – nothing more needed here.
        except ValueError as exc:
            self._feedback_lbl.configure(text=str(exc), text_color=th.DANGER_TEXT)


# ─────────────────────────────────────────────────────────────────────────────
# Custom action button (multi-line, hover-aware)
# ─────────────────────────────────────────────────────────────────────────────

class _ActionButton(ctk.CTkFrame):
    """
    A 240×120 clickable frame that displays a bold main label and a smaller
    subtitle. Hover changes the background; cursor shows a pointer hand.
    """

    def __init__(
        self,
        master,
        *,
        label: str,
        sublabel: str,
        bg: str,
        bg_hover: str,
        sub_color: str,
        command: Callable[[], None],
    ) -> None:
        super().__init__(
            master,
            width=240,
            height=120,
            corner_radius=th.R_LG,
            fg_color=bg,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

        self._bg = bg
        self._bg_hover = bg_hover
        self._cmd = command

        lbl_main = ctk.CTkLabel(
            self,
            text=label,
            font=th.bold(24),
            text_color="#FFFFFF",
            fg_color="transparent",
        )
        lbl_main.pack(expand=True, pady=(22, 2))

        lbl_sub = ctk.CTkLabel(
            self,
            text=sublabel,
            font=th.f(11),
            text_color=sub_color,
            fg_color="transparent",
        )
        lbl_sub.pack(pady=(0, 18))

        # Bind all three layers so hover/click works wherever the mouse lands
        for widget in (self, lbl_main, lbl_sub):
            widget.bind("<Enter>",    lambda _: self.configure(fg_color=self._bg_hover))
            widget.bind("<Leave>",    lambda _: self.configure(fg_color=self._bg))
            widget.bind("<Button-1>", lambda _: self._cmd())
            widget.configure(cursor="hand2")
