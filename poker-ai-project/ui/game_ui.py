"""Main game UI class integrating Pygame with poker AI logic.
Extracted from poker_ai.py and refactored to use core modules.
"""

import pygame
import sys
from .styles import *
from .components import Button, draw_card, ProbPanel
from core import GameState, monte_carlo_simulation, pot_odds, expected_value, calculate_outs, best_hand_from_seven, HAND_NAMES
from core.engine import get_deck_remaining


class PokerGame:
    """Main game window and logic integration."""
    
    PHASE_MENU = 0
    PHASE_PLAYER = 2
    PHASE_REVEAL = 3
    PHASE_END = 4

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Poker AI - Suy Luan Xac Suat")
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont("segoeui", 42, bold=True)
        self.font_med = pygame.font.SysFont("segoeui", 24, bold=True)
        self.font_sm = pygame.font.SysFont("segoeui", 17)
        self.font_tiny = pygame.font.SysFont("segoeui", 13)

        self.player_chips = 1000
        self.ai_chips = 1000
        self.pot = 0
        self.phase = self.PHASE_MENU
        self.message = ""
        self.sub_msg = ""
        self.msg_color = WHITE
        self.show_rules = False
        self.ai_thinking = False
        self.thinking_time = 0

        # Probability panel
        self.prob_panel = ProbPanel(SCREEN_WIDTH - 230, 70, 222, 340)

        self._init_buttons()
        self._reset_round()

    def _init_buttons(self):
        """Initialize all UI buttons."""
        cx = 480
        self.btn_start = Button(SCREEN_WIDTH//2 - 100, 400, 200, 50, "CHƠI NGAY", BLUE_DARK)
        self.btn_rules = Button(SCREEN_WIDTH//2 - 100, 470, 200, 50, "LUẬT CHƠI", DARK_GREEN)
        y = SCREEN_HEIGHT - 85
        self.btn_call = Button(cx - 200, y, 120, 48, "CALL", (30, 150, 60))
        self.btn_raise = Button(cx - 60, y, 120, 48, "RAISE", (180, 120, 0))
        self.btn_fold = Button(cx + 80, y, 120, 48, "FOLD", (150, 30, 30))
        self.btn_next = Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 75, 200, 48, "VĂN TIẾP", BLUE_DARK)
        self.btn_menu2 = Button(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT - 75, 200, 48, "MENU", GRAY_DARK)
        self.all_btns = [self.btn_start, self.btn_rules,
                         self.btn_call, self.btn_raise, self.btn_fold,
                         self.btn_next, self.btn_menu2]

    def _reset_round(self):
        """Reset game state for a new round."""
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
        """Draw a card from deck."""
        return self.deck.draw(1)[0]

    def _deck_remaining(self):
        """Get remaining deck cards (unknown to AI)."""
        return get_deck_remaining(self.ai_hand, self.community)

    def _run_ai(self):
        """Run AI probability analysis and return (action, stats)."""
        import time
        self.ai_thinking = True
        self.thinking_frame = 0
        
        call_amt = max(0, self.player_bet - self.ai_bet)
        
        # Monte Carlo simulation
        win_prob = monte_carlo_simulation(
            self.ai_hand, self.community, self._deck_remaining(), n_simulations=800
        )
        
        # Pot odds
        p_odds = pot_odds(call_amt, self.pot)
        
        # Expected value
        ev_call = expected_value(win_prob, self.pot, call_amt if call_amt > 0 else 10)
        raise_extra = min(50, self.ai_chips)
        ev_raise = expected_value(win_prob, self.pot + raise_extra,
                                  call_amt + raise_extra if call_amt > 0 else raise_extra)
        
        # Outs
        outs, next_level = calculate_outs(self.ai_hand, self.community)
        
        # Decision logic
        if ev_call < -30 and win_prob < 0.3:
            action = "fold"
        elif ev_raise > ev_call and win_prob > 0.55 and self.ai_chips >= raise_extra:
            action = "raise"
        elif ev_call >= 0 or win_prob > p_odds:
            action = "call"
        else:
            action = "fold"
        
        stats = {
            "win_prob": win_prob,
            "pot_odds": p_odds,
            "ev_call": ev_call,
            "ev_raise": ev_raise,
            "outs": outs,
            "next_level": next_level,
            "action": action,
        }
        
        # Add delay for thinking effect
        import time
        time.sleep(1)
        
        self.ai_thinking = False
        return action, stats

    def start_round(self):
        """Start a new round with blinds."""
        self._reset_round()
        blind = min(20, self.player_chips, self.ai_chips)
        self.player_chips -= blind
        self.ai_chips -= blind
        self.pot += blind * 2
        self.player_bet = blind
        self.ai_bet = blind
        self.current_bet = blind
        
        self.player_hand = [self.deal_card(), self.deal_card()]
        self.ai_hand = [self.deal_card(), self.deal_card()]
        self.community_full = [self.deal_card() for _ in range(5)]
        self.community = self.community_full[:3]  # Start with flop
        
        self.message = "Bài đã phát! Lượt của bạn..."
        self.sub_msg = f"Mù: {blind}"
        self.msg_color = GOLD
        self.phase = self.PHASE_PLAYER
        
        # Calculate initial probability
        _, stats = self._run_ai()
        self.prob_panel.update(stats)

    def player_action(self, action):
        """Handle player action."""
        if action == "fold":
            self.ai_chips += self.pot
            self.pot = 0
            self.message = "Bạn bỏ bài! AI thắng."
            self.sub_msg = ""
            self.msg_color = RED
            self.ai_hidden = False
            self.phase = self.PHASE_END
            return

        if action == "raise":
            raise_amt = min(50, self.player_chips)
            if raise_amt <= 0:
                action = "call"
            else:
                self.player_chips -= raise_amt
                self.player_bet += raise_amt
                self.current_bet = self.player_bet
                self.pot += raise_amt

        # AI responds
        ai_act, stats = self._run_ai()
        self.prob_panel.update(stats)

        if ai_act == "fold":
            self.player_chips += self.pot
            self.pot = 0
            self.message = "AI bỏ bài! Bạn thắng."
            ai_wp = stats["win_prob"]
            self.sub_msg = f"[AI] Thắng%={ai_wp*100:.1f}%  EV={stats['ev_call']:+.1f} -> BỎ BÀI"
            self.msg_color = GOLD
            self.ai_hidden = False
            self.phase = self.PHASE_END
            return

        elif ai_act == "raise":
            add = min(50, self.ai_chips)
            self.ai_chips -= add
            self.ai_bet += add
            self.pot += add
            diff = min(self.ai_bet - self.player_bet, self.player_chips)
            self.player_chips -= diff
            self.player_bet += diff
            self.pot += diff
            ai_wp = stats["win_prob"]
            self.sub_msg = (f"[AI] Thắng%={ai_wp*100:.1f}%  EV={stats['ev_raise']:+.1f}"
                           f"  -> TĂNG CỬA {add}")
        else:
            diff = min(self.current_bet - self.ai_bet, self.ai_chips)
            if diff > 0:
                self.ai_chips -= diff
                self.ai_bet += diff
                self.pot += diff
            ai_wp = stats["win_prob"]
            self.sub_msg = (f"[AI] Thắng%={ai_wp*100:.1f}%  Odds={stats['pot_odds']*100:.1f}%"
                           f"  -> THEO CỬA")

        # Reveal next street
        if len(self.community) == 3:
            self.community.append(self.community_full[3])
            self.sub_msg += "  | RÚT"
        elif len(self.community) == 4:
            self.community.append(self.community_full[4])
            self.sub_msg += "  | SÔNG"
        else:
            self._showdown()
            return

        # Update probability for new street
        _, stats2 = self._run_ai()
        self.prob_panel.update(stats2)
        self.message = "Quyết định tiếp theo?"
        self.msg_color = GOLD

    def _showdown(self):
        """Compare hands and determine winner."""
        self.ai_hidden = False
        self.phase = self.PHASE_REVEAL
        self.player_best_hand = best_hand_from_seven(self.player_hand + self.community)
        self.ai_best_hand = best_hand_from_seven(self.ai_hand + self.community)
        p_name = self.player_best_hand.name()
        a_name = self.ai_best_hand.name()
        
        if self.player_best_hand > self.ai_best_hand:
            self.player_chips += self.pot
            self.message = f"BẠN THẮNG!  ({p_name} > {a_name})"
            self.msg_color = GOLD
        elif self.ai_best_hand > self.player_best_hand:
            self.ai_chips += self.pot
            self.message = f"AI THẮNG  ({a_name} > {p_name})"
            self.msg_color = RED
        else:
            half = self.pot // 2
            self.player_chips += half
            self.ai_chips += half
            self.message = f"HÒA!  ({p_name})"
            self.msg_color = (200, 200, 50)
        
        self.sub_msg = f"Tay bạn: {p_name}   |   Tay AI: {a_name}"
        self.pot = 0
        self.phase = self.PHASE_END

    # ═══════════════════════════════════════════════════════════
    #  DRAWING FUNCTIONS
    # ═══════════════════════════════════════════════════════════

    def draw_table(self):
        """Draw the poker table."""
        table_rect = pygame.Rect(60, 80, SCREEN_WIDTH - 310, SCREEN_HEIGHT - 160)
        sh = pygame.Surface((table_rect.w + 20, table_rect.h + 20), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 80), sh.get_rect())
        self.screen.blit(sh, (table_rect.x - 5, table_rect.y + 10))
        pygame.draw.ellipse(self.screen, DARK_GREEN, table_rect)
        pygame.draw.ellipse(self.screen, GREEN_FELT, table_rect.inflate(-20, -20))
        pygame.draw.ellipse(self.screen, GOLD, table_rect, 6)

    def draw_info_bar(self):
        """Draw chip/pot info bar."""
        bar = pygame.Surface((SCREEN_WIDTH, 58), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 150))
        self.screen.blit(bar, (0, 0))
        chips_p = self.font_med.render(f"Bạn: {self.player_chips} (Cược: {self.player_bet})", True, GOLD)
        chips_a = self.font_med.render(f"AI: {self.ai_chips} (Cược: {self.ai_bet})", True, GOLD)
        pot_t = self.font_med.render(f"Pot: {self.pot}", True, WHITE)
        self.screen.blit(chips_p, (20, 14))
        self.screen.blit(pot_t, pot_t.get_rect(centerx=(SCREEN_WIDTH - 230)//2, top=14))
        self.screen.blit(chips_a, (SCREEN_WIDTH - 460, 14))

    def draw_message_bar(self):
        """Draw message output area."""
        bar = pygame.Surface((SCREEN_WIDTH, 50), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 170))
        self.screen.blit(bar, (0, SCREEN_HEIGHT - 140))
        cx = (SCREEN_WIDTH - 230) // 2
        msg = self.font_med.render(self.message, True, self.msg_color)
        sub = self.font_sm.render(self.sub_msg, True, TEAL)
        self.screen.blit(msg, msg.get_rect(centerx=cx, top=SCREEN_HEIGHT - 138))
        self.screen.blit(sub, sub.get_rect(centerx=cx, top=SCREEN_HEIGHT - 112))

    def draw_thinking(self):
        """Draw AI thinking animation."""
        if not self.ai_thinking:
            return
        
        # Animated dots: . .. ...
        dots = "." * ((self.thinking_frame % 30) // 10 + 1)
        thinking_text = f"AI đang suy nghĩ{dots}"
        
        # Semi-transparent overlay
        overlay = pygame.Surface((400, 80), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        overlay_rect = overlay.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(overlay, overlay_rect)
        
        # Thinking text
        txt = self.font_med.render(thinking_text, True, TEAL)
        txt_rect = txt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        self.screen.blit(txt, txt_rect)
        
        # Animated loading bar
        bar_width = 200
        bar_height = 6
        bar_x = SCREEN_WIDTH // 2 - bar_width // 2
        bar_y = SCREEN_HEIGHT // 2 + 5
        
        # Background
        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        # Animated fill
        fill_width = int(bar_width * ((self.thinking_frame % 20) / 20))
        pygame.draw.rect(self.screen, TEAL, (bar_x, bar_y, fill_width, bar_height))
        
        self.thinking_frame += 1

    def draw_cards_row(self, cards, y, hidden_all=False, label=""):
        """Draw a row of cards."""
        total_w = len(cards) * (CARD_WIDTH + 8)
        x0 = (SCREEN_WIDTH - 230) // 2 - total_w // 2
        if label:
            lbl = self.font_tiny.render(label, True, (200, 220, 200))
            self.screen.blit(lbl, (x0, y - 18))
        for i, (r, s) in enumerate(cards):
            draw_card(self.screen, r, s, x0 + i * (CARD_WIDTH + 8), y, hidden=hidden_all)

    def draw_community(self):
        """Draw community cards."""
        total_w = 5 * (CARD_WIDTH + 8)
        cx = (SCREEN_WIDTH - 230) // 2
        x0 = cx - total_w // 2
        lbl = self.font_sm.render("--- Bài chung ---", True, (200, 230, 200))
        self.screen.blit(lbl, lbl.get_rect(centerx=cx, top=SCREEN_HEIGHT // 2 - CARD_HEIGHT // 2 - 28))
        for i in range(5):
            x = x0 + i * (CARD_WIDTH + 8)
            y = SCREEN_HEIGHT // 2 - CARD_HEIGHT // 2
            if i < len(self.community):
                draw_card(self.screen, self.community[i][0], self.community[i][1], x, y)
            else:
                r = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
                pygame.draw.rect(self.screen, DARK_GREEN, r, border_radius=8)
                pygame.draw.rect(self.screen, (80, 120, 80), r, 2, border_radius=8)

    def draw_menu(self):
        """Draw main menu."""
        self.screen.fill((15, 35, 20))
        title = self.font_big.render("POKER AI - Suy Luan Xac Suat", True, GOLD)
        sub = self.font_med.render("Monte Carlo  |  Expected Value  |  Pot Odds  |  Outs", True, TEAL)
        self.screen.blit(title, title.get_rect(centerx=SCREEN_WIDTH//2, top=150))
        self.screen.blit(sub, sub.get_rect(centerx=SCREEN_WIDTH//2, top=210))
        
        demo = [('A', SUITS[0]), ('K', SUITS[1]), ('Q', SUITS[2]), ('J', SUITS[3]), ('10', SUITS[0])]
        x0 = SCREEN_WIDTH//2 - 5*(CARD_WIDTH+6)//2
        for i, (r, s) in enumerate(demo):
            draw_card(self.screen, r, s, x0 + i*(CARD_WIDTH+6), 270)
        
        self.btn_start.draw(self.screen)
        self.btn_rules.draw(self.screen)
        info = self.font_sm.render("AI su dung xac suat thuc su - khong dung random!", True, GRAY)
        self.screen.blit(info, info.get_rect(centerx=SCREEN_WIDTH//2, top=560))

    def draw_gameplay(self):
        """Draw main game screen."""
        self.screen.fill((10, 25, 15))
        self.draw_table()
        self.draw_info_bar()
        self.draw_cards_row(self.ai_hand, 100, hidden_all=self.ai_hidden, label="May")
        self.draw_community()
        
        # Draw player cards or best hand (during showdown)
        if self.phase == self.PHASE_REVEAL and self.player_best_hand:
            self.draw_cards_row(self.player_best_hand.cards, SCREEN_HEIGHT - 230, label="Bạn (Best 5)")
        else:
            self.draw_cards_row(self.player_hand, SCREEN_HEIGHT - 230, label="Bạn")
        
        self.prob_panel.draw(self.screen)
        self.draw_message_bar()
        self.draw_thinking()

        if self.phase == self.PHASE_PLAYER:
            self.btn_call.enabled = self.player_chips > 0
            self.btn_raise.enabled = self.player_chips >= 50
            self.btn_fold.enabled = True
            self.btn_call.draw(self.screen)
            self.btn_raise.draw(self.screen)
            self.btn_fold.draw(self.screen)
            ht = self.font_tiny.render("C=Theo   R=Tăng   F=Bỏ", True, GRAY)
            self.screen.blit(ht, ht.get_rect(centerx=(SCREEN_WIDTH-230)//2, top=SCREEN_HEIGHT - 30))

        elif self.phase == self.PHASE_END:
            ok = self.player_chips > 0 and self.ai_chips > 0
            if ok:
                self.btn_next.draw(self.screen)
            else:
                self.btn_menu2.draw(self.screen)
            if self.player_chips <= 0:
                end = self.font_big.render("GAME OVER - Ban het chip!", True, RED)
                self.screen.blit(end, end.get_rect(centerx=(SCREEN_WIDTH-230)//2, top=SCREEN_HEIGHT-175))
            elif self.ai_chips <= 0:
                end = self.font_big.render("CHIEN THANG - May het chip!", True, GOLD)
                self.screen.blit(end, end.get_rect(centerx=(SCREEN_WIDTH-230)//2, top=SCREEN_HEIGHT-175))

    def run(self):
        """Main game loop."""
        while True:
            mouse_pos = pygame.mouse.get_pos()
            for btn in self.all_btns:
                btn.update(mouse_pos)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                
                if self.phase == self.PHASE_MENU:
                    if self.btn_start.clicked(event):
                        self.player_chips = 1000
                        self.ai_chips = 1000
                        self.pot = 0
                        self.start_round()
                    if self.btn_rules.clicked(event):
                        self.show_rules = not self.show_rules
                
                elif self.phase == self.PHASE_PLAYER:
                    if self.btn_call.clicked(event):
                        self.player_action("call")
                    if self.btn_raise.clicked(event):
                        self.player_action("raise")
                    if self.btn_fold.clicked(event):
                        self.player_action("fold")
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_c:
                            self.player_action("call")
                        if event.key == pygame.K_r:
                            self.player_action("raise")
                        if event.key == pygame.K_f:
                            self.player_action("fold")
                
                elif self.phase == self.PHASE_REVEAL:
                    self.phase = self.PHASE_END
                
                elif self.phase == self.PHASE_END:
                    ok = self.player_chips > 0 and self.ai_chips > 0
                    if ok and self.btn_next.clicked(event):
                        self.start_round()
                    if not ok and self.btn_menu2.clicked(event):
                        self.phase = self.PHASE_MENU
                        self._reset_round()
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        if ok:
                            self.start_round()
                        else:
                            self.phase = self.PHASE_MENU
                            self._reset_round()

            if self.phase == self.PHASE_MENU:
                self.draw_menu()
            else:
                self.draw_gameplay()
            
            pygame.display.flip()
            self.clock.tick(FPS)


if __name__ == "__main__":
    game = PokerGame()
    game.run()
