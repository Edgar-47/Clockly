"""
Login screen — split-panel layout.

Left  (40 %) : brand panel – deep navy with app identity.
Right (60 %) : form panel  – credential fields and submit button.

Errors from the auth layer (ValueError) are caught here and displayed
inline; no native messagebox is ever shown.
"""

from collections.abc import Callable

import customtkinter as ctk

from app.ui import theme as th


class LoginView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        on_login: Callable[[str, str], None],
        on_cancel: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(master, corner_radius=0, fg_color=th.BG_ROOT)
        self.on_login = on_login
        self.on_cancel = on_cancel
        self._compact_layout = False
        self._build()
        self.bind("<Configure>", self._on_resize)

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self) -> None:
        self.columnconfigure(0, weight=5)
        self.columnconfigure(1, weight=7)
        self.rowconfigure(0, weight=1)

        self._brand_panel = self._build_brand(self)
        self._form_panel = self._build_form(self)

    def _on_resize(self, event) -> None:
        if event.widget is not self:
            return
        compact = event.width < 820
        if compact == self._compact_layout:
            return
        self._compact_layout = compact

        if compact:
            self._brand_panel.grid_forget()
            self._form_panel.grid(row=0, column=0, columnspan=2, sticky="nsew")
        else:
            self._form_panel.grid_forget()
            self._brand_panel.grid(row=0, column=0, sticky="nsew")
            self._form_panel.grid(row=0, column=1, sticky="nsew")

    # ── Left: brand panel ─────────────────────────────────────────────────────

    def _build_brand(self, root: ctk.CTkFrame) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(root, corner_radius=0, fg_color=th.BRAND_BG)
        panel.grid(row=0, column=0, sticky="nsew")

        ctk.CTkFrame(panel, height=4, corner_radius=0, fg_color=th.ACCENT).pack(fill="x")

        inner = ctk.CTkFrame(panel, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner,
            text="",
            image=th.logo_for_dark(size=(280, 170)),
        ).pack(pady=(0, 18))

        ctk.CTkLabel(
            inner,
            text="Control horario ClockLy",
            font=th.bold(27),
            text_color=th.BRAND_TEXT,
            justify="center",
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            inner,
            text="Control horario claro para equipos de sala, barra y cocina.",
            font=th.f(14),
            text_color=th.BRAND_SUB,
            justify="center",
            wraplength=290,
        ).pack(pady=(0, 24))

        proof = ctk.CTkFrame(
            inner,
            fg_color=th.BG_CARD,
            corner_radius=th.R_LG,
            border_width=1,
            border_color=th.BORDER,
        )
        proof.pack(fill="x")

        for text in (
            "Fichajes en segundos",
            "Registro local en SQLite",
            "Exportación preparada para Excel",
        ):
            row = ctk.CTkFrame(proof, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=(12, 0))
            ctk.CTkFrame(
                row,
                width=7,
                height=7,
                corner_radius=3,
                fg_color=th.ACCENT,
            ).pack(side="left", padx=(0, 9), pady=5)
            ctk.CTkLabel(
                row,
                text=text,
                font=th.f(12),
                text_color=th.T_SECONDARY,
            ).pack(side="left")

        ctk.CTkLabel(
            proof,
            text="Acceso local para administradores y empleados",
            font=th.bold(11),
            text_color=th.WARNING_TEXT,
        ).pack(anchor="w", padx=14, pady=(12, 14))

        ctk.CTkLabel(
            panel,
            text="Seguro · rápido · local",
            font=th.f(11),
            text_color=th.T_MUTED,
        ).place(relx=0.5, rely=0.96, anchor="center")
        return panel

    # ── Right: form panel ─────────────────────────────────────────────────────

    def _build_form(self, root: ctk.CTkFrame) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(root, corner_radius=0, fg_color=th.BG_ROOT)
        panel.grid(row=0, column=1, sticky="nsew")

        form = th.card(panel, width=430, height=520)
        form.place(relx=0.5, rely=0.5, anchor="center")
        form.pack_propagate(False)

        ctk.CTkLabel(
            form,
            text="ACCESO",
            font=th.bold(10),
            text_color=th.ACCENT_SOFT,
            fg_color=th.ACCENT_DIM,
            corner_radius=th.R_SM,
        ).pack(anchor="w", padx=26, pady=(26, 14), ipadx=10, ipady=4)

        ctk.CTkLabel(
            form,
            text="Iniciar sesion",
            font=th.bold(28),
            text_color=th.T_PRIMARY,
        ).pack(anchor="w", padx=26, pady=(0, 6))

        ctk.CTkLabel(
            form,
            text="Identificate con admin o con el DNI de empleado para iniciar la asistencia.",
            font=th.f(13),
            text_color=th.T_SECONDARY,
            wraplength=360,
            justify="left",
        ).pack(anchor="w", padx=26, pady=(0, 28))

        ctk.CTkLabel(
            form,
            text="IDENTIFICADOR",
            font=th.bold(10),
            text_color=th.T_SECONDARY,
            anchor="w",
        ).pack(fill="x", padx=26)

        self._username = ctk.CTkEntry(
            form,
            placeholder_text="admin o DNI",
            height=48,
            font=th.f(14),
            **th.entry_kwargs(),
        )
        self._username.pack(fill="x", padx=26, pady=(6, 18))

        ctk.CTkLabel(
            form,
            text="CONTRASENA",
            font=th.bold(10),
            text_color=th.T_SECONDARY,
            anchor="w",
        ).pack(fill="x", padx=26)

        self._password = ctk.CTkEntry(
            form,
            placeholder_text="********",
            show="*",
            height=48,
            font=th.f(14),
            **th.entry_kwargs(),
        )
        self._password.pack(fill="x", padx=26, pady=(6, 8))

        self._error_lbl = ctk.CTkLabel(
            form,
            text="",
            font=th.f(12),
            text_color=th.DANGER_TEXT,
            wraplength=360,
            anchor="w",
        )
        self._error_lbl.pack(fill="x", padx=26, pady=(4, 18))

        ctk.CTkButton(
            form,
            text="Entrar",
            height=52,
            font=th.bold(15),
            **th.primary_button_kwargs(),
            command=self._submit,
        ).pack(fill="x", padx=26)

        if self.on_cancel:
            ctk.CTkButton(
                form,
                text="Volver",
                height=44,
                font=th.f(13),
                **th.quiet_button_kwargs(),
                command=self.on_cancel,
            ).pack(fill="x", padx=26, pady=(12, 24))

        self._username.bind("<Return>", lambda _: self._password.focus())
        self._password.bind("<Return>", lambda _: self._submit())
        self._username.focus()
        return panel

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _submit(self) -> None:
        username = self._username.get().strip()
        password = self._password.get()

        if not username or not password:
            self._show_error("Por favor introduce identificador y contrasena.")
            return

        self._clear_error()

        try:
            self.on_login(username, password)
        except ValueError as exc:
            self._show_error(str(exc))

    def _show_error(self, message: str) -> None:
        self._error_lbl.configure(text=f"  {message}")
        self._password.delete(0, "end")
        self._password.focus()

    def _clear_error(self) -> None:
        self._error_lbl.configure(text="")
