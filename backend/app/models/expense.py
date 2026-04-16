"""
app/models/expense.py

Domain models for the employee expenses module.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.database.sql import normalize_datetime


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXPENSE_STATUS_PENDING = "pendiente"
EXPENSE_STATUS_APPROVED = "aprobado"
EXPENSE_STATUS_REIMBURSED = "reembolsado"
EXPENSE_STATUS_REJECTED = "rechazado"

EXPENSE_STATUSES = (
    EXPENSE_STATUS_PENDING,
    EXPENSE_STATUS_APPROVED,
    EXPENSE_STATUS_REIMBURSED,
    EXPENSE_STATUS_REJECTED,
)

EXPENSE_STATUS_LABELS: dict[str, str] = {
    EXPENSE_STATUS_PENDING: "Pendiente",
    EXPENSE_STATUS_APPROVED: "Aprobado",
    EXPENSE_STATUS_REIMBURSED: "Reembolsado",
    EXPENSE_STATUS_REJECTED: "Rechazado",
}

EXPENSE_STATUS_CSS: dict[str, str] = {
    EXPENSE_STATUS_PENDING: "badge--yellow",
    EXPENSE_STATUS_APPROVED: "badge--green",
    EXPENSE_STATUS_REIMBURSED: "badge--blue",
    EXPENSE_STATUS_REJECTED: "badge--red",
}

EXPENSE_CATEGORY_MATERIAL = "material"
EXPENSE_CATEGORY_TRANSPORT = "transporte"
EXPENSE_CATEGORY_FOOD = "comida"
EXPENSE_CATEGORY_SUPPLIES = "suministros"
EXPENSE_CATEGORY_OTHER = "otros"

EXPENSE_CATEGORIES = (
    EXPENSE_CATEGORY_MATERIAL,
    EXPENSE_CATEGORY_TRANSPORT,
    EXPENSE_CATEGORY_FOOD,
    EXPENSE_CATEGORY_SUPPLIES,
    EXPENSE_CATEGORY_OTHER,
)

EXPENSE_CATEGORY_LABELS: dict[str, str] = {
    EXPENSE_CATEGORY_MATERIAL: "Material",
    EXPENSE_CATEGORY_TRANSPORT: "Transporte",
    EXPENSE_CATEGORY_FOOD: "Comida",
    EXPENSE_CATEGORY_SUPPLIES: "Suministros",
    EXPENSE_CATEGORY_OTHER: "Otros",
}

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


# ---------------------------------------------------------------------------
# Expense model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Expense:
    id: int
    business_id: str
    user_id: int
    title: str
    amount: float
    expense_date: str
    status: str
    category: str
    description: str | None = None
    currency: str = "EUR"
    reference_number: str | None = None
    admin_notes: str | None = None
    reviewed_by: int | None = None
    reviewed_at: str | None = None
    reimbursed_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    # Joined fields (populated in enriched queries)
    employee_name: str | None = None
    reviewer_name: str | None = None

    @property
    def status_label(self) -> str:
        return EXPENSE_STATUS_LABELS.get(self.status, self.status)

    @property
    def status_css(self) -> str:
        return EXPENSE_STATUS_CSS.get(self.status, "badge--default")

    @property
    def category_label(self) -> str:
        return EXPENSE_CATEGORY_LABELS.get(self.category, self.category)

    @property
    def amount_display(self) -> str:
        return f"{self.amount:,.2f} {self.currency}"

    @classmethod
    def from_row(cls, row) -> "Expense":
        d = dict(row)
        return cls(
            id=int(d["id"]),
            business_id=d["business_id"],
            user_id=int(d["user_id"]),
            title=d["title"],
            amount=float(d["amount"]),
            expense_date=str(d["expense_date"]),
            status=d["status"],
            category=d.get("category") or EXPENSE_CATEGORY_OTHER,
            description=d.get("description"),
            currency=d.get("currency") or "EUR",
            reference_number=d.get("reference_number"),
            admin_notes=d.get("admin_notes"),
            reviewed_by=int(d["reviewed_by"]) if d.get("reviewed_by") else None,
            reviewed_at=normalize_datetime(d.get("reviewed_at")),
            reimbursed_at=normalize_datetime(d.get("reimbursed_at")),
            created_at=normalize_datetime(d.get("created_at")),
            updated_at=normalize_datetime(d.get("updated_at")),
            employee_name=d.get("employee_name"),
            reviewer_name=d.get("reviewer_name"),
        )


# ---------------------------------------------------------------------------
# ExpenseAttachment model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExpenseAttachment:
    id: int
    expense_id: int
    file_name: str
    file_path: str
    file_size: int | None = None
    mime_type: str | None = None
    created_at: str | None = None

    @property
    def size_display(self) -> str:
        if self.file_size is None:
            return ""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        if self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        return f"{self.file_size / (1024 * 1024):.1f} MB"

    @classmethod
    def from_row(cls, row) -> "ExpenseAttachment":
        d = dict(row)
        return cls(
            id=int(d["id"]),
            expense_id=int(d["expense_id"]),
            file_name=d["file_name"],
            file_path=d["file_path"],
            file_size=int(d["file_size"]) if d.get("file_size") else None,
            mime_type=d.get("mime_type"),
            created_at=normalize_datetime(d.get("created_at")),
        )
