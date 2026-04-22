from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company


class CompanyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, company_id: UUID) -> Company | None:
        return self.db.scalar(
            select(Company).where(
                Company.id == company_id,
                Company.is_active.is_(True),
            )
        )

    def get_by_slug(self, slug: str) -> Company | None:
        return self.db.scalar(select(Company).where(Company.slug == slug))

    def add(self, company: Company) -> Company:
        self.db.add(company)
        self.db.flush()
        return company

