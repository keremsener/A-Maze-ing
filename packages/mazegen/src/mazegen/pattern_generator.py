"""Placement helpers for the closed-cell 42 pattern."""

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


class PatternGenerator:
    """Mixin whose concrete generator supplies maze placement state."""

    width: int
    height: int
    entry: tuple[int, int]
    exit: tuple[int, int]
    _blocked: frozenset[tuple[int, int]]

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
        return sorted(
            range(lowest, highest + 1),
            key=lambda y: abs(y - centred),
        )

    def _pattern_columns(self) -> list[int]:
        """Candidate left columns, closest to the centre first."""
        lowest = 1
        highest = self.width - PATTERN_WIDTH - 1
        centred = (self.width - PATTERN_WIDTH) // 2
        return sorted(
            range(lowest, highest + 1),
            key=lambda x: abs(x - centred),
        )

    def _compute_pattern(self) -> frozenset[tuple[int, int]]:
        if self.height < MIN_MAP_HEIGHT or self.width < MIN_MAP_WIDTH:
            return frozenset()
        forbidden_place = (self.width // 2, self.height // 2)
        coordinates = {self.entry, self.exit, forbidden_place}
        for y0 in self._pattern_rows():
            for x0 in self._pattern_columns():
                candidate_cells = self._block_at(x0, y0)
                if candidate_cells.isdisjoint(coordinates):
                    return candidate_cells
        return frozenset()

    def _block_at(
        self,
        x0: int,
        y0: int,
    ) -> frozenset[tuple[int, int]]:
        cells: set[tuple[int, int]] = set()

        # Process the '4' digit pattern row by row and char by char
        for r, row_str in enumerate(FOUR_PATTERN):
            for c, char in enumerate(row_str):
                if char == "X":
                    cells.add((x0 + c, y0 + r))

        # Process the '2' digit pattern
        for r, row_str in enumerate(TWO_PATTERN):
            for c, char in enumerate(row_str):
                if char == "X":
                    # Shift 4 units right on the
                    # X-axis to avoid overlapping with the '4'
                    cells.add((x0 + 4 + c, y0 + r))

        return frozenset(cells)
