from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid

app = Flask(__name__)
CORS(app)

game_sessions = {}

@app.route('/start-game', methods=['POST'])
def start_game():
    data = request.get_json()

    mode = data.get('mode')
    player1 = data.get('player1')
    player2 = data.get('player2', None)

    if not player1 or not mode:
        return jsonify({
            "status": "error",
            "message": "Missing required information"
        }), 400

    if mode == "2-player" and not player2:
        return jsonify({
            "status": "error",
            "message": "2-player mode requires a second player"
        }), 400

    # Generate a unique game ID
    game_id = str(uuid.uuid4())

    # Store game data
    game_sessions[game_id] = {
        "mode": mode,
        "player1": player1,
        "player2": player2,
        "board": None,
        "moves": [],
        "winner": None
    }

    return jsonify({
        "status": "success",
        "message": "Game started",
        "game_id": game_id
    })

@app.route('/get-game/<game_id>', methods=['GET'])
def get_game(game_id):
    game = game_sessions.get(game_id)
    if not game:
        return jsonify({
            "status": "error",
            "message": "Game not found"
        }), 404

    return jsonify({
        "status": "success",
        "game": game
    })

if __name__ == '__main__':
    app.run(debug=True)
