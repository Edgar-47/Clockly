"""
ActiveEmployeesSidebar — panel lateral con empleados actualmente fichados.

Muestra una tarjeta por cada empleado con sesión activa. Se actualiza
automáticamente cada 10 s y expone refresh() para actualizaciones inmediatas
después de eventos de fichaje/desfichaje.
"""

from __future__ import annotations

import customtkinter as ctk

from app.services.time_clock_service import TimeClockService
from app.ui import theme as th

SIDEBAR_WIDTH = 224
POLL_INTERVAL_MS = 10_000  # 10 segundos


def _format_elapsed(total_seconds: int) -> str:
    hours, remainder = divmod(max(int(total_seconds), 0), 3600)
    minutes, _ = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m en turno"
    return f"{minutes}m en turno"


class ActiveEmployeesSidebar(ctk.CTkFrame):
    """Panel lateral que lista empleados con sesión de fichaje activa."""

    def __init__(
        self,
        master,
        *,
        time_clock_service: TimeClockService,
    ) -> None:
        super().__init__(
            master,
            width=SIDEBAR_WIDTH,
            corner_radius=th.R_LG,
            fg_color=th.BG_CARD,
            border_width=1,
            border_color=th.BORDER,
        )
        self.pack_propagate(False)

        self._time_clock_service = time_clock_service
        self._poll_after_id: str | None = None

        self._build()
        self.refresh()

    # ── Construcción ─────────────────────────────────────────────────────────

    def _build(self) -> None:
        # ── Cabecera ──
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(14, 10))

        # Punto verde de "en vivo"
        dot_container = ctk.CTkFrame(header, fg_color="transparent")
        dot_container.pack(side="left")

        live_dot = ctk.CTkFrame(
            dot_container,
            width=8,
            height=8,
            corner_radius=4,
            fg_color=th.SUCCESS,
        )
        live_dot.pack(side="left", padx=(0, 7), pady=2)
        live_dot.pack_propagate(False)

        ctk.CTkLabel(
            dot_container,
            text="Ahora fichados",
            font=th.bold(12),
            text_color=th.T_PRIMARY,
        ).pack(side="left")

        # Badge con el contador
        self._count_badge = ctk.CTkLabel(
            header,
            text="0",
            font=th.bold(10),
            text_color=th.ACCENT_SOFT,
            fg_color=th.ACCENT_DIM,
            corner_radius=9,
            width=22,
            height=18,
        )
        self._count_badge.pack(side="right")

        th.separator(self, padx=10)

        # ── Área de lista desplazable ──
        self._list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color=th.BORDER_LT,
            scrollbar_button_hover_color=th.BG_HOVER,
        )
        self._list_frame.pack(fill="both", expand=True, padx=4, pady=(6, 8))

    # ── Actualización pública ─────────────────────────────────────────────────

    def refresh(self) -> None:
        """Recarga la lista desde la BD y reprograma el siguiente sondeo."""
        if not self.winfo_exists():
            return

        try:
            statuses = self._time_clock_service.list_currently_clocked_in()
        except Exception:
            statuses = []

        self._redraw_list(statuses)
        self._schedule_poll()

    # ── Dibujo interno ────────────────────────────────────────────────────────

    def _redraw_list(self, statuses: list) -> None:
        for child in self._list_frame.winfo_children():
            child.destroy()

        count = len(statuses)
        self._count_badge.configure(text=str(count))

        if not count:
            self._build_empty_state()
            return

        for status in statuses:
            self._build_employee_card(status)

    def _build_empty_state(self) -> None:
        wrapper = ctk.CTkFrame(self._list_frame, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, pady=32, padx=8)

        ctk.CTkLabel(
            wrapper,
            text="—",
            font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"),
            text_color=th.T_DISABLED,
        ).pack(pady=(0, 6))

        ctk.CTkLabel(
            wrapper,
            text="No hay empleados\nfichados ahora mismo",
            font=th.f(11),
            text_color=th.T_MUTED,
            justify="center",
        ).pack()

    def _build_employee_card(self, status) -> None:
        employee = status.employee

        card = ctk.CTkFrame(
            self._list_frame,
            fg_color=th.BG_RAISED,
            corner_radius=th.R_MD,
            border_width=1,
            border_color=th.BORDER,
        )
        card.pack(fill="x", padx=4, pady=(0, 5))

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=10, pady=9)

        # ── Avatar circular con iniciales ──
        color = th.avatar_color(employee.id)
        avatar = ctk.CTkFrame(
            inner,
            width=36,
            height=36,
            corner_radius=18,
            fg_color=color,
        )
        avatar.pack(side="left", padx=(0, 9))
        avatar.pack_propagate(False)

        ctk.CTkLabel(
            avatar,
            text=employee.initials,
            font=th.bold(13),
            text_color="#FFFFFF",
        ).place(relx=0.5, rely=0.5, anchor="center")

        # ── Nombre y tiempo en turno ──
        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            info,
            text=employee.full_name,
            font=th.bold(12),
            text_color=th.T_PRIMARY,
            anchor="w",
            wraplength=110,
        ).pack(anchor="w")

        if status.active_session:
            elapsed_text = _format_elapsed(status.active_session.elapsed_seconds())
            ctk.CTkLabel(
                info,
                text=elapsed_text,
                font=th.f(10),
                text_color=th.T_MUTED,
                anchor="w",
            ).pack(anchor="w", pady=(1, 0))

        # ── Indicador de estado (punto verde a la derecha) ──
        status_dot = ctk.CTkFrame(
            inner,
            width=7,
            height=7,
            corner_radius=4,
            fg_color=th.SUCCESS,
        )
        status_dot.pack(side="right", padx=(6, 0))
        status_dot.pack_propagate(False)

    # ── Sondeo periódico ─────────────────────────────────────────────────────

    def _schedule_poll(self) -> None:
        self._cancel_poll()
        if self.winfo_exists():
            self._poll_after_id = self.after(POLL_INTERVAL_MS, self.refresh)

    def _cancel_poll(self) -> None:
        if self._poll_after_id:
            self.after_cancel(self._poll_after_id)
            self._poll_after_id = None

    def destroy(self) -> None:
        self._cancel_poll()
        super().destroy()
