import curses
import os
from card_ascii import *
import time
import math
import string 
from config import UIConfig

RED_PAIR = 1
BLACK_PAIR = 2
HIGHLIGHT_PAIR = 3
MESSAGE_PAIR = 4




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
                self.max_y, self.max_x = self.stdscr.getmaxyx()
                for y in range(self.max_y):
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
    
        if warning_msg: self.addstr(0, UIConfig.MARGIN_X, RED + 'WARNING: Screen too small in ' + warning_msg + END)

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
        f = lambda x : (m * (x - x_dim//2)**2 + offset)* math.sin(omega * (x - x_dim//2)/x_dim) #
        n_cards = (y_dim + x_dim)//8
        overlap_num = n_cards//6
        # multiply the decks so there is at least 2 * (1 + 2 * overalap_num) * n_cards in each
        n_decks = 2 * (n_cards + 6 * overlap_num)//52 + 1
        deck1.cards, deck2.cards = deck1.cards * n_decks, deck2.cards * n_decks
        i, n = n_cards, n_cards
        n, n_decks = 0, (n_cards*4)//52 + 1
    
        h, w = - CARD_HEIGHT//2, - CARD_WIDTH//2

        while n < n_decks: 
            _ , _ = deck1.cards.pop(), deck2.cards.pop()  # remove ace of spades
            n += 1
        deck1.shuffle()
        deck2.shuffle()

        title_card = title_ascii()
        
        while i > -3*overlap_num:
            x1, x2 = centre[0] - i * centre[0]/n_cards, centre[0] + (i + 3 * overlap_num) * centre[0]/n_cards
            x3, x4 = centre[0] - (i + 2 * overlap_num) * centre[0]/n_cards, centre[0] + (i +  1 * overlap_num) * centre[0]/n_cards
            # self.addstr(1 , 1, f'{x1} {f(x1)}', 0.1)
            # coming from the left:
            if x1 <= centre[0]: self.addstr(round(centre[1] + f(x1))+h , round(x1)+w, deck1.cards.pop().back, overwrite=check_overwrite(x1))
            if x3 <= centre[0]: self.addstr(round(centre[1] - f(x3))+h , round(x3)+w, deck2.cards.pop().back,  overwrite = not check_overwrite(x3))
            # coming from the right:
            if x2 >= centre[0]: self.addstr(round(centre[1] + f(x2))+h , round(x2)+w, deck1.cards.pop().back, overwrite= check_overwrite(x2))
            if x4 >= centre[0]: self.addstr(round(centre[1] - f(x4))+h , round(x4)+w, deck2.cards.pop().back, overwrite= not check_overwrite(x4))

            if x1 > centre[0]: 
                self.addstr(centre[1]-len(title_card.split('\n'))//2 - 1 , centre[0]-len(title_card.split('\n')[0])//2 - 1, title_card , ignore_spaces=True )

            time.sleep(0.02)

            i -= 1

        
        self.addstr(UIConfig.MARGIN_Y , centre[0] - UIConfig.TITLE_WIDTH//2, UIConfig.TITLE_ART, 0.5,  ignore_spaces=True)
        self.addstr(round(y_dim * 3/4) , centre[0] - UIConfig.AUTHOR_WIDTH//2, UIConfig.AUTHOR_ART, ignore_spaces=True)

                # --- KEY PRESS WAITING LOGIC ---
        wait_msg = "PRESS ANY KEY TO START"
        self.stdscr.addstr(round(y_dim * 3/4) + 6, centre[0] - len(wait_msg)//2, wait_msg, curses.A_BLINK)
        
        # 1. Temporarily enable blocking mode
        self.stdscr.nodelay(False)
        # 2. Wait for a key press
        self.stdscr.getch()
        # 3. Restore non-blocking mode
        self.stdscr.nodelay(True) 

        self.stdscr.clear()
        


    # NEW: Curses function to get the raise amount
    def _get_raise_amount(self, player, min_raise_to = 0):
        self.stdscr.nodelay(False) # Enter blocking mode for input
        curses.curs_set(1) # Show cursor
        
        current_input = ''
        
        # Display the prompt for the raise amount
        prompt_y, prompt_x = UIConfig.BETTING_ROW - 1,  player.x
        
        while True:
            # Clear input line
            self.clear_area(prompt_y, 0,prompt_y + 1, self.max_x - UIConfig.MARGIN_X - UIConfig.POT_WIDTH)
            # Display current input
            display_text = f"Raise by\n>> £{current_input}"
            self.addstr(prompt_y, prompt_x, display_text.ljust(UIConfig.PLAYER_WIDTH))
            self.stdscr.refresh()
            
            # Move cursor to end of input text
            try:
                # The position needs to be calculated based on the length of the *displayed* input
                # Offset by 1 for the prompt x, and then by the length of the string before the input box
                cursor_x = prompt_x + 4 + len(current_input) 
                self.stdscr.move(prompt_y + 1, cursor_x)
            except curses.error:
                 # If cursor positioning fails, continue
                 pass 

            key = self.stdscr.getch()

            if key in (curses.KEY_ENTER, 10): # Enter key
                try:
                    amount = int(current_input)
                    if amount >= min_raise_to:
                        self.stdscr.nodelay(True) # Exit blocking mode
                        curses.curs_set(0) # Hide cursor
                        return amount
                    else:
                        self.addstr(prompt_y, prompt_x, f"Raise must be at least {min_raise_to}", wait=0.5)
                        current_input = str(min_raise_to) # Reset to minimum
                except ValueError:
                    self.addstr(prompt_y, prompt_x, "Invalid amount. Please enter a number.", wait = 0.5)
                    current_input = str(min_raise_to) # Reset to minimum

            elif key in (curses.KEY_BACKSPACE, 127): # Backspace
                if len(current_input) > 0:
                    current_input = current_input[:-1]
                else:
                    # Allow backspace to remove the minimum required amount if the input is empty
                    current_input = ''

            elif chr(key) in string.digits: # Digit keys
                current_input += chr(key)
            # Allow 'Esc' to cancel raise (treat as a call/check)
            elif key == 27:
                self.stdscr.nodelay(True)
                curses.curs_set(0)
                # Return the minimum amount required to call/check
                return 'CANCEL'


    # NEW: Main function to get human action
    def get_human_action(self, player, to_call):
        """
        Pauses the game, draws the action options, and waits for key input.
        """
        self.stdscr.nodelay(False) # Enter blocking mode
        curses.curs_set(1) # Show cursor
        
        prompt_y, prompt_x = UIConfig.BETTING_ROW - 1, player.x
        
        # 1. Determine action names based on to_call
        if to_call == 0:
            call_action = 'Check'
            call_key = 'C'
        else:
            call_action = f'Call £{to_call:.2f}'
            call_key = 'C'
            

        
        # 2. Display Action Prompt
        options = []
        options.append(f"{call_action} ({call_key})")
        options.append("Fold (F)")
        
        # Only allow raise if the player has enough stack to cover the raise amount
        can_raise = player.stack > to_call 
        if can_raise:
            options.append(f"Raise (R) ")
        
        static_options_text = " / ".join(options)
        
        current_input = ''
        last_drawn_input = ' '
        # 3. Wait for valid key input
        while True:
            curses.curs_set(1) 
            # --- REDRAW LOGIC (Flicker Fix) ---
            if current_input != last_drawn_input:
                prompt_text = static_options_text + '\n>> ' + current_input
                
                # Clear and redraw the prompt area
                self.clear_area(prompt_y, 0, prompt_y + 1, self.max_x - UIConfig.MARGIN_X - UIConfig.POT_WIDTH)
                self.addstr(prompt_y, prompt_x, prompt_text.ljust(UIConfig.PLAYER_WIDTH))
                
                # Move cursor
                try:
                    cursor_x = prompt_x + 3 + len(current_input) 
                    self.stdscr.move(prompt_y + 1, cursor_x)
                except curses.error:
                     pass 
                
                last_drawn_input = current_input

            key = self.stdscr.getch()
            try:
                char = chr(key) if chr(key) in string.ascii_letters + string.digits else ''
            except:
                char = ''

            if key in (curses.KEY_ENTER, 10): # Enter key
                if current_input == 'F':
                    action = 'fold'
                    amount = 0
                    break
                
                elif current_input == call_key:
                    action = 'call' if to_call > 0 else 'check'
                    # The amount is the total bet after calling/checking
                    amount = to_call
                    break
                    
                elif current_input == 'R' and can_raise:
                    # 4. Handle Raise input (using helper function for numerical input)
                    amount = self._get_raise_amount(player)
                    action = 'raise'
                    # Check if the raise amount is within stack limit
                    if amount == 'CANCEL':
                        # If canceled, clear input and continue the loop
                        current_input = ''
                        continue 

                    if amount > player.stack: amount = player.stack
                    if amount != 0: break

                # Exit game on Shift+Q
                elif char == 'Q':
                    raise Exception("User requested exit.")
                
                current_input = ''

            elif key in (curses.KEY_BACKSPACE, 127): # Backspace
                if len(current_input) > 0:
                    current_input = current_input[:-1]
                else:
                    # Allow backspace to remove the minimum required amount if the input is empty
                    current_input = ''

            else:
                current_input += char

                    # Exit on Shift+Q (handled on key press, not only on enter)
            if key == ord('Q'):
                raise Exception("User requested exit.")




            # Ignore other keys and keep waiting
        
        # Cleanup input line
        self.clear_area(prompt_y, 0,prompt_y, self.max_x - UIConfig.MARGIN_X - UIConfig.POT_WIDTH)
        self.stdscr.nodelay(True) # Back to non-blocking
        curses.curs_set(0) # Hide cursor
        
        return action, amount
    
    # --- NEW REUSABLE INPUT FUNCTION ---
    def get_entered_input(self, y, x, prompt_text, default_value='', is_numeric=False, allowed_input = []):
        """
        Gets a string input from the user at a specified position, confirmed by Enter.
        Handles basic editing (backspace).
        """
        # 1. Setup Curses for Blocking Input
        self.stdscr.nodelay(False) # Blocking mode

        current_input = default_value
        
        # Area to clear (make sure we cover the prompt and the input line below it)
        clear_y_start = y
        clear_y_end = y + 1 # Prompt on Y, Input on Y+1

        while True:
            curses.curs_set(1)
            # 2. Redraw the prompt and current input
            self.clear_area(clear_y_start, 0, clear_y_end, self.max_x)
            
            # Draw the static prompt text
            self.addstr(y, x, prompt_text)
            
            # Draw the input below the prompt
            input_y = y + 1
            input_prompt = '>> '
            full_input_line = f"{input_prompt}{current_input}"
            self.addstr(input_y, x, full_input_line)
            


            # 3. Move cursor and get key
            try:
                # x position is x + length of '>> ' + length of current_input
                cursor_x = x + len(input_prompt) + len(current_input)
                self.stdscr.move(input_y, cursor_x)
            except curses.error:
                pass

            key = self.stdscr.getch()

            # 4. Process Key Input
            if key in (curses.KEY_ENTER, 10): # Enter key
                if not allowed_input: break
                elif current_input in allowed_input: break
                else: 
                    curses.curs_set(0)
                    self.clear_area(clear_y_end, 0, clear_y_end, self.max_x)
                    self.addstr(input_y, x, input_prompt + (RED + 'Invalid Input' + END).ljust(UIConfig.COMMUNITY_WIDTH), wait = 1.0)
                    current_input = ''
                    continue

            elif key in (curses.KEY_BACKSPACE, 127): # Backspace
                if len(current_input) > 0:
                    current_input = current_input[:-1]
            
            # Allow printable characters (or digits if numeric mode)
            elif 32 <= key <= 126: 
                char = chr(key)
                if is_numeric and char in string.digits:
                    current_input += char
                elif not is_numeric:
                    current_input += char
            
            elif key == 27: # ESC key
                current_input = '' 
                break

        # 5. Cleanup and Return
        # self.clear_area(clear_y_start, 0, clear_y_end, self.max_x)
        self.stdscr.nodelay(True) # Back to non-blocking
        curses.curs_set(0) # Hide cursor
        return current_input.strip()
