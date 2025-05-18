import pygame
import random
import math
import sys
import time
from pygame import gfxdraw
import platform
import asyncio

# Game constants
BOARD_SIZE = 10
CELL_SIZE = 80
BOARD_PIXEL_SIZE = (BOARD_SIZE - 1) * CELL_SIZE
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 1000
MARGIN_LEFT = (WINDOW_WIDTH - BOARD_PIXEL_SIZE) // 2
MARGIN_TOP = (WINDOW_HEIGHT - BOARD_PIXEL_SIZE) // 2

# Colors
MAIN_BACKGROUND = (20, 25, 35)
BOARD_BACKGROUND = (245, 245, 220)
GRID_COLOR = (100, 80, 60)
PLAYER_COLOR = (210, 70, 90)
AI_COLOR = (65, 105, 170)
TEXT_COLOR = (230, 230, 230)
HIGHLIGHT_COLOR = (255, 215, 0, 140)
TIMER_COLOR = (180, 180, 180)
TITLE_GLOW = (255, 215, 0, 100)
TITLE_COLOR = (120, 200, 255)
MODAL_BACKGROUND = (40, 45, 55, 230)
BUTTON_COLOR = (80, 130, 200)
BUTTON_HOVER_COLOR = (100, 150, 220)
EASY_COLOR = (100, 200, 100)
MEDIUM_COLOR = (200, 200, 100)
HARD_COLOR = (200, 100, 100)

# Constants
EMPTY = '.'
PLAYER = 'X'
AI = 'O'

# Difficulty settings
DIFFICULTY_LEVELS = {
    "Easy": {"depth": 1, "color": EASY_COLOR},
    "Medium": {"depth": 2, "color": MEDIUM_COLOR},
    "Hard": {"depth": 2, "color": HARD_COLOR}
}

# Initialize Pygame
pygame.init()
pygame.display.set_caption("Gomoku")
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
clock = pygame.time.Clock()
FPS = 60

# Fonts
try:
    title_font = pygame.font.Font(None, 70)
    game_font = pygame.font.Font(None, 36)
    status_font = pygame.font.Font(None, 30)
    timer_font = pygame.font.Font(None, 40)
    modal_font = pygame.font.Font(None, 60)
    button_font = pygame.font.Font(None, 36)
except:
    title_font = pygame.font.SysFont(None, 70)
    game_font = pygame.font.SysFont(None, 36)
    status_font = pygame.font.SysFont(None, 30)
    timer_font = pygame.font.SysFont(None, 40)
    modal_font = pygame.font.SysFont(None, 60)
    button_font = pygame.font.SysFont(None, 36)

# Skip sound initialization for Pyodide compatibility
has_sound = False

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, border_radius=10, width=2)
        text_surf = button_font.render(self.text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def is_clicked(self, mouse_pos, mouse_click):
        return self.rect.collidepoint(mouse_pos) and mouse_click

class Stone:
    def __init__(self, x, y, player, animate=True):
        self.grid_x = x
        self.grid_y = y
        self.x = MARGIN_LEFT + y * CELL_SIZE
        self.y = MARGIN_TOP + x * CELL_SIZE
        self.player = player
        self.radius = 0 if animate else CELL_SIZE // 3
        self.max_radius = CELL_SIZE // 3
        self.animate = animate
        self.alpha = 0

    def update(self):
        if self.animate and self.radius < self.max_radius:
            self.radius += 2
            self.alpha = min(255, self.alpha + 15)

    def draw(self, surface):
        color = PLAYER_COLOR if self.player == PLAYER else AI_COLOR
        shadow_radius = self.radius + 2
        shadow_pos = (self.x + 2, self.y + 2)
        gfxdraw.filled_circle(surface, shadow_pos[0], shadow_pos[1], shadow_radius, (20, 20, 20, 100))
        gfxdraw.aacircle(surface, self.x, self.y, self.radius, color)
        gfxdraw.filled_circle(surface, self.x, self.y, self.radius, color)
        if self.radius > 3:
            highlight_radius = max(2, self.radius - 5)
            highlight_pos = (self.x - 2, self.y - 2)
            gfxdraw.filled_circle(surface, highlight_pos[0], highlight_pos[1], highlight_radius, (255, 255, 255, 80))

class Gomoku:
    def __init__(self):
        self.board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.stones = []
        self.last_move = None
        self.winner_line = None
        self.game_state = "playing"
        self.hover_pos = None
        self.start_time = time.time()
        self.elapsed_time = 0
        self.show_modal = False
        self.show_difficulty_modal = False
        self.difficulty = "Medium"
        self.play_again_button = Button(
            WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 + 50, 200, 60,
            "Play Again", BUTTON_COLOR, BUTTON_HOVER_COLOR
        )
        self.difficulty_buttons = [
            Button(
                WINDOW_WIDTH // 2 - 100, WINDOW_HEIGHT // 2 - 50 + i * 80, 200, 60,
                difficulty, DIFFICULTY_LEVELS[difficulty]["color"],
                tuple(min(c + 30, 255) for c in DIFFICULTY_LEVELS[difficulty]["color"])
            ) for i, difficulty in enumerate(DIFFICULTY_LEVELS.keys())
        ]
        # Cache board background
        self.board_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        self.draw_background_static()

    def reset(self):
        self.board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.stones = []
        self.last_move = None
        self.winner_line = None
        self.game_state = "playing"
        self.show_modal = False
        self.show_difficulty_modal = True
        self.start_time = time.time()

    def draw_background_static(self):
        self.board_surface.fill(MAIN_BACKGROUND)
        padding = CELL_SIZE * 1.2
        board_width = (BOARD_SIZE - 1) * CELL_SIZE + padding * 2
        board_height = (BOARD_SIZE - 1) * CELL_SIZE + padding * 2
        board_rect = pygame.Rect(
            (WINDOW_WIDTH - board_width) // 2,
            (WINDOW_HEIGHT - board_height) // 2,
            board_width, board_height
        )
        shadow_rect = board_rect.copy()
        shadow_rect.x += 8
        shadow_rect.y += 8
        pygame.draw.rect(self.board_surface, (0, 0, 0, 100), shadow_rect, border_radius=15)
        pygame.draw.rect(self.board_surface, BOARD_BACKGROUND, board_rect, border_radius=15)
        for i in range(BOARD_SIZE):
            x = MARGIN_LEFT + i * CELL_SIZE
            y = MARGIN_TOP + i * CELL_SIZE
            pygame.draw.line(self.board_surface, GRID_COLOR,
                            (x, MARGIN_TOP - CELL_SIZE // 2),
                            (x, MARGIN_TOP + (BOARD_SIZE - 1) * CELL_SIZE + CELL_SIZE // 2), 2)
            pygame.draw.line(self.board_surface, GRID_COLOR,
                            (MARGIN_LEFT - CELL_SIZE // 2, y),
                            (MARGIN_LEFT + (BOARD_SIZE - 1) * CELL_SIZE + CELL_SIZE // 2, y), 2)
        marker_positions = [3, BOARD_SIZE // 2, BOARD_SIZE - 4]
        for x in marker_positions:
            for y in marker_positions:
                center = (MARGIN_LEFT + y * CELL_SIZE, MARGIN_TOP + x * CELL_SIZE)
                pygame.draw.circle(self.board_surface, GRID_COLOR, center, 5)
                pygame.draw.circle(self.board_surface, (0, 0, 0), center, 3)

    def draw_background(self):
        screen.blit(self.board_surface, (0, 0))
        if self.hover_pos and self.is_valid_move(self.hover_pos[0], self.hover_pos[1]):
            hover_x, hover_y = self.hover_pos
            center = (MARGIN_LEFT + hover_y * CELL_SIZE, MARGIN_TOP + hover_x * CELL_SIZE)
            hover_alpha = int(128 + 127 * math.sin(pygame.time.get_ticks() * 0.005))
            hover_color = (*PLAYER_COLOR[:3], hover_alpha)
            pygame.gfxdraw.filled_circle(screen, center[0], center[1], CELL_SIZE // 3, hover_color)
        if self.last_move:
            x, y, player = self.last_move
            center = (MARGIN_LEFT + y * CELL_SIZE, MARGIN_TOP + x * CELL_SIZE)
            pygame.draw.rect(screen, HIGHLIGHT_COLOR,
                            (center[0] - CELL_SIZE // 2, center[1] - CELL_SIZE // 2, CELL_SIZE, CELL_SIZE),
                            border_radius=5)

    def draw_stones(self):
        for stone in self.stones:
            stone.update()
            stone.draw(screen)

    def draw_winner_line(self):
        if self.winner_line and self.game_state in ["player_win", "ai_win"]:
            start_x, start_y, end_x, end_y = self.winner_line
            start_pos = (MARGIN_LEFT + start_y * CELL_SIZE, MARGIN_TOP + start_x * CELL_SIZE)
            end_pos = (MARGIN_LEFT + end_y * CELL_SIZE, MARGIN_TOP + end_x * CELL_SIZE)
            color = PLAYER_COLOR if self.game_state == "player_win" else AI_COLOR
            for width in range(12, 2, -2):
                alpha = 50 - width * 3
                if alpha > 0:
                    glow_color = (*color, alpha)
                    pygame.draw.line(screen, glow_color, start_pos, end_pos, width)
            pygame.draw.line(screen, color, start_pos, end_pos, 4)

    def draw_status(self):
        self.elapsed_time = time.time() - self.start_time if self.game_state == "playing" else self.elapsed_time
        minutes = int(self.elapsed_time // 60)
        seconds = int(self.elapsed_time % 60)
        timer_text = f"{minutes:02d}:{seconds:02d}"
        timer_surface = timer_font.render(timer_text, True, TIMER_COLOR)
        screen.blit(timer_surface, (WINDOW_WIDTH // 2 - timer_surface.get_width() // 2, 20))
        difficulty_surface = status_font.render(f"Difficulty: {self.difficulty}", True, DIFFICULTY_LEVELS[self.difficulty]["color"])
        screen.blit(difficulty_surface, (WINDOW_WIDTH - difficulty_surface.get_width() - 20, 20))
        if not self.show_modal and not self.show_difficulty_modal:
            if self.game_state == "playing":
                status = status_font.render("Your turn" if len(self.stones) % 2 == 0 else "AI is thinking...", True, TEXT_COLOR)
            elif self.game_state == "player_win":
                status = status_font.render("You win!", True, PLAYER_COLOR)
            elif self.game_state == "ai_win":
                status = status_font.render("AI wins!", True, AI_COLOR)
            else:
                status = status_font.render("Draw!", True, TEXT_COLOR)
            screen.blit(status, (WINDOW_WIDTH // 2 - status.get_width() // 2, WINDOW_HEIGHT - 40))

    def draw_title(self):
        title_text = "Gomoku"
        glow_font = pygame.font.Font(None, 75)
        pulse = math.sin(pygame.time.get_ticks() * 0.002) * 0.3 + 0.7
        glow_scale = int(75 * pulse)
        glow_surface = glow_font.render(title_text, True, TITLE_GLOW)
        if glow_scale != 75:
            glow_font = pygame.font.Font(None, glow_scale)
            glow_surface = glow_font.render(title_text, True, TITLE_GLOW)
        glow_rect = glow_surface.get_rect(center=(WINDOW_WIDTH // 2, 80))
        screen.blit(glow_surface, glow_rect)
        title_surface = title_font.render(title_text, True, TITLE_COLOR)
        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, 80))
        screen.blit(title_surface, title_rect)
        line_length = 100
        line_gap = 20
        line_y = 80
        pygame.draw.line(screen, TITLE_COLOR,
                        (title_rect.left - line_gap - line_length, line_y),
                        (title_rect.left - line_gap, line_y), 2)
        pygame.draw.circle(screen, TITLE_COLOR, (title_rect.left - line_gap - line_length, line_y), 4)
        pygame.draw.line(screen, TITLE_COLOR,
                        (title_rect.right + line_gap, line_y),
                        (title_rect.right + line_gap + line_length, line_y), 2)
        pygame.draw.circle(screen, TITLE_COLOR, (title_rect.right + line_gap + line_length, line_y), 4)

    def draw_difficulty_modal(self):
        if not self.show_difficulty_modal:
            return
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        modal_width, modal_height = 500, 400
        modal_rect = pygame.Rect(
            (WINDOW_WIDTH - modal_width) // 2,
            (WINDOW_HEIGHT - modal_height) // 2,
            modal_width, modal_height
        )
        for i in range(10, 0, -2):
            glow_rect = modal_rect.copy()
            glow_rect.inflate_ip(i*2, i*2)
            glow_alpha = 20 - i*2 if i > 0 else 0
            glow_color = (*TITLE_COLOR, glow_alpha)
            pygame.draw.rect(screen, glow_color, glow_rect, border_radius=20)
        pygame.draw.rect(screen, MODAL_BACKGROUND, modal_rect, border_radius=15)
        pygame.draw.rect(screen, TITLE_COLOR, modal_rect, border_radius=15, width=2)
        title_text = "Select Difficulty"
        title_surf = modal_font.render(title_text, True, TEXT_COLOR)
        title_rect = title_surf.get_rect(center=(modal_rect.centerx, modal_rect.y + 50))
        screen.blit(title_surf, title_rect)
        mouse_pos = pygame.mouse.get_pos()
        for button in self.difficulty_buttons:
            button.update(mouse_pos)
            button.draw(screen)

    def draw_win_loss_modal(self):
        if not self.show_modal or self.game_state == "playing":
            return
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        modal_width, modal_height = 500, 300
        modal_rect = pygame.Rect(
            (WINDOW_WIDTH - modal_width) // 2,
            (WINDOW_HEIGHT - modal_height) // 2,
            modal_width, modal_height
        )
        for i in range(10, 0, -2):
            glow_rect = modal_rect.copy()
            glow_rect.inflate_ip(i*2, i*2)
            glow_alpha = 20 - i*2 if i > 0 else 0
            glow_color = (*TITLE_COLOR, glow_alpha)
            pygame.draw.rect(screen, glow_color, glow_rect, border_radius=20)
        pygame.draw.rect(screen, MODAL_BACKGROUND, modal_rect, border_radius=15)
        pygame.draw.rect(screen, TITLE_COLOR, modal_rect, border_radius=15, width=2)
        if self.game_state == "player_win":
            message = "You Won!"
            color = PLAYER_COLOR
        elif self.game_state == "ai_win":
            message = "You Lost!"
            color = AI_COLOR
        else:
            message = "It's a Draw!"
            color = TEXT_COLOR
        for i in range(3):
            glow_surf = modal_font.render(message, True, (*color[:3], 100 - i*30))
            glow_rect = glow_surf.get_rect(center=(modal_rect.centerx, modal_rect.y + 100 + i))
            screen.blit(glow_surf, glow_rect)
        message_surf = modal_font.render(message, True, color)
        message_rect = message_surf.get_rect(center=(modal_rect.centerx, modal_rect.y + 100))
        screen.blit(message_surf, message_rect)
        minutes = int(self.elapsed_time // 60)
        seconds = int(self.elapsed_time % 60)
        time_text = f"Time: {minutes:02d}:{seconds:02d}"
        time_surf = status_font.render(time_text, True, TIMER_COLOR)
        time_rect = time_surf.get_rect(center=(modal_rect.centerx, modal_rect.y + 150))
        screen.blit(time_surf, time_rect)
        mouse_pos = pygame.mouse.get_pos()
        self.play_again_button.update(mouse_pos)
        self.play_again_button.draw(screen)

    def draw_board(self):
        self.draw_background()
        self.draw_stones()
        self.draw_winner_line()
        self.draw_status()
        self.draw_title()
        if self.show_modal:
            self.draw_win_loss_modal()
        if self.show_difficulty_modal:
            self.draw_difficulty_modal()

    def is_valid_move(self, x, y):
        return 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and self.board[x][y] == EMPTY

    def make_move(self, x, y, player, animate=True):
        self.board[x][y] = player
        self.stones.append(Stone(x, y, player, animate))
        self.last_move = (x, y, player)

    def undo_move(self, x, y):
        self.board[x][y] = EMPTY
        for i in range(len(self.stones)-1, -1, -1):
            if self.stones[i].grid_x == x and self.stones[i].grid_y == y:
                self.stones.pop(i)
                break

    def get_legal_moves(self):
        return [(i, j) for i in range(BOARD_SIZE) for j in range(BOARD_SIZE) if self.board[i][j] == EMPTY]

    def check_line(self, x, y, dx, dy, player):
        if self.board[x][y] != player:
            return False, None
        start_x, start_y = x, y
        count = 1
        for i in range(1, 5):
            nx, ny = x + i*dx, y + i*dy
            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and self.board[nx][ny] == player:
                count += 1
            else:
                break
        if count != 5:
            return False, None
        nx, ny = start_x - dx, start_y - dy
        if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and self.board[nx][ny] == player:
            return False, None
        nx, ny = start_x + 5*dx, start_y + 5*dy
        if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and self.board[nx][ny] == player:
            return False, None
        end_x = start_x + 4*dx
        end_y = start_y + 4*dy
        return True, (start_x, start_y, end_x, end_y)

    def is_winner(self, player):
        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                for dx, dy in [(1, 0), (0, 1), (1, 1), (1, -1)]:
                    won, line = self.check_line(x, y, dx, dy, player)
                    if won:
                        self.winner_line = line
                        return True
        return False

    def is_full(self):
        return all(cell != EMPTY for row in self.board for cell in row)

    def evaluate_easy(self):
        def count_lines(player):
            lines = 0
            for i in range(BOARD_SIZE):
                for j in range(BOARD_SIZE - 4):
                    segment = [self.board[i][j+k] for k in range(5)]
                    if segment.count(player) == 5:
                        lines += 100
                    elif segment.count(player) == 4 and segment.count(EMPTY) == 1:
                        lines += 10
                    elif segment.count(player) == 3 and segment.count(EMPTY) == 2:
                        lines += 5
            for i in range(BOARD_SIZE - 4):
                for j in range(BOARD_SIZE):
                    segment = [self.board[i+k][j] for k in range(5)]
                    if segment.count(player) == 5:
                        lines += 100
                    elif segment.count(player) == 4 and segment.count(EMPTY) == 1:
                        lines += 10
                    elif segment.count(player) == 3 and segment.count(EMPTY) == 2:
                        lines += 5
            for i in range(BOARD_SIZE - 4):
                for j in range(BOARD_SIZE - 4):
                    segment = [self.board[i+k][j+k] for k in range(5)]
                    if segment.count(player) == 5:
                        lines += 100
                    elif segment.count(player) == 4 and segment.count(EMPTY) == 1:
                        lines += 10
                    elif segment.count(player) == 3 and segment.count(EMPTY) == 2:
                        lines += 5
            for i in range(4, BOARD_SIZE):
                for j in range(BOARD_SIZE - 4):
                    segment = [self.board[i-k][j+k] for k in range(5)]
                    if segment.count(player) == 5:
                        lines += 100
                    elif segment.count(player) == 4 and segment.count(EMPTY) == 1:
                        lines += 10
                    elif segment.count(player) == 3 and segment.count(EMPTY) == 2:
                        lines += 5
            return lines
        return count_lines(AI) - count_lines(PLAYER) + random.randint(-5, 5)

    def evaluate_medium(self):
        def score_pattern(pattern, player):
            opponent = PLAYER if player == AI else AI
            if pattern.count(player) == 5:
                return 1000
            elif pattern.count(player) == 4 and pattern.count(EMPTY) == 1:
                return 100
            elif pattern.count(player) == 3 and pattern.count(EMPTY) == 2:
                return 10
            elif pattern.count(player) == 2 and pattern.count(EMPTY) == 3:
                return 1
            elif pattern.count(opponent) == 4 and pattern.count(EMPTY) == 1:
                return -100
            elif pattern.count(opponent) == 3 and pattern.count(EMPTY) == 2:
                return -10
            return 0
        score = 0
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE - 4):
                pattern = [self.board[i][j+k] for k in range(5)]
                score += score_pattern(pattern, AI)
        for i in range(BOARD_SIZE - 4):
            for j in range(BOARD_SIZE):
                pattern = [self.board[i+k][j] for k in range(5)]
                score += score_pattern(pattern, AI)
        for i in range(BOARD_SIZE - 4):
            for j in range(BOARD_SIZE - 4):
                pattern = [self.board[i+k][j+k] for k in range(5)]
                score += score_pattern(pattern, AI)
        for i in range(4, BOARD_SIZE):
            for j in range(BOARD_SIZE - 4):
                pattern = [self.board[i-k][j+k] for k in range(5)]
                score += score_pattern(pattern, AI)
        score += random.randint(-3, 3)
        return score

    def evaluate_hard(self):
        def score_pattern(pattern, player):
            opponent = PLAYER if player == AI else AI
            if pattern.count(player) == 5:
                return 10000
            elif pattern.count(player) == 4 and pattern.count(EMPTY) == 1:
                return 1000 if EMPTY in [pattern[0], pattern[4]] else 500
            elif pattern.count(player) == 3 and pattern.count(EMPTY) == 2:
                empty_indices = [i for i, x in enumerate(pattern) if x == EMPTY]
                return 200 if 0 in empty_indices and 4 in empty_indices else 50
            elif pattern.count(player) == 2 and pattern.count(EMPTY) == 3:
                empty_indices = [i for i, x in enumerate(pattern) if x == EMPTY]
                return 10 if 0 in empty_indices and 4 in empty_indices else 5
            elif pattern.count(opponent) == 4 and pattern.count(EMPTY) == 1:
                return -1000
            elif pattern.count(opponent) == 3 and pattern.count(EMPTY) == 2:
                empty_indices = [i for i, x in enumerate(pattern) if x == EMPTY]
                return -200 if 0 in empty_indices and 4 in empty_indices else -50
            elif pattern.count(opponent) == 2 and pattern.count(EMPTY) == 3:
                empty_indices = [i for i, x in enumerate(pattern) if x == EMPTY]
                return -10 if 0 in empty_indices and 4 in empty_indices else -5
            return 0
        score = 0
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE - 4):
                pattern = [self.board[i][j+k] for k in range(5)]
                score += score_pattern(pattern, AI)
        for i in range(BOARD_SIZE - 4):
            for j in range(BOARD_SIZE):
                pattern = [self.board[i+k][j] for k in range(5)]
                score += score_pattern(pattern, AI)
        for i in range(BOARD_SIZE - 4):
            for j in range(BOARD_SIZE - 4):
                pattern = [self.board[i+k][j+k] for k in range(5)]
                score += score_pattern(pattern, AI)
        for i in range(4, BOARD_SIZE):
            for j in range(BOARD_SIZE - 4):
                pattern = [self.board[i-k][j+k] for k in range(5)]
                score += score_pattern(pattern, AI)
        center = BOARD_SIZE // 2
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if self.board[i][j] == AI:
                    distance_from_center = max(abs(i - center), abs(j - center))
                    score += (5 - distance_from_center) // 2
        return score

    def evaluate(self):
        if self.difficulty == "Easy":
            return self.evaluate_easy()
        elif self.difficulty == "Medium":
            return self.evaluate_medium()
        return self.evaluate_hard()

    def minimax(self, depth, alpha, beta, is_maximizing):
        if self.is_winner(AI):
            return 1000 * (depth + 1)
        if self.is_winner(PLAYER):
            return -1000 * (depth + 1)
        if self.is_full() or depth == 0:
            return self.evaluate()
        legal_moves = self.get_smart_moves()
        if is_maximizing:
            max_eval = float('-inf')
            for move in legal_moves:
                x, y = move
                self.make_move(x, y, AI, animate=False)
                eval = self.minimax(depth - 1, alpha, beta, False)
                self.undo_move(x, y)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                x, y = move
                self.make_move(x, y, PLAYER, animate=False)
                eval = self.minimax(depth - 1, alpha, beta, True)
                self.undo_move(x, y)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    def get_smart_moves(self):
        if not any(cell != EMPTY for row in self.board for cell in row):
            center = BOARD_SIZE // 2
            return [(center, center)]
        moves = set()
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                if self.board[i][j] != EMPTY:
                    for di in range(-1, 2):
                        for dj in range(-1, 2):
                            if di == 0 and dj == 0:
                                continue
                            ni, nj = i + di, j + dj
                            if 0 <= ni < BOARD_SIZE and 0 <= nj < BOARD_SIZE and self.board[ni][nj] == EMPTY:
                                moves.add((ni, nj))
        return list(moves) or self.get_legal_moves()

    def get_best_move(self):
        best_score = float('-inf')
        best_move = None
        depth = DIFFICULTY_LEVELS[self.difficulty]["depth"]
        legal_moves = self.get_smart_moves()
        random.shuffle(legal_moves)
        for move in legal_moves:
            x, y = move
            self.make_move(x, y, AI, animate=False)
            score = self.minimax(depth, float('-inf'), float('inf'), False)
            self.undo_move(x, y)
            if self.difficulty == "Easy":
                score += random.randint(-100, 100)
            elif self.difficulty == "Medium":
                score += random.randint(-30, 30)
            if score > best_score:
                best_score = score
                best_move = move
        return best_move

    def ai_move(self):
        if self.game_state != "playing":
            return
        move = self.get_best_move()
        if move:
            x, y = move
            self.make_move(x, y, AI)
            if self.is_winner(AI):
                self.game_state = "ai_win"
                self.show_modal = True
            elif self.is_full():
                self.game_state = "draw"
                self.show_modal = True

    def handle_click(self, pos):
        if self.show_modal:
            if self.play_again_button.is_clicked(pos, True):
                self.reset()
                return
        if self.show_difficulty_modal:
            for i, button in enumerate(self.difficulty_buttons):
                if button.is_clicked(pos, True):
                    self.difficulty = list(DIFFICULTY_LEVELS.keys())[i]
                    self.show_difficulty_modal = False
                    return
            return
        if self.game_state != "playing" or len(self.stones) % 2 != 0:
            return
        x = (pos[1] - MARGIN_TOP + CELL_SIZE // 2) // CELL_SIZE
        y = (pos[0] - MARGIN_LEFT + CELL_SIZE // 2) // CELL_SIZE
        if self.is_valid_move(x, y):
            self.make_move(x, y, PLAYER)
            if self.is_winner(PLAYER):
                self.game_state = "player_win"
                self.show_modal = True
            elif self.is_full():
                self.game_state = "draw"
                self.show_modal = True
            else:
                pygame.time.set_timer(pygame.USEREVENT, 300)  # Reduced delay for faster AI response

    def update_hover(self, pos):
        x = (pos[1] - MARGIN_TOP + CELL_SIZE // 2) // CELL_SIZE
        y = (pos[0] - MARGIN_LEFT + CELL_SIZE // 2) // CELL_SIZE
        self.hover_pos = (x, y) if 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE else None

class GameManager:
    def __init__(self):
        self.state = "menu"
        self.game = None
        self.ai_thinking = False
        self.selected_difficulty = "Medium"

        # Layout constants
        title_y = 100  # Move GOMOKU to top
        layout_center_y = WINDOW_HEIGHT // 2
        subtitle_y = layout_center_y - 50
        button_y = layout_center_y + 10
        play_y = layout_center_y + 100

        # Setup difficulty buttons
        self.difficulty_buttons = []
        button_width = 160
        button_height = 60
        spacing = 40
        total_width = (button_width + spacing) * len(DIFFICULTY_LEVELS) - spacing
        start_x = (WINDOW_WIDTH - total_width) // 2

        for i, level in enumerate(DIFFICULTY_LEVELS):
            color = DIFFICULTY_LEVELS[level]["color"]
            hover = tuple(min(c + 50, 255) for c in color)
            self.difficulty_buttons.append(
                Button(
                    start_x + i * (button_width + spacing),
                    button_y,
                    button_width,
                    button_height,
                    level,
                    color,
                    hover
                )
            )

        self.play_button = Button(
            WINDOW_WIDTH // 2 - 110,
            play_y,
            220,
            70,
            "Play",
            (60, 150, 250),
            (100, 180, 255)
        )

        self.balls = [
            {
                "x": random.randint(0, WINDOW_WIDTH),
                "y": random.randint(0, WINDOW_HEIGHT),
                "radius": random.randint(6, 12),
                "color": random.choice([
                    (160, 180, 200, 15),
                    (140, 160, 190, 15),
                    (120, 140, 180, 15),
                    (100, 120, 160, 15),
                    (80, 100, 140, 15),
                ]),
                "dx": random.choice([-1, 1]) * random.uniform(0.1, 0.2),
                "dy": random.choice([-1, 1]) * random.uniform(0.1, 0.2),
            }
            for _ in range(10)
        ]

        self.title_y = title_y
        self.subtitle_y = subtitle_y
        self.tip_y = WINDOW_HEIGHT - 30

    def draw_static_background(self):
        top_color = (30, 50, 80)
        bottom_color = (15, 25, 45)
        check_size = 40
        for y in range(WINDOW_HEIGHT):
            ratio = y / WINDOW_HEIGHT
            r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
            g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
            b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
            pygame.draw.line(screen, (r, g, b), (0, y), (WINDOW_WIDTH, y))

        check_color = (255, 255, 255, 10)
        check_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        for x in range(0, WINDOW_WIDTH, check_size):
            for y in range(0, WINDOW_HEIGHT, check_size):
                pygame.draw.rect(check_surface, check_color, (x, y, check_size, check_size), 1)
        screen.blit(check_surface, (0, 0))

        for ball in self.balls:
            pygame.draw.circle(screen, ball["color"], (int(ball["x"]), int(ball["y"])), ball["radius"])
            ball["x"] += ball["dx"]
            ball["y"] += ball["dy"]
            if not (0 <= ball["x"] <= WINDOW_WIDTH):
                ball["dx"] *= -1
            if not (0 <= ball["y"] <= WINDOW_HEIGHT):
                ball["dy"] *= -1

    def draw_menu(self):
        self.draw_static_background()

        title_surface = title_font.render("GOMOKU", True, TITLE_COLOR)
        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, self.title_y))
        screen.blit(title_surface, title_rect)

        subtitle_surface = game_font.render("Select Difficulty", True, (200, 220, 240))
        subtitle_rect = subtitle_surface.get_rect(center=(WINDOW_WIDTH // 2, self.subtitle_y))
        screen.blit(subtitle_surface, subtitle_rect)

        mouse_pos = pygame.mouse.get_pos()

        for i, button in enumerate(self.difficulty_buttons):
            button.update(mouse_pos)
            if list(DIFFICULTY_LEVELS)[i] == self.selected_difficulty:
                glow = pygame.Rect(button.rect.x - 5, button.rect.y - 5, button.rect.width + 10, button.rect.height + 10)
                pygame.draw.rect(screen, (255, 255, 255, 30), glow, border_radius=12)
                pygame.draw.rect(screen, (240, 240, 240), glow, border_radius=12, width=1)
            button.draw(screen)

        self.play_button.update(mouse_pos)
        self.play_button.draw(screen)

        tip_surface = status_font.render("Tip: Connect 5 in a row to win!", True, (180, 200, 220))
        tip_rect = tip_surface.get_rect(center=(WINDOW_WIDTH // 2, self.tip_y))
        screen.blit(tip_surface, tip_rect)

    def update(self):
        if self.state == "menu":
            self.draw_menu()
        elif self.state == "playing":
            self.game.draw_board()
        pygame.display.flip()

    async def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.state == "menu":
                    for i, button in enumerate(self.difficulty_buttons):
                        if button.is_clicked(event.pos, True):
                            self.selected_difficulty = list(DIFFICULTY_LEVELS)[i]
                            break
                    if self.play_button.is_clicked(event.pos, True):
                        self.state = "playing"
                        self.game = Gomoku()
                        self.game.difficulty = self.selected_difficulty
                elif self.state == "playing":
                    self.game.handle_click(event.pos)
            elif event.type == pygame.MOUSEMOTION:
                if self.state == "playing":
                    self.game.update_hover(event.pos)
            elif event.type == pygame.USEREVENT and not self.ai_thinking and self.state == "playing":
                pygame.time.set_timer(pygame.USEREVENT, 0)
                self.ai_thinking = True

        if self.state == "playing" and self.game.game_state == "playing" and len(self.game.stones) % 2 == 1 and self.ai_thinking:
            self.game.ai_move()
            self.ai_thinking = False

        return True

async def main():
    manager = GameManager()
    running = True
    while running:
        manager.update()
        running = await manager.handle_events()
        await asyncio.sleep(1.0 / FPS)
    pygame.quit()

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())