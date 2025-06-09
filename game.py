# game.py
# This file contains the core logic for the Battleship game.

import random

class Game:
    """
    Manages the entire game state, including player boards, turns, and game mode.
    """
    PLAYER_1 = 0
    PLAYER_2 = 1
    SHIP_SIZES = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1] # Standard Battleship ship lengths
    GRID_SIZE = 10

    def __init__(self, mode='vs_bot'):
        """Initializes a new game."""
        self.mode = mode
        self.players = {
            self.PLAYER_1: {'board': Board(self.GRID_SIZE), 'ships_placed': False},
            self.PLAYER_2: {'board': Board(self.GRID_SIZE), 'ships_placed': False}
        }
        self.current_turn = self.PLAYER_1
        self.game_over = False
        self.winner = None
        self.status_message = "Player 1, place your ships."

        # If it's a bot game, place the bot's ships automatically.
        if self.mode == 'vs_bot':
            self._place_bot_ships()
            self.players[self.PLAYER_2]['ships_placed'] = True
            self.status_message = "Player 1, place your ships to begin."

    def _place_bot_ships(self):
        """Randomly places ships for the bot (Player 2)."""
        bot_board = self.players[self.PLAYER_2]['board']
        for size in self.SHIP_SIZES:
            placed = False
            while not placed:
                orientation = random.choice(['horizontal', 'vertical'])
                row = random.randint(0, self.GRID_SIZE - 1)
                col = random.randint(0, self.GRID_SIZE - 1)
                placed = bot_board.place_ship(size, row, col, orientation)

    def place_player_ship(self, player, size, row, col, orientation):
        """Attempts to place a ship for a given player."""
        if self.game_over:
            return False, "Game is over."
        if player not in self.players:
            return False, "Invalid player."
        if self.players[player]['ships_placed']:
            return False, "All ships have already been placed."

        board = self.players[player]['board']
        if not board.place_ship(size, row, col, orientation):
            return False, "Invalid placement. Ships may be out of bounds or overlapping."

        # Check if all ships for this player are placed
        if len(board.ships) == len(self.SHIP_SIZES):
            self.players[player]['ships_placed'] = True
            if self._are_all_ships_placed():
                self.status_message = "Player 1's turn to attack."
            else:
                 self.status_message = f"Player {player + 1}'s ships placed. Waiting for opponent."

        return True, "Ship placed successfully."


    def _are_all_ships_placed(self):
        """Checks if both players have placed all their ships."""
        return all(self.players[p]['ships_placed'] for p in self.players)

    def attack(self, player, row, col):
        """Processes an attack from one player to another."""
        if self.game_over:
            return {'error': 'Game is over.'}
        if not self._are_all_ships_placed():
            return {'error': 'Not all ships have been placed yet.'}
        if player != self.current_turn:
            return {'error': 'It is not your turn.'}

        opponent = self.PLAYER_2 if player == self.PLAYER_1 else self.PLAYER_1
        opponent_board = self.players[opponent]['board']

        if not (0 <= row < self.GRID_SIZE and 0 <= col < self.GRID_SIZE):
            return {'error': 'Attack is out of bounds.'}

        result, ship_info = opponent_board.receive_attack(row, col)

        if result == 'already_attacked':
             return {'error': 'This cell has already been attacked.'}

        # Check for win condition
        if opponent_board.all_ships_sunk():
            self.game_over = True
            self.winner = player
            self.status_message = f"Game Over! Player {player + 1} wins!"
        else:
            # Switch turns
            self.current_turn = opponent
            self.status_message = f"Player {self.current_turn + 1}'s turn."

            # If vs_bot mode and it's now the bot's turn
            if self.mode == 'vs_bot' and self.current_turn == self.PLAYER_2:
                bot_result = self._bot_attack()
                # The bot's result will be part of the response
                return {'player_attack': result, 'ship_info': ship_info, 'bot_attack_info': bot_result}

        return {'player_attack': result, 'ship_info': ship_info}


    def _bot_attack(self):
        """The bot makes a random, valid attack."""
        player_board = self.players[self.PLAYER_1]['board']
        attacked = False
        bot_attack_result = {}

        while not attacked:
            row = random.randint(0, self.GRID_SIZE - 1)
            col = random.randint(0, self.GRID_SIZE - 1)

            # Check if the cell has not been attacked before
            if (row, col) not in player_board.attacks:
                result, ship_info = player_board.receive_attack(row, col)
                attacked = True
                bot_attack_result = {
                    'result': result,
                    'row': row,
                    'col': col,
                    'ship_info': ship_info
                }

        # Check for bot win condition
        if player_board.all_ships_sunk():
            self.game_over = True
            self.winner = self.PLAYER_2
            self.status_message = "Game Over! Bot wins!"
        else:
            # Switch turn back to the player
            self.current_turn = self.PLAYER_1
            self.status_message = f"Player {self.current_turn + 1}'s turn."

        return bot_attack_result

    def get_state(self, player):
        """
        Returns the game state from the perspective of a given player.
        The opponent's ship locations are hidden.
        """
        opponent = self.PLAYER_2 if player == self.PLAYER_1 else self.PLAYER_1

        return {
            'player_id': player,
            'your_board': self.players[player]['board'].to_dict(reveal_ships=True),
            'opponent_board': self.players[opponent]['board'].to_dict(reveal_ships=False),
            'your_ships_placed': self.players[player]['ships_placed'],
            'opponent_ships_placed': self.players[opponent]['ships_placed'],
            'current_turn': self.current_turn,
            'game_over': self.game_over,
            'winner': self.winner,
            'status_message': self.status_message,
            'mode': self.mode
        }


class Board:
    """Represents a single player's 10x10 grid."""
    def __init__(self, size):
        self.size = size
        self.grid = [['~' for _ in range(size)] for _ in range(size)] # '~' for water
        self.ships = []
        self.attacks = set() # Stores (row, col) tuples of attacks

    def place_ship(self, size, row, col, orientation):
        """Places a ship on the board if the location is valid."""
        coords = []
        if orientation == 'horizontal':
            if col + size > self.size:
                return False # Out of bounds
            coords = [(row, c) for c in range(col, col + size)]
        elif orientation == 'vertical':
            if row + size > self.size:
                return False # Out of bounds
            coords = [(r, col) for r in range(row, row + size)]
        else:
            return False # Invalid orientation

        # Check for collisions with other ships
        for r, c in coords:
            if self.grid[r][c] == 'S': # 'S' for ship
                return False

        # Place the ship
        ship = {'coords': coords, 'hits': set()}
        self.ships.append(ship)
        for r, c in coords:
            self.grid[r][c] = 'S'
        return True

    def receive_attack(self, row, col):
        """Records an attack and returns the result (hit, miss, or sunk)."""
        if (row, col) in self.attacks:
            return 'already_attacked', None

        self.attacks.add((row, col))

        # Check if a ship was hit
        for ship in self.ships:
            if (row, col) in ship['coords']:
                ship['hits'].add((row, col))
                # Check if the ship is now sunk
                if len(ship['hits']) == len(ship['coords']):
                    return 'sunk', {'size': len(ship['coords']), 'coords': ship['coords']}
                return 'hit', None

        return 'miss', None

    def all_ships_sunk(self):
        """Checks if all ships on the board have been sunk."""
        if not self.ships: return False # No ships placed yet
        return all(len(s['hits']) == len(s['coords']) for s in self.ships)

    def to_dict(self, reveal_ships=False):
        """
        Converts the board state to a dictionary for JSON serialization.
        If reveal_ships is False, ship locations are hidden unless they are hit.
        """
        display_grid = [['~' for _ in range(self.size)] for _ in range(self.size)]
        for r in range(self.size):
            for c in range(self.size):
                if (r, c) in self.attacks:
                    if self.grid[r][c] == 'S':
                        display_grid[r][c] = 'X' # Hit
                    else:
                        display_grid[r][c] = 'O' # Miss
                elif reveal_ships and self.grid[r][c] == 'S':
                    display_grid[r][c] = 'S'
        return {'grid': display_grid, 'ships_sunk': self.all_ships_sunk()}