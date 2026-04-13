"""
Panel de administración.

Layout:
  • Cabecera — logo, título, botón de cierre de sesión.
  • Fila de estadísticas — fichados ahora, empleados activos, sesiones hoy.
  • Cuerpo en dos columnas:
      izquierda (fija)  — formulario de nuevo empleado.
      derecha (flexible) — tabla de usuarios + tabla de sesiones con filtros.

Auto-refresco de sesiones cada 30 s mientras la vista esté activa.
Las notificaciones de estado se auto-desvanecen en 4 s.
"""

from collections.abc import Callable
from datetime import datetime
from tkinter import StringVar, ttk

import customtkinter as ctk

from app.models.employee import Employee
from app.services.attendance_report_service import (
    AttendanceReportService,
    EmployeePeriodSummary,
    SessionReport,
)
from app.services.employee_service import EmployeeService
from app.services.export_service import ExportService
from app.services.time_clock_service import TimeClockService
from app.ui import theme as th
from app.utils.helpers import format_timestamp

_AUTO_REFRESH_MS   = 30_000   # refresco automático de sesiones
_TOAST_DISMISS_MS  = 4_000    # tiempo antes de borrar un mensaje de estado


def _style_treeview() -> None:
    style = ttk.Style()
    style.theme_use("default")
    style.configure(
        "Fichaje.Treeview",
        background=th.BG_RAISED,
        foreground=th.T_PRIMARY,
        fieldbackground=th.BG_RAISED,
        rowheight=34,
        font=("Segoe UI", 10),
        borderwidth=0,
    )
    style.configure(
        "Fichaje.Treeview.Heading",
        background=th.BG_CARD,
        foreground=th.T_MUTED,
        font=("Segoe UI", 9, "bold"),
        relief="flat",
        borderwidth=0,
        padding=(8, 8),
    )
    style.map(
        "Fichaje.Treeview",
        background=[("selected", th.ACCENT_DIM)],
        foreground=[("selected", th.ACCENT_SOFT)],
    )


class AdminDashboardView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        employee: Employee,
        employee_service: EmployeeService,
        export_service: ExportService,
        attendance_report_service: AttendanceReportService,
        time_clock_service: TimeClockService,
        on_logout: Callable[[], None],
    ) -> None:
        super().__init__(master, corner_radius=0, fg_color=th.BG_ROOT)
        self.employee = employee
        self.employee_service = employee_service
        self.export_service = export_service
        self.attendance_report_service = attendance_report_service
        self.time_clock_service = time_clock_service
        self.on_logout = on_logout

        # Datos cacheados para las estadísticas
        self._cached_employees: list = []
        self._cached_statuses: dict = {}
        self._cached_employee_summaries: dict[int, EmployeePeriodSummary] = {}
        self._cached_sessions: list[SessionReport] = []

        # Mapa nombre de empleado → id (para filtro de sesiones)
        self._employee_name_to_id: dict[str, int] = {}

        # IDs de callbacks pendientes
        self._refresh_after_id: str | None = None
        self._toast_after_ids: dict[str, str] = {}   # widget_name → after_id

        _style_treeview()
        self._build()
        self._reload_all()
        self._schedule_refresh()

    # ── Construcción ─────────────────────────────────────────────────────────

    def _build(self) -> None:
        self._build_header()
        self._build_body()

    def _build_header(self) -> None:
        bar = ctk.CTkFrame(self, height=68, corner_radius=0, fg_color=th.BG_CARD)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.pack(side="left", padx=22, pady=12)

        brand_line = ctk.CTkFrame(left, fg_color="transparent")
        brand_line.pack(anchor="w")

        ctk.CTkLabel(
            brand_line,
            text="",
            image=th.logo_mark(size=(28, 28)),
        ).pack(side="left", padx=(0, 9))

        ctk.CTkLabel(
            brand_line,
            text="Panel de administración",
            font=th.bold(18),
            text_color=th.T_PRIMARY,
        ).pack(side="left")

        ctk.CTkLabel(
            left,
            text="Gestiona empleados, usuarios y registros de asistencia.",
            font=th.f(11),
            text_color=th.T_MUTED,
        ).pack(anchor="w", pady=(3, 0))

        # Bloque derecho: nombre + botón
        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right", padx=22, pady=14)

        ctk.CTkButton(
            right,
            text="Cerrar sesión",
            width=130,
            height=36,
            font=th.f(12),
            **th.quiet_button_kwargs(),
            command=self.on_logout,
        ).pack(side="right")

        ctk.CTkLabel(
            right,
            text=self.employee.full_name,
            font=th.f(12),
            text_color=th.T_SECONDARY,
        ).pack(side="right", padx=(0, 14))

        th.separator(self)

    def _build_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=th.PAGE_PAD, pady=16)

        # Fila de estadísticas
        self._build_stats_row(body)

        # Área de contenido (formulario + tablas)
        content = ctk.CTkFrame(body, fg_color="transparent")
        content.pack(fill="both", expand=True)
        content.columnconfigure(0, weight=0)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)
        content.rowconfigure(1, weight=1)

        self._build_create_form(content)
        self._build_user_list(content)
        self._build_attendance_list(content)

    # ── Fila de estadísticas ──────────────────────────────────────────────────

    def _build_stats_row(self, parent: ctk.CTkFrame) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 14))
        row.columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="stat")

        self._stat_clocked_lbl = self._stat_card(row, "Fichados ahora", "—", th.SUCCESS_TEXT, col=0)
        self._stat_active_lbl = self._stat_card(row, "Empleados activos", "—", th.T_PRIMARY, col=1)
        self._stat_hours_today_lbl = self._stat_card(row, "Horas hoy", "—", th.ACCENT, col=2)
        self._stat_incidents_lbl = self._stat_card(row, "Incidencias", "—", th.WARNING_TEXT, col=3)
        self._stat_today_lbl = self._stat_card(row, "Sesiones hoy", "—", th.ACCENT_SOFT, col=4)

    def _stat_card(
        self,
        parent: ctk.CTkFrame,
        title: str,
        initial: str,
        color: str,
        col: int,
    ) -> ctk.CTkLabel:
        """Crea una tarjeta de métrica y devuelve el label del valor."""
        if col == 0:
            padx = (0, 8)
        elif col == 4:
            padx = (8, 0)
        else:
            padx = (8, 8)
        card = ctk.CTkFrame(
            parent,
            fg_color=th.BG_RAISED,
            corner_radius=th.R_LG,
            border_width=1,
            border_color=th.BORDER,
        )
        card.grid(row=0, column=col, sticky="ew", padx=padx)

        ctk.CTkLabel(
            card,
            text=title.upper(),
            font=th.bold(9),
            text_color=th.T_MUTED,
        ).pack(anchor="w", padx=16, pady=(14, 2))

        value_lbl = ctk.CTkLabel(
            card,
            text=initial,
            font=ctk.CTkFont(family="Segoe UI", size=30, weight="bold"),
            text_color=color,
        )
        value_lbl.pack(anchor="w", padx=16, pady=(0, 14))
        return value_lbl

    def _animate_stat(self, label: ctk.CTkLabel, target: int, step: int = 0) -> None:
        """Cuenta desde 0 hasta target en pasos de ~40 ms (efecto numérico)."""
        if not self.winfo_exists():
            return
        if step <= target:
            label.configure(text=str(step))
            increment = max(1, (target - step) // 4 + 1)
            self.after(40, lambda: self._animate_stat(label, target, step + increment))
        else:
            label.configure(text=str(target))

    def _refresh_stats(self) -> None:
        active_count   = len([e for e in self._cached_employees if e.active])
        clocked_count  = len([s for s in self._cached_statuses.values() if s.is_clocked_in])
        today_str      = datetime.now().date().isoformat()
        today_sessions = len([
            r for r in self._cached_sessions
            if str(r.clock_in_time).startswith(today_str)
        ])
        incident_count = len([r for r in self._cached_sessions if r.has_incident])
        today_seconds = sum(
            summary.today.total_seconds
            for summary in self._cached_employee_summaries.values()
        )
        self._animate_stat(self._stat_clocked_lbl,  clocked_count)
        self._animate_stat(self._stat_active_lbl,   active_count)
        self._stat_hours_today_lbl.configure(text=self._format_hours(today_seconds))
        self._animate_stat(self._stat_incidents_lbl, incident_count)
        self._animate_stat(self._stat_today_lbl,    today_sessions)

    # ── Formulario de nuevo empleado ──────────────────────────────────────────

    def _build_create_form(self, parent: ctk.CTkFrame) -> None:
        card = th.card(parent, width=316)
        card.grid(row=0, column=0, rowspan=2, sticky="nsw", padx=(0, 14))
        card.grid_propagate(False)

        # Cabecera del formulario
        ctk.CTkLabel(
            card,
            text="Nuevo empleado",
            font=th.bold(15),
            text_color=th.T_PRIMARY,
        ).pack(anchor="w", padx=18, pady=(18, 4))

        ctk.CTkLabel(
            card,
            text="Los empleados inician sesión con su DNI y no tienen\npermisos de administrador.",
            font=th.f(11),
            text_color=th.T_MUTED,
            wraplength=268,
            justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 14))

        th.separator(card, padx=18, pady=(0, 14))

        # Campos del formulario
        self._new_first_name = self._field(card, "Nombre",      "Ana")
        self._new_last_name  = self._field(card, "Apellidos",   "López García")
        self._new_dni        = self._field(card, "DNI",         "12345678A")
        self._new_password   = self._field(
            card, "Contraseña", "mínimo 6 caracteres", show="•"
        )

        # Toast de estado
        self._create_status = ctk.CTkLabel(
            card,
            text="",
            font=th.f(11),
            text_color=th.SUCCESS_TEXT,
            fg_color="transparent",
            wraplength=268,
            corner_radius=th.R_SM,
            justify="left",
        )
        self._create_status.pack(fill="x", padx=18, pady=(14, 8))

        # Botón de crear
        self._create_btn = ctk.CTkButton(
            card,
            text="Crear empleado",
            height=44,
            font=th.bold(13),
            fg_color=th.SUCCESS,
            hover_color=th.SUCCESS_HOVER,
            corner_radius=th.R_MD,
            text_color="#071B10",
            command=self._create_employee,
        )
        self._create_btn.pack(fill="x", padx=18, pady=(0, 18))

    def _field(
        self,
        parent: ctk.CTkFrame,
        label: str,
        placeholder: str,
        **kwargs,
    ) -> ctk.CTkEntry:
        ctk.CTkLabel(
            parent,
            text=label.upper(),
            font=th.bold(9),
            text_color=th.T_MUTED,
            anchor="w",
        ).pack(fill="x", padx=18, pady=(10, 0))
        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            height=40,
            font=th.f(13),
            **th.entry_kwargs(),
            **kwargs,
        )
        entry.pack(fill="x", padx=18, pady=(4, 0))
        return entry

    # ── Tabla de usuarios ─────────────────────────────────────────────────────

    def _build_user_list(self, parent: ctk.CTkFrame) -> None:
        card = th.card(parent)
        card.grid(row=0, column=1, sticky="nsew", pady=(0, 12))
        card.rowconfigure(1, weight=1)
        card.columnconfigure(0, weight=1)

        # Header: title + action buttons
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 8))

        ctk.CTkLabel(
            header,
            text="Empleados registrados",
            font=th.bold(14),
            text_color=th.T_PRIMARY,
        ).pack(side="left")

        btn_row = ctk.CTkFrame(header, fg_color="transparent")
        btn_row.pack(side="right")

        ctk.CTkButton(
            btn_row,
            text="Activar / Desactivar",
            width=148,
            height=34,
            font=th.f(11),
            **th.quiet_button_kwargs(),
            command=self._toggle_selected_user,
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            btn_row,
            text="Contraseña",
            width=110,
            height=34,
            font=th.f(11),
            **th.quiet_button_kwargs(),
            command=self._open_password_dialog_for_selected,
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            btn_row,
            text="Editar",
            width=80,
            height=34,
            font=th.f(11),
            **th.quiet_button_kwargs(),
            command=self._open_edit_dialog_for_selected,
        ).pack(side="right")

        columns = (
            "name",
            "dni",
            "role",
            "active",
            "attendance",
            "today",
            "week",
            "month",
            "shifts",
            "avg",
        )
        self._users_tree = ttk.Treeview(
            card,
            columns=columns,
            show="headings",
            style="Fichaje.Treeview",
            selectmode="browse",
        )
        config = {
            "name":       ("Nombre",    155, "w"),
            "dni":        ("DNI",       105, "center"),
            "role":       ("Rol",        78, "center"),
            "active":     ("Activo",     62, "center"),
            "attendance": ("Estado",     94, "center"),
            "today":      ("Hoy",        72, "center"),
            "week":       ("Semana",     78, "center"),
            "month":      ("Mes",        78, "center"),
            "shifts":     ("Turnos mes", 82, "center"),
            "avg":        ("Media",      76, "center"),
        }
        for col, (heading, width, anchor) in config.items():
            self._users_tree.heading(col, text=heading)
            self._users_tree.column(col, width=width, anchor=anchor)

        self._users_tree.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 4))

        self._user_status = ctk.CTkLabel(
            card,
            text="",
            font=th.f(11),
            text_color=th.SUCCESS_TEXT,
            fg_color="transparent",
            corner_radius=th.R_SM,
        )
        self._user_status.grid(row=2, column=0, sticky="w", padx=14, pady=(0, 10))

    # ── Tabla de sesiones de asistencia ──────────────────────────────────────

    def _build_attendance_list(self, parent: ctk.CTkFrame) -> None:
        card = th.card(parent)
        card.grid(row=1, column=1, sticky="nsew")
        card.rowconfigure(2, weight=1)   # row 0=header, 1=filters, 2=treeview, 3=status
        card.columnconfigure(0, weight=1)

        # Header: title + action buttons
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))

        ctk.CTkLabel(
            header,
            text="Registros de asistencia",
            font=th.bold(14),
            text_color=th.T_PRIMARY,
        ).pack(side="left")

        btn_row = ctk.CTkFrame(header, fg_color="transparent")
        btn_row.pack(side="right")

        ctk.CTkButton(
            btn_row,
            text="Actualizar",
            width=100,
            height=34,
            font=th.f(11),
            **th.quiet_button_kwargs(),
            command=self._manual_refresh,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            btn_row,
            text="Cerrar turno",
            width=110,
            height=34,
            font=th.f(11),
            fg_color=th.WARNING_DIM,
            hover_color=th.WARNING_DIM,
            border_width=1,
            border_color=th.WARNING,
            text_color=th.WARNING_TEXT,
            corner_radius=th.R_MD,
            command=self._open_admin_close_dialog_for_selected,
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            btn_row,
            text="Exportar a Excel",
            width=130,
            height=34,
            font=th.f(11),
            **th.primary_button_kwargs(),
            command=self._export_entries,
        ).pack(side="left")

        # Barra de filtros
        self._build_session_filters(card)

        # Treeview de sesiones
        columns = (
            "employee",
            "dni",
            "in",
            "out",
            "duration",
            "status",
            "incidents",
            "notes",
        )
        self._sessions_tree = ttk.Treeview(
            card,
            columns=columns,
            show="headings",
            style="Fichaje.Treeview",
            selectmode="browse",
        )
        config = {
            "employee":  ("Empleado",    150, "w"),
            "dni":       ("DNI",          95, "center"),
            "in":        ("Entrada",     130, "center"),
            "out":       ("Salida",      130, "center"),
            "duration":  ("Duración",     90, "center"),
            "status":    ("Estado",       90, "center"),
            "incidents": ("Incidencias", 170, "w"),
            "notes":     ("Notas",       160, "w"),
        }
        for col, (heading, width, anchor) in config.items():
            self._sessions_tree.heading(col, text=heading)
            self._sessions_tree.column(col, width=width, anchor=anchor)

        self._sessions_tree.tag_configure("warning", foreground=th.WARNING_TEXT)
        self._sessions_tree.tag_configure("critical", foreground=th.DANGER_TEXT)

        self._sessions_tree.grid(row=2, column=0, sticky="nsew", padx=8, pady=(0, 4))

        self._export_status = ctk.CTkLabel(
            card,
            text="",
            font=th.f(11),
            text_color=th.SUCCESS_TEXT,
            fg_color="transparent",
            corner_radius=th.R_SM,
        )
        self._export_status.grid(row=3, column=0, sticky="w", padx=14, pady=(0, 10))

    def _build_session_filters(self, card: ctk.CTkFrame) -> None:
        """Compact filter bar for the sessions table."""
        bar = ctk.CTkFrame(card, fg_color=th.BG_RAISED, corner_radius=th.R_MD)
        bar.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 6))

        def lbl(text: str) -> ctk.CTkLabel:
            return ctk.CTkLabel(
                bar,
                text=text,
                font=th.bold(9),
                text_color=th.T_MUTED,
            )

        def small_entry(width: int = 100) -> ctk.CTkEntry:
            return ctk.CTkEntry(
                bar,
                width=width,
                height=30,
                font=th.f(11),
                **th.entry_kwargs(),
            )

        pad = {"side": "left", "padx": (6, 0), "pady": 6}

        lbl("DESDE").pack(**pad)
        self._filter_from = small_entry()
        self._filter_from.pack(**pad)
        self._filter_from.insert(0, "")

        lbl("HASTA").pack(side="left", padx=(10, 0), pady=6)
        self._filter_to = small_entry()
        self._filter_to.pack(**pad)

        lbl("EMPLEADO").pack(side="left", padx=(10, 0), pady=6)
        self._filter_emp_var = StringVar(value="Todos")
        self._filter_emp_combo = ctk.CTkComboBox(
            bar,
            width=150,
            height=30,
            font=th.f(11),
            values=["Todos"],
            variable=self._filter_emp_var,
            fg_color=th.BG_FIELD,
            border_color=th.BORDER_LT,
            border_width=1,
            button_color=th.BORDER_LT,
            button_hover_color=th.BG_HOVER,
            dropdown_fg_color=th.BG_CARD,
            dropdown_text_color=th.T_PRIMARY,
            text_color=th.T_PRIMARY,
            corner_radius=th.R_MD,
        )
        self._filter_emp_combo.pack(**pad)

        lbl("ESTADO").pack(side="left", padx=(10, 0), pady=6)
        self._filter_status_var = StringVar(value="Todos")
        ctk.CTkComboBox(
            bar,
            width=110,
            height=30,
            font=th.f(11),
            values=["Todos", "Activos", "Cerrados"],
            variable=self._filter_status_var,
            fg_color=th.BG_FIELD,
            border_color=th.BORDER_LT,
            border_width=1,
            button_color=th.BORDER_LT,
            button_hover_color=th.BG_HOVER,
            dropdown_fg_color=th.BG_CARD,
            dropdown_text_color=th.T_PRIMARY,
            text_color=th.T_PRIMARY,
            corner_radius=th.R_MD,
        ).pack(**pad)

        lbl("INCIDENCIA").pack(side="left", padx=(10, 0), pady=6)
        self._filter_incidence_var = StringVar(value="Todas")
        ctk.CTkComboBox(
            bar,
            width=150,
            height=30,
            font=th.f(11),
            values=["Todas", "Incidencias", "Abiertas ant.", ">8h", ">10h", ">12h"],
            variable=self._filter_incidence_var,
            fg_color=th.BG_FIELD,
            border_color=th.BORDER_LT,
            border_width=1,
            button_color=th.BORDER_LT,
            button_hover_color=th.BG_HOVER,
            dropdown_fg_color=th.BG_CARD,
            dropdown_text_color=th.T_PRIMARY,
            text_color=th.T_PRIMARY,
            corner_radius=th.R_MD,
        ).pack(**pad)

        ctk.CTkButton(
            bar,
            text="Filtrar",
            width=70,
            height=30,
            font=th.f(11),
            **th.primary_button_kwargs(),
            command=self._apply_session_filters,
        ).pack(side="left", padx=(10, 0), pady=6)

        ctk.CTkButton(
            bar,
            text="Limpiar",
            width=70,
            height=30,
            font=th.f(11),
            **th.quiet_button_kwargs(),
            command=self._clear_session_filters,
        ).pack(side="left", padx=(4, 6), pady=6)

    # ── Carga de datos ────────────────────────────────────────────────────────

    def _reload_all(self) -> None:
        self._reload_users()
        self._reload_sessions()
        self._refresh_stats()

    def _reload_users(self) -> None:
        self._users_tree.delete(*self._users_tree.get_children())
        self._cached_employees = self.employee_service.list_employees()
        self._cached_statuses = {
            status.employee.id: status
            for status in self.time_clock_service.get_attendance_statuses(self._cached_employees)
        }
        employee_ids = [
            employee.id
            for employee in self._cached_employees
            if employee.role == "employee"
        ]
        self._cached_employee_summaries = (
            self.attendance_report_service.get_current_period_summaries(employee_ids)
        )

        # Rebuild employee filter map
        self._employee_name_to_id = {}
        emp_names = ["Todos"]
        for emp in self._cached_employees:
            if emp.role == "employee":
                self._employee_name_to_id[emp.full_name] = emp.id
                emp_names.append(emp.full_name)

        self._filter_emp_combo.configure(values=emp_names)
        if self._filter_emp_var.get() not in emp_names:
            self._filter_emp_var.set("Todos")

        for emp in self._cached_employees:
            status = self._cached_statuses.get(emp.id)
            is_clocked = status.is_clocked_in if status else False
            summary = self._cached_employee_summaries.get(emp.id)
            month_summary = summary.month if summary else None

            self._users_tree.insert(
                "",
                "end",
                iid=str(emp.id),
                values=(
                    emp.full_name,
                    emp.dni,
                    emp.role,
                    "Sí" if emp.active else "No",
                    "Fichado" if is_clocked else "Sin fichar",
                    self._format_hours(summary.today.total_seconds) if summary else "—",
                    self._format_hours(summary.week.total_seconds) if summary else "—",
                    self._format_hours(summary.month.total_seconds) if summary else "—",
                    str(month_summary.shift_count) if month_summary else "—",
                    self._format_hours(month_summary.average_seconds)
                    if month_summary
                    else "—",
                ),
            )

    def _reload_sessions(self) -> None:
        """Reload session table, respecting active filter values."""
        self._sessions_tree.delete(*self._sessions_tree.get_children())

        date_from = self._filter_from.get().strip() or None
        date_to   = self._filter_to.get().strip() or None

        emp_name  = self._filter_emp_var.get()
        user_id   = self._employee_name_to_id.get(emp_name) if emp_name != "Todos" else None

        status_sel = self._filter_status_var.get()
        is_active  = None
        if status_sel == "Activos":
            is_active = 1
        elif status_sel == "Cerrados":
            is_active = 0

        self._cached_sessions = self.attendance_report_service.list_session_reports(
            date_from=date_from,
            date_to=date_to,
            user_id=user_id,
            is_active=is_active,
            incident_filter=self._selected_incident_filter(),
        )

        for row in self._cached_sessions:
            tags = ()
            if row.severity == "critical":
                tags = ("critical",)
            elif row.severity == "warning":
                tags = ("warning",)

            self._sessions_tree.insert(
                "",
                "end",
                iid=str(row.id),
                values=(
                    row.employee_name,
                    row.dni,
                    format_timestamp(row.clock_in_time),
                    format_timestamp(row.clock_out_time) if row.clock_out_time else "—",
                    self._format_session_duration(row),
                    row.status_label,
                    row.incident_label,
                    row.notes_label or "—",
                ),
                tags=tags,
            )

    # ── Acciones de usuario ───────────────────────────────────────────────────

    def _create_employee(self) -> None:
        self._create_btn.configure(state="disabled", text="Guardando...")
        self.update_idletasks()

        try:
            self.employee_service.create_employee(
                first_name=self._new_first_name.get(),
                last_name=self._new_last_name.get(),
                dni=self._new_dni.get(),
                password=self._new_password.get(),
                role="employee",
            )
        except ValueError as exc:
            self._create_btn.configure(state="normal", text="Crear empleado")
            self._toast(self._create_status, f"  ✕  {exc}", th.DANGER_TEXT, th.DANGER_DIM, key="create")
            return

        self._create_btn.configure(state="normal", text="Crear empleado")
        full_name = (
            f"{self._new_first_name.get().strip()} {self._new_last_name.get().strip()}"
        ).strip()
        self._toast(self._create_status, f"  ✓  {full_name} creado correctamente.", th.SUCCESS_TEXT, th.SUCCESS_DIM, key="create")

        for entry in (self._new_first_name, self._new_last_name, self._new_dni, self._new_password):
            entry.delete(0, "end")
        self._reload_all()

    def _toggle_selected_user(self) -> None:
        selected = self._users_tree.selection()
        if not selected:
            self._toast(self._user_status, "  ✕  Selecciona un empleado primero.", th.DANGER_TEXT, th.DANGER_DIM, key="user")
            return

        user_id = int(selected[0])
        try:
            new_state = self.employee_service.toggle_active(user_id)
        except ValueError as exc:
            self._toast(self._user_status, f"  ✕  {exc}", th.DANGER_TEXT, th.DANGER_DIM, key="user")
            return

        self._toast(
            self._user_status,
            "  ✓  Usuario activado." if new_state else "  ✕  Usuario desactivado.",
            th.SUCCESS_TEXT if new_state else th.WARNING_TEXT,
            th.SUCCESS_DIM if new_state else th.WARNING_DIM,
            key="user",
        )
        self._reload_users()
        self._refresh_stats()

    def _open_edit_dialog_for_selected(self) -> None:
        selected = self._users_tree.selection()
        if not selected:
            self._toast(self._user_status, "  ✕  Selecciona un empleado primero.", th.DANGER_TEXT, th.DANGER_DIM, key="user")
            return
        user_id = int(selected[0])
        employee = next((e for e in self._cached_employees if e.id == user_id), None)
        if not employee:
            return
        self._open_edit_dialog(employee)

    def _open_password_dialog_for_selected(self) -> None:
        selected = self._users_tree.selection()
        if not selected:
            self._toast(self._user_status, "  ✕  Selecciona un empleado primero.", th.DANGER_TEXT, th.DANGER_DIM, key="user")
            return
        user_id = int(selected[0])
        employee = next((e for e in self._cached_employees if e.id == user_id), None)
        if not employee:
            return
        self._open_password_dialog(employee)

    # ── Diálogo: editar empleado ──────────────────────────────────────────────

    def _open_edit_dialog(self, employee: Employee) -> None:
        dlg = ctk.CTkToplevel(self)
        dlg.title("Editar empleado")
        dlg.geometry("440x490")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.configure(fg_color=th.BG_CARD)
        dlg.focus_force()

        ctk.CTkLabel(
            dlg, text="Editar empleado", font=th.bold(16), text_color=th.T_PRIMARY
        ).pack(anchor="w", padx=22, pady=(20, 2))
        ctk.CTkLabel(
            dlg, text=employee.full_name, font=th.f(12), text_color=th.T_MUTED
        ).pack(anchor="w", padx=22, pady=(0, 14))
        th.separator(dlg, padx=22, pady=(0, 14))

        def lbl(text: str) -> None:
            ctk.CTkLabel(dlg, text=text.upper(), font=th.bold(9), text_color=th.T_MUTED, anchor="w").pack(fill="x", padx=22, pady=(10, 0))

        def entry(initial: str = "", **kwargs) -> ctk.CTkEntry:
            e = ctk.CTkEntry(dlg, height=38, font=th.f(13), **th.entry_kwargs(), **kwargs)
            e.pack(fill="x", padx=22, pady=(4, 0))
            e.insert(0, initial)
            return e

        lbl("Nombre")
        first_entry = entry(employee.first_name)

        lbl("Apellidos")
        last_entry = entry(employee.last_name)

        lbl("DNI")
        dni_entry = entry(employee.dni)

        lbl("Rol")
        role_var = StringVar(value=employee.role)
        ctk.CTkComboBox(
            dlg,
            height=38,
            font=th.f(13),
            values=["employee", "admin"],
            variable=role_var,
            fg_color=th.BG_FIELD,
            border_color=th.BORDER_LT,
            border_width=1,
            button_color=th.BORDER_LT,
            button_hover_color=th.BG_HOVER,
            dropdown_fg_color=th.BG_CARD,
            dropdown_text_color=th.T_PRIMARY,
            text_color=th.T_PRIMARY,
            corner_radius=th.R_MD,
        ).pack(fill="x", padx=22, pady=(4, 0))

        active_var = ctk.BooleanVar(value=employee.active)
        ctk.CTkCheckBox(
            dlg,
            text="Empleado activo",
            font=th.f(12),
            text_color=th.T_PRIMARY,
            variable=active_var,
            fg_color=th.ACCENT,
            hover_color=th.ACCENT_HOVER,
        ).pack(anchor="w", padx=22, pady=(14, 0))

        status_lbl = ctk.CTkLabel(
            dlg, text="", font=th.f(11), text_color=th.DANGER_TEXT,
            fg_color="transparent", wraplength=390, justify="left",
        )
        status_lbl.pack(fill="x", padx=22, pady=(10, 0))

        def _save():
            try:
                self.employee_service.update_employee(
                    employee.id,
                    first_name=first_entry.get(),
                    last_name=last_entry.get(),
                    dni=dni_entry.get(),
                    role=role_var.get(),
                    active=active_var.get(),
                )
            except ValueError as exc:
                status_lbl.configure(text=f"✕  {exc}", text_color=th.DANGER_TEXT)
                return
            dlg.destroy()
            self._toast(self._user_status, "  ✓  Empleado actualizado correctamente.", th.SUCCESS_TEXT, th.SUCCESS_DIM, key="user")
            self._reload_all()

        ctk.CTkButton(
            dlg, text="Guardar cambios", height=42, font=th.bold(13),
            fg_color=th.ACCENT, hover_color=th.ACCENT_HOVER,
            text_color="#062421", corner_radius=th.R_MD,
            command=_save,
        ).pack(fill="x", padx=22, pady=(14, 6))

        ctk.CTkButton(
            dlg, text="Cancelar", height=36, font=th.f(12),
            **th.quiet_button_kwargs(), command=dlg.destroy,
        ).pack(fill="x", padx=22, pady=(0, 18))

    # ── Diálogo: cambiar contraseña ───────────────────────────────────────────

    def _open_password_dialog(self, employee: Employee) -> None:
        dlg = ctk.CTkToplevel(self)
        dlg.title("Cambiar contraseña")
        dlg.geometry("440x420")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.configure(fg_color=th.BG_CARD)
        dlg.focus_force()

        ctk.CTkLabel(
            dlg, text="Cambiar contraseña", font=th.bold(16), text_color=th.T_PRIMARY
        ).pack(anchor="w", padx=22, pady=(20, 2))
        ctk.CTkLabel(
            dlg, text=employee.full_name, font=th.f(12), text_color=th.T_MUTED
        ).pack(anchor="w", padx=22, pady=(0, 14))
        th.separator(dlg, padx=22, pady=(0, 14))

        ctk.CTkLabel(dlg, text="NUEVA CONTRASEÑA", font=th.bold(9), text_color=th.T_MUTED, anchor="w").pack(fill="x", padx=22, pady=(6, 0))
        pass_entry = ctk.CTkEntry(dlg, height=38, font=th.f(13), show="•", **th.entry_kwargs())
        pass_entry.pack(fill="x", padx=22, pady=(4, 0))

        ctk.CTkLabel(dlg, text="CONFIRMAR CONTRASEÑA", font=th.bold(9), text_color=th.T_MUTED, anchor="w").pack(fill="x", padx=22, pady=(10, 0))
        confirm_entry = ctk.CTkEntry(dlg, height=38, font=th.f(13), show="•", **th.entry_kwargs())
        confirm_entry.pack(fill="x", padx=22, pady=(4, 0))

        status_lbl = ctk.CTkLabel(
            dlg, text="", font=th.f(11), text_color=th.DANGER_TEXT,
            fg_color="transparent", wraplength=390, justify="left",
        )
        status_lbl.pack(fill="x", padx=22, pady=(10, 0))

        def _save():
            new_pass = pass_entry.get()
            confirm  = confirm_entry.get()
            if new_pass != confirm:
                status_lbl.configure(text="✕  Las contraseñas no coinciden.", text_color=th.DANGER_TEXT)
                return
            try:
                self.employee_service.set_password(employee.id, new_pass)
            except ValueError as exc:
                status_lbl.configure(text=f"✕  {exc}", text_color=th.DANGER_TEXT)
                return
            dlg.destroy()
            self._toast(self._user_status, "  ✓  Contraseña actualizada.", th.SUCCESS_TEXT, th.SUCCESS_DIM, key="user")

        def _generate():
            try:
                temp = self.employee_service.reset_password(employee.id)
            except Exception as exc:
                status_lbl.configure(text=f"✕  {exc}", text_color=th.DANGER_TEXT)
                return
            status_lbl.configure(
                text=f"✓  Contraseña temporal generada: {temp}  —  Comunícasela al empleado.",
                text_color=th.WARNING_TEXT,
            )
            # Prefill fields so admin can see and verify before closing
            pass_entry.delete(0, "end")
            pass_entry.insert(0, temp)
            confirm_entry.delete(0, "end")
            confirm_entry.insert(0, temp)

        ctk.CTkButton(
            dlg, text="Guardar contraseña", height=42, font=th.bold(13),
            fg_color=th.ACCENT, hover_color=th.ACCENT_HOVER,
            text_color="#062421", corner_radius=th.R_MD,
            command=_save,
        ).pack(fill="x", padx=22, pady=(14, 6))

        ctk.CTkButton(
            dlg, text="Generar contraseña temporal", height=36, font=th.f(12),
            fg_color=th.WARNING_DIM, hover_color=th.WARNING_DIM,
            border_width=1, border_color=th.WARNING,
            text_color=th.WARNING_TEXT, corner_radius=th.R_MD,
            command=_generate,
        ).pack(fill="x", padx=22, pady=(0, 6))

        ctk.CTkButton(
            dlg, text="Cancelar", height=36, font=th.f(12),
            **th.quiet_button_kwargs(), command=dlg.destroy,
        ).pack(fill="x", padx=22, pady=(0, 18))

    # ── Diálogo: cierre manual de turno ──────────────────────────────────────

    def _open_admin_close_dialog_for_selected(self) -> None:
        selected = self._sessions_tree.selection()
        if not selected:
            self._toast(self._export_status, "  ✕  Selecciona una sesión primero.", th.DANGER_TEXT, th.DANGER_DIM, key="export")
            return

        session_id = int(selected[0])
        session_row = next((r for r in self._cached_sessions if r.id == session_id), None)
        if not session_row:
            return
        if not session_row.is_active:
            self._toast(self._export_status, "  ✕  La sesión seleccionada ya está cerrada.", th.DANGER_TEXT, th.DANGER_DIM, key="export")
            return

        self._open_admin_close_dialog(session_id, session_row)

    def _open_admin_close_dialog(self, session_id: int, session_row: SessionReport) -> None:
        dlg = ctk.CTkToplevel(self)
        dlg.title("Cerrar turno manualmente")
        dlg.geometry("440x340")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.configure(fg_color=th.BG_CARD)
        dlg.focus_force()

        ctk.CTkLabel(
            dlg, text="Cerrar turno manualmente", font=th.bold(16), text_color=th.WARNING_TEXT
        ).pack(anchor="w", padx=22, pady=(20, 2))

        # Session info
        emp_name    = session_row.employee_name or "—"
        clock_in    = format_timestamp(session_row.clock_in_time)
        info_text   = f"{emp_name}  ·  Entrada: {clock_in}"
        ctk.CTkLabel(
            dlg, text=info_text, font=th.f(11), text_color=th.T_MUTED
        ).pack(anchor="w", padx=22, pady=(0, 14))
        th.separator(dlg, padx=22, pady=(0, 14))

        ctk.CTkLabel(
            dlg,
            text="Esta acción cerrará el turno ahora mismo con la hora actual.\nEl cierre quedará registrado como administrativo.",
            font=th.f(11),
            text_color=th.T_SECONDARY,
            wraplength=390,
            justify="left",
        ).pack(anchor="w", padx=22, pady=(0, 14))

        ctk.CTkLabel(dlg, text="MOTIVO DEL CIERRE *", font=th.bold(9), text_color=th.T_MUTED, anchor="w").pack(fill="x", padx=22, pady=(0, 0))
        reason_entry = ctk.CTkEntry(dlg, height=38, font=th.f(13), placeholder_text="Obligatorio", **th.entry_kwargs())
        reason_entry.pack(fill="x", padx=22, pady=(4, 0))

        status_lbl = ctk.CTkLabel(
            dlg, text="", font=th.f(11), text_color=th.DANGER_TEXT,
            fg_color="transparent", wraplength=390,
        )
        status_lbl.pack(fill="x", padx=22, pady=(8, 0))

        def _confirm():
            try:
                self.time_clock_service.admin_close_session(
                    session_id,
                    reason=reason_entry.get(),
                    admin_user_id=self.employee.id,
                )
            except ValueError as exc:
                status_lbl.configure(text=f"✕  {exc}", text_color=th.DANGER_TEXT)
                return
            dlg.destroy()
            self._toast(self._export_status, "  ✓  Turno cerrado manualmente.", th.SUCCESS_TEXT, th.SUCCESS_DIM, key="export")
            self._reload_all()

        ctk.CTkButton(
            dlg, text="Confirmar cierre", height=42, font=th.bold(13),
            fg_color=th.DANGER, hover_color=th.DANGER_HOVER,
            text_color="#FFF", corner_radius=th.R_MD,
            command=_confirm,
        ).pack(fill="x", padx=22, pady=(14, 6))

        ctk.CTkButton(
            dlg, text="Cancelar", height=36, font=th.f(12),
            **th.quiet_button_kwargs(), command=dlg.destroy,
        ).pack(fill="x", padx=22, pady=(0, 18))

    # ── Filtros de sesiones ───────────────────────────────────────────────────

    def _apply_session_filters(self) -> None:
        self._reload_sessions()
        self._refresh_stats()

    def _clear_session_filters(self) -> None:
        self._filter_from.delete(0, "end")
        self._filter_to.delete(0, "end")
        self._filter_emp_var.set("Todos")
        self._filter_status_var.set("Todos")
        self._filter_incidence_var.set("Todas")
        self._reload_sessions()
        self._refresh_stats()

    # ── Exportar ──────────────────────────────────────────────────────────────

    def _export_entries(self) -> None:
        emp_name = self._filter_emp_var.get()
        user_id = self._employee_name_to_id.get(emp_name) if emp_name != "Todos" else None
        try:
            path = self.export_service.export_time_entries_to_excel(
                date_from=self._filter_from.get().strip() or None,
                date_to=self._filter_to.get().strip() or None,
                employee_id=user_id,
            )
        except RuntimeError as exc:
            self._toast(self._export_status, f"  ✕  {exc}", th.DANGER_TEXT, th.DANGER_DIM, key="export")
            return

        self._toast(self._export_status, f"  ✓  Exportación guardada: {path}", th.SUCCESS_TEXT, th.SUCCESS_DIM, key="export")

    # ── Auto-refresco ─────────────────────────────────────────────────────────

    def _manual_refresh(self) -> None:
        self._reload_users()
        self._reload_sessions()
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
            self._reload_users()
            self._reload_sessions()
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

    # ── Toast de notificación con auto-dismiss ────────────────────────────────

    def _toast(
        self,
        label: ctk.CTkLabel,
        message: str,
        text_color: str,
        bg_color: str,
        *,
        key: str,
    ) -> None:
        """Muestra un mensaje en `label` y lo borra automáticamente."""
        label.configure(text=message, text_color=text_color, fg_color=bg_color)

        if key in self._toast_after_ids:
            try:
                self.after_cancel(self._toast_after_ids[key])
            except Exception:
                pass

        def dismiss():
            if self.winfo_exists():
                label.configure(text="", fg_color="transparent")
            self._toast_after_ids.pop(key, None)

        self._toast_after_ids[key] = self.after(_TOAST_DISMISS_MS, dismiss)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _seconds_since(self, timestamp: str) -> int:
        try:
            started = datetime.fromisoformat(timestamp)
        except (TypeError, ValueError):
            return 0
        return max(int((datetime.now() - started).total_seconds()), 0)

    def _selected_incident_filter(self) -> str:
        selected = self._filter_incidence_var.get()
        return {
            "Incidencias": AttendanceReportService.INCIDENT_FILTER_ANY,
            "Abiertas ant.": AttendanceReportService.INCIDENT_FILTER_PREVIOUS_OPEN,
            ">8h": AttendanceReportService.INCIDENT_FILTER_EXCESS_8,
            ">10h": AttendanceReportService.INCIDENT_FILTER_EXCESS_10,
            ">12h": AttendanceReportService.INCIDENT_FILTER_EXCESS_12,
        }.get(selected, AttendanceReportService.INCIDENT_FILTER_ALL)

    def _format_seconds(self, total_seconds: int) -> str:
        hours, remainder = divmod(max(int(total_seconds), 0), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _format_hours(self, total_seconds: int | None) -> str:
        if total_seconds is None:
            return "—"
        hours, remainder = divmod(max(int(total_seconds), 0), 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours}h {minutes:02d}m"

    def _format_session_duration(self, row: SessionReport) -> str:
        if row.is_active:
            elapsed = row.display_duration_seconds or 0
            return f"En curso {self._format_seconds(elapsed)}"
        return self._format_seconds(row.counted_duration_seconds or 0)
