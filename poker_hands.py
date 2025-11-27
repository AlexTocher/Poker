from collections import Counter
from typing import List, Tuple, Dict, Any
import itertools # <-- NEW: Used to generate combinations

# --- Card and Hand Constants ---

# Rank values for internal comparison (A=14 for high-card/kicker, 1 for low-straight)
# This maps the *input rank key* (int) to the *card's value* (int)
RANK_VALUES: Dict[int, int] = {
    2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 
    10: 10, 11: 11, # J
    12: 12, # Q
    13: 13, # K
    1: 14  # A
}

# NEW: Map for creating descriptive names (int value -> string name)
VALUE_NAMES: Dict[int, str] = {
    2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9", 
    10: "10", 11: "Jack", 12: "Queen", 13: "King", 14: "Ace"
}

RANKS: List[int] = list(RANK_VALUES.keys()) # This is [2, 3, 4, ..., 1]

SUITS = ['Clubs', 'Diamonds', 'Hearts', 'Spades']

# Hand Rank IDs (for comparison, lower is worse, higher is better)
# The first element of the hand-rank tuple is this ID.
HAND_RANKS: Dict[int, str] = {
    1: "High Card",
    2: "Pair",
    3: "Two Pair",
    4: "Three of a Kind",
    5: "Straight",
    6: "Flush",
    7: "Full House",
    8: "Four of a Kind",
    9: "Straight Flush",
    10: "Royal Flush"
}

# Card Hand Type: List of (Rank, Suit) tuples
# CORRECTED: The rank is an int (e.g., 1 for Ace, 13 for King)
Hand = List[Tuple[int, str]] 

# --- Helper Functions for Analysis ---

def _get_rank_values_and_counts(hand: Hand) -> Tuple[List[int], Counter]:
    """
    Analyzes the hand to get sorted rank values and a rank counter.
    Returns: (sorted_rank_values, rank_counts)
    """
    # 1. Convert int ranks to their numerical values (e.g., 1 -> 14)
    values = sorted([RANK_VALUES[rank] for rank, suit in hand], reverse=True)
    
    # 2. Get counts of each rank key
    ranks_only = [rank for rank, suit in hand] # e.g., [1, 13, 12, 10, 11]
    counts = Counter(ranks_only) # e.g., {1:1, 13:1, 12:1, 10:1, 11:1}
    
    return values, counts

def _is_flush(hand: Hand) -> bool:
    """Checks if all cards have the same suit."""
    first_suit = hand[0][1]
    return all(suit == first_suit for rank, suit in hand)

def _is_straight(rank_values: List[int]) -> bool:
    """
    Checks if the ranks form a sequence.
    Handles the special A-5 straight (Ace low).
    """
    # Check for the standard straight sequence
    is_standard_straight = all(rank_values[i] == rank_values[i+1] + 1 for i in range(4))
    
    if is_standard_straight:
        return True
    
    # Check for the A-2-3-4-5 straight (Ace low: 14, 5, 4, 3, 2)
    # The sorted list is [14, 5, 4, 3, 2].
    is_ace_low_straight = (rank_values == [14, 5, 4, 3, 2])
    
    return is_ace_low_straight

# --- Core Evaluation Function (5-Card Hand) ---

def get_poker_hand_rank(hand: Hand) -> Tuple[int, Tuple[int, ...], str]:
    """
    Evaluates a 5-card poker hand and assigns a score tuple for ranking
    and a full descriptive name.

    Args:
        hand (Hand): A list of 5 (Rank, Suit) tuples.

    Returns:
        Tuple[int, Tuple[int, ...], str]: (Rank ID, Kicker Tuple, Descriptive Name)
    """
    if len(hand) != 5:
        raise ValueError("Hand must contain exactly 5 cards.")

    # Get analyzed data
    rank_values, rank_counts = _get_rank_values_and_counts(hand)
    is_flush = _is_flush(hand)
    is_straight = _is_straight(rank_values)
    
    # --- Step 1: Handle Straights and Flushes ---

    # Royal Flush (T-J-Q-K-A and same suit)
    if is_flush and is_straight and rank_values[0] == 14: # Ace high straight
        return (10, (14,), "Royal Flush") # Rank 10, Ace kicker
    
    # Straight Flush (Any 5 in a sequence and same suit)
    if is_flush and is_straight:
        # For A-5 straight, the high card is 5, not 14
        straight_high_card = 5 if rank_values == [14, 5, 4, 3, 2] else rank_values[0]
        high_rank_str = VALUE_NAMES[straight_high_card]
        return (9, (straight_high_card,), f"Straight Flush, {high_rank_str} High")

    # Flush (Any 5 cards of the same suit)
    if is_flush:
        high_rank_str = VALUE_NAMES[rank_values[0]]
        return (6, tuple(rank_values), f"Flush, {high_rank_str} High")

    # Straight (Any 5 cards in a sequence, different suits)
    if is_straight:
        straight_high_card = 5 if rank_values == [14, 5, 4, 3, 2] else rank_values[0]
        high_rank_str = VALUE_NAMES[straight_high_card]
        return (5, (straight_high_card,), f"Straight, {high_rank_str} High")

    # --- Step 2: Handle Grouped Ranks (Pairs, Trips, Quads, Full House) ---
    
    # Get grouped ranks, sorted by count (desc) then by rank value (desc)
    # rank_counts.items() is (rank_key, count), e.g., (13, 2)
    # We sort by count, then by the rank's *value* (e.g., 1=Ace -> 14)
    grouped_ranks = sorted(
        [(count, RANK_VALUES[rank_key]) for rank_key, count in rank_counts.items()],
        key=lambda x: (x[0], x[1]),
        reverse=True
    )
    # Example: Two pair, Aces and Kings. grouped_ranks = [(2, 14), (2, 13), (1, 5)]

    # Four of a Kind (e.g., [4, 4, 4, 4, 9])
    if grouped_ranks[0][0] == 4:
        quad_rank = grouped_ranks[0][1] # Value, e.g., 4
        kicker_rank = grouped_ranks[1][1] # Value, e.g., 9
        quad_rank_str = VALUE_NAMES[quad_rank]
        return (8, (quad_rank, kicker_rank), f"Four of a Kind, {quad_rank_str}s")
    
    # Full House (e.g., [K, K, K, 5, 5])
    if grouped_ranks[0][0] == 3 and grouped_ranks[1][0] == 2:
        trip_rank = grouped_ranks[0][1] # Value, e.g., 13
        pair_rank = grouped_ranks[1][1] # Value, e.g., 5
        trip_rank_str = VALUE_NAMES[trip_rank]
        pair_rank_str = VALUE_NAMES[pair_rank]
        return (7, (trip_rank, pair_rank), f"Full House, {trip_rank_str}s over {pair_rank_str}s")

    # Three of a Kind (e.g., [Q, Q, Q, 7, 3])
    if grouped_ranks[0][0] == 3:
        trip_rank = grouped_ranks[0][1] # Value, e.g., 12
        # The two remaining cards are the kickers, already sorted high-to-low
        kickers = tuple(r for c, r in grouped_ranks[1:])
        trip_rank_str = VALUE_NAMES[trip_rank]
        return (4, (trip_rank, *kickers), f"Three of a Kind, {trip_rank_str}s")

    # Two Pair (e.g., [J, J, 9, 9, 4])
    if grouped_ranks[0][0] == 2 and grouped_ranks[1][0] == 2:
        pair1_rank = grouped_ranks[0][1] # Higher pair value, e.g., 11
        pair2_rank = grouped_ranks[1][1] # Lower pair value, e.g., 9
        kicker_rank = grouped_ranks[2][1] # Kicker value, e.g., 4
        pair1_rank_str = VALUE_NAMES[pair1_rank]
        pair2_rank_str = VALUE_NAMES[pair2_rank]
        return (3, (pair1_rank, pair2_rank, kicker_rank), f"Two Pair, {pair1_rank_str}s and {pair2_rank_str}s")
    
    # Pair (e.g., [8, 8, K, 5, 2])
    if grouped_ranks[0][0] == 2:
        pair_rank = grouped_ranks[0][1] # Value, e.g., 8
        # The three remaining cards are the kickers, already sorted
        kickers = tuple(r for c, r in grouped_ranks[1:])
        pair_rank_str = VALUE_NAMES[pair_rank]
        return (2, (pair_rank, *kickers), f"Pair of {pair_rank_str}s")

    # High Card
    # If nothing else matches
    high_rank_str = VALUE_NAMES[rank_values[0]]
    return (1, tuple(rank_values), f"High Card, {high_rank_str}")

def _reorder_winning_hand(hand: List, score_tuple: Tuple[int, Tuple[int, ...]]) -> List:
    """
    Reorders the 5-card hand (List[CardObject]) based on the score tuple (kickers).
    """
    rank_id = score_tuple[0]
    kicker_values = score_tuple[1]
    
    # For hands where simple high-to-low rank order is sufficient
    if rank_id in [1, 5, 6, 9, 10]:
        # Sorts based on rank value (1=14 for A, 13=13 for K, etc.)
        # Assumes hand is List[CardObject] with .rank attribute
        return sorted(hand, key=lambda card: RANK_VALUES[card.rank], reverse=True)

    # For hands requiring grouped ordering (Pair, Two Pair, Trips, FH, Quads)
    
    # 1. Create a custom sort key map based on the kicker_values
    sort_rank_map = {}
    for i, rank_val in enumerate(kicker_values):
        sort_rank_map[rank_val] = 100 - i 

    # 2. Define the sorting function
    def sort_key(card):
        rank_key = card.rank # e.g., 1 for Ace
        rank_val = RANK_VALUES[rank_key] # e.g., 14
        
        # Primary key: Significance based on position in kicker_values
        primary_key = sort_rank_map.get(rank_val, 0)
        
        # Secondary key: The rank value itself
        return (primary_key, rank_val)

    # Sort the hand. reverse=True ensures the highest significance (primary group) is first.
    reordered_hand = sorted(hand, key=sort_key, reverse=True)
    
    return reordered_hand


# --- Function for 6 or 7 Card Evaluation ---

def get_best_5_card_hand(cards: List) -> Tuple[str, List, List, Tuple[int, Tuple[int, ...]], str]:
    """
    Evaluates a set of 6 or 7 cards (e.g., 2 hole + 5 community) to find the
    absolute best 5-card poker hand combination.
    Assumes 'cards' is a list of CardObjects, each with .rank and .suit.

    Returns:
        Tuple[str, List, List, Tuple[int, Tuple[int, ...]], str]: 
            (Short Hand Name, Best 5-card Hand, Discarded Cards, Score Tuple, Descriptive Name)
    """
    if len(cards) < 5:
        raise ValueError("Must have at least 5 cards to form a hand.")

    # Score format: (rank_id, kicker_tuple, descriptive_name)
    best_score: Tuple[int, Tuple[int, ...], str] = (0, (), "None")
    best_hand_found: List = [] # Will be List[CardObject]

    # Generate all possible 5-card combinations
    for five_card_combo in itertools.combinations(cards, 5):
        # Convert the tuple combination back to a list of CardObjects
        current_hand_objects = list(five_card_combo)
        
        # Convert to the List[Tuple[int, str]] format for get_poker_hand_rank
        current_hand_tuples: Hand = [(c.rank, c.suit) for c in current_hand_objects]
        
        # Get the rank, score, and name for the current 5-card combination
        current_score = get_poker_hand_rank(current_hand_tuples)
        
        # Compare scores: higher score is better (tuple comparison on first 2 elements)
        if (current_score[0], current_score[1]) > (best_score[0], best_score[1]):
            best_score = current_score
            best_hand_found = current_hand_objects
            
    # Reorder the winning hand for presentation clarity
    if best_hand_found:
        # Pass only the 2-element score tuple that _reorder_winning_hand expects
        score_tuple_for_reorder = (best_score[0], best_score[1])
        reordered_best_hand = _reorder_winning_hand(best_hand_found, score_tuple_for_reorder)
    else:
        reordered_best_hand = []
            
    # Calculate Discarded Cards
    cards_set = set(card for card in cards)
    best_hand_set = set(card for card in best_hand_found)
    
    discarded_cards_set = cards_set - best_hand_set
    discarded_cards: List = [card for card in discarded_cards_set]
    
    hand_name = best_score[2] # Get the new descriptive name
            
    # Return all 5 items
    return hand_name, reordered_best_hand, (best_score[0], best_score[1]), discarded_cards

def rank_players(players_list):
    """
    Ranks players based on their player.score and assigns a 0-based rank 
    (0 for 1st place, 1 for 2nd, etc.) to the player.rank attribute.
    
    This function handles ties by assigning the same rank index to tied players.

    Args:
        players_list: A list of Player objects, each having a .score attribute.

    Returns:
        The original list of Player objects (now with the rank attribute set).
    """
    
    # 1. Sort the players by score (highest first) into a new list
    # The original players_list order is not changed.
    sorted_players = sorted(
        players_list, 
        key=lambda player: player.score, 
        reverse=True
    )
    
    current_rank = 0 # 0-based index for the rank
    
    # Check for empty list
    if not sorted_players:
        return players_list
    
    # Assign rank 0 to the top player(s)
    sorted_players[0].rank = 0
    
    # 2. Iterate through the sorted list to assign ranks, handling ties
    for i in range(1, len(sorted_players)):
        current_player = sorted_players[i]
        previous_player = sorted_players[i-1]
        
        # Check for a tie with the previous player
        if current_player.score == previous_player.score:
            # If tied, assign the same rank as the previous player
            current_player.rank = previous_player.rank
        else:
            # If not tied, the rank is the current list index (0-based)
            current_player.rank = i
    
