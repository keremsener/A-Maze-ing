"""Writing a generated maze to disk in the subject's output format.

The file holds one hexadecimal digit per cell, row by row, where a set bit
marks a *closed* wall: bit 0 = North, 1 = East, 2 = South, 3 = West. After
a blank line come three footer lines: the entry, the exit and the shortest
path spelled with the letters N, E, S and W.

Coordinates are written as ``x,y`` with no trailing comment, which is what
``maze_analyzer.py`` expects: it splits the line on the comma and calls
``int()`` on both halves, so anything else on the line makes it give up.
"""

from __future__ import annotations

from typing import Sequence

from config import MazeConfig
from errors import OutputError

Grid = Sequence[Sequence[int]]


def format_maze(
    grid: Grid,
    entry: tuple[int, int],
    exit_: tuple[int, int],
    path_letters: str,
) -> str:
    """Render a maze as the full text of the output file.

    Args:
        grid: Wall bitmasks indexed as ``grid[y][x]``.
        entry: Entry cell as ``(x, y)``.
        exit_: Exit cell as ``(x, y)``.
        path_letters: Shortest path spelled with N, E, S and W.

    Returns:
        The complete file contents, ending with a newline.

    Raises:
        OutputError: A cell does not fit in a single hexadecimal digit.
    """
    lines: list[str] = []
    for y, row in enumerate(grid):
        digits: list[str] = []
        for x, cell in enumerate(row):
            if not 0 <= cell <= 15:
                raise OutputError(
                    f"cell ({x}, {y}) holds {cell}, which does not fit "
                    f"in one hexadecimal digit (expected 0..15)."
                )
            digits.append(f"{cell:x}")
        lines.append("".join(digits))
    lines.append("")
    lines.append(f"{entry[0]},{entry[1]}")
    lines.append(f"{exit_[0]},{exit_[1]}")
    lines.append(path_letters)
    return "\n".join(lines) + "\n"


def write_maze(
    config: MazeConfig,
    grid: Grid,
    path_letters: str,
) -> None:
    """Write the maze described by *config* and *grid* to disk.

    Args:
        config: The validated configuration, used for the output path
            and for the entry and exit coordinates.
        grid: Wall bitmasks indexed as ``grid[y][x]``.
        path_letters: Shortest path spelled with N, E, S and W.

    Raises:
        OutputError: The file cannot be written, or the grid is invalid.
    """
    text = format_maze(grid, config.entry, config.exit, path_letters)
    try:
        with open(config.output_file, "w", encoding="utf-8") as stream:
            stream.write(text)
    except IsADirectoryError:
        raise OutputError(
            f"{config.output_file} is a directory, not a file."
        ) from None
    except PermissionError:
        raise OutputError(
            f"no permission to write {config.output_file}."
        ) from None
    except OSError as error:
        raise OutputError(
            f"cannot write {config.output_file}: {error}"
        ) from None
