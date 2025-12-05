
from poker_lib import *
if __name__ == '__main__':
    # Start the application, which handles initialization and game creation
    # poker_tui(n_players = 5, buyin = 250, sb = 10 )
    players = [Player(i, name = f'Player #{i+1}') for i in range(5)]
    players = players + [Player(5, name = 'Alex', is_human = True)]
    game = Game(players, 100, 2)

    # 2. Execute the game logic
    game.play(max_rounds = 50, suppress_output=False )