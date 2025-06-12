# game.py
# This file contains the core logic for the Battleship game engine.
# It is completely decoupled from the web server and manages all game rules and state for a single round.

import random

class Game:
    """
    Manages the entire state of a single Battleship round, including player boards,
    turns, AI behavior, and win conditions.
    """
    # --- Class-level constants for game rules ---
    PLAYER_1 = 0
    PLAYER_2 = 1
    SHIP_SIZES = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1] # Standard Battleship ship lengths
    GRID_SIZE = 10
    
    SHIP_NAMES = {4: "Battleship", 3: "Cruiser", 2: "Destroyer", 1: "Submarine"}

    def __init__(self, mode='vs_bot'):
        """
        Initializes a new game round.
        By default, all ships are randomly placed on the boards for both players.
        """
        self.mode = mode
        self.players = {
            self.PLAYER_1: {'board': Board(self.GRID_SIZE), 'ships_placed': True},
            self.PLAYER_2: {'board': Board(self.GRID_SIZE), 'ships_placed': True}
        }
        self.bot_target_list = [] # A priority queue for the bot's "Target" mode.
    
        #Automatically place ships for both players ---
        self._randomly_place_ships(self.PLAYER_1)
        self._randomly_place_ships(self.PLAYER_2)

        # Initialize game state variables.
        self.current_turn = self.PLAYER_1
        self.game_over = False
        self.winner = None
        self.last_event_messages = {self.PLAYER_1: "", self.PLAYER_2: ""}
        self.status_message = "All ships placed. Player 1's turn to attack."
    
    def _randomly_place_ships(self, player_id):
        """Randomly places all ships for a given player."""
        player_board = self.players[player_id]['board']
        for size in self.SHIP_SIZES:
            placed = False
            # Loop until a valid position is found for the current ship size.
            while not placed:
                orientation = random.choice(['horizontal', 'vertical'])
                row = random.randint(0, self.GRID_SIZE - 1)
                col = random.randint(0, self.GRID_SIZE - 1)
                # The Board class's place_ship method handles all placement validation.
                placed = player_board.place_ship(size, row, col, orientation)

    def _are_all_ships_placed(self):
        """A utility to check if both players have finished placing their ships."""
        return all(self.players[p]['ships_placed'] for p in self.players)

    def attack(self, player, row, col):
        """
        Processes a single attack, updates the game state, and handles the "hit and go again" rule.
        If playing against a bot and the player misses, this method also triggers the bot's entire turn.
        """
        # --- Pre-attack validation ---
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

        # --- Update status messages for both players based on the attack result ---
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

        # --- Win and Turn Logic ---
        response = {'player_attack': result, 'ship_info': ship_info}
        if opponent_board.all_ships_sunk():
            self.game_over = True
            self.winner = player
            self.status_message = f"Game Over! Player {player + 1} wins!"
            response['game_over'] = self.game_over
            response['winner'] = self.winner
        else:
            if result == 'miss':
                # On a miss, switch the turn to the opponent.
                self.current_turn = opponent
                self.status_message = f"Player {self.current_turn + 1}'s turn."
                # If it's now the bot's turn, execute its entire turn sequence.
                if self.mode == 'vs_bot' and self.current_turn == self.PLAYER_2:
                    response['bot_turns'] = self._execute_bot_turn()
            else:
                # On a hit or sunk, the current player gets another turn.
                self.status_message = f"Hit! Player {player + 1} gets another turn."

        return response

    def _execute_bot_turn(self):
        """Handles the bot's entire turn, allowing it to attack repeatedly until it misses or wins."""
        turn_summary = []
        # The bot continues to attack as long as it's its turn and the game isn't over.
        while self.current_turn == self.PLAYER_2 and not self.game_over:
            shot_result, shot_details = self._bot_single_attack()
            turn_summary.append(shot_details)

            # If the bot makes a winning move, break the loop.
            if shot_details.get('game_over'):
                break
        
            # If the bot misses, its turn is over. Switch back to the human player.
            if shot_result == 'miss':
                self.current_turn = self.PLAYER_1
                self.status_message = f"Player {self.PLAYER_1 + 1}'s turn."
                break

        return turn_summary

    def _bot_single_attack(self):
        """Makes one "smart" attack for the bot using Hunt/Target logic."""
        player_board = self.players[self.PLAYER_1]['board']
        row, col = -1, -1

        """Makes one "smart" attack for the bot using Hunt/Target logic."""
        if self.bot_target_list:
            row, col = self.bot_target_list.pop()
        # HUNT mode: Otherwise, fire at a random, un-attacked cell.    
        else:
            while True:
                r = random.randint(0, self.GRID_SIZE - 1)
                c = random.randint(0, self.GRID_SIZE - 1)
                if (r, c) not in player_board.attacks:
                    row, col = r, c
                    break

        result, ship_info = player_board.receive_attack(row, col)
        shot_details = {'result': result, 'row': row, 'col': col, 'ship_info': ship_info}

        # Update bot's strategy based on the result. Update event messages for display on the frontend.
        if result == 'sunk':
            self.bot_target_list = [] # A sink resets the targeting logic.
            ship_name = self.SHIP_NAMES.get(ship_info['size'], "ship")
            self.last_event_messages[self.PLAYER_1] = f"The bot sunk your {ship_name}!"
            self.last_event_messages[self.PLAYER_2] = f"You sunk their {ship_name}!"
        elif result == 'hit':
            # On a hit, add valid adjacent cells to the target list.
            self.last_event_messages[self.PLAYER_1] = "The bot hit your ship!"
            self.last_event_messages[self.PLAYER_2] = "You hit an enemy ship!"
            for r_offset, c_offset in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                next_r, next_c = row + r_offset, col + c_offset
                if (0 <= next_r < self.GRID_SIZE and 0 <= next_c < self.GRID_SIZE and (next_r, next_c) not in player_board.attacks):
                    if (next_r, next_c) not in self.bot_target_list:
                        self.bot_target_list.append((next_r, next_c))
        else: # Miss
            self.last_event_messages[self.PLAYER_1] = "The bot fired and missed."
            self.last_event_messages[self.PLAYER_2] = "You missed."

        # Check if the bot's attack was a winning move.
        if player_board.all_ships_sunk():
            self.game_over = True
            self.winner = self.PLAYER_2
            self.status_message = "Game Over! Bot wins!"
            shot_details['game_over'] = self.game_over
            shot_details['winner'] = self.winner

        return result, shot_details



    def get_state(self, player):
        """
        Compiles the complete game state from the perspective of a single player.
        This ensures that a player only sees their own un-hit ships.
        """
        opponent = self.PLAYER_2 if player == self.PLAYER_1 else self.PLAYER_1

        # Get the state of each player's board (revealing ships only for the current player).
        your_board_state = self.players[player]['board'].to_dict(reveal_ships=True)
        opponent_board_state = self.players[opponent]['board'].to_dict(reveal_ships=False)

        # Assemble the final state dictionary for the API.
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
        """Resets the game state for the next round in a multi-game match."""
        # Create fresh boards for both players.
        self.players = {
            self.PLAYER_1: {'board': Board(self.GRID_SIZE), 'ships_placed': False},
            self.PLAYER_2: {'board': Board(self.GRID_SIZE), 'ships_placed': False}
        }
        # Reset all game state variables.
        self.current_turn = self.PLAYER_1
        self.game_over = False
        self.winner = None
        self.last_event_messages = {self.PLAYER_1: "", self.PLAYER_2: ""}
        self.bot_target_list = [] # Also reset the target list for a new round
    
        # Randomly place ships for both players for the new round.
        self._randomly_place_ships(self.PLAYER_1)
        self.players[self.PLAYER_1]['ships_placed'] = True
        self._randomly_place_ships(self.PLAYER_2)
        self.players[self.PLAYER_2]['ships_placed'] = True

        self.status_message = "New round started! All ships have been placed. Player 1's turn."


class Board:
    """Represents a single player's 10x10 grid, their ships, and attack history."""
    def __init__(self, size):
        """Initializes an empty board."""
        self.size = size
        self.grid = [['~' for _ in range(size)] for _ in range(size)] # '~' for water
        self.ships = []
        self.attacks = set() # Stores (row, col) tuples of attacks
        self.sunk_ships_count = 0

    def place_ship(self, size, row, col, orientation):
        """
        Places a ship on the board if the location is valid and not adjacent to other ships.
        This enforces the "1-cell gap" rule.
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

        # Validate that the ship's coordinates and its entire surrounding area are free.
        for r, c in coords:
            #  Iterate through a 3x3 bounding box around each part of the ship.
            for i in range(r - 1, r + 2):
                for j in range(c - 1, c + 2):
                    # Check if the neighboring cell is within the grid bounds.
                    if 0 <= i < self.size and 0 <= j < self.size:
                        # If any cell in the bounding box already has a ship, placement is invalid
                        if self.grid[i][j] == 'S':
                            return False

        # If all checks pass, add the ship to the board state.
        ship = {'coords': coords, 'hits': set()}
        self.ships.append(ship)
        for r, c in coords:
            self.grid[r][c] = 'S' # Mark the ship's location on the master grid.
        return True

    # Replace the existing receive_attack method with this one.

    def receive_attack(self, row, col):
        """Records an attack, determines the result, and reveals surrounding cells on a sink."""
        if (row, col) in self.attacks:
            return 'already_attacked', None

        self.attacks.add((row, col))

        # Check if the attack hit any ship.
        for ship in self.ships:
            if (row, col) in ship['coords']:
                ship['hits'].add((row, col))
                # Check if the ship is now sunk
                if len(ship['hits']) == len(ship['coords']):
                    self.sunk_ships_count += 1
                    
                    # When a ship is sunk, automatically mark all surrounding cells as attacked.
                    # This reveals the water around the sunk ship to the players.
                    for r_ship, c_ship in ship['coords']:
                        for i in range(r_ship - 1, r_ship + 2):
                            for j in range(c_ship - 1, c_ship + 2):
                                if 0 <= i < self.size and 0 <= j < self.size:
                                    self.attacks.add((i, j))
                    
                    return 'sunk', {'size': len(ship['coords']), 'coords': ship['coords']}
                return 'hit', None

        # If no ship was hit, it's a miss.
        return 'miss', None

    def all_ships_sunk(self):
        """Checks if all ships on the board have been sunk."""
        if not self.ships: return False
        return all(len(s['hits']) == len(s['coords']) for s in self.ships)

    def to_dict(self, reveal_ships=False):
        """
        Converts the board state to a dictionary for JSON serialization.
        This method implements the "fog of war" by hiding opponent ships.
        """
        # For an opponent's board, start with all cells hidden as '?'.
        if not reveal_ships:
            display_grid = [['?' for _ in range(self.size)] for _ in range(self.size)]
        # For your own board, show the water '~' and your ship locations 'S'.
        else:
            display_grid = [['~' for _ in range(self.size)] for _ in range(self.size)]
            for ship in self.ships:
                for r, c in ship['coords']:
                    display_grid[r][c] = 'S'
    
        # Mark all misses on the display grid.
        for r, c in self.attacks:
            if self.grid[r][c] == '~':
                # A miss on an opponent's board reveals water '~'.
                # A miss on your own board is marked as 'O'.
                display_grid[r][c] = '~' if not reveal_ships else 'O'

        # Mark all hits and sunk ships on the display grid.
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