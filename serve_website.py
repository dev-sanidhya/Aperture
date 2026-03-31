from __future__ import annotations

import subprocess
import sys
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PYTHON = ROOT / "backend" / ".venv" / "Scripts" / "python.exe"
WEBSITE_DIR = ROOT / "website"
PORT = 4173
URL = f"http://127.0.0.1:{PORT}"


def site_is_up() -> bool:
    try:
        with urllib.request.urlopen(URL, timeout=1) as response:
            return response.status == 200
    except Exception:
        return False


def main() -> int:
    if site_is_up():
        print(URL)
        return 0

    creationflags = 0
    if sys.platform.startswith("win"):
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

    subprocess.Popen(
        [str(PYTHON), "-m", "http.server", str(PORT), "--directory", str(WEBSITE_DIR)],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags,
        close_fds=True,
    )

    for _ in range(20):
      time.sleep(0.5)
      if site_is_up():
        print(URL)
        return 0

    print("Failed to start website server.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
