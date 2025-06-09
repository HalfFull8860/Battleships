# app.py
# This file contains the Flask web application.

from flask import Flask, request, jsonify
from flask_cors import CORS  # To allow frontend requests
import uuid

# Import the game logic
from game import Game, Game

# Initialize Flask App
app = Flask(__name__)
CORS(app)  # This allows requests from any origin. For production, you might want to restrict this.

# In-memory storage for games.
# For a real application, you would use a database (e.g., Redis, PostgreSQL).
games = {}

@app.route("/")
def index():
    """A simple welcome route to confirm the server is running."""
    return "<h1>Battleship API is running!</h1>"


@app.route("/game", methods=["POST"])
def create_game():
    """
    Creates a new game session.
    Request body (JSON): {"mode": "vs_bot" or "vs_player"}
    """
    data = request.get_json()
    mode = data.get("mode", "vs_bot")
    if mode not in ["vs_bot", "vs_player"]:
        return jsonify({"error": "Invalid game mode"}), 400

    game_id = str(uuid.uuid4())
    games[game_id] = Game(mode=mode)

    return jsonify({
        "message": "Game created successfully!",
        "game_id": game_id,
        "player_1_id": Game.PLAYER_1,
        "player_2_id": Game.PLAYER_2,
        "mode": mode
    }), 201


@app.route("/game/<game_id>", methods=["GET"])
def get_game_state():
    """
    Gets the state of a specific game for a specific player.
    Query params: ?player_id=0
    """
    game = games.get(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    player_id = request.args.get('player_id')
    if player_id is None:
        return jsonify({"error": "player_id query parameter is required"}), 400

    try:
        player_id = int(player_id)
        if player_id not in [Game.PLAYER_1, Game.PLAYER_2]:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid player_id"}), 400

    return jsonify(game.get_state(player_id))


@app.route("/game/<game_id>/place", methods=["POST"])
def place_ship(game_id):
    """
    Places a ship for a player.
    Request body (JSON): {
        "player_id": 0,
        "ship_size": 5,
        "row": 0,
        "col": 0,
        "orientation": "horizontal"
    }
    """
    game = games.get(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    data = request.get_json()
    try:
        player_id = data['player_id']
        ship_size = data['ship_size']
        row = data['row']
        col = data['col']
        orientation = data['orientation']
    except KeyError:
        return jsonify({"error": "Missing required fields in request body"}), 400

    # Ensure the requested ship size is valid for this game
    if ship_size not in Game.SHIP_SIZES:
         return jsonify({"error": f"Invalid ship size. Valid sizes are: {Game.SHIP_SIZES}"}), 400

    # Ensure the ship has not already been placed
    placed_ship_sizes = [len(s['coords']) for s in game.players[player_id]['board'].ships]
    if placed_ship_sizes.count(ship_size) >= Game.SHIP_SIZES.count(ship_size):
         return jsonify({"error": f"All ships of size {ship_size} have already been placed."}), 400

    success, message = game.place_player_ship(player_id, ship_size, row, col, orientation)

    if not success:
        return jsonify({"error": message}), 400

    return jsonify({"message": message, "game_state": game.get_state(player_id)})


@app.route("/game/<game_id>/attack", methods=["POST"])
def attack(game_id):
    """
    Performs an attack.
    Request body (JSON): { "player_id": 0, "row": 1, "col": 1 }
    """
    game = games.get(game_id)
    if not game:
        return jsonify({"error": "Game not found"}), 404

    data = request.get_json()
    try:
        player_id = data['player_id']
        row = data['row']
        col = data['col']
    except KeyError:
        return jsonify({"error": "Missing required fields in request body"}), 400

    result = game.attack(player_id, row, col)

    if "error" in result:
        return jsonify(result), 400

    return jsonify({
        "message": "Attack successful!",
        "attack_result": result,
        "game_state": game.get_state(player_id)
    })

# To run this application:
# 1. Save the code above as app.py
# 2. Save the first code block as game.py in the same directory.
# 3. Install Flask: pip install Flask Flask-Cors
#    (If you get a permission error, try: pip install --user Flask Flask-Cors)
# 4. Run from your terminal: flask --app app run
if __name__ == "__main__":
    # This allows running the file directly with `python app.py`
    app.run(debug=True, port=5001)g