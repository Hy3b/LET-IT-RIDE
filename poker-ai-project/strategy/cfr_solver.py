class NodeCFR:
    def __init__(self, num_actions):
        self.regret_sum = [0.0] * num_actions
        self.strategy_sum = [0.0] * num_actions
        self.strategy = [1.0 / num_actions] * num_actions

    def get_strategy(self, realization_weight):
        """Cập nhật chiến lược dựa trên Regret Matching"""
        normalizing_sum = 0
        for a in range(len(self.regret_sum)):
            self.strategy[a] = self.regret_sum[a] if self.regret_sum[a] > 0 else 0
            normalizing_sum += self.strategy[a]

        for a in range(len(self.strategy)):
            if normalizing_sum > 0:
                self.strategy[a] /= normalizing_sum
            else:
                self.strategy[a] = 1.0 / len(self.strategy)
            
            self.strategy_sum[a] += realization_weight * self.strategy[a]

        return self.strategy
        
# Thuật toán duyệt đệ quy (Recursive CFR) sẽ được implement tại đây để 
# duyệt qua toàn bộ cây và cập nhật regret_sum cho mỗi node.