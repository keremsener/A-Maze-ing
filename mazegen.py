from dataclasses import dataclass
from random import Random

# ---- GLOBAL VARIABLES ----
NORTH = 1
EAST = 2
SOUTH = 4
WEST = 8
ALL_WALLS = NORTH | EAST | SOUTH | WEST
OPPOSITE = {NORTH: SOUTH, SOUTH: NORTH, EAST: WEST, WEST: EAST}
STEP = {NORTH: (0, -1), EAST: (1, 0), SOUTH: (0, 1), WEST: (-1, 0)}


class MazeError(Exception):
    """Maze configuration errors."""
    pass


class MazeGenerator:
    def __init__(
        self,
        width: int,
        height: int,
        entry: tuple[int, int],
        exit: tuple[int, int],
        perfect: bool = True,
        seed: int | None = None,
    ):
        self.width = width
        self.height = height
        self.entry = entry
        self.exit = exit
        self.perfect = perfect
        self.seed = seed
        self.random = Random(seed)
        self._validate()
        self.grid = [[ALL_WALLS] * self.width for _ in range(self.height)]

    def _validate(self) -> None:
        if self.width < 2 or self.height < 2:
            raise MazeError(
                f"Maze size must be at least 2x2 (got {self.width}x{self.height})."
            )

        if self.entry == self.exit:
            raise MazeError("Entry and exit cannot be the same point.")
        self._validate_point(self.entry, "Entry")
        self._validate_point(self.exit, "Exit")

    def _validate_point(self, point: tuple[int, int], name: str) -> None:
        if not (0 <= point[0] < self.width):
            raise MazeError(
                f"{name} x-coordinate ({point[0]}) is outside the maze."
            )

        if not (0 <= point[1] < self.height):
            raise MazeError(
                f"{name} y-coordinate ({point[1]}) is outside the maze."
            )

    def _in_bounds(self, x: int, y: int) -> bool:
        if (x >= 0 and x <= self.width) and (y >= 0 and x <= self.height):
            return True
        return False


if __name__ == "__main__":
    maze = MazeGenerator(
        width=4,
        height=4,
        entry=(0, 0),
        exit=(3, 3),
        perfect=True,
        seed=42,
    )

    print("Maze created successfully!")
