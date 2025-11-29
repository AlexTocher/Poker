import curses
import os
from card_ascii import *
import time
import math

RED_PAIR = 1
BLACK_PAIR = 2
HIGHLIGHT_PAIR = 3
MESSAGE_PAIR = 4

#spacing globals
MARGIN_X = 4
MARGIN_Y = 2
FOOTER_HEIGHT = 4
PLAYER_WIDTH = 24
PLAYER_HEIGHT = 16
PLAYER_START_ROW = 32
BETTING_ROW = PLAYER_START_ROW + 12

DECK_X = MARGIN_X
DECK_Y = MARGIN_Y
DECK_HEIGHT = 14



COMMUNITY_X = MARGIN_X + (4 + 3 * CARD_WIDTH) + (1 + 2 * CARD_WIDTH) + MARGIN_X
COMMUNITY_Y = 2 * MARGIN_Y
COMMUNITY_WIDTH = 4 + 5 * CARD_WIDTH

POT_Y = MARGIN_Y
POT_WIDTH = 32

BETTING_WIDTH = POT_WIDTH

TITLE_ART = r"""  _____ _______  __    _    ____     _   _  ___  _     ____  _____ __  __ _ 
 |_   _| ____\ \/ /   / \  / ___|   | | | |/ _ \| |   |  _ \| ____|  \/  ( )
   | | |  _|  \  /   / _ \ \___ \   | |_| | | | | |   | | | |  _| | |\/| |/ 
   | | | |___ /  \  / ___ \ ___) |  |  _  | |_| | |___| |_| | |___| |  | |  
   |_| |_____/_/\_\/_/  _\_\____/_  |_|_|_|\___/|_____|____/|_____|_|  |_|  
                       |  _ \ / _ \| |/ / ____|  _ \                        
                       | |_) | | | |   /|  _| | |_) |                       
                       |  __/| |_| |   \| |___|  _ <                        
                       |_|    \___/|_|\_\_____|_| \_\ """
TITLE_WIDTH = max(len(line) for line in TITLE_ART.strip().split('\n')) 
TITLE_HEIGHT = len(TITLE_ART.strip().split('\n'))

AUTHOR_ART = r"""  ______   __     _    _     _______  __  _____ ___   ____ _   _ _____ ____  
 | __ ) \ / /    / \  | |   | ____\ \/ / |_   _/ _ \ / ___| | | | ____|  _ \ 
 |  _ \\ V /    / _ \ | |   |  _|  \  /    | || | | | |   | |_| |  _| | |_) |
 | |_) || |    / ___ \| |___| |___ /  \    | || |_| | |___|  _  | |___|  _ < 
 |____/ |_|   /_/   \_\_____|_____/_/\_\   |_| \___/ \____|_| |_|_____|_| \_\ """

AUTHOR_WIDTH = max(len(line) for line in AUTHOR_ART.strip().split('\n')) 


class Visualizer:
    """Helper class to manage drawing on the stdscr."""
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.ideal_x = 200
        self.ideal_y = 50

        # Configure the screen
        curses.curs_set(0) # Hide cursor
        stdscr.nodelay(True) # Non-blocking input
        self.stdscr.timeout(100)
        self.stdscr.clear()
        self.get_screen_dimensions()

        if curses.has_colors():
             # --- START: FIX FOR BRIGHT WHITE BACKGROUND ---
            # 1. Use default terminal colors. This is the key step.
            if curses.can_change_color():
                # Redefine the standard curses.COLOR_WHITE (index 7) to be pure bright white (RGB 1000, 1000, 1000)
                # This overrides the terminal's potentially muted 'white' definition.
                try:
                    curses.init_color(curses.COLOR_WHITE, 1000, 1000, 1000)
                except curses.error:
                    # In some rare cases, this fails. We proceed with default white.
                    pass
            curses.start_color()
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
            curses.init_pair(2, curses.COLOR_RED, curses.COLOR_WHITE)
            curses.init_pair(3, curses.COLOR_BLUE, curses.COLOR_WHITE)
            curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_WHITE)
            self.stdscr.bkgd(' ', curses.color_pair(1))
            self.stdscr.clear()
            try:
                max_y, max_x = self.stdscr.getmaxyx()
                for y in range(max_y):
                    self.stdscr.chgat(y, 0, -1, curses.color_pair(1) | curses.A_BOLD)
            except curses.error:
                # Handles cases where the terminal is too small
                pass

        self.stdscr.refresh()

    def get_screen_dimensions(self):
        self.max_y, self.max_x = self.stdscr.getmaxyx()
        self.clear_area(0,0,0,self.max_x)
        self.center = (self.max_x//2, self.max_y//2)
        warning_msg = ''
        y_check = False
        if self.max_y < self.ideal_y:
            warning_msg += f'height (currently {self.max_y}; recommended {self.ideal_y})'
            y_check = True
        if self.max_x < self.ideal_x:
            if y_check: warning_msg += ' and '
            warninhg_msg += f'width (currently {self.max_x}; recommended {self.ideal_x})'
    
        if warning_msg: self.addstr(0, MARGIN_X, RED + 'WARNING: Screen too small in ' + warning_msg + END)

    def get_input(self):
        """
        Retrieves a key from the screen in non-blocking mode.
        Returns the integer value of the key, or -1 if no key was pressed.
        """
        return self.stdscr.getch()

    def addstr(self, y: int, x: int, text: str, wait = 0, overwrite = True, ignore_spaces = False) -> int:
        """
        Helper method to render a multi-line string starting at (y, x).
        It respects newlines and attempts to center each line horizontally.
        Returns the final row index used.
        """

        # --- Curses Color/Attribute Mapping ---
        # Assuming the standard color pairs initialized in __init__
        COLOR_BLACK = curses.color_pair(1)  # Black text on White BG
        COLOR_RED = curses.color_pair(2)  # Red text on White BG
        COLOR_BLUE = curses.color_pair(3)  # Red text on White BG
        COLOR_MAGENTA = curses.color_pair(4)  # Red text on White BG
        COLOR_DEFAULT = curses.color_pair(1) 
        
        ANSI_MAP = {
            '\033[90m': COLOR_BLACK, # Black (Default)
            '\033[91m': COLOR_RED,            # Red
            '\033[94m': COLOR_BLUE,    # Blue
            '\033[95m': COLOR_MAGENTA,    # Blue
            '\033[0m':  COLOR_DEFAULT,         # Reset
        }

        
        # Define the most common ANSI sequences to look for
        ANSI_SEQUENCES = list(ANSI_MAP.keys())

        max_y, max_x = self.stdscr.getmaxyx()
        
        lines = text.split('\n')
        current_y = y
        # Start with the default color attribute
        current_attr = COLOR_DEFAULT 

        for line in lines:

            first_non_space = len(line) if not line.strip() else line.find(line.strip()[0])
            last_non_space =  len(line) if not line.strip() else line.rfind(line.strip()[-1])

            if current_y >= max_y:
                break
            
            # Calculate x position to center the current line content (after removing ANSI codes)
            clean_line = line
            for seq in ANSI_SEQUENCES:
                clean_line = clean_line.replace(seq, '')
                
            current_x = x
            
            i = 0
            while i < len(line):
                
                # Check for ANSI escape sequences
                found_ansi = False
                for seq in ANSI_SEQUENCES:
                    seq_len = len(seq)
                    if line[i:i + seq_len] == seq:
                        current_attr = ANSI_MAP[seq] 
                        i += seq_len
                        found_ansi = True
                        break
                
                if found_ansi:
                    continue
                
                # Draw the actual character
                char = line[i]

                can_write = overwrite or not self.is_cell_filled(current_y, current_x)
                if char == ' ' and ignore_spaces and (i < first_non_space or i > last_non_space): 
                    can_write = False
                # Avoid writing off the screen horizontally or vertically
                if current_x < max_x and current_y < max_y:
                    try:
                        if can_write: self.stdscr.addstr(current_y, current_x, char, current_attr | curses.A_NORMAL)
                    except curses.error:
                        # Should not happen if bounds check is correct, but safe to catch
                        pass 

                current_x += 1
                i += 1
            
            current_y += 1
            
        self.stdscr.refresh()
        if wait: time.sleep(wait)
        return current_y - 1
        

    def addstrs(self, str_list, wait = 0):
        for y, x, str in str_list:
            self.addstr(y, x, str)
        time.sleep(wait)

    def clear_area(self, y1: int, x1: int, y2: int, x2: int):
        """
        Clears a rectangular area defined by the top-left (y1, x1) and 
        bottom-right (y2, x2) coordinates by drawing spaces over it.

        Args:
            y1 (int): Top row coordinate (inclusive).
            x1 (int): Left column coordinate (inclusive).
            y2 (int): Bottom row coordinate (inclusive).
            x2 (int): Right column coordinate (inclusive).
        """
        # Use min/max to ensure (y1, x1) is always the top-left and stay within bounds
        y_start = max(0, min(y1, y2))
        y_end = min(self.max_y - 1, max(y1, y2))
        x_start = max(0, min(x1, x2))
        x_end = min(self.max_x - 1, max(x1, x2))

        # Calculate the width of the space string needed for the clearing area
        width = x_end - x_start + 1
        if width <= 0:
            return

        clear_line = ' ' * width

        # Iterate over the rows and draw the space string
        for y in range(y_start, y_end + 1):
            # We call addstr which uses the default background color/attribute
            self.addstr(y, x_start, clear_line) 

        # self.stdscr.refresh()

    def is_cell_filled(self, y: int, x: int) -> bool:
        """
        Checks if the cell at (y, x) contains a non-space character
        on the curses standard screen (stdscr).
        
        Args:
            stdscr: The curses screen object.
            y (int): Row coordinate.
            x (int): Column coordinate.
            max_y (int): Max row index of the terminal.
            max_x (int): Max column index of the terminal.
                
        Returns:
            bool: True if the cell contains a character other than a space.
        """

        max_x , max_y = self.max_x, self.max_y
        # 1. Boundary Check: Ensure the coordinates are valid
        if y < 0 or y >= max_y or x < 0 or x >= max_x:
            return False # Outside the screen bounds

        try:
            # 2. Use stdscr.inch(y, x) to get the character and its attributes
            # inch() returns an integer, where the character is the lower 8 bits.
            char_int = self.stdscr.inch(y, x)
            
            # 3. Extract the character (mask off attributes)
            char_code = char_int & 0xFF
            
            # 4. Convert the character code back to a string character
            # Note: In a class method, this uses 'self.stdscr'
            current_char = chr(char_code)

            # 5. Check if the character is not a space
            return current_char != ' '
            
        except curses.error:
            # Handle exceptions like terminal resize issues
            return False
        
    def starting_animation(self, deck1, deck2):

        x_dim , y_dim = self.max_x, self.max_y
        centre = (x_dim//2, y_dim//2)
        offset = y_dim//10
        m = (2/3) * (centre[1]) * (centre[0])**-2
        omega = x_dim/10
        check_overwrite = lambda x : math.cos(omega * (x - x_dim//2)/x_dim) > 0
        f = lambda x : (m * (x - x_dim//2)**2 + offset)* math.sin(omega * (x - x_dim//2)/x_dim) + centre[1] #
        n_cards = (y_dim + x_dim)//8
        overlap_num = n_cards//2
        # multiply the decks so there is at least 2 * (1 + 2 * overalap_num) * n_cards in each
        n_decks = 2 * (n_cards + 2 * overlap_num)//52 + 1
        deck1.cards, deck2.cards = deck1.cards * n_decks, deck2.cards * n_decks
        i, n = n_cards, n_cards
        n, n_decks = 0, (n_cards*4)//52 + 1
    
        h, w = - CARD_HEIGHT//2, - CARD_WIDTH//2

        while n < n_decks: 
            _ , _ = deck1.cards.pop(), deck2.cards.pop()  # remove ace of spades
            n += 1
        deck1.shuffle()
        deck2.shuffle()
        
        while i > -overlap_num:
            x1, x2 = centre[0] - i * centre[0]/n_cards, centre[0] + i * centre[0]/n_cards
            x3, x4 = centre[0] - (i + overlap_num) * centre[0]/n_cards, centre[0] + (i + overlap_num) * centre[0]/n_cards
            # self.addstr(1 , 1, f'{x1} {f(x1)}', 0.1)
            # coming from the left:
            if x1 <= centre[0]: self.addstr(round(f(x1))+h , round(x1)+w, deck1.cards.pop().back, overwrite=check_overwrite(x1))
            if x3 <= centre[0]: self.addstr(round(f(x4))+h , round(x3)+w, deck2.cards.pop().back,  overwrite = not check_overwrite(x3))
            # coming from the right:
            if x2 >= centre[0]: self.addstr(round(f(x2))+h , round(x2)+w, deck1.cards.pop().back, overwrite= check_overwrite(x2))
            if x4 >= centre[0]: self.addstr(round(f(x3))+h , round(x4)+w, deck2.cards.pop().back, overwrite= not check_overwrite(x4))

            time.sleep(0.02)

            i -= 1

        title_card = title_ascii()
        self.addstr(centre[1]-len(title_card.split('\n'))//2 - 1 , centre[0]-len(title_card.split('\n')[0])//2 - 1, title_card , 0.5, ignore_spaces=True )
        self.addstr(1 , centre[0] - TITLE_WIDTH//2, TITLE_ART, 0.5,  ignore_spaces=True)
        self.addstr(round(y_dim * 3/4) , centre[0] - AUTHOR_WIDTH//2, AUTHOR_ART, ignore_spaces=True)

                # --- KEY PRESS WAITING LOGIC ---
        wait_msg = "PRESS ANY KEY TO START"
        self.stdscr.addstr(y_dim - 4, centre[0] - len(wait_msg)//2, wait_msg, curses.A_BLINK)
        
        # 1. Temporarily enable blocking mode
        self.stdscr.nodelay(False)
        # 2. Wait for a key press
        self.stdscr.getch()
        # 3. Restore non-blocking mode
        self.stdscr.nodelay(True) 

        self.stdscr.clear()
        