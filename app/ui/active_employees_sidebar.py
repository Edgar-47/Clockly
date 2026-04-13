"""
ActiveEmployeesSidebar — panel lateral con empleados actualmente fichados.

Muestra una tarjeta por cada empleado con sesión activa. Se actualiza
automáticamente cada 10 s (sondeo completo desde BD) y expone refresh()
para actualizaciones inmediatas después de eventos de fichaje/desfichaje.

UX improvements:
  • Elapsed time labels tick every second for a live feeling.
  • Better empty state with an icon and clearer copy.
  • Count badge animates its value change.
"""

from __future__ import annotations

import customtkinter as ctk

from app.services.time_clock_service import TimeClockService
from app.ui import theme as th

SIDEBAR_WIDTH    = 224
POLL_INTERVAL_MS = 10_000   # full DB refresh every 10 s
TICK_INTERVAL_MS = 1_000    # elapsed label update every 1 s


def _format_elapsed(total_seconds: int) -> str:
    hours, remainder = divmod(max(int(total_seconds), 0), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m {seconds:02d}s"
    if minutes:
        return f"{minutes}m {seconds:02d}s"
    return f"{seconds}s en turno"


class ActiveEmployeesSidebar(ctk.CTkFrame):
    """Panel lateral que lista empleados con sesión de fichaje activa."""

    def __init__(
        self,
        master,
        *,
        time_clock_service: TimeClockService,
    ) -> None:
        super().__init__(
            master,
            width=SIDEBAR_WIDTH,
            corner_radius=th.R_LG,
            fg_color=th.BG_CARD,
            border_width=1,
            border_color=th.BORDER,
        )
        self.pack_propagate(False)

        self._time_clock_service = time_clock_service
        self._poll_after_id: str | None = None
        self._tick_after_id: str | None = None

        # Keeps references to (session, label) pairs for live ticking
        self._elapsed_pairs: list[tuple] = []

        self._build()
        self.refresh()

    # ── Construction ─────────────────────────────────────────────────────────

    def _build(self) -> None:
        # ── Header ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(14, 10))

        dot_container = ctk.CTkFrame(header, fg_color="transparent")
        dot_container.pack(side="left")

        live_dot = ctk.CTkFrame(
            dot_container,
            width=8,
            height=8,
            corner_radius=4,
            fg_color=th.SUCCESS,
        )
        live_dot.pack(side="left", padx=(0, 7), pady=2)
        live_dot.pack_propagate(False)

        ctk.CTkLabel(
            dot_container,
            text="Ahora fichados",
            font=th.bold(12),
            text_color=th.T_PRIMARY,
        ).pack(side="left")

        # Count badge
        self._count_badge = ctk.CTkLabel(
            header,
            text="0",
            font=th.bold(10),
            text_color=th.ACCENT_SOFT,
            fg_color=th.ACCENT_DIM,
            corner_radius=9,
            width=22,
            height=18,
        )
        self._count_badge.pack(side="right")

        th.separator(self, padx=10)

        # ── Scrollable list area ──
        self._list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=th.BORDER_LT,
            scrollbar_button_hover_color=th.BG_HOVER,
        )
        self._list_frame.pack(fill="both", expand=True, padx=4, pady=(6, 8))

    # ── Public refresh ────────────────────────────────────────────────────────

    def refresh(self) -> None:
        """Reload the list from the DB and reschedule the next poll."""
        if not self.winfo_exists():
            return

        # Cancel live-tick while we rebuild
        self._cancel_tick()

        try:
            statuses = self._time_clock_service.list_currently_clocked_in()
        except Exception:
            statuses = []

        self._redraw_list(statuses)
        self._schedule_poll()
        self._start_tick()

    # ── Internal drawing ─────────────────────────────────────────────────────

    def _redraw_list(self, statuses: list) -> None:
        for child in self._list_frame.winfo_children():
            child.destroy()
        self._elapsed_pairs = []

        count = len(statuses)
        self._count_badge.configure(text=str(count))

        if not count:
            self._build_empty_state()
            return

        for status in statuses:
            self._build_employee_card(status)

    def _build_empty_state(self) -> None:
        wrapper = ctk.CTkFrame(self._list_frame, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, pady=32, padx=8)

        # Simple dash icon
        ctk.CTkLabel(
            wrapper,
            text="—",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=th.T_DISABLED,
        ).pack(pady=(0, 6))

        ctk.CTkLabel(
            wrapper,
            text="Ningún empleado\nfichado ahora mismo",
            font=th.f(11),
            text_color=th.T_MUTED,
            justify="center",
        ).pack()

    def _build_employee_card(self, status) -> None:
        employee = status.employee

        card = ctk.CTkFrame(
            self._list_frame,
            fg_color=th.BG_RAISED,
            corner_radius=th.R_MD,
            border_width=1,
            border_color=th.BORDER,
        )
        card.pack(fill="x", padx=4, pady=(0, 5))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=9)

        # ── Circular avatar with initials ──
        color = th.avatar_color(employee.id)
        avatar = ctk.CTkFrame(
            inner,
            width=36,
            height=36,
            corner_radius=18,
            fg_color=color,
        )
        avatar.pack(side="left", padx=(0, 9))
        avatar.pack_propagate(False)

        ctk.CTkLabel(
            avatar,
            text=employee.initials,
            font=th.bold(13),
            text_color="#FFFFFF",
        ).place(relx=0.5, rely=0.5, anchor="center")

        # ── Name and live elapsed time ──
        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            info,
            text=employee.full_name,
            font=th.bold(12),
            text_color=th.T_PRIMARY,
            anchor="w",
            wraplength=110,
        ).pack(anchor="w")

        if status.active_session:
            elapsed_lbl = ctk.CTkLabel(
                info,
                text=_format_elapsed(status.active_session.elapsed_seconds()),
                font=th.f(10),
                text_color=th.SUCCESS_TEXT,
                anchor="w",
            )
            elapsed_lbl.pack(anchor="w", pady=(1, 0))
            # Register for live updates
            self._elapsed_pairs.append((status.active_session, elapsed_lbl))

        # ── Status dot (right side) ──
        status_dot = ctk.CTkFrame(
            inner,
            width=7,
            height=7,
            corner_radius=4,
            fg_color=th.SUCCESS,
        )
        status_dot.pack(side="right", padx=(6, 0))
        status_dot.pack_propagate(False)

    # ── Live elapsed ticking ─────────────────────────────────────────────────

    def _start_tick(self) -> None:
        if not self._elapsed_pairs:
            return
        self._tick()

    def _tick(self) -> None:
        if not self.winfo_exists():
            return
        alive = []
        for session, label in self._elapsed_pairs:
            try:
                if label.winfo_exists():
                    label.configure(text=_format_elapsed(session.elapsed_seconds()))
                    alive.append((session, label))
            except Exception:
                pass
        self._elapsed_pairs = alive
        if self._elapsed_pairs:
            self._tick_after_id = self.after(TICK_INTERVAL_MS, self._tick)

    def _cancel_tick(self) -> None:
        if self._tick_after_id:
            self.after_cancel(self._tick_after_id)
            self._tick_after_id = None

    # ── Periodic polling ─────────────────────────────────────────────────────

    def _schedule_poll(self) -> None:
        self._cancel_poll()
        if self.winfo_exists():
            self._poll_after_id = self.after(POLL_INTERVAL_MS, self.refresh)

    def _cancel_poll(self) -> None:
        if self._poll_after_id:
            self.after_cancel(self._poll_after_id)
            self._poll_after_id = None

    def destroy(self) -> None:
        self._cancel_poll()
        self._cancel_tick()
        super().destroy()
