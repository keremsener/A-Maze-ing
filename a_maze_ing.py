from mazegen import MazeGenerator, MazeError, EAST
# pip install -e ./packages/mazegen


def main_func():

    # 1. Create a fresh 4x4 maze
    maze = MazeGenerator(
        width=4,
        height=4,
        entry=(0, 0),
        exit=(3, 3)
    )

    def print_grid(title: str):
        print(f"\n=== {title} ===")
        for y in range(maze.height):
            row_str = []
            for x in range(maze.width):
                # Format numbers to be 2 chars wide for alignment (e.g., 15,  7, 13)
                row_str.append(f"{maze.grid[y][x]:2}")
            print("  ".join(row_str))
    # Show initial fully closed state
    print_grid("INITIAL STATE (All Walls - 15)")
    # 2. Action: Open the EAST wall of cell (0,0)
    print("\n Action: Opening the EAST wall of cell (0,0)...")
    maze._open_wall(0, 0, EAST)
    # Show the grid after breaking the wall
    print_grid("AFTER OPENING WALL")
    # 3. Action: Close the wall back
    print("\n Action: Closing the wall back...")
    maze._close_wall(0, 0, EAST)
    # Show the grid after restoring the wall
    print_grid("AFTER CLOSING WALL (Restored)")

    # 4. Preview the '42' pattern
    pattern_maze = MazeGenerator(width=9, height=7, entry=(0, 0), exit=(8, 6))
    print("\n=== '42' PATTERN PREVIEW ===")
    for y in range(pattern_maze.height):
        row_str = []
        for x in range(pattern_maze.width):
            # print(x, y)
            if (x, y) in pattern_maze.pattern_cells:
                row_str.append("XX")
            else:
                row_str.append("..")
        print("  ".join(row_str))

    print("\n=== PERFECT MAZE ===")
    perfect_maze = MazeGenerator(
        width=10, height=10, entry=(0, 0), exit=(9, 9), perfect=True)
    perfect_maze.generate()
    solution_path = perfect_maze.solve()

    for y in range(perfect_maze.height):
        row_str = []
        for x in range(perfect_maze.width):
            if (x, y) == perfect_maze.entry:
                row_str.append("EN")
            elif (x, y) in perfect_maze.pattern_cells:
                row_str.append("XX")
            elif (x, y) == perfect_maze.exit:
                row_str.append("EX")
            elif (x, y) in solution_path:
                row_str.append("..")
            else:
                row_str.append(f"{perfect_maze.grid[y][x]:2}")
        print("  ".join(row_str))

    print("\n=== PAC-MAN MAZE ===")
    pacman_maze = MazeGenerator(
        width=10, height=10, entry=(0, 0), exit=(9, 9), perfect=False)
    pacman_maze.generate()
    solution_path = pacman_maze.solve()

    for y in range(pacman_maze.height):
        row_str = []
        for x in range(pacman_maze.width):
            if (x, y) == pacman_maze.entry:
                row_str.append("EN")
            elif (x, y) == pacman_maze.exit:
                row_str.append("EX")
            elif (x, y) in pacman_maze.pattern_cells:
                row_str.append("XX")
            # EĞER BU HÜCRE ÇÖZÜM YOLUNUN İÇİNDEYSE
            elif (x, y) in solution_path:
                # Ayak izi gibi görünmesi için nokta koyuyoruz
                row_str.append("..")
            else:
                row_str.append(f"{pacman_maze.grid[y][x]:2}")

        print("  ".join(row_str))


if __name__ == "__main__":
    main_func()
