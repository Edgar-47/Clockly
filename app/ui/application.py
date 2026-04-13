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

from app.config import APP_TITLE, KIOSK_MODE
from app.database import initialize_database
from app.models.business import Business
from app.models.employee import Employee
from app.services import (
    AttendanceReportService,
    AuthService,
    BusinessService,
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

        self.current_employee: Employee | None = None
        self.current_business: Business | None = None
        self._active_frame: ctk.CTkFrame | None = None
        self.auth_service = AuthService()
        self.business_service = BusinessService()
        self._configure_business_context(None)

        self.title(APP_TITLE)
        self._set_window_icon()
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        self.minsize(760, 560)
        self.resizable(True, True)
        self.configure(fg_color=th.BG_ROOT)

        self._center_window()

        if KIOSK_MODE:
            # Maximize window for tablet / kiosk display.
            try:
                self.state("zoomed")
            except Exception:
                pass
            self.show_kiosk()
        else:
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
        if self.current_business is None:
            default_business = self.business_service.choose_default_business(
                self.current_employee.id
            )
            if default_business is None:
                self.show_business_onboarding()
                return
            self._enter_business(default_business)
            return
        from app.ui.admin_control_center_view import AdminDashboardView
        business_count = len(
            self.business_service.list_businesses_for_user(self.current_employee.id)
        )
        self._swap(
            AdminDashboardView(
                self,
                employee=self.current_employee,
                business=self.current_business,
                business_count=business_count,
                employee_service=self.employee_service,
                export_service=self.export_service,
                attendance_report_service=self.attendance_report_service,
                time_clock_service=self.time_clock_service,
                business_service=self.business_service,
                on_logout=self._on_logout,
                on_change_business=self.show_business_selector,
                on_create_business=self.show_business_onboarding,
                on_business_updated=self._handle_business_updated,
            )
        )

    def show_business_onboarding(self) -> None:
        if not self.current_employee or self.current_employee.role != "admin":
            self.show_login()
            return

        has_existing_business = (
            self.business_service.count_for_user(self.current_employee.id) > 0
        )

        from app.ui.business_onboarding_view import BusinessOnboardingView
        self._swap(
            BusinessOnboardingView(
                self,
                owner_name=self.current_employee.full_name,
                on_create=self._create_business,
                on_continue=self._enter_business,
                on_cancel=self.show_admin if has_existing_business else None,
            )
        )

    def show_business_selector(self) -> None:
        if not self.current_employee:
            self.show_login()
            return

        businesses = self.business_service.list_businesses_for_user(
            self.current_employee.id
        )
        if not businesses:
            if self.current_employee.role == "admin":
                self.show_business_onboarding()
                return
            self.show_login()
            return

        from app.ui.business_selector_view import BusinessSelectorView
        self._swap(
            BusinessSelectorView(
                self,
                businesses=businesses,
                user_name=self.current_employee.full_name,
                on_select=self._select_business,
                on_create_new=self.show_business_onboarding,
                on_logout=self._on_logout,
            )
        )

    def show_kiosk(self) -> None:
        """
        Display the tablet kiosk interface.

        Called on startup when KIOSK_MODE=True, and also after an admin
        logs out while kiosk mode is active.  Admin users can still reach
        the admin panel via the "Acceso admin" button inside the kiosk,
        which routes to show_login() as usual.
        """
        self.current_employee = None
        from app.ui.kiosk_view import KioskView
        self._swap(
            KioskView(
                self,
                employee_service=self.employee_service,
                time_clock_service=self.time_clock_service,
                auth_service=self.auth_service,
                on_admin_login=self.show_login,
            )
        )

    def _on_logout(self) -> None:
        """
        Handle logout from the admin panel.

        Returns to kiosk mode when KIOSK_MODE is enabled; otherwise
        returns to the standard login screen.
        """
        if KIOSK_MODE:
            self.show_kiosk()
        else:
            self._configure_business_context(None)
            self.show_login()

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _handle_login(self, username: str, password: str) -> None:
        """
        Authenticate and navigate.  ValueError from the service propagates
        back to LoginView, which shows it inline.
        """
        employee = self.auth_service.login(username, password)
        self.current_employee = employee
        if employee.role == "admin":
            self._route_admin_after_login(employee)
            return

        self._route_employee_after_login(employee)

    def _route_admin_after_login(self, employee: Employee) -> None:
        businesses = self.business_service.list_businesses_for_user(employee.id)
        if not businesses:
            self.show_business_onboarding()
            return
        if len(businesses) == 1:
            self._enter_business(businesses[0])
            return
        self.show_business_selector()

    def _route_employee_after_login(self, employee: Employee) -> None:
        businesses = self.business_service.list_businesses_for_user(employee.id)
        if businesses:
            business = self.business_service.activate_business_for_user(
                user_id=employee.id,
                business_id=businesses[0].id,
            )
            self._configure_business_context(business)

        # Navigate to the attendance view; the employee will choose to clock in/out.
        # Any other employees who are currently clocked in are not affected.
        self.show_clock()

    def _create_business(
        self,
        business_name: str,
        business_type: str,
        login_code: str,
    ) -> Business:
        if not self.current_employee:
            raise ValueError("No hay usuario autenticado.")
        return self.business_service.create_business(
            owner_user_id=self.current_employee.id,
            business_name=business_name,
            business_type=business_type,
            login_code=login_code,
        )

    def _select_business(self, business_id: str) -> None:
        if not self.current_employee:
            self.show_login()
            return
        business = self.business_service.activate_business_for_user(
            user_id=self.current_employee.id,
            business_id=business_id,
        )
        self._enter_business(business)

    def _enter_business(self, business: Business) -> None:
        if not self.current_employee:
            self.show_login()
            return
        business = self.business_service.activate_business_for_user(
            user_id=self.current_employee.id,
            business_id=business.id,
        )
        self._configure_business_context(business)
        if self.current_employee.role == "admin":
            self.show_admin()
        else:
            self.show_clock()

    def _handle_business_updated(self, business: Business) -> None:
        self.current_business = business

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

    def _configure_business_context(self, business: Business | None) -> None:
        self.current_business = business
        business_id = business.id if business else None
        self.employee_service = EmployeeService(business_id=business_id)
        self.time_clock_service = TimeClockService(business_id=business_id)
        self.attendance_report_service = AttendanceReportService(
            self.time_clock_service.attendance_session_repository
        )
        self.export_service = ExportService(
            attendance_session_repository=(
                self.time_clock_service.attendance_session_repository
            ),
            attendance_report_service=self.attendance_report_service,
        )

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
