from collections.abc import Callable

import customtkinter as ctk

from app.models.business import Business
from app.services.business_service import BusinessService
from app.ui import theme as th


class BusinessSelectorView(ctk.CTkFrame):
    def __init__(
        self,
        master,
        *,
        businesses: list[Business],
        user_name: str,
        on_select: Callable[[str], None],
        on_create_new: Callable[[], None],
        on_logout: Callable[[], None],
    ) -> None:
        super().__init__(master, corner_radius=0, fg_color=th.BG_ROOT)
        self.businesses = businesses
        self.user_name = user_name
        self.on_select = on_select
        self.on_create_new = on_create_new
        self.on_logout = on_logout
        self._build()

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        shell = ctk.CTkFrame(self, fg_color="transparent")
        shell.grid(row=0, column=0, sticky="nsew", padx=32, pady=28)
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(2, weight=1)

        top = ctk.CTkFrame(shell, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 18))

        title_col = ctk.CTkFrame(top, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            title_col,
            text="Elige un negocio",
            font=th.bold(30),
            text_color=th.T_PRIMARY,
            anchor="w",
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_col,
            text=f"{self.user_name}, selecciona donde quieres trabajar ahora.",
            font=th.f(13),
            text_color=th.T_SECONDARY,
            anchor="w",
        ).pack(anchor="w", pady=(5, 0))

        action_row = ctk.CTkFrame(top, fg_color="transparent")
        action_row.pack(side="right")
        ctk.CTkButton(
            action_row,
            text="Nuevo negocio",
            width=132,
            height=38,
            font=th.f(12),
            **th.primary_button_kwargs(),
            command=self.on_create_new,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            action_row,
            text="Cerrar sesion",
            width=122,
            height=38,
            font=th.f(12),
            **th.quiet_button_kwargs(),
            command=self.on_logout,
        ).pack(side="left")

        th.separator(shell)

        list_frame = ctk.CTkScrollableFrame(
            shell,
            fg_color="transparent",
            scrollbar_button_color=th.BORDER,
            scrollbar_button_hover_color=th.BORDER_LT,
        )
        list_frame.grid(row=2, column=0, sticky="nsew", pady=(20, 0))
        list_frame.columnconfigure((0, 1), weight=1, uniform="business_cards")

        for index, business in enumerate(self.businesses):
            card = self._business_card(list_frame, business)
            card.grid(
                row=index // 2,
                column=index % 2,
                sticky="nsew",
                padx=10,
                pady=10,
            )

    def _business_card(self, parent: ctk.CTkFrame, business: Business) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            parent,
            fg_color=th.BG_CARD,
            corner_radius=th.R_LG,
            border_width=1,
            border_color=th.BORDER,
        )
        card.columnconfigure(0, weight=1)

        type_label = BusinessService.BUSINESS_TYPES.get(
            business.business_type,
            business.business_type.title(),
        )
        ctk.CTkLabel(
            card,
            text=type_label.upper(),
            font=th.bold(9),
            text_color=th.ACCENT_SOFT,
            fg_color=th.ACCENT_DIM,
            corner_radius=th.R_SM,
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 10), ipadx=8, ipady=3)

        ctk.CTkLabel(
            card,
            text=business.business_name,
            font=th.bold(19),
            text_color=th.T_PRIMARY,
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=18)

        ctk.CTkLabel(
            card,
            text=f"Codigo: {business.login_code}  |  ID: {business.short_id}",
            font=th.f(12),
            text_color=th.T_MUTED,
            anchor="w",
        ).grid(row=2, column=0, sticky="ew", padx=18, pady=(6, 16))

        ctk.CTkButton(
            card,
            text="Entrar",
            height=42,
            font=th.bold(13),
            **th.primary_button_kwargs(),
            command=lambda: self.on_select(business.id),
        ).grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 18))

        return card
