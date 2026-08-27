"""Installed/converted plugin model."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Plugin:
    name: str
    path: Path
    plugin_type: str  # "VST2" or "VST3"
