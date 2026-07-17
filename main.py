from a_maze_ing import MazeGenerator, NORTH, EAST


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


if __name__ == "__main__":
    main_func()
