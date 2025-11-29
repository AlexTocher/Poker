import random
import sys
import traceback
from poker_ui import *
from poker_hands import *

slow = True
if slow: DEAL_DELAY, BETTING_DELAY, SHOW_HANDS_DELAY = 0.1, 0.25, 1
else: DEAL_DELAY, BETTING_DELAY, SHOW_HANDS_DELAY = 0.01, 0.01, 0.01

CURSES_ERROR_TRACEBACK = None 
EXIT_MSG = 'Press shift + Q to exit'

class Game:
    def __init__(self, players, buyin, sb, stdscr = None):
        self.sb = sb # small blind
        self.bb = 2*sb # big blind
        self.minimum_bet = 0
        self.n_rounds = 0
        self.table = Table(len(players)) # class to store info about what's on the table
        self.visualizer =  None
        self.running = True # NEW: State variable for controlling the main game loop

        if stdscr:
            # Initialize the visualizer if stdscr is provided
            self.visualizer = Visualizer(stdscr)

        for p in players: p.stack += buyin
        self.players = players

        # decide on order of players by drawing a card, highest card goes first
     
        self.deck = DeckOfCards(back_color=MAGENTA)
        if self.visualizer: self.visualizer.starting_animation(deck1 = DeckOfCards( back_color=MAGENTA), 
                                                               deck2 = DeckOfCards( back_color=BLUE) )
            
        self.redraw()
        time.sleep(1)
        self.deck.deal(self.table, 5, discard=False, visualizer = self.visualizer, delay = 0.1)
        # self.visualizer.addstr(MARGIN_Y + 2 , self.table.x - (1 + CARD_WIDTH), 'WELCOME!'.center(6 + 7 * CARD_WIDTH, ' '))
        time.sleep(5)
        self.reset(cycle = False)

        self.deck.shuffle()
        self.deck.cut()
        self.deck.deal(players, 1, visualizer=self.visualizer)
        card_order = [(RANK_VALUES[p.hand[0].rank], SUITS.index(p.hand[0].suit)) for p in players]
        winning_idx = card_order.index(sorted(card_order, reverse = True)[0])   
        players[winning_idx].is_my_go = True

        hdr = 'High Card is:' + players[winning_idx].hand[0].name  + '\nDrawn by:\n'

        # If visualizer is available, show the result immediately
        if self.visualizer:
            self.visualizer.addstrs([(p.y - 4, p.x, hdr + p.player_info(show = True)) if i == winning_idx else \
                                    (p.y, p.x, p.player_info(show = True)) for i, p in enumerate(players)], BETTING_DELAY * 4 )
               
        self.players = players[winning_idx - 1:] + players[:winning_idx - 1] # reorder players to start with dealer
        self.reset() 


    def end_game(self):
        if self.visualizer: 
            self.redraw()
            self.deck.sort()
            self.visualizer.addstr(MARGIN_Y + 2 , self.table.x - (1 + CARD_WIDTH), 'TOO FEW PLAYERS; END OF GAME'.center(6 + 7 * CARD_WIDTH, ' '))
            self.deck.deal(self.table, 5, discard=False, visualizer=self.visualizer, delay = 1)
            time.sleep(5)
        else: return

    def __repr__(self):
        player_names = ", ".join([p.name for p in self.players])
        return f"Game(players=[{player_names}], sb={self.sb:.2f}, bb={self.bb:.2f}, minimum_bet={self.minimum_bet:.2f})"

    def __str__(self):
        return f"Poker Game (Blinds: £{self.sb:.2f}/£{self.bb:.2f}) with {len(self.players)} players."
    
    def _check_for_quit(self):
        """
        Checks for 'Q' keypress to terminate the game.
        This must be called frequently during the game loop.
        """
        if self.visualizer:
            # Use the non-blocking input method
            key = self.visualizer.get_input()
            # Check for 'q' or 'Q' (curses returns integer key codes)
            if key in [ord('Q')]:
                self.running = False
                if self.visualizer:
                    # Optional: Display a quick message before exiting
                    self.visualizer.addstr(2, 2, "Quitting game...             ", 1)
                return True
        return False
        
    
    def redraw(self):
        if not self.visualizer: return 
        time.sleep(BETTING_DELAY)

        self.visualizer.get_screen_dimensions()
        self.visualizer.clear_area(MARGIN_Y, MARGIN_X, self.visualizer.max_y, self.visualizer.max_x)
        self.get_positions()

        self.visualizer.addstr(0, self.visualizer.max_x - MARGIN_X - len(EXIT_MSG),  EXIT_MSG )
        self.visualizer.addstr(MARGIN_Y, self.visualizer.center[0] - TITLE_WIDTH//2, TITLE_ART)
        self.visualizer.addstr(self.deck.y, self.deck.x, self.deck.deck_info())
        self.visualizer.addstr(self.table.bety, self.table.betx, self.betting_info())
        self.visualizer.addstr(self.table.y, self.table.x, self.table.table_info())
        self.visualizer.addstr(self.table.poty, self.table.potx, self.table.pot_info())
        self.visualizer.addstrs([(p.y, p.x, p.player_info()) for p in self.players])

    def get_positions(self):
        global PLAYER_WIDTH, PLAYER_START_ROW 
        self.deck.y, self.deck.x = MARGIN_Y, MARGIN_X
        self.table.y, self.table.x = max(self.visualizer.center[1]//2, MARGIN_Y + TITLE_HEIGHT + 2), self.visualizer.center[0] - COMMUNITY_WIDTH//2
        self.table.poty, self.table.potx = MARGIN_Y,  self.visualizer.max_x - MARGIN_X - POT_WIDTH,
        self.table.bety, self.table.betx = self.table.poty + (self.visualizer.max_y - 2 * MARGIN_Y - FOOTER_HEIGHT)//2,  self.table.potx
        PLAYER_WIDTH = (self.table.potx - MARGIN_X)//len(self.players)
        PLAYER_START_ROW = self.visualizer.max_y - PLAYER_HEIGHT - MARGIN_Y
        for p in self.players:
            p.y, p.x = PLAYER_START_ROW, MARGIN_X + PLAYER_WIDTH * p.idx


    def reset(self, raise_blinds = False, cycle = True):
        for p in self.players: self.deck.cards += p.reset()
        self.deck.cards += self.table.reset()
        self.deck.reset()
        self.minimum_bet = 0
        
        if cycle: self.players[:] = self.players[1:] + self.players[:1] # move dealer, sb, and bb one place on

        for p in self.players:
            if p.stack == 0 and not p.is_out:
                p.is_out = True
                if not self.visualizer: print(p.name + ' is eliminated')
        
        self.players = [p for p in self.players if p.is_out] + [p for p in self.players if not p.is_out]
        
        if cycle:   
            for p in self.players:
                p.dealer = False
                p.sb = False
                p.bb = False
            self.players[0].dealer = True
            self.players[1].sb = True
            self.players[2].bb = True

            

        if raise_blinds: 
            self.sb += raise_blinds
            self.bb = 2 * self.sb
        self.redraw()
        
         # Ensure total contribution is reset for all players
        for p in self.players: assert(p.total_contribution == 0.0) 
        for p in self.players: assert(len(p.hand) == 0)
        assert(len(self.deck.discard) == 0)
        assert(len(self.deck.cards)%52 == 0)

    def deal(self): 
        self.deck.deal(self.players, 2, visualizer=self.visualizer)

    def flop(self):
        assert(len(self.table.cards) == 0)
        
        self.deck.discard += [self.deck.cards.pop()] # discard only once on the flop
        self.deck.deal(self.table, 3, discard = False, visualizer=self.visualizer)
        if not self.visualizer: 
            print('\nFlop')
            print(combine_cards(self.table.cards))



    def turn(self):
        assert(len(self.table.cards) == 3)
    
        self.deck.deal(self.table, 1, discard = True, visualizer=self.visualizer) 
        if not self.visualizer: 
            print('\nTurn')
            print(combine_cards(self.table.cards))

    
    def river(self):
        assert(len(self.table.cards) == 4)

        self.deck.deal(self.table, 1, discard = True, visualizer=self.visualizer)
        if not self.visualizer: 
            print('\nRiver')
            print(combine_cards(self.table.cards))

    
    def show_hands(self):
        if not self.visualizer:
            print('\n\nCards on the Table:')
            print(combine_cards(self.table.cards) + '\n\n\n')

        start_idx = [p.last_raised for p in self.players].index(True)
        reordered_players = self.players[start_idx:] + self.players[:start_idx] #show last peson that raised first
        # 1. Evaluate hands and Rank players
        for i, p in  enumerate(reordered_players):
            if not p.folded or not p.is_out: # Only evaluate hands of active players
                p.hand_name, p.best_hand, p.score, p.discarded = get_best_5_card_hand(self.table.cards + p.hand)
                if self.visualizer:
                    self.visualizer.clear_area(self.table.y + 1, self.table.x, self.table.y + CARD_HEIGHT + 6, self.table.x + 7 + 7 * CARD_WIDTH )
                    self.visualizer.addstr(self.table.y, self.table.x, self.table.table_info(), 0)
                    self.visualizer.addstrs([(pl.y, pl.x, pl.player_info(show = True if j <= i and not pl.folded else False )) for j, pl in enumerate(reordered_players)], SHOW_HANDS_DELAY)
                    self.visualizer.addstr(p.y, p.x, p.player_info(no_cards = True), 0)
                    self.visualizer.addstr(self.table.y + 2, self.table.x, self.winner_info(p), SHOW_HANDS_DELAY)
            else:
                p.score = (0, (0,)) # Folded players have the lowest score

           

        rank_players(self.players) # Assigns p.rank (0-based, handles ties)

     
        
        # 2. Distribute Pots
        if not self.visualizer: print('\n--- Pot Distribution ---')
        remaining_pot_amount = self.table.total_pot_amount # Should be zero at the end

        for i, pot in enumerate(self.table.pots):
            # Find the best eligible player for this pot
            eligible_winners = sorted(
                [p for p in self.players if p.rank != 0 and p in pot.eligible_players],
                key=lambda p: p.score,
                reverse=True
            )
            # Find the highest rank among eligible players (0 is best, 1 is next, etc.)
            best_rank_in_pot = min(p.rank for p in pot.eligible_players if not p.folded) if pot.eligible_players else None

            # Actual winners are those tied for the best rank among all eligible players
            winners_of_pot = [p for p in pot.eligible_players 
                              if not p.folded and p.rank == best_rank_in_pot]
            
            n_winners = len(winners_of_pot)

            if n_winners > 0:
                winnings = pot.amount / n_winners
                for p in winners_of_pot:
                    p.stack += winnings
                    ftr = f"{p.name} wins £{winnings:.2f} from Pot {i+1}".ljust(5 * CARD_WIDTH + 4, ' ')
                    if not self.visualizer: 
                        print(ftr)
                    else: 
                        self.visualizer.addstrs([(pl.y, pl.x, pl.player_info(show = True if not pl.folded else True)) for  pl in self.players])
                        self.visualizer.addstr(p.y, p.x, p.player_info(no_cards = True))
                        self.visualizer.addstr(self.table.y + 2, self.table.x, '\n'.join(self.winner_info(p).split('\n')[:-1]) + '\n' + ftr, SHOW_HANDS_DELAY)
                remaining_pot_amount -= pot.amount
            else:
                if not self.visualizer: print(f"Pot {i+1} (£{pot.amount:.2f}) had no eligible winners and remains unclaimed.")
                
        
        # 3. Show Final Hands and Stacks
        if not self.visualizer: print('\n--- Final Hands ---')
        for p in sorted([pl for pl in self.players if not pl.is_out], key=lambda player: player.rank):
            if p.folded:
                if not self.visualizer: print(f"\n{p.name} Folded")
                continue

            if not self.visualizer: 
                print( f"\n#{p.rank + 1}: {p.name} - {p.hand_name}")
                print(combine_cards(p.best_hand , discarded_cards=p.discarded, overlap = (0,1), reverse = (0,0)))



        if not self.visualizer: 
            print('\n--- Final Stacks ---')
            for p in self.players: print( p.name + f' has: £{p.stack:.2f}')

        assert(abs(remaining_pot_amount) < 0.01) # Check for zero remaining money

    def winner_info(self, player):
        hdr = (player.name + ' - ' + player.hand_name).ljust(5 * CARD_WIDTH + 4, ' ')
        body = combine_cards(player.best_hand, discarded_cards=player.discarded, overlap=(0,1))
        pad = '\n' + ' ' * (4 + 5 * CARD_WIDTH)
        while len(body.split('\n')) < 12:
            body += pad
        
        
        return hdr + '\n\n' + body 

        
    def betting_info(self): 
        hdr = 'BETTING'.center(BETTING_WIDTH, '-')
        body = ''
        if sum([p.total_contribution for p in self.players]) != 0:
            hdr += '\n\n' + f'Minimum bet: £{self.minimum_bet:.2f}'.ljust(BETTING_WIDTH)
            for p in sorted(self.players, key = lambda p : p.idx):
                if p.is_out: continue
                body += f'{p.name}:'.ljust(12) + f' £{p.total_contribution:.2f}' 
                if p.is_all_in: body += ' all-in'
                body = body.ljust(BETTING_WIDTH) + '\n'

        pad = '\n' + ' '.ljust(BETTING_WIDTH)
        while len(body.split('\n')) < 12:
            body += pad
    
        return hdr + '\n\n' + body 
    

    # --- NEW CRUCIAL SIDE POT LOGIC METHOD ---
    def distribute_chips_to_pots(self):
        """
        Calculates the side pots based on each player's total contribution 
        across the entire hand so far.
        """
        # 1. Collect all contributions from active (non-folded) players
        active_contributions = sorted(
            [p.total_contribution for p in self.players if not p.folded and p.total_contribution > 0],
            key=lambda x: x
        )
        
        # Get unique contribution levels to define the pot caps
        # Start with 0.0 to handle the tier calculation correctly
        contribution_levels = sorted(list(set([0.0] + active_contributions)))

        # 2. Iterate through levels to build pots
        self.table.pots = []
        
        # Total contribution from folded players (will be added to the Main Pot)
        folded_contribution = sum(p.total_contribution for p in self.players if p.folded)
        
        # Total money placed by ALL players (including folded)
        total_money_in_hand = sum(p.total_contribution for p in self.players)

        # Iterate over contribution levels starting from the first actual contribution
        for i, cap in enumerate(contribution_levels):
            if i == 0: continue # Skip 0.0 level
            
            prev_cap = contribution_levels[i-1]
            tier_amount = cap - prev_cap
            
            # Eligible players are those who contributed AT LEAST the current cap
            eligible_players = [p for p in self.players 
                                if p.total_contribution >= cap and not p.folded]

            # Contribution to this tier: (amount of tier) * (number of eligible players)
            pot_tier_total = tier_amount * len(eligible_players)

            if pot_tier_total > 0:
                # Create a new pot for this tier
                new_pot = Pot(eligible_players=eligible_players, cap=cap)
                new_pot.amount = pot_tier_total
                self.table.pots.append(new_pot)

        # 3. Add folded money to the MAIN pot (the first pot created)
        if folded_contribution > 0:
             if self.table.pots:
                 self.table.pots[0].amount += folded_contribution
             else:
                 # Case where only folded players contributed (shouldn't happen in a real game flow)
                 self.table.pots = [Pot(eligible_players=[], amount=folded_contribution, cap=float('inf'))]
                 
        # Final sanity check: Total money in all pots must equal total money contributed
        assert(abs(self.table.total_pot_amount - total_money_in_hand) < 0.01)


    def round_of_betting(self):
        if not self.visualizer: print('\n--- Starting Betting Round ---')
        
        # Reset current round bets before the action starts
        for p in self.players:
            p.current_round_bet = 0.0
        
        # Determine current players who can act (not folded and not all-in)
        active_players = [p for p in self.players if not p.folded and not p.is_all_in]
        
        # 1. INITIALIZE BETTING (Blinds)
        if self.table.total_pot_amount == 0: # Pre-Flop
            hdr = self.players[0].name +  f' is the dealer'
            if self.visualizer:
                self.visualizer.clear_area(BETTING_ROW, 0, BETTING_ROW, self.visualizer.max_x)   
                self.visualizer.addstrs([(p.y, p.x, p.player_info()) for i, p in enumerate(self.players) if i != 0 ])
                self.visualizer.addstr(self.players[0].y, self.players[0].x,  self.players[0].player_info(hdr))
                self.visualizer.addstr(self.table.bety, self.table.betx,  self.betting_info(), BETTING_DELAY)
            else: print(hdr)

            # SB posts (Player 1)
            hdr = self.players[1].name + f' is the small blind'
            self.players[1].raise_bet(self.sb, self.minimum_bet, verbose = False)
            if self.visualizer:
                self.visualizer.clear_area(BETTING_ROW, 0, BETTING_ROW, self.visualizer.max_x)
                self.visualizer.addstrs([(p.y, p.x, p.player_info()) for i, p in enumerate(self.players) if i != 1 ])
                self.visualizer.addstr(self.players[1].y, self.players[1].x,  self.players[1].player_info(hdr))
                self.visualizer.addstr(self.table.bety, self.table.betx,  self.betting_info(), BETTING_DELAY)

            else: print(hdr)
            
            # BB posts (Player 2)
            hdr = self.players[2].name + f' is the big blind'
            self.players[2].raise_bet(self.bb, self.minimum_bet, verbose = False)
            if self.visualizer:
                self.visualizer.clear_area(BETTING_ROW, 0, BETTING_ROW, self.visualizer.max_x)
                self.visualizer.addstrs([(p.y, p.x, p.player_info()) for i, p in enumerate(self.players) if i != 2 ])
                self.visualizer.addstr(self.players[2].y, self.players[2].x,  self.players[2].player_info(hdr))
                self.visualizer.addstr(self.table.bety, self.table.betx,  self.betting_info(), BETTING_DELAY)

            else: print(hdr)

            for pl in self.players: pl.last_raised = False 
            self.players[2].last_raised = True
            
            self.minimum_bet = self.bb
            idx = 3 # Action starts UTG
            
        else: # Post-Flop
            # Find the first player after the dealer (Player 0) who is active
            idx = 1 
            while self.players[idx % len(self.players)].folded:
                idx += 1
            
            # minimum_bet is the highest total_contribution currently in the pot
            self.minimum_bet = max(p.total_contribution for p in self.players) if self.players else 0

        
        # 2. COLLECT BETS
        all_called_checked = 0
        n_players_to_act = len(active_players)
        
        # Loop until all players who can act have called the current minimum_bet
        while all_called_checked < n_players_to_act:
            
            player_obj = self.players[idx % len(self.players)]
            
            # Skip folded or already all-in players
            if player_obj.folded or player_obj.is_all_in or player_obj.is_out:
                if player_obj.is_all_in: all_called_checked += 1
                idx += 1
                continue
            
            # Action: Player either calls/checks or raises (using mock methods)
            bet_placed, hdr = player_obj.call_check_bet(self.minimum_bet, verbose = False if self.visualizer else True) # Simplified to always call/go all-in
            # Check if player raised (i.e., new total contribution > old minimum_bet)
            if player_obj.total_contribution > self.minimum_bet:
                
                # New minimum bet to call is the player's new total contribution
                self.minimum_bet = player_obj.total_contribution 
                
                # A raise restarts the loop condition for all players who still need to act
                all_called_checked = 1 
                for pl in self.players: pl.last_raised = False 
                player_obj.last_raised = True
                
                if self.visualizer:
                    self.visualizer.clear_area(BETTING_ROW, 0,BETTING_ROW, self.visualizer.max_x)
                    self.visualizer.addstrs([(p.y, p.x, p.player_info()) for i, p in enumerate(self.players) if i != idx % len(self.players) ])
                    self.visualizer.addstr(self.players[idx % len(self.players)].y, self.players[idx % len(self.players)].x,  self.players[idx % len(self.players)].player_info(hdr))
                    self.visualizer.addstr(self.table.bety, self.table.betx,  self.betting_info(), BETTING_DELAY)
                else: print(f"{player_obj.name} raised. New bet to call: £{self.minimum_bet:.2f}")
            else:
                # Player called or checked
                all_called_checked += 1 
                if self.visualizer: 
                    self.visualizer.clear_area(BETTING_ROW, 0,BETTING_ROW, self.visualizer.max_x)
                    self.visualizer.addstrs([(p.y, p.x, p.player_info()) for i, p in enumerate(self.players) if i != idx % len(self.players) ])
                    self.visualizer.addstr(self.players[idx % len(self.players)].y, self.players[idx % len(self.players)].x,  self.players[idx % len(self.players)].player_info(hdr))
                    self.visualizer.addstr(self.table.bety, self.table.betx,  self.betting_info(), BETTING_DELAY)

            idx += 1
                

        # 3. DISTRIBUTE CHIPS
        self.distribute_chips_to_pots()
        if not self.visualizer:
            print(f'\nBetting Done. Total Pot: £{self.table.total_pot_amount:.2f} across {len(self.table.pots)} pot(s).')
            for i, pot in enumerate(self.table.pots):
                print(f"Pot {i+1}: {pot}")
        else:
            self.visualizer.clear_area(BETTING_ROW, 0,BETTING_ROW, self.visualizer.max_x)
            self.visualizer.addstr(self.table.poty, self.table.potx, self.table.pot_info())
            self.visualizer.addstr(self.table.bety, self.table.betx, self.betting_info(), BETTING_DELAY)



    
    
    
    def play(self, max_rounds = 5):

        n = 0
        while self.running and self.n_rounds < max_rounds:
            if len([p for p in self.players if not p.is_out]) < 3: 
                self.running = False # End game if not enough players
                self.end_game()
                return
            self.deal()
            self.round_of_betting()
            if self._check_for_quit(): break
            self.flop()
            self.round_of_betting()
            if self._check_for_quit(): break
            self.turn()
            self.round_of_betting()
            if self._check_for_quit(): break
            self.river()
            self.round_of_betting()
            if self._check_for_quit(): break
            self.show_hands()
            n += 1
            if n%len(self.players) == 0:
                self.reset(raise_blinds=1) 
                self.n_rounds += 1
            else:
                self.reset()
            if self._check_for_quit(): break # Exit the loop if Q was pressed here too

class Player:
    def __init__(self, idx, name=""):
        self.name = name
        self.hand = []
        self.best_hand = [] 
        self.hand_name = ''
        self.discarded = []
        self.stack = 0
        self.folded = False
        self.score = (0,0)
        self.rank = 0
        self.total_contribution: float = 0.0  # Total money bet in the ENTIRE hand
        self.current_round_bet: float = 0.0   # Money bet in the CURRENT betting round
        self.is_all_in: bool = False
        self.is_out = False
        self.last_raised = False

        self.idx = idx
        self.x = MARGIN_X + idx * PLAYER_WIDTH
        self.y = PLAYER_START_ROW

        self.dealer = False
        self.sb = False
        self.bb = False

    def show_hand(self):
        print(combine_cards([c for c in self.hand]))

    def reset(self):
        out = self.hand
        self.hand = []
        self.stake = 0
        self.current_round_bet = 0.0
        self.total_contribution = 0.0 # Crucial: Reset total contribution for a new hand
        self.folded = False
        self.is_all_in = False
        assert(len(self.hand) == 0)
        return out
    
    
    def call_check_bet(self, minimum_bet, verbose = True):
        # Bet required to match the minimum_bet (the highest total contribution)
        bet_required = minimum_bet - self.total_contribution 
        
        # Calculate actual amount to bet (capped by stack)
        bet_amount = min(bet_required, self.stack)
        
        if bet_amount <= 0: # Check
            out_str = self.name + ' checks' 
            if verbose: print( out_str)
            return 0.0, out_str
        
        out_str = self.name + ' calls'  if bet_amount < self.stack or self.stake == 0 else self.name + f' calls (all in) £{bet_amount:.2f}'

        if verbose: 
            print( out_str)

        self.stack -= bet_amount
        self.total_contribution += bet_amount
        self.current_round_bet += bet_amount

        if self.stack == 0:
            self.is_all_in = True
        
        return bet_amount, out_str
        
    def raise_bet(self, amount, minimum_bet, verbose = True):
        # Calculate the amount needed to call the minimum_bet
        call_amount = minimum_bet - self.total_contribution
        
        # The total amount the player wants to put in (call + raise amount)
        total_bet_amount = call_amount + amount 
        
        # Check if they can cover the entire intended bet
        if total_bet_amount >= self.stack:
            bet_amount = self.stack
            self.is_all_in = True
            out_str = self.name + f' goes all in £{bet_amount:.2f}'
        else:
            bet_amount = total_bet_amount
            out_str = self.name + f' raises £{amount:.2f} (Total bet: £{bet_amount:.2f})'
        if verbose: print(out_str )

        self.stack -= bet_amount
        self.total_contribution += bet_amount
        self.current_round_bet += bet_amount

        return bet_amount, out_str

    def fold(self):
        out = self.reset_hand()
        print( self.name + ' folds')
        self.folded = True
        return out
    
    def player_info(self, betting_str = '', show = False, no_cards = False):
        hdr = self.name + '\n'
        if self.dealer: hdr += 'Dealer'
        elif self.sb: hdr += 'Small Blind'
        elif self.bb: hdr += 'Big Blind'
        body = ' ' * PLAYER_WIDTH
        if not no_cards: body = combine_cards(self.hand, overlap = (1,0) ,reverse = (not show, 0))
        pad = '\n' + ' ' * PLAYER_WIDTH
        while len(body.split('\n')) < 12:
            body += pad

        ftr = betting_str.ljust(PLAYER_WIDTH * 2) + '\n' + f'Stack: £{self.stack:.2f}'.ljust(PLAYER_WIDTH) +'\n' +  f'Stake: £{self.total_contribution:.2f}'.ljust(PLAYER_WIDTH)\
              if not self.is_out else 'Out'.ljust(PLAYER_WIDTH) + '\n'.ljust(PLAYER_WIDTH)
        return hdr + '\n' + body + '\n' + ftr + 3 * pad



    def __repr__(self):
        status = []
        if self.is_all_in: status.append("ALL-IN")
        if self.folded: status.append("FOLDED")
        status_str = f" ({', '.join(status)})" if status else ""
        return f"Player(name='{self.name}', stack={self.stack:.2f}, total_contrib={self.total_contribution:.2f}{status_str})"

    def __str__(self):
        status = " (ALL-IN)" if self.is_all_in else ""
        folded = " (FOLDED)" if self.folded else ""
        return f"{self.name} | Stack: £{self.stack:.2f} | Bet: £{self.total_contribution:.2f}{status}{folded}"
  

class Pot:
    def __init__(self, eligible_players, amount: float = 0.0, cap: float = float('inf')):
        self.eligible_players = eligible_players # List of players who can win this pot
        self.amount = amount                     # Total chips in this pot
        self.cap = cap                           # Max contribution from any player to this pot
   

    def __repr__(self):
        names = ", ".join([p.name for p in self.eligible_players])
        return f"Pot(amount={self.amount:.2f}, cap={self.cap:.2f}, eligible=[{names}])"

    def __str__(self):
        names = "\n              ".join([p.name for p in self.eligible_players])
        cap_str = f" (Cap: £{self.cap:.2f})" if self.cap != float('inf') else ""
        return f"£{self.amount:.2f}{cap_str} ".ljust(POT_WIDTH) #+ f"\n    Eligible: {names}"

    
class Table:
    def __init__(self, n_players):
        self.cards = []
        self.pots: List[Pot] = []
        self.x = COMMUNITY_X
        self.y = COMMUNITY_Y
        self.potx = COMMUNITY_X + 6 + 7 * CARD_WIDTH + MARGIN_X
        self.poty = POT_Y
        self.betx = self.potx
        self.bety = POT_Y + 20
        
    @property
    def total_pot_amount(self) -> float:
        return sum(p.amount for p in self.pots)

    def reset(self):
        out = self.cards
        self.cards = []
        self.pots = [] # Clear all pots for a new hand
        return out
    
    def table_info(self): 
        hdr = 'COMMUNITY CARDS'.center(5 * CARD_WIDTH + 4, '-') + '\n\n\n'
        body = combine_cards(self.cards)
        pad = '\n' + ' ' * (4 + 5 * CARD_WIDTH)
        while len(body.split('\n')) < 10:
            body += pad
        return hdr + '\n' + body 
    
    def pot_info(self): 
        hdr = 'POT'.center(POT_WIDTH, '-') +'\n\n'
        body = ''
        if self.total_pot_amount != 0: 
            body = f'Total Pot: £{self.total_pot_amount:.2f} across {len(self.pots)} pot(s)'.ljust(POT_WIDTH) 
            for i, pot in enumerate(self.pots):
                body += '\n\n' + f"Pot {i+1}: {pot}"
        pad = '\n' + ' ' * POT_WIDTH
        while len((hdr + body).split('\n')) < self.bety - self.poty :
            body += pad
    
        return hdr + body 


    def __repr__(self):
        return f"Table(cards={len(self.cards)}, pots={self.pots})"

    def __str__(self):
        return f"Table: {len(self.cards)} community cards. Total Pot: £{self.total_pot_amount:.2f} ({len(self.pots)} pots)."
  


class Card:
    def __init__(self, suit, rank, back_color = RED):
        self.suit = suit
        self.rank = rank
        if   rank == 1:  name = 'Ace of '  
        elif rank == 11: name = 'Jack of ' 
        elif rank == 12: name = 'Queen of ' 
        elif rank == 13: name = 'King of '
        else:            name = str(rank) + ' of '
        name = name + suit
        self.name = name      
        self.front = card_ascii(rank, suit)
        self.back = card_ascii(rank, suit, back = True, back_color=back_color)

    def __repr__(self):
        return f"Card('{self.suit}', {self.rank})"

    def __str__(self):
        return self.name


class DeckOfCards:
    def __init__(self, n_decks = 1, back_color = RED):
        self.cards = []
        self.discard = []
        self.x = DECK_X
        self.y = DECK_Y
        for i in range(n_decks):
            for suit in SUITS:
                for rank in RANKS:
                    self.cards += [Card(suit, rank, back_color=back_color)]

    def shuffle(self):
        random.shuffle(self.cards)

    def sort(self):
        def sort_key(card):
            suit_index = SUITS.index(card.suit)
            adjusted_rank = 14 if card.rank == 1 else card.rank
            return (suit_index, adjusted_rank)
        self.cards.sort(key=sort_key)
        self.discard.sort(key=sort_key)

    def cut(self, n = None):
        if not n: n = random.randint(0,len(self.cards))
        self.cards = self.cards[n%len(self.cards):] + self.cards[0:n%len(self.cards)]


    def deal(self, recievers, n_cards, visualizer = None, discard = True, delay = 0):

        if not delay: delay = DEAL_DELAY
        
        if not isinstance(recievers, list): recievers = [recievers]
        for _ in range(0, n_cards):
            if discard: 
                if visualizer: visualizer.addstr(self.y, self.x, self.deck_info(), delay)
                
                self.discard += [self.cards.pop()]
                if visualizer: visualizer.addstr(self.y, self.x, self.deck_info(), delay)
            
            for r in recievers:
                if isinstance(r, Player): 
                    if not r.is_out: r.hand += [self.cards.pop()]
                    if visualizer: 
                        visualizer.addstr(r.y, r.x, r.player_info())
                        visualizer.addstr(self.y, self.x, self.deck_info(), delay)
                        
                elif isinstance(r, Table): 
                    r.cards += [self.cards.pop()]
                    if visualizer: 
                        visualizer.addstr(r.y, r.x, r.table_info())
                        visualizer.addstr(self.y, self.x, self.deck_info(), delay)
            
            

    def deck_info(self):
        hdr = 'DECK'.center(4 + 3 * CARD_WIDTH, '-') +'\n\n'
        hdr += f'Deck: {len(self.cards):d}'.ljust(3 + 2 * CARD_WIDTH) + f'Discard: {len(self.discard):d}' + '\n'
        body = combine_cards(self.cards[:2], discarded_cards=self.discard[:2] ,overlap = (1,1) ,reverse = (1,1))
        pad = '\n' + ' ' * (4 + 3 * CARD_WIDTH)
        while len(body.split('\n')) < 11:
            body += pad
        return hdr + '\n' + body 


    
    def __repr__(self):
        return f"DeckOfCards(cards={len(self.cards)}, discard={len(self.discard)})"


    def __str__(self):
        return f"Deck: {len(self.cards)} cards remaining."
        
    def reset(self):
        while len(self.discard) > 0:
            self.cards += [self.discard.pop()]
        assert(len(self.cards)%52 == 0)


def main_tui(stdscr, n_players = 5, buyin = 100, sb = 2):
    """
    The Curses entry point, with an internal error capture.
    """
    global CURSES_ERROR_TRACEBACK # MUST be at the top
    
    # 1. Initialize Game
    players = [Player(i, name = f'Player #{i+1}') for i in range(n_players)]
    
    # --- CRITICAL TRY/EXCEPT BLOCK INSIDE CURSES ---
    try:
        game = Game(players, buyin, sb, stdscr=stdscr)
        
        # 2. Execute the game logic
        game.play(max_rounds = 50)
        
    except Exception as e:
        # 3. Capture the full traceback details (file, line number, etc.)
        exc_info = sys.exc_info()
        tb_str = traceback.format_exception(*exc_info)
        
        # 4. Store the captured traceback in the global variable
        CURSES_ERROR_TRACEBACK = "".join(tb_str)
        
        # 5. Re-raise the exception. This is essential to force curses.wrapper() 
        #    to immediately clean up and restore the terminal state.
        raise
        

def poker_tui(**kwargs):
    """Wrapper function to initialize and terminate curses safely."""
    global CURSES_ERROR_TRACEBACK # MUST be at the top
    
    # We remove the try/except from here and move it to the caller
    # to simplify the internal logic.
    
    if not sys.stdout.isatty():
         print("Error: Not running in a proper terminal environment for curses.")
         return
         
    # Curses wrapper calls main_tui(stdscr)
    curses.wrapper(main_tui, **kwargs)


if __name__ == '__main__':
    # --- FINAL OUTER TRY/EXCEPT BLOCK (CRITICAL FOR PRE-CURSES ERRORS) ---
    try:
        # Start the application, which handles initialization and game creation
        poker_tui(n_players = 8, buyin = 100)
    
    except Exception as e:
        # This catches errors that occur either:
        # 1. Before poker_tui is called (unlikely).
        # 2. During the setup phase inside poker_tui (before curses.wrapper).
        # 3. An exception re-raised from main_tui (after curses cleanup).
        
        # 6. Check if a traceback was captured during the curses phase
        if CURSES_ERROR_TRACEBACK:
            # 7. Print the detailed error message clearly outside of curses.
            print("\n--- DETAILED TRACEBACK from Curses Execution ---")
            print(CURSES_ERROR_TRACEBACK, file=sys.stderr)
            print("-------------------------------------------------")
        else:
            # 8. Print the detailed error for errors occurring outside of curses.
            print("\n--- DETAILED TRACEBACK from Pre-Curses Execution ---")
            # This captures the traceback *at the point of the error* in the outer code
            traceback.print_exc(file=sys.stderr)
            print("--------------------------------------------------")
            
    finally:
        # Cleanup the global variable
        CURSES_ERROR_TRACEBACK = None