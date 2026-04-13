"""
Admin panel view — three-tab back-office interface.

Tabs
────
  1. Fichajes  – full attendance table with date-range filter
  2. Empleados – employee roster + add-form + toggle active/inactive
  3. Exportar  – export to Excel with optional date filter

Design notes
────────────
  • Uses theme.py tokens throughout for visual consistency.
  • No native messagebox calls: all feedback is shown inline via status labels.
  • ttk.Treeview is styled to blend with the dark palette.
"""

from collections.abc import Callable
from tkinter import ttk

import customtkinter as ctk

from app.models.employee import Employee
from app.services.employee_service import EmployeeService
from app.services.export_service import ExportService
from app.services.time_clock_service import TimeClockService
from app.ui import theme as th
from app.utils.helpers import format_timestamp, label_for_entry_type, split_timestamp


# ── Treeview dark-mode styling (applied once on first AdminView instantiation)
def _style_treeview() -> None:
    s = ttk.Style()
    s.theme_use("default")
    s.configure(
        "Fichaje.Treeview",
        background=th.BG_RAISED,
        foreground=th.T_PRIMARY,
        fieldbackground=th.BG_RAISED,
        rowheight=34,
        font=("Segoe UI", 11),
        borderwidth=0,
    )
    s.configure(
        "Fichaje.Treeview.Heading",
        background=th.BG_CARD,
        foreground=th.T_SECONDARY,
        font=("Segoe UI", 10, "bold"),
        relief="flat",
        borderwidth=0,
        padding=(8, 8),
    )
    s.map(
        "Fichaje.Treeview",
        background=[("selected", th.ACCENT_DIM)],
        foreground=[("selected", th.ACCENT)],
    )
    s.configure(
        "Vertical.TScrollbar",
        background=th.BG_RAISED,
        troughcolor=th.BG_CARD,
        arrowcolor=th.T_MUTED,
        relief="flat",
    )


class _MetricCard(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        label: str,
        value: str,
        accent: str,
        helper: str,
    ) -> None:
        super().__init__(
            master,
            height=92,
            fg_color=th.BG_CARD,
            corner_radius=th.R_LG,
            border_width=1,
            border_color=th.BORDER,
        )
        self.grid_propagate(False)
        self.columnconfigure(1, weight=1)

        ctk.CTkFrame(
            self,
            width=4,
            height=54,
            fg_color=accent,
            corner_radius=2,
        ).grid(row=0, column=0, rowspan=2, padx=(16, 12), pady=18, sticky="ns")

        self._value = ctk.CTkLabel(
            self,
            text=value,
            font=th.bold(26),
            text_color=th.T_PRIMARY,
        )
        self._value.grid(row=0, column=1, sticky="sw", padx=(0, 16), pady=(15, 0))

        ctk.CTkLabel(
            self,
            text=label,
            font=th.bold(11),
            text_color=th.T_SECONDARY,
        ).grid(row=1, column=1, sticky="nw", padx=(0, 16), pady=(0, 0))

        ctk.CTkLabel(
            self,
            text=helper,
            font=th.f(10),
            text_color=th.T_MUTED,
        ).grid(row=2, column=1, sticky="nw", padx=(0, 16), pady=(0, 12))

    def set(self, value: int | str) -> None:
        self._value.configure(text=str(value))


class AdminView(ctk.CTkFrame):
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
        self._employee_refresh_after_id: str | None = None

        _style_treeview()
        self._build()
        self._admin_compact_layout = False
        self.bind("<Configure>", self._on_resize)
        self._reload_fichajes()
        self._reload_employees()
        self._schedule_employee_refresh()

    # ═════════════════════════════════════════════════════════════════════════
    # Shell
    # ═════════════════════════════════════════════════════════════════════════

    def _build(self) -> None:
        self._build_header()
        th.separator(self)
        self._build_tabs()

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self) -> None:
        bar = ctk.CTkFrame(self, height=72, corner_radius=0, fg_color=th.BG_CARD)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # Left: icon + title
        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.pack(side="left", padx=20, pady=0)

        # Coloured square icon
        icon = ctk.CTkFrame(
            left,
            width=36, height=36,
            corner_radius=th.R_MD,
            fg_color=th.ACCENT,
        )
        icon.pack(side="left", padx=(0, 12), pady=18)
        icon.pack_propagate(False)
        ctk.CTkLabel(
            icon, text="A", font=th.bold(14), text_color="#062421"
        ).place(relx=0.5, rely=0.5, anchor="center")

        title_stack = ctk.CTkFrame(left, fg_color="transparent")
        title_stack.pack(side="left", pady=14)
        ctk.CTkLabel(
            title_stack,
            text="Panel de Administración",
            font=th.bold(18),
            text_color=th.T_PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_stack,
            text="Fichajes, empleados y exportación operativa",
            font=th.f(11),
            text_color=th.T_MUTED,
        ).pack(anchor="w", pady=(2, 0))

        # Right: role badge + user name + logout
        right = ctk.CTkFrame(bar, fg_color="transparent")
        right.pack(side="right", padx=20)

        ctk.CTkButton(
            right,
            text="Cerrar sesión",
            width=140,
            height=34,
            font=th.f(12),
            **th.quiet_button_kwargs(),
            command=self.on_logout,
        ).pack(side="right", padx=(10, 0), pady=14)

        # User pill
        user_pill = ctk.CTkFrame(
            right,
            fg_color=th.BG_RAISED,
            corner_radius=th.R_XL,
            border_width=1,
            border_color=th.BORDER_LT,
        )
        user_pill.pack(side="right", pady=14)
        ctk.CTkLabel(
            user_pill,
            text=self.employee.name,
            font=th.f(12),
            text_color=th.T_PRIMARY,
        ).pack(side="left", padx=(14, 6), pady=6)
        # Role chip inside the pill
        role_chip = ctk.CTkFrame(
            user_pill,
            fg_color=th.ACCENT_DIM,
            corner_radius=th.R_XL,
        )
        role_chip.pack(side="left", padx=(0, 10), pady=5)
        ctk.CTkLabel(
            role_chip,
            text="ADMIN",
            font=th.bold(9),
            text_color=th.ACCENT,
        ).pack(padx=8, pady=3)

    # ── Tabs ──────────────────────────────────────────────────────────────────

    def _build_tabs(self) -> None:
        tabs = ctk.CTkTabview(
            self,
            fg_color=th.BG_ROOT,
            segmented_button_fg_color=th.BG_CARD,
            segmented_button_selected_color=th.ACCENT_DIM,
            segmented_button_selected_hover_color=th.BG_HOVER,
            segmented_button_unselected_color=th.BG_CARD,
            segmented_button_unselected_hover_color=th.BG_RAISED,
            text_color=th.T_SECONDARY,
            text_color_disabled=th.T_MUTED,
        )
        tabs.pack(fill="both", expand=True, padx=th.PAGE_PAD, pady=(14, 18))

        tabs.add("  Fichajes  ")
        tabs.add("  Empleados  ")
        tabs.add("  Exportar  ")

        self._build_tab_fichajes(tabs.tab("  Fichajes  "))
        self._build_tab_empleados(tabs.tab("  Empleados  "))
        self._build_tab_exportar(tabs.tab("  Exportar  "))

    def _on_resize(self, event) -> None:
        if event.widget is not self or not hasattr(self, "_emp_right_panel"):
            return

        compact = event.width < 980
        if compact == self._admin_compact_layout:
            return
        self._admin_compact_layout = compact

        if compact:
            self._emp_right_panel.configure(width=max(event.width - 96, 320))
            self._emp_left_panel.grid_configure(
                row=1,
                column=0,
                columnspan=2,
                padx=0,
                pady=(0, 10),
            )
            self._emp_right_panel.grid_configure(
                row=2,
                column=0,
                columnspan=2,
                sticky="ew",
                pady=(0, 6),
            )
        else:
            self._emp_right_panel.configure(width=320)
            self._emp_left_panel.grid_configure(
                row=1,
                column=0,
                columnspan=1,
                padx=(0, 10),
                pady=(0, 6),
            )
            self._emp_right_panel.grid_configure(
                row=1,
                column=1,
                columnspan=1,
                sticky="nsew",
                pady=(0, 6),
            )

    # ═════════════════════════════════════════════════════════════════════════
    # Tab 1 – Fichajes
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tab_fichajes(self, tab: ctk.CTkFrame) -> None:
        summary = ctk.CTkFrame(tab, fg_color="transparent")
        summary.pack(fill="x", pady=(6, 12))
        summary.columnconfigure((0, 1, 2), weight=1, uniform="fichaje_metrics")

        self._fich_total_card = _MetricCard(
            summary,
            label="Registros",
            value="0",
            accent=th.ACCENT,
            helper="Según el filtro actual",
        )
        self._fich_total_card.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self._fich_entry_card = _MetricCard(
            summary,
            label="Entradas",
            value="0",
            accent=th.SUCCESS,
            helper="Inicios de turno",
        )
        self._fich_entry_card.grid(row=0, column=1, sticky="ew", padx=8)

        self._fich_exit_card = _MetricCard(
            summary,
            label="Salidas",
            value="0",
            accent=th.DANGER,
            helper="Finales de turno",
        )
        self._fich_exit_card.grid(row=0, column=2, sticky="ew", padx=(8, 0))

        # ── Filter bar ────────────────────────────────────────────────────────
        bar = ctk.CTkFrame(
            tab,
            fg_color=th.BG_CARD,
            corner_radius=th.R_MD,
            border_width=1,
            border_color=th.BORDER,
        )
        bar.pack(fill="x", pady=(0, 10))
        bar.columnconfigure(6, weight=1)

        ctk.CTkLabel(
            bar, text="Periodo:", font=th.bold(11), text_color=th.T_SECONDARY
        ).grid(row=0, column=0, padx=(16, 8), pady=12)

        self._fich_from = ctk.CTkEntry(
            bar,
            placeholder_text="Desde (AAAA-MM-DD)",
            width=160,
            height=36,
            font=th.f(12),
            **th.entry_kwargs(),
        )
        self._fich_from.grid(row=0, column=1, padx=4, pady=12)

        ctk.CTkLabel(
            bar, text="→", font=th.f(13), text_color=th.T_MUTED
        ).grid(row=0, column=2, padx=4)

        self._fich_to = ctk.CTkEntry(
            bar,
            placeholder_text="Hasta (AAAA-MM-DD)",
            width=160,
            height=36,
            font=th.f(12),
            **th.entry_kwargs(),
        )
        self._fich_to.grid(row=0, column=3, padx=4, pady=12)

        ctk.CTkButton(
            bar,
            text="Filtrar",
            width=86,
            height=36,
            font=th.bold(12),
            **th.primary_button_kwargs(),
            command=self._reload_fichajes,
        ).grid(row=0, column=4, padx=(14, 4), pady=12)

        ctk.CTkButton(
            bar,
            text="Limpiar",
            width=86,
            height=36,
            font=th.f(12),
            **th.quiet_button_kwargs(),
            command=self._clear_fich_filter,
        ).grid(row=0, column=5, padx=(0, 16), pady=12)

        self._fich_empty_hint = ctk.CTkLabel(
            bar,
            text="",
            font=th.f(12),
            text_color=th.WARNING_TEXT,
            anchor="e",
        )
        self._fich_empty_hint.grid(row=0, column=6, sticky="e", padx=(0, 16))

        # ── Table ─────────────────────────────────────────────────────────────
        table_card = ctk.CTkFrame(
            tab,
            fg_color=th.BG_CARD,
            corner_radius=th.R_MD,
            border_width=1,
            border_color=th.BORDER,
        )
        table_card.pack(fill="both", expand=True, pady=(0, 4))

        cols = ("id", "empleado", "tipo", "fecha", "hora", "observaciones")
        self._fich_tree = ttk.Treeview(
            table_card,
            columns=cols,
            show="headings",
            style="Fichaje.Treeview",
            selectmode="browse",
        )

        col_cfg = {
            "id":            ("ID",           52,  "center"),
            "empleado":      ("Empleado",     200,  "w"),
            "tipo":          ("Tipo",          90,  "center"),
            "fecha":         ("Fecha",        110,  "center"),
            "hora":          ("Hora",          82,  "center"),
            "observaciones": ("Observaciones", 260, "w"),
        }
        for col, (heading, width, anchor) in col_cfg.items():
            self._fich_tree.heading(col, text=heading)
            self._fich_tree.column(col, width=width, anchor=anchor, minwidth=40)

        self._fich_tree.tag_configure("odd",  background=th.BG_RAISED)
        self._fich_tree.tag_configure("even", background=th.BG_CARD)
        self._fich_tree.tag_configure(
            "entrada", foreground=th.SUCCESS_TEXT
        )
        self._fich_tree.tag_configure(
            "salida", foreground=th.DANGER_TEXT
        )

        vsb = ttk.Scrollbar(
            table_card, orient="vertical", command=self._fich_tree.yview
        )
        self._fich_tree.configure(yscrollcommand=vsb.set)
        self._fich_tree.pack(
            side="left", fill="both", expand=True, padx=(6, 0), pady=6
        )
        vsb.pack(side="right", fill="y", pady=6, padx=(0, 4))

    # ═════════════════════════════════════════════════════════════════════════
    # Tab 2 – Empleados
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tab_empleados(self, tab: ctk.CTkFrame) -> None:
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=0)
        tab.rowconfigure(1, weight=1)

        summary = ctk.CTkFrame(tab, fg_color="transparent")
        summary.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(6, 12))
        summary.columnconfigure((0, 1, 2, 3), weight=1, uniform="employee_metrics")

        self._emp_total_card = _MetricCard(
            summary,
            label="Empleados",
            value="0",
            accent=th.ACCENT,
            helper="Plantilla registrada",
        )
        self._emp_total_card.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self._emp_active_card = _MetricCard(
            summary,
            label="Activos",
            value="0",
            accent=th.SUCCESS,
            helper="Disponibles para fichar",
        )
        self._emp_active_card.grid(row=0, column=1, sticky="ew", padx=8)

        self._emp_clocked_in_card = _MetricCard(
            summary,
            label="Dentro ahora",
            value="0",
            accent=th.ACCENT,
            helper="Turnos abiertos",
        )
        self._emp_clocked_in_card.grid(row=0, column=2, sticky="ew", padx=8)

        self._emp_admin_card = _MetricCard(
            summary,
            label="Admins",
            value="0",
            accent=th.WARNING,
            helper="Acceso al panel",
        )
        self._emp_admin_card.grid(row=0, column=3, sticky="ew", padx=(8, 0))

        # ── Left: roster ──────────────────────────────────────────────────────
        left = ctk.CTkFrame(
            tab,
            fg_color=th.BG_CARD,
            corner_radius=th.R_MD,
            border_width=1,
            border_color=th.BORDER,
        )
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(0, 6))
        self._emp_left_panel = left

        # Section header
        roster_hdr = ctk.CTkFrame(
            left, fg_color="transparent", height=46
        )
        roster_hdr.pack(fill="x", padx=14, pady=(10, 0))
        roster_hdr.pack_propagate(False)

        ctk.CTkLabel(
            roster_hdr,
            text="Empleados",
            font=th.bold(14),
            text_color=th.T_PRIMARY,
        ).pack(side="left", pady=12)

        self._employee_filter = ctk.CTkSegmentedButton(
            roster_hdr,
            values=["Todos", "Activos", "Inactivos"],
            width=240,
            height=30,
            fg_color=th.BG_RAISED,
            selected_color=th.ACCENT_DIM,
            selected_hover_color=th.BG_HOVER,
            unselected_color=th.BG_RAISED,
            unselected_hover_color=th.BG_HOVER,
            text_color=th.T_PRIMARY,
            font=th.f(11),
            command=lambda _: self._reload_employees(),
        )
        self._employee_filter.set("Todos")
        self._employee_filter.pack(side="right", pady=8)

        th.separator(left, padx=10, pady=(4, 0))

        # Treeview
        tree_wrap = ctk.CTkFrame(left, fg_color="transparent")
        tree_wrap.pack(fill="both", expand=True, padx=8, pady=(4, 0))

        emp_cols = (
            "nombre",
            "apellido",
            "usuario",
            "rol",
            "estado",
            "fichaje",
            "ultimo",
        )
        self._emp_tree = ttk.Treeview(
            tree_wrap,
            columns=emp_cols,
            show="headings",
            style="Fichaje.Treeview",
            selectmode="browse",
        )

        emp_col_cfg = {
            "nombre":   ("Nombre",   140, "w"),
            "apellido": ("Apellido", 150, "w"),
            "usuario":  ("Usuario",  140, "center"),
            "rol":      ("Rol",        82, "center"),
            "estado":   ("Estado",     82, "center"),
            "fichaje":  ("Fichaje",   118, "center"),
            "ultimo":   ("Ultimo",    132, "center"),
        }
        for col, (heading, width, anchor) in emp_col_cfg.items():
            self._emp_tree.heading(col, text=heading)
            self._emp_tree.column(col, width=width, anchor=anchor)

        self._emp_tree.tag_configure("odd",      background=th.BG_RAISED)
        self._emp_tree.tag_configure("even",     background=th.BG_CARD)
        self._emp_tree.tag_configure("inactive", foreground=th.T_MUTED)
        self._emp_tree.tag_configure("clocked_in", foreground=th.SUCCESS_TEXT)
        self._emp_tree.tag_configure("clocked_out", foreground=th.T_SECONDARY)

        emp_vsb = ttk.Scrollbar(
            tree_wrap, orient="vertical", command=self._emp_tree.yview
        )
        self._emp_tree.configure(yscrollcommand=emp_vsb.set)
        self._emp_tree.pack(side="left", fill="both", expand=True)
        emp_vsb.pack(side="right", fill="y")

        # Toggle button + inline status
        action_row = ctk.CTkFrame(left, fg_color="transparent")
        action_row.pack(fill="x", padx=12, pady=(8, 12))

        ctk.CTkButton(
            action_row,
            text="Cambiar estado",
            height=36,
            font=th.f(12),
            fg_color=th.BG_RAISED,
            hover_color=th.BG_HOVER,
            border_width=1,
            border_color=th.BORDER_LT,
            text_color=th.T_SECONDARY,
            corner_radius=th.R_SM,
            command=self._toggle_selected_employee,
        ).pack(side="left")

        self._emp_status = ctk.CTkLabel(
            action_row,
            text="",
            font=th.f(12),
            text_color=th.SUCCESS_TEXT,
        )
        self._emp_status.pack(side="left", padx=12)

        # ── Right: add employee form ──────────────────────────────────────────
        right = ctk.CTkFrame(
            tab,
            width=320,
            fg_color=th.BG_CARD,
            corner_radius=th.R_MD,
            border_width=1,
            border_color=th.BORDER,
        )
        right.grid(row=1, column=1, sticky="nsew", pady=(0, 6))
        self._emp_right_panel = right
        right.pack_propagate(False)
        right.grid_propagate(False)

        # Form header
        form_hdr = ctk.CTkFrame(right, fg_color=th.BG_RAISED, corner_radius=0,
                                height=52)
        form_hdr.pack(fill="x")
        form_hdr.pack_propagate(False)
        ctk.CTkLabel(
            form_hdr,
            text="Nuevo empleado",
            font=th.bold(13),
            text_color=th.T_PRIMARY,
        ).pack(side="left", padx=16, pady=16)

        th.separator(right)

        # Fields
        def _field(lbl: str, **kw) -> ctk.CTkEntry:
            ctk.CTkLabel(
                right, text=lbl, font=th.bold(9),
                text_color=th.T_SECONDARY, anchor="w"
            ).pack(padx=16, fill="x", pady=(12, 0))
            e = ctk.CTkEntry(
                right,
                height=40,
                font=th.f(13),
                **th.entry_kwargs(),
                **kw,
            )
            e.pack(padx=16, fill="x", pady=(4, 0))
            return e

        self._new_first_name = _field("NOMBRE", placeholder_text="Edgar")
        self._new_last_name = _field("APELLIDO", placeholder_text="Pedret")
        self._new_password = _field(
            "CONTRASEÑA",
            placeholder_text="mínimo 6 caracteres",
            show="●",
        )

        ctk.CTkLabel(
            right, text="ROL", font=th.bold(9),
            text_color=th.T_SECONDARY, anchor="w"
        ).pack(padx=16, fill="x", pady=(12, 0))

        self._new_role = ctk.CTkSegmentedButton(
            right,
            values=["employee", "admin"],
            fg_color=th.BG_RAISED,
            selected_color=th.ACCENT_DIM,
            selected_hover_color=th.BG_HOVER,
            unselected_color=th.BG_RAISED,
            unselected_hover_color=th.BG_HOVER,
            text_color=th.T_PRIMARY,
            font=th.f(12),
        )
        self._new_role.set("employee")
        self._new_role.pack(padx=16, fill="x", pady=(4, 0))

        self._add_status = ctk.CTkLabel(
            right,
            text="",
            font=th.f(11),
            text_color=th.SUCCESS_TEXT,
            wraplength=250,
        )
        self._add_status.pack(padx=16, pady=(10, 4))

        ctk.CTkButton(
            right,
            text="Crear empleado",
            height=44,
            font=th.bold(13),
            fg_color=th.SUCCESS,
            hover_color=th.SUCCESS_HOVER,
            corner_radius=th.R_SM,
            text_color="#071B10",
            command=self._create_employee,
        ).pack(padx=16, fill="x", pady=(0, 16))

    # ═════════════════════════════════════════════════════════════════════════
    # Tab 3 – Exportar
    # ═════════════════════════════════════════════════════════════════════════

    def _build_tab_exportar(self, tab: ctk.CTkFrame) -> None:
        # Centred export card
        card = ctk.CTkFrame(
            tab,
            width=620,
            height=372,
            fg_color=th.BG_CARD,
            corner_radius=th.R_LG,
            border_width=1,
            border_color=th.BORDER,
        )
        card.pack(expand=True)
        card.pack_propagate(False)

        # Card header strip
        card_hdr = ctk.CTkFrame(
            card,
            fg_color=th.BG_RAISED,
            corner_radius=0,
            height=56,
        )
        card_hdr.pack(fill="x")
        card_hdr.pack_propagate(False)

        # Excel icon mark
        xls_badge = ctk.CTkFrame(
            card_hdr,
            width=32, height=32,
            corner_radius=th.R_SM,
            fg_color="#1D6F42",   # Excel green
        )
        xls_badge.pack(side="left", padx=(16, 10), pady=12)
        xls_badge.pack_propagate(False)
        ctk.CTkLabel(
            xls_badge, text="XLS", font=th.bold(8), text_color="#FFFFFF"
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            card_hdr,
            text="Exportar fichajes a Excel",
            font=th.bold(14),
            text_color=th.T_PRIMARY,
        ).pack(side="left", pady=16)

        th.separator(card)

        # Body
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=24, pady=20)

        ctk.CTkLabel(
            body,
            text="Rango de fechas (opcional)",
            font=th.bold(11),
            text_color=th.T_SECONDARY,
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        date_row = ctk.CTkFrame(body, fg_color="transparent")
        date_row.pack(fill="x")

        ctk.CTkLabel(
            date_row, text="Desde", font=th.f(12), text_color=th.T_MUTED, width=50
        ).pack(side="left")

        self._exp_from = ctk.CTkEntry(
            date_row,
            placeholder_text="AAAA-MM-DD",
            width=158,
            height=40,
            font=th.f(13),
            **th.entry_kwargs(),
        )
        self._exp_from.pack(side="left", padx=(6, 12))

        ctk.CTkLabel(
            date_row, text="Hasta", font=th.f(12), text_color=th.T_MUTED, width=46
        ).pack(side="left")

        self._exp_to = ctk.CTkEntry(
            date_row,
            placeholder_text="AAAA-MM-DD",
            width=158,
            height=40,
            font=th.f(13),
            **th.entry_kwargs(),
        )
        self._exp_to.pack(side="left", padx=(6, 0))

        ctk.CTkLabel(
            body,
            text="Deja ambos campos vacíos para exportar todos los registros.",
            font=th.f(11),
            text_color=th.T_MUTED,
        ).pack(anchor="w", pady=(8, 0))

        th.separator(card, padx=24, pady=(16, 0))

        # Status + button
        bottom = ctk.CTkFrame(card, fg_color="transparent")
        bottom.pack(fill="x", padx=24, pady=20)

        self._exp_status = ctk.CTkLabel(
            bottom,
            text="",
            font=th.f(12),
            text_color=th.SUCCESS_TEXT,
            wraplength=500,
            anchor="w",
        )
        self._exp_status.pack(fill="x", pady=(0, 14))

        ctk.CTkButton(
            bottom,
            text="Generar archivo Excel",
            height=50,
            font=th.bold(14),
            **th.primary_button_kwargs(),
            command=self._export_excel,
        ).pack(fill="x")

    # ═════════════════════════════════════════════════════════════════════════
    # Data helpers
    # ═════════════════════════════════════════════════════════════════════════

    def _reload_fichajes(self) -> None:
        date_from = self._fich_from.get().strip() or None
        date_to   = self._fich_to.get().strip() or None

        rows = self.export_service.time_entry_repository.list_with_employee_names(
            date_from=date_from, date_to=date_to
        )

        total = len(rows)
        entries = sum(1 for row in rows if row["entry_type"] == TimeClockService.ENTRY)
        exits = sum(1 for row in rows if row["entry_type"] == TimeClockService.EXIT)
        self._fich_total_card.set(total)
        self._fich_entry_card.set(entries)
        self._fich_exit_card.set(exits)
        self._fich_empty_hint.configure(
            text="Sin resultados para ese periodo." if total == 0 else ""
        )

        self._fich_tree.delete(*self._fich_tree.get_children())
        for i, row in enumerate(rows):
            date_str, time_str = split_timestamp(row["timestamp"])
            is_entrada = row["entry_type"] == TimeClockService.ENTRY
            row_tag  = "even" if i % 2 == 0 else "odd"
            type_tag = "entrada" if is_entrada else "salida"
            self._fich_tree.insert(
                "", "end",
                values=(
                    row["id"],
                    row["employee_name"],
                    label_for_entry_type(row["entry_type"]),
                    date_str,
                    time_str,
                    row["notes"] or "",
                ),
                tags=(row_tag, type_tag),
            )

    def _clear_fich_filter(self) -> None:
        self._fich_from.delete(0, "end")
        self._fich_to.delete(0, "end")
        self._reload_fichajes()

    def _reload_employees(self) -> None:
        self._emp_tree.delete(*self._emp_tree.get_children())
        employees = self.employee_service.list_employees()
        statuses = self.time_clock_service.get_attendance_statuses(employees)
        total = len(employees)
        active = sum(1 for emp in employees if emp.active)
        admins = sum(1 for emp in employees if emp.role == "admin")
        clocked_in = sum(
            1 for status in statuses if status.employee.active and status.is_clocked_in
        )
        self._emp_total_card.set(total)
        self._emp_active_card.set(active)
        self._emp_clocked_in_card.set(clocked_in)
        self._emp_admin_card.set(admins)

        current_filter = self._employee_filter.get()
        if current_filter == "Activos":
            statuses = [status for status in statuses if status.employee.active]
        elif current_filter == "Inactivos":
            statuses = [status for status in statuses if not status.employee.active]

        for i, status in enumerate(statuses):
            emp = status.employee
            row_tag = "even" if i % 2 == 0 else "odd"
            status_tag = "clocked_in" if status.is_clocked_in else "clocked_out"
            tags = (row_tag, "inactive") if not emp.active else (row_tag, status_tag)
            last_action = (
                f"{status.last_action_label} "
                f"{format_timestamp(status.last_timestamp, '%d/%m %H:%M')}"
                if status.last_timestamp
                else "Sin fichajes"
            )
            self._emp_tree.insert(
                "", "end",
                iid=str(emp.id),
                values=(
                    emp.first_name,
                    emp.last_name,
                    emp.username,
                    emp.role,
                    "Activo" if emp.active else "Inactivo",
                    status.status_label,
                    last_action,
                ),
                tags=tags,
            )

    def _schedule_employee_refresh(self) -> None:
        if not self.winfo_exists():
            return
        self._employee_refresh_after_id = self.after(
            15000,
            self._refresh_employee_statuses,
        )

    def _refresh_employee_statuses(self) -> None:
        if not self.winfo_exists():
            return
        self._reload_employees()
        self._schedule_employee_refresh()

    def destroy(self) -> None:
        if self._employee_refresh_after_id:
            self.after_cancel(self._employee_refresh_after_id)
            self._employee_refresh_after_id = None
        super().destroy()

    # ═════════════════════════════════════════════════════════════════════════
    # Actions
    # ═════════════════════════════════════════════════════════════════════════

    def _toggle_selected_employee(self) -> None:
        selected = self._emp_tree.selection()
        if not selected:
            self._emp_status.configure(
                text="Selecciona un empleado primero.",
                text_color=th.DANGER_TEXT,
            )
            return
        emp_id = int(selected[0])
        new_state = self.employee_service.toggle_active(emp_id)
        verb = "activado" if new_state else "desactivado"
        self._emp_status.configure(
            text=f"Empleado {verb} correctamente.",
            text_color=th.SUCCESS_TEXT,
        )
        self._reload_employees()

    def _create_employee(self) -> None:
        try:
            self.employee_service.create_employee(
                first_name=self._new_first_name.get(),
                last_name=self._new_last_name.get(),
                password=self._new_password.get(),
                role=self._new_role.get(),
            )
        except ValueError as exc:
            self._add_status.configure(text=str(exc), text_color=th.DANGER_TEXT)
            return

        name = (
            f"{self._new_first_name.get().strip()} "
            f"{self._new_last_name.get().strip()}"
        ).strip()
        self._add_status.configure(
            text=f"'{name}' creado correctamente.",
            text_color=th.SUCCESS_TEXT,
        )
        self._new_first_name.delete(0, "end")
        self._new_last_name.delete(0, "end")
        self._new_password.delete(0, "end")
        self._new_role.set("employee")
        self._reload_employees()

    def _export_excel(self) -> None:
        date_from = self._exp_from.get().strip() or None
        date_to   = self._exp_to.get().strip() or None

        try:
            path = self.export_service.export_time_entries_to_excel(
                date_from=date_from, date_to=date_to
            )
        except RuntimeError as exc:
            self._exp_status.configure(
                text=f"Error: {exc}", text_color=th.DANGER_TEXT
            )
            return

        self._exp_status.configure(
            text=f"Archivo guardado:\n{path}",
            text_color=th.SUCCESS_TEXT,
        )
