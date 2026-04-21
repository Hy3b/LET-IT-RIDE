import os
import urllib.request
import array
from evaluator.models import Card

class LookupEvaluator:
    """
    Sử dụng bảng tra cứu Two Plus Two (2+2) cho tốc độ đánh giá cực nhanh và chính xác nhất.
    Tra cứu sẽ nhảy qua các ID bộ nhớ (pointers) để tìm ra điểm số chỉ sau 7 lần lookup.
    """

    def __init__(self):
        # Đường dẫn tới file HandRanks.dat
        self.dat_file = os.path.join(os.path.dirname(__file__), 'HandRanks.dat')
        self.table = None
        self.load_table()

    def load_table(self):
        if not os.path.exists(self.dat_file):
            print("⚠️ Chưa có file HandRanks.dat (130MB).")
            print("⏳ Đang bắt đầu tải tự động từ Github... (Chỉ phải tải 1 lần, vui lòng chờ!)")
            # Tải bảng 2+2 chuẩn từ repo github
            url = "https://github.com/christophschmalhofer/poker/raw/master/XPokerEval/XPokerEval.TwoPlusTwo/HandRanks.dat"
            urllib.request.urlretrieve(url, self.dat_file)
            print("✅ Tải hoàn tất HandRanks.dat!")
        
        print("⏳ Đang nạp bảng tra cứu vào RAM (Khoảng 130MB)...")
        with open(self.dat_file, 'rb') as f:
            # Bảng chứa tổng cộng 32,487,834 phần tử (số nguyên 32-bit)
            self.table = array.array('i')
            self.table.fromfile(f, 32487834)
        print("✅ Đã nạp xong bảng tra cứu O(1)!")

    @staticmethod
    def cactus_kev_to_2plus2(ck_card):
        """
        Chuyển đổi card format từ 32-bit (models.py) sang dạng index từ 1-52 của TwoPlusTwo.
        """
        rank = Card.get_rank_int(ck_card) # 0 - 12 (0 là 2, 12 là Át)
        suit_flags = Card.get_suit_int(ck_card) # s=1, h=2, d=4, c=8
        
        if suit_flags == 8: suit_val = 0   # Club
        elif suit_flags == 4: suit_val = 1 # Diamond
        elif suit_flags == 2: suit_val = 2 # Heart
        elif suit_flags == 1: suit_val = 3 # Spade
        else: suit_val = 0
        
        # 2+2 Index: 1 đến 52
        return suit_val * 13 + (rank + 1)

    def evaluate_7_cards(self, cards):
        """
        Đánh giá 7 lá bài kết hợp (2 lá trên tay + 5 lá chung).
        Yêu cầu truyền vào list chứa 7 lá bài (đã được mã hóa dạng nguyên thủy 32-bit của models.py)
        Trả về: Điểm số ranking (Điểm CÀNG LỚN bài CÀNG MẠNH, max là 7462)
        """
        if len(cards) != 7:
            raise ValueError("Evaluator 2+2 yêu cầu chính xác 7 lá bài.")

        # Chuyển đổi 7 lá bài về hệ quy chiếu 1-52
        c = [self.cactus_kev_to_2plus2(card) for card in cards]
        
        # O(1) Tra cứu bảng (Nhảy pointer)
        p = self.table[53 + c[0]]
        p = self.table[p + c[1]]
        p = self.table[p + c[2]]
        p = self.table[p + c[3]]
        p = self.table[p + c[4]]
        p = self.table[p + c[5]]
        res = self.table[p + c[6]]
        
        return res

# ----- Khối Test -----
if __name__ == "__main__":
    # Test khởi tạo (Sẽ tự tải file .dat nếu chưa có)
    evaluator = LookupEvaluator()
    
    # Giả lập tình huống
    # Bài trên tay AI: Át Bích (As), Già Bích (Ks)
    # Bài chung (Board): Qs, Js, Ts, 2h, 3d (Sảnh chúa dọn bàn - Royal Flush)
    hole = [Card.new('As'), Card.new('Ks')]
    board = [Card.new('Qs'), Card.new('Js'), Card.new('Ts'), Card.new('2h'), Card.new('3d')]
    
    score = evaluator.evaluate_7_cards(hole + board)
    print(f"\n🏆 Điểm của tay bài Sảnh Chúa (Royal Flush): {score} / 32767")
    print("(Ghi chú: Thường thì TwoPlusTwo format sẽ nhóm Hand lại, Royal Flush điểm sẽ cao nhất)")
