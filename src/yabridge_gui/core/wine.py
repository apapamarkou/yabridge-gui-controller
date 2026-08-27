"""Wine detection and version helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

WINE_VERSION = "9.21"
WINE_DIR = Path.home() / f".local/share/wine-staging-{WINE_VERSION}"
WINE_URL = f"https://github.com/Kron4ek/Wine-Builds/releases/download/{WINE_VERSION}/wine-{WINE_VERSION}-staging-amd64.tar.xz"


def get_wine_version() -> str | None:
    for cmd in ["wine", str(WINE_DIR / "bin/wine")]:
        try:
            r = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                return (r.stdout + r.stderr).strip().splitlines()[0]
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            continue
    return None


def wine_is_available() -> bool:
    return get_wine_version() is not None
