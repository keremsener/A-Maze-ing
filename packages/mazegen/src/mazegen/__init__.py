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
DIRECTIONS = (NORTH, EAST, SOUTH, WEST)

# ---- "42" PATTERN CONSTANTS ----
PATTERN_HEIGHT = 5
PATTERN_WIDTH = 7

MIN_MAP_HEIGHT = 7
MIN_MAP_WIDTH = 9

FOUR_PATTERN = (
    "X.X",
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
        self._blocked = self._compute_pattern()

    def _validate(self) -> None:
        if self.width < 2 or self.height < 2:
            try:
                raise MazeError(
                    f"Maze size must be at least 2x2 (got {self.width}x{self.height})."
                )
            except MazeError as e:
                print(e)

        if self.entry == self.exit:
            try:
                raise MazeError("Entry and exit cannot be the same point.")
            except MazeError as e:
                print(e)
        self._validate_point(self.entry, "Entry")
        self._validate_point(self.exit, "Exit")

    def _validate_point(self, point: tuple[int, int], name: str) -> None:
        if not (0 <= point[0] < self.width):
            try:
                raise MazeError(
                    f"{name} x-coordinate ({point[0]}) is outside the maze."
                )
            except MazeError as e:
                print(e)

        if not (0 <= point[1] < self.height):
            try:
                raise MazeError(
                    f"{name} y-coordinate ({point[1]}) is outside the maze."
                )
            except MazeError as e:
                print(e)

    def _in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def _neighbour(self, x: int, y: int, direction: int) -> tuple[int, int]:
        dx, dy = STEP[direction]
        return x + dx, y + dy

    def _open_wall(self, x: int, y: int, direction: int):
        # The new neighbor's coordinates are return
        nx, ny = self._neighbour(x, y, direction)
        if not self._in_bounds(nx, ny):
            try:
                raise MazeError("Cannot go outside the map")
            except MazeError as e:
                print(e)
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

    def _open_cells(self) -> list[tuple[int, int]]:
        safe_zone = []
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) not in self._blocked:
                    safe_zone.append((x, y))
        return safe_zone

    def _carve(self) -> None:
        start = self.entry
        stack = [start]  # yolumuzu kaybetmemek için
        visited = {start}  # Gittiğimiz yerleri unutmamak için

        while stack:
            x, y = stack[-1]
            option = []
            for direction in DIRECTIONS:
                nx, ny = self._neighbour(x, y, direction)
                if not self._in_bounds(nx, ny):
                    continue
                if (nx, ny) in self._blocked or (nx, ny) in visited:
                    continue
                option.append((direction, nx, ny))
            if not option:
                stack.pop()
                continue
            direction, nx, ny = self.random.choice(option)
            self._open_wall(x, y, direction)
            visited.add((nx, ny))
            stack.append((nx, ny))

    def generate(self) -> list[list[int]]:
        self._carve()
        if not self.perfect:
            self._braid()
        return self.grid

    def _pattern_rows(self) -> list[int]:
        """Candidate top rows, closest to the centred position first."""
        lowest = 1
        highest = self.height - PATTERN_HEIGHT - 1
        centred = (self.height - PATTERN_HEIGHT) // 2

        return sorted(range(lowest, highest + 1), key=lambda y: abs(y - centred))

    def _block_at(self, x0: int, y0: int) -> frozenset[tuple[int, int]]:
        cells = set()

        # Process the '4' digit pattern row by row and char by char
        for r, row_str in enumerate(FOUR_PATTERN):
            for c, char in enumerate(row_str):
                if char == "X":
                    cells.add((x0 + c, y0 + r))

        # Process the '2' digit pattern
        for r, row_str in enumerate(TWO_PATTERN):
            for c, char in enumerate(row_str):
                if char == "X":
                    # Shift 4 units right on the X-axis to avoid overlapping with the '4'
                    cells.add((x0 + 4 + c, y0 + r))

        return frozenset(cells)

    def _compute_pattern(self):
        if self.height < MIN_MAP_HEIGHT or self.width < MIN_MAP_WIDTH:
            return frozenset()
        x0 = (self.width - PATTERN_WIDTH) // 2
        forbidden_place = (self.width // 2, self.height // 2)
        coordinates = {self.entry, self.exit, forbidden_place}
        for y0 in self._pattern_rows():
            candidate_cells = self._block_at(x0, y0)
            if candidate_cells.isdisjoint(coordinates):
                return candidate_cells
        return frozenset()

    def _open_count(self, x: int, y: int) -> int:
        counter: int = 0
        for direction in DIRECTIONS:
            if not self.grid[y][x] & direction:
                counter += 1
        return counter

    def _is_open_area(self, x0: int, y0: int) -> bool:
        for y in range(y0, y0 + 3):
            for x in range(x0, x0 + 3):
                if not self._in_bounds(x, y):
                    return False
                if (x, y) in self._blocked:
                    return False

        for y in range(y0, y0 + 3):
            for x in range(x0, x0 + 3):
                if x < x0 + 2 and self.grid[y][x] & EAST:
                    return False
                if y < y0 + 2 and self.grid[y][x] & SOUTH:
                    return False
        return True

    def _creates_open_area(self, x: int, y: int, direction: int) -> bool:
        self._open_wall(x, y, direction)
        nx, ny = self._neighbour(x, y, direction)
        danger = False
        for cx, cy in ((x, y), (nx, ny)):
            for x0 in range(cx - 2, cx + 1):
                for y0 in range(cy - 2, cy + 1):
                    if self._is_open_area(x0, y0):
                        danger = True
        self._close_wall(x, y, direction)
        return danger

    def _braid(self) -> None:
        safe_zone = self._open_cells()
        for x, y in safe_zone:
            if self._open_count(x, y) == 1:
                local_directions = list(DIRECTIONS)
                self.random.shuffle(local_directions)
                for direction in DIRECTIONS:
                    nx, ny = self._neighbour(x, y, direction)
                    if self._in_bounds(nx, ny) and (nx, ny) not in self._blocked:
                        if not self._creates_open_area(x, y, direction):
                            self._open_wall(x, y, direction)
                            break

    def solve(self) -> list[tuple[int, int]]:
        """BFS algoritması ile girişten çıkışa giden yolu bulur."""
        queue = [[self.entry]]  # Gidilecek yolların listesi
        visited = {self.entry}  # Kendi etrafımızda dönmemek için hafıza

        while queue:
            # Kuyruktaki ilk yolu al
            path = queue.pop(0)
            # Bu yolun en sonundaki (şu an bulunduğumuz) hücreyi al
            x, y = path[-1]

            # Eğer çıkışa ulaştıysak, bu yolu direkt teslim et
            if (x, y) == self.exit:
                return path

            # Çıkışta değilsek, 4 yöne bak
            for direction in DIRECTIONS:
                # O yönde DUVAR YOKSA (Bitwise kontrolü)
                if not self.grid[y][x] & direction:
                    nx, ny = self._neighbour(x, y, direction)
                    # Daha önce o hücreye gitmediysek
                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        # Mevcut yola bu yeni adımı ekle ve kuyruğa at
                        queue.append(path + [(nx, ny)])

        # Eğer harita çözülemiyorsa boş liste dön
        return []
