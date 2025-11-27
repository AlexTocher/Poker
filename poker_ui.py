import curses
import os
from card_ascii import *
import time

RED_PAIR = 1
BLACK_PAIR = 2
HIGHLIGHT_PAIR = 3
MESSAGE_PAIR = 4

#spacing globals
MARGIN_X = 8
MARGIN_Y = 4
PLAYER_WIDTH = 24
PLAYER_START_ROW = 32

DECK_X = MARGIN_X
DECK_Y = MARGIN_Y
DECK_HEIGHT = 14



COMMUNITY_X = MARGIN_X + 6 + 4 * CARD_WIDTH + MARGIN_X
COMMUNITY_Y = 2 * MARGIN_Y

POT_Y = MARGIN_Y
POT_WIDTH = 32

BETTING_WIDTH = 32


class Visualizer:
    """Helper class to manage drawing on the stdscr."""
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.max_y, self.max_x = self.stdscr.getmaxyx()
        
        # Configure the screen
        curses.curs_set(0) # Hide cursor
        stdscr.nodelay(True) # Non-blocking input
        self.stdscr.timeout(100)
        self.stdscr.clear()

        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
            curses.init_pair(2, curses.COLOR_RED, curses.COLOR_WHITE)
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


    def addstr(self, y: int, x: int, text: str, wait = 0) -> int:
        """
        Helper method to render a multi-line string starting at (y, x).
        It respects newlines and attempts to center each line horizontally.
        Returns the final row index used.
        """

        # --- Curses Color/Attribute Mapping ---
        # Assuming the standard color pairs initialized in __init__
        COLOR_BLACK = curses.color_pair(1)  # Black text on White BG
        COLOR_RED = curses.color_pair(2)  # Red text on White BG
        COLOR_DEFAULT = curses.color_pair(1) 
        
        ANSI_MAP = {
            '\033[90m': COLOR_BLACK, # Black (Default)
            '\033[91m': COLOR_RED,            # Red
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
                
                # Avoid writing off the screen horizontally or vertically
                if current_x < max_x and current_y < max_y:
                    try:
                        self.stdscr.addstr(current_y, current_x, char, current_attr | curses.A_NORMAL)
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