import unittest
import sys
import os

# Thêm đường dẫn project vào sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modeling.ranges import HandRange
from modeling.heuristics import get_action_likelihood
from modeling.bayesian_update import BayesianUpdater

class TestModeling(unittest.TestCase):
    def setUp(self):
        self.hand_range = HandRange()
    
    def test_1_hand_range_initialization(self):
        """Kiểm tra khởi tạo HandRange"""
        self.assertEqual(len(self.hand_range.all_hands), 1326)
        
        # Thử lấy mẫu một hand ngẫu nhiên
        sampled_hand = self.hand_range.sample_hand()
        self.assertIsNotNone(sampled_hand)
        self.assertEqual(len(sampled_hand), 2)
        print(f"\n[Test Range] Lấy mẫu ngẫu nhiên thành công: {sampled_hand}")
        
    def test_2_remove_dead_cards(self):
        """Kiểm tra loại bỏ lá bài đã biết (dead cards)"""
        dead_cards = ['Ah', 'Kh', 'Qh']
        self.hand_range.remove_dead_cards(dead_cards)
        
        # Đảm bảo các hand chứa dead cards có xác suất bằng 0
        dead_count = 0
        for hand, prob in self.hand_range.probabilities.items():
            if any(card in hand for card in dead_cards):
                self.assertEqual(prob, 0.0)
                dead_count += 1
        print(f"\n[Test Range] Đã loại bỏ thành công {dead_count} tổ hợp có chứa bài chết {dead_cards}")
                
    def test_3_heuristics(self):
        """Kiểm tra logic suy luận hành động (Heuristics)"""
        # Bài mạnh EHS = 0.9, hành động raise
        prob_strong_raise = get_action_likelihood("raise", 0.9)
        self.assertEqual(prob_strong_raise, 0.60)
        
        # Bài rác EHS = 0.1, hành động fold
        prob_weak_fold = get_action_likelihood("fold", 0.1)
        self.assertEqual(prob_weak_fold, 0.85)
        print(f"\n[Test Heuristics] Bài mạnh (EHS=0.9) xác suất Raise: {prob_strong_raise}")
        print(f"[Test Heuristics] Bài yếu (EHS=0.1) xác suất Fold: {prob_weak_fold}")

    def test_4_bayesian_update(self):
        """Giả lập dữ liệu và kiểm tra luồng Bayesian Update"""
        updater = BayesianUpdater(self.hand_range)
        
        # Giả sử Flop ra 3 lá: 2 bích, 5 rô, 9 chuồn
        board_cards = ['2s', '5d', '9c']
        # Đối thủ vừa raise lớn
        action = "raise"
        
        # Cập nhật bằng Bayes
        updated_range = updater.update_probabilities(action, board_cards)
        
        # Lấy top 5 tay bài có khả năng cao nhất để xem kết quả
        top_hands = updated_range.get_most_likely_hands(5)
        self.assertTrue(len(top_hands) > 0)
        
        # Đảm bảo tổng xác suất được chuẩn hóa về xấp xỉ 1
        total_prob = sum(updated_range.probabilities.values())
        self.assertAlmostEqual(total_prob, 1.0, places=5)
        
        # In ra output kết quả giả lập
        print(f"\n[Giả lập Bayes] Board: {board_cards}, Đối thủ: {action}")
        print("Top 5 tay bài đối thủ có khả năng cầm cao nhất:")
        for i, (hand, prob) in enumerate(top_hands, 1):
            print(f"  {i}. {hand}: {prob*100:.2f}%")

if __name__ == '__main__':
    unittest.main()
