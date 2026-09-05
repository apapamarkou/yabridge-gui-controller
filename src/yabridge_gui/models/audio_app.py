# __   __    _          _     _               ____ _   _ ___
# \ \ / /_ _| |__  _ __(_) __| | __ _  ___   / ___| | | |_ _|
#  \ V / _` | '_ \| '__| |/ _` |/ _` |/ _ \ | |  _| | | || |
#   | | (_| | |_) | |  | | (_| | (_| |  __/ | |_| | |_| || |
#   |_|\__,_|_.__/|_|  |_|\__,_|\__, |\___|  \____|\___/|___|
#                               |___/
#   ____            _             _ _
#  / ___|___  _ __ | |_ _ __ ___ | | | ___ _ __
# | |   / _ \| '_ \| __| '__/ _ \| | |/ _ \ '__|
# | |__| (_) | | | | |_| | | (_) | | |  __/ |
#  \____\___/|_| |_|\__|_|  \___/|_|_|\___|_|
#
# Author: Andrianos Papamarkou
# Licence: GPL3
# https://github.com/apapamarkou/yabridge-gui-controller

"""Audio app database model."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AudioApp:
    slug: str
    name: str
    developer: str
    description: str
    category: str
    website: str
    download: str
    formats: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)
    free: bool = True
    image_path: Path | None = None

    @classmethod
    def from_dict(cls, slug: str, data: dict, image_path: Path | None = None) -> AudioApp:
        return cls(
            slug=slug,
            name=data.get("name", slug),
            developer=data.get("developer", ""),
            description=data.get("description", ""),
            category=data.get("category", ""),
            website=data.get("website", ""),
            download=data.get("download", ""),
            formats=data.get("formats", []),
            platforms=data.get("platforms", []),
            free=data.get("free", True),
            image_path=image_path,
        )
