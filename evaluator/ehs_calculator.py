import random
import itertools
from core.models import Deck, Card
from evaluator.evaluator import LookupEvaluator

class EHSCalculator:
    """
    Chuyên gia Định giá (Hand Strength & Equity).
    Chịu trách nhiệm tính tỷ lệ Thắng/Hòa/Thua dựa trên tổ hợp và Monte Carlo.
    """
    def __init__(self, lookup_evaluator):
        self.evaluator = lookup_evaluator
        
    def _get_dead_cards(self, hole_cards, board_cards):
        """Trả về danh sách 32-bit int của các lá bài đã xuất hiện."""
        return [c for c in hole_cards + board_cards]

    def _get_deck_remaining(self, dead_cards):
        """Lọc ra các lá bài còn nguyên trong bộ."""
        full_deck = Deck().get_full_deck()
        return [c for c in full_deck if c not in dead_cards]

    def calculate_equity_monte_carlo(self, hole_cards, board_cards, num_simulations=2000):
        """
        Tính Equity tổng hợp (Đại diện cho EHS) kết hợp cả sức mạnh hiện tại (HS) và tương lai (Potential).
        Sử dụng Monte Carlo Sampling để chạy hàng ngàn ván đấu giả định thay vì rà soát kiệt quệ 
        (rất lâu nếu ở Pre-flop hoặc Flop).
        
        Trả về: EHS_Score (0.0 đến 1.0)
        """
        dead_cards = self._get_dead_cards(hole_cards, board_cards)
        remaining_deck = self._get_deck_remaining(dead_cards)
        
        wins = 0
        ties = 0
        losses = 0
        
        # Số lá bài chung còn thiếu (để đủ 5 lá)
        cards_to_draw_for_board = 5 - len(board_cards)
        
        for _ in range(num_simulations):
            # Tạo bản sao của bộ bài còn lại bằng random.sample thay vì xáo (rất nhanh)
            # Rút 2 lá cho đối thủ ngẫu nhiên + X lá board còn thiếu
            drawn_cards = random.sample(remaining_deck, 2 + cards_to_draw_for_board)
            
            villain_hole = drawn_cards[:2]
            simulated_board = board_cards + drawn_cards[2:]
            
            # Tổ hợp 7 lá của mình và 7 lá của đối thủ
            hero_7_cards = hole_cards + simulated_board
            villain_7_cards = villain_hole + simulated_board
            
            # Đo sức mạnh bằng Evaluator siêu tốc 2+2
            hero_score = self.evaluator.evaluate_7_cards(hero_7_cards)
            villain_score = self.evaluator.evaluate_7_cards(villain_7_cards)
            
            if hero_score > villain_score:
                wins += 1
            elif hero_score == villain_score:
                ties += 1
            else:
                losses += 1
                
        # Công thức EHS (Equity): Thắng + 50% Hòa chia cho tổng số trận
        ehs = (wins + (ties / 2.0)) / num_simulations
        return ehs

    def calculate_exact_equity_river(self, hole_cards, board_cards):
        """
        Duyệt tổ hợp kiệt quệ (Exact Calculation).
        Nên DÙNG KHI Ở RIVER (Vì lúc này board đã đủ 5 lá, chỉ cần duyệt 1.081 hand của đối thủ), 
        nếu dùng ở Pre-Flop sẽ gây treo máy vì có > 2 triệu tổ hợp.
        """
        if len(board_cards) != 5:
            raise ValueError("Hàm duyệt chính xác này chỉ nên chạy khi Board đã ra đủ 5 lá (River).")
            
        dead_cards = self._get_dead_cards(hole_cards, board_cards)
        remaining_deck = self._get_deck_remaining(dead_cards)
        
        wins, ties, losses = 0, 0, 0
        total_combinations = 0
        
        # Duyệt mọi cặp 2 lá mà đối thủ có thể gầm
        for villain_hole in itertools.combinations(remaining_deck, 2):
            hero_7_cards = hole_cards + board_cards
            villain_7_cards = list(villain_hole) + board_cards
            
            hero_score = self.evaluator.evaluate_7_cards(hero_7_cards)
            villain_score = self.evaluator.evaluate_7_cards(villain_7_cards)
            
            if hero_score > villain_score:
                wins += 1
            elif hero_score == villain_score:
                ties += 1
            else:
                losses += 1
            total_combinations += 1
            
        ehs = (wins + (ties / 2.0)) / total_combinations
        return ehs

# ----- Khối Test Nhanh -----
if __name__ == "__main__":
    from time import time
    evaluator = LookupEvaluator()
    ehs_calc = EHSCalculator(evaluator)
    
    print("\n--- TEST SCENARIO ---")
    # Bài của mình: Đôi Át (AA)
    hole = [Card.new('Ah'), Card.new('Ad')]
    # Bài chung (Flop): 2 Bích, 7 Bích, 9 Bích
    board = [Card.new('2s'), Card.new('7s'), Card.new('9s')]
    
    print("Bài Tẩy: Đôi Át đỏ")
    print("Board Flop: 2s, 7s, 9s (Rất nguy hiểm vì dễ bị đối thủ cầm Thùng Bích)")
    
    # 1. Chạy Monte Carlo Sampling (2000 mô phỏng)
    start_time = time()
    equity_mc = ehs_calc.calculate_equity_monte_carlo(hole, board, 2000)
    end_time = time()
    print(f"\n[Monte Carlo 2000 ván] EHS Tỷ lệ thắng kỳ vọng: {equity_mc:.2%} (Mất {end_time - start_time:.4f} giây)")
