"""
Main application controller.

Owns the single CTk root window and swaps full-screen frames between
the public clock kiosk, admin login, and admin panel.

Error handling philosophy
─────────────────────────
ValueError raised by the service layer is deliberately NOT caught here.
Instead it propagates to the calling view, which shows it inline without
any native messagebox. This keeps the UI cohesive and avoids jarring
OS-level popups.
"""

import customtkinter as ctk
from tkinter import PhotoImage

from app.config import APP_TITLE
from app.database import initialize_database
from app.models.employee import Employee
from app.services import (
    AttendanceReportService,
    AuthService,
    EmployeeService,
    ExportService,
    TimeClockService,
)
from app.ui import theme as th

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class TimeClockApplication(ctk.CTk):
    """Root window – manages navigation between views."""

    WIDTH = 1180
    HEIGHT = 740

    def __init__(self) -> None:
        super().__init__()

        initialize_database()

        self.auth_service        = AuthService()
        self.employee_service    = EmployeeService()
        self.time_clock_service  = TimeClockService()
        self.attendance_report_service = AttendanceReportService(
            self.time_clock_service.attendance_session_repository
        )
        self.export_service      = ExportService(
            attendance_session_repository=(
                self.time_clock_service.attendance_session_repository
            ),
            attendance_report_service=self.attendance_report_service,
        )

        self.current_employee: Employee | None = None
        self._active_frame: ctk.CTkFrame | None = None

        self.title(APP_TITLE)
        self._set_window_icon()
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(760, 560)
        self.resizable(True, True)
        self.configure(fg_color=th.BG_ROOT)

        self._center_window()
        self.show_login()

    # ── Navigation ────────────────────────────────────────────────────────────

    def show_login(self) -> None:
        self.current_employee = None
        from app.ui.login_view import LoginView
        self._swap(
            LoginView(
                self,
                on_login=self._handle_login,
            )
        )

    def show_clock(self) -> None:
        if not self.current_employee or self.current_employee.role != "employee":
            self.show_login()
            return

        # Fetch existing active session — may be None if employee is not yet clocked in.
        # Never auto-start a session here; let the employee choose via the UI.
        session = self.time_clock_service.get_active_session(self.current_employee.id)

        from app.ui.attendance_view import AttendanceView
        self._swap(
            AttendanceView(
                self,
                employee=self.current_employee,
                attendance_session=session,
                time_clock_service=self.time_clock_service,
                on_clock_in=self._handle_clock_in,
                on_clock_out=self._handle_clock_out,
                on_return_to_login=self.show_login,
            )
        )

    def show_admin(self) -> None:
        if not self.current_employee or self.current_employee.role != "admin":
            self.show_login()
            return
        from app.ui.admin_dashboard_view import AdminDashboardView
        self._swap(
            AdminDashboardView(
                self,
                employee=self.current_employee,
                employee_service=self.employee_service,
                export_service=self.export_service,
                attendance_report_service=self.attendance_report_service,
                time_clock_service=self.time_clock_service,
                on_logout=self.show_login,
            )
        )

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _handle_login(self, username: str, password: str) -> None:
        """
        Authenticate and navigate.  ValueError from the service propagates
        back to LoginView, which shows it inline.
        """
        employee = self.auth_service.login(username, password)
        self.current_employee = employee
        if employee.role == "admin":
            self.show_admin()
            return

        # Navigate to the attendance view; the employee will choose to clock in/out.
        # Any other employees who are currently clocked in are not affected.
        self.show_clock()

    def _handle_clock_in(self):
        if not self.current_employee:
            raise ValueError("No hay usuario autenticado.")
        return self.time_clock_service.start_session_for_employee(self.current_employee.id)

    def _handle_clock_out(self, exit_note=None, incident_type=None):
        if not self.current_employee:
            raise ValueError("No hay usuario autenticado.")
        return self.time_clock_service.clock_out_employee(
            self.current_employee.id,
            exit_note=exit_note,
            incident_type=incident_type,
        )

    def _handle_register(self, employee_id: int, password: str, entry_type: str) -> str:
        """
        Validate the selected employee password and record a time entry.
        ValueError from the service propagates back to ClockView for inline display.
        """
        employee = self.auth_service.verify_employee_password(employee_id, password)
        self.time_clock_service.register(
            employee_id=employee.id,
            entry_type=entry_type,
        )
        action = "entrada" if entry_type == TimeClockService.ENTRY else "salida"
        return f"{employee.full_name}: {action} registrada correctamente."

    # ── Internal ──────────────────────────────────────────────────────────────

    def _swap(self, new_frame: ctk.CTkFrame) -> None:
        if self._active_frame is not None:
            self._active_frame.destroy()
        self._active_frame = new_frame
        new_frame.pack(fill="both", expand=True)

    def _center_window(self) -> None:
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max((screen_w - self.WIDTH) // 2, 0)
        y = max((screen_h - self.HEIGHT) // 2, 0)
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

    def _set_window_icon(self) -> None:
        try:
            self._window_icon = PhotoImage(file=str(th.LOGO_MARK))
            self.iconphoto(True, self._window_icon)
        except Exception:
            self._window_icon = None
