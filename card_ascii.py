from poker_hands import SUITS
import re

CARD_WIDTH  = 11
CARD_HEIGHT = 9

# Define color for hearts and diamonds
RED = '\033[91m' # ANSI escape code for red
BLACK = '\033[90m' # ANSI escape code for black (dark grey)
BLUE = '\033[94m' # ANSI escape code to blue color
MAGENTA = '\033[95m' # ANSI escape code to blue color
END = '\033[0m' # ANSI escape code to reset color

def card_ascii(rank, suit: str, back = False, back_color=RED) -> str:
    """
    Generates ASCII art representation for a single card.
    
    Args:
        rank (str): Rank of the card (e.g., 'A', 'K', '5').
        suit (str): Suit symbol (e.g., '♠', '♥', '♦', '♣').
        
    Returns:
        str: The ASCII art string.
    """

    def generate_card_face(rank, suit):
        """Generates the 5 lines of the inner card art """
        
        # Placeholder for the colored suit symbol (S is a single character placeholder)
        S = suit 
        
        if rank in ['J', 'Q', 'K', 'A']:
            rank_str_top = f"{rank:8}"+ suit
            rank_str_bottom = suit + f"{rank:>8}" 
        else:
            rank_str_top = f"{rank:9}" 
            rank_str_bottom = f"{rank:>9}" 

        if rank in ['A', 'J', 'Q', 'K']:
    
            pictograms = {
                'J': [ # stylized soft cap
                    f"         ",
                    f"    ●    ",
                    f" ▄▆▇█▇▆▄ ",
                    f" ▀▀▀▀▀▀▀ ",
                    f"         "
                ],
                'Q': [ # Tiara / Small Crown
                    f"         ",
                    f" ✱✱✱✱✱✱✱ ",
                    f" ┗┻┻┻┻┻┛ ",
                    f" ▀▀▀▀▀▀▀ ",
                    f"         "
                ],
                'K': [ # Grand Crown
                    f"         ",
                    f"  ╻┃┃┃╻  ",
                    f" ┗┻┻┻┻┻┛ ",
                    f" ▀▀▀▀▀▀▀ ",
                    f"         "
                ]
            }

            if rank == 'A':
                if suit == '♠': # Large Spade
                    pictograms['A'] = [
                        f"   ▗█▖   ",
                        f"  ▗███▖  ",
                        f" ▗█████▖ ",
                        f" ▜█▛█▜█▛ ",
                        f"  ▔ █ ▔  "
                    ]
                elif suit == '♥': # Large Heart
                    pictograms['A'] = [
                        f"  ▂   ▂  ",
                        f" ▟██▆██▙ ",
                        f" ▝█████▘ ",
                        f"  ▝███▘  ",
                        f"   ▝█▘   "
                    ]
                elif suit == '♦': # Large Diamond
                    pictograms['A'] = [
                        f"   ▗█▖   ",
                        f"  ▗███▖  ",
                        f"  █████  ",
                        f"  ▝███▘  ",
                        f"   ▝█▘   "
                    ]
                elif suit == '♣': # Large Club
                    rank_str_top = f"{rank:4}" + "▁   " + suit 
                    pictograms['A'] = [
                        f"   ▟█▙   ",
                        f"  ▁▜█▛▁  ",
                        f" ▟█▙█▟█▙ ",
                        f" ▜█▛█▜█▛ ",
                        f"  ▔ █ ▔  "
                    ]
                else:
                    pictograms['A'] = ["       "] * 5 # Fallback
                
            # If the rank is not a face card, return empty lines (shouldn't happen with proper calling)
            final_lines = pictograms.get(rank, ["     "] * 5)

        else: # if not a picture card or ace

            # Define 5x5 grid layouts using 'S' for a suit symbol, ' ' for space
            pip_layouts_raw = {
                # 2: Top, Bottom
                '2': ["  S  ", "     ", "     ", "     ", "  S  "],
                # 3: Top, Center, Bottom
                '3': ["  S  ", "     ", "  S  ", "     ", "  S  "],
                # 4: Four corners
                '4': ["S   S", "     ", "     ", "     ", "S   S"],
                # 5: Four corners + center
                '5': ["S   S", "     ", "  S  ", "     ", "S   S"],
                # 6: Six sides (3 top, 3 bottom)
                '6': ["S   S", "     ", "S   S", "     ", "S   S"],
                # 7: Six sides + top center
                '7': ["S   S", "  S  ", "S   S", "     ", "S   S"], 
                # 8: Four corners + 4 mid-side
                '8': ["S   S", "S   S", "     ", "S   S", "S   S"],
                # 9: Border 3x3 with center
                '9': ["S   S", "S   S", "  S  ", "S   S", "S   S"],
                # 10: Two columns of 5
                '10': [ "S   S", "S   S", "S   S", "S   S", "S   S"],
            }

            # For number cards, replace the 'S' placeholder with the actual colored symbol
            raw_lines = pip_layouts_raw.get(rank, ["     "] * 5)
            final_lines = ["  " + line.replace('S', S) + "  " for line in raw_lines]

        return [rank_str_top] + final_lines + [rank_str_bottom]
    
    def overlay(top, bottom):
        out = [''] * len(top)
        for i, line_top in enumerate(top):
            for j , char in enumerate(line_top): 
                if char == ' ':
                    out[i] += bottom[i][j]
                else:
                    out[i] += top[i][j]
        return out

    suit_names = SUITS
    suit_symbols = ['♣', '♦', '♥','♠' ]

    suit = suit_symbols[suit_names.index(suit)]

    if back == True:
        S, H, D, C = BLACK + '♠' + END, back_color + '♥' + END, back_color + '♦' + END, BLACK + '♣' + END
        line = [f"{S}",f"{H}",f"{C}",f"{D}"] * 9 
        return "\n".join(["╔═════════╗"] + \
                         ["║" + f"".join(line[start: start + 9]) + "║" for start in range(0, 7) ] + \
                         ["╚═════════╝"])
    

    if suit in ('♥', '♦'):
        color = RED
    else:
        color = BLACK
        
    if rank == 1: rank = 'A'
    elif rank == 11: rank = 'J'
    elif rank == 12: rank = 'Q'
    elif rank == 13: rank = 'K'
    else: rank = str(rank)

    inner_lines = generate_card_face(rank, suit)

    # inner_lines = overlay(top = inner_lines, bottom= generate_face_pictogram('A', suit))
    lines = [
        "╔═════════╗",                         # 0
        f"║{color}{inner_lines[0]}{END}║",     # 6 (Top Rank)
        f"║{color}{inner_lines[1]}{END}║",     # 2
        f"║{color}{inner_lines[2]}{END}║",     # 3
        f"║{color}{inner_lines[3]}{END}║",     # 4
        f"║{color}{inner_lines[4]}{END}║",     # 5
        f"║{color}{inner_lines[5]}{END}║",     # 6
        f"║{color}{inner_lines[6]}{END}║",     # 7 (Bottom Rank)
        "╚═════════╝"                          # 8
    ]
    
    return "\n".join(lines)

# Regex to find ANSI escape codes (colors)
ANSI_ESCAPE = re.compile(r'(\x1b\[[0-9;]*m)')

def string_to_visual_cells(s):
    """
    Converts a string with ANSI codes into a list of 'cells'.
    Each cell is a string containing the character and its active color code.
    Example: "\x1b[31mA\x1b[0m" -> ["\x1b[31mA\x1b[0m"] (Length 1 list)
    """
    tokens = ANSI_ESCAPE.split(s)
    cells = []
    current_style = ""
    old_current_style = ""
    for token in tokens:
        if ANSI_ESCAPE.match(token):
            # It's a color code, update the current style state
            current_style += token
        else:
            # It's visible text, break it into individual chars
            for char in token:
                # We wrap every character in the current style + a reset
                # This ensures that if we move this character, it keeps its color
                # and doesn't bleed into neighbors.
                if current_style != old_current_style:
                    cell = current_style + char 
                    current_style = old_current_style
                else:
                    cell = char
                cells.append(cell) #+ "\033[0m")
                
    return cells

def overlap_cards(cards, v_spacing=3, h_spacing=1, reverse=False):
    if not cards:
        return ""

    # 1. Determine the card images
    card_images = [c.front for c in cards] if not reverse else [c.back for c in cards]
    
    # 2. Calculate total canvas dimensions
    # Get dimensions of a single card (assuming all are same size)
    sample_lines = card_images[0].split('\n')
    card_h = len(sample_lines)
    # We must calculate card width based on VISIBLE characters, not string length
    card_w = len(string_to_visual_cells(sample_lines[0]))

    total_width = (len(cards) - 1) * h_spacing + card_w
    total_height = (len(cards) - 1) * v_spacing + card_h

    # 3. Create a 2D Grid (The Canvas) filled with empty spaces
    # grid[y][x] will hold the specific string for that coordinate
    grid = [[" " for _ in range(total_width)] for _ in range(total_height)]

    i_0, j_0 = 0, 0 

    # 4. Paint cards onto the grid
    for image in card_images:
        lines = image.split('\n')
        for j, line in enumerate(lines):
            # Convert the string line into a list of visual blocks
            visual_cells = string_to_visual_cells(line)
            
            # Determine where to place this line on the canvas
            start_x = i_0
            start_y = j_0 + j
            
            # Overwrite the canvas cells with the new card's cells
            for x, cell in enumerate(visual_cells):
                if start_x + x < total_width and start_y < total_height:
                    grid[start_y][start_x + x] = cell

        # Update offsets for the next card
        j_0 += v_spacing
        i_0 += h_spacing

    # 5. Join the grid back into a single string
    output_lines = ["".join(row) for row in grid]
    return "\n".join(output_lines)
        

GAP_ART = [" " * 11] * 9 

def combine_cards(cards: list[str], n_cards_per_line: int = 13,  discarded_cards = None, overlap = (0,0), reverse = (0,0), justify_width = 0) -> str:
    """
    Takes a list of multiline card strings and combines them horizontally, 
    wrapping to a new line after every n_cards_per_line.

    Returns:
        str: A single multiline string with all cards printed horizontally, wrapped.
    """
    if not cards:
        return ""
        
    discards_to_process = discarded_cards if discarded_cards is not None else []

    
    
    if overlap[0]: card_strings = [overlap_cards(cards, reverse = reverse[0], v_spacing = 1 if reverse[0] else 3)]
    else: card_strings = [c.front for c in cards] if reverse[0] == 0 else [c.back for c in cards]
    if overlap[1]: discards_to_process = [overlap_cards(discards_to_process, reverse = reverse[1], v_spacing = 1 if reverse[1] else 3)]
    else: discards_to_process = [d.front for d in discards_to_process] if reverse[1] == 0 else [d.back for d in discards_to_process]
    
    # 1. Create a unified sequence of card art (list of 9-line strings)
    # This list will contain either a 9-line card string, or the GAP_ART list.
    card_sequence_art = list(card_strings)
    
    # 2. Insert GAP_ART (which represents 1 card unit) if discards are present
    if len(discards_to_process) > 0:
        # GAP_ART itself is used as the marker for the 1-card-unit gap
        card_sequence_art.append(GAP_ART) 
        card_sequence_art.extend(discards_to_process)

    # 3. Split all card art strings into their 9 lines/rows
    processed_art_sequence = []
    for unit in card_sequence_art:
        if isinstance(unit, list): # It's the GAP_ART list
            processed_art_sequence.append(unit)
        else: # It's a normal card art string
            processed_art_sequence.append(unit.split('\n'))
            
    num_units = len(processed_art_sequence) # Max 8 units (5 cards + 1 gap + 2 discards)
    final_output_lines = []
    
    # 4. Chunk the sequence based on n_cards_per_line
    for i in range(0, num_units, n_cards_per_line):
        line_chunk = processed_art_sequence[i : i + n_cards_per_line]
        num_rows = max([len(image) for image in line_chunk])

        # 5. Build the line, row by row
        for row_index in range(num_rows) :
            row_parts = []
            for unit_lines in line_chunk :
                width = len(unit_lines[0])
                # unit_lines is a list of 9 strings (either card art lines or GAP_ART lines)
                if row_index > len(unit_lines) - 1:
                    row_parts.append(' ' * width)
                else:
                    row_parts.append(unit_lines[row_index])
            
            # 6. Join with a single space separator. Since GAP_ART lines are 11 spaces wide,
            # this results in a 1-space separator, creating the 12-space (1 card width) gap.
            final_output_lines.append(" ".join(row_parts))
        
        # Add an empty line between line wraps for better separation
        if i + n_cards_per_line < num_units:
             final_output_lines.append("")

    if justify_width:
        for i, line in enumerate(final_output_lines):
            final_output_lines[i] = line.ljust(justify_width)

    return "\n".join(final_output_lines)


def title_ascii():
    inner_lines = [
    " ▞▚             ▟▙ ", # Line 0: Top rank and suit
    " ▛▜     ▗█▖    ▝▜▛▘", # Line 1: Top part of the spade
    "       ▗███▖       ", # Line 2
    "      ▗█▛ ▜█▖      ", # Line 3
    "     ▗█▛   ▜█▖     ", # Line 3
    "    ▗█▛ ▗█▖ ▜█▖    ", # Line 3
    "   ▗█▛ ▗███▖ ▜█▖   ", # Line 4
    "  ▗█▛ ▗█▛ ▜█▖ ▜█▖  ", # Line 5
    " ▗█▛ ▗██▄▂▄██▖ ▜█▖ ",
    " ▐█▌  ▀▀▔▔▔▀▀  ▐█▌ ",
    " ▝██▆▄▄▆███▆▄▄▆██▘ ", # Line 6: Center point/cutout
    "   ▔▀▀▀▔▕█ ▔▀▀▀▔   ", # Line 7: Neck
    "        ▐█▌        ", # Line 8: Stem top
    " ▟▙     ███     ▞▚ ", # Line 9: Stem bottom
    "▝▜▛▘            ▛▜ "  # Line 10: Bottom rank and suit
]

        # inner_lines = overlay(top = inner_lines, bottom= generate_face_pictogram('A', suit))
    lines = [
        "          " +                               f"╔══════════" +           f"═════════╗          ",           
        f"     " +            f"╔════" +             f"║{BLACK}{inner_lines[0]}{END}" +  f"║"       + f"════╗",
       f"╔════" +             f"║{BLACK}▐▂▞{END} " + f"║{BLACK}{inner_lines[1]}{END}" +  f"║{BLACK} ▟▙{END} ║" +             f"════╗",
       f"║{BLACK} ▀▜{END} " + f"║{BLACK}▐▔▚{END} " + f"║{BLACK}{inner_lines[2]}{END}" +  f"║{BLACK}▝▜▛▘{END}║" + f" {BLACK}▟▙ {END}║",   
       f"║{BLACK} ▚▞{END} " + f"║    " +             f"║{BLACK}{inner_lines[3]}{END}" +  f"║" +       f"    ║" + f"{BLACK}▝▜▛▘{END}║",          
       f"║    " +             f"║    " +             f"║{BLACK}{inner_lines[4]}{END}" +  f"║" +       f"    ║"             + f"    ║",     
       f"║    " +             f"║    " +             f"║{BLACK}{inner_lines[5]}{END}" +  f"║" +       f"    ║"             + f"    ║",     
       f"║    " +             f"║    " +             f"║{BLACK}{inner_lines[6]}{END}" +  f"║" +       f"    ║"             + f"    ║",     
       f"║    " +             f"║    " +             f"║{BLACK}{inner_lines[7]}{END}" +  f"║" +       f"    ║"             + f"    ║",     
       f"║    " +             f"║    " +             f"║{BLACK}{inner_lines[8]}{END}" +  f"║" +       f"    ║"             + f"    ║",     
       f"║    " +             f"║    " +             f"║{BLACK}{inner_lines[9]}{END}" +  f"║" +       f"    ║"             + f"    ║",     
       f"║    " +             f"║    " +             f"║{BLACK}{inner_lines[10]}{END}" + f"║" +       f"    ║"             + f"    ║",  
       f"║{BLACK} ▟▙ {END}" + f"║    " +             f"║{BLACK}{inner_lines[11]}{END}" + f"║" +       f"    ║" + f"{BLACK}▐▗▀▖{END}║",   
       f"║{BLACK}▝▜▛▘{END}" + f"║ {BLACK}▟▙ {END}" + f"║{BLACK}{inner_lines[12]}{END}" + f"║{BLACK}▗▀▚{END} ║" + f"{BLACK}▐▝▄▘{END}║",  
       f"╚════" +             f"║{BLACK}▝▜▛▘{END}" + f"║{BLACK}{inner_lines[13]}{END}" + f"║{BLACK}▝▄▞▖{END}║" +             f"════╝",
       f"     " +             f"╚════" +             f"║{BLACK}{inner_lines[14]}{END}" + f"║" +       f"════╝     ",
        "          " +                               f"╚══════════" +           f"═════════╝          "                          
    ]

    return "\n".join(lines)

if __name__ == '__main__': 
    print(title_ascii())