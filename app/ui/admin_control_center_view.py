from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime
from tkinter import StringVar

import customtkinter as ctk

from app.models.business import Business
from app.models.employee import Employee
from app.services.attendance_report_service import AttendanceReportService
from app.services.business_service import BusinessService
from app.services.employee_service import EmployeeService
from app.services.export_service import ExportService
from app.services.time_clock_service import TimeClockService
from app.ui import theme as th

_AUTO_REFRESH_MS = 30_000
_TOAST_DISMISS_MS = 4_000


class _KpiCard(ctk.CTkFrame):
    def __init__(self, master, title: str, helper: str, accent: str) -> None:
        super().__init__(
            master,
            height=116,
            fg_color=th.BG_CARD,
            corner_radius=th.R_LG,
            border_width=1,
            border_color=th.BORDER,
        )
        self.grid_propagate(False)
        self.columnconfigure(0, weight=1)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 0))
        top.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            top,
            text=title.upper(),
            font=th.bold(9),
            text_color=th.T_MUTED,
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkFrame(
            top,
            width=9,
            height=9,
            fg_color=accent,
            corner_radius=4,
        ).grid(row=0, column=1, sticky="e")

        self.value = ctk.CTkLabel(
            self,
            text="-",
            font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"),
            text_color=th.T_PRIMARY,
        )
        self.value.grid(row=1, column=0, sticky="w", padx=16, pady=(6, 0))
        ctk.CTkLabel(
            self,
            text=helper,
            font=th.f(11),
            text_color=th.T_SECONDARY,
        ).grid(row=2, column=0, sticky="w", padx=16, pady=(2, 14))

    def set(self, value: str | int) -> None:
        self.value.configure(text=str(value))


class AdminDashboardView(ctk.CTkFrame):
    ROUTES = {
        "create": "Crear usuario",
        "edit": "Editar usuario",
        "delete": "Eliminar usuario",
        "activate": "Activar usuario",
        "business": "Ajustes del negocio",
        "exports": "Exportar registros",
    }

    def __init__(
        self,
        master,
        *,
        employee: Employee,
        business: Business | None = None,
        business_count: int = 0,
        employee_service: EmployeeService,
        export_service: ExportService,
        attendance_report_service: AttendanceReportService,
        time_clock_service: TimeClockService,
        on_logout: Callable[[], None],
        on_change_business: Callable[[], None] | None = None,
        on_create_business: Callable[[], None] | None = None,
        business_service: BusinessService | None = None,
        on_business_updated: Callable[[Business], None] | None = None,
    ) -> None:
        super().__init__(master, corner_radius=0, fg_color=th.BG_ROOT)
        self.employee = employee
        self.business = business
        self.business_count = business_count
        self.employee_service = employee_service
        self.export_service = export_service
        self.attendance_report_service = attendance_report_service
        self.time_clock_service = time_clock_service
        self.business_service = business_service or BusinessService()
        self.on_logout = on_logout
        self.on_change_business = on_change_business
        self.on_create_business = on_create_business
        self.on_business_updated = on_business_updated

        self._employees: list[Employee] = []
        self._statuses: dict[int, object] = {}
        self._summaries = {}
        self._sessions = []
        self._kpis: dict[str, _KpiCard] = {}
        self._live_count: ctk.CTkLabel | None = None
        self._route_var = StringVar(value=self.ROUTES["create"])
        self._route_lookup = {label: key for key, label in self.ROUTES.items()}
        self._refresh_after_id: str | None = None
        self._toast_after_ids: dict[str, str] = {}

        self._build_header()
        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.pack(fill="both", expand=True)
        self._reload_all()
        self._show_home()
        self._schedule_refresh()

    def _build_header(self) -> None:
        bar = ctk.CTkFrame(self, height=72, corner_radius=0, fg_color=th.BG_CARD)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.pack(side="left", padx=22, pady=12)
        title_row = ctk.CTkFrame(left, fg_color="transparent")
        title_row.pack(anchor="w")
        ctk.CTkLabel(title_row, text="", image=th.logo_mark(size=(28, 28))).pack(
            side="left", padx=(0, 9)
        )
        ctk.CTkButton(
            title_row,
            text="Panel de administracion",
            width=220,
            height=28,
            fg_color="transparent",
            hover_color=th.BG_HOVER,
            text_color=th.T_PRIMARY,
            font=th.bold(18),
            corner_radius=th.R_SM,
            command=self._show_home,
        ).pack(side="left")
        self._business_label = ctk.CTkLabel(
            left,
            text=self._business_header_text(),
            font=th.f(11),
            text_color=th.T_MUTED,
        )
        self._business_label.pack(anchor="w", pady=(3, 0))

        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right", padx=22, pady=14)
        ctk.CTkButton(
            right,
            text="Cerrar sesion",
            width=130,
            height=36,
            font=th.f(12),
            **th.quiet_button_kwargs(),
            command=self.on_logout,
        ).pack(side="right")
        if self.on_create_business:
            ctk.CTkButton(
                right,
                text="Nuevo negocio",
                width=126,
                height=36,
                font=th.f(12),
                **th.quiet_button_kwargs(),
                command=self.on_create_business,
            ).pack(side="right", padx=(0, 8))
        if self.on_change_business and self.business_count > 1:
            ctk.CTkButton(
                right,
                text="Cambiar negocio",
                width=134,
                height=36,
                font=th.f(12),
                **th.quiet_button_kwargs(),
                command=self.on_change_business,
            ).pack(side="right", padx=(0, 8))
        ctk.CTkLabel(
            right,
            text=self.employee.full_name,
            font=th.f(12),
            text_color=th.T_SECONDARY,
        ).pack(side="right", padx=(0, 14))
        th.separator(self)

    def _business_header_text(self) -> str:
        if not self.business:
            return "Negocio activo pendiente"
        return f"Negocio activo: {self.business.business_name}"

    def _clear_content(self) -> None:
        self._kpis = {}
        self._live_count = None
        for child in self._content.winfo_children():
            child.destroy()

    def _show_home(self) -> None:
        self._clear_content()
        page = ctk.CTkFrame(self._content, fg_color="transparent")
        page.pack(fill="both", expand=True, padx=th.PAGE_PAD, pady=18)
        self._build_stats(page)
        self._build_live_count(page)
        self._build_terminal(page)
        self._refresh_stats()

    def _build_stats(self, parent: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 14))
        row.columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="kpis")
        data = [
            ("clocked", "Fichados ahora", "Personal en turno", th.SUCCESS),
            ("active", "Empleados activos", "Usuarios operativos", th.ACCENT),
            ("hours", "Horas hoy", "Tiempo cerrado hoy", th.ACCENT_SOFT),
            ("incidents", "Incidencias", "Alertas detectadas", th.WARNING),
            ("sessions", "Sesiones hoy", "Turnos iniciados", th.T_SECONDARY),
        ]
        for col, (key, title, helper, accent) in enumerate(data):
            padx = (0, 8) if col == 0 else (8, 0) if col == 4 else (8, 8)
            card = _KpiCard(row, title, helper, accent)
            card.grid(row=0, column=col, sticky="ew", padx=padx)
            self._kpis[key] = card

    def _build_live_count(self, parent: ctk.CTkFrame) -> None:
        block = ctk.CTkFrame(
            parent,
            height=106,
            fg_color=th.SURFACE,
            corner_radius=th.R_LG,
            border_width=1,
            border_color=th.BORDER,
        )
        block.pack(fill="x", pady=(0, 14))
        block.pack_propagate(False)
        block.columnconfigure(1, weight=1)
        meter = ctk.CTkFrame(
            block,
            width=70,
            height=70,
            fg_color=th.SUCCESS_DIM,
            corner_radius=th.R_LG,
            border_width=1,
            border_color=th.SUCCESS,
        )
        meter.grid(row=0, column=0, padx=(20, 16), pady=18)
        meter.grid_propagate(False)
        self._live_count = ctk.CTkLabel(
            meter,
            text="-",
            font=ctk.CTkFont(family="Segoe UI", size=31, weight="bold"),
            text_color=th.SUCCESS_TEXT,
        )
        self._live_count.place(relx=0.5, rely=0.5, anchor="center")
        copy = ctk.CTkFrame(block, fg_color="transparent")
        copy.grid(row=0, column=1, sticky="ew")
        ctk.CTkLabel(
            copy,
            text="Personas fichadas actualmente",
            font=th.bold(17),
            text_color=th.T_PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            copy,
            text="Vista operativa inmediata del negocio activo.",
            font=th.f(12),
            text_color=th.T_MUTED,
        ).pack(anchor="w", pady=(4, 0))
        ctk.CTkButton(
            block,
            text="Actualizar",
            width=112,
            height=36,
            font=th.f(12),
            **th.quiet_button_kwargs(),
            command=self._manual_refresh,
        ).grid(row=0, column=2, padx=(16, 20), pady=35)

    def _build_terminal(self, parent: ctk.CTkFrame) -> None:
        terminal = ctk.CTkFrame(
            parent,
            fg_color="#080B0A",
            corner_radius=th.R_LG,
            border_width=1,
            border_color="#33433A",
        )
        terminal.pack(fill="both", expand=True)
        terminal.columnconfigure(0, weight=1)
        terminal.rowconfigure(1, weight=1)

        title = ctk.CTkFrame(terminal, height=48, fg_color="#101411", corner_radius=th.R_LG)
        title.grid(row=0, column=0, sticky="ew")
        title.grid_propagate(False)
        controls = ctk.CTkFrame(title, fg_color="transparent")
        controls.pack(side="left", padx=18, pady=17)
        for color in ("#FF5F57", "#FEBC2E", "#28C840"):
            ctk.CTkFrame(controls, width=11, height=11, fg_color=color, corner_radius=5).pack(
                side="left", padx=(0, 7)
            )
        ctk.CTkLabel(
            title,
            text="admin@clockly:~/operaciones",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=th.T_SECONDARY,
        ).pack(side="left")
        ctk.CTkLabel(
            title,
            text="ready",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=th.SUCCESS_TEXT,
        ).pack(side="right", padx=18)

        body = ctk.CTkFrame(terminal, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=30, pady=28)
        body.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            body,
            text="$ abrir centro_administrativo",
            font=ctk.CTkFont(family="Consolas", size=15, weight="bold"),
            text_color=th.ACCENT_SOFT,
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            body,
            text="Selecciona una accion administrativa para abrir una seccion dedicada.",
            font=th.f(14),
            text_color=th.T_SECONDARY,
        ).grid(row=1, column=0, sticky="w", pady=(10, 18))

        launcher = ctk.CTkFrame(
            body,
            fg_color="#101411",
            corner_radius=th.R_LG,
            border_width=1,
            border_color="#26342D",
        )
        launcher.grid(row=2, column=0, sticky="ew")
        launcher.columnconfigure(0, weight=1)
        ctk.CTkLabel(
            launcher,
            text="ACCION ADMINISTRATIVA",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            text_color=th.T_MUTED,
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 6))

        action = ctk.CTkFrame(launcher, fg_color="transparent")
        action.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 18))
        action.columnconfigure(0, weight=1)
        self._option_menu(action, self._route_var, list(self.ROUTES.values())).grid(
            row=0, column=0, sticky="ew"
        )
        ctk.CTkButton(
            action,
            text="Abrir seccion",
            width=150,
            height=44,
            font=th.bold(13),
            **th.primary_button_kwargs(),
            command=self._open_route,
        ).grid(row=0, column=1, padx=(12, 0))
        ctk.CTkLabel(
            body,
            text="$ estado --dashboard limpio --tablas fuera_de_home",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=th.T_MUTED,
        ).grid(row=3, column=0, sticky="w", pady=(18, 0))

    def _open_route(self) -> None:
        self._show_section(self._route_lookup.get(self._route_var.get(), "create"))

    def _show_section(self, route: str) -> None:
        self._clear_content()
        self._reload_all()
        builders = {
            "create": self._build_create_user,
            "edit": self._build_edit_user,
            "delete": self._build_delete_user,
            "activate": self._build_activate_user,
            "business": self._build_business_settings,
            "exports": self._build_export_records,
        }
        builders.get(route, self._build_create_user)()

    def _section(self, title: str, subtitle: str) -> ctk.CTkFrame:
        page = ctk.CTkFrame(self._content, fg_color="transparent")
        page.pack(fill="both", expand=True, padx=th.PAGE_PAD, pady=18)
        page.columnconfigure(0, weight=1)
        page.rowconfigure(1, weight=1)
        head = ctk.CTkFrame(page, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        head.columnconfigure(0, weight=1)
        text = ctk.CTkFrame(head, fg_color="transparent")
        text.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(text, text=title, font=th.bold(22), text_color=th.T_PRIMARY).pack(
            anchor="w"
        )
        ctk.CTkLabel(text, text=subtitle, font=th.f(12), text_color=th.T_MUTED).pack(
            anchor="w", pady=(4, 0)
        )
        ctk.CTkButton(
            head,
            text="Volver al dashboard",
            width=164,
            height=38,
            font=th.f(12),
            **th.quiet_button_kwargs(),
            command=self._show_home,
        ).grid(row=0, column=1, sticky="e")
        body = ctk.CTkFrame(page, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        return body

    def _build_create_user(self) -> None:
        body = self._section(
            "Crear usuario",
            "Alta de empleados o administradores dentro del negocio activo.",
        )
        panel = th.card(body)
        panel.grid(row=0, column=0, sticky="new")
        panel.columnconfigure((0, 1), weight=1)
        first = self._entry(panel, "Nombre", "Ana", 0, 0)
        last = self._entry(panel, "Apellidos", "Lopez Garcia", 0, 1)
        dni = self._entry(panel, "DNI", "12345678A", 1, 0)
        password = self._entry(panel, "Contrasena", "minimo 6 caracteres", 1, 1, show="*")
        role = self._segment(panel, ["employee", "admin"], row=4, col=0, label="Rol")
        role.set("employee")
        status = self._status(panel, row=6, col=0, colspan=2)

        def save() -> None:
            try:
                self.employee_service.create_employee(
                    first_name=first.get(),
                    last_name=last.get(),
                    dni=dni.get(),
                    password=password.get(),
                    role=role.get(),
                )
            except ValueError as exc:
                self._toast(status, str(exc), th.DANGER_TEXT, th.DANGER_DIM, key="create")
                return
            name = f"{first.get().strip()} {last.get().strip()}".strip()
            for field in (first, last, dni, password):
                field.delete(0, "end")
            role.set("employee")
            self._reload_all()
            self._toast(status, f"Usuario creado: {name}", th.SUCCESS_TEXT, th.SUCCESS_DIM, key="create")

        ctk.CTkButton(
            panel,
            text="Crear usuario",
            height=46,
            font=th.bold(13),
            **th.primary_button_kwargs(),
            command=save,
        ).grid(row=7, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 18))

    def _build_edit_user(self) -> None:
        body = self._section(
            "Editar usuario",
            "Actualiza datos, rol, estado y contrasena desde una vista dedicada.",
        )
        panel = th.card(body)
        panel.grid(row=0, column=0, sticky="new")
        panel.columnconfigure((0, 1), weight=1)
        options, by_option = self._employee_options()
        selected = StringVar(value=options[0])
        self._field_label(panel, "Usuario", 0, 0, colspan=2)
        selector = self._option_menu(panel, selected, options)
        selector.grid(row=1, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 14))
        first = self._entry(panel, "Nombre", "", 1, 0)
        last = self._entry(panel, "Apellidos", "", 1, 1)
        dni = self._entry(panel, "DNI", "", 2, 0)
        password = self._entry(panel, "Nueva contrasena", "opcional", 2, 1, show="*")
        role = self._segment(panel, ["employee", "admin"], row=6, col=0, label="Rol")
        active = self._segment(panel, ["Activo", "Inactivo"], row=6, col=1, label="Estado")
        status = self._status(panel, row=8, col=0, colspan=2)

        def populate(_: str | None = None) -> None:
            emp = by_option.get(selected.get())
            if not emp:
                return
            self._replace(first, emp.first_name)
            self._replace(last, emp.last_name)
            self._replace(dni, emp.dni)
            password.delete(0, "end")
            role.set(emp.role)
            active.set("Activo" if emp.active else "Inactivo")

        selector.configure(command=populate)
        populate()

        def save() -> None:
            emp = by_option.get(selected.get())
            if not emp:
                self._toast(status, "Selecciona un usuario.", th.DANGER_TEXT, th.DANGER_DIM, key="edit")
                return
            try:
                self.employee_service.update_employee(
                    emp.id,
                    first_name=first.get(),
                    last_name=last.get(),
                    dni=dni.get(),
                    role=role.get(),
                    active=active.get() == "Activo",
                )
                if password.get().strip():
                    self.employee_service.set_password(emp.id, password.get())
            except ValueError as exc:
                self._toast(status, str(exc), th.DANGER_TEXT, th.DANGER_DIM, key="edit")
                return
            self._reload_all()
            self._toast(status, "Usuario actualizado correctamente.", th.SUCCESS_TEXT, th.SUCCESS_DIM, key="edit")

        ctk.CTkButton(
            panel,
            text="Guardar cambios",
            height=46,
            font=th.bold(13),
            **th.primary_button_kwargs(),
            command=save,
        ).grid(row=9, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 18))

    def _reload_all(self) -> None:
        self._employees = self.employee_service.list_employees()
        self._statuses = {
            status.employee.id: status
            for status in self.time_clock_service.get_attendance_statuses(self._employees)
        }
        employee_ids = [emp.id for emp in self._employees if emp.role == "employee"]
        self._summaries = self.attendance_report_service.get_current_period_summaries(employee_ids)
        self._sessions = self.attendance_report_service.list_session_reports()

    def _refresh_stats(self) -> None:
        if not self._kpis:
            return
        active_count = len([emp for emp in self._employees if emp.active])
        clocked_count = len(
            [
                status
                for status in self._statuses.values()
                if status.is_clocked_in and status.employee.active
            ]
        )
        today = datetime.now().date().isoformat()
        today_sessions = len(
            [session for session in self._sessions if str(session.clock_in_time).startswith(today)]
        )
        incident_count = len([session for session in self._sessions if session.has_incident])
        today_seconds = sum(summary.today.total_seconds for summary in self._summaries.values())
        self._kpis["clocked"].set(clocked_count)
        self._kpis["active"].set(active_count)
        self._kpis["hours"].set(self._format_hours(today_seconds))
        self._kpis["incidents"].set(incident_count)
        self._kpis["sessions"].set(today_sessions)
        if self._live_count:
            self._live_count.configure(text=str(clocked_count))

    def _manual_refresh(self) -> None:
        self._reload_all()
        self._refresh_stats()
        self._cancel_refresh()
        self._schedule_refresh()

    def _schedule_refresh(self) -> None:
        self._cancel_refresh()
        if self.winfo_exists():
            self._refresh_after_id = self.after(_AUTO_REFRESH_MS, self._auto_refresh)

    def _cancel_refresh(self) -> None:
        if self._refresh_after_id:
            self.after_cancel(self._refresh_after_id)
            self._refresh_after_id = None

    def _auto_refresh(self) -> None:
        if self.winfo_exists():
            self._reload_all()
            self._refresh_stats()
            self._schedule_refresh()

    def destroy(self) -> None:
        self._cancel_refresh()
        for after_id in self._toast_after_ids.values():
            try:
                self.after_cancel(after_id)
            except Exception:
                pass
        super().destroy()

    def _field_label(
        self,
        parent: ctk.CTkFrame,
        label: str,
        row: int,
        col: int,
        *,
        colspan: int = 1,
    ) -> None:
        ctk.CTkLabel(
            parent,
            text=label.upper(),
            font=th.bold(9),
            text_color=th.T_MUTED,
            anchor="w",
        ).grid(row=row, column=col, columnspan=colspan, sticky="w", padx=18, pady=(18, 4))

    def _entry(
        self,
        parent: ctk.CTkFrame,
        label: str,
        placeholder: str,
        group: int,
        col: int,
        *,
        show: str | None = None,
    ) -> ctk.CTkEntry:
        row = group * 2
        self._field_label(parent, label, row, col)
        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            height=40,
            font=th.f(13),
            show=show,
            **th.entry_kwargs(),
        )
        entry.grid(row=row + 1, column=col, sticky="ew", padx=18)
        return entry

    def _option_menu(
        self,
        parent: ctk.CTkFrame,
        variable: StringVar,
        values: list[str],
    ) -> ctk.CTkOptionMenu:
        return ctk.CTkOptionMenu(
            parent,
            variable=variable,
            values=values,
            height=40,
            fg_color=th.BG_FIELD,
            button_color=th.ACCENT_DIM,
            button_hover_color=th.BG_HOVER,
            dropdown_fg_color=th.BG_CARD,
            dropdown_hover_color=th.BG_HOVER,
            dropdown_text_color=th.T_PRIMARY,
            text_color=th.T_PRIMARY,
            font=th.f(13),
            corner_radius=th.R_MD,
        )

    def _segment(
        self,
        parent: ctk.CTkFrame,
        values: list[str],
        *,
        row: int,
        col: int,
        label: str | None = None,
    ) -> ctk.CTkSegmentedButton:
        if label:
            self._field_label(parent, label, row, col)
            row += 1
        segment = ctk.CTkSegmentedButton(
            parent,
            values=values,
            fg_color=th.BG_RAISED,
            selected_color=th.ACCENT_DIM,
            selected_hover_color=th.BG_HOVER,
            unselected_color=th.BG_RAISED,
            unselected_hover_color=th.BG_HOVER,
            text_color=th.T_PRIMARY,
            font=th.f(12),
        )
        segment.grid(row=row, column=col, sticky="ew", padx=18, pady=(0, 18))
        return segment

    def _status(
        self,
        parent: ctk.CTkFrame,
        *,
        row: int,
        col: int,
        colspan: int = 1,
    ) -> ctk.CTkLabel:
        label = ctk.CTkLabel(
            parent,
            text="",
            font=th.f(12),
            text_color=th.T_SECONDARY,
            fg_color="transparent",
            corner_radius=th.R_SM,
            justify="left",
            anchor="w",
        )
        label.grid(row=row, column=col, columnspan=colspan, sticky="ew", padx=18, pady=(0, 12))
        return label

    def _employee_options(self) -> tuple[list[str], dict[str, Employee]]:
        if not self._employees:
            return ["Sin usuarios"], {}
        options: list[str] = []
        by_option: dict[str, Employee] = {}
        for emp in self._employees:
            state = "activo" if emp.active else "inactivo"
            label = f"{emp.full_name} ({emp.dni}) - {state}"
            options.append(label)
            by_option[label] = emp
        return options, by_option

    def _replace(self, entry: ctk.CTkEntry, value: str) -> None:
        entry.delete(0, "end")
        entry.insert(0, value)

    def _fact(self, parent: ctk.CTkFrame, label: str, value: str, row: int) -> None:
        ctk.CTkLabel(
            parent,
            text=label.upper(),
            font=th.bold(9),
            text_color=th.T_MUTED,
        ).grid(row=row * 2, column=0, sticky="w", pady=(0 if row == 0 else 8, 2))
        ctk.CTkLabel(
            parent,
            text=value,
            font=th.f(12),
            text_color=th.T_SECONDARY,
            anchor="w",
        ).grid(row=row * 2 + 1, column=0, sticky="ew")

    def _toast(
        self,
        label: ctk.CTkLabel,
        message: str,
        text_color: str,
        bg_color: str,
        *,
        key: str,
    ) -> None:
        label.configure(text=f"  {message}", text_color=text_color, fg_color=bg_color)
        if key in self._toast_after_ids:
            try:
                self.after_cancel(self._toast_after_ids[key])
            except Exception:
                pass

        def dismiss() -> None:
            if self.winfo_exists():
                label.configure(text="", fg_color="transparent")
            self._toast_after_ids.pop(key, None)

        self._toast_after_ids[key] = self.after(_TOAST_DISMISS_MS, dismiss)

    def _pretty_json(self, raw: str) -> str:
        try:
            parsed = json.loads(raw or "{}")
        except json.JSONDecodeError:
            return raw or "{}"
        return json.dumps(parsed, ensure_ascii=True, indent=2)

    def _format_hours(self, total_seconds: int | None) -> str:
        if total_seconds is None:
            return "-"
        hours, remainder = divmod(max(int(total_seconds), 0), 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours}h {minutes:02d}m"

    def _build_delete_user(self) -> None:
        body = self._section(
            "Eliminar usuario",
            "Baja segura: desactiva el acceso y conserva el historico de fichajes.",
        )
        panel = th.card(body)
        panel.grid(row=0, column=0, sticky="new")
        panel.columnconfigure(0, weight=1)
        options, by_option = self._employee_options()
        selected = StringVar(value=options[0])
        self._field_label(panel, "Usuario", 0, 0)
        selector = self._option_menu(panel, selected, options)
        selector.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 14))
        details = ctk.CTkLabel(
            panel,
            text="",
            font=th.f(13),
            text_color=th.T_SECONDARY,
            justify="left",
            anchor="w",
        )
        details.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 14))
        status = self._status(panel, row=3, col=0)

        def populate(_: str | None = None) -> None:
            emp = by_option.get(selected.get())
            if not emp:
                details.configure(text="No hay usuarios disponibles.")
                return
            state = "Activo" if emp.active else "Inactivo"
            details.configure(
                text=f"Nombre: {emp.full_name}\nDNI: {emp.dni}\nRol: {emp.role}\nEstado actual: {state}"
            )

        selector.configure(command=populate)
        populate()

        def deactivate() -> None:
            emp = by_option.get(selected.get())
            if not emp:
                self._toast(status, "Selecciona un usuario.", th.DANGER_TEXT, th.DANGER_DIM, key="delete")
                return
            if emp.id == self.employee.id:
                self._toast(status, "No puedes darte de baja desde tu propia sesion.", th.DANGER_TEXT, th.DANGER_DIM, key="delete")
                return
            if not emp.active:
                self._toast(status, "El usuario ya esta inactivo.", th.WARNING_TEXT, th.WARNING_DIM, key="delete")
                return
            try:
                self.employee_service.update_employee(
                    emp.id,
                    first_name=emp.first_name,
                    last_name=emp.last_name,
                    dni=emp.dni,
                    role=emp.role,
                    active=False,
                )
            except ValueError as exc:
                self._toast(status, str(exc), th.DANGER_TEXT, th.DANGER_DIM, key="delete")
                return
            self._reload_all()
            details.configure(
                text=f"Nombre: {emp.full_name}\nDNI: {emp.dni}\nRol: {emp.role}\nEstado actual: Inactivo"
            )
            self._toast(status, "Usuario dado de baja. El historico se conserva.", th.SUCCESS_TEXT, th.SUCCESS_DIM, key="delete")

        ctk.CTkButton(
            panel,
            text="Dar de baja usuario",
            height=46,
            font=th.bold(13),
            fg_color=th.DANGER,
            hover_color=th.DANGER_HOVER,
            text_color="#FFFFFF",
            corner_radius=th.R_MD,
            command=deactivate,
        ).grid(row=4, column=0, sticky="ew", padx=18, pady=(0, 18))

    def _build_activate_user(self) -> None:
        body = self._section(
            "Activar usuario",
            "Activa o desactiva usuarios sin mezclar la gestion con la home.",
        )
        panel = th.card(body)
        panel.grid(row=0, column=0, sticky="new")
        panel.columnconfigure(0, weight=1)
        options, by_option = self._employee_options()
        selected = StringVar(value=options[0])
        self._field_label(panel, "Usuario", 0, 0)
        selector = self._option_menu(panel, selected, options)
        selector.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 14))
        state = self._segment(panel, ["Activo", "Inactivo"], row=2, col=0, label="Estado")
        status = self._status(panel, row=4, col=0)

        def populate(_: str | None = None) -> None:
            emp = by_option.get(selected.get())
            if emp:
                state.set("Activo" if emp.active else "Inactivo")

        selector.configure(command=populate)
        populate()

        def save() -> None:
            emp = by_option.get(selected.get())
            if not emp:
                self._toast(status, "Selecciona un usuario.", th.DANGER_TEXT, th.DANGER_DIM, key="activate")
                return
            try:
                self.employee_service.update_employee(
                    emp.id,
                    first_name=emp.first_name,
                    last_name=emp.last_name,
                    dni=emp.dni,
                    role=emp.role,
                    active=state.get() == "Activo",
                )
            except ValueError as exc:
                self._toast(status, str(exc), th.DANGER_TEXT, th.DANGER_DIM, key="activate")
                return
            self._reload_all()
            self._toast(status, "Estado actualizado correctamente.", th.SUCCESS_TEXT, th.SUCCESS_DIM, key="activate")

        ctk.CTkButton(
            panel,
            text="Guardar estado",
            height=46,
            font=th.bold(13),
            **th.primary_button_kwargs(),
            command=save,
        ).grid(row=5, column=0, sticky="ew", padx=18, pady=(0, 18))

    def _build_business_settings(self) -> None:
        body = self._section(
            "Ajustes del negocio",
            "Configuracion basica del negocio activo preparada para evolucion SaaS.",
        )
        panel = th.card(body)
        panel.grid(row=0, column=0, sticky="new")
        panel.columnconfigure((0, 1), weight=1)
        if not self.business:
            ctk.CTkLabel(
                panel,
                text="No hay negocio activo.",
                font=th.f(13),
                text_color=th.WARNING_TEXT,
            ).grid(row=0, column=0, padx=18, pady=18, sticky="w")
            return

        name = self._entry(panel, "Nombre del negocio", "Restaurante Central", 0, 0)
        code = self._entry(panel, "Codigo de acceso", "CENTRAL", 0, 1)
        name.insert(0, self.business.business_name)
        code.insert(0, self.business.login_code)

        labels = list(self.business_service.BUSINESS_TYPES.values())
        label_to_code = {label: key for key, label in self.business_service.BUSINESS_TYPES.items()}
        current_label = self.business_service.BUSINESS_TYPES.get(
            self.business.business_type,
            self.business.business_type,
        )
        business_type = StringVar(value=current_label)
        self._field_label(panel, "Tipo de negocio", 4, 0)
        self._option_menu(panel, business_type, labels).grid(
            row=5, column=0, sticky="ew", padx=18, pady=(0, 14)
        )

        facts = ctk.CTkFrame(panel, fg_color="transparent")
        facts.grid(row=4, column=1, rowspan=2, sticky="nsew", padx=18, pady=(0, 14))
        self._fact(facts, "Identificador", self.business.short_id, 0)
        self._fact(facts, "Business key", self.business.business_key, 1)
        self._fact(facts, "Slug", self.business.slug, 2)

        self._field_label(panel, "Configuracion JSON", 6, 0, colspan=2)
        settings = ctk.CTkTextbox(
            panel,
            height=104,
            fg_color=th.BG_FIELD,
            border_color=th.BORDER_LT,
            border_width=1,
            corner_radius=th.R_MD,
            text_color=th.T_PRIMARY,
            font=ctk.CTkFont(family="Consolas", size=12),
        )
        settings.grid(row=7, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 14))
        settings.insert("1.0", self._pretty_json(self.business.settings_json))
        status = self._status(panel, row=8, col=0, colspan=2)

        def save() -> None:
            try:
                updated = self.business_service.update_business(
                    requester_user_id=self.employee.id,
                    business_id=self.business.id,
                    business_name=name.get(),
                    business_type=label_to_code.get(business_type.get(), business_type.get()),
                    login_code=code.get(),
                    settings_json=settings.get("1.0", "end").strip() or "{}",
                )
            except ValueError as exc:
                self._toast(status, str(exc), th.DANGER_TEXT, th.DANGER_DIM, key="business")
                return
            self.business = updated
            self._business_label.configure(text=self._business_header_text())
            if self.on_business_updated:
                self.on_business_updated(updated)
            settings.delete("1.0", "end")
            settings.insert("1.0", self._pretty_json(updated.settings_json))
            self._toast(status, "Ajustes del negocio guardados.", th.SUCCESS_TEXT, th.SUCCESS_DIM, key="business")

        ctk.CTkButton(
            panel,
            text="Guardar ajustes",
            height=46,
            font=th.bold(13),
            **th.primary_button_kwargs(),
            command=save,
        ).grid(row=9, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 18))

    def _build_export_records(self) -> None:
        body = self._section(
            "Exportar registros",
            "Exportacion separada de la home para mantener el dashboard limpio.",
        )
        panel = th.card(body)
        panel.grid(row=0, column=0, sticky="new")
        panel.columnconfigure((0, 1), weight=1)

        date_from = self._entry(panel, "Desde", "AAAA-MM-DD", 0, 0)
        date_to = self._entry(panel, "Hasta", "AAAA-MM-DD", 0, 1)

        names = ["Todos"]
        employee_by_name: dict[str, int] = {}
        for emp in self._employees:
            if emp.role == "employee":
                names.append(emp.full_name)
                employee_by_name[emp.full_name] = emp.id
        employee_name = StringVar(value="Todos")
        self._field_label(panel, "Empleado", 4, 0, colspan=2)
        self._option_menu(panel, employee_name, names).grid(
            row=5, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 14)
        )
        status = self._status(panel, row=6, col=0, colspan=2)

        actions = ctk.CTkFrame(panel, fg_color="transparent")
        actions.grid(row=7, column=0, columnspan=2, sticky="ew", padx=18, pady=(0, 18))
        actions.columnconfigure((0, 1), weight=1)

        def export(fmt: str) -> None:
            raw_from = date_from.get().strip() or None
            raw_to = date_to.get().strip() or None
            selected = employee_name.get()
            user_id = employee_by_name.get(selected) if selected != "Todos" else None
            selected_name = selected if selected != "Todos" else None
            try:
                if fmt == "pdf":
                    path = self.export_service.export_sessions_to_pdf(
                        date_from=raw_from,
                        date_to=raw_to,
                        user_id=user_id,
                        employee_name=selected_name,
                    )
                else:
                    path = self.export_service.export_sessions_to_excel(
                        date_from=raw_from,
                        date_to=raw_to,
                        user_id=user_id,
                        employee_name=selected_name,
                    )
            except (RuntimeError, ValueError) as exc:
                self._toast(status, str(exc), th.DANGER_TEXT, th.DANGER_DIM, key="exports")
                return
            self._toast(status, f"Exportacion guardada: {path}", th.SUCCESS_TEXT, th.SUCCESS_DIM, key="exports")

        ctk.CTkButton(
            actions,
            text="Exportar Excel",
            height=44,
            font=th.bold(13),
            **th.primary_button_kwargs(),
            command=lambda: export("xlsx"),
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ctk.CTkButton(
            actions,
            text="Exportar PDF",
            height=44,
            font=th.f(13),
            **th.quiet_button_kwargs(),
            command=lambda: export("pdf"),
        ).grid(row=0, column=1, sticky="ew", padx=(8, 0))
