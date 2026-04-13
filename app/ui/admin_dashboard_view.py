from collections.abc import Callable
from datetime import datetime
from tkinter import ttk

import customtkinter as ctk

from app.models.employee import Employee
from app.services.employee_service import EmployeeService
from app.services.export_service import ExportService
from app.services.time_clock_service import TimeClockService
from app.ui import theme as th
from app.utils.helpers import format_timestamp


def _style_treeview() -> None:
    style = ttk.Style()
    style.theme_use("default")
    style.configure(
        "Fichaje.Treeview",
        background=th.BG_RAISED,
        foreground=th.T_PRIMARY,
        fieldbackground=th.BG_RAISED,
        rowheight=32,
        font=("Segoe UI", 10),
        borderwidth=0,
    )
    style.configure(
        "Fichaje.Treeview.Heading",
        background=th.BG_CARD,
        foreground=th.T_SECONDARY,
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
        time_clock_service: TimeClockService,
        on_logout: Callable[[], None],
    ) -> None:
        super().__init__(master, corner_radius=0, fg_color=th.BG_ROOT)
        self.employee = employee
        self.employee_service = employee_service
        self.export_service = export_service
        self.time_clock_service = time_clock_service
        self.on_logout = on_logout

        _style_treeview()
        self._build()
        self._reload_all()

    def _build(self) -> None:
        self._build_header()
        self._build_body()

    def _build_header(self) -> None:
        bar = ctk.CTkFrame(self, height=72, corner_radius=0, fg_color=th.BG_CARD)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.pack(side="left", padx=22, pady=14)

        brand_line = ctk.CTkFrame(left, fg_color="transparent")
        brand_line.pack(anchor="w")
        ctk.CTkLabel(
            brand_line,
            text="",
            image=th.logo_mark(size=(28, 28)),
        ).pack(side="left", padx=(0, 9))
        ctk.CTkLabel(
            brand_line,
            text="Admin panel",
            font=th.bold(19),
            text_color=th.T_PRIMARY,
        ).pack(side="left")
        ctk.CTkLabel(
            left,
            text="Create employees, review users, and monitor attendance.",
            font=th.f(11),
            text_color=th.T_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        ctk.CTkButton(
            bar,
            text="Log out",
            width=128,
            height=36,
            font=th.f(12),
            **th.quiet_button_kwargs(),
            command=self.on_logout,
        ).pack(side="right", padx=22, pady=18)

        ctk.CTkLabel(
            bar,
            text=self.employee.full_name,
            font=th.f(12),
            text_color=th.T_SECONDARY,
        ).pack(side="right", padx=(0, 12), pady=20)

        th.separator(self)

    def _build_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=th.PAGE_PAD, pady=18)
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(1, weight=1)

        self._build_create_form(body)
        self._build_user_list(body)
        self._build_attendance_list(body)

    def _build_create_form(self, parent: ctk.CTkFrame) -> None:
        card = th.card(parent, width=320)
        card.grid(row=0, column=0, rowspan=2, sticky="nsw", padx=(0, 14))
        card.grid_propagate(False)

        ctk.CTkLabel(
            card,
            text="New employee",
            font=th.bold(16),
            text_color=th.T_PRIMARY,
        ).pack(anchor="w", padx=18, pady=(18, 4))
        ctk.CTkLabel(
            card,
            text="Normal users always log in with DNI and have no admin permissions.",
            font=th.f(11),
            text_color=th.T_MUTED,
            wraplength=270,
            justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 14))

        self._new_first_name = self._field(card, "First name", "Ana")
        self._new_last_name = self._field(card, "Last name", "Lopez")
        self._new_dni = self._field(card, "DNI", "12345678A")
        self._new_password = self._field(
            card,
            "Password",
            "minimum 6 characters",
            show="*",
        )

        self._create_status = ctk.CTkLabel(
            card,
            text="",
            font=th.f(12),
            text_color=th.SUCCESS_TEXT,
            wraplength=270,
        )
        self._create_status.pack(fill="x", padx=18, pady=(14, 8))

        ctk.CTkButton(
            card,
            text="Create employee",
            height=44,
            font=th.bold(13),
            fg_color=th.SUCCESS,
            hover_color=th.SUCCESS_HOVER,
            corner_radius=th.R_MD,
            text_color="#071B10",
            command=self._create_employee,
        ).pack(fill="x", padx=18, pady=(0, 18))

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
            text_color=th.T_SECONDARY,
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

    def _build_user_list(self, parent: ctk.CTkFrame) -> None:
        card = th.card(parent)
        card.grid(row=0, column=1, sticky="nsew", pady=(0, 14))
        card.rowconfigure(1, weight=1)
        card.columnconfigure(0, weight=1)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 8))
        ctk.CTkLabel(
            header,
            text="Existing users",
            font=th.bold(15),
            text_color=th.T_PRIMARY,
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="Toggle active",
            width=120,
            height=34,
            font=th.f(12),
            **th.quiet_button_kwargs(),
            command=self._toggle_selected_user,
        ).pack(side="right")

        columns = ("name", "dni", "role", "active", "attendance", "created")
        self._users_tree = ttk.Treeview(
            card,
            columns=columns,
            show="headings",
            style="Fichaje.Treeview",
            selectmode="browse",
        )
        config = {
            "name": ("Name", 190, "w"),
            "dni": ("DNI", 120, "center"),
            "role": ("Role", 90, "center"),
            "active": ("Active", 80, "center"),
            "attendance": ("Status", 110, "center"),
            "created": ("Created", 120, "center"),
        }
        for column, (heading, width, anchor) in config.items():
            self._users_tree.heading(column, text=heading)
            self._users_tree.column(column, width=width, anchor=anchor)

        self._users_tree.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        self._user_status = ctk.CTkLabel(
            card,
            text="",
            font=th.f(12),
            text_color=th.SUCCESS_TEXT,
        )
        self._user_status.grid(row=2, column=0, sticky="w", padx=14, pady=(0, 10))

    def _build_attendance_list(self, parent: ctk.CTkFrame) -> None:
        card = th.card(parent)
        card.grid(row=1, column=1, sticky="nsew")
        card.rowconfigure(1, weight=1)
        card.columnconfigure(0, weight=1)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 8))
        ctk.CTkLabel(
            header,
            text="Attendance sessions",
            font=th.bold(15),
            text_color=th.T_PRIMARY,
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="Export entries",
            width=120,
            height=34,
            font=th.f(12),
            **th.primary_button_kwargs(),
            command=self._export_entries,
        ).pack(side="right")

        columns = ("employee", "dni", "in", "out", "duration", "status")
        self._sessions_tree = ttk.Treeview(
            card,
            columns=columns,
            show="headings",
            style="Fichaje.Treeview",
            selectmode="browse",
        )
        config = {
            "employee": ("Employee", 180, "w"),
            "dni": ("DNI", 120, "center"),
            "in": ("Clock In", 145, "center"),
            "out": ("Clock Out", 145, "center"),
            "duration": ("Duration", 90, "center"),
            "status": ("Status", 90, "center"),
        }
        for column, (heading, width, anchor) in config.items():
            self._sessions_tree.heading(column, text=heading)
            self._sessions_tree.column(column, width=width, anchor=anchor)

        self._sessions_tree.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

        self._export_status = ctk.CTkLabel(
            card,
            text="",
            font=th.f(12),
            text_color=th.SUCCESS_TEXT,
        )
        self._export_status.grid(row=2, column=0, sticky="w", padx=14, pady=(0, 10))

    def _reload_all(self) -> None:
        self._reload_users()
        self._reload_sessions()

    def _reload_users(self) -> None:
        self._users_tree.delete(*self._users_tree.get_children())
        employees = self.employee_service.list_employees()
        statuses = {
            status.employee.id: status
            for status in self.time_clock_service.get_attendance_statuses(employees)
        }

        for employee in employees:
            status = statuses.get(employee.id)
            self._users_tree.insert(
                "",
                "end",
                iid=str(employee.id),
                values=(
                    employee.full_name,
                    employee.dni,
                    employee.role,
                    "Yes" if employee.active else "No",
                    status.status_label if status else "Clocked Out",
                    format_timestamp(employee.created_at, "%d/%m/%Y")
                    if employee.created_at
                    else "",
                ),
            )

    def _reload_sessions(self) -> None:
        self._sessions_tree.delete(*self._sessions_tree.get_children())
        rows = self.time_clock_service.attendance_session_repository.list_with_user_names()

        for row in rows:
            total_seconds = row["total_seconds"]
            if row["is_active"]:
                total_seconds = self._seconds_since(row["clock_in_time"])

            self._sessions_tree.insert(
                "",
                "end",
                values=(
                    row["employee_name"],
                    row["dni"],
                    format_timestamp(row["clock_in_time"]),
                    format_timestamp(row["clock_out_time"]) if row["clock_out_time"] else "-",
                    self._format_seconds(total_seconds or 0),
                    "Active" if row["is_active"] else "Closed",
                ),
            )

    def _create_employee(self) -> None:
        try:
            self.employee_service.create_employee(
                first_name=self._new_first_name.get(),
                last_name=self._new_last_name.get(),
                dni=self._new_dni.get(),
                password=self._new_password.get(),
                role="employee",
            )
        except ValueError as exc:
            self._create_status.configure(text=str(exc), text_color=th.DANGER_TEXT)
            return

        full_name = (
            f"{self._new_first_name.get().strip()} "
            f"{self._new_last_name.get().strip()}"
        ).strip()
        self._create_status.configure(
            text=f"{full_name} created and saved.",
            text_color=th.SUCCESS_TEXT,
        )
        for entry in (
            self._new_first_name,
            self._new_last_name,
            self._new_dni,
            self._new_password,
        ):
            entry.delete(0, "end")
        self._reload_all()

    def _toggle_selected_user(self) -> None:
        selected = self._users_tree.selection()
        if not selected:
            self._user_status.configure(
                text="Select a user first.",
                text_color=th.DANGER_TEXT,
            )
            return

        user_id = int(selected[0])
        new_state = self.employee_service.toggle_active(user_id)
        self._user_status.configure(
            text="User activated." if new_state else "User deactivated.",
            text_color=th.SUCCESS_TEXT,
        )
        self._reload_users()

    def _export_entries(self) -> None:
        try:
            path = self.export_service.export_time_entries_to_excel()
        except RuntimeError as exc:
            self._export_status.configure(text=str(exc), text_color=th.DANGER_TEXT)
            return

        self._export_status.configure(
            text=f"Export saved: {path}",
            text_color=th.SUCCESS_TEXT,
        )

    def _seconds_since(self, timestamp: str) -> int:
        try:
            started = datetime.fromisoformat(timestamp)
        except (TypeError, ValueError):
            return 0
        return max(int((datetime.now() - started).total_seconds()), 0)

    def _format_seconds(self, total_seconds: int) -> str:
        hours, remainder = divmod(max(int(total_seconds), 0), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
