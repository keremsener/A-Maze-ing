from mazegen import MazeGenerator
from dotenv import load_dotenv
import os
import sys
# pip install -e ./packages/mazegen

maze_counter = 0


def main_func():
    global maze_counter
    try:
        load_dotenv()
        raw_entry = os.getenv("ENTRY", "0,0")
        entry_tuple = tuple(map(int, raw_entry.split(",")))
        perfect_val = os.getenv("PERFECT", "True").lower() == "true"
        raw_exit = os.getenv("EXIT", "3,3")
        exit_tuple = tuple(map(int, raw_exit.split(",")))

        if perfect_val:
            type = "PERFECT"
        else:
            type = "PAC-MAN"

        print(f"\n=== {type} MAZE ===")
        perfect_maze = MazeGenerator(
            width=int(os.getenv("WIDTH")),
            height=int(os.getenv("HEIGHT")),
            entry=entry_tuple,
            exit=exit_tuple,
            perfect=perfect_val)
        maze_counter += 1
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
        while True:
            print("=== A-Maze-ing ===")
            print("""
1. Re-generate a new maze
2. Show/Hide the shortest path
3. Rotate the wall colours
4. Quit
""")
            question = int(input("Choice? (1-4):"))
            if question == 1:
                main_func()
            elif question == 4:
                print(f"Total number of mazes generated: {maze_counter}."
                      f" Program closing..")
                sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main_func()
