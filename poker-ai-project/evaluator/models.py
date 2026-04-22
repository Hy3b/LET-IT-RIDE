class Card:
    """
    Lớp Card (Tĩnh) - Mã hóa lá bài thành một số nguyên 32-bit (sử dụng phương pháp Cactus Kev's).
    Việc này giúp việc tính toán và so sánh bài đạt tốc độ cực cao, O(1).
    
    Cấu trúc mã hóa 32-bit:
    +--------+--------+--------+--------+
    |xxxbbbbb|bbbbbbbb|cdhsrrrr|xxpppppp|
    +--------+--------+--------+--------+

    p = số nguyên tố đại diện cho Rank (2=2, 3=3, 4=5, 5=7,..., A=41)
    r = Rank của lá bài (2=0, 3=1, 4=2, 5=3,..., A=12)
    cdhs = Bit đại diện cho Chất (Club, Diamond, Heart, Spade)
    b = Bit phụ thuộc vào Rank của lá bài
    """

    RANK_TO_INT = {'2': 0, '3': 1, '4': 2, '5': 3, '6': 4, '7': 5, '8': 6, '9': 7, 'T': 8, 'J': 9, 'Q': 10, 'K': 11, 'A': 12}
    INT_TO_RANK = {v: k for k, v in RANK_TO_INT.items()}
    
    # Số nguyên tố tương ứng với các Rank: 2, 3, 4, 5, 6, 7, 8, 9, T, J, Q, K, A
    PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41]

    # Chất: s (spades), h (hearts), d (diamonds), c (clubs)
    SUIT_TO_INT = {'s': 1, 'h': 2, 'd': 4, 'c': 8}
    INT_TO_SUIT = {1: 's', 2: 'h', 4: 'd', 8: 'c'}

    @staticmethod
    def new(card_string):
        """
        Khởi tạo lá bài nguyên thủy 32-bit từ chuỗi (Vd: 'Ah', 'Ks', '2c')
        """
        rank_char = card_string[0]
        suit_char = card_string[1]
        
        rank_int = Card.RANK_TO_INT[rank_char]
        suit_int = Card.SUIT_TO_INT[suit_char]
        rank_prime = Card.PRIMES[rank_int]

        # Bit tương ứng cho Rank: Dịch trái số 1 đi 'rank_int' lần
        bit_rank = 1 << rank_int << 16
        
        # Tổ hợp tất cả lại thành số nguyên 32-bit
        suit = suit_int << 12
        rank = rank_int << 8

        return bit_rank | suit | rank | rank_prime

    @staticmethod
    def int_to_string(card_int):
        """
        Chuyển đổi ngược từ số nguyên 32-bit về dạng chuỗi dễ đọc (Vd: 'Ah')
        """
        rank_int = (card_int >> 8) & 0xF
        suit_int = (card_int >> 12) & 0xF
        
        return Card.INT_TO_RANK[rank_int] + Card.INT_TO_SUIT[suit_int]

    @staticmethod
    def get_rank_int(card_int):
        return (card_int >> 8) & 0xF

    @staticmethod
    def get_suit_int(card_int):
        return (card_int >> 12) & 0xF

class Deck:
    """
    Quản lý bộ bài 52 lá bằng cấu trúc 32-bit.
    """
    import random

    def __init__(self):
        self.cards = self.get_full_deck()

    def get_full_deck(self):
        cards = []
        for rank in Card.RANK_TO_INT.keys():
            for suit in Card.SUIT_TO_INT.keys():
                cards.append(Card.new(rank + suit))
        return cards

    def shuffle(self):
        self.random.shuffle(self.cards)

    def draw(self, n=1):
        if n == 1:
            return self.cards.pop()
        return [self.cards.pop() for _ in range(n)]

# ----- Test nhẹ ở cuối file -----
if __name__ == "__main__":
    card1 = Card.new('Ah') # Át Cơ
    card2 = Card.new('Kd') # Già Rô
    
    print(f"Ah trong máy tính (32-bit): {bin(card1)} (Hệ 10: {card1})")
    print(f"Kd trong máy tính (32-bit): {bin(card2)} (Hệ 10: {card2})")
    
    print(f"Kiểm tra giải mã ngược: {Card.int_to_string(card1)}, {Card.int_to_string(card2)}")
