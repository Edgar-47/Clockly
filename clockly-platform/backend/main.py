"""Backend entry point for ClockLy.

The repository root ``main.py`` remains as a compatibility wrapper. New
deployments can run this module directly from the backend directory.
"""

from pathlib import Path
import sys
import argparse
import os

import uvicorn


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    railway_port = os.getenv("PORT")
    default_host = "0.0.0.0" if railway_port else "127.0.0.1"
    default_port = int(railway_port or "8000")

    parser = argparse.ArgumentParser(description="ClockLy backend server")
    parser.add_argument("--host", default=default_host, help=f"Bind host (default: {default_host})")
    parser.add_argument("--port", type=int, default=default_port, help=f"Bind port (default: {default_port})")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for local development")
    args = parser.parse_args()

    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
