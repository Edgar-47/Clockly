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
        attendance_session: AttendanceSession,
        time_clock_service: TimeClockService,
        on_clock_out: Callable[[], AttendanceSession],
        on_return_to_login: Callable[[], None],
    ) -> None:
        super().__init__(master, corner_radius=0, fg_color=th.BG_ROOT)
        self.employee = employee
        self.attendance_session = attendance_session
        self.time_clock_service = time_clock_service
        self.on_clock_out = on_clock_out
        self.on_return_to_login = on_return_to_login
        self._timer_after_id: str | None = None

        self._build()
        self._refresh()

    def _build(self) -> None:
        self._build_header()
        self._build_body()

    def _build_header(self) -> None:
        bar = ctk.CTkFrame(self, height=64, corner_radius=0, fg_color=th.BG_CARD)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        ctk.CTkLabel(
            bar,
            text="FICHAJE RESTAURANTE",
            font=th.bold(13),
            text_color=th.T_PRIMARY,
        ).pack(side="left", padx=22, pady=20)

        self._header_status = ctk.CTkLabel(
            bar,
            text="Clocked In",
            font=th.bold(12),
            text_color=th.SUCCESS_TEXT,
        )
        self._header_status.pack(side="right", padx=22, pady=20)

        th.separator(self)

    def _build_body(self) -> None:
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=th.PAGE_PAD, pady=th.PAGE_PAD)

        card = th.card(body, width=560, height=520)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        ctk.CTkLabel(
            card,
            text="Attendance session",
            font=th.bold(11),
            text_color=th.ACCENT_SOFT,
            fg_color=th.ACCENT_DIM,
            corner_radius=th.R_SM,
        ).pack(anchor="w", padx=28, pady=(28, 16), ipadx=10, ipady=4)

        ctk.CTkLabel(
            card,
            text=self.employee.full_name,
            font=th.bold(30),
            text_color=th.T_PRIMARY,
        ).pack(anchor="w", padx=28, pady=(0, 6))

        ctk.CTkLabel(
            card,
            text=f"DNI: {self.employee.dni}",
            font=th.f(13),
            text_color=th.T_SECONDARY,
        ).pack(anchor="w", padx=28, pady=(0, 26))

        self._status_label = ctk.CTkLabel(
            card,
            text="Clocked In",
            font=th.bold(18),
            text_color=th.SUCCESS_TEXT,
        )
        self._status_label.pack(anchor="w", padx=28, pady=(0, 12))

        self._started_label = ctk.CTkLabel(
            card,
            text="",
            font=th.f(14),
            text_color=th.T_SECONDARY,
        )
        self._started_label.pack(anchor="w", padx=28, pady=(0, 28))

        ctk.CTkLabel(
            card,
            text="Elapsed time",
            font=th.bold(11),
            text_color=th.T_MUTED,
        ).pack(anchor="w", padx=28)

        self._elapsed_label = ctk.CTkLabel(
            card,
            text="00:00:00",
            font=ctk.CTkFont(family="Segoe UI", size=58, weight="bold"),
            text_color=th.T_PRIMARY,
        )
        self._elapsed_label.pack(anchor="w", padx=28, pady=(4, 28))

        self._feedback_label = ctk.CTkLabel(
            card,
            text="",
            font=th.f(13),
            text_color=th.DANGER_TEXT,
            wraplength=500,
        )
        self._feedback_label.pack(fill="x", padx=28, pady=(0, 12))

        self._clock_out_button = ctk.CTkButton(
            card,
            text="Clock Out",
            height=50,
            font=th.bold(15),
            fg_color=th.DANGER,
            hover_color=th.DANGER_HOVER,
            corner_radius=th.R_MD,
            text_color="#FFFFFF",
            command=self._clock_out,
        )
        self._clock_out_button.pack(fill="x", padx=28)

        self._return_button = ctk.CTkButton(
            card,
            text="Return to login",
            height=44,
            font=th.f(13),
            **th.quiet_button_kwargs(),
            command=self.on_return_to_login,
        )

    def _refresh(self) -> None:
        self._started_label.configure(
            text=f"Started at: {format_timestamp(self.attendance_session.clock_in_time)}"
        )
        self._tick_elapsed()

    def _tick_elapsed(self) -> None:
        if not self.winfo_exists():
            return

        elapsed = self.attendance_session.elapsed_seconds()
        self._elapsed_label.configure(text=self._format_seconds(elapsed))

        if self.attendance_session.is_active:
            self._timer_after_id = self.after(1000, self._tick_elapsed)

    def _clock_out(self) -> None:
        self._feedback_label.configure(text="")
        try:
            self.attendance_session = self.on_clock_out()
        except ValueError as exc:
            self._feedback_label.configure(text=str(exc), text_color=th.DANGER_TEXT)
            return

        self._header_status.configure(text="Clocked Out", text_color=th.T_SECONDARY)
        self._status_label.configure(text="Clocked Out", text_color=th.T_SECONDARY)
        self._clock_out_button.configure(state="disabled", text="Session saved")

        if self._timer_after_id:
            self.after_cancel(self._timer_after_id)
            self._timer_after_id = None

        self._elapsed_label.configure(
            text=self._format_seconds(self.attendance_session.elapsed_seconds())
        )
        self._feedback_label.configure(
            text="Attendance saved. You can return to login.",
            text_color=th.SUCCESS_TEXT,
        )
        self._return_button.pack(fill="x", padx=28, pady=(12, 0))

    def destroy(self) -> None:
        if self._timer_after_id:
            self.after_cancel(self._timer_after_id)
            self._timer_after_id = None
        super().destroy()

    def _format_seconds(self, total_seconds: int) -> str:
        hours, remainder = divmod(max(int(total_seconds), 0), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
