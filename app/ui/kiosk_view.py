"""
Kiosk View — tablet-optimized clock-in/out interface.

Flow:
  1. Full-screen grid of employee cards with real-time status.
  2. Tap a card → password modal (step 1).
  3. Correct password → show Clock In / Clock Out buttons (step 2).
  4. After action → full-screen confirmation overlay for 2.5 s.
  5. Overlay auto-dismisses → back to the grid.

Admin access via the top-right "Acceso admin" button, which routes to
the standard login screen so the admin can authenticate normally.

Double-click / accidental-tap protection:
  • _action_in_progress flag blocks new card taps while an action is
    executing or the confirmation overlay is displayed.
  • Modal buttons are disabled during the network/DB call.
"""

from __future__ import annotations

import datetime
from collections.abc import Callable

import customtkinter as ctk

from app.models.attendance_session import AttendanceSession
from app.models.attendance_status import AttendanceStatus
from app.models.employee import Employee
from app.services.auth_service import AuthService
from app.services.employee_service import EmployeeService
from app.services.time_clock_service import TimeClockService
from app.ui import theme as th


# ── Spanish locale strings ─────────────────────────────────────────────────────

_DAY_NAMES = [
    "lunes", "martes", "miércoles", "jueves",
    "viernes", "sábado", "domingo",
]
_MONTH_NAMES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


class KioskView(ctk.CTkFrame):
    """Full-screen kiosk mode for fast employee clock-in/out on a tablet."""

    # ── Timings ────────────────────────────────────────────────────────────────
    _CLOCK_REFRESH_MS  = 1_000   # clock label update interval
    _STATUS_REFRESH_MS = 30_000  # background employee-status refresh
    _CONFIRMATION_MS   = 2_500   # how long confirmation overlay is shown

    # ── Card geometry ──────────────────────────────────────────────────────────
    _CARD_W     = 150
    _CARD_H     = 192
    _AVATAR_SZ  = 70

    # ── Grid ──────────────────────────────────────────────────────────────────
    _MIN_COLS = 3
    _MAX_COLS = 7

    def __init__(
        self,
        master,
        *,
        employee_service: EmployeeService,
        time_clock_service: TimeClockService,
        auth_service: AuthService,
        on_admin_login: Callable[[], None],
    ) -> None:
        super().__init__(master, corner_radius=0, fg_color=th.BG_ROOT)

        self.employee_service   = employee_service
        self.time_clock_service = time_clock_service
        self.auth_service       = auth_service
        self.on_admin_login     = on_admin_login

        self._clock_after:   str | None = None
        self._refresh_after: str | None = None
        self._confirm_after: str | None = None
        self._confirm_overlay: ctk.CTkFrame | None = None

        # Protects against rapid taps / double submissions.
        self._action_in_progress = False

        # Cached data (refreshed on init and every _STATUS_REFRESH_MS).
        self._employees: list[Employee]            = []
        self._statuses:  dict[int, AttendanceStatus] = {}

        self._build()
        self._refresh_all()
        self._tick_clock()
        self._schedule_status_refresh()

    # ── Build ──────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self._build_header()
        th.separator(self)
        self._build_grid_area()

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, height=80, corner_radius=0, fg_color=th.BG_CARD)
        header.pack(fill="x")
        header.pack_propagate(False)

        # ── Left: logo + brand ──
        brand = ctk.CTkFrame(header, fg_color="transparent")
        brand.pack(side="left", padx=24, pady=16)

        ctk.CTkLabel(
            brand,
            text="",
            image=th.logo_mark(size=(38, 38)),
        ).pack(side="left", padx=(0, 12))

        brand_text = ctk.CTkFrame(brand, fg_color="transparent")
        brand_text.pack(side="left")

        ctk.CTkLabel(
            brand_text,
            text="CLOCKLY",
            font=th.bold(15),
            text_color=th.T_PRIMARY,
        ).pack(anchor="w")

        ctk.CTkLabel(
            brand_text,
            text="Registro de presencia",
            font=th.f(11),
            text_color=th.T_MUTED,
        ).pack(anchor="w")

        # ── Right: live clock + admin button ──
        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right", padx=24, pady=14)

        ctk.CTkButton(
            right,
            text="Acceso admin",
            width=130,
            height=34,
            font=th.f(12),
            **th.quiet_button_kwargs(),
            command=self.on_admin_login,
        ).pack(side="right", padx=(14, 0))

        clock_block = ctk.CTkFrame(right, fg_color="transparent")
        clock_block.pack(side="right")

        self._clock_time_lbl = ctk.CTkLabel(
            clock_block,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=th.T_PRIMARY,
            anchor="e",
        )
        self._clock_time_lbl.pack(anchor="e")

        self._clock_date_lbl = ctk.CTkLabel(
            clock_block,
            text="",
            font=th.f(11),
            text_color=th.T_MUTED,
            anchor="e",
        )
        self._clock_date_lbl.pack(anchor="e")

    def _build_grid_area(self) -> None:
        """Scrollable area that holds the employee card grid."""
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=20, pady=16)

        self._scroll = ctk.CTkScrollableFrame(
            wrapper,
            fg_color="transparent",
            scrollbar_button_color=th.BORDER,
            scrollbar_button_hover_color=th.BORDER_LT,
        )
        self._scroll.pack(fill="both", expand=True)
        self._grid_frame = self._scroll

    # ── Live clock ─────────────────────────────────────────────────────────────

    def _tick_clock(self) -> None:
        if not self.winfo_exists():
            return
        now = datetime.datetime.now()
        self._clock_time_lbl.configure(text=now.strftime("%H:%M:%S"))
        day_name   = _DAY_NAMES[now.weekday()]
        month_name = _MONTH_NAMES[now.month - 1]
        self._clock_date_lbl.configure(
            text=f"{day_name}, {now.day} de {month_name}"
        )
        self._clock_after = self.after(self._CLOCK_REFRESH_MS, self._tick_clock)

    # ── Employee-status refresh ────────────────────────────────────────────────

    def _refresh_all(self) -> None:
        """Fetch employees + current statuses, then rebuild the card grid."""
        try:
            self._employees = self.employee_service.list_clockable_employees()
            statuses = self.time_clock_service.get_attendance_statuses(self._employees)
            self._statuses = {s.employee.id: s for s in statuses}
        except Exception:
            pass
        self._rebuild_cards()

    def _schedule_status_refresh(self) -> None:
        if not self.winfo_exists():
            return
        self._refresh_after = self.after(
            self._STATUS_REFRESH_MS, self._on_scheduled_refresh
        )

    def _on_scheduled_refresh(self) -> None:
        if not self.winfo_exists():
            return
        self._refresh_all()
        self._schedule_status_refresh()

    # ── Card grid ──────────────────────────────────────────────────────────────

    def _rebuild_cards(self) -> None:
        """Destroy all existing cards and rebuild from the current employee list."""
        for widget in self._grid_frame.winfo_children():
            widget.destroy()

        if not self._employees:
            ctk.CTkLabel(
                self._grid_frame,
                text="No hay empleados activos.",
                font=th.f(16),
                text_color=th.T_MUTED,
            ).grid(row=0, column=0, padx=20, pady=60)
            return

        # Compute column count from current window width.
        try:
            win_w = self.winfo_width() or 1180
        except Exception:
            win_w = 1180
        card_slot = self._CARD_W + 20
        cols = max(self._MIN_COLS, min(self._MAX_COLS, (win_w - 48) // card_slot))

        for idx, emp in enumerate(self._employees):
            grid_row, grid_col = divmod(idx, cols)
            status = self._statuses.get(emp.id)
            card   = self._build_card(emp, status)
            card.grid(row=grid_row, column=grid_col, padx=10, pady=10, sticky="n")

        for c in range(cols):
            self._grid_frame.columnconfigure(c, weight=1)

    def _build_card(
        self, employee: Employee, status: AttendanceStatus | None
    ) -> ctk.CTkFrame:
        """Build a single employee tile."""
        is_in       = status.is_clocked_in if status else False
        border_clr  = th.SUCCESS if is_in else th.BORDER
        border_w    = 2 if is_in else 1
        # Clocked-in cards get a subtle tinted background for instant recognition
        card_bg     = "#131F14" if is_in else th.BG_CARD

        card = ctk.CTkFrame(
            self._grid_frame,
            width=self._CARD_W,
            height=self._CARD_H,
            corner_radius=th.R_LG,
            fg_color=card_bg,
            border_color=border_clr,
            border_width=border_w,
        )
        card.pack_propagate(False)
        card.grid_propagate(False)

        # ── Content (centered) ──
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.place(relx=0.5, rely=0.46, anchor="center")

        # Avatar circle
        av_bg = th.avatar_color(employee.id)
        avatar = ctk.CTkFrame(
            inner,
            width=self._AVATAR_SZ,
            height=self._AVATAR_SZ,
            corner_radius=self._AVATAR_SZ // 2,
            fg_color=av_bg,
        )
        avatar.pack()
        avatar.pack_propagate(False)
        ctk.CTkLabel(
            avatar,
            text=employee.initials,
            font=th.bold(22),
            text_color="#FFFFFF",
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Status dot — top-right corner of card
        dot = ctk.CTkFrame(
            card,
            width=14,
            height=14,
            corner_radius=7,
            fg_color=th.SUCCESS if is_in else th.T_DISABLED,
            border_color=card_bg,
            border_width=2,
        )
        dot.place(x=self._CARD_W - 22, y=16)
        dot.pack_propagate(False)

        # Name
        ctk.CTkLabel(
            inner,
            text=employee.first_name,
            font=th.bold(13),
            text_color=th.T_PRIMARY,
            wraplength=self._CARD_W - 14,
        ).pack(pady=(8, 1))

        ctk.CTkLabel(
            inner,
            text=employee.last_name,
            font=th.f(11),
            text_color=th.T_SECONDARY,
            wraplength=self._CARD_W - 14,
        ).pack()

        # Status line: for clocked-in employees show entry time + elapsed
        if is_in and status and status.active_session:
            try:
                ci = datetime.datetime.fromisoformat(
                    status.active_session.clock_in_time
                )
                elapsed_secs = status.active_session.elapsed_seconds()
                h, rem = divmod(int(elapsed_secs), 3600)
                m = rem // 60
                elapsed_str = f"{h}h {m:02d}m" if h else f"{m}m"
                status_txt   = f"desde {ci.strftime('%H:%M')}  ·  {elapsed_str}"
                status_color = th.SUCCESS_TEXT
            except Exception:
                status_txt   = "Fichado"
                status_color = th.SUCCESS_TEXT
        else:
            status_txt   = "Sin fichar"
            status_color = th.T_MUTED

        ctk.CTkLabel(
            inner,
            text=status_txt,
            font=th.f(10),
            text_color=status_color,
            wraplength=self._CARD_W - 14,
        ).pack(pady=(5, 0))

        # ── Click binding (all descendants, so labels also respond) ──
        def _on_click(event=None, emp=employee, stat=status):
            if not self._action_in_progress:
                self._on_card_click(emp, stat)

        def _bind_recursive(w) -> None:
            w.configure(cursor="hand2")
            w.bind("<Button-1>", _on_click, add="+")
            for child in w.winfo_children():
                _bind_recursive(child)

        _bind_recursive(card)

        return card

    # ── Auth + action modal ────────────────────────────────────────────────────

    def _on_card_click(
        self, employee: Employee, status: AttendanceStatus | None
    ) -> None:
        self._open_auth_modal(employee, status)

    def _open_auth_modal(
        self, employee: Employee, status: AttendanceStatus | None
    ) -> None:
        """
        Two-step modal:
          Step 1 — password field.
          Step 2 — large Clock In / Clock Out buttons.
        """
        is_in = status.is_clocked_in if status else False

        dlg = ctk.CTkToplevel(self)
        dlg.title(employee.full_name)
        dlg.geometry("440x400")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.configure(fg_color=th.BG_CARD)
        dlg.focus_force()

        # ── Modal header ──
        hdr = ctk.CTkFrame(dlg, fg_color="transparent")
        hdr.pack(fill="x", padx=24, pady=(24, 0))

        av_bg  = th.avatar_color(employee.id)
        avatar = ctk.CTkFrame(
            hdr, width=56, height=56, corner_radius=28, fg_color=av_bg
        )
        avatar.pack(side="left")
        avatar.pack_propagate(False)
        ctk.CTkLabel(
            avatar,
            text=employee.initials,
            font=th.bold(20),
            text_color="#FFFFFF",
        ).place(relx=0.5, rely=0.5, anchor="center")

        name_col = ctk.CTkFrame(hdr, fg_color="transparent")
        name_col.pack(side="left", padx=(14, 0))
        ctk.CTkLabel(
            name_col,
            text=employee.full_name,
            font=th.bold(17),
            text_color=th.T_PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            name_col,
            text="Fichado" if is_in else "Sin fichar",
            font=th.f(12),
            text_color=th.SUCCESS_TEXT if is_in else th.T_MUTED,
        ).pack(anchor="w")

        th.separator(dlg, padx=24, pady=(16, 14))

        # ── Step 1: password ──
        step1 = ctk.CTkFrame(dlg, fg_color="transparent")
        step1.pack(fill="x", padx=24)

        ctk.CTkLabel(
            step1,
            text="CONTRASEÑA",
            font=th.bold(9),
            text_color=th.T_MUTED,
            anchor="w",
        ).pack(fill="x")

        pw_entry = ctk.CTkEntry(
            step1,
            height=44,
            font=th.f(16),
            show="•",
            placeholder_text="••••••",
            **th.entry_kwargs(),
        )
        pw_entry.pack(fill="x", pady=(4, 8))

        error_lbl = ctk.CTkLabel(
            step1,
            text="",
            font=th.f(11),
            text_color=th.DANGER_TEXT,
            fg_color="transparent",
            wraplength=380,
        )
        error_lbl.pack(fill="x", pady=(0, 8))

        # Mutable ref so the inner closure can re-enable the button on failure.
        _verify_btn: list[ctk.CTkButton] = []

        # ── Step 2: action buttons (hidden until auth succeeds) ──
        step2 = ctk.CTkFrame(dlg, fg_color="transparent")

        action_error_lbl = ctk.CTkLabel(
            step2,
            text="",
            font=th.f(11),
            text_color=th.DANGER_TEXT,
            fg_color="transparent",
            wraplength=380,
        )

        def _execute_action(emp: Employee, entry_type: str, btn_in, btn_out) -> None:
            """Perform clock-in or clock-out; show confirmation on success."""
            if self._action_in_progress:
                return
            self._action_in_progress = True

            # Disable both action buttons immediately.
            for b in (btn_in, btn_out):
                try:
                    b.configure(state="disabled")
                except Exception:
                    pass

            action_error_lbl.configure(text="")

            try:
                if entry_type == TimeClockService.ENTRY:
                    session      = self.time_clock_service.start_session_for_employee(emp.id)
                    action_label = "Entrada registrada"
                else:
                    session      = self.time_clock_service.clock_out_employee(emp.id)
                    action_label = "Salida registrada"
            except ValueError as exc:
                self._action_in_progress = False
                for b in (btn_in, btn_out):
                    try:
                        b.configure(state="normal")
                    except Exception:
                        pass
                action_error_lbl.configure(text=f"✕  {exc}")
                return

            dlg.destroy()
            self._refresh_all()
            self._show_confirmation(emp, action_label, session)

        def _show_step2(authenticated_emp: Employee) -> None:
            """Transition from password step to action-selection step."""
            step1.pack_forget()
            step2.pack(fill="x", padx=24)

            ctk.CTkLabel(
                step2,
                text="¿Qué deseas registrar?",
                font=th.bold(14),
                text_color=th.T_PRIMARY,
                anchor="w",
            ).pack(fill="x", pady=(0, 14))

            btns_row = ctk.CTkFrame(step2, fg_color="transparent")
            btns_row.pack(fill="x")
            btns_row.columnconfigure(0, weight=1)
            btns_row.columnconfigure(1, weight=1)

            # Clock-In button — highlighted if currently NOT clocked in.
            btn_in = ctk.CTkButton(
                btns_row,
                text="↓  Fichar entrada",
                height=56,
                font=th.bold(13),
                fg_color=th.SUCCESS       if not is_in else th.BG_RAISED,
                hover_color=th.SUCCESS_HOVER if not is_in else th.BG_HOVER,
                text_color="#071B10"      if not is_in else th.T_SECONDARY,
                border_color=th.SUCCESS   if is_in else "transparent",
                border_width=1            if is_in else 0,
                corner_radius=th.R_MD,
            )
            btn_in.grid(row=0, column=0, padx=(0, 6), sticky="ew")

            # Clock-Out button — highlighted if currently clocked in.
            btn_out = ctk.CTkButton(
                btns_row,
                text="↑  Fichar salida",
                height=56,
                font=th.bold(13),
                fg_color=th.DANGER        if is_in else th.BG_RAISED,
                hover_color=th.DANGER_HOVER if is_in else th.BG_HOVER,
                text_color="#FFFFFF"      if is_in else th.T_SECONDARY,
                border_color=th.DANGER    if not is_in else "transparent",
                border_width=1            if not is_in else 0,
                corner_radius=th.R_MD,
            )
            btn_out.grid(row=0, column=1, padx=(6, 0), sticky="ew")

            # Wire commands after both buttons exist.
            btn_in.configure(
                command=lambda: _execute_action(
                    authenticated_emp, TimeClockService.ENTRY, btn_in, btn_out
                )
            )
            btn_out.configure(
                command=lambda: _execute_action(
                    authenticated_emp, TimeClockService.EXIT, btn_in, btn_out
                )
            )

            action_error_lbl.pack(fill="x", pady=(10, 0))

        def _verify() -> None:
            pw = pw_entry.get().strip()
            if not pw:
                error_lbl.configure(text="Introduce tu contraseña.")
                return
            if _verify_btn:
                _verify_btn[0].configure(state="disabled", text="Verificando...")
            error_lbl.configure(text="")
            try:
                auth_emp = self.auth_service.verify_employee_password(
                    employee.id, pw_entry.get()
                )
            except ValueError as exc:
                error_lbl.configure(text=f"✕  {exc}")
                if _verify_btn:
                    _verify_btn[0].configure(state="normal", text="Continuar  →")
                return
            _show_step2(auth_emp)

        continue_btn = ctk.CTkButton(
            step1,
            text="Continuar  →",
            height=44,
            font=th.bold(13),
            fg_color=th.ACCENT,
            hover_color=th.ACCENT_HOVER,
            text_color="#062421",
            corner_radius=th.R_MD,
            command=_verify,
        )
        continue_btn.pack(fill="x")
        _verify_btn.append(continue_btn)

        # ── Cancel (always visible) ──
        ctk.CTkButton(
            dlg,
            text="Cancelar",
            height=36,
            font=th.f(12),
            **th.quiet_button_kwargs(),
            command=dlg.destroy,
        ).pack(fill="x", padx=24, pady=(14, 18))

        pw_entry.focus()
        pw_entry.bind("<Return>", lambda _: _verify())
        dlg.bind("<Escape>", lambda _: dlg.destroy())

    # ── Full-screen confirmation overlay ───────────────────────────────────────

    def _show_confirmation(
        self,
        employee: Employee,
        action_label: str,
        session: AttendanceSession,
    ) -> None:
        """
        Overlay a full-screen success panel over the kiosk grid.
        Automatically dismisses after _CONFIRMATION_MS, or on tap.
        """
        # Clean up any lingering overlay.
        if self._confirm_overlay and self._confirm_overlay.winfo_exists():
            self._confirm_overlay.destroy()
        if self._confirm_after:
            self.after_cancel(self._confirm_after)

        is_clock_in = session.is_active
        # Use visibly distinct colours — darker than ROOT but clearly tinted
        bg_color   = "#0D2E13" if is_clock_in else "#2A0C12"
        accent_clr = th.SUCCESS if is_clock_in else th.DANGER
        icon_text  = "✔" if is_clock_in else "✔"

        overlay = ctk.CTkFrame(self, corner_radius=0, fg_color=bg_color)
        overlay.place(x=0, y=0, relwidth=1, relheight=1)
        self._confirm_overlay = overlay

        # Force the overlay above all siblings.
        overlay.lift()

        # ── Centered card ──
        center = ctk.CTkFrame(
            overlay,
            fg_color=th.BG_CARD,
            corner_radius=th.R_LG,
            border_width=2,
            border_color=accent_clr,
        )
        center.place(relx=0.5, rely=0.5, anchor="center")

        inner = ctk.CTkFrame(center, fg_color="transparent")
        inner.pack(padx=48, pady=40)

        # Large avatar
        av_bg = th.avatar_color(employee.id)
        av = ctk.CTkFrame(inner, width=80, height=80, corner_radius=40, fg_color=av_bg)
        av.pack()
        av.pack_propagate(False)
        ctk.CTkLabel(
            av,
            text=employee.initials,
            font=th.bold(28),
            text_color="#FFFFFF",
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Check icon
        ctk.CTkLabel(
            inner,
            text=icon_text,
            font=ctk.CTkFont(family="Segoe UI", size=52),
            text_color=accent_clr,
        ).pack(pady=(14, 2))

        # Action label
        ctk.CTkLabel(
            inner,
            text=action_label,
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=th.T_PRIMARY,
        ).pack()

        # Employee name
        ctk.CTkLabel(
            inner,
            text=employee.full_name,
            font=th.bold(16),
            text_color=th.T_SECONDARY,
        ).pack(pady=(6, 4))

        # Time detail line
        try:
            if is_clock_in:
                dt     = datetime.datetime.fromisoformat(session.clock_in_time)
                detail = f"Entrada registrada a las {dt.strftime('%H:%M')}"
            else:
                secs = session.total_seconds or 0
                h, rem = divmod(max(int(secs), 0), 3600)
                m      = rem // 60
                detail = f"Turno completado · {h}h {m:02d}m trabajados"
        except Exception:
            detail = ""

        if detail:
            ctk.CTkLabel(
                inner,
                text=detail,
                font=th.f(13),
                text_color=accent_clr,
            ).pack(pady=(2, 0))

        # Tap-to-dismiss hint
        ctk.CTkLabel(
            inner,
            text="Toca en cualquier lugar para cerrar",
            font=th.f(10),
            text_color=th.T_DISABLED,
        ).pack(pady=(16, 0))

        def _dismiss(event=None) -> None:
            self._action_in_progress = False
            if self._confirm_after:
                try:
                    self.after_cancel(self._confirm_after)
                except Exception:
                    pass
                self._confirm_after = None
            if overlay.winfo_exists():
                overlay.destroy()

        # Allow tapping anywhere on the overlay to dismiss early
        overlay.bind("<Button-1>", _dismiss)
        for w in overlay.winfo_children():
            try:
                w.bind("<Button-1>", _dismiss)
            except Exception:
                pass
        center.bind("<Button-1>", _dismiss)
        for w in center.winfo_children():
            try:
                w.bind("<Button-1>", _dismiss)
            except Exception:
                pass

        self._confirm_after = self.after(self._CONFIRMATION_MS, _dismiss)

    # ── Cleanup ────────────────────────────────────────────────────────────────

    def destroy(self) -> None:
        for after_id in (self._clock_after, self._refresh_after, self._confirm_after):
            if after_id:
                try:
                    self.after_cancel(after_id)
                except Exception:
                    pass
        super().destroy()
