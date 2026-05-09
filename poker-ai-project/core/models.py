"""Các mô hình dữ liệu cơ bản cho game Poker.
Chứa: Card, Deck, Hand ranking logic.
"""

import random
from itertools import combinations
from collections import Counter

# ── Hằng số Card ──────────────────────────────────────────────────────────────
SUITS = ['\u2660', '\u2665', '\u2666', '\u2663']  # Cơ, Tim, Rô, Tép
RANKS = ['2','3','4','5','6','7','8','9','10','J','Q','K','A']
RANK_VALUE = {r: i+2 for i, r in enumerate(RANKS)}  # Giá trị: 2->2, ..., A->14

HAND_NAMES = [
    "Bài cao",        # 0: High card
    "Một đôi",        # 1: One pair
    "Hai đôi",        # 2: Two pairs
    "Ba cây",          # 3: Three of a kind
    "Sảnh",           # 4: Straight
    "Thùng",          # 5: Flush
    "Cù lũ",          # 6: Full house
    "Tứ quý",         # 7: Four of a kind
    "Thùng sảnh"      # 8: Straight flush
]


class Card:
    """Đại diện một lá bài tây."""
    def __init__(self, rank, suit):
        if rank not in RANKS:
            raise ValueError(f"Rank không hợp lệ: {rank}")
        if suit not in SUITS:
            raise ValueError(f"Suit không hợp lệ: {suit}")
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
        """Parse lá bài từ string như 'As', 'Kh', '10d', '2c'."""
        if len(card_str) < 2:
            raise ValueError(f"String lá bài không hợp lệ: {card_str}")
        if card_str[-1] not in 'shdc':
            raise ValueError(f"Suit không hợp lệ: {card_str}")
        
        suit_char = card_str[-1]
        suit_map = {'s': SUITS[0], 'h': SUITS[1], 'd': SUITS[2], 'c': SUITS[3]}
        rank = card_str[:-1]
        
        return Card(rank, suit_map[suit_char])


class Deck:
    """Bộ bài chuẩn 52 lá."""
    def __init__(self):
        self.cards = self._create_deck()
        self.shuffle()
    
    def _create_deck(self):
        """Tạo bộ bài mới đầy đủ 52 lá."""
        return [(r, s) for s in SUITS for r in RANKS]
    
    def shuffle(self):
        """Xáo trộn bộ bài."""
        random.shuffle(self.cards)
    
    def draw(self, n=1):
        """Lấy n lá bài từ bộ."""
        if n > len(self.cards):
            raise ValueError(f"Không thể lấy {n} lá từ {len(self.cards)} lá còn lại")
        cards = []
        for _ in range(n):
            cards.append(self.cards.pop())
        return cards
    
    def remaining(self):
        """Trả về số lá bài còn lại."""
        return len(self.cards)
    
    def reset(self):
        """Đặt lại bộ bài về đầy đủ."""
        self.cards = self._create_deck()
        self.shuffle()


class Hand:
    """Đại diện một bộ bài (5 lá) trong poker."""
    def __init__(self, five_cards):
        """Khởi tạo với chính xác 5 lá bài."""
        if len(five_cards) != 5:
            raise ValueError(f"Hand requires 5 cards, got {len(five_cards)}")
        self.cards = five_cards
        self.rank_value, self.groups = self._evaluate(five_cards)
    
    @staticmethod
    def _evaluate(five_cards):
        """Đánh giá loại bộ bài. Trả về (category, groups)."""
        ranks = sorted([RANK_VALUE[r] for r, s in five_cards], reverse=True)
        suits = [s for r, s in five_cards]
        
        # Kiểm tra Flush
        flush = len(set(suits)) == 1
        
        # Kiểm tra Straight
        straight = (ranks[0] - ranks[4] == 4 and len(set(ranks)) == 5)
        # Trường hợp đặc biệt: A-2-3-4-5 (wheel)
        if set(ranks) == {14, 2, 3, 4, 5}:
            straight, ranks = True, [5, 4, 3, 2, 1]
        
        # Phân tích tần suất
        cnt = Counter(ranks)
        freq = sorted(cnt.values(), reverse=True)
        groups = sorted(cnt.keys(), key=lambda x: (cnt[x], x), reverse=True)
        
        # Xác định loại bộ bài
        if straight and flush:
            category = 8  # Thùng sảnh (Straight flush)
            groups = ranks  # Dùng ranks cho Straight flush
        elif freq == [4, 1]:
            category = 7  # Tứ quý (Four of a kind)
        elif freq == [3, 2]:
            category = 6  # Cù lũ (Full house)
        elif flush:
            category = 5  # Thùng (Flush)
            groups = ranks  # Dùng ranks sắp xếp cao->thấp cho Flush
        elif straight:
            category = 4  # Sảnh (Straight)
            groups = ranks  # Dùng ranks cho Straight
        elif freq == [3, 1, 1]:
            category = 3  # Ba cây (Three of a kind)
        elif freq == [2, 2, 1]:
            category = 2  # Hai đôi (Two pair)
        elif freq == [2, 1, 1, 1]:
            category = 1  # Một đôi (One pair)
        else:
            category = 0  # Bài cao (High card)
            groups = ranks  # Dùng ranks cho High card
        
        return (category, groups)
    
    def rank(self):
        """Trả về tuple hạng bộ bài để so sánh."""
        return (self.rank_value, self.groups)
    
    def name(self):
        """Trả về tên bộ bài theo định dạng người đọc."""
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
    """Tìm bộ bài 5 lá tốt nhất từ 7 lá bài.
    
    Args:
        seven_cards: Danh sách các tuple (rank, suit)
    
    Returns:
        Hand: Đối tượng bộ bài tốt nhất
    """
    best = None
    for combo in combinations(seven_cards, 5):
        hand = Hand(list(combo))
        if best is None or hand > best:
            best = hand
    return best
