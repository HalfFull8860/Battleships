# app.py
# This is the final, fully merged application.
# It handles database storage, match play, and different placement modes.

import os
import uuid
import string
import secrets
from flask import Flask, request, jsonify
from flask_cors import CORS

from game import Game
import database


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'battleship.sqlite'),
        JSONIFY_PRETTYPRINT_REGULAR=True  # Makes Postman output readable
    )
    CORS(app)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    database.init_app(app)

    # --- API ENDPOINTS ---

    @app.route("/")
    def index():
        return "<h1>Battleship API is running! (Merged)</h1>"

    @app.route("/game", methods=["POST"])
    def create_game_endpoint():
        data = request.get_json()
        if not data: return jsonify({"error": "Request body must be JSON"}), 400

        # Get all options for game creation
        mode = data.get("mode", "vs_bot")
        placement = data.get("placement", "random")
        number_of_games = data.get("number_of_games", 1)
        player1_name = data.get("player1_name", "Player 1")
        player2_name = data.get("player2_name", "The Bot" if mode == 'vs_bot' else "Player 2")

        if mode == "vs_player" and player1_name == player2_name:
            return jsonify({"error": "Player names must be unique"}), 400

        # Create a new game instance and session data
        game_id = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for i in range(6))
        game_instance = Game(mode=mode, placement=placement)

        session_data = {
            "game_logic": game_instance,
            "player1_name": player1_name,
            "player2_name": player2_name,
            "number_of_games": number_of_games,
            "wins": {Game.PLAYER_1: 0, Game.PLAYER_2: 0}
        }

        # Save the new game session to the database
        database.save_game(game_id, session_data)

        # --- THIS IS THE UPDATED RESPONSE ---
        return jsonify({
            "message": "Game created successfully!",
            "game_id": game_id,
            "mode": mode,
            "number_of_games": number_of_games,
            "player1_name": player1_name,
            "player2_name": player2_name,
            "player_1_id": Game.PLAYER_1,
            "player_2_id": Game.PLAYER_2
        }), 201

    @app.route("/game/<game_id>", methods=["GET"])
    def get_game_state_endpoint(game_id):
        player_id = request.args.get('player_id', type=int)
        if player_id is None or player_id not in [0, 1]:
            return jsonify({"error": "A valid player_id (0 or 1) is required"}), 400

        session = database.load_game_session(game_id)
        if not session: return jsonify({"error": "Game not found"}), 404

        # Get state from the game logic and add session data to it
        game_state = session['game_logic'].get_state(player_id)
        game_state['player1_name'] = session['player1_name']
        game_state['player2_name'] = session['player2_name']
        game_state['wins'] = session['wins']

        # Check for a match winner
        for p_id, score in session['wins'].items():
            if score >= session['number_of_games']:
                game_state['match_winner'] = p_id
                break

        return jsonify(game_state)

    @app.route("/game/<game_id>/place", methods=["POST"])
    def place_ship_endpoint(game_id):
        session = database.load_game_session(game_id)
        if not session: return jsonify({"error": "Game not found"}), 404
        game = session['game_logic']

        data = request.get_json()
        player_id = data.get('player_id')

        success, message = game.place_player_ship(
            player_id, data['ship_size'], data['row'], data['col'], data['orientation']
        )
        if not success: return jsonify({"error": message}), 400

        # Save the updated game state back to the database
        database.save_game(game_id, session)
        return jsonify({"message": message, "game_state": game.get_state(player_id)})

    @app.route("/game/<game_id>/attack", methods=["POST"])
    def attack_endpoint(game_id):
        session = database.load_game_session(game_id)
        if not session: return jsonify({"error": "Game not found"}), 404
        game = session['game_logic']

        data = request.get_json()
        player_id = data.get('player_id')

        result = game.attack(player_id, data['row'], data['col'])
        if "error" in result: return jsonify(result), 400

        # Check for a round winner and update score
        if game.game_over:
            winner = game.winner
            if winner is not None:
                session['wins'][winner] += 1

                # Check if this win ends the whole match
                if session['wins'][winner] >= session['number_of_games']:
                    session['match_winner'] = winner
                    game.status_message = f"MATCH OVER! {session[f'player{winner + 1}_name']} wins the match!"
                else:
                    # If match is not over, reset the board for the next round
                    game.reset_game()

        # Save the updated session data (score and new board state)
        database.save_game(game_id, session)

        # Get the latest state to return to the user
        final_state = game.get_state(player_id)
        final_state.update({
            'wins': session['wins'],
            'match_winner': session.get('match_winner')
        })

        return jsonify(final_state)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5001)