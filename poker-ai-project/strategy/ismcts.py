import random
from strategy.tree_node import InformationSetNode
# Import giả định từ các module của thành viên khác
# from modeling.ranges import sample_opponent_hand
# from evaluator.ehs_calculator import evaluate_winner

class ISMCTS:
    def __init__(self, iterations=5000):
        self.iterations = iterations

    def search(self, initial_state):
        """Hàm chính để tìm ra nước đi tốt nhất"""
        root_node = InformationSetNode(initial_state)

        for _ in range(self.iterations):
            # 1. Determinization (Lấy mẫu bài đối thủ dựa trên Bayes)
            # Thành viên 3 cung cấp hàm sample_opponent_hand()
            simulated_state = initial_state.clone()
            simulated_state.opponent_hand = self._get_belief_sample(simulated_state)

            # 2. Selection (Chọn lá bài để duyệt)
            node = root_node
            while not node.untried_actions and node.children:
                node = max(node.children, key=lambda c: c.ucb_score())
                simulated_state.apply_action(node.parent_action)

            # 3. Expansion (Mở rộng cây)
            if node.untried_actions:
                action = random.choice(node.untried_actions)
                simulated_state.apply_action(action)
                node = node.add_child(action, simulated_state)

            # 4. Simulation (Chơi ngẫu nhiên đến cuối ván)
            while not simulated_state.is_terminal():
                possible_actions = simulated_state.get_legal_actions()
                action = random.choice(possible_actions)
                simulated_state.apply_action(action)

            # Phân định thắng thua (Thành viên 2 cung cấp hàm evaluate)
            # reward = evaluate_winner(simulated_state)
            reward = simulated_state.get_reward(ai_player_id=1) 

            # 5. Backpropagation (Cập nhật kết quả ngược lên gốc)
            while node is not None:
                node.visits += 1
                node.total_value += reward
                node = node.parent

        # Trả về hành động của nút con có số lần truy cập nhiều nhất (Đáng tin cậy nhất)
        best_child = max(root_node.children, key=lambda c: c.visits)
        return best_child.parent_action

    def _get_belief_sample(self, state):
        """Gọi sang Module Bayes của Thành viên 3 để dự đoán bài đối thủ"""
        # return sample_opponent_hand(state.history, state.public_cards)
        pass # Placeholder