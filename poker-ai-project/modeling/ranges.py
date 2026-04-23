# ranges.py
# Quản lý tập hợp các tay bài (Hand Ranges)
# Trách nhiệm:
# 1. Khởi tạo xác suất ban đầu (Prior) cho tất cả các hand có thể (1326 tổ hợp).
# 2. Lưu trữ và cập nhật phân phối xác suất hiện tại.
# 3. Phân phối xác suất cho ISMCTS ở bước sau lấy mẫu.

import itertools
import random

def generate_all_starting_hands():
    """Tạo ra 1326 tổ hợp bài tẩy ban đầu."""
    suits = ['s', 'h', 'd', 'c'] # Bích (spades), Cơ (hearts), Rô (diamonds), Chuồn (clubs)
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    deck = [r + s for r in ranks for s in suits]
    
    # Tạo tổ hợp 2 lá từ 52 lá (Trả về list các tuple dạng ('As', 'Kd'))
    return list(itertools.combinations(deck, 2))

class HandRange:
    def __init__(self, all_possible_hands=None):
        """
        Khởi tạo HandRange với xác suất tiên nghiệm (Prior).
        all_possible_hands: danh sách 1326 tổ hợp bài. Nếu None, tự động sinh.
        """
        if all_possible_hands is None:
            self.all_hands = generate_all_starting_hands()
        else:
            self.all_hands = all_possible_hands
            
        self.probabilities = {}
        self.reset()

    def reset(self):
        """Khôi phục về trạng thái xác suất ban đầu (Uniform Prior)."""
        num_hands = len(self.all_hands)
        initial_prob = 1.0 / num_hands if num_hands > 0 else 0
        self.probabilities = {hand: initial_prob for hand in self.all_hands}

    def remove_dead_cards(self, dead_cards):
        """
        Loại bỏ các hand chứa bài đã xuất hiện trên bàn (board_cards) hoặc bài của mình.
        dead_cards: danh sách các lá bài (VD: ['Ah', 'Kd'])
        """
        for hand in list(self.probabilities.keys()):
            # Nếu hand chứa bất kỳ lá bài nào trong dead_cards
            if any(card in hand for card in dead_cards):
                self.probabilities[hand] = 0.0
                
        self.normalize()

    def update_probability(self, hand, new_prob):
        """Cập nhật xác suất cho một hand cụ thể."""
        if hand in self.probabilities:
            self.probabilities[hand] = new_prob

    def normalize(self):
        """Chuẩn hóa tổng xác suất về 1.0 (P(Action) Evidence trong Định lý Bayes)."""
        total = sum(self.probabilities.values())
        if total > 0:
            for hand in self.probabilities:
                self.probabilities[hand] /= total
        else:
            # Nếu tất cả xác suất = 0 (tình huống lỗi logic), reset để tránh crash
            self.reset()

    def get_most_likely_hands(self, top_n=10):
        """Lấy top N tay bài có khả năng cao nhất để in ra debug."""
        sorted_hands = sorted(self.probabilities.items(), key=lambda x: x[1], reverse=True)
        return sorted_hands[:top_n]

    def sample_hand(self):
        """
        Lấy mẫu ngẫu nhiên một tay bài từ phân phối xác suất.
        (Đầu ra quan trọng cho Thành viên 4 đưa vào ISMCTS).
        """
        hands = list(self.probabilities.keys())
        weights = list(self.probabilities.values())
        if sum(weights) == 0:
            return None
        # random.choices trả về list, lấy phần tử đầu tiên
        return random.choices(hands, weights=weights, k=1)[0]
