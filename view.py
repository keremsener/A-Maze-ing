"""Colour themes and the drawable snapshot of a maze.

Both renderers -- the terminal one and the MiniLibX one -- draw the same
:class:`Scene` with the same :class:`Theme`, so switching colours or
toggling the solution path behaves identically in either display.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Sequence

Grid = Sequence[Sequence[int]]


@dataclass(frozen=True)
class Theme:
    """One colour scheme, in both 24-bit RGB and ANSI terminal form.

    Attributes:
        name: Label shown in the status bar.
        wall: Wall colour as 0xRRGGBB.
        floor: Corridor colour as 0xRRGGBB.
        pattern: Colour of the fully closed "42" cells.
        path: Colour of the shortest path.
        entry: Colour of the entry cell.
        exit: Colour of the exit cell.
    """

    name: str
    wall: int
    floor: int
    pattern: int
    path: int
    entry: int
    exit: int


THEMES: Final[tuple[Theme, ...]] = (
    Theme("classic", 0xC8C8D0, 0x14141C, 0xE8E8F0, 0x35D6E8,
          0xE452C8, 0xE8433F),
    Theme("amber", 0xE8A020, 0x1A1408, 0xF5E0B0, 0xFFD966,
          0xE452C8, 0xE8433F),
    Theme("matrix", 0x37D45A, 0x081008, 0xAEF5BC, 0xE8E8F0,
          0xE452C8, 0xE8433F),
    Theme("ice", 0x6AA8E8, 0x0A1420, 0xD6E8FA, 0xFFFFFF,
          0xE452C8, 0xE8433F),
)

ANSI_RESET: Final[str] = "\033[0m"


def ansi_bg(colour: int) -> str:
    """Return the ANSI escape that sets *colour* as the background."""
    return f"\033[48;2;{colour >> 16 & 255};{colour >> 8 & 255};" \
           f"{colour & 255}m"


@dataclass(frozen=True)
class Scene:
    """Everything a renderer needs in order to draw one maze.

    Attributes:
        width: Number of cells per row.
        height: Number of rows.
        grid: Wall bitmasks indexed as ``grid[y][x]``.
        entry: Entry cell as ``(x, y)``.
        exit: Exit cell as ``(x, y)``.
        path: Cells on the shortest path, entry and exit included.
        pattern: Cells that draw the "42", or an empty set.
        perfect: True when the maze was generated in PERFECT mode.
    """

    width: int
    height: int
    grid: Grid
    entry: tuple[int, int]
    exit: tuple[int, int]
    path: frozenset[tuple[int, int]]
    pattern: frozenset[tuple[int, int]]
    perfect: bool

    def cell_colour(
        self, x: int, y: int, theme: Theme, show_path: bool
    ) -> int:
        """Return the fill colour of the cell at ``(x, y)``.

        Args:
            x: Column index.
            y: Row index.
            theme: The active colour scheme.
            show_path: Whether the solution path is visible.

        Returns:
            The colour as 0xRRGGBB.
        """
        if (x, y) == self.entry:
            return theme.entry
        if (x, y) == self.exit:
            return theme.exit
        if (x, y) in self.pattern:
            return theme.pattern
        if show_path and (x, y) in self.path:
            return theme.path
        return theme.floor


def ansi_fg(colour: int) -> str:
    """Return the ANSI escape that sets *colour* as the foreground."""
    return f"\033[38;2;{colour >> 16 & 255};{colour >> 8 & 255};" \
           f"{colour & 255}m"
