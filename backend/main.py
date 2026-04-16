"""Backend entry point for ClockLy.

The repository root ``main.py`` remains as a compatibility wrapper. New
deployments can run this module directly from the backend directory.
"""

from pathlib import Path
import sys

import uvicorn


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
