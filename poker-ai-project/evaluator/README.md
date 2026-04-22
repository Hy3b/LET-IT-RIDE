# 📈 Module EHS (Effective Hand Strength) & Đánh giá Tay bài
**Thực hiện bởi: Thành viên 2 (Chuyên gia Định giá - EHS Specialist)**

## 1. Tổng quan Module
Module này đóng vai trò là "con mắt phân tích" của toàn bộ hệ thống AI. Nhiệm vụ cốt lõi là nhận vào các lá bài hiện tại và trả về **Tỷ lệ thắng kỳ vọng (Equity/EHS)** dưới dạng 1 con số từ `0.0` đến `1.0`.

Con số này là nguyên liệu đầu vào sống còn để:
- **Thành viên 3 (Bayes):** Dự đoán mô hình đối thủ.
- **Thành viên 4 (ISMCTS):** Quyết định chọn hành động (Check/Call/Raise) dựa trên Cây tìm kiếm.

---

## 2. Các kỹ thuật tiên tiến đã áp dụng
Module không dùng các câu lệnh rẽ nhánh `if/else` thủ công chậm chạp, mà áp dụng các tiêu chuẩn cao nhất của AI Poker thế giới:

1. **Bitwise & Cactus Kev's Representation (`evaluator/models.py`):**
   - Không sử dụng Object hay Chuỗi ký tự (String) để lưu bài.
   - Mỗi lá bài được nén thành một số nguyên 32-bit `[xxxbbbbb|bbbbbbbb|cdhsrrrr|xxpppppp]`.
   - Giúp cho thao tác định giá trở nên siêu nhẹ và tốn 0 byte bộ nhớ thừa.

2. **Bảng tra cứu 2+2 / TwoPlusTwo (`evaluator/evaluator.py`):**
   - Áp dụng thuật toán O(1) Lookup Table dài 32 triệu phần tử (File `HandRanks.dat` 130MB). 
   - Tốc độ tăng gấp ~1000 lần so với việc dò xét logic thông thường, đáp ứng được hàng trăm ngàn ván đấu một giây.

3. **Monte Carlo Sampling (`evaluator/ehs_calculator.py`):**
   - Thay vì vét cạn hàng triệu ván bài để tìm tỷ lệ thắng (gây treo máy ở Pre-flop và Flop). Thuật toán áp dụng lấy mẫu ngẫu nhiên **2.000 ván**.
   - Thời gian tính toán cho 1 lượt là dưới **~0.03s** nhưng độ lệch số liệu chỉ dao động sai số <1%.

---

## 3. Cấu trúc thư mục

```text
poker/
├── evaluator/
│   ├── api.py                    # (Final Step) Interface gọn gàng nhất cho các team gọi hàm.
│   ├── ehs_calculator.py         # (Step 3) Logic chạy Monte Carlo và Toán Tổ hợp.
│   ├── evaluator.py              # (Step 2) Engine lõi: Đọc file HandRanks.dat.
│   ├── HandRanks.dat             # file ~130M, tự động tải xuống lần tiên nếu chưa có.
│   └── README.md                 # Tài liệu này.
```

---

## 4. Hướng dẫn sử dụng cho các Thành viên khác (API)

Nếu bạn là **Thành viên 1** (Game Engine) hoặc **Thành viên 4** (MCTS), bạn KHÔNG CẦN quan tâm đến thiết kế toán học bên trong.
Bạn chỉ cần tham chiếu đến file cấu hình `evaluator.api` và gọi hàm sinh điểm theo ví dụ dưới đây.

```python
from evaluator.api import EHS_API

# 1. Các lá bài trên tay AI (2 lá)
hole_cards = ['Ah', 'Ad'] # Át Cơ, Át Rô

# 2. Các lá bài chung trên trải trên bàn (Có thể là 0, 3, 4, hoặc 5 lá tuỳ vào Game State)
board_cards = ['2s', '7s', '9s'] 

# 3. Gọi hàm đo lường sức mạnh (Hệ thống dùng Singleton Pattern để tối ưu RAM)
diem_ehs = EHS_API.get_score(hole_cards, board_cards)

print(f"Sức mạnh tay bài hiện tại: {diem_ehs}")
# Kết quả Output: ~0.765 (Đại diện cho tỷ lệ thắng là 76.5%)
```

💡 **Tính năng Auto-Routing của Hệ thống:**
- Khi bạn ném vào Board chứa **3 đến 4 lá** (Flop, Turn) -> Hệ thống sẽ âm thầm chạy ảo hóa tương lai bằng **Monte Carlo**.
- Khi bạn ném vào Board chứa đủ **5 lá** (River) -> Hệ thống tự đổi thuật toán sang **Vét cạn (Exact Combinatorics)** chạy 1.081 trường hợp để trả kết quả chuẩn 100%. Mọi thứ trong suốt với người sử dụng!

---

## 5. Lộ trình đã triển khai (Dev Log)

Dưới đây là tóm tắt các bước hệ thống mà Thành viên 2 đã thực hiện để xây dựng thành công module này từ con số không:

### Bước 1: Xây dựng cấu trúc dữ liệu lá bài siêu tốc (Bitwise)
- **Vấn đề:** Máy tính tốn rất nhiều chu kỳ CPU để xử lý và so sánh chuỗi String (vd. `'Ah'`). Nếu chạy hàng triệu phép tính sẽ gây treo máy.
- **Giải pháp:** Áp dụng thuật toán của **Cactus Kev**. Nén toàn bộ thông tin (Hạng, Chất, Cờ kiểm tra) của một lá bài vào một số nguyên 32-bit `[xxxbbbbb|bbbbbbbb|cdhsrrrr|xxpppppp]`.
- **Kết quả:** Đã lập trình xong class `Card` tĩnh thao tác với Bitwise và class `Deck` chuẩn hóa bên trong `evaluator/models.py`.

### Bước 2: Tích hợp Bộ Phân Loại Lookup Table O(1)
- **Vấn đề:** Tự code logic bằng tay (so sánh tìm Đôi, Cù lú, Sảnh...) bằng IF/ELSE lồng nhau là ngõ cụt về mặt hiệu năng.
- **Giải pháp:** Bê nguyên thư viện tra cứu mã nguồn mở **TwoPlusTwo (2+2)**. Đây là một mảng khổng lồ có sẵn đáp án của toàn bộ hơn 32 triệu ván bài Poker.
- **Kết quả:** Tạo ra class `LookupEvaluator` trong file `evaluator/evaluator.py`. Tính năng tự động tải tập tin kết quả đồ sộ `HandRanks.dat` (130MB) từ internet trực tiếp vào RAM. Bất cứ bộ 7 lá bài nào được đưa vào sẽ có kết quả định lượng chỉ qua 7 bước tham chiếu bộ nhớ mảng.

### Bước 3: Toán học Trạng thái (Hand Strength & Phương pháp Monte Carlo)
- **Vấn đề:** Điểm số thô (vài vạn điểm) không có nhiều ý nghĩa. AI cần biết **Equity (%)** - Tỷ lệ thắng là bao nhiêu (HS), và rủi ro ở các vòng sau là gì (Potential).
- **Giải pháp:** 
  - Tại vòng cuối (River): 5 lá chung đã ra hết. Máy code thuật toán duyệt tổ hợp chính xác hoàn toàn (vét cạn 1081 cặp lá bài của đối thủ).
  - Tại vòng Flop, vòng Turn: Chạy vét cạn sẽ bị chết vi xử lý. Do đó, thiết kế mô hình **Monte Carlo Sampling**. Máy sẽ tự chia 2.000 ván bài giả định, rút đại bài cho đối thủ và board để sinh ra trung bình cộng tỷ lệ EHS. Thuật toán này đã ngầm xử lý cả PPOT (Tỷ lệ rùa được ván bài) và NPOT (Tỷ lệ bị đối thủ lật kèo).
- **Kết quả:** Hoàn thiện `EHSCalculator` cực sắc bén nằm tại `evaluator/ehs_calculator.py`.

### Bước 4: Đóng gói API dễ sử dụng cho Làm việc nhóm (Integration)
- **Vấn đề:** Code đang ở dạng rời rạc (cần gọi mã hóa -> gọi calculator -> ép kiểu). Thành viên 1 và Thành viên 4 sẽ thấy khó dùng nếu bị ép quan tâm đến bản chất toán học.
- **Giải pháp:** Đóng gói hoàn toàn bằng Hướng đối tượng để che giấu độ phức tạp kỹ thuật. Áp dụng chuẩn thiết kế *Singleton* để một khi RAM đã ngậm bảng 130MB thì không bao giờ phải load lại lần thứ hai.
- **Kết quả:** Hoàn chỉnh file `evaluator/api.py`. Giờ đây cả team chơi Poker bằng cách gọi đúng 1 hàm duy nhất nhận params string cực kì thân thiện.
