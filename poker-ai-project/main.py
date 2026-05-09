"""
Poker AI - Điểm nhập chín
Tích hợp tất cả các mô đun: Core, Evaluator, Modeling, Strategy, và UI
"""

import sys
from ui.game_ui import PokerGame

# Tùy chọn: ISMCTS song song để có hiệu suất tốt hơn
import multiprocessing as mp
from strategy.ismcts import ISMCTS


def run_mcts_worker(initial_state, iterations):
    """Quá trình worker cho tìm kiếm MCTS song song."""
    mcts = ISMCTS(iterations=iterations)
    return mcts.search(initial_state)


def parallel_ismcts_search(initial_state, total_iterations=5000, num_workers=4):
    """Chạy MCTS song song với nhiều quá trình để tránh GIL."""
    iters_per_worker = total_iterations // num_workers
    pool = mp.Pool(num_workers)
    results = [
        pool.apply_async(run_mcts_worker, (initial_state, iters_per_worker))
        for _ in range(num_workers)
    ]
    pool.close()
    pool.join()
    return [r.get() for r in results]


if __name__ == "__main__":
    # Bắt đầu UI trò chơi
    game = PokerGame()
    game.run()