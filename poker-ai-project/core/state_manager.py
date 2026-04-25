"""Game state management - tracks game phase, bets, cards, history.
Extracted from poker_ai.py - GameState class for managing round state.
"""

from .models import Deck


class GameState:
    """Manages complete game state for a poker round."""
    
    # Game phases
    PHASE_MENU = 0
    PHASE_PREFLOP = 1
    PHASE_FLOP = 2
    PHASE_TURN = 3
    PHASE_RIVER = 4
    PHASE_SHOWDOWN = 5
    PHASE_END = 6
    
    def __init__(self, player_chips=1000, ai_chips=1000):
        self.player_chips = player_chips
        self.ai_chips = ai_chips
        self.pot = 0
        self.phase = self.PHASE_MENU
        
        # Current round state
        self.deck = None
        self.player_hand = []
        self.ai_hand = []
        self.community = []  # 0-5 cards on board
        self.community_full = []  # All 5 community cards (dealt but not revealed)
        
        # Betting state
        self.current_bet = 0
        self.player_bet = 0
        self.ai_bet = 0
        self.player_last_action = None
        self.ai_last_action = None
        
        # History
        self.action_history = []
        self.message = ""
        self.sub_message = ""
    
    def reset_round(self):
        """Reset state for a new round."""
        self.deck = Deck()
        self.player_hand = []
        self.ai_hand = []
        self.community = []
        self.community_full = []
        self.current_bet = 0
        self.player_bet = 0
        self.ai_bet = 0
        self.player_last_action = None
        self.ai_last_action = None
        self.action_history = []
        self.message = ""
        self.sub_message = ""
    
    def start_round(self, blind_amount):
        """Start a new round with blinds."""
        self.reset_round()
        
        # Post blinds
        self.player_chips -= blind_amount
        self.ai_chips -= blind_amount
        self.pot += blind_amount * 2
        self.player_bet = blind_amount
        self.ai_bet = blind_amount
        self.current_bet = blind_amount
        
        # Deal cards
        self.player_hand = self.deck.draw(2)
        self.ai_hand = self.deck.draw(2)
        self.community_full = self.deck.draw(5)
        self.community = self.community_full[:0]  # Start with no community cards
        
        self.phase = self.PHASE_PREFLOP
        self.message = "Bai da duoc phat! Hay quyet dinh..."
        self.sub_message = f"Blind: {blind_amount} chip"
    
    def post_action(self, action, amount=0):
        """Record a player action.
        
        Args:
            action: "call", "raise", "fold", "check"
            amount: Chips bet (for raise)
        """
        self.action_history.append({
            'action': action,
            'amount': amount,
            'phase': self.phase
        })
    
    def reveal_next_street(self):
        """Progress to next betting street."""
        if self.phase == self.PHASE_PREFLOP:
            self.community = self.community_full[:3]  # Flop
            self.phase = self.PHASE_FLOP
            return "Flop"
        elif self.phase == self.PHASE_FLOP:
            self.community = self.community_full[:4]  # Turn
            self.phase = self.PHASE_TURN
            return "Turn"
        elif self.phase == self.PHASE_TURN:
            self.community = self.community_full[:5]  # River
            self.phase = self.PHASE_RIVER
            return "River"
        elif self.phase == self.PHASE_RIVER:
            self.phase = self.PHASE_SHOWDOWN
            return "Showdown"
        return None
    
    def player_call(self):
        """Player calls."""
        call_amount = max(0, self.current_bet - self.player_bet)
        if call_amount > self.player_chips:
            call_amount = self.player_chips  # All-in
        self.player_chips -= call_amount
        self.player_bet += call_amount
        self.pot += call_amount
        self.player_last_action = "call"
        self.post_action("call", call_amount)
    
    def player_raise(self, raise_amount):
        """Player raises."""
        if raise_amount > self.player_chips:
            raise_amount = self.player_chips  # All-in
        self.player_chips -= raise_amount
        self.player_bet += raise_amount
        self.current_bet = self.player_bet
        self.pot += raise_amount
        self.player_last_action = "raise"
        self.post_action("raise", raise_amount)
    
    def player_fold(self):
        """Player folds."""
        self.player_last_action = "fold"
        self.post_action("fold", 0)
    
    def ai_call(self):
        """AI calls."""
        call_amount = max(0, self.current_bet - self.ai_bet)
        if call_amount > self.ai_chips:
            call_amount = self.ai_chips  # All-in
        self.ai_chips -= call_amount
        self.ai_bet += call_amount
        self.pot += call_amount
        self.ai_last_action = "call"
        self.post_action("ai_call", call_amount)
    
    def ai_raise(self, raise_amount):
        """AI raises."""
        if raise_amount > self.ai_chips:
            raise_amount = self.ai_chips  # All-in
        self.ai_chips -= raise_amount
        self.ai_bet += raise_amount
        self.current_bet = self.ai_bet
        self.pot += raise_amount
        self.ai_last_action = "raise"
        self.post_action("ai_raise", raise_amount)
    
    def ai_fold(self):
        """AI folds."""
        self.ai_last_action = "fold"
        self.post_action("ai_fold", 0)
    
    def get_deck_remaining(self):
        """Get cards not yet seen by AI."""
        known = set(self.ai_hand + self.community)
        from .models import SUITS, RANKS
        all_cards = [(r, s) for s in SUITS for r in RANKS]
        return [c for c in all_cards if c not in known]
    
    def get_status(self):
        """Return current game status summary."""
        return {
            'phase': self.phase,
            'player_chips': self.player_chips,
            'ai_chips': self.ai_chips,
            'pot': self.pot,
            'player_bet': self.player_bet,
            'ai_bet': self.ai_bet,
            'community': self.community,
            'message': self.message,
            'sub_message': self.sub_message
        }
