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
        """Bu özellik, '42' deseninin kapatılmış olarak ayrılmış hücrelerini döndürür."""
        return self._blocked

    @property
    def pattern_applied(self) -> bool:
        """Bu özellik, '42' deseni labirente uygulanmışsa True döndürür; aksi halde False döner."""
        return bool(self._blocked)

    def _pattern_rows(self) -> list[int]:
        """Desenin üst satır adaylarını döndürür; merkez konuma en yakın satırlar önce gelir."""
        lowest = 1
        highest = self.height - PATTERN_HEIGHT - 1
        centred = (self.height - PATTERN_HEIGHT) // 2
        return sorted(
            range(lowest, highest + 1),
            key=lambda y: abs(y - centred),
        )

    def _pattern_columns(self) -> list[int]:
        """Desenin sol sütun adaylarını döndürür; merkez konuma en yakın sütunlar önce gelir."""
        lowest = 1
        highest = self.width - PATTERN_WIDTH - 1
        centred = (self.width - PATTERN_WIDTH) // 2
        return sorted(
            range(lowest, highest + 1),
            key=lambda x: abs(x - centred),
        )

    def _compute_pattern(self) -> frozenset[tuple[int, int]]:
        """Haritanın merkezine yerleştirilecek '42' deseninin uygun konumunu bulup o hücreleri döndürür."""
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
        """Verilen başlangıç konumundan '4' ve '2' rakamlarının desenini oluşturan tüm hücre koordinatlarını hesaplar."""
        cells: set[tuple[int, int]] = set()

        # '4' rakamı desenini satır satır ve karakter karakter işler.
        for r, row_str in enumerate(FOUR_PATTERN):
            for c, char in enumerate(row_str):
                if char == "X":
                    cells.add((x0 + c, y0 + r))

        # '2' rakamı desenini oluşturur.
        for r, row_str in enumerate(TWO_PATTERN):
            for c, char in enumerate(row_str):
                if char == "X":
                    # '4' ile çakışmaması için x ekseninde 4 birim sağa kaydırır.
                    cells.add((x0 + 4 + c, y0 + r))

        return frozenset(cells)
