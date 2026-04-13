"""
Attendance view — shown after an employee logs in.

Handles two states without navigating away:
  • Clocked out  → prominent "Fichar" button
  • Clocked in   → active-session timer + prominent "Desfichar" button

"Volver al inicio" is always visible in the header so another employee
can log in immediately without disturbing any active sessions.
"""

from collections.abc import Callable

import customtkinter as ctk

from app.models.attendance_session import AttendanceSession
from app.models.employee import Employee
from app.services.time_clock_service import TimeClockService
from app.ui import theme as th
from app.utils.helpers import format_timestamp


class AttendanceView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        employee: Employee,
        attendance_session: AttendanceSession | None,
        time_clock_service: TimeClockService,
        on_clock_in: Callable[[], AttendanceSession],
        on_clock_out: Callable[[], AttendanceSession],
        on_return_to_login: Callable[[], None],
    ) -> None:
        super().__init__(master, corner_radius=0, fg_color=th.BG_ROOT)
        self.employee = employee
        self.attendance_session = attendance_session
        self.time_clock_service = time_clock_service
        self.on_clock_in = on_clock_in
        self.on_clock_out = on_clock_out
        self.on_return_to_login = on_return_to_login
        self._timer_after_id: str | None = None

        self._build()
        self._apply_state()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self._build_header()
        self._build_body()

    def _build_header(self) -> None:
        bar = ctk.CTkFrame(self, height=64, corner_radius=0, fg_color=th.BG_CARD)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        brand = ctk.CTkFrame(bar, fg_color="transparent")
        brand.pack(side="left", padx=22, pady=13)

        ctk.CTkLabel(
            brand,
            text="",
            image=th.logo_mark(size=(34, 34)),
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            brand,
            text="CLOCKLY",
            font=th.bold(13),
            text_color=th.T_PRIMARY,
        ).pack(side="left")

        # Always-visible: lets another employee navigate to login right away.
        ctk.CTkButton(
            bar,
            text="Volver al inicio",
            width=140,
            height=36,
            font=th.f(12),
            **th.quiet_button_kwargs(),
            command=self.on_return_to_login,
        ).pack(side="right", padx=22, pady=14)

        self._header_status = ctk.CTkLabel(
            bar,
            text="",
            font=th.bold(12),
            text_color=th.T_SECONDARY,
        )
        self._header_status.pack(side="right", padx=8, pady=20)

        th.separator(self)

    def _build_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=th.PAGE_PAD, pady=th.PAGE_PAD)

        card = th.card(body, width=560, height=580)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.grid_propagate(False)

        # All children of card use grid so we can show/hide rows cleanly.
        card.columnconfigure(0, weight=1)

        row = 0

        # ── Badge ──
        ctk.CTkLabel(
            card,
            text="Fichaje de asistencia",
            font=th.bold(11),
            text_color=th.ACCENT_SOFT,
            fg_color=th.ACCENT_DIM,
            corner_radius=th.R_SM,
        ).grid(row=row, column=0, sticky="w", padx=28, pady=(28, 16), ipadx=10, ipady=4)
        row += 1

        # ── Employee name ──
        ctk.CTkLabel(
            card,
            text=self.employee.full_name,
            font=th.bold(30),
            text_color=th.T_PRIMARY,
        ).grid(row=row, column=0, sticky="w", padx=28, pady=(0, 4))
        row += 1

        # ── DNI ──
        ctk.CTkLabel(
            card,
            text=f"DNI: {self.employee.dni}",
            font=th.f(13),
            text_color=th.T_SECONDARY,
        ).grid(row=row, column=0, sticky="w", padx=28, pady=(0, 22))
        row += 1

        # ── Attendance status (Fichado / Sin fichar) ──
        self._status_label = ctk.CTkLabel(
            card,
            text="",
            font=th.bold(18),
            text_color=th.T_SECONDARY,
        )
        self._status_label.grid(row=row, column=0, sticky="w", padx=28, pady=(0, 8))
        row += 1

        # ── Session start time (hidden when clocked out) ──
        self._started_label = ctk.CTkLabel(
            card,
            text="",
            font=th.f(14),
            text_color=th.T_SECONDARY,
        )
        self._started_label.grid(row=row, column=0, sticky="w", padx=28, pady=(0, 4))
        row += 1

        # ── Elapsed time section (hidden when clocked out) ──
        elapsed_frame = ctk.CTkFrame(card, fg_color="transparent")
        elapsed_frame.grid(row=row, column=0, sticky="ew", padx=28, pady=(0, 16))
        elapsed_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            elapsed_frame,
            text="Tiempo en turno",
            font=th.bold(11),
            text_color=th.T_MUTED,
        ).pack(anchor="w")

        self._elapsed_label = ctk.CTkLabel(
            elapsed_frame,
            text="00:00:00",
            font=ctk.CTkFont(family="Segoe UI", size=58, weight="bold"),
            text_color=th.T_PRIMARY,
        )
        self._elapsed_label.pack(anchor="w", pady=(4, 0))
        self._elapsed_frame = elapsed_frame
        row += 1

        # ── Feedback (errors / confirmations) ──
        self._feedback_label = ctk.CTkLabel(
            card,
            text="",
            font=th.f(13),
            text_color=th.DANGER_TEXT,
            wraplength=500,
        )
        self._feedback_label.grid(row=row, column=0, sticky="ew", padx=28, pady=(0, 8))
        row += 1

        # ── Single action button — reconfigured per state ──
        self._action_button = ctk.CTkButton(
            card,
            text="",
            height=52,
            font=th.bold(16),
            corner_radius=th.R_MD,
        )
        self._action_button.grid(row=row, column=0, sticky="ew", padx=28, pady=(0, 28))

    # ── State management ──────────────────────────────────────────────────────

    def _apply_state(self) -> None:
        """Update every UI element to match self.attendance_session."""
        self._cancel_timer()
        self._feedback_label.configure(text="")

        if self.attendance_session and self.attendance_session.is_active:
            self._show_clocked_in()
        else:
            self._show_clocked_out()

    def _show_clocked_in(self) -> None:
        self._header_status.configure(text="Fichado", text_color=th.SUCCESS_TEXT)
        self._status_label.configure(text="Fichado", text_color=th.SUCCESS_TEXT)
        self._started_label.configure(
            text=f"Entrada: {format_timestamp(self.attendance_session.clock_in_time)}"
        )

        # Restore rows that were hidden in clocked-out state.
        self._started_label.grid()
        self._elapsed_frame.grid()

        self._action_button.configure(
            text="Desfichar",
            fg_color=th.DANGER,
            hover_color=th.DANGER_HOVER,
            text_color="#FFFFFF",
            state="normal",
            command=self._clock_out,
        )

        self._tick_elapsed()

    def _show_clocked_out(self) -> None:
        self._header_status.configure(text="Sin fichar", text_color=th.T_SECONDARY)
        self._status_label.configure(text="Sin fichar", text_color=th.T_SECONDARY)
        self._started_label.configure(text="")

        # Hide session-specific rows — grid_remove() remembers position for later restore.
        self._started_label.grid_remove()
        self._elapsed_frame.grid_remove()

        self._action_button.configure(
            text="Fichar",
            fg_color=th.SUCCESS,
            hover_color=th.SUCCESS_HOVER,
            text_color="#071B10",
            state="normal",
            command=self._clock_in,
        )

    # ── Actions ───────────────────────────────────────────────────────────────

    def _clock_in(self) -> None:
        self._feedback_label.configure(text="")
        self._action_button.configure(state="disabled", text="Registrando...")
        try:
            self.attendance_session = self.on_clock_in()
        except ValueError as exc:
            self._feedback_label.configure(text=str(exc), text_color=th.DANGER_TEXT)
            self._action_button.configure(state="normal", text="Fichar")
            return

        self._apply_state()
        self._feedback_label.configure(
            text="Entrada registrada correctamente.",
            text_color=th.SUCCESS_TEXT,
        )

    def _clock_out(self) -> None:
        self._feedback_label.configure(text="")
        self._action_button.configure(state="disabled", text="Registrando...")
        try:
            self.attendance_session = self.on_clock_out()
        except ValueError as exc:
            self._feedback_label.configure(text=str(exc), text_color=th.DANGER_TEXT)
            self._action_button.configure(state="normal", text="Desfichar")
            return

        self._apply_state()
        self._feedback_label.configure(
            text="Salida registrada. Puedes volver al inicio o fichar de nuevo.",
            text_color=th.SUCCESS_TEXT,
        )

    # ── Timer ─────────────────────────────────────────────────────────────────

    def _tick_elapsed(self) -> None:
        if not self.winfo_exists():
            return
        if not self.attendance_session or not self.attendance_session.is_active:
            return
        elapsed = self.attendance_session.elapsed_seconds()
        self._elapsed_label.configure(text=self._format_seconds(elapsed))
        self._timer_after_id = self.after(1000, self._tick_elapsed)

    def _cancel_timer(self) -> None:
        if self._timer_after_id:
            self.after_cancel(self._timer_after_id)
            self._timer_after_id = None

    def destroy(self) -> None:
        self._cancel_timer()
        super().destroy()

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _format_seconds(total_seconds: int) -> str:
        hours, remainder = divmod(max(int(total_seconds), 0), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
