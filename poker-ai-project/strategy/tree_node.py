import math

class InformationSetNode:
    def __init__(self, game_state, parent=None, parent_action=None):
        self.game_state = game_state      # Trạng thái hiện tại của ván bài (bài chung, pot, cược...)
        self.parent = parent              # Nút cha
        self.parent_action = parent_action # Hành động dẫn đến nút này
        self.children = []                # Danh sách các nút con
        
        # Thống kê cho MCTS
        self.visits = 0                   # Số lần thuật toán đi qua nút này
        self.total_value = 0.0            # Tổng giá trị chiến thắng thu được
        
        # Danh sách các hành động hợp lệ (Legal Actions): Call, Fold, Raise...
        self.untried_actions = game_state.get_legal_actions()
        
    def ucb_score(self, exploration_constant=1.414):
        """Công thức UCB (Upper Confidence Bound) để chọn nhánh tối ưu"""
        if self.visits == 0:
            return float('inf')
        
        exploitation = self.total_value / self.visits
        exploration = exploration_constant * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploitation + exploration

    def add_child(self, action, next_state):
        """Mở rộng cây bằng cách thêm nút con"""
        child_node = InformationSetNode(next_state, parent=self, parent_action=action)
        self.untried_actions.remove(action)
        self.children.append(child_node)
        return child_node