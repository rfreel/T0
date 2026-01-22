"""Verifier for Ralph loop tracer-bullet."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent
    result = subprocess.run(
        [sys.executable, str(root / "main.py")],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0 or result.stdout != "OK\n":
        return 1

    print("verify: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
