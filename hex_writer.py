from typing import List, Tuple

class HexWriter:
    def __init__(self, filepath: str):
        self.filepath = filepath

    def write(self, grid: List[List[int]], entry: Tuple[int, int], exit_point: Tuple[int, int], solution: str):
        hex_grid = self._convert_to_bitmask(grid)

        with open(self.filepath, "w", encoding="utf-8") as f:
            for row in hex_grid:
                f.write("".join(row) + "\n")

            f.write("\n")
            f.write(f"{entry[0]},{entry[1]}\n")
            f.write(f"{exit_point[0]},{exit_point[1]}\n")
            f.write(f"{solution}\n")

    def _convert_to_bitmask(self, grid: List[List[int]]) -> List[List[str]]:
        height = len(grid)
        width = len(grid[0])
        hex_grid = []

        for y in range(height):
            row = []
            for x in range(width):
                if grid[y][x] == 1:
                    row.append("F")
                else:
                    val = 0
                    if y > 0 and grid[y-1][x] == 1: val += 1
                    if x < width - 1 and grid[y][x+1] == 1: val += 2
                    if y < height - 1 and grid[y+1][x] == 1: val += 4
                    if x > 0 and grid[y][x-1] == 1: val += 8

                    row.append(format(val, "X"))
            hex_grid.append(row)

        return hex_grid