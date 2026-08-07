"""A-Maze-ing: generate a maze from a configuration file and display it.

Usage::

    python3 a_maze_ing.py config.txt

The configuration is validated before anything else runs, so the maze
generator only ever receives values it can work with. Every expected
failure surfaces as a single readable line rather than a traceback.
"""

from __future__ import annotations

import os
import random
import sys

from config import MazeConfig, load_config
from errors import AMazeIngError, RenderError
from view import Scene
from writer import write_maze

USAGE = "usage: python3 a_maze_ing.py config.txt"
SEED_LIMIT = 2 ** 31 - 1


def build_scene(config: MazeConfig, seed: int | None) -> Scene:
    """Generate a maze, write it to disk and wrap it for display.

    Args:
        config: The validated configuration.
        seed: Seed for this particular maze, or None for a random one.

    Returns:
        A drawable snapshot of the generated maze.

    Raises:
        AMazeIngError: The generator is missing, or produced no path.
    """
    try:
        from packages.mazegen import MazeGenerator
    except ImportError as error:
        raise AMazeIngError(
            f"cannot import the mazegen package ({error}); run "
            f"'make install' first."
        ) from None

    maze = MazeGenerator(
        width=config.width,
        height=config.height,
        entry=config.entry,
        exit=config.exit,
        perfect=config.perfect,
        seed=seed,
    )
    maze.generate()

    # MazeGenerator.solve() writes to the file named by OUTPUT_FILE and
    # raises TypeError when that variable is unset. Pointing it at our
    # own output path keeps it happy; write_maze() then overwrites the
    # file with the complete, correctly formatted contents.
    os.environ["OUTPUT_FILE"] = config.output_file
    path = maze.solve()
    if not path:
        raise AMazeIngError(
            f"no path exists between entry {config.entry} and exit "
            f"{config.exit}."
        )

    write_maze(config, maze.grid, MazeGenerator.coords_to_letters(path))
    if not maze.pattern_applied:
        print(
            "Note: the maze is too small to hold the '42' pattern, "
            "so it was omitted.",
            file=sys.stderr,
        )
    return Scene(
        width=config.width,
        height=config.height,
        grid=maze.grid,
        entry=config.entry,
        exit=config.exit,
        path=frozenset(path),
        pattern=maze.pattern_cells,
        perfect=config.perfect,
    )


def display(config: MazeConfig, scene: Scene) -> None:
    """Show *scene*, preferring MiniLibX and falling back to the terminal.

    Args:
        config: The validated configuration, used when regenerating.
        scene: The maze to display.
    """
    def regenerate() -> Scene:
        """Build a brand new maze with a fresh random seed."""
        return build_scene(config, random.randrange(SEED_LIMIT))

    try:
        from render_mlx import MazeWindow

        MazeWindow(scene, regenerate, "A-Maze-ing").run()
    except RenderError as error:
        print(f"Graphical display unavailable: {error}", file=sys.stderr)
        print("Falling back to the terminal.\n", file=sys.stderr)
        import render_ascii

        render_ascii.run(scene, regenerate)


def main(argv: list[str]) -> int:
    """Run the program and return the process exit code.

    Args:
        argv: Command-line arguments, without the program name.

    Returns:
        0 on success, 1 on any expected failure.
    """
    if len(argv) != 1:
        print(USAGE, file=sys.stderr)
        return 1
    try:
        config = load_config(argv[0])
        scene = build_scene(config, config.seed)
        print(
            f"Maze {config.width}x{config.height} written to "
            f"{config.output_file}."
        )
        display(config, scene)
    except AMazeIngError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        print()
        sys.exit(130)
