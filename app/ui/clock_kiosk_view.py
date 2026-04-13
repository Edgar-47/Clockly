"""
Public employee clock-in / clock-out kiosk.

The main screen shows active employees as visual profile cards. Staff members
select their profile, enter their password, choose Entrada or Salida, and the
existing service layer records the attendance entry.
"""

from collections.abc import Callable
from datetime import datetime

import customtkinter as ctk

from app.models.employee import Employee
from app.services.employee_service import EmployeeService
from app.services.time_clock_service import TimeClockService
from app.ui import theme as th
from app.utils.helpers import format_timestamp


class ClockKioskView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        employee_service: EmployeeService,
        time_clock_service: TimeClockService,
        on_register: Callable[[int, str, str], str],
        on_admin_login: Callable[[], None],
    ) -> None:
        super().__init__(master, corner_radius=0, fg_color=th.BG_ROOT)
        self.employee_service = employee_service
        self.time_clock_service = time_clock_service
        self.on_register = on_register
        self.on_admin_login = on_admin_login
        self._success_clear_after_id: str | None = None
        self._resize_after_id: str | None = None
        self._grid_columns = 0

        self._build()
        self._render_employee_cards()
        self.bind("<Configure>", self._on_resize)
        self._tick()

    def _build(self) -> None:
        self._build_header()
        self._build_body()

    def _build_header(self) -> None:
        bar = ctk.CTkFrame(self, height=72, corner_radius=0, fg_color=th.BG_CARD)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        brand = ctk.CTkFrame(bar, fg_color="transparent")
        brand.pack(side="left", padx=22, pady=0)

        ctk.CTkLabel(
            brand,
            text="",
            image=th.logo_mark(size=(38, 38)),
        ).pack(side="left", padx=(0, 12), pady=17)

        ctk.CTkLabel(
            brand,
            text="CLOCKLY",
            font=th.bold(13),
            text_color=th.T_PRIMARY,
        ).pack(side="left", pady=22)

        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right", padx=22)

        ctk.CTkButton(
            right,
            text="Admin",
            width=112,
            height=36,
            font=th.f(12),
            **th.quiet_button_kwargs(),
            command=self.on_admin_login,
        ).pack(side="right", padx=(14, 0), pady=16)

        clock_box = ctk.CTkFrame(right, fg_color="transparent")
        clock_box.pack(side="right", pady=10)
        self._clock_lbl = ctk.CTkLabel(
            clock_box,
            text="",
            font=th.bold(20),
            text_color=th.T_PRIMARY,
        )
        self._clock_lbl.pack(anchor="e")
        self._date_lbl = ctk.CTkLabel(
            clock_box,
            text="",
            font=th.f(11),
            text_color=th.T_MUTED,
        )
        self._date_lbl.pack(anchor="e")

        th.separator(self)

    def _build_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=th.PAGE_PAD, pady=20)

        hero = th.card(body)
        hero.pack(fill="x", pady=(0, 14))
        hero.columnconfigure(0, weight=1)

        copy = ctk.CTkFrame(hero, fg_color="transparent")
        copy.grid(row=0, column=0, sticky="ew", padx=22, pady=20)
        ctk.CTkLabel(
            copy,
            text="Terminal de fichaje",
            font=th.bold(10),
            text_color=th.ACCENT_SOFT,
            fg_color=th.ACCENT_DIM,
            corner_radius=th.R_SM,
        ).pack(anchor="w", pady=(0, 10), ipadx=10, ipady=4)
        ctk.CTkLabel(
            copy,
            text="Selecciona tu perfil",
            font=th.bold(32),
            text_color=th.T_PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            copy,
            text="Pulsa tu tarjeta, confirma tu contraseña y registra entrada o salida con un solo gesto.",
            font=th.f(14),
            text_color=th.T_SECONDARY,
            wraplength=620,
            justify="left",
        ).pack(anchor="w", pady=(6, 0))

        stats = ctk.CTkFrame(hero, fg_color="transparent")
        stats.grid(row=0, column=1, sticky="e", padx=22, pady=20)
        self._active_count_lbl = _MiniStat(stats, label="Activos", value="0")
        self._active_count_lbl.pack(side="left", padx=(0, 10))
        _MiniStat(stats, label="Modo", value="Local").pack(side="left")

        self._success_banner = ctk.CTkFrame(
            body,
            height=42,
            fg_color=th.SUCCESS_DIM,
            corner_radius=th.R_MD,
            border_width=1,
            border_color=th.SUCCESS,
        )
        self._success_banner.pack(fill="x", pady=(0, 12))
        self._success_banner.pack_propagate(False)
        self._success_lbl = ctk.CTkLabel(
            self._success_banner,
            text="Listo para registrar fichajes.",
            font=th.bold(13),
            text_color=th.SUCCESS_TEXT,
            anchor="w",
        )
        self._success_lbl.pack(fill="x", padx=14, pady=10)

        self._cards_scroll = ctk.CTkScrollableFrame(
            body,
            fg_color="transparent",
            scrollbar_button_color=th.BG_RAISED,
            scrollbar_button_hover_color=th.BG_HOVER,
        )
        self._cards_scroll.pack(fill="both", expand=True)

    def _render_employee_cards(self) -> None:
        for child in self._cards_scroll.winfo_children():
            child.destroy()

        employees = self.employee_service.list_clockable_employees()
        self._active_count_lbl.set(str(len(employees)))
        if not employees:
            empty = ctk.CTkFrame(
                self._cards_scroll,
                fg_color=th.BG_CARD,
                corner_radius=th.R_LG,
                border_width=1,
                border_color=th.BORDER,
            )
            empty.pack(fill="x", padx=4, pady=8)
            ctk.CTkLabel(
                empty,
                text="No hay empleados activos para fichar.",
                font=th.bold(16),
                text_color=th.T_PRIMARY,
            ).pack(anchor="w", padx=20, pady=(18, 4))
            ctk.CTkLabel(
                empty,
                text="Entra como administrador y crea empleados desde la pestaña Empleados.",
                font=th.f(13),
                text_color=th.T_SECONDARY,
            ).pack(anchor="w", padx=20, pady=(0, 18))
            return

        grid = ctk.CTkFrame(self._cards_scroll, fg_color="transparent")
        grid.pack(fill="x", anchor="n", pady=(0, 20))
        columns = self._columns_for_width(self.winfo_width())
        self._grid_columns = columns
        for col in range(columns):
            grid.columnconfigure(col, weight=1, uniform="employee_cards")

        for index, employee in enumerate(employees):
            status_text, status_color = self._employee_status(employee)
            card = _EmployeeCard(
                grid,
                employee=employee,
                status_text=status_text,
                status_color=status_color,
                command=lambda selected=employee: self._open_password_dialog(selected),
            )
            card.grid(
                row=index // columns,
                column=index % columns,
                padx=12,
                pady=12,
                sticky="n",
            )

    def _columns_for_width(self, width: int) -> int:
        usable = max(width - (th.PAGE_PAD * 2), 320)
        if usable < 520:
            return 1
        if usable < 760:
            return 2
        if usable < 1000:
            return 3
        if usable < 1250:
            return 4
        return 5

    def _on_resize(self, event) -> None:
        if event.widget is not self:
            return
        columns = self._columns_for_width(event.width)
        if columns == self._grid_columns:
            return
        if self._resize_after_id:
            self.after_cancel(self._resize_after_id)
        self._resize_after_id = self.after(120, self._render_employee_cards)

    def _employee_status(self, employee: Employee) -> tuple[str, str]:
        active = self.time_clock_service.get_active_session(employee.id)
        if active:
            time_text = format_timestamp(active.clock_in_time, "%H:%M")
            return f"Dentro desde {time_text}", th.SUCCESS_TEXT

        latest = (
            self.time_clock_service.attendance_session_repository.get_latest_for_user(
                employee.id
            )
        )
        if latest and latest.clock_out_time:
            time_text = format_timestamp(latest.clock_out_time, "%H:%M")
            return f"Ultima salida {time_text}", th.T_MUTED
        return "Sin fichajes", th.T_MUTED

    def _open_password_dialog(self, employee: Employee) -> None:
        _PasswordDialog(
            self,
            employee=employee,
            suggested_entry_type=self._suggest_next_entry_type(employee),
            on_submit=self._submit_attendance,
            on_success=self._show_success,
        )

    def _suggest_next_entry_type(self, employee: Employee) -> str:
        if self.time_clock_service.get_active_session(employee.id):
            return TimeClockService.EXIT
        return TimeClockService.ENTRY

    def _submit_attendance(
        self,
        employee: Employee,
        password: str,
        entry_type: str,
    ) -> str:
        message = self.on_register(employee.id, password, entry_type)
        self._render_employee_cards()
        return message

    def _show_success(self, message: str) -> None:
        if self._success_clear_after_id:
            self.after_cancel(self._success_clear_after_id)

        self._success_lbl.configure(text=message, text_color=th.SUCCESS_TEXT)
        self._success_clear_after_id = self.after(
            4500,
            lambda: self._success_lbl.configure(text="Listo para registrar fichajes."),
        )

    def _tick(self) -> None:
        if not self.winfo_exists():
            return
        now = datetime.now()
        self._clock_lbl.configure(text=now.strftime("%H:%M:%S"))
        self._date_lbl.configure(text=now.strftime("%d/%m/%Y"))
        self.after(1000, self._tick)


class _MiniStat(ctk.CTkFrame):
    def __init__(self, master, *, label: str, value: str) -> None:
        super().__init__(
            master,
            width=104,
            height=64,
            fg_color=th.BG_RAISED,
            corner_radius=th.R_MD,
            border_width=1,
            border_color=th.BORDER,
        )
        self.pack_propagate(False)

        self._value = ctk.CTkLabel(
            self,
            text=value,
            font=th.bold(20),
            text_color=th.T_PRIMARY,
        )
        self._value.pack(anchor="w", padx=12, pady=(9, 0))
        ctk.CTkLabel(
            self,
            text=label,
            font=th.f(11),
            text_color=th.T_MUTED,
        ).pack(anchor="w", padx=12, pady=(0, 8))

    def set(self, value: str) -> None:
        self._value.configure(text=value)


class _EmployeeCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        employee: Employee,
        status_text: str,
        status_color: str,
        command: Callable[[], None],
    ) -> None:
        super().__init__(
            master,
            width=208,
            height=224,
            corner_radius=th.R_LG,
            fg_color=th.BG_CARD,
            border_width=1,
            border_color=th.BORDER,
        )
        self.employee = employee
        self.command = command
        self._bg = th.BG_CARD
        self._hover = th.BG_RAISED
        self.grid_propagate(False)
        self.pack_propagate(False)

        ctk.CTkFrame(self, height=3, corner_radius=0, fg_color=th.ACCENT).pack(fill="x")

        avatar = ctk.CTkFrame(
            self,
            width=82,
            height=82,
            corner_radius=th.R_LG,
            fg_color=th.ACCENT_DIM,
            border_width=2,
            border_color=th.ACCENT,
        )
        avatar.pack(pady=(18, 12))
        avatar.pack_propagate(False)
        ctk.CTkLabel(
            avatar,
            text=employee.initials,
            font=th.bold(27),
            text_color=th.ACCENT,
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            self,
            text=employee.full_name,
            font=th.bold(15),
            text_color=th.T_PRIMARY,
            wraplength=174,
            justify="center",
        ).pack(padx=14)

        ctk.CTkLabel(
            self,
            text=f"@{employee.username}",
            font=th.f(11),
            text_color=th.T_MUTED,
            wraplength=174,
            justify="center",
        ).pack(padx=14, pady=(4, 8))

        status_pill = ctk.CTkFrame(
            self,
            fg_color=th.BG_RAISED,
            corner_radius=th.R_MD,
            border_width=1,
            border_color=th.BORDER,
        )
        status_pill.pack(padx=14, pady=(0, 12))
        ctk.CTkLabel(
            status_pill,
            text=status_text,
            font=th.bold(11),
            text_color=status_color,
            wraplength=160,
            justify="center",
        ).pack(padx=10, pady=5)

        self._bind_clicks()

    def _bind_clicks(self) -> None:
        widgets = [self, *self.winfo_children()]
        for child in self.winfo_children():
            widgets.extend(child.winfo_children())

        for widget in widgets:
            widget.bind("<Enter>", lambda _: self.configure(fg_color=self._hover))
            widget.bind("<Leave>", lambda _: self.configure(fg_color=self._bg))
            widget.bind("<Button-1>", lambda _: self.command())
            widget.configure(cursor="hand2")


class _PasswordDialog(ctk.CTkToplevel):
    _LABEL_TO_TYPE = {
        "Entrada": TimeClockService.ENTRY,
        "Salida": TimeClockService.EXIT,
    }
    _TYPE_TO_LABEL = {
        TimeClockService.ENTRY: "Entrada",
        TimeClockService.EXIT: "Salida",
    }

    def __init__(
        self,
        master,
        *,
        employee: Employee,
        suggested_entry_type: str,
        on_submit: Callable[[Employee, str, str], str],
        on_success: Callable[[str], None],
    ) -> None:
        super().__init__(master)
        self.employee = employee
        self.on_submit = on_submit
        self.on_success = on_success

        self.title("Registrar fichaje")
        self.geometry("440x462")
        self.resizable(False, False)
        self.configure(fg_color=th.BG_ROOT)
        self.transient(master.winfo_toplevel())
        self.grab_set()

        self._build(suggested_entry_type)
        self._center(master)
        self._password.focus()
        self.bind("<Return>", lambda _: self._submit())
        self.bind("<Escape>", lambda _: self.destroy())

    def _build(self, suggested_entry_type: str) -> None:
        card = ctk.CTkFrame(
            self,
            fg_color=th.BG_CARD,
            corner_radius=th.R_LG,
            border_width=1,
            border_color=th.BORDER_LT,
        )
        card.pack(fill="both", expand=True, padx=18, pady=18)

        avatar = ctk.CTkFrame(
            card,
            width=78,
            height=78,
            corner_radius=th.R_LG,
            fg_color=th.ACCENT_DIM,
            border_width=2,
            border_color=th.ACCENT,
        )
        avatar.pack(pady=(22, 10))
        avatar.pack_propagate(False)
        ctk.CTkLabel(
            avatar,
            text=self.employee.initials,
            font=th.bold(24),
            text_color=th.ACCENT,
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            card,
            text=self.employee.full_name,
            font=th.bold(20),
            text_color=th.T_PRIMARY,
        ).pack(pady=(0, 4))
        ctk.CTkLabel(
            card,
            text="Confirma tu contraseña y el tipo de fichaje.",
            font=th.f(12),
            text_color=th.T_SECONDARY,
        ).pack(pady=(0, 18))

        self._mode = ctk.CTkSegmentedButton(
            card,
            values=["Entrada", "Salida"],
            height=42,
            fg_color=th.BG_RAISED,
            selected_color=th.ACCENT_DIM,
            selected_hover_color=th.BG_HOVER,
            unselected_color=th.BG_RAISED,
            unselected_hover_color=th.BG_HOVER,
            text_color=th.T_PRIMARY,
            font=th.bold(12),
        )
        self._mode.set(self._TYPE_TO_LABEL.get(suggested_entry_type, "Entrada"))
        self._mode.pack(fill="x", padx=28, pady=(0, 16))

        self._password = ctk.CTkEntry(
            card,
            placeholder_text="Contraseña",
            show="*",
            height=46,
            font=th.f(14),
            **th.entry_kwargs(),
        )
        self._password.pack(fill="x", padx=28, pady=(0, 8))

        self._error_lbl = ctk.CTkLabel(
            card,
            text="",
            height=28,
            font=th.f(12),
            text_color=th.DANGER_TEXT,
            wraplength=330,
        )
        self._error_lbl.pack(fill="x", padx=28)

        ctk.CTkButton(
            card,
            text="Registrar fichaje",
            height=46,
            font=th.bold(14),
            fg_color=th.SUCCESS,
            hover_color=th.SUCCESS_HOVER,
            corner_radius=th.R_MD,
            text_color="#071B10",
            command=self._submit,
        ).pack(fill="x", padx=28, pady=(8, 10))

        ctk.CTkButton(
            card,
            text="Cancelar",
            height=38,
            font=th.f(12),
            **th.quiet_button_kwargs(),
            command=self.destroy,
        ).pack(fill="x", padx=28)

    def _submit(self) -> None:
        password = self._password.get()
        entry_type = self._LABEL_TO_TYPE[self._mode.get()]

        if not password:
            self._show_error("Introduce la contraseña.")
            return

        try:
            message = self.on_submit(self.employee, password, entry_type)
        except ValueError as exc:
            self._show_error(str(exc))
            return

        self.on_success(message)
        self.destroy()

    def _show_error(self, message: str) -> None:
        self._error_lbl.configure(text=message, text_color=th.DANGER_TEXT)
        self._password.delete(0, "end")
        self._password.focus()

    def _center(self, master) -> None:
        self.update_idletasks()
        parent = master.winfo_toplevel()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (440 // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (462 // 2)
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
