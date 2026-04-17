from __future__ import annotations

import argparse
import getpass
import sys

from app.database.schema import initialize_database
from app.services.superadmin_bootstrap_service import SuperadminBootstrapService


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Provisiona acceso Superadmin sin usar el login normal.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="Crea o actualiza el propietario Superadmin.")
    create.add_argument("--email", required=True, help="Email interno del Superadmin.")
    create.add_argument("--name", required=True, help="Nombre completo.")
    create.add_argument(
        "--password",
        help="Contrasena temporal. Si se omite, se pedira por terminal.",
    )
    create.add_argument(
        "--force-change",
        action="store_true",
        help="Marca la cuenta para cambio de contrasena futuro.",
    )

    args = parser.parse_args(argv)
    if args.command == "create":
        password = args.password or getpass.getpass("Contrasena Superadmin: ")
        if not args.password:
            confirmation = getpass.getpass("Repite la contrasena: ")
            if password != confirmation:
                print("Las contrasenas no coinciden.", file=sys.stderr)
                return 2

        initialize_database()
        result = SuperadminBootstrapService().create_or_update_superadmin(
            email=args.email,
            full_name=args.name,
            password=password,
            force_password_change=args.force_change,
        )
        action = "creado" if result.created else "actualizado"
        print(f"Superadmin {action}: {result.email} (id={result.user_id})")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())

