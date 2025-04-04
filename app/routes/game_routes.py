import csv
import os
import socket
import uuid 
from flask import Blueprint, render_template, request, redirect, url_for, jsonify

game_bp = Blueprint("game", __name__)

CSV_FILE = "player_ships.csv"
TURN_FILE = "turn.txt"
SHOTS_FILE = "shots.csv"
players = {}

# Initialisation fichiers
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["game_id", "player_id", "row", "col", "size", "orientation"])

if not os.path.exists(TURN_FILE):
    with open(TURN_FILE, "w") as f:
        f.write("")

if not os.path.exists(SHOTS_FILE):
    with open(SHOTS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["game_id", "target_player", "row", "col", "result"])

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def save_ships_csv(game_id, player_id, ships):
    existing_rows = []
    with open(CSV_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["game_id"] != game_id or row["player_id"] != player_id:
                existing_rows.append(row)

    with open(CSV_FILE, "w", newline="") as f:
        fieldnames = ["game_id", "player_id", "row", "col", "size", "orientation"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in existing_rows:
            writer.writerow(row)
        for ship in ships:
            writer.writerow({
                "game_id": game_id,
                "player_id": player_id,
                "row": ship["row"],
                "col": ship["col"],
                "size": ship["size"],
                "orientation": ship["orientation"]
            })

def get_ships_csv(game_id, player_id):
    ships = []
    with open(CSV_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["game_id"] == game_id and row["player_id"] == player_id:
                ships.append({
                    "row": int(row["row"]),
                    "col": int(row["col"]),
                    "size": int(row["size"]),
                    "orientation": row["orientation"]
                })
    return ships

def save_shot(game_id, target_player, row, col, result):
    with open(SHOTS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([game_id, target_player, row, col, result])

def get_received_shots(game_id, player_id):
    shots = []
    ships_coords = set()
    for ship in get_ships_csv(game_id, player_id):
        for i in range(ship["size"]):
            r = ship["row"] + i if ship["orientation"] == "vertical" else ship["row"]
            c = ship["col"] + i if ship["orientation"] == "horizontal" else ship["col"]
            ships_coords.add((r, c))

    with open(SHOTS_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["game_id"] == game_id and row["target_player"] == player_id:
                r, c = int(row["row"]), int(row["col"])
                if (r, c) in ships_coords:
                    shots.append({
                        "row": r,
                        "col": c,
                        "result": row["result"]
                    })
    return shots

# ROUTES
@game_bp.route("/")
def home():
    return render_template("index.html")

@game_bp.route("/mode")
def mode():
    return render_template("mode.html")

@game_bp.route("/game/1v1")
def game_1v1_redirect():
    new_game_id = str(uuid.uuid4())[:8]
    return redirect(url_for("game.game_1v1", game_id=new_game_id))

@game_bp.route("/game/1v1/<game_id>")
def game_1v1(game_id):
    ip = get_local_ip()
    return render_template("game_1v1.html", ip=ip, game_id=game_id)

@game_bp.route("/game/1v1/<game_id>/player2")
def game_1v1_player2(game_id):
    return render_template("game_1v1_player2.html", game_id=game_id)

@game_bp.route("/game/<game_id>/<player_id>")
def game(game_id, player_id):
    player_name = players.get(f"{game_id}:{player_id}", player_id)
    return render_template("game.html", player_id=player_id, game_id=game_id, player_name=player_name)

@game_bp.route("/join", methods=["POST"])
def join():
    name = request.form.get("player_name")
    role = request.form.get("player_role")
    game_id = request.form.get("game_id")

    if not all([name, role, game_id]):
        return "Données manquantes", 400

    players[f"{game_id}:{role}"] = name
    return redirect(url_for("game.game", game_id=game_id, player_id=role))

@game_bp.route("/save_ships", methods=["POST"])
def save_ships():
    data = request.json
    player_id = data.get("player_id")
    game_id = data.get("game_id")
    ships = data.get("ships")

    if not all([player_id, ships, game_id]):
        return jsonify({"status": "error", "message": "Données manquantes"}), 400

    save_ships_csv(game_id, player_id, ships)
    return jsonify({"status": "success", "message": "Bateaux sauvegardés."})

@game_bp.route("/confirm_ships", methods=["POST"])
def confirm_ships():
    data = request.json
    game_id = data.get("game_id")

    player1_ready = get_ships_csv(game_id, "player1")
    player2_ready = get_ships_csv(game_id, "player2")

    if player1_ready and player2_ready:
        already_initialized = False
        if os.path.exists(TURN_FILE):
            with open(TURN_FILE, "r") as f:
                for line in f:
                    if line.startswith(f"{game_id}:"):
                        already_initialized = True
                        break

        if not already_initialized:
            update_turn_file(game_id, "player1")

        return jsonify({"status": "ready"})
    
    return jsonify({"status": "waiting"})

@game_bp.route("/battle/<game_id>/<player_id>")
def battle(game_id, player_id):
    enemy_role = "player2" if player_id == "player1" else "player1"
    player_name = players.get(f"{game_id}:{player_id}", player_id)
    enemy_name = players.get(f"{game_id}:{enemy_role}", enemy_role)
    return render_template("battle.html", player_id=player_id, player_name=player_name, enemy_name=enemy_name, game_id=game_id)

@game_bp.route("/get_ships/<game_id>/<player_id>")
def get_ships(game_id, player_id):
    ships = get_ships_csv(game_id, player_id)
    if ships:
        return jsonify({"status": "success", "ships": ships})
    return jsonify({"status": "error", "message": "Aucun bateau trouvé"}), 404

@game_bp.route("/fire", methods=["POST"])
def fire():
    data = request.json
    x = data.get("row")
    y = data.get("col")
    player = data.get("player_id")
    game_id = data.get("game_id")

    if not all([x is not None, y is not None, player, game_id]):
        return jsonify({"status": "error", "message": "Données incomplètes"}), 400

    current_turn = None
    if os.path.exists(TURN_FILE):
        with open(TURN_FILE, "r") as f:
            for line in f:
                if line.startswith(f"{game_id}:"):
                    current_turn = line.strip().split(":")[1]
                    break

    if current_turn != player:
        return jsonify({"status": "error", "message": "Ce n'est pas votre tour"}), 403

    target_player = "player2" if player == "player1" else "player1"
    ships = get_ships_csv(game_id, target_player)

    for ship in ships:
        row, col, size, orientation = ship["row"], ship["col"], ship["size"], ship["orientation"]
        for i in range(size):
            ship_row = row + i if orientation == "vertical" else row
            ship_col = col + i if orientation == "horizontal" else col
            if ship_row == x and ship_col == y:
                save_shot(game_id, target_player, x, y, "hit")
                update_turn_file(game_id, target_player)
                return jsonify({"status": "success", "result": "hit"})

    save_shot(game_id, target_player, x, y, "miss")
    update_turn_file(game_id, target_player)
    return jsonify({"status": "success", "result": "miss"})

def update_turn_file(game_id, next_player):
    lines = []
    found = False
    if os.path.exists(TURN_FILE):
        with open(TURN_FILE, "r") as f:
            for line in f:
                if line.startswith(f"{game_id}:"):
                    lines.append(f"{game_id}:{next_player}\n")
                    found = True
                else:
                    lines.append(line)
    if not found:
        lines.append(f"{game_id}:{next_player}\n")
    with open(TURN_FILE, "w") as f:
        f.writelines(lines)

@game_bp.route("/turn/<game_id>/<player_id>")
def turn(game_id, player_id):
    if not os.path.exists(TURN_FILE):
        return jsonify({"your_turn": False})
    with open(TURN_FILE, "r") as f:
        for line in f:
            if line.startswith(f"{game_id}:"):
                return jsonify({"your_turn": line.strip().split(":")[1] == player_id})
    return jsonify({"your_turn": False})

@game_bp.route("/received_shots/<game_id>/<player_id>")
def received_shots(game_id, player_id):
    try:
        shots = get_received_shots(game_id, player_id)
        return jsonify({"status": "success", "shots": shots})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@game_bp.route("/next_turn", methods=["POST"])
def next_turn():
    data = request.json
    game_id = data.get("game_id")
    if not game_id:
        return jsonify({"status": "error", "message": "game_id requis"}), 400

    current_turn = None
    with open(TURN_FILE, "r") as f:
        lines = f.readlines()

    for line in lines:
        if line.startswith(f"{game_id}:"):
            current_turn = line.strip().split(":")[1]
            break

    new_turn = "player2" if current_turn == "player1" else "player1"
    update_turn_file(game_id, new_turn)

    return jsonify({"status": "success", "next_turn": new_turn})
