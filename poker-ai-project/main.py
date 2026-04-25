"""
Poker AI - Main Entry Point
Integrates all modules: Core, Evaluator, Modeling, Strategy, and UI
"""

import sys
from ui.game_ui import PokerGame

# Optional: Parallel ISMCTS for better performance
import multiprocessing as mp
from strategy.ismcts import ISMCTS


def run_mcts_worker(initial_state, iterations):
    """Worker process for parallel MCTS search."""
    mcts = ISMCTS(iterations=iterations)
    return mcts.search(initial_state)


def parallel_ismcts_search(initial_state, total_iterations=5000, num_workers=4):
    """Run MCTS in parallel using multiple processes to avoid GIL."""
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
    # Start the game UI
    game = PokerGame()
    game.run()