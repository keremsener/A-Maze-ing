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

MIN_MAP_HEIGHT = 7
MIN_MAP_WIDTH = 9

def solve_func(self) -> list[tuple[int, int]]:
        """BFS algoritması ile girişten çıkışa giden yolu bulur."""
        queue = [[self.entry]]  # Gidilecek yolların listesi
        visited = {self.entry}  # Kendi etrafımızda dönmemek için hafıza

        while queue:
            # Kuyruktaki ilk yolu al
            path = queue.pop(0)
            # Bu yolun en sonundaki (şu an bulunduğumuz) hücreyi al
            x, y = path[-1]

            # Eğer çıkışa ulaştıysak, bu yolu direkt teslim et (Dosya I/O işlemi YOK!)
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