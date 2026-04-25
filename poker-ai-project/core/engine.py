"""Poker game engine - core game flow logic.
Extracted from poker_ai.py - hand evaluation, pot odds, expected value, outs.
"""

import random
from .models import Hand, Deck, best_hand_from_seven, HAND_NAMES


def calculate_outs(hole_cards, community_cards):
    """Count number of outs (cards that improve the hand).
    
    Outs are cards that would improve hand strength to next level.
    
    Args:
        hole_cards: 2-tuple of (rank, suit)
        community_cards: List of (rank, suit) up to 5 cards
    
    Returns:
        outs (int): Number of improving cards
        next_level (str): Name of hand that could be achieved
    """
    if len(hole_cards + community_cards) < 5:
        return 0, ""
    
    current_best = best_hand_from_seven(hole_cards + community_cards)
    current_rank = current_best.rank()[0]
    
    known_cards = set(hole_cards + community_cards)
    
    # All possible cards
    from .models import SUITS, RANKS
    all_cards = [(r, s) for s in SUITS for r in RANKS]
    unknown = [c for c in all_cards if c not in known_cards]
    
    outs = 0
    next_level = ""
    for card in unknown:
        test_hand = best_hand_from_seven(hole_cards + community_cards + [card])
        new_rank = test_hand.rank()[0]
        if new_rank > current_rank:
            outs += 1
            if not next_level:
                next_level = test_hand.name()
    
    return outs, next_level


def pot_odds(call_amount, pot_size):
    """Calculate pot odds - required win probability to justify a call.
    
    Formula: Pot Odds = call_amount / (pot_size + call_amount)
    
    If actual_win_prob > pot_odds, then calling has positive expected value.
    
    Args:
        call_amount: Chips needed to call
        pot_size: Current pot
    
    Returns:
        float: Pot odds in [0, 1]
    """
    total = pot_size + call_amount
    if total == 0:
        return 0.0
    return call_amount / total


def expected_value(win_prob, pot, call_amount):
    """Calculate expected value of a call.
    
    Formula:
        EV = P(win) * pot - P(lose) * call_amount
           = win_prob * pot - (1 - win_prob) * call_amount
    
    EV > 0 means the action has positive expected value (should call).
    EV < 0 means negative expected value (should fold).
    
    Args:
        win_prob: Estimated probability of winning [0, 1]
        pot: Total pot if we win
        call_amount: Chips needed to call
    
    Returns:
        float: Expected value in chips
    """
    return win_prob * pot - (1 - win_prob) * call_amount


def monte_carlo_simulation(hole_cards, community_cards, deck_remaining, n_simulations=1000):
    """Estimate win probability via Monte Carlo simulation.
    
    Algorithm:
        1. Run n_simulations random games
        2. For each simulation:
           - Deal remaining community cards randomly
           - Deal opponent 2 random cards
           - Compare hand strengths
        3. Return win_prob = wins / n_simulations
    
    Args:
        hole_cards: 2 cards in hand
        community_cards: 0-5 cards on board
        deck_remaining: Cards left in deck (excludes known cards)
        n_simulations: Number of Monte Carlo runs
    
    Returns:
        float: Estimated win probability [0, 1]
    """
    wins = 0
    need_community = 5 - len(community_cards)
    
    for _ in range(n_simulations):
        # Shuffle remaining deck
        sim_deck = deck_remaining[:]
        random.shuffle(sim_deck)
        
        # Deal opponent 2 cards
        opponent_hand = [sim_deck.pop(), sim_deck.pop()]
        
        # Complete community cards
        extra_comm = [sim_deck.pop() for _ in range(need_community)]
        full_community = community_cards + extra_comm
        
        # Evaluate best hands
        my_hand = best_hand_from_seven(hole_cards + full_community)
        opp_hand = best_hand_from_seven(opponent_hand + full_community)
        
        if my_hand > opp_hand:
            wins += 1
    
    return wins / n_simulations


def get_deck_remaining(hole_cards, community_cards):
    """Get remaining cards in deck (cards not seen by AI).
    
    Args:
        hole_cards: AI's 2 cards
        community_cards: Board cards
    
    Returns:
        list: Remaining (rank, suit) tuples
    """
    from .models import SUITS, RANKS
    known = set(hole_cards + community_cards)
    all_cards = [(r, s) for s in SUITS for r in RANKS]
    return [c for c in all_cards if c not in known]
