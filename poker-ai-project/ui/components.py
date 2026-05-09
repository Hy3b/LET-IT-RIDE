"""Các thành phần UI: Button, Vẽ Card, Bảng Xác Suất.
Trích xuất từ poker_ai.py - tất cả các yếu tố UI dựa trên Pygame.
"""

import pygame
from .styles import *


class Button:
    """Nút bấm tương tác với hiệu ứng hover."""
    def __init__(self, x, y, w, h, text, color, text_color=WHITE, font_size=22):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = tuple(min(c + 40, 255) for c in color)
        self.text_color = text_color
        self.font = pygame.font.SysFont("segoeui", font_size, bold=True)
        self.enabled = True
        self.hovered = False

    def draw(self, surf):
        col = self.hover_color if (self.hovered and self.enabled) else self.color
        if not self.enabled:
            col = GRAY_DARK
        pygame.draw.rect(surf, col, self.rect, border_radius=10)
        pygame.draw.rect(surf, WHITE, self.rect, 2, border_radius=10)
        tc = self.text_color if self.enabled else GRAY
        txt = self.font.render(self.text, True, tc)
        surf.blit(txt, txt.get_rect(center=self.rect.center))

    def update(self, pos):
        self.hovered = self.rect.collidepoint(pos)

    def clicked(self, event):
        return (self.enabled
                and event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))


def draw_card(surf, rank, suit, x, y, hidden=False):
    """Vẽ một lá bài trên đề."""
    rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
    
    # Shadow effect
    sh = pygame.Surface((CARD_WIDTH, CARD_HEIGHT), pygame.SRCALPHA)
    sh.fill((0, 0, 0, 80))
    surf.blit(sh, (x + 4, y + 4))
    
    if hidden:
        # Back of card (blue with pattern)
        pygame.draw.rect(surf, BLUE_DARK, rect, border_radius=8)
        pygame.draw.rect(surf, BLUE, rect, 2, border_radius=8)
        inner = rect.inflate(-10, -10)
        for i in range(0, inner.w, 10):
            pygame.draw.line(surf, (70, 130, 230),
                           (inner.x + i, inner.y),
                           (inner.x, inner.y + i), 1)
        return

    # Front of card
    pygame.draw.rect(surf, CREAM, rect, border_radius=8)
    pygame.draw.rect(surf, (200, 200, 200), rect, 1, border_radius=8)
    
    # Determine color based on suit
    is_red = suit in ('\u2665', '\u2666')
    color = RED_CARD if is_red else (10, 10, 30)
    
    # Use fonts that support unicode symbols well
    font_s = pygame.font.SysFont("arial unicode ms, arial, segoeui", 14, bold=True)
    font_b = pygame.font.SysFont("arial unicode ms, arial, segoeui", 28, bold=True)
    
    # Corner: rank
    corner = font_s.render(rank, True, color)
    surf.blit(corner, (x + 3, y + 2))
    
    # Small suit symbol in corner
    suit_small = font_s.render(suit, True, color)
    surf.blit(suit_small, (x + 3, y + 16))
    
    # Large suit symbol in center
    big = font_b.render(suit, True, color)
    surf.blit(big, big.get_rect(center=rect.center))


class ProbPanel:
    """Panel displaying AI's probability calculations in real-time."""

    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.font_t = pygame.font.SysFont("segoeui", 15, bold=True)
        self.font_v = pygame.font.SysFont("consolas", 14)
        self.font_tiny = pygame.font.SysFont("segoeui", 12)
        self.stats = {}

    def update(self, stats):
        """Update displayed statistics."""
        self.stats = stats

    def _bar(self, surf, x, y, w, h, value, color):
        """Draw a progress bar."""
        pygame.draw.rect(surf, (40, 40, 40), (x, y, w, h), border_radius=4)
        fill_w = int(w * max(0, min(1, value)))
        if fill_w > 0:
            pygame.draw.rect(surf, color, (x, y, fill_w, h), border_radius=4)
        pygame.draw.rect(surf, GRAY_DARK, (x, y, w, h), 1, border_radius=4)

    def draw(self, surf):
        """Render the probability panel."""
        # Background
        bg = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        bg.fill((10, 20, 15, 210))
        surf.blit(bg, (self.rect.x, self.rect.y))
        pygame.draw.rect(surf, TEAL, self.rect, 2, border_radius=8)

        x, y = self.rect.x + 10, self.rect.y + 8
        w = self.rect.w - 20

        # Title
        title = self.font_t.render("[ AI Probability Engine ]", True, TEAL)
        surf.blit(title, (x, y))
        y += 24

        if not self.stats:
            return

        s = self.stats

        # 1. Win Probability
        wp = s.get("win_prob", 0)
        wp_color = (
            (220, 60, 60) if wp < 0.35 else
            (220, 180, 0) if wp < 0.55 else
            (60, 200, 100)
        )
        surf.blit(self.font_t.render("P(thang):", True, WHITE), (x, y))
        y += 18
        self._bar(surf, x, y, w, 14, wp, wp_color)
        pct = self.font_v.render(f"{wp*100:.1f}%", True, wp_color)
        surf.blit(pct, (x + w - pct.get_width(), y - 1))
        y += 22

        # 2. Pot Odds
        po = s.get("pot_odds", 0)
        surf.blit(self.font_t.render("Tỷ lệ cược:", True, WHITE), (x, y))
        y += 18
        self._bar(surf, x, y, w, 14, po, (100, 150, 220))
        po_txt = self.font_v.render(f"{po*100:.1f}%", True, (100, 150, 220))
        surf.blit(po_txt, (x + w - po_txt.get_width(), y - 1))
        y += 20

        # 3. Expected Value
        ev_c = s.get("ev_call", 0)
        ev_r = s.get("ev_raise", 0)
        surf.blit(self.font_t.render("Giá trị kỳ vọng:", True, WHITE), (x, y))
        y += 18
        ev_c_col = (80, 220, 100) if ev_c >= 0 else (220, 80, 80)
        ev_r_col = (80, 220, 100) if ev_r >= 0 else (220, 80, 80)
        surf.blit(self.font_v.render(f"{ev_c:+.1f}  /  {ev_r:+.1f}", True, ev_c_col), (x, y))
        y += 22

        # 4. Outs
        outs = s.get("outs", 0)
        nxt = s.get("next_level", "")
        out_color = GOLD if outs > 6 else (GRAY if outs == 0 else (200, 180, 80))
        surf.blit(self.font_t.render("Lá tốt:", True, WHITE), (x, y))
        y += 18
        out_txt = f"{outs}"
        if nxt:
            out_txt += f"  ({nxt})"
        surf.blit(self.font_v.render(out_txt, True, out_color), (x, y))
        y += 24

        # 5. AI Decision
        pygame.draw.line(surf, TEAL, (x, y), (x + w, y), 1)
        y += 10
        action = s.get("action", "?").upper()
        act_colors = {"FOLD": (220, 60, 60), "CALL": (60, 200, 100), "RAISE": (220, 180, 0)}
        act_col = act_colors.get(action, WHITE)
        act_surf = pygame.font.SysFont("segoeui", 24, bold=True).render(
            f"{action}", True, act_col)
        surf.blit(act_surf, act_surf.get_rect(centerx=self.rect.centerx, top=y))
