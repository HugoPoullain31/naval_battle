import webbrowser
from flask import Flask
from routes.game_routes import game_bp
from routes.stats_routes import stats_bp

app = Flask(__name__, template_folder="templates", static_folder="static")

app.register_blueprint(game_bp)
app.register_blueprint(stats_bp)

if __name__ == "__main__":
    # Ouvre automatiquement le navigateur sur la page d'accueil
    webbrowser.open("http://127.0.0.1:5000/")
    
    # Démarre le serveur Flask
app.run(debug=True, use_reloader=False)

