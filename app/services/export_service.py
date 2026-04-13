"""
ExportService — genera ficheros Excel a partir de attendance_sessions.

La fuente de verdad es attendance_sessions (no time_entries).
Cada fila del Excel representa una sesión completa con entrada, salida y
duración calculada. Las sesiones todavía abiertas se exportan indicando
que la salida está pendiente.
"""

from datetime import datetime
from pathlib import Path

from app.config import EXPORTS_DIR, ensure_runtime_directories
from app.database.attendance_session_repository import AttendanceSessionRepository
from app.services.attendance_report_service import AttendanceReportService
from app.utils.helpers import split_timestamp


def _fmt_duration(total_seconds: int | None, is_active: bool) -> str:
    """Format total_seconds as HH:MM or '—' for open sessions."""
    if is_active or total_seconds is None:
        return "En curso"
    hours, remainder = divmod(max(int(total_seconds), 0), 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours:02d}h {minutes:02d}m"


class ExportService:
    def __init__(
        self,
        attendance_session_repository: AttendanceSessionRepository | None = None,
        attendance_report_service: AttendanceReportService | None = None,
    ) -> None:
        self.attendance_session_repository = (
            attendance_session_repository or AttendanceSessionRepository()
        )
        self.attendance_report_service = (
            attendance_report_service
            or AttendanceReportService(self.attendance_session_repository)
        )

    def export_sessions_to_excel(
        self,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        user_id: int | None = None,
    ) -> Path:
        """
        Export attendance sessions to an Excel file in the exports/ folder.

        Parameters (all optional)
        -------------------------
        date_from   YYYY-MM-DD  Lower bound, inclusive (by clock_in_time)
        date_to     YYYY-MM-DD  Upper bound, inclusive (by clock_in_time)
        user_id                 Filter to a single user

        Returns
        -------
        Path to the generated .xlsx file.

        Columns
        -------
        ID · Empleado · DNI · Fecha · Entrada · Salida · Duración · Estado · Notas
        """
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Alignment, Font, PatternFill
        except ImportError as exc:
            raise RuntimeError(
                "Falta openpyxl. Instala dependencias con: pip install -r requirements.txt"
            ) from exc

        ensure_runtime_directories()

        reports = self.attendance_report_service.list_session_reports(
            date_from=date_from,
            date_to=date_to,
            user_id=user_id,
        )

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Sesiones"

        # ── Header ───────────────────────────────────────────────────────────
        headers = [
            "ID",
            "Empleado",
            "DNI",
            "Fecha",
            "Entrada",
            "Salida",
            "Duración",
            "Estado",
            "Incidencias",
            "Notas",
            "Nota salida",
            "Motivo cierre admin",
        ]
        sheet.append(headers)

        header_fill = PatternFill("solid", fgColor="1F538D")
        header_font = Font(color="FFFFFF", bold=True)
        for cell in sheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

        # ── Data rows ────────────────────────────────────────────────────────
        for row in reports:
            date_str, in_time = split_timestamp(row.clock_in_time)

            if row.clock_out_time:
                _, out_time = split_timestamp(row.clock_out_time)
            else:
                out_time = "—"

            duration = _fmt_duration(row.counted_duration_seconds, row.is_active)

            sheet.append(
                [
                    row.id,
                    row.employee_name,
                    row.dni,
                    date_str,
                    in_time,
                    out_time,
                    duration,
                    row.status_label,
                    row.incident_label,
                    row.notes or "",
                    row.exit_note or "",
                    row.manual_close_reason or "",
                ]
            )

        # ── Column widths ────────────────────────────────────────────────────
        min_widths = {
            "A": 6,   # ID
            "B": 24,  # Empleado
            "C": 14,  # DNI
            "D": 12,  # Fecha
            "E": 10,  # Entrada
            "F": 10,  # Salida
            "G": 12,  # Duración
            "H": 10,  # Estado
            "I": 24,  # Incidencias
            "J": 32,  # Notas
            "K": 32,  # Nota salida
            "L": 32,  # Motivo cierre admin
        }
        for col_letter, min_w in min_widths.items():
            col_cells = sheet[col_letter]
            max_len = max((len(str(c.value or "")) for c in col_cells), default=0)
            sheet.column_dimensions[col_letter].width = max(max_len + 2, min_w)

        # ── Save ─────────────────────────────────────────────────────────────
        filename = f"fichajes_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
        output_path = EXPORTS_DIR / filename
        workbook.save(output_path)
        return output_path

    # ── Backward-compatible alias ─────────────────────────────────────────────
    def export_time_entries_to_excel(
        self,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        employee_id: int | None = None,
    ) -> Path:
        """
        Alias kept for call sites that haven't been updated yet.
        Delegates to export_sessions_to_excel using attendance_sessions.
        """
        return self.export_sessions_to_excel(
            date_from=date_from,
            date_to=date_to,
            user_id=employee_id,
        )
