import pygame
import random
import math

BOARD_SIZE = 10
CELL_SIZE = 60
MARGIN = 40
WINDOW_SIZE = BOARD_SIZE * CELL_SIZE + MARGIN * 2
EMPTY = '.'
PLAYER = 'X'
AI = 'O'

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

pygame.init()
font = pygame.font.SysFont(None, 36)
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("Gomoku")

class Gomoku:
    def __init__(self):
        self.board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    def draw_board(self):
        screen.fill(WHITE)
        for i in range(BOARD_SIZE):
            pygame.draw.line(screen, BLACK, (MARGIN, MARGIN + i * CELL_SIZE), (WINDOW_SIZE - MARGIN, MARGIN + i * CELL_SIZE))
            pygame.draw.line(screen, BLACK, (MARGIN + i * CELL_SIZE, MARGIN), (MARGIN + i * CELL_SIZE, WINDOW_SIZE - MARGIN))

        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                center = (MARGIN + y * CELL_SIZE, MARGIN + x * CELL_SIZE)
                if self.board[x][y] == PLAYER:
                    pygame.draw.circle(screen, RED, center, CELL_SIZE // 3)
                elif self.board[x][y] == AI:
                    pygame.draw.circle(screen, BLUE, center, CELL_SIZE // 3)

        pygame.display.flip()

    def is_valid_move(self, x, y):
        return 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and self.board[x][y] == EMPTY

    def make_move(self, x, y, player):
        self.board[x][y] = player

    def undo_move(self, x, y):
        self.board[x][y] = EMPTY

    def get_legal_moves(self):
        return [(i, j) for i in range(BOARD_SIZE) for j in range(BOARD_SIZE) if self.board[i][j] == EMPTY]

    def is_winner(self, player):
        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                if self.check_line(x, y, 1, 0, player): return True
                if self.check_line(x, y, 0, 1, player): return True
                if self.check_line(x, y, 1, 1, player): return True
                if self.check_line(x, y, 1, -1, player): return True
        return False

    def check_line(self, x, y, dx, dy, player):
        count = 0
        for i in range(5):
            nx, ny = x + i*dx, y + i*dy
            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and self.board[nx][ny] == player:
                count += 1
            else:
                break
        return count == 5

    def is_full(self):
        return all(cell != EMPTY for row in self.board for cell in row)

    def game_over(self):
        return self.is_winner(PLAYER) or self.is_winner(AI) or self.is_full()

    def evaluate(self):
        if self.is_winner(AI): return 1000
        if self.is_winner(PLAYER): return -1000
        return 0

    def minimax(self, depth, alpha, beta, maximizing):
        if self.game_over() or depth == 0:
            return self.evaluate(), None

        best_move = None
        if maximizing:
            max_eval = -math.inf
            for move in self.get_legal_moves():
                self.make_move(move[0], move[1], AI)
                eval, _ = self.minimax(depth-1, alpha, beta, False)
                self.undo_move(move[0], move[1])
                if eval > max_eval:
                    max_eval = eval
                    best_move = move
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = math.inf
            for move in self.get_legal_moves():
                self.make_move(move[0], move[1], PLAYER)
                eval, _ = self.minimax(depth-1, alpha, beta, True)
                self.undo_move(move[0], move[1])
                if eval < min_eval:
                    min_eval = eval
                    best_move = move
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval, best_move

def main():
    game = Gomoku()
    running = True
    player_turn = True

    while running:
        game.draw_board()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and player_turn and not game.game_over():
                mx, my = pygame.mouse.get_pos()
                x = (my - MARGIN + CELL_SIZE // 2) // CELL_SIZE
                y = (mx - MARGIN + CELL_SIZE // 2) // CELL_SIZE
                if game.is_valid_move(x, y):
                    game.make_move(x, y, PLAYER)
                    player_turn = False

        if not player_turn and not game.game_over():
            _, move = game.minimax(depth=3, alpha=-math.inf, beta=math.inf, maximizing=True)
            if move:
                game.make_move(move[0], move[1], AI)
            player_turn = True

        if game.game_over():
            game.draw_board()
            pygame.time.wait(1000)
            if game.is_winner(PLAYER):
                print("You win!")
            elif game.is_winner(AI):
                print("AI wins!")
            else:
                print("Draw!")
            pygame.time.wait(2000)
            running = False

    pygame.quit()

if __name__ == '__main__':
    main()