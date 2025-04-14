import random
import csv
import os

SHOTS_FILE = "shots.csv"
HISTORY_FILE = "games_history.csv"

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


def evaluer_coups(game_id, target_player):
    # Initialisation du dictionnaire des scores pour chaque case
    scores = {(r, c): 0 for r in range(10) for c in range(10)}

    # 1. On retire les coups déjà joués
    already_shot = set()
    if os.path.exists(SHOTS_FILE):
        with open(SHOTS_FILE, "r") as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                if row["game_id"] == game_id and row["target_player"] == target_player:
                    already_shot.add((int(row["row"]), int(row["col"])))

    for coord in already_shot:
        scores.pop(coord, None)  # on enlève du dico

    # 2. Bonus pour les cases centrales
    for coord in scores:
        row, col = coord
        if 3 <= row <= 6 and 3 <= col <= 6:
            scores[coord] += 3

    # 3. Bonus autour des anciens "hits"
    hits = set()
    if os.path.exists(SHOTS_FILE):
        with open(SHOTS_FILE, "r") as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                if row["game_id"] == game_id and row["target_player"] == target_player:
                    if row["result"] == "hit":
                        hits.add((int(row["row"]), int(row["col"])))

    for (r, c) in hits:
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in scores:
                scores[(nr, nc)] += 5  # fort bonus autour des touches

    # 4. (OPTIONNEL) Historique basé sur games_history.csv

    return scores


def ai_select_target(game_id, target_player):
    scores = evaluer_coups(game_id, target_player)
    if not scores:
        return (0, 0)

    max_score = max(scores.values())
    meilleurs_coups = [coord for coord, score in scores.items() if score == max_score]

    return random.choice(meilleurs_coups)
