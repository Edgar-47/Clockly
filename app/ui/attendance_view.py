"""
Attendance view — shown after an employee logs in.

Handles two states without navigating away:
  • Clocked out  → prominent "Fichar" button
  • Clocked in   → active-session timer + prominent "Desfichar" button

"Volver al inicio" is always visible in the header so another employee
can log in immediately without disturbing any active sessions.
"""

from collections.abc import Callable
from tkinter import StringVar

import customtkinter as ctk

from app.models.attendance_session import AttendanceSession
from app.models.employee import Employee
from app.services.time_clock_service import TimeClockService
from app.ui import theme as th
from app.ui.active_employees_sidebar import ActiveEmployeesSidebar
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
        self._pulse_state = False
        self._sidebar: ActiveEmployeesSidebar | None = None
        self._incident_label_to_type = {
            "Sin incidencia": None,
            "Descanso": "descanso",
            "Olvido": "olvido",
            "Correccion manual": "correccion_manual",
            "Otro": "otro",
        }

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
            font=th.bold(11),
            text_color=th.T_SECONDARY,
        )
        self._header_status.pack(side="right", padx=8, pady=20)

        th.separator(self)

    def _build_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # Sidebar (pack primero en la derecha para que el área principal
        # ocupe todo el espacio restante con fill="both", expand=True).
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

        # Área principal (contiene la tarjeta de fichaje centrada)
        main_area = ctk.CTkFrame(body, fg_color="transparent")
        main_area.pack(
            side="left",
            fill="both",
            expand=True,
            padx=th.PAGE_PAD,
            pady=th.PAGE_PAD,
        )

        card = th.card(main_area, width=560, height=620)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.grid_propagate(False)

        # All children of card use grid so we can show/hide rows cleanly.
        card.columnconfigure(0, weight=1)

        row = 0

        # ── Avatar del empleado ──
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

        # ── Nombre del empleado ──
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

        # ── Estado con punto pulsante ──
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

        # ── Hora de entrada (oculta cuando no hay sesión) ──
        self._started_label = ctk.CTkLabel(
            card,
            text="",
            font=th.f(14),
            text_color=th.T_SECONDARY,
        )
        self._started_label.grid(row=row, column=0, sticky="w", padx=28, pady=(0, 4))
        row += 1

        # ── Sección de tiempo transcurrido (oculta cuando no hay sesión) ──
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

        # ── Feedback (errores / confirmaciones) ──
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

        # ── Botón de acción único — reconfigurado según estado ──
        self._action_button = ctk.CTkButton(
            card,
            text="",
            height=52,
            font=th.bold(16),
            corner_radius=th.R_MD,
        )
        self._action_button.grid(row=row, column=0, sticky="ew", padx=28, pady=(0, 28))

    # ── Gestión de estado ──────────────────────────────────────────────────────

    def _apply_state(self) -> None:
        """Actualiza todos los elementos UI según self.attendance_session."""
        self._cancel_timer()
        self._cancel_pulse()
        self._feedback_label.configure(text="", fg_color="transparent")

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

        # Restaura las filas ocultas en el estado "sin fichar".
        self._started_label.grid()
        self._elapsed_frame.grid()

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

        # Oculta filas de sesión — grid_remove() recuerda la posición para restaurar.
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

    # ── Acciones ──────────────────────────────────────────────────────────────

    def _clock_in(self) -> None:
        self._feedback_label.configure(text="", fg_color="transparent")
        self._action_button.configure(state="disabled", text="Registrando...")
        try:
            self.attendance_session = self.on_clock_in()
        except ValueError as exc:
            self._feedback_label.configure(
                text=f"  ✕  {exc}",
                text_color=th.DANGER_TEXT,
                fg_color=th.DANGER_DIM,
            )
            self._action_button.configure(state="normal", text="Fichar")
            return

        self._apply_state()
        if self._sidebar:
            self._sidebar.refresh()
        self._feedback_label.configure(
            text="  ✓  Entrada registrada correctamente.",
            text_color=th.SUCCESS_TEXT,
            fg_color=th.SUCCESS_DIM,
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
            text="Puedes anadir una nota opcional antes de registrar la salida.",
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
        self._feedback_label.configure(text="", fg_color="transparent")
        self._action_button.configure(state="disabled", text="Registrando...")
        try:
            self.attendance_session = self.on_clock_out(exit_note, incident_type)
        except ValueError as exc:
            if status_label is not None:
                status_label.configure(text=f"  ✕  {exc}", text_color=th.DANGER_TEXT)
            self._feedback_label.configure(
                text=f"  ✕  {exc}",
                text_color=th.DANGER_TEXT,
                fg_color=th.DANGER_DIM,
            )
            self._action_button.configure(state="normal", text="Desfichar")
            return

        if dialog is not None:
            dialog.destroy()
        self._apply_state()
        if self._sidebar:
            self._sidebar.refresh()
        self._feedback_label.configure(
            text="  ✓  Salida registrada. Puedes volver al inicio o fichar de nuevo.",
            text_color=th.SUCCESS_TEXT,
            fg_color=th.SUCCESS_DIM,
        )

    # ── Temporizador ─────────────────────────────────────────────────────────

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

    # ── Animación de pulso del punto de estado ────────────────────────────────

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
        super().destroy()

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _format_seconds(total_seconds: int) -> str:
        hours, remainder = divmod(max(int(total_seconds), 0), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
