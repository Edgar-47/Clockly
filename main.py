"""
main.py — Clockly web application entry point.

Usage:
  python main.py              → starts the dev server on http://localhost:8000
  python main.py --port 9000  → custom port

Production:
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2

Notes:
  - The old desktop (Tkinter) entry point has been replaced by FastAPI.
  - Set CLOCKLY_SECRET_KEY in your environment before running in production.
  - Set FICHAJE_DATABASE_PATH to a path outside OneDrive to avoid SQLite lock issues.
"""

import argparse
import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Clockly web server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
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
