# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid

# Import the core game logic from game.py
from game import Game

app = Flask(__name__)
CORS(app)

games = {}  # In-memory session storage

@app.route("/")
def index():
    return "<h1>Battleship API is running!</h1>"

@app.route("/game", methods=["POST"])
def create_game():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    mode = data.get("mode", "vs_bot")
    number_of_games = data.get("number_of_games", 1)
    player1_name = data.get("player1_name")
    player2_name = data.get("player2_name")

    if not player1_name:
        return jsonify({"error": "player1_name is a required field"}), 400
    if mode == "vs_player" and not player2_name:
        return jsonify({"error": "Two-player mode requires player2_name"}), 400
    if mode not in ["vs_bot", "vs_player"]:
        return jsonify({"error": "Invalid game mode"}), 400

    game_id = str(uuid.uuid4())
    game_instance = Game(mode=mode)

    games[game_id] = {
        "game_logic": game_instance,
        "player1_name": player1_name,
        "player2_name": player2_name,
        "mode": mode,
        "number_of_games": number_of_games,
        "wins": {
            Game.PLAYER_1: 0,
            Game.PLAYER_2: 0
        },
        "match_winner": None
    }

    return jsonify({
        "message": "Game created successfully!",
        "game_id": game_id,
        "player_1_id": Game.PLAYER_1,
        "player_2_id": Game.PLAYER_2,
        "player1_name": player1_name,
        "player2_name": player2_name,
        "mode": mode,
        "number_of_games": number_of_games
    }), 201

@app.route("/game/<game_id>", methods=["GET"])
def get_game_state(game_id):
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

    game_state = session['game_logic'].get_state(player_id)
    game_state['player1_name'] = session['player1_name']
    game_state['player2_name'] = session['player2_name']
    game_state['wins'] = session['wins']
    game_state['match_winner'] = session['match_winner']

    return jsonify(game_state)

@app.route("/game/<game_id>/place", methods=["POST"])
def place_ship(game_id):
    session = games.get(game_id)
    if not session:
        return jsonify({"error": "Game not found"}), 404
    game = session['game_logic']

    data = request.get_json()
    try:
        player_id = data['player_id']
        ship_size = data['ship_size']
        row = data['row']
        col = data['col']
        orientation = data['orientation']
    except KeyError:
        return jsonify({"error": "Missing required fields in request body"}), 400
    
    try:
        player_id = int(player_id)
        if player_id not in [Game.PLAYER_1, Game.PLAYER_2]:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid player_id"}), 400

    success, message = game.place_player_ship(player_id, ship_size, row, col, orientation)

    if not success:
        return jsonify({"error": message}), 400

    return jsonify({"message": message, "game_state": game.get_state(player_id)})

@app.route("/game/<game_id>/attack", methods=["POST"])
def attack(game_id):
    session = games.get(game_id)
    if not session:
        return jsonify({"error": "Game not found"}), 404
    game = session['game_logic']

    data = request.get_json()
    try:
        player_id = data['player_id']
        row = data['row']
        col = data['col']
    except KeyError:
        return jsonify({"error": "Missing required fields in request body"}), 400
    
    try:
        player_id = int(player_id)
        if player_id not in [Game.PLAYER_1, Game.PLAYER_2]:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid player_id"}), 400

    result = game.attack(player_id, row, col)

    if "error" in result:
        return jsonify(result), 400

    if result.get("game_over"):
        winner = result.get("winner")
        if winner is not None:
            session['wins'][winner] += 1
            if session['wins'][winner] == session['number_of_games']:
                session['match_winner'] = winner
            else:
                game.reset_game()  # reset for the next round

    return jsonify({
        "message": "Attack successful!",
        "attack_result": result,
        "game_state": game.get_state(player_id),
        "wins": session['wins'],
        "match_winner": session['match_winner']
    })

if __name__ == "__main__":
    app.run(debug=True, port=5001)
