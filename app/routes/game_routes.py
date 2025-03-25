import csv
import os
import socket
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
        writer.writerow(["player_id", "row", "col", "size", "orientation"])

if not os.path.exists(TURN_FILE):
    with open(TURN_FILE, "w") as f:
        f.write("player1")

if not os.path.exists(SHOTS_FILE):
    with open(SHOTS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["target_player", "row", "col", "result"])

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def save_ships_csv(player_id, ships):
    existing_rows = []
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["player_id"] != player_id:
                    existing_rows.append(row)

    with open(CSV_FILE, "w", newline="") as f:
        fieldnames = ["player_id", "row", "col", "size", "orientation"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in existing_rows:
            writer.writerow(row)
        for ship in ships:
            writer.writerow({
                "player_id": player_id,
                "row": ship["row"],
                "col": ship["col"],
                "size": ship["size"],
                "orientation": ship["orientation"]
            })

def get_ships_csv(player_id):
    ships = []
    with open(CSV_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["player_id"] == player_id:
                ships.append({
                    "row": int(row["row"]),
                    "col": int(row["col"]),
                    "size": int(row["size"]),
                    "orientation": row["orientation"]
                })
    return ships

def save_shot(target_player, row, col, result):
    with open(SHOTS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([target_player, row, col, result])

def get_received_shots(player_id):
    shots = []
    if not os.path.exists(SHOTS_FILE):
        return shots

    with open(SHOTS_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["target_player"] == player_id:
                shots.append({
                    "row": int(row["row"]),
                    "col": int(row["col"]),
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
def game_1v1():
    ip = get_local_ip()
    return render_template("game_1v1.html", ip=ip)

@game_bp.route("/game/1v1/player2")
def game_1v1_player2():
    return render_template("game_1v1_player2.html")

@game_bp.route("/join", methods=["POST"])
def join():
    name = request.form.get("player_name")
    if "player1" not in players:
        players["player1"] = name
        return redirect(url_for("game.game", player_id="player1"))
    else:
        players["player2"] = name
        return redirect(url_for("game.game", player_id="player2"))

@game_bp.route("/game/<player_id>")
def game(player_id):
    return render_template("game.html", player_id=player_id)

@game_bp.route("/save_ships", methods=["POST"])
def save_ships():
    data = request.json
    player_id = data.get("player_id")
    ships = data.get("ships")
    if not player_id or not ships:
        return jsonify({"status": "error", "message": "Données manquantes"}), 400
    save_ships_csv(player_id, ships)
    return jsonify({"status": "success", "message": "Bateaux sauvegardés."})

@game_bp.route("/confirm_ships", methods=["POST"])
def confirm_ships():
    if get_ships_csv("player1") and get_ships_csv("player2"):
        return jsonify({"status": "ready"})
    return jsonify({"status": "waiting"})

@game_bp.route("/battle/<player_id>")
def battle(player_id):
    return render_template("battle.html", player_id=player_id)

@game_bp.route("/get_ships/<player_id>")
def get_ships(player_id):
    ships = get_ships_csv(player_id)
    if ships:
        return jsonify({"status": "success", "ships": ships})
    return jsonify({"status": "error", "message": "Aucun bateau trouvé"}), 404

@game_bp.route("/fire", methods=["POST"])
def fire():
    data = request.json
    x = data.get("row")
    y = data.get("col")
    player = data.get("player_id")

    if not all([x is not None, y is not None, player]):
        return jsonify({"status": "error", "message": "Données incomplètes"}), 400

    # 🔁 Empêche les tirs hors tour
    with open(TURN_FILE, "r") as f:
        current_turn = f.read().strip()

    if player != current_turn:
        return jsonify({"status": "error", "message": "Ce n'est pas votre tour"}), 403

    target_player = "player2" if player == "player1" else "player1"
    ships = get_ships_csv(target_player)

    for ship in ships:
        row = ship["row"]
        col = ship["col"]
        size = ship["size"]
        orientation = ship["orientation"]

        for i in range(size):
            ship_row = row + i if orientation == "vertical" else row
            ship_col = col + i if orientation == "horizontal" else col
            if ship_row == x and ship_col == y:
                save_shot(target_player, x, y, "hit")
                with open(TURN_FILE, "w") as f:
                    f.write(target_player)
                return jsonify({"status": "success", "result": "hit"})

    save_shot(target_player, x, y, "miss")
    with open(TURN_FILE, "w") as f:
        f.write(target_player)
    return jsonify({"status": "success", "result": "miss"})

@game_bp.route("/turn/<player_id>")
def turn(player_id):
    with open(TURN_FILE, "r") as f:
        current_turn = f.read().strip()
    return jsonify({"your_turn": player_id == current_turn})

@game_bp.route("/received_shots/<player_id>")
def received_shots(player_id):
    try:
        shots = get_received_shots(player_id)
        return jsonify({"status": "success", "shots": shots})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
