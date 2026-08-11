"""Breadth-first path finding for maze wall grids."""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence


NORTH = 1
EAST = 2
SOUTH = 4
WEST = 8
OPPOSITE = {NORTH: SOUTH, SOUTH: NORTH, EAST: WEST, WEST: EAST}
STEP = {
    NORTH: (0, -1),
    EAST: (1, 0),
    SOUTH: (0, 1),
    WEST: (-1, 0),
}
DIRECTIONS = (NORTH, EAST, SOUTH, WEST)

Point = tuple[int, int]
Grid = Sequence[Sequence[int]]


def solve_grid(grid: Grid, entry: Point, exit_: Point) -> list[Point]:
    """Return the shortest open-passage path from *entry* to *exit_*.

    An empty list means the exit is unreachable. The public generator
    translates that result into its domain-specific exception.
    """
    if not grid or not grid[0]:
        return []
    height = len(grid)
    width = len(grid[0])
    parents: dict[Point, Point | None] = {entry: None}
    queue = deque([entry])

    while queue:
        x, y = queue.popleft()
        if (x, y) == exit_:
            break
        for direction in DIRECTIONS:
            if grid[y][x] & direction:
                continue
            dx, dy = STEP[direction]
            nx, ny = x + dx, y + dy
            neighbour = (nx, ny)
            if not (0 <= nx < width and 0 <= ny < height):
                continue
            if grid[ny][nx] & OPPOSITE[direction]:
                continue
            if neighbour in parents:
                continue
            parents[neighbour] = (x, y)
            queue.append(neighbour)

    if exit_ not in parents:
        return []
    path: list[Point] = []
    cursor: Point | None = exit_
    while cursor is not None:
        path.append(cursor)
        cursor = parents[cursor]
    path.reverse()
    return path
