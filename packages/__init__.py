"""Application modules for configuration, display, and presentation."""

from __future__ import annotations

from .configuration import MazeConfig, load_config
from .presentation import (
    ANSI_RESET,
    Scene,
    Theme,
    THEMES,
    ansi_bg,
    ansi_fg,
    write_maze,
)

__all__ = [
    "ANSI_RESET",
    "MazeConfig",
    "Scene",
    "Theme",
    "THEMES",
    "MazeWindow",
    "ansi_bg",
    "ansi_fg",
    "load_config",
    "write_maze",
]


def __getattr__(name: str) -> object:
    if name == "MazeWindow":
        from .display import MazeWindow

        return MazeWindow
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
