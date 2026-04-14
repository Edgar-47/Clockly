"""
main.py — Clockly web application entry point.

Usage:
  python main.py              → starts the dev server on http://localhost:8000
  python main.py --port 9000  → custom port

Production:
  uvicorn app.main:app --host 0.0.0.0 --port $PORT

Notes:
  - The old desktop (Tkinter) entry point has been replaced by FastAPI.
  - Set DATABASE_URL, CLOCKLY_SECRET_KEY, and CLOCKLY_DEFAULT_ADMIN_PASSWORD in production.
"""

import argparse
import os
import uvicorn


def main() -> None:
    railway_port = os.getenv("PORT")
    default_host = "0.0.0.0" if railway_port else "127.0.0.1"
    default_port = int(railway_port or "8000")

    parser = argparse.ArgumentParser(description="Clockly web server")
    parser.add_argument("--host", default=default_host, help=f"Bind host (default: {default_host})")
    parser.add_argument("--port", type=int, default=default_port, help=f"Bind port (default: {default_port})")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (dev only)")
    args = parser.parse_args()

    print(f"\n  Clockly running at  http://{args.host}:{args.port}")
    print(f"  Docs available at   http://{args.host}:{args.port}/docs\n")

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
