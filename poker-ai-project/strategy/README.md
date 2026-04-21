# Thư mục Strategy (Decision Making)

Thư mục `strategy` là bộ não cốt lõi của dự án AI Poker, chịu trách nhiệm ra quyết định: **Đưa ra các hành động tối ưu nhất (Fold, Call, Raise...) để giúp AI đạt được lợi nhuận cao nhất về lâu dài.**

Trong Poker, chúng ta phải đối mặt với "thông tin không hoàn hảo" (hidden information - chúng ta không biết bài của đối thủ là gì). Do đó, các thuật toán tìm kiếm và ra quyết định thông thường (như Minimax trong cờ vua) không thể áp dụng trực tiếp. Thư mục này chứa các thuật toán AI tiên tiến chuyên dụng cho các trò chơi có thông tin ẩn.

## 📂 Cấu trúc các file

### 1. `ismcts.py` (Information Set Monte Carlo Tree Search)
Đây là thuật toán tìm kiếm trên cây quyết định chuyên dùng cho trò chơi có thông tin không hoàn hảo.
Quy trình hoạt động của ISMCTS bao gồm 5 bước:
- **Determinization**: Lấy mẫu (sample) bài của đối thủ dựa trên xác suất (belief state từ Module Bayes) để tạo ra một trạng thái mô phỏng "hoàn hảo".
- **Selection**: Duyệt cây từ gốc xuống dựa trên công thức UCB (Upper Confidence Bound) để cân bằng giữa việc khai thác (nhánh đang có lợi nhuận cao) và khám phá (nhánh chưa được duyệt nhiều).
- **Expansion**: Thêm các nút hành động mới vào cây.
- **Simulation**: Chơi ngẫu nhiên (rollout) từ trạng thái hiện tại cho đến khi kết thúc ván bài.
- **Backpropagation**: Cập nhật lại kết quả (thắng/thua/hòa) ngược lên các nút gốc.

### 2. `cfr_solver.py` (Counterfactual Regret Minimization)
Thuật toán CFR giúp AI học cách chơi thông qua cơ chế tự chơi (self-play). Mục tiêu là đạt tới **Trạng thái cân bằng Nash (Nash Equilibrium)**, nơi mà chiến thuật của AI là không thể bị khai thác bởi đối thủ.
- AI sẽ tính toán mức "hối tiếc" (regret) nếu như nó không chọn một hành động cụ thể trong quá khứ.
- Sau hàng ngàn ván tự chơi, AI sẽ điều chỉnh chiến lược (strategy) ưu tiên những hành động có mức hối tiếc dương cao nhất (Regret Matching).

### 3. `tree_node.py` (Data structure for Decision Trees)
Định nghĩa cấu trúc dữ liệu `InformationSetNode` được sử dụng để xây dựng cây quyết định trong MCTS. Mỗi nút lưu trữ:
- Trạng thái hiện tại của game (game state).
- Lịch sử hành động, số lần thuật toán duyệt qua (`visits`).
- Tổng lợi nhuận/giá trị kỳ vọng thu được (`total_value`).
- Hàm tính điểm `ucb_score` để lựa chọn nhánh đi tối ưu nhất trong quá trình chọn lựa của MCTS.

## 🤝 Mối liên hệ với các Module khác
- **`core`**: Nhận Game State, danh sách các hành động hợp lệ (Legal actions).
- **`modeling`**: Lấy thông tin phân bố bài của đối thủ (Belief distribution / Range) để thuật toán ISMCTS lấy mẫu (Determinization).
- **`evaluator`**: Sử dụng hàm tính điểm bài / xác định người thắng cuộc ở giai đoạn Simulation (cuối ván bài).
