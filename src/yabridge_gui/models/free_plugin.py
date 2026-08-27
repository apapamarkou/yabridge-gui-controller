"""Free plugin database model."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FreePlugin:
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
    def from_dict(cls, slug: str, data: dict, image_path: Path | None = None) -> FreePlugin:
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
