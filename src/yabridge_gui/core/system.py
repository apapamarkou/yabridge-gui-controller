"""System information helpers."""

from __future__ import annotations

import platform
import subprocess


def get_kernel() -> str:
    return platform.release()


def get_architecture() -> str:
    return platform.machine()


def get_hostname() -> str:
    return platform.node()


def enable_wireplumber() -> None:
    subprocess.run(
        ["systemctl", "--user", "--now", "enable", "wireplumber.service"],
        check=True,
        capture_output=True,
    )
