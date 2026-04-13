from datetime import datetime
from pathlib import Path

from app.config import EXPORTS_DIR, ensure_runtime_directories
from app.database.time_entry_repository import TimeEntryRepository
from app.utils.helpers import label_for_entry_type, split_timestamp


class ExportService:
    def __init__(self, time_entry_repository: TimeEntryRepository | None = None) -> None:
        self.time_entry_repository = time_entry_repository or TimeEntryRepository()

    def export_time_entries_to_excel(
        self,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        employee_id: int | None = None,
    ) -> Path:
        """
        Export attendance records to an Excel file in the exports/ folder.

        Parameters (all optional)
        -------------------------
        date_from   YYYY-MM-DD  Lower bound, inclusive
        date_to     YYYY-MM-DD  Upper bound, inclusive
        employee_id             Filter to a single employee

        Returns
        -------
        Path to the generated .xlsx file.
        """
        try:
            from openpyxl import Workbook
            from openpyxl.styles import Alignment, Font, PatternFill
        except ImportError as exc:
            raise RuntimeError(
                "Falta openpyxl. Instala dependencias con: pip install -r requirements.txt"
            ) from exc

        ensure_runtime_directories()

        rows = self.time_entry_repository.list_with_employee_names(
            date_from=date_from,
            date_to=date_to,
            employee_id=employee_id,
        )

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Fichajes"

        # ── Header row ────────────────────────────────────────────────────────
        headers = ["ID", "Empleado", "Usuario", "Tipo", "Fecha", "Hora", "Observaciones"]
        sheet.append(headers)

        header_fill = PatternFill("solid", fgColor="1F538D")
        header_font = Font(color="FFFFFF", bold=True)
        for cell in sheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

        # ── Data rows ─────────────────────────────────────────────────────────
        for row in rows:
            date_str, time_str = split_timestamp(row["timestamp"])
            sheet.append(
                [
                    row["id"],
                    row["employee_name"],
                    row["username"],
                    label_for_entry_type(row["entry_type"]),
                    date_str,
                    time_str,
                    row["notes"] or "",
                ]
            )

        # ── Column widths ─────────────────────────────────────────────────────
        min_widths = {"A": 6, "B": 22, "C": 16, "D": 10, "E": 12, "F": 10, "G": 30}
        for col_letter, min_w in min_widths.items():
            col_cells = sheet[col_letter]
            max_len = max((len(str(c.value or "")) for c in col_cells), default=0)
            sheet.column_dimensions[col_letter].width = max(max_len + 2, min_w)

        # ── Save ──────────────────────────────────────────────────────────────
        filename = f"fichajes_{datetime.now():%Y%m%d_%H%M%S}.xlsx"
        output_path = EXPORTS_DIR / filename
        workbook.save(output_path)
        return output_path
