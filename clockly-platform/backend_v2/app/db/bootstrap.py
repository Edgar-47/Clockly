import argparse
import re

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.company import Company
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.company_repository import CompanyRepository
from app.repositories.user_repository import UserRepository


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "company"


def seed_owner(
    db: Session,
    *,
    company_name: str,
    email: str,
    password: str,
    business_type: str | None = None,
    timezone: str = "Europe/Madrid",
) -> tuple[Company, User]:
    users = UserRepository(db)
    existing = users.get_by_email(email.lower())
    if existing:
        company = CompanyRepository(db).get(existing.company_id)
        if company is None:
            raise RuntimeError("Existing user is linked to an inactive or missing company.")
        return company, existing

    base_slug = slugify(company_name)
    slug = base_slug
    companies = CompanyRepository(db)
    suffix = 2
    while companies.get_by_slug(slug):
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    company = companies.add(
        Company(
            name=company_name,
            slug=slug,
            business_type=business_type,
            timezone=timezone,
        )
    )
    user = users.add(
        User(
            company_id=company.id,
            email=email.lower(),
            full_name="Owner",
            password_hash=hash_password(password),
            role=UserRole.OWNER,
        )
    )
    db.commit()
    return company, user


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed an initial ClockLy company owner.")
    parser.add_argument("--company-name", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--business-type", default=None)
    parser.add_argument("--timezone", default="Europe/Madrid")
    args = parser.parse_args()

    with SessionLocal() as db:
        company, user = seed_owner(
            db,
            company_name=args.company_name,
            email=args.email,
            password=args.password,
            business_type=args.business_type,
            timezone=args.timezone,
        )
    print(f"Seed ready: company={company.slug} owner={user.email}")


if __name__ == "__main__":
    main()

