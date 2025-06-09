# game_terminal.py
# This file allows you to play the Battleship game in your terminal.
# It uses the game logic from game.py.

import os
import time
from game import Game  # Make sure game.py is in the same directory


def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_boards(game, player_id):
    """Prints the boards side-by-side for the current player's view with row/column labels."""
    player_view = game.get_state(player_id)
    your_board = player_view['your_board']['grid']
    opponent_board = player_view['opponent_board']['grid']

    print("=" * 40)
    print(f"PLAYER {player_id + 1}'s TURN")
    print(f"Status: {player_view['status_message']}")
    print("=" * 40)

    # Column Headers (A, B, C...)
    col_headers = " ".join([chr(ord('A') + i) for i in range(10)])

    print("         YOUR BOARD" + " " * 15 + "OPPONENT'S BOARD")
    print("   " + col_headers + " " * 12 + "   " + col_headers)
    print("  +" + "-" * 21 + "+" + " " * 10 + "  +" + "-" * 21 + "+")

    for i in range(10):
        # Your board row with row number
        your_row_str = f"{i} | " + " ".join(your_board[i]) + " |"

        # Opponent board row with row number
        opponent_row_str = f"{i} | " + " ".join(opponent_board[i]) + " |"

        print(your_row_str + " " * 10 + opponent_row_str)

    print("  +" + "-" * 21 + "+" + " " * 10 + "  +" + "-" * 21 + "+")
    print("\n")


def get_validated_input(prompt, validation_type):
    """Safely gets and validates player input for rows or columns."""
    while True:
        try:
            value = input(prompt).upper()  # Use upper() for case-insensitivity
            if validation_type == 'row':
                num = int(value)
                if 0 <= num <= 9:
                    return num
                else:
                    print("Invalid input. Row must be between 0 and 9.")
            elif validation_type == 'col':
                if 'A' <= value <= 'J' and len(value) == 1:
                    # Convert letter 'A'-'J' to number 0-9
                    return ord(value) - ord('A')
                else:
                    print("Invalid input. Column must be a letter from A to J.")
            elif validation_type == 'orientation':
                value = value.lower()
                if value in ['horizontal', 'vertical', 'h', 'v']:
                    return 'horizontal' if value.startswith('h') else 'vertical'
                else:
                    print("Invalid input. Please enter 'horizontal' or 'vertical'.")

        except ValueError:
            print("Invalid input. Please enter a valid number for the row.")
        except KeyboardInterrupt:
            print("\nExiting game.")
            exit()


def place_ships_for_player(game, player_id):
    """Guides a player through placing their ships."""
    for ship_size in game.SHIP_SIZES:
        placed = False
        while not placed:
            clear_screen()
            print_boards(game, player_id)
            print(f"Player {player_id + 1}, place your ship of size {ship_size}.")

            try:
                row = get_validated_input("Enter starting row (0-9): ", 'row')
                col = get_validated_input("Enter starting column (A-J): ", 'col')
                orientation = get_validated_input("Enter orientation (h/v): ", 'orientation')

                success, message = game.place_player_ship(player_id, ship_size, row, col, orientation)

                if success:
                    print(message)
                    placed = True
                    time.sleep(1)
                else:
                    print(f"Error: {message} Please try again.")
                    time.sleep(2)
            except Exception as e:
                print(f"An error occurred: {e}")
                time.sleep(2)


def main():
    """The main game loop for the terminal application."""
    clear_screen()
    print("*" * 30)
    print("   WELCOME TO BATTLESHIP!   ")
    print("*" * 30)

    mode = ""
    while mode not in ['1', '2']:
        mode = input("Select game mode:\n1. Player vs. Bot\n2. Player vs. Player\nEnter choice (1 or 2): ")

    game_mode = 'vs_bot' if mode == '1' else 'vs_player'
    game = Game(mode=game_mode)

    # --- Ship Placement Phase ---
    place_ships_for_player(game, Game.PLAYER_1)

    if game.mode == 'vs_player':
        clear_screen()
        input("Player 1, your ships are placed. Press Enter to clear the screen for Player 2...")
        clear_screen()
        place_ships_for_player(game, Game.PLAYER_2)
        clear_screen()
        input("Player 2, your ships are placed. Press Enter to begin the game...")

    # --- Attack Phase ---
    while not game.game_over:
        clear_screen()
        current_player = game.current_turn
        print_boards(game, current_player)

        print(f"Player {current_player + 1}, it's your turn to attack.")

        try:
            row = get_validated_input("Enter attack row (0-9): ", 'row')
            col = get_validated_input("Enter attack column (A-J): ", 'col')

            attack_result = game.attack(current_player, row, col)

            if 'error' in attack_result:
                print(f"Error: {attack_result['error']}")
                time.sleep(2)
                continue

            clear_screen()
            print_boards(game, current_player)
            print("Processing attack...")
            time.sleep(2)

            if 'bot_attack_info' in attack_result and attack_result['bot_attack_info']:
                bot_info = attack_result['bot_attack_info']
                bot_col_letter = chr(ord('A') + bot_info['col'])
                print(f"Bot attacked at ({bot_info['row']}, {bot_col_letter}) and it was a {bot_info['result']}!")
                time.sleep(3)

        except Exception as e:
            print(f"A critical error occurred: {e}")
            time.sleep(3)

    # --- Game Over ---
    clear_screen()
    print("*" * 30)
    print("         GAME OVER!         ")
    print("*" * 30)
    winner_name = "Bot" if game.mode == 'vs_bot' and game.winner == 1 else f"Player {game.winner + 1}"
    print(f"Congratulations {winner_name}! You are the winner!")
    print("\nFinal Boards:\n")

    final_p1_state = game.get_state(Game.PLAYER_1)
    final_p2_board_revealed = game.players[Game.PLAYER_2]['board'].to_dict(reveal_ships=True)['grid']
    final_p1_state['opponent_board']['grid'] = final_p2_board_revealed

    # We need to reveal Player 1's board too for the final view
    final_p1_state['your_board']['grid'] = game.players[Game.PLAYER_1]['board'].to_dict(reveal_ships=True)['grid']

    # Temporarily adjust the game object to use our fully revealed state
    game.get_state = lambda p: final_p1_state
    print_boards(game, Game.PLAYER_1)


if __name__ == "__main__":
    main()