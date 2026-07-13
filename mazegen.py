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
        self._dfs(entry_x, entry_y)