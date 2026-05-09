"""
ISMCTS (Information Set Monte Carlo Tree Search)

Thuật toán AI thông minh để chơi Poker.
Cách hoạt động:
  1. Chạy 5000 lần mô phỏng game
  2. Mỗi lần: Giả định bài đối thủ → Chọn hành động → Chơi ngẫu nhiên
  3. Đếm: CALL thắng bao nhiêu? RAISE thắng bao nhiêu? FOLD mất bao nhiêu?
  4. Chọn hành động thắng nhiều nhất

Lợi ích:
  - Không cần biết bài đối thủ
  - Học được từ hàng ngàn tình huống
  - Ra quyết định thông minh hơn random
"""

import random
from strategy.tree_node import InformationSetNode
from modeling.ranges import HandRange
from core.engine import monte_carlo_simulation, get_deck_remaining
from evaluator.api import EHS_API

class ISMCTS:
    def __init__(self, iterations=5000):
        """
        Khởi tạo AI Agent.
        
        Args:
            iterations (int): Số lần mô phỏng (mặc định 5000)
                           - Càng cao → Càng tốt nhưng chậy hơn
                           - 5000 là sự cân bằng giữa tốc độ và chính xác
        
        Ví dụ:
            ai = ISMCTS(iterations=5000)
            ai_agent = ISMCTS(iterations=10000)  # Thông minh hơn, chậy hơn
        """
        self.iterations = iterations

    def search(self, initial_state):
        """
        Hàm CHÍNH: Tìm nước đi tốt nhất sử dụng ISMCTS.
        
        Các bước:
          1. Khởi tạo cây tìm kiếm (gốc = trạng thái hiện tại)
          2. Chạy 5000 lần mô phỏng
          3. Chọn hành động thắng nhiều nhất
        
        Args:
            initial_state: Trạng thái game hiện tại
                         Chứa: Bài của tôi, bài chung, pot, etc.
        
        Returns:
            str: Hành động tốt nhất ("FOLD", "CALL", "RAISE")
        
        Ví dụ:
            game_state = get_current_game_state()
            ai = ISMCTS(iterations=5000)
            best_action = ai.search(game_state)
            print(best_action)  # "CALL" hoặc "RAISE" hoặc "FOLD"
        """
        # Tạo gốc cây (Root Node)
        # Đây là điểm khởi đầu của tất cả tìm kiếm
        root_node = InformationSetNode(initial_state)

        # ========== CHẠY 5000 LầN MÔ PHỏNG ==========
        for iteration in range(self.iterations):
            # iteration = 0, 1, 2, ..., 4999 (tổng 5000 lần)
            
            # ===== Bước 1: SAMPLING (LấY Mẫu BÀI Đᴝ THỦ) =====
            # Vì không biết đối thủ cầm bài gì, ta GIẢ ĐịNH 1 tay bài random.
            # Lần 1: Đối thủ có 5♣ 3♦
            # Lần 2: Đối thủ có K♠ Q♦
            # Lần 3: Đối thủ có J♥ 10♠
            # ...v.v.
            
            simulated_state = initial_state.clone()
            # Clone = Sao chép trạng thái game
            # Lý do: Không muốn sửa game state thật
            
            simulated_state.opponent_hand = self._get_belief_sample(simulated_state)
            # Gán một tay bài random cho đối thủ

            # ===== Bước 2: SELECTION (CHỌN CON ĐƯỜNG TỐT NHẤT) =====
            # Nếu cây đã có những node từ lần trước:
            # → Chọn con đường mà trước đây thắng nhiều nhất
            # 
            # Ví dụ:
            #       [ROOT]
            #       /  |  \
            #    CALL RAISE FOLD
            #   (200w) (50w) (30w)
            #   ↑
            #   Chọn CALL vì thắng 200 lần (nhiều nhất)
            
            node = root_node
            # Bắt đầu từ gốc cây
            
            # While loop: Tiếp tục chọn cho tới khi nào?
            # "Khi tất cả hành động đã thử (not untried_actions)
            #  VÀ node có con (node.children)"
            while not node.untried_actions and node.children:
                # max() = Tìm cái lớn nhất
                # key=lambda c: c.ucb_score() = Dựa vào UCB score
                # UCB = "Điểm số" = (Thắng/Thử) + Bonus cho untested
                node = max(node.children, key=lambda c: c.ucb_score())
                # Chọn node con có UCB score cao nhất
                
                simulated_state.apply_action(node.parent_action)
                # Thực hiện hành động đó trong game (cập nhật state)

            # ===== Bước 3: EXPANSION (MỞ RỘNG CÂY) =====
            # Nếu node hiện tại còn hành động chưa thử:
            # → Chọn 1 hành động random và thêm nó vào cây
            # 
            # Ví dụ: Nếu node có hành động [CALL, RAISE] đã thử,
            #        còn [FOLD] chưa thử
            #        → Chọn FOLD và tạo node con FOLD
            
            if node.untried_actions:
                # Nếu còn hành động chưa thử
                
                action = random.choice(node.untried_actions)
                # Chọn 1 hành động RANDOM từ danh sách chưa thử
                # Ví dụ: action = "FOLD"
                
                simulated_state.apply_action(action)
                # Thực hiện hành động đó (FOLD)
                
                node = node.add_child(action, simulated_state)
                # Tạo node con mới cho hành động FOLD

            # ===== Bước 4: SIMULATION (MÔ PHỎNG NGẪU NHIÊN) =====
            # Sau khi chọn/mở rộng, KHÔNG SÁNG SUỐT nữa.
            # CHỈ CHƠI NGẪU NHIÊN cho tới hết game!
            # 
            # Lý do: Để tìm ra kết quả thực tế của hành động này.
            # Nếu quyết định logic mãi, sẽ mất thời gian.
            #
            # Ví dụ Poker:
            #   Hiện tại: Flop (3 lá)
            #   Mô phỏng:
            #     - Turn lật: 7♠ (random)
            #     - River lật: J♥ (random)
            #     - Showdown: So sánh tay
            #     - Kết quả: Tôi thắng +100 hoặc thua -100
            
            while not simulated_state.is_terminal():
                # is_terminal() = Game đã kết thúc chưa?
                # Loop này chạy cho tới khi game kết thúc
                
                possible_actions = simulated_state.get_legal_actions()
                # Lấy danh sách hành động hợp lệ hiện tại
                # Ví dụ: ["CALL", "RAISE", "FOLD"] hoặc ["CHECK", "BET"]
                
                action = random.choice(possible_actions)
                # Chọn 1 hành động NGẪU NHIÊN từ danh sách
                # Không suy nghĩ, chỉ random!
                
                simulated_state.apply_action(action)
                # Thực hiện hành động đó, cập nhật trạng thái

            # ===== TÍNH KẾT QUẢ (REWARD) =====
            # Game kết thúc, AI thắng bao nhiêu chip?
            reward = simulated_state.get_reward(ai_player_id=1)
            # reward = +50 (thắng 50 chip)
            # reward = -100 (thua 100 chip)
            # reward = 0 (hòa) 

            # ===== Bước 5: BACKPROPAGATION (CẬP NHẬT KẾT QUẢ) =====
            # Mô phỏng kết thúc, có kết quả (reward).
            # Bây giờ "lan truyền" kết quả này LÊN cây!
            # 
            # Ví dụ: Path mô phỏng = ROOT → CALL → RAISE → FOLD → [SHOWDOWN: +50]
            # Backpropagation:
            #   1. Cập nhật FOLD node: visits=1, total_value=+50
            #   2. Cập nhật RAISE node: visits=1, total_value=+50
            #   3. Cập nhật CALL node: visits=1, total_value=+50
            #   4. Cập nhật ROOT: visits=1, total_value=+50
            # 
            # Lý do: Tất cả node trong path này đều đóng góp vào kết quả.
            
            while node is not None:
                # node = None khi đã tới gốc (ROOT.parent = None)
                
                node.visits += 1
                # Cộng 1 lần "thăm" node này
                # Đếm: Node này được thử bao nhiêu lần?
                
                node.total_value += reward
                # Cộng reward (lợi/thua) vào tổng
                # Ví dụ:
                #   Lần 1: total_value = +50
                #   Lần 2: total_value = +50 + (-100) = -50
                #   Lần 3: total_value = -50 + (+20) = -30
                
                node = node.parent
                # Di chuyển lên node cha (gần gốc hơn)
                # Khi node = None, while loop dừng

        # ========== CHỌN HÀNH ĐỘNG TỐT NHẤT ==========
        # Sau 5000 lần mô phỏng, tính toán kết quả:
        # 
        # Ví dụ:
        #   CALL node:   visits=2000, avg_reward=+0.4 ✅ TỐT NHẤT
        #   RAISE node:  visits=1500, avg_reward=-0.2 ❌
        #   FOLD node:   visits=1500, avg_reward=-0.4 ❌
        # 
        # → Chọn CALL (visits cao nhất = đáng tin cậy nhất)
        
        best_child = max(root_node.children, key=lambda c: c.visits)
        # max() = Tìm node con có visits cao nhất
        # key=lambda c: c.visits = Dựa vào số lần thăm
        # best_child = Node con được thử nhiều nhất = đáng tin cậy
        
        return best_child.parent_action
        # Trả về hành động của best node
        # Ví dụ: "CALL"

    def _get_belief_sample(self, state):
        """
        Lấy mẫu bài đối thủ (Phụ trợ cho BƯỚC 1: SAMPLING).
        
        Ý tưởng:
          - Không biết đối thủ cầm bài gì
          - Nên lấy 1 tay bài random
          - Nếu có Bayesian belief (dự đoán từ hành động trước)
            → Dùng Bayesian (thông minh hơn)
          - Nếu không → Chọn random (bình thường)
        
        Args:
            state: Game state hiện tại
        
        Returns:
            list: 2 lá bài cho đối thủ
                  Ví dụ: [Card('5', '♣'), Card('3', '♦')]
        
        Ví dụ:
            # Lần 1: Trả [5♣, 3♦]
            # Lần 2: Trả [K♠, Q♦]
            # Lần 3: Trả [J♥, 10♠]
            # ...v.v.
        """
        
        # Kiểm tra: Có Bayesian belief không?
        if hasattr(state, 'opponent_belief') and state.opponent_belief:
            # hasattr() = "Có attribute opponent_belief không?"
            # state.opponent_belief = Object chứa dự đoán bài đối thủ
            # dựa trên các hành động của họ trước đó
            
            # Nếu CÓ Bayesian belief → Dùng nó (THÔNG MINH)
            # Lấy mẫu từ phân phối xác suất Bayesian
            # Tay bài có xác suất cao → Nhiều khả năng được chọn
            # Tay bài có xác suất thấp → Ít khả năng được chọn
            return state.opponent_belief.sample_hand()
        else:
            # Nếu KHÔNG có Bayesian belief → Chọn random (BÌNH THƯỜNG)
            # Lý do: Chưa có thông tin gì về đối thủ
            
            remaining = get_deck_remaining(state.player_hand, state.community)
            # remaining = Tất cả lá bài CÒN LẠI trong deck
            # = 52 lá TRỪ (2 lá mình + lá chung)
            # Ví dụ: Nếu mình có [A♠, K♥] và bàn [2♠, 7♠, 9♠]
            #        remaining = 52 - 5 = 47 lá còn lại
            
            if len(remaining) >= 2:
                # Nếu còn đủ 2 lá
                return random.sample(remaining, 2)
                # random.sample(remaining, 2) = Chọn 2 lá từ 47 lá
                # Tất cả tổ hợp có xác suất bằng nhau (uniform)
            else:
                # Nếu không đủ 2 lá (hiếm gặp, game gần kết thúc)
                return []
                # Trả về list rỗng