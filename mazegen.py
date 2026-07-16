from dataclasses import dataclass
from random import Random


@dataclass(frozen=True)
class Point:
    x: int
    y: int


class MazeError(Exception):
    """Maze configuration errors."""
    pass


class MazeGenerator:
    def __init__(
        self,
        width: int,
        height: int,
        entry: Point,
        exit: Point,
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

    def _validate(self) -> None:
        if self.width < 2 or self.height < 2:
            raise MazeError(
                f"Maze size must be at least 2x2 (got {self.width}x{self.height})."
            )


        if self.entry == self.exit:
            raise MazeError("Entry and exit cannot be the same point.")
        self._validate_point(self.entry, "Entry")
        self._validate_point(self.exit, "Exit")

    def _validate_point(self, point: Point, name: str) -> None:
        if not (0 <= point.x < self.width):
            raise MazeError(
                f"{name} x-coordinate ({point.x}) is outside the maze."
            )

        if not (0 <= point.y < self.height):
            raise MazeError(
                f"{name} y-coordinate ({point.y}) is outside the maze."
            )


if __name__ == "__main__":
    maze = MazeGenerator(
        width=4,
        height=4,
        entry=Point(0, 0),
        exit=Point(3, 3),
        perfect=True,
        seed=42,
    )

    print("Maze created successfully!")