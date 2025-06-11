# game.py

import random


class Game:
    PLAYER_1 = 0
    PLAYER_2 = 1
    SHIP_SIZES = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
    GRID_SIZE = 10
    SHIP_NAMES = {4: "Battleship", 3: "Cruiser", 2: "Destroyer", 1: "Submarine"}

    def __init__(self, mode='vs_bot', placement='random'):
        self.mode = mode
        self.placement_mode = placement
        self.players = {
            p: {'board': Board(self.GRID_SIZE), 'ships_placed': False}
            for p in [self.PLAYER_1, self.PLAYER_2]
        }
        self.current_turn = self.PLAYER_1
        self.game_over = False
        self.winner = None
        self.last_event_messages = {self.PLAYER_1: "", self.PLAYER_2: ""}
        self.status_message = "Game starting. Place your ships."

        if self.placement_mode == 'random':
            self._randomly_place_ships(self.PLAYER_1)
            self._randomly_place_ships(self.PLAYER_2)
            self.players[self.PLAYER_1]['ships_placed'] = True
            self.players[self.PLAYER_2]['ships_placed'] = True
            self.status_message = "All ships randomly placed. Player 1's turn."
        elif self.mode == 'vs_bot':
            self._randomly_place_ships(self.PLAYER_2)
            self.players[self.PLAYER_2]['ships_placed'] = True
            self.status_message = "Player 1, place your ships to begin."

    def _randomly_place_ships(self, player_id):
        player_board = self.players[player_id]['board']
        for size in self.SHIP_SIZES:
            placed = False
            while not placed:
                orientation = random.choice(['horizontal', 'vertical'])
                row = random.randint(0, self.GRID_SIZE - 1)
                col = random.randint(0, self.GRID_SIZE - 1)
                placed = player_board.place_ship(size, row, col, orientation)

    def place_player_ship(self, player, size, row, col, orientation):
        if self.game_over: return False, "Game is over."
        if self.placement_mode == 'random': return False, "Cannot place ships in random placement mode."
        if self.players[player]['ships_placed']: return False, "All your ships have already been placed."

        board = self.players[player]['board']
        placed_ship_sizes = [len(s['coords']) for s in board.ships]
        if placed_ship_sizes.count(size) >= self.SHIP_SIZES.count(size):
            return False, f"All ships of size {size} have been placed."

        if not board.place_ship(size, row, col, orientation):
            return False, "Invalid placement. Ships may be out of bounds or overlapping."

        if len(board.ships) == len(self.SHIP_SIZES):
            self.players[player]['ships_placed'] = True
            self.status_message = "All ships placed. Player 1's turn." if self._are_all_ships_placed() else f"Player {player + 1} ships placed."
        return True, "Ship placed successfully."

    def _are_all_ships_placed(self):
        return all(p['ships_placed'] for p in self.players.values())

    def attack(self, player, row, col):
        if self.game_over: return {'error': 'Game is over.'}
        if not self._are_all_ships_placed(): return {'error': 'Not all ships have been placed yet.'}
        if player != self.current_turn: return {'error': 'It is not your turn.'}

        opponent_id = self.PLAYER_2 if player == self.PLAYER_1 else self.PLAYER_1
        result, ship_info = self.players[opponent_id]['board'].receive_attack(row, col)

        if result == 'already_attacked': return {'error': 'This cell has already been attacked.'}

        self._set_attack_messages(player, opponent_id, result, ship_info)

        if self.players[opponent_id]['board'].all_ships_sunk():
            self.game_over = True
            self.winner = player
            self.status_message = f"Round Over! Player {player + 1} wins this round!"
        else:
            self.current_turn = opponent_id
            self.status_message = f"Player {self.current_turn + 1}'s turn."
            if self.mode == 'vs_bot' and self.current_turn == self.PLAYER_2:
                bot_attack_details = self._bot_attack()
                return {'player_attack': result, 'ship_info': ship_info, 'bot_attack_info': bot_attack_details,
                        'game_over': self.game_over, 'winner': self.winner}

        return {'player_attack': result, 'ship_info': ship_info, 'game_over': self.game_over, 'winner': self.winner}

    def _bot_attack(self):
        while True:
            row, col = random.randint(0, self.GRID_SIZE - 1), random.randint(0, self.GRID_SIZE - 1)
            if (row, col) not in self.players[self.PLAYER_1]['board'].attacks: break

        result, ship_info = self.players[self.PLAYER_1]['board'].receive_attack(row, col)
        self._set_attack_messages(self.PLAYER_2, self.PLAYER_1, result, ship_info)

        if self.players[self.PLAYER_1]['board'].all_ships_sunk():
            self.game_over = True
            self.winner = self.PLAYER_2
            self.status_message = "Round Over! The Bot wins this round!"
        else:
            self.current_turn = self.PLAYER_1
            self.status_message = f"Player {self.current_turn + 1}'s turn."
        return {'result': result, 'row': row, 'col': col, 'ship_info': ship_info}

    def _set_attack_messages(self, attacker, defender, result, ship_info):
        if result == 'miss':
            self.last_event_messages[attacker] = "You missed."
            self.last_event_messages[defender] = "The opponent fired and missed."
        elif result == 'hit':
            self.last_event_messages[attacker] = "You hit an enemy ship!"
            self.last_event_messages[defender] = "Your ship has been hit!"
        elif result == 'sunk':
            ship_name = self.SHIP_NAMES.get(ship_info['size'], "ship")
            self.last_event_messages[attacker] = f"You sunk their {ship_name}!"
            self.last_event_messages[defender] = f"Your {ship_name} has been sunk!"

    def reset_game(self):
        self.__init__(self.mode, self.placement_mode)

    def get_state(self, player_id):
        opponent_id = self.PLAYER_2 if player_id == self.PLAYER_1 else self.PLAYER_1
        your_board_state = self.players[player_id]['board'].to_dict(reveal_ships=True)
        opponent_board_state = self.players[opponent_id]['board'].to_dict(reveal_ships=False)
        return {
            'your_board': your_board_state['grid'],
            'opponent_board': opponent_board_state['grid'],
            'your_sinks': f"{opponent_board_state['sunk_ships_count']}/{opponent_board_state['total_ships']}",
            'opponent_sinks': f"{your_board_state['sunk_ships_count']}/{your_board_state['total_ships']}",
            'your_ships_placed': self.players[player_id]['ships_placed'],
            'status_message': self.status_message,
            'last_event': self.last_event_messages[player_id],
            'current_turn': self.current_turn,
            'game_over': self.game_over,
            'winner': self.winner,
            'mode': self.mode,
            'placement_mode': self.placement_mode
        }

    def to_dict(self):
        return {
            'mode': self.mode,
            'placement_mode': self.placement_mode,
            'players': {p: {'board': self.players[p]['board'].to_dict(full_state=True),
                            'ships_placed': self.players[p]['ships_placed']} for p in self.players},
            'current_turn': self.current_turn,
            'game_over': self.game_over,
            'winner': self.winner,
            'status_message': self.status_message,
            'last_event_messages': self.last_event_messages
        }

    @classmethod
    def from_dict(cls, data):
        """Creates a Game instance from a dictionary, fixing key types."""
        # This is the corrected from_dict method
        game = cls(data['mode'], data.get('placement_mode', 'random'))
        game.players = {int(p): {'board': Board.from_dict(data['players'][p]['board']),
                                 'ships_placed': data['players'][p]['ships_placed']} for p in data['players']}
        game.current_turn = data['current_turn']
        game.game_over = data['game_over']
        game.winner = data['winner']
        game.status_message = data['status_message']

        # --- THIS IS THE FIX ---
        # Rebuild the dictionary, converting string keys ("0", "1") to integers (0, 1)
        loaded_messages = data.get('last_event_messages', {})
        game.last_event_messages = {int(k): v for k, v in loaded_messages.items()}
        # --- END OF FIX ---

        return game


class Board:
    def __init__(self, size):
        self.size = size
        self.grid = [['~' for _ in range(size)] for _ in range(size)]
        self.ships = []
        self.attacks = set()

    def place_ship(self, size, row, col, orientation):
        coords = []
        if orientation == 'horizontal':
            if col + size > self.size: return False
            coords = [(row, c) for c in range(col, col + size)]
        elif orientation == 'vertical':
            if row + size > self.size: return False
            coords = [(r, col) for r in range(row, row + size)]
        else:
            return False
        if any(self.grid[r][c] == 'S' for r, c in coords): return False

        ship = {'coords': coords, 'hits': set()}
        self.ships.append(ship)
        for r, c in coords:
            self.grid[r][c] = 'S'
        return True

    def receive_attack(self, row, col):
        if (row, col) in self.attacks: return 'already_attacked', None
        self.attacks.add((row, col))
        for ship in self.ships:
            if (row, col) in ship['coords']:
                ship['hits'].add((row, col))
                if len(ship['hits']) == len(ship['coords']):
                    return 'sunk', {'size': len(ship['coords']), 'coords': ship['coords']}
                return 'hit', None
        return 'miss', None

    def all_ships_sunk(self):
        if not self.ships: return False
        return all(len(s['hits']) == len(s['coords']) for s in self.ships)

    def to_dict(self, reveal_ships=False, full_state=False):
        if full_state:
            return {
                'size': self.size, 'grid': self.grid,
                'ships': [{'coords': [list(c) for c in s['coords']], 'hits': [list(h) for h in s['hits']]} for s in
                          self.ships],
                'attacks': [list(a) for a in self.attacks]
            }

        display_grid = [['?' for _ in range(self.size)] if not reveal_ships else list(row) for row in self.grid]
        if reveal_ships:
            for r in range(self.size):
                for c in range(self.size):
                    if (r, c) in self.attacks and self.grid[r][c] == '~':
                        display_grid[r][c] = 'O'  # Show misses on your own board

        for ship in self.ships:
            is_sunk = len(ship['hits']) == len(ship['coords'])
            for r, c in ship['coords']:
                if (r, c) in self.attacks:
                    if is_sunk:
                        display_grid[r][c] = 'X'
                    elif reveal_ships:
                        display_grid[r][c] = 'x'  # Show partial hits on own board
                    else:
                        display_grid[r][c] = 'x'  # Show partial hits on opponent board
                elif not reveal_ships:
                    if (r, c) in self.attacks:
                        display_grid[r][c] = '~'  # reveal water on miss
                    else:
                        display_grid[r][c] = '?'  # hide water

        return {
            'grid': display_grid,
            'sunk_ships_count': sum(1 for s in self.ships if len(s['hits']) == len(s['coords'])),
            'total_ships': len(Game.SHIP_SIZES)
        }

    @classmethod
    def from_dict(cls, data):
        board = cls(data['size'])
        board.grid = data['grid']
        board.attacks = set(tuple(a) for a in data['attacks'])
        board.ships = [{'coords': [tuple(c) for c in s['coords']], 'hits': set(tuple(h) for h in s['hits'])} for s in
                       data['ships']]
        return board