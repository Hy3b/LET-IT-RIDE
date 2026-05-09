"""Lớp UI trò chơi chín tích hợp Pygame với logic Poker AI.
Trích xuất từ poker_ai.py và tái cấu trúc để sử dụng các mô đun cận.
"""

import pygame
import sys
from .styles import *
from .components import Button, draw_card, ProbPanel
from core import GameState, monte_carlo_simulation, pot_odds, expected_value, calculate_outs, best_hand_from_seven, HAND_NAMES
from core.engine import get_deck_remaining


class PokerGame:
    """Lớp quản lý UI trò chơi Poker AI với Pygame.
    
    Xử lý:
      - Vòng chơi (blind, cược, showdown)
      - Hiển thị giao diện (bài, pot, thông tin người chơi)
      - Tương tác người chơi (nút bấm, phím tắt)
    """
    
    # ==================== GAME PHASES ====================
    PHASE_MENU = 0
    PHASE_PLAYER = 2
    PHASE_REVEAL = 3
    PHASE_END = 4
    
    # ==================== VIEW MODES ====================
    VIEW_GAME = 0
    VIEW_HAND_RANKINGS = 1
    
    # ==================== INITIAL CHIPS ====================
    INITIAL_CHIPS = 1000
    INITIAL_BLIND = 20

    def __init__(self):
        """Khởi tạo Pygame, các font chữ, UI component và trạng thái game."""
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Poker AI - Suy Luận Xác Suất")
        self.clock = pygame.time.Clock()
        
        # View mode
        self.current_view = self.VIEW_GAME
        
        self._init_fonts()
        self._init_ui_components()
        self._init_game_state()
        self._init_buttons()
        self._reset_round()
    
    def _init_fonts(self):
        """Khởi tạo tất cả font chữ cần thiết."""
        self.font_big = pygame.font.SysFont("segoeui", 42, bold=True)
        self.font_med = pygame.font.SysFont("segoeui", 24, bold=True)
        self.font_sm = pygame.font.SysFont("segoeui", 17)
        self.font_tiny = pygame.font.SysFont("segoeui", 13)
    
    def _init_ui_components(self):
        """Khởi tạo các thành phần UI (clock, probability panel)."""
        self.prob_panel = ProbPanel(SCREEN_WIDTH - 230, 70, 222, 340)
    
    def _init_game_state(self):
        """Khởi tạo trạng thái game ban đầu."""
        self.player_chips = self.INITIAL_CHIPS
        self.ai_chips = self.INITIAL_CHIPS
        self.pot = 0
        self.phase = self.PHASE_MENU
        self.message = ""
        self.sub_msg = ""
        self.msg_color = WHITE
        self.show_rules = False
        self.ai_thinking = False
        self.thinking_frame = 0

    def _init_buttons(self):
        """Khởi tạo tất cả các nút UI.
        
        Nút hành động chính:
          - CALL: Theo cược hiện tại
          - RAISE: Tăng cược thêm 50
          - FOLD: Bỏ bài
        
        Nút menu:
          - START: Bắt đầu game mới
          - RULES: Hiển thị luật chơi
          - NEXT: Vòng tiếp theo
          - MENU: Quay lại menu chính
        """
        cx = 480
        button_y = SCREEN_HEIGHT - 60
        
        # Nút hành động chính
        self.btn_call = Button(cx - 200, button_y, 120, 48, "CALL", (30, 150, 60))
        self.btn_raise = Button(cx - 60, button_y, 120, 48, "RAISE", (180, 120, 0))
        self.btn_fold = Button(cx + 80, button_y, 120, 48, "FOLD", (150, 30, 30))
        
        # Nút menu
        menu_y = SCREEN_HEIGHT - 60
        self.btn_start = Button(SCREEN_WIDTH//2 - 100, 400, 200, 50, "CHƠI NGAY", BLUE_DARK)
        self.btn_rules = Button(SCREEN_WIDTH//2 - 100, 470, 200, 50, "LUẬT CHƠI", DARK_GREEN)
        self.btn_next = Button(SCREEN_WIDTH//2 - 100, menu_y, 200, 48, "VĂN TIẾP", BLUE_DARK)
        self.btn_menu2 = Button(SCREEN_WIDTH//2 - 100, menu_y, 200, 48, "MENU", GRAY_DARK)
        
        # Danh sách tất cả nút (để cập nhật trạng thái)
        self.all_btns = [self.btn_start, self.btn_rules,
                         self.btn_call, self.btn_raise, self.btn_fold,
                         self.btn_next, self.btn_menu2]

    def _reset_round(self):
        """Lấp lại trạng thái trò chơi cho một vàn mới."""
        from core.models import Deck
        self.deck = Deck()
        self.player_hand = []
        self.ai_hand = []
        self.community = []
        self.community_full = []
        self.current_bet = 0
        self.player_bet = 0
        self.ai_bet = 0
        self.ai_hidden = True
        self.player_best_hand = None  # Store best 5-card hand for showdown
        self.ai_best_hand = None      # Store best 5-card hand for showdown
        self.prob_panel.update({})

    def deal_card(self):
        """Rút một lá bài từ bộ bài."""
        return self.deck.draw(1)[0]

    def _deck_remaining(self):
        """Get remaining deck cards (unknown to AI)."""
        return get_deck_remaining(self.ai_hand, self.community)

    def _run_ai(self):
        """Chạy AI sử dụng phân tích xác suất.
        
        Bước:
          1. Mô phỏng Monte Carlo: Tính xác suất thắng
          2. Tính pot odds: Liệu cược có xứng đáng?
          3. Tính Expected Value: Giá trị kỳ vọng của mỗi hành động
          4. Tính outs: Bao nhiêu lá bài có thể cải thiện tay hiện tại?
          5. Ra quyết định: Fold/Call/Raise dựa trên các số liệu trên
        
        Returns:
          tuple: (action, stats) - Hành động AI và chi tiết phân tích
        """
        self.ai_thinking = True
        self.thinking_frame = 0
        
        call_amt = max(0, self.player_bet - self.ai_bet)
        
        # Bước 1: Mô phỏng Monte Carlo
        win_prob = monte_carlo_simulation(
            self.ai_hand, self.community, self._deck_remaining(), n_simulations=800
        )
        
        # Bước 2-4: Tính các chỉ số
        p_odds = pot_odds(call_amt, self.pot)
        ev_call = expected_value(win_prob, self.pot, call_amt if call_amt > 0 else 10)
        raise_extra = min(50, self.ai_chips)
        ev_raise = expected_value(win_prob, self.pot + raise_extra,
                                  call_amt + raise_extra if call_amt > 0 else raise_extra)
        outs, next_level = calculate_outs(self.ai_hand, self.community)
        
        # Bước 5: Ra quyết định dựa trên heuristic
        action = self._decide_action(ev_call, ev_raise, win_prob, p_odds, raise_extra)
        
        # Tạo bảng thống kê để hiển thị
        stats = {
            "win_prob": win_prob,
            "pot_odds": p_odds,
            "ev_call": ev_call,
            "ev_raise": ev_raise,
            "outs": outs,
            "next_level": next_level,
            "action": action,
        }
        
        import time
        time.sleep(1)  # Thêm độ trễ để AI có vẻ suy nghĩ
        
        self.ai_thinking = False
        return action, stats
    
    def _decide_action(self, ev_call, ev_raise, win_prob, p_odds, raise_extra):
        """Quyết định hành động dựa trên các chỉ số phân tích.
        
        Heuristic:
          - Nếu EV(call) < -30 và xác suất thắng < 30%: FOLD
          - Nếu EV(raise) > EV(call) và xác suất > 55%: RAISE
          - Nếu EV(call) >= 0 hoặc xác suất > pot odds: CALL
          - Ngược lại: FOLD
        """
        if ev_call < -30 and win_prob < 0.3:
            return "fold"
        elif ev_raise > ev_call and win_prob > 0.55 and self.ai_chips >= raise_extra:
            return "raise"
        elif ev_call >= 0 or win_prob > p_odds:
            return "call"
        else:
            return "fold"

    def start_round(self):
        """Bắt đầu vòng chơi mới với blind.
        
        Trình tự:
          1. Reset trạng thái
          2. Tính blind (20 chips mỗi người)
          3. Cấp bài (2 lá cho mỗi người)
          4. Cấp flop (3 lá chung đầu tiên)
          5. Chạy AI để phân tích
        """
        self._reset_round()
        blind = min(20, self.player_chips, self.ai_chips)
        
        # Trừ blind từ chip của mỗi người
        self.player_chips -= blind
        self.ai_chips -= blind
        self.pot = blind * 2
        self.player_bet = blind
        self.ai_bet = blind
        self.current_bet = blind
        
        # Cấp bài
        self.player_hand = [self.deal_card(), self.deal_card()]
        self.ai_hand = [self.deal_card(), self.deal_card()]
        self.community_full = [self.deal_card() for _ in range(5)]
        self.community = self.community_full[:3]  # Flop (3 lá đầu tiên)
        
        # Cập nhật giao diện
        self.message = "Bài đã phát! Lượt của bạn..."
        self.sub_msg = f"Mù: {blind}"
        self.msg_color = GOLD
        self.phase = self.PHASE_PLAYER
        
        # Phân tích AI ban đầu
        _, stats = self._run_ai()
        self.prob_panel.update(stats)

    def player_action(self, action):
        """Xử lý hành động của người chơi và phản ứng AI.
        
        Trình tự:
          1. Nếu FOLD: AI thắng, cộng pot vào chip AI
          2. Nếu RAISE: Tăng cược, chờ AI phản ứng
          3. Nếu CALL: Theo cược hiện tại, rồi AI quyết định
          4. Sau mỗi lượt cược, kiểm tra xem vòng cược có kết thúc không
        
        Args:
          action (str): "fold", "call", hoặc "raise"
        """
        if action == "fold":
            self._handle_player_fold()
            return

        if action == "call":
            self._handle_player_call()
        elif action == "raise":
            self._process_player_raise()

        # Kiểm tra xem vòng cược kết thúc chưa (cả 2 matched bets hoặc all-in)
        if self._is_betting_round_complete():
            self._advance_street()
            return
        
        # AI phản ứng
        ai_act, stats = self._run_ai()
        self.prob_panel.update(stats)

        if ai_act == "fold":
            self._handle_ai_fold(stats)
        elif ai_act == "raise":
            self._handle_ai_raise(stats)
        else:
            self._handle_ai_call(stats)

        # Kiểm tra lại sau AI phản ứng
        if self._is_betting_round_complete():
            self._advance_street()

    def _handle_player_fold(self):
        """Người chơi bỏ bài."""
        self.ai_chips += self.pot
        self.pot = 0
        self.message = "Bạn bỏ bài! AI thắng."
        self.sub_msg = ""
        self.msg_color = RED
        self.ai_hidden = False
        self.phase = self.PHASE_END

    def _handle_player_call(self):
        """Xử lý khi người chơi theo cược."""
        call_amt = max(0, self.current_bet - self.player_bet)
        if call_amt <= 0:
            # Nếu bets đã matched, đây là check
            self.message = "Bạn check"
        elif call_amt > self.player_chips:
            # All-in
            call_amt = self.player_chips
            self.player_chips = 0
            self.player_bet += call_amt
            self.pot += call_amt
            self.message = f"Bạn all-in {call_amt}"
        else:
            self.player_chips -= call_amt
            self.player_bet += call_amt
            self.pot += call_amt
            self.message = f"Bạn theo cược {call_amt}"
        
        self.msg_color = GOLD

    def _process_player_raise(self):
        """Xử lý khi người chơi tăng cược."""
        raise_amt = min(50, self.player_chips)
        if raise_amt <= 0:
            return
        
        self.player_chips -= raise_amt
        self.player_bet += raise_amt
        self.current_bet = self.player_bet
        self.pot += raise_amt
        
        self.message = f"Bạn tăng cược {raise_amt}"
        self.msg_color = GOLD

    def _handle_ai_fold(self, stats):
        """AI bỏ bài."""
        self.player_chips += self.pot
        self.pot = 0
        self.message = "AI bỏ bài! Bạn thắng."
        ai_wp = stats["win_prob"]
        self.sub_msg = f"[AI] Thắng%={ai_wp*100:.1f}%  EV={stats['ev_call']:+.1f} -> BỎ BÀI"
        self.msg_color = GOLD
        self.ai_hidden = False
        self.phase = self.PHASE_END

    def _handle_ai_raise(self, stats):
        """AI tăng cược - yêu cầu người chơi phản ứng."""
        add = min(50, self.ai_chips)
        if add <= 0:
            # Nếu AI không đủ chip để raise, thì call
            self._handle_ai_call(stats)
            return
        
        self.ai_chips -= add
        self.ai_bet += add
        self.current_bet = self.ai_bet  # Cập nhật current_bet cho người chơi biết
        self.pot += add
        
        ai_wp = stats["win_prob"]
        self.sub_msg = f"[AI] Thắng%={ai_wp*100:.1f}%  EV={stats['ev_raise']:+.1f}  -> TĂNG CỬA {add}"
        self.message = "AI tăng cược - lượt của bạn..."
        self.msg_color = (255, 100, 100)  # Đỏ để nhấn mạnh AI tăng
        self.phase = self.PHASE_PLAYER  # Chuyển lại cho người chơi quyết định

    def _handle_ai_call(self, stats):
        """AI theo cược."""
        diff = min(self.current_bet - self.ai_bet, self.ai_chips)
        if diff > 0:
            self.ai_chips -= diff
            self.ai_bet += diff
            self.pot += diff
        
        ai_wp = stats["win_prob"]
        self.sub_msg = f"[AI] Thắng%={ai_wp*100:.1f}%  Odds={stats['pot_odds']*100:.1f}%  -> THEO CỬA"

    def _is_betting_round_complete(self):
        """Kiểm tra xem vòng cược có kết thúc không.
        
        Vòng cược kết thúc khi:
        - Cả 2 người đã matched bets (player_bet == ai_bet)
        - Hoặc 1 trong 2 người all-in (chips = 0)
        """
        return (self.player_bet == self.ai_bet or 
                self.player_chips == 0 or 
                self.ai_chips == 0)

    def _advance_street(self):
        """Rút lá tiếp theo hoặc vào showdown.
        
        Reset betting state cho street mới.
        """
        # Reset cược cho street tiếp theo
        self.player_bet = 0
        self.ai_bet = 0
        self.current_bet = 0
        
        if len(self.community) == 3:
            # Flop -> Turn
            self.community.append(self.community_full[3])
            self.message = "TURN - Quyết định tiếp theo?"
        elif len(self.community) == 4:
            # Turn -> River
            self.community.append(self.community_full[4])
            self.message = "RIVER - Quyết định tiếp theo?"
        else:
            # River -> Showdown
            self._showdown()
            return

        # Phân tích AI cho street mới
        _, stats2 = self._run_ai()
        self.prob_panel.update(stats2)
        self.msg_color = GOLD
        self.phase = self.PHASE_PLAYER  # Cho phép người chơi hành động

    def _showdown(self):
        """So sánh bài và xác định người thắng.
        
        Trình tự:
          1. Lấy 5 lá bài tốt nhất cho mỗi người chơi
          2. So sánh tay (rank cao hơn thắng)
          3. Chia pot (nếu hòa)
        """
        self.ai_hidden = False
        self.phase = self.PHASE_REVEAL
        
        # Lấy tay tốt nhất
        self.player_best_hand = best_hand_from_seven(self.player_hand + self.community)
        self.ai_best_hand = best_hand_from_seven(self.ai_hand + self.community)
        p_name = self.player_best_hand.name()
        a_name = self.ai_best_hand.name()
        
        # Xác định người thắng
        if self.player_best_hand > self.ai_best_hand:
            self.player_chips += self.pot
            self.message = f"BẠN THẮNG!  ({p_name} > {a_name})"
            self.msg_color = GOLD
        elif self.ai_best_hand > self.player_best_hand:
            self.ai_chips += self.pot
            self.message = f"AI THẮNG  ({a_name} > {p_name})"
            self.msg_color = RED
        else:
            # Hòa
            half = self.pot // 2
            self.player_chips += half
            self.ai_chips += half
            self.message = f"HÒA!  ({p_name})"
            self.msg_color = (200, 200, 50)
        
        self.sub_msg = f"Tay bạn: {p_name}   |   Tay AI: {a_name}"
        self.pot = 0
        self.phase = self.PHASE_END

    # ═══════════════════════════════════════════════════════════
    #  VẼ BÀNG (RENDERING FUNCTIONS)
    # ═══════════════════════════════════════════════════════════

    def draw(self):
        """Vẽ màn hình dựa trên view hiện tại."""
        if self.phase == self.PHASE_MENU:
            self.draw_menu()
        elif self.current_view == self.VIEW_HAND_RANKINGS:
            self._draw_hand_rankings_tab()
        else:
            self.draw_gameplay()
    
    def draw_menu(self):
        """Vẽ menu chính."""
        self.screen.fill((15, 35, 20))
        
        # Tiêu đề
        title = self.font_big.render("POKER AI", True, GOLD)
        self.screen.blit(title, title.get_rect(centerx=SCREEN_WIDTH//2, top=150))
        
        # Mô tả
        sub = self.font_med.render("Monte Carlo  |  Expected Value  |  Pot Odds  |  Outs", True, TEAL)
        self.screen.blit(sub, sub.get_rect(centerx=SCREEN_WIDTH//2, top=210))
        
        # Demo bài
        demo = [('A', SUITS[0]), ('K', SUITS[1]), ('Q', SUITS[2]), ('J', SUITS[3]), ('10', SUITS[0])]
        x0 = SCREEN_WIDTH//2 - 5*(CARD_WIDTH+6)//2
        for i, (r, s) in enumerate(demo):
            draw_card(self.screen, r, s, x0 + i*(CARD_WIDTH+6), 270)
        
        # Nút
        self.btn_start.draw(self.screen)
        self.btn_rules.draw(self.screen)

    def draw_gameplay(self):
        """Vẽ màn hình game chính với tất cả thông tin."""
        self.screen.fill((10, 25, 15))
        
        # Vẽ các thành phần chính
        self.draw_table()
        self.draw_info_bar()
        self._draw_ai_cards()
        self._draw_community_cards()
        self._draw_player_cards()
        
        self.prob_panel.draw(self.screen)
        self.draw_message_bar()
        self.draw_thinking()

        # Vẽ nút tương ứng với phase
        if self.phase == self.PHASE_PLAYER:
            self._draw_action_buttons()
        elif self.phase == self.PHASE_END:
            self._draw_end_buttons()
        
        # Nút tab Hand Rankings
        self._draw_hand_rankings_tab_button()

    def _draw_ai_cards(self):
        """Vẽ bài của AI (ẩn cho đến khi showdown)."""
        self.draw_cards_row(self.ai_hand, 100, hidden_all=self.ai_hidden, label="AI")

    def _draw_community_cards(self):
        """Vẽ bài chung."""
        self.draw_community()

    def _draw_player_cards(self):
        """Vẽ bài của người chơi (hoặc best hand nếu showdown)."""
        if self.phase == self.PHASE_REVEAL and self.player_best_hand:
            self.draw_cards_row(self.player_best_hand.cards, SCREEN_HEIGHT - 230, label="Bạn (Best 5)")
        else:
            self.draw_cards_row(self.player_hand, SCREEN_HEIGHT - 230, label="Bạn")

    def _draw_action_buttons(self):
        """Vẽ nút hành động khi đến lượt người chơi."""
        self.btn_call.enabled = self.player_chips > 0
        self.btn_raise.enabled = self.player_chips >= 50
        self.btn_fold.enabled = True
        
        self.btn_call.draw(self.screen)
        self.btn_raise.draw(self.screen)
        self.btn_fold.draw(self.screen)

    def _draw_end_buttons(self):
        """Vẽ nút khi vòng kết thúc."""
        ok = self.player_chips > 0 and self.ai_chips > 0
        
        if ok:
            self.btn_next.draw(self.screen)
        else:
            self.btn_menu2.draw(self.screen)
        
        # Hiển thị kết quả game
        if self.player_chips <= 0:
            end = self.font_big.render("GAME OVER - Bạn hết chip!", True, RED)
            self.screen.blit(end, end.get_rect(centerx=(SCREEN_WIDTH-230)//2, top=SCREEN_HEIGHT-175))
        elif self.ai_chips <= 0:
            end = self.font_big.render("CHIẾN THẮNG - AI hết chip!", True, GOLD)
            self.screen.blit(end, end.get_rect(centerx=(SCREEN_WIDTH-230)//2, top=SCREEN_HEIGHT-175))

    def _draw_hand_rankings_tab_button(self):
        """Vẽ nút để vào tab Hand Rankings."""
        btn_rect = pygame.Rect(SCREEN_WIDTH - 180, 10, 170, 40)
        pygame.draw.rect(self.screen, GOLD, btn_rect, 2)
        pygame.draw.rect(self.screen, (0, 0, 0), btn_rect)
        
        text = self.font_sm.render("Hand Rankings", True, GOLD)
        self.screen.blit(text, (btn_rect.x + 15, btn_rect.y + 8))
        
        # Lưu rect để xử lý click
        self.btn_hand_rankings_rect = btn_rect

    def _draw_hand_rankings_tab(self):
        """Vẽ tab Hand Rankings ở màn hình chính."""
        self.screen.fill((10, 25, 15))
        
        # Tiêu đề
        title = self.font_big.render("POKER HAND RANKINGS", True, GOLD)
        self.screen.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 30))
        
        # Danh sách 10 loại tay với ví dụ
        hand_examples = [
            ("ROYAL FLUSH", [('A', 'S'), ('K', 'S'), ('Q', 'S'), ('J', 'S'), ('T', 'S')], GOLD),
            ("STRAIGHT FLUSH", [('9', 'S'), ('8', 'S'), ('7', 'S'), ('6', 'S'), ('5', 'S')], (255, 200, 50)),
            ("FOUR OF A KIND", [('A', 'D'), ('A', 'S'), ('A', 'C'), ('A', 'H'), ('K', 'S')], (200, 200, 200)),
            ("FULL HOUSE", [('K', 'S'), ('K', 'H'), ('K', 'C'), ('T', 'C'), ('T', 'D')], (200, 200, 200)),
            ("FLUSH", [('Q', 'S'), ('8', 'S'), ('6', 'S'), ('4', 'S'), ('3', 'S')], (100, 200, 255)),
            ("STRAIGHT", [('6', 'D'), ('5', 'S'), ('4', 'C'), ('3', 'D'), ('2', 'S')], (200, 200, 200)),
            ("THREE OF A KIND", [('J', 'D'), ('J', 'S'), ('J', 'H'), ('9', 'D'), ('8', 'S')], (200, 200, 200)),
            ("TWO PAIR", [('6', 'S'), ('6', 'C'), ('T', 'H'), ('T', 'D'), ('K', 'S')], (200, 200, 200)),
            ("ONE PAIR", [('A', 'H'), ('A', 'S'), ('2', 'D'), ('4', 'C'), ('8', 'S')], (200, 200, 200)),
            ("HIGH CARD", [('Q', 'H'), ('T', 'S'), ('8', 'C'), ('4', 'D'), ('3', 'S')], (150, 150, 150)),
        ]
        
        # Vẽ danh sách xếp hạng ở giữa màn hình
        y = 110
        card_w = 50
        card_h = 68
        
        for i, (name, cards, color) in enumerate(hand_examples, 1):
            # Số thứ tự
            rank_num = self.font_med.render(str(i), True, WHITE)
            self.screen.blit(rank_num, (50, y + 8))
            
            # Tên tay
            hand_text = self.font_med.render(name, True, color)
            self.screen.blit(hand_text, (100, y + 8))
            
            # Vẽ 5 lá bài ví dụ (vẽ thủ công để đẹp)
            for j, (rank, suit) in enumerate(cards):
                card_x = 350 + j * (card_w + 3)
                card_y = y
                
                # Nền bài (trắng)
                card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
                pygame.draw.rect(self.screen, WHITE, card_rect, border_radius=3)
                pygame.draw.rect(self.screen, (200, 200, 200), card_rect, 2, border_radius=3)
                
                # Màu chữ theo suit
                suit_color = RED if suit in ['H', 'D'] else BLACK
                suit_symbol = {'H': '♥', 'D': '♦', 'C': '♣', 'S': '♠'}[suit]
                
                # Rank ở trên trái
                rank_text = pygame.font.SysFont("arial", 18, bold=True).render(rank, True, suit_color)
                self.screen.blit(rank_text, (card_x + 5, card_y + 4))
                
                # Suit ở giữa (to)
                suit_text = pygame.font.SysFont("arial", 24, bold=True).render(suit_symbol, True, suit_color)
                self.screen.blit(suit_text, (card_x + 12, card_y + 20))
                
                # Rank ở dưới phải (xoay 180 độ, nhưng chỉ vẽ nằm ngang)
                rank_text2 = pygame.font.SysFont("arial", 14, bold=True).render(rank, True, suit_color)
                self.screen.blit(rank_text2, (card_x + 30, card_y + 48))
                
                # Suit ở dưới phải
                suit_text2 = pygame.font.SysFont("arial", 16, bold=True).render(suit_symbol, True, suit_color)
                self.screen.blit(suit_text2, (card_x + 32, card_y + 54))
            
            y += 65
        
        # Nút quay lại
        back_btn_rect = pygame.Rect(SCREEN_WIDTH - 180, 10, 170, 40)
        pygame.draw.rect(self.screen, GOLD, back_btn_rect, 2)
        pygame.draw.rect(self.screen, (0, 0, 0), back_btn_rect)
        
        back_text = self.font_sm.render("Back to Game", True, GOLD)
        self.screen.blit(back_text, (back_btn_rect.x + 20, back_btn_rect.y + 8))
        
        self.btn_hand_rankings_rect = back_btn_rect

    def draw_hand_rankings(self):
        """Vẽ bảng xếp hạng tay Poker với ví dụ bên trái màn hình."""
        # Danh sách 10 loại tay với ví dụ
        hand_examples = [
            ("ROYAL FLUSH", [('A', 'S'), ('K', 'S'), ('Q', 'S'), ('J', 'S'), ('T', 'S')], GOLD),
            ("STRAIGHT FLUSH", [('9', 'S'), ('8', 'S'), ('7', 'S'), ('6', 'S'), ('5', 'S')], (255, 200, 50)),
            ("FOUR OF A KIND", [('A', 'D'), ('A', 'S'), ('A', 'C'), ('A', 'H'), ('K', 'S')], (200, 200, 200)),
            ("FULL HOUSE", [('K', 'S'), ('K', 'H'), ('K', 'C'), ('T', 'C'), ('T', 'D')], (200, 200, 200)),
            ("FLUSH", [('Q', 'S'), ('8', 'S'), ('6', 'S'), ('4', 'S'), ('3', 'S')], (100, 200, 255)),
            ("STRAIGHT", [('6', 'D'), ('5', 'S'), ('4', 'C'), ('3', 'D'), ('2', 'S')], (200, 200, 200)),
            ("THREE OF A KIND", [('J', 'D'), ('J', 'S'), ('J', 'H'), ('9', 'D'), ('8', 'S')], (200, 200, 200)),
            ("TWO PAIR", [('6', 'S'), ('6', 'C'), ('T', 'H'), ('T', 'D'), ('K', 'S')], (200, 200, 200)),
            ("ONE PAIR", [('A', 'H'), ('A', 'S'), ('2', 'D'), ('4', 'C'), ('8', 'S')], (200, 200, 200)),
            ("HIGH CARD", [('Q', 'H'), ('T', 'S'), ('8', 'C'), ('4', 'D'), ('3', 'S')], (150, 150, 150)),
        ]
        
        # Vẽ nền panel
        panel_width = 370
        panel_height = SCREEN_HEIGHT - 130
        panel_rect = pygame.Rect(5, 65, panel_width, panel_height)
        
        # Nền bán trong suốt
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel_surface.fill((0, 0, 0, 150))
        self.screen.blit(panel_surface, (5, 65))
        
        # Viền
        pygame.draw.rect(self.screen, GOLD, panel_rect, 2)
        
        # Tiêu đề
        title = self.font_tiny.render("HAND RANKINGS", True, GOLD)
        self.screen.blit(title, (12, 72))
        
        # Danh sách xếp hạng
        y = 95
        card_width = 18
        card_height = 26
        
        for i, (name, cards, color) in enumerate(hand_examples, 1):
            # Số thứ tự
            rank_num = self.font_tiny.render(str(i), True, WHITE)
            self.screen.blit(rank_num, (12, y))
            
            # Tên tay (giảm kích thước)
            name_short = name if len(name) <= 10 else name[:10]
            hand_text = self.font_tiny.render(name_short, True, color)
            self.screen.blit(hand_text, (28, y))
            
            # Vẽ 5 lá bài ví dụ (nhỏ)
            for j, (rank, suit) in enumerate(cards):
                card_x = 205 + j * 20
                card_y = y - 2
                
                # Background
                card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
                pygame.draw.rect(self.screen, WHITE, card_rect, border_radius=1)
                pygame.draw.rect(self.screen, GRAY_DARK, card_rect, 1, border_radius=1)
                
                # Text (rank + suit)
                suit_symbol = {'H': '♥', 'D': '♦', 'C': '♣', 'S': '♠'}[suit]
                suit_color = RED if suit in ['H', 'D'] else BLACK
                
                rank_text = pygame.font.SysFont("arial", 9).render(rank, True, suit_color)
                suit_text = pygame.font.SysFont("arial", 8).render(suit_symbol, True, suit_color)
                
                self.screen.blit(rank_text, (card_x + 2, card_y + 2))
                self.screen.blit(suit_text, (card_x + 2, card_y + 12))
            
            y += 28

    def draw_table(self):
        """Vẽ bàn chơi Poker (hình oval xanh)."""
        table_rect = pygame.Rect(60, 80, SCREEN_WIDTH - 310, SCREEN_HEIGHT - 160)
        
        # Bóng
        sh = pygame.Surface((table_rect.w + 20, table_rect.h + 20), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 80), sh.get_rect())
        self.screen.blit(sh, (table_rect.x - 5, table_rect.y + 10))
        
        # Bàn chính
        pygame.draw.ellipse(self.screen, DARK_GREEN, table_rect)
        pygame.draw.ellipse(self.screen, GREEN_FELT, table_rect.inflate(-20, -20))
        pygame.draw.ellipse(self.screen, GOLD, table_rect, 6)

    def draw_info_bar(self):
        """Vẽ thanh thông tin (chip, pot, cược)."""
        bar = pygame.Surface((SCREEN_WIDTH, 58), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 150))
        self.screen.blit(bar, (0, 0))
        
        # Thông tin từng người chơi
        chips_p = self.font_med.render(f"Bạn: {self.player_chips} (Cược: {self.player_bet})", True, GOLD)
        chips_a = self.font_med.render(f"AI: {self.ai_chips} (Cược: {self.ai_bet})", True, GOLD)
        pot_t = self.font_med.render(f"Pot: {self.pot}", True, WHITE)
        
        self.screen.blit(chips_p, (20, 14))
        self.screen.blit(pot_t, pot_t.get_rect(centerx=(SCREEN_WIDTH - 230)//2, top=14))
        self.screen.blit(chips_a, (SCREEN_WIDTH - 460, 14))

    def draw_message_bar(self):
        """Vẽ thanh thông báo và phân tích AI."""
        bar = pygame.Surface((SCREEN_WIDTH, 65), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 170))
        self.screen.blit(bar, (0, SCREEN_HEIGHT - 125))
        
        cx = (SCREEN_WIDTH - 230) // 2
        msg = self.font_sm.render(self.message, True, self.msg_color)
        sub = self.font_tiny.render(self.sub_msg, True, TEAL)
        
        self.screen.blit(msg, msg.get_rect(centerx=cx, top=SCREEN_HEIGHT - 120))
        self.screen.blit(sub, sub.get_rect(centerx=cx, top=SCREEN_HEIGHT - 100))

    def draw_thinking(self):
        """Vẽ animation AI đang suy nghĩ (3 chấm trôi + progress bar)."""
        if not self.ai_thinking:
            return
        
        # Chấm trôi
        dots = "." * ((self.thinking_frame % 30) // 10 + 1)
        thinking_text = f"AI đang suy nghĩ{dots}"
        
        # Nền bán trong suốt
        overlay = pygame.Surface((400, 80), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        overlay_rect = overlay.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(overlay, overlay_rect)
        
        # Text suy nghĩ
        txt = self.font_med.render(thinking_text, True, TEAL)
        txt_rect = txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        self.screen.blit(txt, txt_rect)
        
        # Thanh tiến trình
        bar_width = 200
        bar_height = 6
        bar_x = SCREEN_WIDTH // 2 - bar_width // 2
        bar_y = SCREEN_HEIGHT // 2 + 5
        
        # Nền thanh
        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        # Thanh điền (trôi qua lại)
        fill_width = int(bar_width * ((self.thinking_frame % 20) / 20))
        pygame.draw.rect(self.screen, TEAL, (bar_x, bar_y, fill_width, bar_height))
        
        self.thinking_frame += 1

    def draw_cards_row(self, cards, y, hidden_all=False, label=""):
        """Vẽ một hàng bài.
        
        Args:
          cards: List[(rank, suit)] hoặc Hand object
          y: Tọa độ Y
          hidden_all: Ẩn tất cả bài (cho bài AI chưa showdown)
          label: Nhãn trên bài ("Bạn", "AI", etc)
        """
        total_w = len(cards) * (CARD_WIDTH + 8)
        x0 = (SCREEN_WIDTH - 230) // 2 - total_w // 2
        
        # Vẽ nhãn
        if label:
            lbl = self.font_tiny.render(label, True, (200, 220, 200))
            self.screen.blit(lbl, (x0, y - 18))
        
        # Vẽ từng lá bài
        for i, (r, s) in enumerate(cards):
            draw_card(self.screen, r, s, x0 + i * (CARD_WIDTH + 8), y, hidden=hidden_all)

    def draw_community(self):
        """Vẽ 5 bài chung (có thể hiển thị từ 0 đến 5 lá).
        
        Nếu chưa tới lá nào, vẽ placeholder (hộp trống xanh).
        """
        total_w = 5 * (CARD_WIDTH + 8)
        cx = (SCREEN_WIDTH - 230) // 2
        x0 = cx - total_w // 2
        
        # Tiêu đề
        lbl = self.font_sm.render("--- Bài chung ---", True, (200, 230, 200))
        self.screen.blit(lbl, lbl.get_rect(centerx=cx, top=SCREEN_HEIGHT // 2 - CARD_HEIGHT // 2 - 28))
        
        # Vẽ 5 vị trí
        for i in range(5):
            x = x0 + i * (CARD_WIDTH + 8)
            y = SCREEN_HEIGHT // 2 - CARD_HEIGHT // 2
            
            if i < len(self.community):
                # Vẽ bài thực
                draw_card(self.screen, self.community[i][0], self.community[i][1], x, y)
            else:
                # Vẽ placeholder (hộp trống)
                r = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
                pygame.draw.rect(self.screen, DARK_GREEN, r, border_radius=8)
                pygame.draw.rect(self.screen, (80, 120, 80), r, 2, border_radius=8)

    def run(self):
        """Vòng lặp chính của game.
        
        Xử lý:
          - Cập nhật mouse position cho các nút
          - Xử lý sự kiện (click, phím)
          - Vẽ màn hình
          - Duy trì 60 FPS
        """
        while True:
            mouse_pos = pygame.mouse.get_pos()
            self._update_button_states(mouse_pos)
            
            for event in pygame.event.get():
                self._handle_event(event)
            
            self.draw()
            pygame.display.flip()
            self.clock.tick(FPS)

    def _update_button_states(self, mouse_pos):
        """Cập nhật trạng thái hover của tất cả nút."""
        for btn in self.all_btns:
            btn.update(mouse_pos)

    def _handle_event(self, event):
        """Xử lý sự kiện pygame."""
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        
        # Xử lý click nút Hand Rankings khi đang chơi
        if hasattr(self, 'btn_hand_rankings_rect') and self.current_view == self.VIEW_GAME:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.btn_hand_rankings_rect.collidepoint(event.pos):
                    self.current_view = self.VIEW_HAND_RANKINGS
                    return
        
        # Xử lý click nút Back to Game khi ở tab Hand Rankings
        if self.current_view == self.VIEW_HAND_RANKINGS:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if hasattr(self, 'btn_hand_rankings_rect') and self.btn_hand_rankings_rect.collidepoint(event.pos):
                    self.current_view = self.VIEW_GAME
                    return
        
        if self.phase == self.PHASE_MENU:
            self._handle_menu_event(event)
        elif self.phase == self.PHASE_PLAYER:
            self._handle_player_event(event)
        elif self.phase == self.PHASE_REVEAL:
            self._handle_reveal_event(event)
        elif self.phase == self.PHASE_END:
            self._handle_end_event(event)

    def _handle_menu_event(self, event):
        """Xử lý sự kiện trên menu chính."""
        if self.btn_start.clicked(event):
            self.player_chips = self.INITIAL_CHIPS
            self.ai_chips = self.INITIAL_CHIPS
            self.pot = 0
            self.start_round()
        
        if self.btn_rules.clicked(event):
            self.show_rules = not self.show_rules

    def _handle_player_event(self, event):
        """Xử lý sự kiện khi đến lượt người chơi (nút chuột)."""
        # Nút chuột
        if self.btn_call.clicked(event):
            self.player_action("call")
        if self.btn_raise.clicked(event):
            self.player_action("raise")
        if self.btn_fold.clicked(event):
            self.player_action("fold")

    def _handle_reveal_event(self, event):
        """Xử lý sự kiện trên phase reveal (showdown)."""
        self.phase = self.PHASE_END

    def _handle_end_event(self, event):
        """Xử lý sự kiện khi vòng kết thúc (nút chuột)."""
        ok = self.player_chips > 0 and self.ai_chips > 0
        
        # Nút chuột
        if ok and self.btn_next.clicked(event):
            self.start_round()
        if not ok and self.btn_menu2.clicked(event):
            self.phase = self.PHASE_MENU
            self._reset_round()


if __name__ == "__main__":
    game = PokerGame()
    game.run()
