"""Bộ máy trò chơi Poker - logic luồng trò chơi cơ bản.
Trích xuất từ poker_ai.py - đánh giá bài, pot odds, expected value, outs.
"""

import random
from .models import Hand, Deck, best_hand_from_seven, HAND_NAMES


def calculate_outs(hole_cards, community_cards):
    """Đếm số lá bài cải thiện (Outs).
    
    Outs là các lá bài có thể nâng cấp bộ bài lên mức tiếp theo.
    
    Args:
        hole_cards: 2-tuple của (rank, suit)
        community_cards: Danh sách (rank, suit) tối đa 5 lá
    
    Returns:
        outs (int): Số lá bài cải thiện
        next_level (str): Tên bộ bài có thể đạt được
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
    """Tính Pot Odds - xác suất thắng cần thiết để justify một cuộc call.
    
    Công thức: Pot Odds = call_amount / (pot_size + call_amount)
    
    Nếu actual_win_prob > pot_odds, thì call có EV dương.
    
    Args:
        call_amount: Chip cần để call
        pot_size: Pot hiện tại
    
    Returns:
        float: Pot odds trong [0, 1]
    """
    total = pot_size + call_amount
    if total == 0:
        return 0.0
    return call_amount / total


def expected_value(win_prob, pot, call_amount):
    """Tính Expected Value của một cuộc call.
    
    Công thức:
        EV = P(win) * pot - P(lose) * call_amount
           = win_prob * pot - (1 - win_prob) * call_amount
    
    EV > 0 nghĩa là hành động có EV dương (nên call).
    EV < 0 nghĩa là EV âm (nên fold).
    
    Args:
        win_prob: Xác suất thắng dự tính [0, 1]
        pot: Pot tổng nếu chúng ta thắng
        call_amount: Chip cần để call
    
    Returns:
        float: Expected value tính bằng chip
    """
    return win_prob * pot - (1 - win_prob) * call_amount


def monte_carlo_simulation(hole_cards, community_cards, deck_remaining, n_simulations=1000):
    """Ước tính xác suất thắng qua mô phỏng Monte Carlo.
    
    Thuật toán:
        1. Chạy n_simulations trò chơi ngẫu nhiên
        2. Cho mỗi mô phỏng:
           - Lật các lá bài chung còn lại ngẫu nhiên
           - Phát 2 lá ngẫu nhiên cho đối thủ
           - So sánh sức mạnh bài
        3. Trả về win_prob = wins / n_simulations
    
    Args:
        hole_cards: 2 lá trong tay
        community_cards: 0-5 lá trên bàn
        deck_remaining: Lá bài còn lại trong bộ (loại trừ lá đã biết)
        n_simulations: Số lần chạy Monte Carlo
    
    Returns:
        float: Xác suất thắng dự tính [0, 1]
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
    """Lấy các lá bài còn lại trong bộ (lá không được AI nhìn thấy).
    
    Args:
        hole_cards: 2 lá của AI
        community_cards: Lá bài trên bàn
    
    Returns:
        list: Các tuple (rank, suit) còn lại
    """
    from .models import SUITS, RANKS
    known = set(hole_cards + community_cards)
    all_cards = [(r, s) for s in SUITS for r in RANKS]
    return [c for c in all_cards if c not in known]
