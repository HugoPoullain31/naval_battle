import csv
import os
import socket
from flask import Blueprint, render_template, request, redirect, url_for, jsonify

game_bp = Blueprint("game", __name__)
CSV_FILE = "player_ships.csv"
players = {}

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["player_id", "row", "col", "size", "orientation"])

def save_ships_csv(player_id, ships):
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        for ship in ships:
            writer.writerow([player_id, ship["row"], ship["col"], ship["size"], ship["orientation"]])

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

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

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

@game_bp.route("/join", methods=["POST"])
def join():
    name = request.form.get("player_name")
    if "player1" not in players:
        players["player1"] = name
        player_id = "player1"
    elif "player2" not in players:
        players["player2"] = name
        player_id = "player2"
    else:
        return "La partie est déjà pleine !", 403

    return redirect(url_for("game.game", player_id=player_id))


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
