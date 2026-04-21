from evaluator.models import Card
from evaluator.evaluator import LookupEvaluator
from evaluator.ehs_calculator import EHSCalculator

class EHS_API:
    """
    Điểm trung chuyển (API Interface) - Lớp giao tiếp chuẩn mực cho các Thành Viên khác.
    """
    _evaluator = None
    _ehs_calc = None

    @classmethod
    def _initialize(cls):
        """Khởi tạo một lần (Singleton) để tránh việc phải nạp lại bảng 130MB RAM liên tục."""
        if cls._evaluator is None:
            # Sẽ tự in ra thông báo quá trình tải khi khởi tạo
            cls._evaluator = LookupEvaluator()
            cls._ehs_calc = EHSCalculator(cls._evaluator)

    @classmethod
    def get_score(cls, str_hole_cards, str_board_cards, mc_simulations=2000):
        """
        Giao diện gọn gàng nhất cho Thành viên 1 (Engine) và Thành viên 4 (ISMCTS).
        
        Input: 
            str_hole_cards: list ví dụ ['Ah', 'Ad']
            str_board_cards: list ví dụ ['2s', '7s', '9s']
        Output: EHS dạng Float (0.000 đến 1.000)
        """
        cls._initialize()
        
        # 1. Ép kiểu dữ liệu (từ String thân thiện sang Bitwise tốc độ cao)
        try:
            hole_32bit = [Card.new(c) for c in str_hole_cards]
            board_32bit = [Card.new(c) for c in str_board_cards]
        except KeyError as e:
            raise ValueError(f"⚠️ Định dạng lá bài sai chuẩn! Vui lòng viết kiểu: 'Ah', 'Ts'. Lỗi ở lá {e}")

        # 2. Định tuyến Thuật Toán thông minh dựa theo giai đoạn của ván đấu
        # Nếu ván đấu đã đến vòng River (Đủ 5 lá chung) -> Bật tính năng đo kiệt quệ 100% chính xác
        if len(board_32bit) == 5:
            return cls._ehs_calc.calculate_exact_equity_river(hole_32bit, board_32bit)
            
        # Nếu đang ở Flop (3 lá) hoặc Turn (4 lá) hoặc PreFlop (0 lá) -> Bật Monte Carlo mô phỏng
        else:
            return cls._ehs_calc.calculate_equity_monte_carlo(
                hole_32bit, 
                board_32bit, 
                num_simulations=mc_simulations
            )

# ----- Sách Hướng Dẫn Sử Dụng (Dành cho thành viên khác) -----
if __name__ == "__main__":
    print("⏳ AI đang cấu hình bộ não EHS lần đầu tiên (Singleton init)...")
    
    # Kịch bản 1: Đánh giá sức mạnh ở vòng Flop (Dùng Monte Carlo)
    hole = ['Ah', 'Ad']
    board_flop = ['2s', '7s', '9s']
    score_flop = EHS_API.get_score(hole, board_flop)
    print(f"\n👉 Sức mạnh Đôi Át (ở vòng Flop): {score_flop:.4f}")
    
    # Kịch bản 2: Vẫn là ván bài đó nhưng ở vòng River (Dùng Exact Math)
    # Tự dưng ra thêm con Át Chuồn (Ac), và Già Rô (Kd). Thành Cù Lũ Át (Full House)!
    board_river = ['2s', '7s', '9s', 'Ac', 'Kd']
    score_river = EHS_API.get_score(hole, board_river)
    print(f"👉 Sức mạnh Cù Lũ Át (ở vòng River): {score_river:.4f}")
