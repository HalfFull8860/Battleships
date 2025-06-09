# app.py
# This file contains the merged Flask web application.
from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid

# Import the core game logic from game.py
from game import Game

# Initialize Flask App
app = Flask(__name__)
CORS(app)  # This allows requests from any origin.

# In-memory storage for game sessions.
# This dictionary will hold the game logic object and player metadata.
# e.g., games['some-uuid'] = {'game_logic': Game(...), 'player1_name': 'Alice'}
games = {}


@app.route("/")
def index():
    """A simple welcome route to confirm the server is running."""
    return "<h1>Battleship API is running!</h1>"


@app.route("/game", methods=["POST"])
def create_game():
    """
    Creates a new game session, combining logic from both versions.
    Request body (JSON): {
        "mode": "vs_bot" or "vs_player",
        "player1_name": "Alice",
        "player2_name": "Bob" (optional)
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # --- Merged Logic ---
    # Get player names and mode from the request body
    mode = data.get("mode", "vs_bot")
    player1_name = data.get("player1_name")
    player2_name = data.get("player2_name")  # Will be None if not provided

    # Validate input
    if not player1_name:
        return jsonify({"error": "player1_name is a required field"}), 400
    if mode == "vs_player" and not player2_name:
        return jsonify({"error": "Two-player mode requires player2_name"}), 400
    if mode not in ["vs_bot", "vs_player"]:
        return jsonify({"error": "Invalid game mode"}), 400

    # --- Core Game Logic ---
    # Create a unique ID and a new Game instance
    game_id = str(uuid.uuid4())
    game_instance = Game(mode=mode)

    # Store both the game logic and the new metadata
    games[game_id] = {
        "game_logic": game_instance,
        "player1_name": player1_name,
        "player2_name": player2_name,
    }

    return jsonify({
        "message": "Game created successfully!",
        "game_id": game_id,
        "player_1_id": Game.PLAYER_1,
        "player_2_id": Game.PLAYER_2,
        "player1_name": player1_name,
        "player2_name": player2_name,
        "mode": mode
    }), 201


@app.route("/game/<game_id>", methods=["GET"])
def get_game_state(game_id):
    """
    Gets the state of a specific game for a specific player.
    This is the more powerful endpoint from your original version.
    Query params: ?player_id=0
    """
    session = games.get(game_id)
    if not session:
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

    # Get the state from the game_logic object
    game_state = session['game_logic'].get_state(player_id)

    # Add the player names to the response
    game_state['player1_name'] = session['player1_name']
    game_state['player2_name'] = session['player2_name']

    return jsonify(game_state)


@app.route("/game/<game_id>/place", methods=["POST"])
def place_ship(game_id):
    """
    Places a ship for a player.
    """
    session = games.get(game_id)
    if not session:
        return jsonify({"error": "Game not found"}), 404
    game = session['game_logic']  # Get the actual game object

    data = request.get_json()
    try:
        player_id = data['player_id']
        ship_size = data['ship_size']
        row = data['row']
        col = data['col']
        orientation = data['orientation']
    except KeyError:
        return jsonify({"error": "Missing required fields in request body"}), 400

    if ship_size not in Game.SHIP_SIZES:
        return jsonify({"error": f"Invalid ship size. Valid sizes are: {Game.SHIP_SIZES}"}), 400

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
    """
    session = games.get(game_id)
    if not session:
        return jsonify({"error": "Game not found"}), 404
    game = session['game_logic']  # Get the actual game object

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


# Main entry point to run the application
if __name__ == "__main__":
    app.run(debug=True, port=5001)

