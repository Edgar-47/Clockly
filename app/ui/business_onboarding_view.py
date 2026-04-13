from collections.abc import Callable

import customtkinter as ctk

from app.models.business import Business
from app.services.business_service import BusinessService
from app.ui import theme as th


class BusinessOnboardingView(ctk.CTkFrame):
    BUSINESS_OPTIONS = [
        ("cafeteria", "CAF", "Cafeteria"),
        ("restaurante", "RES", "Restaurante"),
        ("bar", "BAR", "Bar"),
        ("tienda", "TDA", "Tienda"),
        ("taller", "TLR", "Taller"),
        ("peluqueria", "PEL", "Peluqueria"),
        ("clinica", "CLI", "Clinica"),
        ("gimnasio", "GYM", "Gimnasio"),
        ("oficina", "OFI", "Oficina"),
        ("otro", "OTR", "Otro"),
    ]

    def __init__(
        self,
        master,
        *,
        owner_name: str,
        on_create: Callable[[str, str, str], Business],
        on_continue: Callable[[Business], None],
        on_cancel: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master, corner_radius=0, fg_color=th.BG_ROOT)
        self.owner_name = owner_name
        self.on_create = on_create
        self.on_continue = on_continue
        self.on_cancel = on_cancel

        self._selected_type = "restaurante"
        self._type_buttons: dict[str, ctk.CTkButton] = {}
        self._loading = False
        self._code_edited = False

        self._build()

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.grid(row=0, column=0, sticky="nsew", padx=28, pady=24)
        wrapper.columnconfigure(0, weight=4)
        wrapper.columnconfigure(1, weight=5)
        wrapper.rowconfigure(0, weight=1)

        self._build_intro(wrapper)
        self._build_form(wrapper)

    def _build_intro(self, parent: ctk.CTkFrame) -> None:
        panel = ctk.CTkFrame(parent, corner_radius=0, fg_color="transparent")
        panel.grid(row=0, column=0, sticky="nsew", padx=(0, 22))
        panel.rowconfigure(1, weight=1)

        ctk.CTkLabel(
            panel,
            text="Configura tu negocio",
            font=th.bold(34),
            text_color=th.T_PRIMARY,
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", pady=(24, 10))

        copy = ctk.CTkFrame(panel, fg_color="transparent")
        copy.grid(row=1, column=0, sticky="new")

        ctk.CTkLabel(
            copy,
            text=(
                "Hola, "
                + (self.owner_name or "admin")
                + ". Crea tu primer negocio para empezar a gestionar fichajes, "
                "empleados y reportes desde un entorno propio."
            ),
            font=th.f(15),
            text_color=th.T_SECONDARY,
            wraplength=420,
            justify="left",
        ).pack(anchor="w", pady=(0, 22))

        for title, body, color in [
            (
                "1 minuto",
                "Nombre, tipo de negocio y codigo corto de acceso.",
                th.ACCENT,
            ),
            (
                "Multi-negocio",
                "La cuenta queda preparada para gestionar varios negocios.",
                th.SUCCESS,
            ),
            (
                "ID automatico",
                "El identificador interno se genera y guarda sin que tengas que tocarlo.",
                th.WARNING,
            ),
        ]:
            item = ctk.CTkFrame(copy, fg_color="transparent")
            item.pack(fill="x", pady=(0, 14))
            ctk.CTkFrame(
                item,
                width=8,
                height=38,
                corner_radius=4,
                fg_color=color,
            ).pack(side="left", padx=(0, 12))
            text_col = ctk.CTkFrame(item, fg_color="transparent")
            text_col.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(
                text_col,
                text=title,
                font=th.bold(13),
                text_color=th.T_PRIMARY,
                anchor="w",
            ).pack(anchor="w")
            ctk.CTkLabel(
                text_col,
                text=body,
                font=th.f(12),
                text_color=th.T_MUTED,
                anchor="w",
                wraplength=360,
                justify="left",
            ).pack(anchor="w")

        footer = ctk.CTkFrame(
            panel,
            fg_color=th.BG_CARD,
            corner_radius=th.R_LG,
            border_width=1,
            border_color=th.BORDER,
        )
        footer.grid(row=2, column=0, sticky="ew", pady=(18, 18))
        ctk.CTkLabel(
            footer,
            text="Despues podras usar este codigo como acceso rapido al negocio.",
            font=th.f(12),
            text_color=th.ACCENT_SOFT,
            wraplength=390,
            justify="left",
        ).pack(anchor="w", padx=16, pady=14)

    def _build_form(self, parent: ctk.CTkFrame) -> None:
        card = th.card(parent)
        card.grid(row=0, column=1, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(1, weight=1)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 8))

        ctk.CTkLabel(
            header,
            text="Nuevo negocio",
            font=th.bold(20),
            text_color=th.T_PRIMARY,
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Elige el tipo y completa los datos basicos.",
            font=th.f(12),
            text_color=th.T_MUTED,
            anchor="w",
        ).pack(anchor="w", pady=(4, 0))

        body = ctk.CTkScrollableFrame(
            card,
            fg_color="transparent",
            scrollbar_button_color=th.BORDER,
            scrollbar_button_hover_color=th.BORDER_LT,
        )
        body.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 8))
        body.columnconfigure((0, 1), weight=1, uniform="business_type")

        ctk.CTkLabel(
            body,
            text="TIPO DE NEGOCIO",
            font=th.bold(9),
            text_color=th.T_MUTED,
            anchor="w",
        ).grid(row=0, column=0, columnspan=2, sticky="ew", padx=8, pady=(8, 8))

        for index, (value, short, label) in enumerate(self.BUSINESS_OPTIONS):
            btn = ctk.CTkButton(
                body,
                text=f"{short}\n{label}",
                height=66,
                font=th.bold(12),
                border_width=1,
                corner_radius=th.R_MD,
                command=lambda selected=value: self._select_type(selected),
            )
            row = 1 + index // 2
            col = index % 2
            btn.grid(row=row, column=col, sticky="ew", padx=8, pady=6)
            self._type_buttons[value] = btn

        field_row = 7
        self._business_name = self._field(
            body,
            field_row,
            "NOMBRE DEL NEGOCIO",
            "Ej. Restaurante La Plaza",
        )
        self._business_name.bind("<KeyRelease>", self._maybe_suggest_code)

        self._login_code = self._field(
            body,
            field_row + 2,
            "CODIGO DE INICIO DE SESION",
            "Ej. LA-PLAZA",
        )
        self._login_code.bind("<KeyRelease>", self._mark_code_edited)

        ctk.CTkLabel(
            body,
            text="ID DEL NEGOCIO",
            font=th.bold(9),
            text_color=th.T_MUTED,
            anchor="w",
        ).grid(row=field_row + 4, column=0, columnspan=2, sticky="ew", padx=8, pady=(16, 0))

        self._business_id_preview = ctk.CTkLabel(
            body,
            text="Se generara automaticamente al crear el negocio.",
            font=th.f(12),
            text_color=th.T_SECONDARY,
            fg_color=th.BG_RAISED,
            corner_radius=th.R_MD,
            anchor="w",
        )
        self._business_id_preview.grid(
            row=field_row + 5,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=8,
            pady=(5, 0),
            ipady=10,
        )

        self._error_lbl = ctk.CTkLabel(
            body,
            text="",
            font=th.f(12),
            text_color=th.DANGER_TEXT,
            fg_color="transparent",
            wraplength=420,
            justify="left",
            anchor="w",
        )
        self._error_lbl.grid(
            row=field_row + 6,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=8,
            pady=(12, 0),
        )

        footer = ctk.CTkFrame(card, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 22))
        footer.columnconfigure(0, weight=1)

        self._submit_btn = ctk.CTkButton(
            footer,
            text="Crear negocio y continuar",
            height=48,
            font=th.bold(14),
            **th.primary_button_kwargs(),
            command=self._submit,
        )
        self._submit_btn.grid(row=0, column=0, sticky="ew")

        if self.on_cancel:
            ctk.CTkButton(
                footer,
                text="Volver",
                height=40,
                font=th.f(12),
                **th.quiet_button_kwargs(),
                command=self.on_cancel,
            ).grid(row=1, column=0, sticky="ew", pady=(9, 0))

        self._select_type(self._selected_type)
        self._business_name.focus()

    def _field(
        self,
        parent: ctk.CTkFrame,
        row: int,
        label: str,
        placeholder: str,
    ) -> ctk.CTkEntry:
        ctk.CTkLabel(
            parent,
            text=label,
            font=th.bold(9),
            text_color=th.T_MUTED,
            anchor="w",
        ).grid(row=row, column=0, columnspan=2, sticky="ew", padx=8, pady=(16, 0))

        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            height=44,
            font=th.f(13),
            **th.entry_kwargs(),
        )
        entry.grid(
            row=row + 1,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=8,
            pady=(5, 0),
        )
        return entry

    def _select_type(self, business_type: str) -> None:
        self._selected_type = business_type
        for value, button in self._type_buttons.items():
            if value == business_type:
                button.configure(
                    fg_color=th.ACCENT_DIM,
                    hover_color=th.ACCENT_DIM,
                    border_color=th.ACCENT,
                    text_color=th.ACCENT_SOFT,
                )
            else:
                button.configure(
                    fg_color=th.BG_RAISED,
                    hover_color=th.BG_HOVER,
                    border_color=th.BORDER_LT,
                    text_color=th.T_SECONDARY,
                )

    def _maybe_suggest_code(self, _event=None) -> None:
        if self._code_edited:
            return
        name = self._business_name.get().strip()
        if not name:
            return
        suggestion = "-".join(name.upper().split())[:18]
        self._login_code.delete(0, "end")
        self._login_code.insert(0, suggestion)

    def _mark_code_edited(self, _event=None) -> None:
        self._code_edited = True

    def _submit(self) -> None:
        if self._loading:
            return

        name = self._business_name.get().strip()
        login_code = self._login_code.get().strip()

        if not name:
            self._show_error("El nombre del negocio es obligatorio.")
            return
        if not login_code:
            self._show_error("El codigo de inicio de sesion es obligatorio.")
            return
        if self._selected_type not in BusinessService.BUSINESS_TYPES:
            self._show_error("Selecciona un tipo de negocio.")
            return

        self._clear_error()
        self._set_loading(True)
        self.after(50, lambda: self._do_create(name, self._selected_type, login_code))

    def _do_create(self, name: str, business_type: str, login_code: str) -> None:
        try:
            business = self.on_create(name, business_type, login_code)
        except ValueError as exc:
            self._set_loading(False)
            self._show_error(str(exc))
            return

        self._business_id_preview.configure(
            text=f"ID creado: {business.id}",
            text_color=th.SUCCESS_TEXT,
            fg_color=th.SUCCESS_DIM,
        )
        self._error_lbl.configure(
            text="Negocio creado correctamente. Entrando al panel...",
            text_color=th.SUCCESS_TEXT,
            fg_color="transparent",
        )
        self.after(650, lambda: self.on_continue(business))

    def _set_loading(self, loading: bool) -> None:
        self._loading = loading
        if loading:
            self._submit_btn.configure(
                text="Creando negocio...",
                state="disabled",
                fg_color=th.ACCENT_DIM,
                text_color=th.T_MUTED,
            )
        else:
            self._submit_btn.configure(
                text="Crear negocio y continuar",
                state="normal",
                **th.primary_button_kwargs(),
            )

    def _show_error(self, message: str) -> None:
        self._error_lbl.configure(
            text=message,
            text_color=th.DANGER_TEXT,
            fg_color=th.DANGER_DIM,
            corner_radius=th.R_SM,
        )

    def _clear_error(self) -> None:
        self._error_lbl.configure(text="", fg_color="transparent")
