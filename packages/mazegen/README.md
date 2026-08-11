# mazegen

`mazegen` is the reusable maze-generation library from A-Maze-ing. It
supports deterministic seeds, perfect mazes, non-perfect mazes with at least
two independent cycles, protected closed-cell `42` patterns, and shortest-path
solving.

## Installation

```bash
python3 -m pip install mazegen-0.1.0-py3-none-any.whl
```

Python 3.10 or newer is required.

## Public API

```python
from mazegen import MazeError, MazeGenerator

maze = MazeGenerator(
    width=20,
    height=15,
    entry=(0, 0),
    exit=(19, 14),
    perfect=False,
    seed=42,
)
grid = maze.generate()
path = maze.solve()
directions = MazeGenerator.coords_to_letters(path)
```

The grid is indexed as `grid[y][x]`. Cell bits represent closed walls:
North=`1`, East=`2`, South=`4`, and West=`8`. `MazeError` reports
invalid inputs or an unsatisfiable maze contract.

## License

MIT. See `LICENSE.md`.
