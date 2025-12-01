import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, concatenate

# --- Configuration Constants ---
# Max features needed for the fixed-size input vector
MAX_PLAYERS = 8 # Total players including the current AI (used to define max opponent slots)
NUM_CARD_FEATURES = 52 # One-hot encoding for each card (Aces high, 4 suits)
MAX_COMMUNITY_CARDS = 5
INPUT_VECTOR_SIZE = 104 + (MAX_COMMUNITY_CARDS * NUM_CARD_FEATURES) + 8 + (MAX_PLAYERS * 10)
# 104 (Player Hand) + 260 (Community Cards) + 8 (Betting Context) + 80 (Opponent States) = 452
# Let's verify the total size based on the logic:
# 2 Player Cards * 52 = 104
# 5 Community Cards * 52 = 260
# Betting Context = 8 (4 stages + 4 values)
# Opponents (MAX_PLAYERS - 1, since the current player isn't an opponent)
# Assuming 8 total players, 7 opponents. 7 * 10 = 70.
INPUT_VECTOR_SIZE = 104 + 260 + 8 + 70 # Total: 442
# We will use 7 opponent slots.

# --- Helper Functions for Encoding ---

def card_to_one_hot(card):
    """Converts a standard playing card string (e.g., 'Ah', 'Ts') into a 52-feature one-hot vector."""
    if card is None:
        return np.zeros(NUM_CARD_FEATURES)

    ranks = '23456789TJQKA'
    suits = 'shdc' # Spades, Hearts, Diamonds, Clubs
    
    rank = card[0].upper()
    suit = card[1].lower()
    
    rank_index = ranks.find(rank)
    suit_index = suits.find(suit)
    
    if rank_index == -1 or suit_index == -1:
        # Should not happen with valid input
        return np.zeros(NUM_CARD_FEATURES)

    # Index = (rank_index * 4) + suit_index
    index = (rank_index * 4) + suit_index
    
    one_hot = np.zeros(NUM_CARD_FEATURES)
    one_hot[index] = 1.0
    return one_hot

def normalize(value, min_val, max_val):
    """Normalizes a numerical value to be between 0 and 1."""
    if max_val == min_val:
        return 0.0
    return (value - min_val) / (max_val - min_val)

# --- Poker AI Class ---

class PokerAI:
    def __init__(self, player_id):
        self.player_id = player_id
        # Initialize the dual neural network structure
        self.action_model, self.magnitude_model = self._build_models()
        print(f"PokerAI initialized for Player ID: {self.player_id}. Input size: {INPUT_VECTOR_SIZE}")

    def _build_models(self):
        """
        Builds the shared-body, dual-head neural network architecture.
        Policy/Magnitude Network structure: 512 -> 256 -> 128 -> Split Heads.
        """
        # --- Shared Body ---
        input_layer = Input(shape=(INPUT_VECTOR_SIZE,), name='input_layer')
        
        # Dense Layers - Increased capacity for high-dimensional input
        shared_dense_1 = Dense(512, activation='relu', name='shared_dense_1')(input_layer)
        shared_dense_2 = Dense(256, activation='relu', name='shared_dense_2')(shared_dense_1)
        shared_dense_3 = Dense(128, activation='relu', name='shared_dense_3')(shared_dense_2)
        
        # --- Head 1: Action Policy Network (Fold, Call/Check, Raise) ---
        action_head = Dense(32, activation='relu', name='action_head_dense')(shared_dense_3)
        # 3 actions: [Fold, Call/Check, Raise]
        action_output = Dense(3, activation='softmax', name='action_output')(action_head)
        
        action_model = Model(inputs=input_layer, outputs=action_output, name='ActionPolicyNet')
        
        # --- Head 2: Magnitude Network (Raise Amount) ---
        magnitude_head = Dense(32, activation='relu', name='magnitude_head_dense')(shared_dense_3)
        # 1 output: normalized raise amount (0.0 to 1.0)
        magnitude_output = Dense(1, activation='sigmoid', name='magnitude_output')(magnitude_head)
        
        magnitude_model = Model(inputs=input_layer, outputs=magnitude_output, name='MagnitudeNet')

        # Compilation (We will fine-tune the loss/optimizer during the RL phase)
        action_model.compile(optimizer='adam', loss='categorical_crossentropy')
        magnitude_model.compile(optimizer='adam', loss='mse')

        return action_model, magnitude_model

    def _get_input_vector(self, game_state):
        """
        Converts the Game object state into the fixed-size (442) feature vector.
        This is the most crucial part of feature engineering.
        """
        features = []
        
        current_player = game_state.players[self.player_id]
        
        # --- 1. Private Hand Encoding (104 features) ---
        card1_oh = card_to_one_hot(current_player.hole_cards[0] if current_player.hole_cards else None)
        card2_oh = card_to_one_hot(current_player.hole_cards[1] if current_player.hole_cards else None)
        features.extend(card1_oh)
        features.extend(card2_oh)
        
        # --- 2. Community Cards Encoding (260 features) ---
        community_cards = game_state.community_cards
        for i in range(MAX_COMMUNITY_CARDS):
            card = community_cards[i] if i < len(community_cards) else None
            features.extend(card_to_one_hot(card))

        # --- 3. Betting Context (8 features) ---
        
        # Use simple max/min values for initial normalization bounds (needs refinement based on game type)
        MAX_POT = 1000 
        MAX_STACK = 1000
        
        # Normalize pot and stacks
        pot_size_norm = normalize(game_state.pot, 0, MAX_POT)
        to_call_norm = normalize(game_state.current_bet - current_player.current_bet, 0, MAX_POT)
        stack_norm = normalize(current_player.chips, 0, MAX_STACK)
        # Minimum legal raise amount (can be complex, but for now use current_bet as a proxy max)
        min_raise_norm = normalize(game_state.current_bet * 2, 0, MAX_POT) 
        
        features.extend([pot_size_norm, to_call_norm, stack_norm, min_raise_norm])

        # Stage of the Game (One-hot 4 features: Pre-flop, Flop, Turn, River)
        stage_oh = np.zeros(4)
        if game_state.stage == 'pre_flop': stage_oh[0] = 1
        elif game_state.stage == 'flop': stage_oh[1] = 1
        elif game_state.stage == 'turn': stage_oh[2] = 1
        elif game_state.stage == 'river': stage_oh[3] = 1
        features.extend(stage_oh)
        
        # --- 4. Opponent State Encoding (70 features) ---
        
        opponents = [p for p in game_state.players.values() if p.id != self.player_id]
        
        opponent_features = []
        
        for i in range(MAX_PLAYERS - 1): # 7 opponent slots
            if i < len(opponents):
                opponent = opponents[i]
                
                # 1. Normalized Stack Size (1 feature)
                opp_stack_norm = normalize(opponent.chips, 0, MAX_STACK)
                # 2. Has Folded (1 feature)
                opp_folded = 1.0 if opponent.folded else 0.0
                # 3. Normalized Current Bet (1 feature)
                opp_bet_norm = normalize(opponent.current_bet, 0, MAX_POT)
                # 4. Last Action (7 features - simple one-hot encoding for last action)
                # (e.g., [Check, Call, Bet, Raise, Fold, All-in, None/Initial])
                last_action_oh = np.zeros(7)
                # Note: 'last_action' needs to be tracked on the player object for a real implementation
                # For now, we simulate a simple action state:
                if opponent.folded:
                    last_action_oh[4] = 1
                elif opponent.current_bet > 0 and opponent.current_bet == game_state.current_bet:
                    last_action_oh[1] = 1 # Called
                elif opponent.current_bet > 0 and opponent.current_bet > game_state.current_bet:
                    last_action_oh[3] = 1 # Raised
                else:
                    last_action_oh[6] = 1 # Unknown/Initial/Checked

                opponent_features.extend([opp_stack_norm, opp_folded, opp_bet_norm])
                opponent_features.extend(last_action_oh)
                # Total for one opponent: 1 + 1 + 1 + 7 = 10 features
            else:
                # Zero-padding for absent players
                opponent_features.extend(np.zeros(10)) 

        features.extend(opponent_features)
        
        # Final check: the length must exactly match the expected INPUT_VECTOR_SIZE (442)
        if len(features) != INPUT_VECTOR_SIZE:
            print(f"ERROR: Feature vector size mismatch. Expected {INPUT_VECTOR_SIZE}, got {len(features)}")
            # Fallback: Pad or truncate if needed, but this indicates a code bug.
            
        return np.array(features, dtype=np.float32)

    def get_ai_action(self, game_state):
        """
        The main function to get the AI's action based on the current game state.
        It uses the dual network approach.
        """
        # 1. Transform game state into the input vector
        input_vector = self._get_input_vector(game_state)
        # Reshape for the model: (1, 442)
        input_vector = input_vector.reshape(1, INPUT_VECTOR_SIZE) 

        # 2. Get the Policy Action (Fold, Call/Check, Raise)
        action_probabilities = self.action_model.predict(input_vector, verbose=0)[0]
        
        # In a real training environment, you would use these probabilities to sample an action.
        # For a simple deterministic implementation (for testing):
        action_index = np.argmax(action_probabilities) 

        if action_index == 0:
            return 'fold', 0 # Fold
        
        elif action_index == 1:
            # Check if we can check (0 to call) or must call
            to_call = game_state.current_bet - game_state.players[self.player_id].current_bet
            if to_call == 0:
                return 'check', 0 # Check
            else:
                return 'call', to_call # Call
        
        elif action_index == 2:
            # 3. Get the Raise Magnitude if the Policy decided to Raise
            normalized_raise = self.magnitude_model.predict(input_vector, verbose=0)[0][0]
            
            # Convert normalized value (0 to 1) back to a real bet amount.
            # This is complex in poker (needs to respect minimum raise, stack size, etc.)
            
            # Simple example conversion: 
            # Bet size is between min_raise and max_stack
            min_raise = game_state.current_bet # Placeholder: needs to be true min legal raise
            max_raise = game_state.players[self.player_id].chips
            
            # Linear interpolation of the normalized amount
            raise_amount = min_raise + normalized_raise * (max_raise - min_raise)
            
            # Ensure the raise amount is an integer and at least the minimum required
            # And that it doesn't exceed the player's chips
            final_raise = max(min_raise, int(raise_amount))
            final_raise = min(final_raise, max_raise)

            return 'raise', final_raise

        return 'check', 0 # Default fallback