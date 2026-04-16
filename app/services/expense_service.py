"""
app/services/expense_service.py

Business logic for the employee expenses module.

Responsibilities:
- Validate expense fields and amounts.
- Enforce role-based access: employees see only their own expenses.
- Save uploaded ticket images safely (unique names, type + size checks).
- Control status transitions (only admin can approve/reject/reimburse).
"""
from __future__ import annotations

import os
import uuid
from datetime import date, datetime
from pathlib import Path

from app.database.expense_repository import ExpenseRepository
from app.models.expense import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    EXPENSE_CATEGORIES,
    EXPENSE_STATUS_APPROVED,
    EXPENSE_STATUS_PENDING,
    EXPENSE_STATUS_REIMBURSED,
    EXPENSE_STATUS_REJECTED,
    EXPENSE_STATUSES,
    MAX_FILE_SIZE_BYTES,
    Expense,
    ExpenseAttachment,
)

# Upload root — resolved relative to project root at service instantiation time.
_UPLOADS_ROOT = Path("uploads") / "tickets"


class ExpensePermissionError(Exception):
    """Raised when a user attempts an action they are not authorised for."""


class ExpenseValidationError(Exception):
    """Raised when submitted expense data fails validation."""


class ExpenseService:
    def __init__(
        self,
        *,
        business_id: str | None = None,
        uploads_root: Path | None = None,
    ) -> None:
        self.business_id = business_id
        self.repo = ExpenseRepository(business_id=business_id)
        self._uploads_root = uploads_root or _UPLOADS_ROOT

    # ------------------------------------------------------------------
    # Employee-facing operations
    # ------------------------------------------------------------------

    def create_expense(
        self,
        *,
        user_id: int,
        title: str,
        amount_raw: str,
        expense_date_raw: str,
        description: str | None = None,
        category: str = "otros",
        currency: str = "EUR",
        reference_number: str | None = None,
    ) -> int:
        title = title.strip()
        description = (description or "").strip() or None
        reference_number = (reference_number or "").strip() or None
        category = (category or "otros").strip().lower()
        currency = (currency or "EUR").strip().upper()

        if not title:
            raise ExpenseValidationError("El concepto del gasto es obligatorio.")

        try:
            amount = float(amount_raw.replace(",", ".").strip())
        except (ValueError, AttributeError) as exc:
            raise ExpenseValidationError("El importe debe ser un número válido.") from exc

        if amount <= 0:
            raise ExpenseValidationError("El importe debe ser mayor que 0.")

        if amount > 99_999.99:
            raise ExpenseValidationError("El importe no puede superar 99.999,99 €.")

        try:
            date.fromisoformat(expense_date_raw.strip())
            expense_date = expense_date_raw.strip()
        except (ValueError, AttributeError) as exc:
            raise ExpenseValidationError("La fecha del gasto no es válida (AAAA-MM-DD).") from exc

        if category not in EXPENSE_CATEGORIES:
            category = "otros"

        if currency not in {"EUR", "USD", "GBP"}:
            currency = "EUR"

        return self.repo.create(
            user_id=user_id,
            title=title,
            amount=amount,
            expense_date=expense_date,
            description=description,
            category=category,
            currency=currency,
            reference_number=reference_number,
        )

    def get_my_expense(self, expense_id: int, user_id: int) -> Expense:
        """Return an expense only if it belongs to user_id."""
        expense = self.repo.get_by_id(expense_id)
        if expense is None:
            raise ExpensePermissionError("Gasto no encontrado.")
        if expense.user_id != user_id:
            raise ExpensePermissionError("No tienes acceso a este gasto.")
        return expense

    def list_my_expenses(
        self,
        user_id: int,
        *,
        status: str | None = None,
    ) -> list[Expense]:
        return self.repo.list_by_user(user_id, status=status)

    def get_my_total(self, user_id: int) -> float:
        return self.repo.total_by_user(user_id)

    # ------------------------------------------------------------------
    # Admin-facing operations
    # ------------------------------------------------------------------

    def get_expense_for_admin(self, expense_id: int) -> Expense:
        expense = self.repo.get_by_id(expense_id)
        if expense is None:
            raise ExpensePermissionError("Gasto no encontrado.")
        return expense

    def list_all_expenses(
        self,
        *,
        status: str | None = None,
        user_id: int | None = None,
        search: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        amount_min: float | None = None,
        amount_max: float | None = None,
    ) -> list[Expense]:
        return self.repo.list_all(
            status=status,
            user_id=user_id,
            search=search,
            date_from=date_from,
            date_to=date_to,
            amount_min=amount_min,
            amount_max=amount_max,
        )

    def review_expense(
        self,
        expense_id: int,
        *,
        new_status: str,
        reviewer_id: int,
        admin_notes: str | None = None,
    ) -> None:
        if new_status not in {EXPENSE_STATUS_APPROVED, EXPENSE_STATUS_REJECTED, EXPENSE_STATUS_REIMBURSED}:
            raise ExpenseValidationError(f"Estado '{new_status}' no es válido para revisión.")

        expense = self.repo.get_by_id(expense_id)
        if expense is None:
            raise ExpensePermissionError("Gasto no encontrado.")

        if expense.status == EXPENSE_STATUS_REIMBURSED:
            raise ExpenseValidationError("Un gasto ya reembolsado no puede ser modificado.")

        reimbursed_at = None
        if new_status == EXPENSE_STATUS_REIMBURSED:
            reimbursed_at = datetime.utcnow().isoformat()

        self.repo.update_status(
            expense_id,
            status=new_status,
            reviewed_by=reviewer_id,
            admin_notes=(admin_notes or "").strip() or expense.admin_notes,
            reimbursed_at=reimbursed_at,
        )

    def update_admin_notes(
        self,
        expense_id: int,
        admin_notes: str | None,
    ) -> None:
        self.repo.update_admin_notes(expense_id, admin_notes)

    def get_summary(self) -> dict:
        counts = self.repo.count_by_status()
        total_pending = self.repo.total_amount_by_status(EXPENSE_STATUS_PENDING)
        total_approved = self.repo.total_amount_by_status(EXPENSE_STATUS_APPROVED)
        total_reimbursed = self.repo.total_amount_by_status(EXPENSE_STATUS_REIMBURSED)
        total_rejected = self.repo.total_amount_by_status(EXPENSE_STATUS_REJECTED)
        return {
            "count_pending": counts.get(EXPENSE_STATUS_PENDING, 0),
            "count_approved": counts.get(EXPENSE_STATUS_APPROVED, 0),
            "count_reimbursed": counts.get(EXPENSE_STATUS_REIMBURSED, 0),
            "count_rejected": counts.get(EXPENSE_STATUS_REJECTED, 0),
            "total_pending": total_pending,
            "total_approved": total_approved,
            "total_reimbursed": total_reimbursed,
            "total_rejected": total_rejected,
        }

    # ------------------------------------------------------------------
    # Attachment / file operations
    # ------------------------------------------------------------------

    def save_attachment(
        self,
        expense_id: int,
        *,
        file_bytes: bytes,
        original_filename: str,
        content_type: str | None = None,
    ) -> ExpenseAttachment:
        """
        Persist an uploaded ticket image to disk and record it in the DB.

        Steps:
          1. Validate extension and MIME type.
          2. Check file size.
          3. Build a safe unique path under uploads/tickets/{business_id}/{YYYY}/{MM}/
          4. Write to disk.
          5. Insert attachment row.
        """
        if not file_bytes:
            raise ExpenseValidationError("El archivo está vacío.")

        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise ExpenseValidationError(
                f"El archivo supera el tamaño máximo de {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
            )

        suffix = Path(original_filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise ExpenseValidationError(
                "Tipo de archivo no permitido. Usa JPG, PNG o WEBP."
            )

        # Accept both explicit content_type and derive from extension.
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }
        mime_type = content_type or mime_map.get(suffix, "application/octet-stream")
        if mime_type not in ALLOWED_MIME_TYPES and mime_type != "application/octet-stream":
            raise ExpenseValidationError("Tipo MIME no permitido.")

        # Build storage path: uploads/tickets/<business_id>/<YYYY>/<MM>/<uuid><ext>
        now = datetime.utcnow()
        bucket = (
            self._uploads_root
            / (self.business_id or "shared")
            / str(now.year)
            / f"{now.month:02d}"
        )
        bucket.mkdir(parents=True, exist_ok=True)

        unique_name = f"{uuid.uuid4().hex}{suffix}"
        file_path = bucket / unique_name

        file_path.write_bytes(file_bytes)

        # Store path relative to project root so it's portable.
        relative_path = str(file_path.as_posix())

        attachment_id = self.repo.add_attachment(
            expense_id=expense_id,
            file_name=original_filename,
            file_path=relative_path,
            file_size=len(file_bytes),
            mime_type=mime_type,
        )

        return ExpenseAttachment(
            id=attachment_id,
            expense_id=expense_id,
            file_name=original_filename,
            file_path=relative_path,
            file_size=len(file_bytes),
            mime_type=mime_type,
        )

    def get_attachments(self, expense_id: int) -> list[ExpenseAttachment]:
        return self.repo.get_attachments(expense_id)

    def delete_expense(self, expense_id: int, *, user_id: int, is_admin: bool) -> None:
        """
        Delete an expense and its attachments from disk.
        Only the owner or an admin can delete; and only if status is pending.
        """
        expense = self.repo.get_by_id(expense_id)
        if expense is None:
            raise ExpensePermissionError("Gasto no encontrado.")

        if not is_admin and expense.user_id != user_id:
            raise ExpensePermissionError("No tienes permiso para eliminar este gasto.")

        if not is_admin and expense.status != EXPENSE_STATUS_PENDING:
            raise ExpenseValidationError(
                "Solo puedes eliminar gastos que aún están en estado pendiente."
            )

        # Remove attachment files from disk
        attachments = self.repo.get_attachments(expense_id)
        for att in attachments:
            try:
                Path(att.file_path).unlink(missing_ok=True)
            except OSError:
                pass  # Non-critical: leave orphan file rather than crashing

        self.repo.delete(expense_id)
