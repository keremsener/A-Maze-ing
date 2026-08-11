"""Terminal fallback display, used when MiniLibX cannot open a window.

Two details make the terminal picture readable, and both differ from the
graphical display on purpose.

Walls and corridors occupy the same single cell on a character grid, so a
bright wall colour would swamp the drawing. The roles are therefore
swapped here: walls are painted in the dark colour and corridors carry the
theme's accent, which is how a maze is normally printed on a terminal.

Rows are packed two at a time into one line of upper-half blocks, the
foreground giving the upper row and the background the lower one. That
halves the height and brings the picture back to roughly square, since a
character cell is about twice as tall as it is wide.
"""

from __future__ import annotations

from typing import Callable

from packages.presentation.view import (
    ANSI_RESET,
    Scene,
    Theme,
    THEMES,
    ansi_bg,
    ansi_fg,
)

HALF_BLOCK = "\u2580"

EAST = 2
SOUTH = 4


def corridor_colour(
    scene: Scene, x: int, y: int, theme: Theme, show_path: bool
) -> int:
    """Return the colour of the corridor at ``(x, y)``.

    Args:
        scene: The maze being drawn.
        x: Column index.
        y: Row index.
        theme: The active colour scheme.
        show_path: Whether the solution path is highlighted.

    Returns:
        The colour as 0xRRGGBB.
    """
    if (x, y) == scene.entry:
        return theme.entry
    if (x, y) == scene.exit:
        return theme.exit
    if (x, y) in scene.pattern:
        return theme.pattern
    if show_path and (x, y) in scene.path:
        return theme.path
    return theme.wall


def build_canvas(
    scene: Scene, theme: Theme, show_path: bool
) -> list[list[int]]:
    """Return a colour grid twice as fine as the cell grid.

    Odd rows and columns hold cells, even ones hold the walls between
    them. Neighbouring "42" cells are joined through the wall that
    separates them, so the digits read as shapes instead of dots.

    Args:
        scene: The maze to draw.
        theme: The active colour scheme.
        show_path: Whether the solution path is highlighted.

    Returns:
        A ``(2 * height + 1)`` by ``(2 * width + 1)`` grid of colours.
    """
    columns = scene.width * 2 + 1
    rows = scene.height * 2 + 1
    canvas = [[theme.floor] * columns for _ in range(rows)]
    for y in range(scene.height):
        for x in range(scene.width):
            colour = corridor_colour(scene, x, y, theme, show_path)
            canvas[y * 2 + 1][x * 2 + 1] = colour
            if (x, y) in scene.pattern:
                if (x + 1, y) in scene.pattern:
                    canvas[y * 2 + 1][x * 2 + 2] = theme.pattern
                if (x, y + 1) in scene.pattern:
                    canvas[y * 2 + 2][x * 2 + 1] = theme.pattern
                continue
            walls = scene.grid[y][x]
            if not walls & EAST and x + 1 < scene.width:
                canvas[y * 2 + 1][x * 2 + 2] = colour
            if not walls & SOUTH and y + 1 < scene.height:
                canvas[y * 2 + 2][x * 2 + 1] = colour
    return canvas


def draw(scene: Scene, theme: Theme, show_path: bool) -> str:
    """Return the maze as a block of ANSI-coloured text.

    Args:
        scene: The maze to draw.
        theme: The active colour scheme.
        show_path: Whether the solution path is highlighted.

    Returns:
        The rendered maze, two canvas rows per terminal line.
    """
    canvas = build_canvas(scene, theme, show_path)
    filler = [theme.floor] * len(canvas[0])
    lines = []
    for index in range(0, len(canvas), 2):
        upper = canvas[index]
        lower = canvas[index + 1] if index + 1 < len(canvas) else filler
        line = "".join(
            f"{ansi_fg(top)}{ansi_bg(bottom)}{HALF_BLOCK}"
            for top, bottom in zip(upper, lower)
        )
        lines.append(line + ANSI_RESET)
    return "\n".join(lines)


def run(scene: Scene, regenerate: Callable[[], Scene]) -> None:
    """Show the maze and loop on the interaction menu.

    Args:
        scene: The maze to display.
        regenerate: Callable returning a freshly generated scene.
    """
    show_path = True
    theme_index = 0
    while True:
        theme = THEMES[theme_index % len(THEMES)]
        mode = "perfect" if scene.perfect else "pac-man"
        state = "shown" if show_path else "hidden"
        print(draw(scene, theme, show_path))
        print(f"\n=== A-Maze-ing ({mode}) ===")
        print("1. Re-generate a new maze")
        print(f"2. Show / hide the shortest path  [{state}]")
        print(f"3. Rotate the wall colours        [{theme.name}]")
        print("4. Quit")
        try:
            choice = input("Choice? (1-4): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if choice == "1":
            scene = regenerate()
        elif choice == "2":
            show_path = not show_path
        elif choice == "3":
            theme_index += 1
        elif choice == "4":
            return
        else:
            print("Please enter a number between 1 and 4.")
