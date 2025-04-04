from flask import Blueprint, render_template

stats_bp = Blueprint("stats", __name__)

@stats_bp.route("/stats")
def stats():
    return render_template("stats.html")

