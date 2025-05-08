import math

BOARD_SIZE = 5
EMPTY = '.'
PLAYER = 'X'
AI = 'O'

class Gomoku:
    def __init__(self):
        self.board = [[EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

    def is_valid_move(self, x, y):
        return 0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE and self.board[x][y] == EMPTY

    def make_move(self, x, y, player):
        self.board[x][y] = player

    def undo_move(self, x, y):
        self.board[x][y] = EMPTY

    def is_winner(self, player):
        def check_line(x, y, dx, dy):
            for i in range(4):
                nx, ny = x + i*dx, y + i*dy
                if not (0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE) or self.board[nx][ny] != player:
                    return False
            return True
        for x in range(BOARD_SIZE):
            for y in range(BOARD_SIZE):
                if any(check_line(x, y, dx, dy) for dx, dy in [(1,0), (0,1), (1,1), (1,-1)]):
                    return True
        return False

    def get_legal_moves(self):
        return [(i, j) for i in range(BOARD_SIZE) for j in range(BOARD_SIZE) if self.board[i][j] == EMPTY]

    def evaluate(self):
        if self.is_winner(AI): return 100
        if self.is_winner(PLAYER): return -100
        return 0

    def minimax(self, depth, alpha, beta, maximizing):
        if self.is_winner(AI) or self.is_winner(PLAYER) or depth == 0:
            return self.evaluate(), None

        best_move = None
        if maximizing:
            max_eval = -math.inf
            for move in self.get_legal_moves():
                self.make_move(*move, AI)
                eval, _ = self.minimax(depth - 1, alpha, beta, False)
                self.undo_move(*move)
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
                self.make_move(*move, PLAYER)
                eval, _ = self.minimax(depth - 1, alpha, beta, True)
                self.undo_move(*move)
                if eval < min_eval:
                    min_eval = eval
                    best_move = move
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval, best_move

def test_minimax():
    game = Gomoku()
    game.make_move(0, 0, PLAYER)
    game.make_move(0, 1, PLAYER)
    game.make_move(1, 0, AI)
    game.make_move(1, 1, AI)
    _, move = game.minimax(depth=3, alpha=-math.inf, beta=math.inf, maximizing=True)
    print("Best move for AI:", move)

if __name__ == "__main__":
    test_minimax()
