"""Core data models for Poker game.
Extracted from poker_ai.py - Card, Deck, Hand ranking logic.
"""

import random
from itertools import combinations
from collections import Counter

# ── Card Constants ─────────────────────────────────────────────────────────────
SUITS = ['\u2660', '\u2665', '\u2666', '\u2663']  # Spade, Heart, Diamond, Club
RANKS = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
RANK_VALUE = {r: i+2 for i, r in enumerate(RANKS)}  # 2->2, 3->3, ..., A->14

HAND_NAMES = [
    "Bai cao",        # 0: High card
    "Mot doi",        # 1: One pair
    "Hai doi",        # 2: Two pairs
    "Bo ba",          # 3: Three of a kind
    "Sanh",           # 4: Straight
    "Thung",          # 5: Flush
    "Cu lu",          # 6: Full house
    "Tu quy",         # 7: Four of a kind
    "Thung sanh"      # 8: Straight flush
]


class Card:
    """Representation of a playing card."""
    def __init__(self, rank, suit):
        if rank not in RANKS:
            raise ValueError(f"Invalid rank: {rank}")
        if suit not in SUITS:
            raise ValueError(f"Invalid suit: {suit}")
        self.rank = rank
        self.suit = suit
    
    def __repr__(self):
        return f"{self.rank}{self.suit}"
    
    def __eq__(self, other):
        if isinstance(other, Card):
            return self.rank == other.rank and self.suit == other.suit
        return False
    
    def __hash__(self):
        return hash((self.rank, self.suit))
    
    @staticmethod
    def from_string(card_str):
        """Parse card from string like 'As', 'Kh', '10d', '2c'."""
        if len(card_str) < 2:
            raise ValueError(f"Invalid card string: {card_str}")
        if card_str[-1] not in 'shdc':
            raise ValueError(f"Invalid suit in: {card_str}")
        
        suit_char = card_str[-1]
        suit_map = {'s': SUITS[0], 'h': SUITS[1], 'd': SUITS[2], 'c': SUITS[3]}
        rank = card_str[:-1]
        
        return Card(rank, suit_map[suit_char])


class Deck:
    """Standard 52-card deck."""
    def __init__(self):
        self.cards = self._create_deck()
        self.shuffle()
    
    def _create_deck(self):
        """Create a fresh deck of 52 cards."""
        return [(r, s) for s in SUITS for r in RANKS]
    
    def shuffle(self):
        """Shuffle the deck."""
        random.shuffle(self.cards)
    
    def draw(self, n=1):
        """Draw n cards from the deck."""
        if n > len(self.cards):
            raise ValueError(f"Cannot draw {n} cards from {len(self.cards)}-card deck")
        cards = []
        for _ in range(n):
            cards.append(self.cards.pop())
        return cards
    
    def remaining(self):
        """Return number of remaining cards."""
        return len(self.cards)
    
    def reset(self):
        """Reset deck to full."""
        self.cards = self._create_deck()
        self.shuffle()


class Hand:
    """Represents a poker hand."""
    def __init__(self, five_cards):
        """Initialize with exactly 5 cards."""
        if len(five_cards) != 5:
            raise ValueError(f"Hand requires 5 cards, got {len(five_cards)}")
        self.cards = five_cards
        self.rank_value, self.groups = self._evaluate(five_cards)
    
    @staticmethod
    def _evaluate(five_cards):
        """Evaluate hand rank. Returns (category, groups)."""
        ranks = sorted([RANK_VALUE[r] for r, s in five_cards], reverse=True)
        suits = [s for r, s in five_cards]
        
        # Check flush
        flush = len(set(suits)) == 1
        
        # Check straight
        straight = (ranks[0] - ranks[4] == 4 and len(set(ranks)) == 5)
        # Special case: A-2-3-4-5 (wheel)
        if set(ranks) == {14, 2, 3, 4, 5}:
            straight, ranks = True, [5, 4, 3, 2, 1]
        
        # Frequency analysis
        cnt = Counter(ranks)
        freq = sorted(cnt.values(), reverse=True)
        groups = sorted(cnt.keys(), key=lambda x: (cnt[x], x), reverse=True)
        
        # Determine hand category
        if straight and flush:
            category = 8  # Straight flush
        elif freq == [4, 1]:
            category = 7  # Four of a kind
        elif freq == [3, 2]:
            category = 6  # Full house
        elif flush:
            category = 5  # Flush
        elif straight:
            category = 4  # Straight
        elif freq == [3, 1, 1]:
            category = 3  # Three of a kind
        elif freq == [2, 2, 1]:
            category = 2  # Two pair
        elif freq == [2, 1, 1, 1]:
            category = 1  # One pair
        else:
            category = 0  # High card
        
        return (category, groups)
    
    def rank(self):
        """Return hand rank tuple for comparison."""
        return (self.rank_value, self.groups)
    
    def name(self):
        """Return human-readable hand name."""
        return HAND_NAMES[self.rank_value]
    
    def __gt__(self, other):
        return (self.rank_value, self.groups) > (other.rank_value, other.groups)
    
    def __lt__(self, other):
        return (self.rank_value, self.groups) < (other.rank_value, other.groups)
    
    def __eq__(self, other):
        return (self.rank_value, self.groups) == (other.rank_value, other.groups)
    
    def __repr__(self):
        return f"Hand({self.name()}): {self.cards}"


def best_hand_from_seven(seven_cards):
    """Find best 5-card hand from 7 cards.
    
    Args:
        seven_cards: List of (rank, suit) tuples
    
    Returns:
        Hand: Best hand object
    """
    best = None
    for combo in combinations(seven_cards, 5):
        hand = Hand(list(combo))
        if best is None or hand > best:
            best = hand
    return best
