"""
Login screen — split-panel layout.

Left  (40 %) : brand panel – identity panel con logo y propuesta de valor.
Right (60 %) : form panel  – campos de credenciales y botón de acceso.

Los errores de la capa de autenticación (ValueError) se muestran inline;
nunca se abre un messagebox nativo.
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
        self._show_password = False
        self._loading = False
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

    # ── Panel izquierdo: marca ────────────────────────────────────────────────

    def _build_brand(self, root: ctk.CTkFrame) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(root, corner_radius=0, fg_color=th.BRAND_BG)
        panel.grid(row=0, column=0, sticky="nsew")

        # Barra de acento superior
        ctk.CTkFrame(panel, height=3, corner_radius=0, fg_color=th.ACCENT).pack(fill="x")

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
            font=th.bold(26),
            text_color=th.BRAND_TEXT,
            justify="center",
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            inner,
            text="Gestión de asistencia clara\npara equipos de sala, barra y cocina.",
            font=th.f(13),
            text_color=th.BRAND_SUB,
            justify="center",
            wraplength=290,
        ).pack(pady=(0, 28))

        # Tarjeta de características
        proof = ctk.CTkFrame(
            inner,
            fg_color=th.BG_CARD,
            corner_radius=th.R_LG,
            border_width=1,
            border_color=th.BORDER,
        )
        proof.pack(fill="x")

        features = [
            ("Fichajes en segundos",                th.ACCENT),
            ("Registro local seguro en SQLite",     th.SUCCESS),
            ("Exportación directa a Excel",         th.WARNING),
        ]
        for i, (text, dot_color) in enumerate(features):
            row = ctk.CTkFrame(proof, fg_color="transparent")
            top_pad = 14 if i == 0 else 8
            row.pack(fill="x", padx=14, pady=(top_pad, 0))

            ctk.CTkFrame(
                row,
                width=7,
                height=7,
                corner_radius=3,
                fg_color=dot_color,
            ).pack(side="left", padx=(0, 10), pady=5)

            ctk.CTkLabel(
                row,
                text=text,
                font=th.f(12),
                text_color=th.T_SECONDARY,
            ).pack(side="left")

        th.separator(proof, padx=14, pady=(12, 0))

        ctk.CTkLabel(
            proof,
            text="Acceso local para administradores y empleados",
            font=th.bold(10),
            text_color=th.WARNING_TEXT,
        ).pack(anchor="w", padx=14, pady=(10, 14))

        ctk.CTkLabel(
            panel,
            text="Seguro · rápido · local",
            font=th.f(10),
            text_color=th.T_MUTED,
        ).place(relx=0.5, rely=0.96, anchor="center")
        return panel

    # ── Panel derecho: formulario ─────────────────────────────────────────────

    def _build_form(self, root: ctk.CTkFrame) -> ctk.CTkFrame:
        panel = ctk.CTkFrame(root, corner_radius=0, fg_color=th.BG_ROOT)
        panel.grid(row=0, column=1, sticky="nsew")

        form = th.card(panel, width=430, height=540)
        form.place(relx=0.5, rely=0.5, anchor="center")
        form.pack_propagate(False)

        # ── Badge ──
        ctk.CTkLabel(
            form,
            text="ACCESO",
            font=th.bold(10),
            text_color=th.ACCENT_SOFT,
            fg_color=th.ACCENT_DIM,
            corner_radius=th.R_SM,
        ).pack(anchor="w", padx=28, pady=(28, 14), ipadx=10, ipady=4)

        # ── Título ──
        ctk.CTkLabel(
            form,
            text="Iniciar sesión",
            font=th.bold(28),
            text_color=th.T_PRIMARY,
        ).pack(anchor="w", padx=28, pady=(0, 6))

        ctk.CTkLabel(
            form,
            text="Identifícate con «admin» o con el DNI del empleado.",
            font=th.f(13),
            text_color=th.T_SECONDARY,
            wraplength=360,
            justify="left",
        ).pack(anchor="w", padx=28, pady=(0, 24))

        # ── Campo identificador ──
        ctk.CTkLabel(
            form,
            text="IDENTIFICADOR",
            font=th.bold(9),
            text_color=th.T_MUTED,
            anchor="w",
        ).pack(fill="x", padx=28)

        self._username = ctk.CTkEntry(
            form,
            placeholder_text="admin  ó  DNI del empleado",
            height=46,
            font=th.f(14),
            **th.entry_kwargs(),
        )
        self._username.pack(fill="x", padx=28, pady=(5, 18))

        # ── Campo contraseña con toggle ──
        ctk.CTkLabel(
            form,
            text="CONTRASEÑA",
            font=th.bold(9),
            text_color=th.T_MUTED,
            anchor="w",
        ).pack(fill="x", padx=28)

        pw_row = ctk.CTkFrame(form, fg_color="transparent")
        pw_row.pack(fill="x", padx=28, pady=(5, 0))

        self._password = ctk.CTkEntry(
            pw_row,
            placeholder_text="••••••••",
            show="•",
            height=46,
            font=th.f(14),
            **th.entry_kwargs(),
        )
        self._password.pack(side="left", fill="x", expand=True)

        self._eye_btn = ctk.CTkButton(
            pw_row,
            text="Ver",
            width=52,
            height=46,
            font=th.f(11),
            **th.quiet_button_kwargs(),
            command=self._toggle_password,
        )
        self._eye_btn.pack(side="right", padx=(6, 0))

        # ── Mensaje de error ──
        self._error_lbl = ctk.CTkLabel(
            form,
            text="",
            font=th.f(12),
            text_color=th.DANGER_TEXT,
            fg_color="transparent",
            wraplength=360,
            anchor="w",
            justify="left",
        )
        self._error_lbl.pack(fill="x", padx=28, pady=(10, 14))

        # ── Botón principal ──
        self._submit_btn = ctk.CTkButton(
            form,
            text="Entrar",
            height=52,
            font=th.bold(15),
            **th.primary_button_kwargs(),
            command=self._submit,
        )
        self._submit_btn.pack(fill="x", padx=28)

        if self.on_cancel:
            ctk.CTkButton(
                form,
                text="Volver",
                height=44,
                font=th.f(13),
                **th.quiet_button_kwargs(),
                command=self.on_cancel,
            ).pack(fill="x", padx=28, pady=(10, 0))

        self._username.bind("<Return>", lambda _: self._password.focus())
        self._password.bind("<Return>", lambda _: self._submit())
        self._username.focus()
        return panel

    # ── Toggle contraseña ─────────────────────────────────────────────────────

    def _toggle_password(self) -> None:
        self._show_password = not self._show_password
        # Accedemos al Entry de tkinter subyacente para cambiar `show`
        self._password._entry.config(show="" if self._show_password else "•")
        self._eye_btn.configure(text="Ocultar" if self._show_password else "Ver")

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _submit(self) -> None:
        if self._loading:
            return

        username = self._username.get().strip()
        password = self._password.get()

        if not username or not password:
            self._show_error("Introduce identificador y contraseña.")
            return

        self._clear_error()
        self._set_loading(True)

        # Usamos after(0) para que la UI se actualice antes del bloqueo del login
        self.after(50, lambda: self._do_login(username, password))

    def _do_login(self, username: str, password: str) -> None:
        try:
            self.on_login(username, password)
        except ValueError as exc:
            self._show_error(str(exc))
        finally:
            if self.winfo_exists():
                self._set_loading(False)

    def _set_loading(self, loading: bool) -> None:
        self._loading = loading
        if loading:
            self._submit_btn.configure(
                text="Verificando...",
                state="disabled",
                fg_color=th.ACCENT_DIM,
                text_color=th.T_MUTED,
            )
        else:
            self._submit_btn.configure(
                text="Entrar",
                state="normal",
                **th.primary_button_kwargs(),
            )

    def _show_error(self, message: str) -> None:
        self._error_lbl.configure(
            text=f"  ✕  {message}",
            text_color=th.DANGER_TEXT,
            fg_color=th.DANGER_DIM,
            corner_radius=th.R_SM,
        )
        self._password.delete(0, "end")
        self._password.focus()

    def _clear_error(self) -> None:
        self._error_lbl.configure(text="", fg_color="transparent")
