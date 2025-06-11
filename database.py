# database.py
# This file handles all interactions with the SQLite database.
# database.py
# This file handles all interactions with the SQLite database.
# It's now updated to handle match-level data like scores.

import sqlite3
import json
import click
from flask import current_app, g


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('init-db')
def init_db_command():
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)


# --- GAME-SPECIFIC DATABASE FUNCTIONS (UPDATED) ---

def save_game(game_id, session_data):
    """Saves or updates a complete game session in the database."""
    db = get_db()
    game_state_json = json.dumps(session_data['game_logic'].to_dict())

    # Check if the game already exists to decide whether to INSERT or UPDATE
    if db.execute('SELECT id FROM games WHERE id = ?', (game_id,)).fetchone():
        db.execute(
            '''UPDATE games
               SET game_state = ?,
                   wins_p1    = ?,
                   wins_p2    = ?
               WHERE id = ?''',
            (game_state_json, session_data['wins'][0], session_data['wins'][1], game_id)
        )
    else:
        # This is for creating a new game
        db.execute(
            '''INSERT INTO games
               (id, game_state, player1_name, player2_name, number_of_games, wins_p1, wins_p2)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (game_id, game_state_json, session_data['player1_name'], session_data['player2_name'],
             session_data['number_of_games'], session_data['wins'][0], session_data['wins'][1])
        )
    db.commit()


def load_game_session(game_id):
    """Loads a complete game session from the database."""
    row = get_db().execute('SELECT * FROM games WHERE id = ?', (game_id,)).fetchone()
    if row is None:
        return None

    from game import Game  # Import here to avoid circular dependencies
    game_object = Game.from_dict(json.loads(row['game_state']))

    session_data = {
        "game_logic": game_object,
        "player1_name": row['player1_name'],
        "player2_name": row['player2_name'],
        "number_of_games": row['number_of_games'],
        "wins": {
            Game.PLAYER_1: row['wins_p1'],
            Game.PLAYER_2: row['wins_p2']
        },
        "match_winner": None  # This is calculated live in the app
    }

    return session_data