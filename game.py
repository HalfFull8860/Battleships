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
    
    SHIP_NAMES = {4: "Battleship", 3: "Cruiser", 2: "Destroyer", 1: "Submarine"}

    def __init__(self, mode='vs_bot'):
        """Initializes a new game with all ships randomly placed."""
        self.mode = mode
        self.players = {
            self.PLAYER_1: {'board': Board(self.GRID_SIZE), 'ships_placed': True}, # Note: ships_placed is now True
            self.PLAYER_2: {'board': Board(self.GRID_SIZE), 'ships_placed': True}
        }
        self.status_message = "All ships placed. Player 1's turn to attack."
        self.bot_target_list = [] # Add this new list to track targets
        
        #Automatically place ships for both players ---
        self._randomly_place_ships(self.PLAYER_1)
        self._randomly_place_ships(self.PLAYER_2)

        self.current_turn = self.PLAYER_1
        self.game_over = False
        self.winner = None
        self.last_event_messages = {self.PLAYER_1: "", self.PLAYER_2: ""}
        self.status_message = "All ships placed. Player 1's turn to attack."
        
    # def _place_bot_ships(self):
    #     """Randomly places ships for the bot (Player 2)."""
    #     bot_board = self.players[self.PLAYER_2]['board']
    #     for size in self.SHIP_SIZES:
    #         placed = False
    #         while not placed:
    #             orientation = random.choice(['horizontal', 'vertical'])
    #             row = random.randint(0, self.GRID_SIZE - 1)
    #             col = random.randint(0, self.GRID_SIZE - 1)
    #             placed = bot_board.place_ship(size, row, col, orientation)
    
    def _randomly_place_ships(self, player_id):
        """Randomly places all ships for a given player."""
        player_board = self.players[player_id]['board']
        for size in self.SHIP_SIZES:
            placed = False
            while not placed:
                orientation = random.choice(['horizontal', 'vertical'])
                row = random.randint(0, self.GRID_SIZE - 1)
                col = random.randint(0, self.GRID_SIZE - 1)
                placed = player_board.place_ship(size, row, col, orientation)

    # def place_player_ship(self, player, size, row, col, orientation):
    #     """Attempts to place a ship for a given player with full validation."""
    #     if self.game_over:
    #         return False, "Game is over."
    #     if player not in self.players:
    #         return False, "Invalid player."
    #     if self.players[player]['ships_placed']:
    #         return False, "All ships have already been placed."

    #     # --- CORRECTED VALIDATION LOGIC ---
    #     if size not in self.SHIP_SIZES:
    #         return False, f"Invalid ship size. Valid sizes are: {self.SHIP_SIZES}"

    #     board = self.players[player]['board']
    #     placed_ship_sizes = [len(s['coords']) for s in board.ships]
    #     if placed_ship_sizes.count(size) >= self.SHIP_SIZES.count(size):
    #         return False, f"All ships of size {size} have already been placed."
    #     # --- END OF CORRECTION ---

    #     if not board.place_ship(size, row, col, orientation):
    #         return False, "Invalid placement. Ships may be out of bounds or overlapping."

    #     # Check if all ships for this player are placed
    #     if len(board.ships) == len(self.SHIP_SIZES):
    #         self.players[player]['ships_placed'] = True
    #         if self._are_all_ships_placed():
    #             self.status_message = "Player 1's turn to attack."
    #         else:
    #             self.status_message = f"Player {player + 1}'s ships placed. Waiting for opponent."

    #     return True, "Ship placed successfully."


    def _are_all_ships_placed(self):
        """Checks if both players have placed all their ships."""
        return all(self.players[p]['ships_placed'] for p in self.players)

    # game.py -> Replace the whole attack() method

# Replace the entire attack method in game.py with this version.

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
    
        # --- Message Logic (no changes here) ---
        if result == 'miss':
            self.last_event_messages[player] = "You missed."
            self.last_event_messages[opponent] = "The opponent fired and missed."
        elif result == 'hit':
            self.last_event_messages[player] = "You hit an enemy ship!"
            self.last_event_messages[opponent] = "Your ship has been hit!"
        elif result == 'sunk':
            ship_name = self.SHIP_NAMES.get(ship_info['size'], "ship")
            self.last_event_messages[player] = f"You sunk their {ship_name}!"
            self.last_event_messages[opponent] = f"Your {ship_name} has been sunk!"

        # --- Win Condition and Return Logic ---
        if opponent_board.all_ships_sunk():
            self.game_over = True
            self.winner = player
            self.status_message = f"Game Over! Player {player + 1} wins!"
            self.last_event_messages = {self.PLAYER_1: "", self.PLAYER_2: ""}
        
            # FIX: Return a dictionary that explicitly includes the game_over status.
            return {
                'player_attack': result,
                'ship_info': ship_info,
                'game_over': self.game_over,
                'winner': self.winner
            }
        else:
            # --- Turn Switching Logic (no changes here) ---
            self.current_turn = opponent
            self.status_message = f"Player {self.current_turn + 1}'s turn."

            if self.mode == 'vs_bot' and self.current_turn == self.PLAYER_2:
                bot_result, bot_attack_details = self._bot_attack()
                # If the bot makes a winning move, return that game_over status
                if bot_attack_details.get('game_over'):
                    return bot_attack_details
                return {'player_attack': result, 'ship_info': ship_info, 'bot_attack_info': bot_attack_details}

        return {'player_attack': result, 'ship_info': ship_info}

    # Replace the existing _bot_attack method with this one.

    # Replace the existing _bot_attack method with this one.

    def _bot_attack(self):
        """
        The bot makes a "smart" attack.
        Hunts randomly, then targets adjacent cells after a hit.
        """
        player_board = self.players[self.PLAYER_1]['board']
        attacked = False
        row, col = -1, -1

        # --- HUNT / TARGET LOGIC ---
        # If there are priority targets, enter TARGET mode
        if self.bot_target_list:
            # Take the most recent target from the list
            row, col = self.bot_target_list.pop()
        # Otherwise, enter HUNT mode
        else:
            # Hunt randomly for a cell that has not been attacked yet
            while not attacked:
                r = random.randint(0, self.GRID_SIZE - 1)
                c = random.randint(0, self.GRID_SIZE - 1)
                if (r, c) not in player_board.attacks:
                    row, col = r, c
                    attacked = True

        # --- EXECUTE ATTACK ---
        result, ship_info = player_board.receive_attack(row, col)
        bot_attack_details = {'result': result, 'row': row, 'col': col, 'ship_info': ship_info}

        # --- UPDATE STATE BASED ON RESULT ---
        # If a ship is SUNK, clear the target list and go back to HUNTING
        if result == 'sunk':
            self.bot_target_list = []
            ship_name = self.SHIP_NAMES.get(ship_info['size'], "ship")
            self.last_event_messages[self.PLAYER_1] = f"The bot sunk your {ship_name}!"
            self.last_event_messages[self.PLAYER_2] = f"You sunk their {ship_name}!"
    
        # If it's a HIT, add adjacent cells to the target list
        elif result == 'hit':
            self.last_event_messages[self.PLAYER_1] = "The bot hit your ship!"
            self.last_event_messages[self.PLAYER_2] = "You hit an enemy ship!"
            # Add valid neighbors (up, down, left, right) to the target list
            for r_offset, c_offset in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                next_r, next_c = row + r_offset, col + c_offset
                # Check if the cell is on the board and not already attacked
                if (0 <= next_r < self.GRID_SIZE and
                    0 <= next_c < self.GRID_SIZE and
                    (next_r, next_c) not in player_board.attacks):
                    self.bot_target_list.append((next_r, next_c))

        # If it's a MISS
        else:
            self.last_event_messages[self.PLAYER_1] = "The bot fired and missed."
            self.last_event_messages[self.PLAYER_2] = "You missed."

        # --- Bot Win Condition ---
        if player_board.all_ships_sunk():
            self.game_over = True
            self.winner = self.PLAYER_2
            self.status_message = "Game Over! Bot wins!"
            bot_attack_details['game_over'] = self.game_over
            bot_attack_details['winner'] = self.winner
        else:
            self.current_turn = self.PLAYER_1
            self.status_message = f"Player {self.current_turn + 1}'s turn."

        # We return bot_attack_result for the old logic, but bot_attack_details is what's used
        return result, bot_attack_details

    def get_state(self, player):
        """
        Returns the game state from the perspective of a given player.
        The opponent's ship locations are hidden.
        """
        opponent = self.PLAYER_2 if player == self.PLAYER_1 else self.PLAYER_1

        # First, get the full state dictionaries from each board
        your_board_state = self.players[player]['board'].to_dict(reveal_ships=True)
        opponent_board_state = self.players[opponent]['board'].to_dict(reveal_ships=False)

        # Now, build the final state dictionary for the API
        return {
            'player_id': player,
            'your_board': your_board_state['grid'],
            'opponent_board': opponent_board_state['grid'],
            'your_sinks': f"{opponent_board_state['sunk_ships_count']}/{opponent_board_state['total_ships']}",
            'opponent_sinks': f"{your_board_state['sunk_ships_count']}/{your_board_state['total_ships']}",
            'your_ships_placed': self.players[player]['ships_placed'],
            'opponent_ships_placed': self.players[opponent]['ships_placed'],
            'current_turn': self.current_turn,
            'game_over': self.game_over,
            'winner': self.winner,
            'last_event': self.last_event_messages[player],
            'status_message': self.status_message,
            'mode': self.mode
        }

    def reset_game(self):
        """Resets the game for the next round in a match."""
        self.players = {
            self.PLAYER_1: {'board': Board(self.GRID_SIZE), 'ships_placed': False},
            self.PLAYER_2: {'board': Board(self.GRID_SIZE), 'ships_placed': False}
        }
        self.current_turn = self.PLAYER_1
        self.game_over = False
        self.winner = None
        self.last_event_messages = {self.PLAYER_1: "", self.PLAYER_2: ""}
        self.bot_target_list = [] # Also reset the target list for a new round
    
        # FIX: Randomly place ships for BOTH players to prepare for the next round.
        # This ensures the "random placement for all" rule is consistent.
        self._randomly_place_ships(self.PLAYER_1)
        self.players[self.PLAYER_1]['ships_placed'] = True
    
        self._randomly_place_ships(self.PLAYER_2)
        self.players[self.PLAYER_2]['ships_placed'] = True

        self.status_message = "New round started! All ships have been placed. Player 1's turn."


class Board:
    """Represents a single player's 10x10 grid."""
    def __init__(self, size):
        self.size = size
        self.grid = [['~' for _ in range(size)] for _ in range(size)] # '~' for water
        self.ships = []
        self.attacks = set() # Stores (row, col) tuples of attacks
        self.sunk_ships_count = 0

    # Replace the existing place_ship method with this one.

    def place_ship(self, size, row, col, orientation):
        """
        Places a ship on the board if the location is valid and not adjacent
        to any other ships.
        """
        coords = []
        if orientation == 'horizontal':
            if col + size > self.size:
                return False  # Out of bounds
            coords = [(row, c) for c in range(col, col + size)]
        elif orientation == 'vertical':
            if row + size > self.size:
                return False  # Out of bounds
            coords = [(r, col) for r in range(row, row + size)]
        else:
            return False  # Invalid orientation

        # NEW: Validate that the ship and its surrounding area are free
        for r, c in coords:
            # Iterate through a 3x3 bounding box around each ship coordinate
            for i in range(r - 1, r + 2):
                for j in range(c - 1, c + 2):
                    # Check if the neighboring cell is within the grid bounds
                    if 0 <= i < self.size and 0 <= j < self.size:
                        # If any cell in the bounding box already has a ship, placement is invalid
                        if self.grid[i][j] == 'S':
                            return False

        # If all checks pass, place the ship
        ship = {'coords': coords, 'hits': set()}
        self.ships.append(ship)
        for r, c in coords:
            self.grid[r][c] = 'S'
        return True

    # Replace the existing receive_attack method with this one.

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
                    self.sunk_ships_count += 1
                    
                    # NEW: Reveal surrounding cells when a ship is sunk
                    # Iterate through each coordinate of the newly sunk ship
                    for r_ship, c_ship in ship['coords']:
                        # Iterate through the 3x3 bounding box around it
                        for i in range(r_ship - 1, r_ship + 2):
                            for j in range(c_ship - 1, c_ship + 2):
                                # Check if the cell is within the grid bounds
                                if 0 <= i < self.size and 0 <= j < self.size:
                                    # Add the surrounding water cells to the set of attacks
                                    # The existing to_dict() method will handle displaying them
                                    self.attacks.add((i, j))
                    
                    return 'sunk', {'size': len(ship['coords']), 'coords': ship['coords']}
                return 'hit', None

        return 'miss', None

    def all_ships_sunk(self):
        """Checks if all ships on the board have been sunk."""
        if not self.ships: return False # No ships placed yet
        return all(len(s['hits']) == len(s['coords']) for s in self.ships)

    # In game.py, inside the Board class

    def to_dict(self, reveal_ships=False):
        """
        Converts the board state to a dictionary for JSON serialization.
        Implements advanced "fog of war" display logic.
        """
        # If it's the opponent's board, start with '?' for unknown cells.
        if not reveal_ships:
            display_grid = [['?' for _ in range(self.size)] for _ in range(self.size)]
        else:
            # For your own board, start with '~' for water.
            display_grid = [['~' for _ in range(self.size)] for _ in range(self.size)]
            # And show your own ships.
            for ship in self.ships:
                for r, c in ship['coords']:
                    display_grid[r][c] = 'S'
    
        # Handle misses first
        for r, c in self.attacks:
            if self.grid[r][c] == '~': # If an attacked cell is water in the master grid
                # On your own board, this shows as 'O'. On the opponent's, it changes '?' to '~'.
                display_grid[r][c] = '~' if not reveal_ships else 'O'

        # Handle hits and sunk ships
        for ship in self.ships:
            is_sunk = len(ship['hits']) == len(ship['coords'])
            for r, c in ship['hits']:
                if is_sunk:
                    display_grid[r][c] = 'X' # Uppercase 'X' for a fully sunk ship
                else:
                    display_grid[r][c] = 'x' # Lowercase 'x' for a partially hit ship

        return {
            'grid': display_grid,
            'sunk_ships_count': self.sunk_ships_count,
            'total_ships': len(Game.SHIP_SIZES)
        }