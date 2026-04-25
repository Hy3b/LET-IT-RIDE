"""Bayesian probability updater for opponent hand estimation.
Uses Bayes' theorem to update probability distribution of opponent's hand
based on their observed actions and hand strength.

P(Hand | Action) = P(Action | Hand) * P(Hand) / P(Action)
"""

from .heuristics import get_action_likelihood
from .ranges import HandRange
from evaluator.api import EHS_API


class BayesianUpdater:
    def __init__(self, hand_range, ehs_evaluator_func=None):
        """
        Khởi tạo bộ máy suy luận.
        - hand_range: Đối tượng HandRange (từ ranges.py).
        - ehs_evaluator_func: Hàm tính EHS (Thành viên 2). 
                              Nhận vào (hand, board_cards), trả về float 0.0 -> 1.0.
        """
        self.hand_range = hand_range
        
        # Dependency Injection để dễ unit test độc lập
        # Nếu chưa có hàm tính EHS của Thành viên 2, dùng hàm mock tạm.
        if ehs_evaluator_func is None:
            self.ehs_evaluator_func = self._mock_ehs_evaluator
        else:
            self.ehs_evaluator_func = ehs_evaluator_func

    def _mock_ehs_evaluator(self, hand, board_cards):
        """
        Default EHS estimator when core.engine is not provided.
        Uses hand strength heuristic based on card values.
        """
        try:
            # Try to use actual EHS from evaluator
            hole_str = [f"{card[0]}{self._suit_to_char(card[1])}" for card in hand]
            board_str = [f"{card[0]}{self._suit_to_char(card[1])}" for card in board_cards]
            return EHS_API.get_score(hole_str, board_str, mc_simulations=500)
        except:
            # Fallback to simple heuristic
            strength = 0.3
            for card in hand:
                if 'A' in str(card): strength += 0.3
                elif 'K' in str(card): strength += 0.2
                elif 'Q' in str(card): strength += 0.1
            return min(strength, 1.0)
    
    @staticmethod
    def _suit_to_char(suit):
        """Convert suit symbol to character code."""
        suit_map = {'\u2660': 's', '\u2665': 'h', '\u2666': 'd', '\u2663': 'c'}
        return suit_map.get(suit, 's')

    def update_probabilities(self, action, board_cards):
        """
        Cập nhật phân phối xác suất (Posterior) mỗi khi đối thủ hành động.
        
        Tham số:
        - action: Chuỗi hành động ("call", "raise", "fold", ...).
        - board_cards: Danh sách các lá bài chung đã lật (vd: ['As', 'Th', '2c']).
        """
        # Bước 1: Loại bỏ những tay bài không thể cầm do đã xuất hiện trên bàn
        self.hand_range.remove_dead_cards(board_cards)
        
        # Bước 2: Cập nhật bằng định lý Bayes cho từng hand còn lại
        for hand in self.hand_range.probabilities:
            prior = self.hand_range.probabilities[hand]
            
            # Chỉ tính toán nếu tay bài này vẫn còn khả năng xảy ra (tiết kiệm CPU)
            if prior <= 0:
                continue
            
            # Tính sức mạnh tay bài (EHS) - do Thành viên 2 cung cấp
            ehs = self.ehs_evaluator_func(hand, board_cards)
            
            # Lấy Likelihood: P(Action | Hand)
            likelihood = get_action_likelihood(action, ehs)
            
            # Tính Posterior (Chưa chuẩn hóa)
            posterior = prior * likelihood
            
            # Lưu tạm lại
            self.hand_range.update_probability(hand, posterior)
            
        # Bước 3: Chuẩn hóa lại tổng xác suất về 1.0 (tương đương chia cho P(Action))
        self.hand_range.normalize()
        
        return self.hand_range
