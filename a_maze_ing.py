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

# ---- "42" PATTERN CONSTANTS ----
PATTERN_HEIGHT = 5
PATTERN_WIDTH = 7

MIN_MAP_HEIGHT = 7
MIN_MAP_WIDTH = 9

FOUR_PATTERN = (
    "..X",
    "X.X",
    "XXX",
    "..X",
    "..X",
)

TWO_PATTERN = (
    "XXX",
    "..X",
    "XXX",
    "X..",
    "XXX",
)


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
        return 0 <= x < self.width and 0 <= y < self.height

    def _neighbour(self, x: int, y: int, direction: int) -> tuple[int, int]:
        dx, dy = STEP[direction]
        return x + dx, y + dy

    def _open_wall(self, x: int, y: int, direction: int):
        # The new neighbor's coordinates are return
        nx, ny = self._neighbour(x, y, direction)
        if not self._in_bounds(nx, ny):
            raise MazeError("Cannot go outside the map")
        # Don't change the cell value; just clear the specified direction bit.
        self.grid[y][x] &= ~direction
        self.grid[ny][nx] &= ~OPPOSITE[direction]

    def _close_wall(self, x: int, y: int, direction: int):
        # The new neighbor's coordinates are return
        nx, ny = self._neighbour(x, y, direction)
        if not self._in_bounds(nx, ny):
            raise MazeError("Cannot go outside the map")
        # Don't change the cell value; just clear the specified direction bit.
        self.grid[y][x] |= direction
        self.grid[ny][nx] |= OPPOSITE[direction]

    @property
    def pattern_cells(self) -> frozenset[tuple[int, int]]:
        """Return the set of cells reserved for the '42' pattern."""
        return self._blocked

    @property
    def pattern_applied(self) -> bool:
        """Return True if the '42' pattern has been applied to the maze."""
        return bool(self._blocked)

    def _pattern_rows(self) -> list[int]:
        """Candidate top rows, closest to the centred position first."""
        lowest = 1
        highest = self.height - PATTERN_HEIGHT - 1
        centred = (self.height - PATTERN_HEIGHT) // 2

        return sorted(range(lowest, highest + 1), key=lambda y: abs(y - centred))


def main_func():

    # 1. Create a fresh 4x4 maze

    maze = MazeGenerator(
        width=4,
        height=4,
        entry=(0, 0),
        exit=(3, 3)
    )

    def print_grid(title: str):

        print(f"\n=== {title} ===")

        for y in range(maze.height):

            row_str = []

            for x in range(maze.width):

                # Format numbers to be 2 chars wide for alignment (e.g., 15,  7, 13)
                row_str.append(f"{maze.grid[y][x]:2}")
            print("  ".join(row_str))
    # Show initial fully closed state
    print_grid("INITIAL STATE (All Walls - 15)")
    # 2. Action: Open the EAST wall of cell (0,0)
    print("\n Action: Opening the EAST wall of cell (0,0)...")
    maze._open_wall(0, 0, EAST)
    # Show the grid after breaking the wall
    print_grid("AFTER OPENING WALL")
    # 3. Action: Close the wall back
    print("\n Action: Closing the wall back...")
    maze._close_wall(0, 0, EAST)
    # Show the grid after restoring the wall
    print_grid("AFTER CLOSING WALL (Restored)")


if __name__ == "__main__":
    main_func()
