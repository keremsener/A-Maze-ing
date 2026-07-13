
import random

class MazeGenerator:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.grid = [[1 for _ in range(width)] for _ in range(height)]
        self.visited = [[False for _ in range(width)] for _ in range(height)]
        self.directions = [(0, -2), (0, 2), (-2, 0), (2, 0)]

    def _dfs(self, x: int, y: int):
        self.visited[y][x] = True
        self.grid[y][x] = 0

        random.shuffle(self.directions)

        for dx, dy in (self.directions):
            nx, ny = x + dx, y + dy

            if 0 < nx < self.width and 0 < ny < self.height:
                if not self.visited[ny][nx]:
                    self.grid[y + dy // 2][x + dx // 2] = 0
                    self._dfs(nx, ny)
    
    def generate(self, entry_x: int, entry_y: int, exit_x: int, exit_y: int, perfect: int):
        self._dfs(1, 1)

        self.grid[entry_y][entry_x] = 0
        self.grid[exit_y][exit_x] = 0

        if entry_x == 0:
            self.grid[entry_y][1] = 0
        elif entry_y == 0:
            self.grid[1][entry_x] = 0

        if exit_x == self.width - 1:
            self.grid[exit_y][self.width - 2] = 0
        elif exit_y == self.height - 1:
            self.grid[self.height - 2][exit_x] = 0

        if perfect == 0:
            self._make_imperfect()

        return self.grid

    def _make_imperfect(self):
        loop_count = (self.width * self.height) // 10
        for _ in range(loop_count):
            rx = random.randint(1, self.width - 2)
            ry = random.randint(1, self.height - 2)
            self.grid[ry][rx] = 0

if __name__ == "__main__":
    generator = MazeGenerator(21, 21)
    grid = generator.generate(0, 0, 20, 20, 1)
    for row in grid:
        print("".join(["██" if cell == 1 else "  " for cell in row]))