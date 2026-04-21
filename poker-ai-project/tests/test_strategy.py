import unittest
import math
import sys
import os

# Thêm đường dẫn project vào sys.path để import được các module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from strategy.tree_node import InformationSetNode
from strategy.cfr_solver import NodeCFR
from strategy.ismcts import ISMCTS

# === MOCK CLASSES ===
# Tạo class giả (Mock) thay thế cho GameState vì core/engine.py chưa hoàn thiện
class MockGameState:
    def __init__(self, actions=None):
        self.actions = actions if actions is not None else ['Call', 'Fold', 'Raise']
        self._is_terminal = False
        
    def get_legal_actions(self):
        return self.actions.copy()
        
    def clone(self):
        return MockGameState(self.actions)
        
    def apply_action(self, action):
        # Giả lập khi thực hiện hành động, game sẽ tiến tới trạng thái kết thúc sau vài bước
        # Ở đây đơn giản hóa luôn là kết thúc luôn để test MCTS không bị lặp vô tận
        self._is_terminal = True
        
    def is_terminal(self):
        return self._is_terminal
        
    def get_reward(self, ai_player_id):
        return 1.0 # Luôn giả sử AI thắng (1 điểm) để test backpropagation


class TestTreeNode(unittest.TestCase):
    def setUp(self):
        self.mock_state = MockGameState(['Call', 'Fold'])
        self.node = InformationSetNode(self.mock_state)

    def test_initialization(self):
        """Test việc khởi tạo Node lấy đúng danh sách actions chưa thử."""
        self.assertEqual(self.node.untried_actions, ['Call', 'Fold'])
        self.assertEqual(self.node.visits, 0)
        self.assertEqual(self.node.total_value, 0.0)

    def test_ucb_score_unvisited(self):
        """Nếu node chưa được thăm (visits=0), UCB phải trả về vô cực."""
        self.assertEqual(self.node.ucb_score(), float('inf'))

    def test_ucb_score_visited(self):
        """Kiểm tra công thức UCB xem tính toán Exploitation và Exploration chuẩn không."""
        self.node.visits = 10
        self.node.total_value = 5.0
        # Cần khởi tạo parent để tính phần log(parent.visits)
        self.node.parent = InformationSetNode(self.mock_state)
        self.node.parent.visits = 100
        
        expected_exploitation = 5.0 / 10.0 # = 0.5
        expected_exploration = 1.414 * math.sqrt(math.log(100) / 10)
        self.assertAlmostEqual(self.node.ucb_score(), expected_exploitation + expected_exploration)

    def test_add_child(self):
        """Test xem mở rộng cây có lưu đúng child và xoá hành động khỏi untried_actions chưa."""
        next_state = MockGameState(['Call', 'Raise'])
        child = self.node.add_child('Call', next_state)
        
        self.assertEqual(self.node.untried_actions, ['Fold']) # 'Call' bị xoá
        self.assertIn(child, self.node.children) # Child đã vào mảng
        self.assertEqual(child.parent_action, 'Call')
        self.assertEqual(child.parent, self.node)


class TestCFRSolver(unittest.TestCase):
    def test_node_cfr_initialization(self):
        """Kiểm tra khởi tạo CFR node với phân bố đều."""
        node = NodeCFR(num_actions=3)
        self.assertEqual(node.regret_sum, [0.0, 0.0, 0.0])
        self.assertEqual(node.strategy, [1/3, 1/3, 1/3])

    def test_get_strategy_positive_regrets(self):
        """Kiểm tra xem khi có hối tiếc dương (positive regret), CFR có cập nhật đúng chiến lược không."""
        node = NodeCFR(num_actions=3)
        node.regret_sum = [10.0, 20.0, 0.0]
        
        # Regret dương tổng cộng = 30. Vậy chiến lược nên là 10/30, 20/30, và 0.
        strategy = node.get_strategy(realization_weight=1.0)
        
        self.assertAlmostEqual(strategy[0], 1/3)
        self.assertAlmostEqual(strategy[1], 2/3)
        self.assertEqual(strategy[2], 0.0)
        
        # strategy_sum cũng phải được cập nhật
        self.assertAlmostEqual(node.strategy_sum[0], 1/3)

    def test_get_strategy_all_negative_regrets(self):
        """Nếu tất cả các hành động đều gây hối tiếc âm (càng làm càng lỗ), nó phải fallback về phân bố đều."""
        node = NodeCFR(num_actions=3)
        node.regret_sum = [-10.0, -5.0, -1.0]
        
        strategy = node.get_strategy(realization_weight=1.0)
        self.assertEqual(strategy, [1/3, 1/3, 1/3])


class TestISMCTS(unittest.TestCase):
    def test_ismcts_search(self):
        """Kiểm tra xem vòng lặp chính của ISMCTS có chạy mượt mà mà không báo lỗi logic không."""
        mock_state = MockGameState(['Call', 'Raise', 'Fold'])
        
        # Tạo ISMCTS với 10 vòng mô phỏng để test cho nhanh
        mcts = ISMCTS(iterations=10)
        
        # MCTS sẽ trả về hành động tốt nhất sau mô phỏng
        best_action = mcts.search(mock_state)
        
        # Hành động trả ra phải thuộc 1 trong 3 hành động ban đầu
        self.assertIn(best_action, ['Call', 'Raise', 'Fold'])


if __name__ == '__main__':
    unittest.main()
