import csv
import os
from flask import Blueprint, render_template, request, jsonify

game_bp = Blueprint("game", __name__)

CSV_FILE = "player_ships.csv"

# Vérifier si le fichier CSV existe, sinon le créer avec un en-tête
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["player_id", "row", "col", "size", "orientation"])  # En-tête du fichier

# Fonction pour sauvegarder les bateaux d'un joueur dans un fichier CSV
def save_ships_csv(player_id, ships):
    """Sauvegarde les bateaux du joueur dans un fichier CSV."""
    with open(CSV_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        for ship in ships:
            writer.writerow([player_id, ship["row"], ship["col"], ship["size"], ship["orientation"]])
    print(f"✅ Bateaux enregistrés pour {player_id} dans {CSV_FILE}")

# Fonction pour récupérer les bateaux d'un joueur depuis le CSV
def get_ships_csv(player_id):
    """Récupère les bateaux placés par un joueur dans le fichier CSV."""
    ships = []
    with open(CSV_FILE, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["player_id"] == player_id:
                ships.append({
                    "row": int(row["row"]),
                    "col": int(row["col"]),
                    "size": int(row["size"]),
                    "orientation": row["orientation"]
                })
    return ships

# ROUTES ORIGINALES CONSERVÉES ✅
@game_bp.route("/")
def home():
    return render_template("index.html")

@game_bp.route("/game")
def game():
    return render_template("game.html")

@game_bp.route("/mode")
def mode():
    return render_template("mode.html")

@game_bp.route("/game/1v1")
def game_1v1():
    return render_template("game_1v1.html")  # MAJ pour charger une vraie page

@game_bp.route("/game/1vIA")
def game_1vIA():
    return render_template("game_1vIA.html")  # MAJ pour charger une vraie page

@game_bp.route("/battle")
def battle():
    return render_template("battle.html")  # MAJ pour charger une vraie page

# Route pour sauvegarder les bateaux d'un joueur
@game_bp.route("/save_ships", methods=["POST"])
def save_ships():
    data = request.json
    player_id = data.get("player_id")  
    ships = data.get("ships")  

    if not player_id or not ships:
        return jsonify({"status": "error", "message": "Données manquantes"}), 400

    save_ships_csv(player_id, ships)

    return jsonify({"status": "success", "message": f"Bateaux de {player_id} sauvegardés."})

# Route pour récupérer les bateaux d'un joueur
@game_bp.route("/get_ships/<player_id>")
def get_ships(player_id):
    ships = get_ships_csv(player_id)
    if ships:
        return jsonify({"status": "success", "ships": ships})
    return jsonify({"status": "error", "message": "Aucun bateau trouvé"}), 404

# Route pour vérifier si les deux joueurs ont placé leurs bateaux
@game_bp.route("/confirm_ships", methods=["POST"])
def confirm_ships():
    """Vérifie si les deux joueurs ont placé leurs bateaux"""
    player1_ships = get_ships_csv("player1")
    player2_ships = get_ships_csv("player2")

    if player1_ships and player2_ships:
        return jsonify({"status": "ready", "message": "Les deux joueurs sont prêts."})
    return jsonify({"status": "waiting", "message": "En attente du deuxième joueur."})
