import random

def generate_ai_ships():
    sizes = [5, 4, 3, 3, 2]
    ships = []
    grid = [[0]*10 for _ in range(10)]

    for size in sizes:
        placed = False
        while not placed:
            orientation = random.choice(["horizontal", "vertical"])
            row = random.randint(0, 9)
            col = random.randint(0, 9)

            if orientation == "horizontal" and col + size <= 10 and all(grid[row][c] == 0 for c in range(col, col+size)):
                for c in range(col, col+size):
                    grid[row][c] = 1
                ships.append({"row": row, "col": col, "size": size, "orientation": "horizontal"})
                placed = True

            elif orientation == "vertical" and row + size <= 10 and all(grid[r][col] == 0 for r in range(row, row+size)):
                for r in range(row, row+size):
                    grid[r][col] = 1
                ships.append({"row": row, "col": col, "size": size, "orientation": "vertical"})
                placed = True

    return ships
