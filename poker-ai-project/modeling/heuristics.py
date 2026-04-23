# heuristics.py
# Các quy tắc dự đoán hành động đối thủ (Likelihood P(E|H))
# Trách nhiệm: 
# Cung cấp xác suất một hành động xảy ra, dựa trên sức mạnh tay bài (EHS).

def get_action_likelihood(action, hand_strength_ehs):
    """
    Tính Likelihood: P(Action | Hand Strength).
    
    Tham số:
    - action: Hành động của đối thủ ("fold", "check", "call", "raise", "all-in").
    - hand_strength_ehs: Sức mạnh bài (0.0 đến 1.0) do Thành viên 2 (EHS) cấp.
    
    Trả về:
    - Xác suất (float) đối thủ thực hiện action này.
    """
    ehs = hand_strength_ehs
    action = action.lower()
    
    # Sử dụng kỹ thuật Abstraction/Bucketing: Chia EHS thành các nhóm.
    # Nhóm: Rác (< 0.3), Trung bình (0.3-0.6), Khá (0.6-0.8), Rất mạnh (> 0.8)
    
    if action == "fold":
        if ehs < 0.3: return 0.85     # Bài rác có khả năng fold cao
        elif ehs < 0.6: return 0.40   # Bài trung bình fold khi gặp raise
        elif ehs < 0.8: return 0.05   # Bài khá rất hiếm khi fold
        else: return 0.01             # Bài cực mạnh không bao giờ fold

    elif action in ["check", "call"]:
        if ehs < 0.3: return 0.10     # Bài rác có thể check, hiếm khi call
        elif ehs < 0.6: return 0.50   # Bài trung bình thường check/call
        elif ehs < 0.8: return 0.60   # Bài khá có xu hướng call/check
        else: return 0.29             # Bài cực mạnh có thể slowplay (gài bẫy)

    elif action == "raise":
        if ehs < 0.3: return 0.04     # Thỉnh thoảng bluff bằng bài rác
        elif ehs < 0.6: return 0.09   # Semi-bluff bằng bài có tiềm năng
        elif ehs < 0.8: return 0.30   # Bài khá thường raise (Value bet)
        else: return 0.60             # Bài cực mạnh cực kỳ thích raise

    elif action == "all-in":
        if ehs < 0.2: return 0.01     # Crazy bluff all-in (rất hiếm)
        elif ehs < 0.6: return 0.01   # Rất ít all-in ở mức bài lỡ cỡ
        elif ehs < 0.8: return 0.05   # Đôi khi all-in bảo vệ bài dễ bị vượt
        else: return 0.10             # Bài khủng all-in

    # Trả về mặc định cho các action không nhận diện được (tránh nhân với 0)
    return 0.01
