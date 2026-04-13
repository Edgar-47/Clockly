"""
Attendance view — shown after an employee logs in.

Handles two states without navigating away:
  • Clocked out  → prominent "Fichar" button
  • Clocked in   → active-session timer + prominent "Desfichar" button

"Cambiar usuario" is always visible in the header so another employee
can log in immediately without disturbing any active sessions.

UX improvements:
  • Live clock in header so employees always see current time.
  • Card border turns green when clocked in for immediate visual state.
  • Feedback messages auto-dismiss after 5 s.
  • Clock-out success message shows worked duration.
  • "Sin fichar" state shows a subtle prompt.
"""

from collections.abc import Callable
from tkinter import StringVar
import datetime

import customtkinter as ctk

from app.models.attendance_session import AttendanceSession
from app.models.employee import Employee
from app.services.time_clock_service import TimeClockService
from app.ui import theme as th
from app.ui.active_employees_sidebar import ActiveEmployeesSidebar
from app.utils.helpers import format_timestamp

_FEEDBACK_DISMISS_MS = 5_000   # how long success/error banners stay visible


class AttendanceView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        employee: Employee,
        attendance_session: AttendanceSession | None,
        time_clock_service: TimeClockService,
        on_clock_in: Callable[[], AttendanceSession],
        on_clock_out: Callable[[str | None, str | None], AttendanceSession],
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
        self._pulse_after_id: str | None = None
        self._clock_after_id: str | None = None
        self._feedback_after_id: str | None = None
        self._pulse_state = False
        self._sidebar: ActiveEmployeesSidebar | None = None
        self._card_frame: ctk.CTkFrame | None = None
        self._incident_label_to_type = {
            "Sin incidencia": None,
            "Descanso": "descanso",
            "Olvido": "olvido",
            "Correccion manual": "correccion_manual",
            "Otro": "otro",
        }

        self._build()
        self._apply_state()
        self._tick_clock()

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

        # Right side: live clock + back button
        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right", padx=22, pady=10)

        # "Cambiar usuario" is clearer than "Volver al inicio"
        ctk.CTkButton(
            right,
            text="Cambiar usuario",
            width=140,
            height=36,
            font=th.f(12),
            **th.quiet_button_kwargs(),
            command=self.on_return_to_login,
        ).pack(side="right", padx=(10, 0))

        # Live clock — always visible so employees know the time
        clock_block = ctk.CTkFrame(right, fg_color="transparent")
        clock_block.pack(side="right")

        self._live_clock_label = ctk.CTkLabel(
            clock_block,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=th.T_PRIMARY,
            anchor="e",
        )
        self._live_clock_label.pack(anchor="e")

        self._live_date_label = ctk.CTkLabel(
            clock_block,
            text="",
            font=th.f(10),
            text_color=th.T_MUTED,
            anchor="e",
        )
        self._live_date_label.pack(anchor="e")

        self._header_status = ctk.CTkLabel(
            bar,
            text="",
            font=th.bold(11),
            text_color=th.T_SECONDARY,
        )
        self._header_status.pack(side="right", padx=8, pady=20)

        th.separator(self)

    def _build_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # Sidebar (packed right first so main area fills remaining space)
        self._sidebar = ActiveEmployeesSidebar(
            body,
            time_clock_service=self.time_clock_service,
        )
        self._sidebar.pack(
            side="right",
            fill="y",
            padx=(0, th.PAGE_PAD),
            pady=th.PAGE_PAD,
        )

        # Main area (centered clock card)
        main_area = ctk.CTkFrame(body, fg_color="transparent")
        main_area.pack(
            side="left",
            fill="both",
            expand=True,
            padx=th.PAGE_PAD,
            pady=th.PAGE_PAD,
        )

        # Card — border_color updated on state change for visual state cue
        card = th.card(main_area, width=560, height=620)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.grid_propagate(False)
        self._card_frame = card

        # All children use grid so we can show/hide rows cleanly.
        card.columnconfigure(0, weight=1)

        row = 0

        # ── Employee avatar row ──
        avatar_row = ctk.CTkFrame(card, fg_color="transparent")
        avatar_row.grid(row=row, column=0, sticky="w", padx=28, pady=(28, 16))

        avatar_bg = th.avatar_color(self.employee.id)
        avatar = ctk.CTkFrame(avatar_row, width=52, height=52, corner_radius=26, fg_color=avatar_bg)
        avatar.pack(side="left")
        avatar.pack_propagate(False)
        ctk.CTkLabel(
            avatar,
            text=self.employee.initials,
            font=th.bold(18),
            text_color="#FFFFFF",
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            avatar_row,
            text="Fichaje de asistencia",
            font=th.bold(10),
            text_color=th.ACCENT_SOFT,
            fg_color=th.ACCENT_DIM,
            corner_radius=th.R_SM,
        ).pack(side="left", padx=(14, 0), ipadx=10, ipady=4)
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
        ).grid(row=row, column=0, sticky="w", padx=28, pady=(0, 20))
        row += 1

        # ── Status row with pulsing dot ──
        status_row = ctk.CTkFrame(card, fg_color="transparent")
        status_row.grid(row=row, column=0, sticky="w", padx=28, pady=(0, 8))

        self._status_dot = ctk.CTkFrame(
            status_row,
            width=10,
            height=10,
            corner_radius=5,
            fg_color=th.T_DISABLED,
        )
        self._status_dot.pack(side="left", padx=(0, 9))
        self._status_dot.pack_propagate(False)

        self._status_label = ctk.CTkLabel(
            status_row,
            text="",
            font=th.bold(17),
            text_color=th.T_SECONDARY,
        )
        self._status_label.pack(side="left")
        row += 1

        # ── Entry timestamp (hidden when not clocked in) ──
        self._started_label = ctk.CTkLabel(
            card,
            text="",
            font=th.f(14),
            text_color=th.T_SECONDARY,
        )
        self._started_label.grid(row=row, column=0, sticky="w", padx=28, pady=(0, 4))
        row += 1

        # ── Elapsed time section (hidden when not clocked in) ──
        elapsed_frame = ctk.CTkFrame(card, fg_color="transparent")
        elapsed_frame.grid(row=row, column=0, sticky="ew", padx=28, pady=(0, 14))
        elapsed_frame.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            elapsed_frame,
            text="Tiempo en turno",
            font=th.bold(10),
            text_color=th.T_MUTED,
        ).pack(anchor="w")

        self._elapsed_label = ctk.CTkLabel(
            elapsed_frame,
            text="00:00:00",
            font=ctk.CTkFont(family="Segoe UI", size=56, weight="bold"),
            text_color=th.T_PRIMARY,
        )
        self._elapsed_label.pack(anchor="w", pady=(3, 0))
        self._elapsed_frame = elapsed_frame
        row += 1

        # ── Feedback banner (success / error) ──
        self._feedback_label = ctk.CTkLabel(
            card,
            text="",
            font=th.f(12),
            text_color=th.DANGER_TEXT,
            fg_color="transparent",
            wraplength=500,
            corner_radius=th.R_SM,
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

    # ── Live clock ────────────────────────────────────────────────────────────

    _DAY_NAMES = [
        "lunes", "martes", "miércoles", "jueves",
        "viernes", "sábado", "domingo",
    ]
    _MONTH_NAMES = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ]

    def _tick_clock(self) -> None:
        if not self.winfo_exists():
            return
        now = datetime.datetime.now()
        self._live_clock_label.configure(text=now.strftime("%H:%M:%S"))
        day   = self._DAY_NAMES[now.weekday()]
        month = self._MONTH_NAMES[now.month - 1]
        self._live_date_label.configure(text=f"{day}, {now.day} de {month}")
        self._clock_after_id = self.after(1000, self._tick_clock)

    # ── State management ──────────────────────────────────────────────────────

    def _apply_state(self) -> None:
        """Update all UI elements according to self.attendance_session."""
        self._cancel_timer()
        self._cancel_pulse()
        self._clear_feedback()

        if self.attendance_session and self.attendance_session.is_active:
            self._show_clocked_in()
        else:
            self._show_clocked_out()

    def _show_clocked_in(self) -> None:
        self._header_status.configure(text="Fichado", text_color=th.SUCCESS_TEXT)
        self._status_label.configure(text="Fichado", text_color=th.SUCCESS_TEXT)
        self._status_dot.configure(fg_color=th.SUCCESS)
        self._started_label.configure(
            text=f"Entrada: {format_timestamp(self.attendance_session.clock_in_time)}"
        )

        # Restore rows hidden in clocked-out state
        self._started_label.grid()
        self._elapsed_frame.grid()

        # Green border signals active shift at a glance
        if self._card_frame:
            self._card_frame.configure(border_color=th.SUCCESS)

        self._action_button.configure(
            text="Desfichar",
            fg_color=th.DANGER,
            hover_color=th.DANGER_HOVER,
            text_color="#FFFFFF",
            state="normal",
            command=self._open_clock_out_dialog,
        )

        self._tick_elapsed()
        self._start_pulse()

    def _show_clocked_out(self) -> None:
        self._header_status.configure(text="Sin fichar", text_color=th.T_SECONDARY)
        self._status_label.configure(text="Sin fichar", text_color=th.T_SECONDARY)
        self._status_dot.configure(fg_color=th.T_DISABLED)
        self._started_label.configure(text="")

        # Hide session rows — grid_remove() remembers position for restore
        self._started_label.grid_remove()
        self._elapsed_frame.grid_remove()

        # Reset card border to neutral
        if self._card_frame:
            self._card_frame.configure(border_color=th.BORDER)

        self._action_button.configure(
            text="Fichar entrada",
            fg_color=th.SUCCESS,
            hover_color=th.SUCCESS_HOVER,
            text_color="#071B10",
            state="normal",
            command=self._clock_in,
        )

    # ── Actions ───────────────────────────────────────────────────────────────

    def _clock_in(self) -> None:
        self._clear_feedback()
        self._action_button.configure(state="disabled", text="Registrando...")
        try:
            self.attendance_session = self.on_clock_in()
        except ValueError as exc:
            self._show_feedback(f"  ✕  {exc}", th.DANGER_TEXT, th.DANGER_DIM)
            self._action_button.configure(state="normal", text="Fichar entrada")
            return

        self._apply_state()
        if self._sidebar:
            self._sidebar.refresh()
        self._show_feedback(
            "  ✓  Entrada registrada correctamente.",
            th.SUCCESS_TEXT,
            th.SUCCESS_DIM,
        )

    def _open_clock_out_dialog(self) -> None:
        dlg = ctk.CTkToplevel(self)
        dlg.title("Desfichar")
        dlg.geometry("460x360")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.configure(fg_color=th.BG_CARD)
        dlg.focus_force()

        ctk.CTkLabel(
            dlg,
            text="Cerrar turno",
            font=th.bold(18),
            text_color=th.T_PRIMARY,
        ).pack(anchor="w", padx=22, pady=(22, 2))
        ctk.CTkLabel(
            dlg,
            text="Puedes añadir una nota opcional antes de registrar la salida.",
            font=th.f(12),
            text_color=th.T_SECONDARY,
            wraplength=400,
            justify="left",
        ).pack(anchor="w", padx=22, pady=(0, 16))
        th.separator(dlg, padx=22, pady=(0, 14))

        ctk.CTkLabel(
            dlg,
            text="TIPO",
            font=th.bold(9),
            text_color=th.T_MUTED,
            anchor="w",
        ).pack(fill="x", padx=22)
        incident_var = StringVar(value="Sin incidencia")
        ctk.CTkComboBox(
            dlg,
            height=38,
            font=th.f(13),
            values=list(self._incident_label_to_type.keys()),
            variable=incident_var,
            fg_color=th.BG_FIELD,
            border_color=th.BORDER_LT,
            border_width=1,
            button_color=th.BORDER_LT,
            button_hover_color=th.BG_HOVER,
            dropdown_fg_color=th.BG_CARD,
            dropdown_text_color=th.T_PRIMARY,
            text_color=th.T_PRIMARY,
            corner_radius=th.R_MD,
        ).pack(fill="x", padx=22, pady=(4, 12))

        ctk.CTkLabel(
            dlg,
            text="NOTA OPCIONAL",
            font=th.bold(9),
            text_color=th.T_MUTED,
            anchor="w",
        ).pack(fill="x", padx=22)
        note_entry = ctk.CTkEntry(
            dlg,
            height=38,
            font=th.f(13),
            placeholder_text="Ej. descanso, olvido, ajuste operativo",
            **th.entry_kwargs(),
        )
        note_entry.pack(fill="x", padx=22, pady=(4, 8))

        status_lbl = ctk.CTkLabel(
            dlg,
            text="",
            font=th.f(11),
            text_color=th.DANGER_TEXT,
            fg_color="transparent",
            wraplength=400,
        )
        status_lbl.pack(fill="x", padx=22, pady=(0, 8))

        def _confirm() -> None:
            incident_type = self._incident_label_to_type.get(incident_var.get())
            self._clock_out(
                exit_note=note_entry.get(),
                incident_type=incident_type,
                dialog=dlg,
                status_label=status_lbl,
            )

        ctk.CTkButton(
            dlg,
            text="Confirmar salida",
            height=42,
            font=th.bold(13),
            fg_color=th.DANGER,
            hover_color=th.DANGER_HOVER,
            text_color="#FFFFFF",
            corner_radius=th.R_MD,
            command=_confirm,
        ).pack(fill="x", padx=22, pady=(2, 6))

        ctk.CTkButton(
            dlg,
            text="Cancelar",
            height=36,
            font=th.f(12),
            **th.quiet_button_kwargs(),
            command=dlg.destroy,
        ).pack(fill="x", padx=22)

        note_entry.focus()
        dlg.bind("<Return>", lambda _: _confirm())
        dlg.bind("<Escape>", lambda _: dlg.destroy())

    def _clock_out(
        self,
        *,
        exit_note: str | None = None,
        incident_type: str | None = None,
        dialog: ctk.CTkToplevel | None = None,
        status_label: ctk.CTkLabel | None = None,
    ) -> None:
        self._clear_feedback()
        self._action_button.configure(state="disabled", text="Registrando...")
        try:
            closed_session = self.on_clock_out(exit_note, incident_type)
        except ValueError as exc:
            if status_label is not None:
                status_label.configure(text=f"  ✕  {exc}", text_color=th.DANGER_TEXT)
            self._show_feedback(f"  ✕  {exc}", th.DANGER_TEXT, th.DANGER_DIM)
            self._action_button.configure(state="normal", text="Desfichar")
            return

        self.attendance_session = closed_session
        if dialog is not None:
            dialog.destroy()
        self._apply_state()
        if self._sidebar:
            self._sidebar.refresh()

        # Show worked duration in the success message
        duration_text = ""
        try:
            secs = closed_session.total_seconds or 0
            h, rem = divmod(max(int(secs), 0), 3600)
            m = rem // 60
            if h:
                duration_text = f" Turno: {h}h {m:02d}m."
            else:
                duration_text = f" Turno: {m}m."
        except Exception:
            pass

        self._show_feedback(
            f"  ✓  Salida registrada.{duration_text} Puedes cambiar de usuario.",
            th.SUCCESS_TEXT,
            th.SUCCESS_DIM,
        )

    # ── Feedback helpers ──────────────────────────────────────────────────────

    def _show_feedback(self, message: str, text_color: str, bg: str) -> None:
        """Show a status message that auto-dismisses after _FEEDBACK_DISMISS_MS."""
        if self._feedback_after_id:
            self.after_cancel(self._feedback_after_id)
            self._feedback_after_id = None
        self._feedback_label.configure(
            text=message,
            text_color=text_color,
            fg_color=bg,
        )
        self._feedback_after_id = self.after(
            _FEEDBACK_DISMISS_MS, self._clear_feedback
        )

    def _clear_feedback(self) -> None:
        if self._feedback_after_id:
            self.after_cancel(self._feedback_after_id)
            self._feedback_after_id = None
        if self.winfo_exists():
            self._feedback_label.configure(text="", fg_color="transparent")

    # ── Elapsed timer ─────────────────────────────────────────────────────────

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

    # ── Status dot pulse animation ────────────────────────────────────────────

    def _start_pulse(self) -> None:
        self._cancel_pulse()
        self._pulse_state = False
        self._pulse_tick()

    def _pulse_tick(self) -> None:
        if not self.winfo_exists():
            return
        if not self.attendance_session or not self.attendance_session.is_active:
            return
        self._pulse_state = not self._pulse_state
        color = th.SUCCESS if self._pulse_state else "#1A5C35"
        self._status_dot.configure(fg_color=color)
        self._pulse_after_id = self.after(900, self._pulse_tick)

    def _cancel_pulse(self) -> None:
        if self._pulse_after_id:
            self.after_cancel(self._pulse_after_id)
            self._pulse_after_id = None

    def destroy(self) -> None:
        self._cancel_timer()
        self._cancel_pulse()
        if self._clock_after_id:
            self.after_cancel(self._clock_after_id)
            self._clock_after_id = None
        if self._feedback_after_id:
            self.after_cancel(self._feedback_after_id)
            self._feedback_after_id = None
        super().destroy()

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _format_seconds(total_seconds: int) -> str:
        hours, remainder = divmod(max(int(total_seconds), 0), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
