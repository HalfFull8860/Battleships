# app.py
# This file defines the Flask web server that acts as the API for the Battleship game.
# It handles all HTTP requests, manages game sessions, and communicates with the core game logic in game.py.

from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import string
import secrets

# Import the core game logic from game.py
from game import Game

app = Flask(__name__)
CORS(app) # Enable Cross-Origin Resource Sharing to allow the frontend to connect.

# A simple in-memory dictionary to store active game sessions.
# The key is the game_id, and the value is a dictionary containing session metadata.
games = {} 

@app.route("/")
def index():
    return "<h1>Battleship API is running!</h1>"

@app.route("/game", methods=["POST"])
def create_game():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    # --- Input Validation ---
    # Extracts game parameters from the request, providing default values where applicable.
    mode = data.get("mode", "vs_bot")
    number_of_games = data.get("number_of_games", 1)
    player1_name = data.get("player1_name")
    player2_name = data.get("player2_name")

    # Ensures all required fields are present for the chosen game mode.
    if not player1_name:
        return jsonify({"error": "player1_name is a required field"}), 400
    if mode == "vs_player" and not player2_name:
        return jsonify({"error": "Two-player mode requires player2_name"}), 400
    if mode not in ["vs_bot", "vs_player"]:
        return jsonify({"error": "Invalid game mode"}), 400

    # --- Game Session Creation ---
    # Generate a secure, URL-friendly 6-character ID for the new game.
    alphabet = string.ascii_uppercase + string.digits
    game_id = ''.join(secrets.choice(alphabet) for i in range(6))
    # Create a new instance of the Game engine from game.py.
    game_instance = Game(mode=mode)

    # Store the game instance and all match-related metadata in the sessions dictionary.
    # This separates the persistent match data from the round-specific game logic.
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

    # Return the new game details to the client so it can join the session.
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

    # Validate the player_id provided in the URL query parameter.
    player_id = request.args.get('player_id')
    if player_id is None:
        return jsonify({"error": "player_id query parameter is required"}), 400

    try:
        player_id = int(player_id)
        if player_id not in [Game.PLAYER_1, Game.PLAYER_2]:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid player_id"}), 400

    # Get the base state from the game logic
    game_state = session['game_logic'].get_state(player_id)
    
    # Enrich the game state with session-level data (names, wins, etc.).
    game_state['player1_name'] = session['player1_name']
    game_state['player2_name'] = session['player2_name']
    game_state['wins'] = session['wins']
    game_state['match_winner'] = session['match_winner']

    # Wrap the final game state object for a consistent API response structure.
    return jsonify({
        "message": "Game state retrieved successfully.",
        "game_state": game_state
    })


@app.route("/game/<game_id>/attack", methods=["POST"])
def attack(game_id):
    session = games.get(game_id)
    if not session:
        return jsonify({"error": "Game not found"}), 404
    game = session['game_logic']

    # Validate the required fields from the JSON request body.
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

    # Delegate the attack action to the game engine.
    result = game.attack(player_id, row, col)

    # Return any errors generated by the game logic (e.g., "It's not your turn").
    if "error" in result:
        return jsonify(result), 400

    # Check if the bot made a winning move.
    # The 'game_over' flag would be nested inside the 'bot_turns' list.
    bot_turns = result.get('bot_turns')
    if bot_turns:
        # The last move in the list is the decisive one.
        last_bot_turn = bot_turns[-1]
        if last_bot_turn.get('game_over'):
            # Promote the game_over and winner status to the top-level result object
            # so the following logic block can process it correctly.
            result['game_over'] = True
            result['winner'] = last_bot_turn.get('winner')

    # This logic block now correctly handles wins by either the player OR the bot.
    if result.get("game_over"):
        winner = result.get("winner")
        if winner is not None:
            session['wins'][winner] += 1
            # Check if the match is over or if a new round should begin.
            if session['wins'][winner] >= session['number_of_games']:
                session['match_winner'] = winner
            else:
                game.reset_game()

    # Always return the complete, most up-to-date game state after a move.
    # This is enriched with session data to ensure the client has all necessary info.
    final_game_state = game.get_state(player_id)
    final_game_state['player1_name'] = session['player1_name']
    final_game_state['player2_name'] = session['player2_name']
    final_game_state['wins'] = session['wins']
    final_game_state['match_winner'] = session['match_winner']

    return jsonify({
        "message": "Attack successful!",
        "attack_result": result, # 'result' now contains player_attack and possibly bot_turns
        "game_state": final_game_state
    })

# This block runs the Flask development server when the script is executed directly.
if __name__ == "__main__":
    app.run(debug=True, port=5001)
