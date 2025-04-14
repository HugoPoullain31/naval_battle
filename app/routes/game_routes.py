import csv
import os
import socket
import uuid 
from .ia import generate_ai_ships
from flask import Blueprint, render_template, request, redirect, url_for, jsonify

game_bp = Blueprint("game", __name__)

CSV_FILE = "player_ships.csv"
TURN_FILE = "turn.txt"
SHOTS_FILE = "shots.csv"
players = {}

# Initialisation fichiers
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f, delimiter=';')  # Ajout
        writer.writerow(["game_id", "player_id", "row", "col", "size", "orientation"])

if not os.path.exists(SHOTS_FILE):
    with open(SHOTS_FILE, "w", newline="") as f:
        writer = csv.writer(f, delimiter=';')  # Ajout
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
        reader = csv.DictReader(f, delimiter=';')  # Ajout du délimiteur
        for row in reader:
            if row["game_id"] != game_id or row["player_id"] != player_id:
                existing_rows.append(row)

    with open(CSV_FILE, "w", newline="") as f:
        fieldnames = ["game_id", "player_id", "row", "col", "size", "orientation"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')  # Ajout du délimiteur
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
        reader = csv.DictReader(f, delimiter=';')  # Ajout du délimiteur
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
        writer = csv.writer(f, delimiter=';')  # Ajout du délimiteur
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
        reader = csv.DictReader(f, delimiter=';')  # Ajout du délimiteur
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


def log_game_history(game_id, player_name, opponent_name, turn_number, row, col, result, opponent_ships, winner=None):
    file_path = "games_history.csv"
    
    if not os.path.exists(file_path):
        with open(file_path, mode="w", newline="") as f:
            writer = csv.writer(f, delimiter=';')  # Ajout du délimiteur
            writer.writerow([
                "game_id",
                "player_name",
                "opponent_name",
                "turn_number",
                "row",
                "col",
                "result",
                "opponent_ship_positions",
                "winner"
            ])

    with open(file_path, mode="a", newline="") as f:
        writer = csv.writer(f, delimiter=';')  # Ajout du délimiteur
        writer.writerow([
            game_id,
            player_name,
            opponent_name,
            turn_number,
            row,
            col,
            result,
            str(opponent_ships),
            winner or ""
        ])



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

    if not all([player, game_id]):
        return jsonify({"status": "error", "message": "Données incomplètes"}), 400

    # Vérifie le tour
    current_turn = None
    if os.path.exists(TURN_FILE):
        with open(TURN_FILE, "r") as f:
            for line in f:
                if line.startswith(f"{game_id}:"):
                    current_turn = line.strip().split(":")[1]
                    break

    if current_turn != player:
        return jsonify({"status": "error", "message": "Ce n'est pas votre tour"}), 403

    # Détermine la cible
    if player == "player":
        target_player = "ai"
    elif player == "ai":
        target_player = "player"
        from .ia import ai_select_target
        x, y = ai_select_target(game_id, target_player)
    elif player == "player1":
        target_player = "player2"
    elif player == "player2":
        target_player = "player1"
    else:
        return jsonify({"status": "error", "message": "Joueur invalide"}), 400

    # Vérifie si le tir touche un bateau
    ships = get_ships_csv(game_id, target_player)
    result = "miss"
    for ship in ships:
        for i in range(ship["size"]):
            r = ship["row"] + i if ship["orientation"] == "vertical" else ship["row"]
            c = ship["col"] + i if ship["orientation"] == "horizontal" else ship["col"]
            if r == x and c == y:
                result = "hit"

    save_shot(game_id, target_player, x, y, result)

    # Vérifie si la partie est finie AVANT de changer de tour
    def count_hits(target):
        count = 0
        with open(SHOTS_FILE, "r") as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                if row["game_id"] == game_id and row["target_player"] == target and row["result"] == "hit":
                    count += 1
        return count

    total_parts_ai = sum(s["size"] for s in get_ships_csv(game_id, "ai"))
    total_parts_player = sum(s["size"] for s in get_ships_csv(game_id, "player"))

    hits_ai = count_hits("ai")
    hits_player = count_hits("player")

    victory = False
    defeat = False

    if player == "player":
        if hits_ai >= total_parts_ai:
            victory = True
        elif hits_player >= total_parts_player:
            defeat = True
    elif player == "ai":
        if hits_player >= total_parts_player:
            victory = True
        elif hits_ai >= total_parts_ai:
            defeat = True



    # Mise à jour du tour SEULEMENT si la partie continue
    if not victory and not defeat:
        update_turn_file(game_id, target_player)

    # Log historique
    turn_number = 0
    if os.path.exists("games_history.csv"):
        with open("games_history.csv", "r") as f:
            turn_number = sum(1 for line in f if line.startswith(game_id))

    log_game_history(
        game_id=game_id,
        player_name=players.get(f"{game_id}:{player}", player),
        opponent_name=players.get(f"{game_id}:{target_player}", target_player),
        turn_number=turn_number + 1,
        row=x,
        col=y,
        result=result,
        opponent_ships=ships
    )

    return jsonify({
        "status": "success",
        "result": result,
        "row": x,
        "col": y,
        "victory": victory,
        "defeat": defeat
    })





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

@game_bp.route("/game/1vsIA")
def game_1vs_ia_redirect():
    game_id = str(uuid.uuid4())[:8]
    return redirect(url_for("game.game_1vs_ia", game_id=game_id))

@game_bp.route("/game/1vsIA/<game_id>")
def game_1vs_ia(game_id):
    return render_template("game_vs_ia.html", game_id=game_id)


@game_bp.route("/start_game_vs_ai", methods=["POST"])
def start_game_vs_ai():
    data = request.get_json()
    player_ships = data.get("ships")
    if not player_ships:
        return jsonify({"status": "error", "message": "Aucun bateau envoyé"}), 400

    game_id = str(uuid.uuid4())[:8]
    save_ships_csv(game_id, "player", player_ships)
    ai_ships = generate_ai_ships()
    save_ships_csv(game_id, "ai", ai_ships)
    update_turn_file(game_id, "player")
    return jsonify({"status": "success", "game_id": game_id})


@game_bp.route("/battle_ia/<game_id>/<player_id>")
def battle_ia(game_id, player_id):
    return render_template("battle_ia.html", game_id=game_id, player_id=player_id)
