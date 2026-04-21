# main.py
# File chạy chính, kết nối các module
import multiprocessing as mp # Sử dụng đa tiến trình thay vì đa luồng

def run_mcts_worker(initial_state, iterations):
    # Mỗi worker chạy trong một tiến trình riêng biệt, không bị vướng GIL
    mcts = ISMCTS(iterations=iterations)
    return mcts.search_and_return_root(initial_state)

def parallel_ismcts_search(initial_state, total_iterations=5000, num_workers=4):
    iters_per_worker = total_iterations // num_workers
    pool = mp.Pool(num_workers) # Tạo một pool gồm 4 tiến trình độc lập