import pygame
import sys
import copy

# Инициализация Pygame
pygame.init()

# Константы
BOARD_SIZE = 8
SQUARE_SIZE = 80
BOARD_PIXELS = BOARD_SIZE * SQUARE_SIZE
WINDOW_WIDTH = BOARD_PIXELS
WINDOW_HEIGHT = BOARD_PIXELS + 60

# Цвета
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
SELECTED = (106, 170, 100)
POSSIBLE_MOVE = (130, 151, 130)
LAST_MOVE = (247, 236, 92)
CHECK_COLOR = (220, 50, 50)
WHITE_PIECE = (255, 255, 255)
BLACK_PIECE = (30, 30, 30)
WHITE_OUTLINE = (40, 40, 40)
BLACK_OUTLINE = (220, 220, 220)
BORDER_COLOR = (50, 50, 50)

# Настройка окна
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Шахматы")
clock = pygame.time.Clock()


class Piece:
    def __init__(self, color, piece_type):
        self.color = color
        self.piece_type = piece_type
        self.has_moved = False


def create_initial_board():
    """Создаёт начальную расстановку фигур"""
    board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    back_row = ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook']
    for col, piece_type in enumerate(back_row):
        board[0][col] = Piece('black', piece_type)
    for col in range(BOARD_SIZE):
        board[1][col] = Piece('black', 'pawn')
    for col, piece_type in enumerate(back_row):
        board[7][col] = Piece('white', piece_type)
    for col in range(BOARD_SIZE):
        board[6][col] = Piece('white', 'pawn')
    return board


def is_in_bounds(row, col):
    return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE


def find_king(board, color):
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            piece = board[row][col]
            if piece and piece.piece_type == 'king' and piece.color == color:
                return row, col
    return None


def get_raw_moves(board, row, col, piece):
    moves = []
    color = piece.color
    enemy = 'black' if color == 'white' else 'white'

    if piece.piece_type == 'pawn':
        direction = -1 if color == 'white' else 1
        start_row = 6 if color == 'white' else 1
        if is_in_bounds(row + direction, col) and not board[row + direction][col]:
            moves.append((row + direction, col))
            if row == start_row and not board[row + 2 * direction][col]:
                moves.append((row + 2 * direction, col))
        for dc in [-1, 1]:
            nr, nc = row + direction, col + dc
            if is_in_bounds(nr, nc) and board[nr][nc] and board[nr][nc].color == enemy:
                moves.append((nr, nc))

    elif piece.piece_type == 'knight':
        offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                   (1, -2), (1, 2), (2, -1), (2, 1)]
        for dr, dc in offsets:
            nr, nc = row + dr, col + dc
            if is_in_bounds(nr, nc):
                target = board[nr][nc]
                if not target or target.color == enemy:
                    moves.append((nr, nc))

    elif piece.piece_type == 'bishop':
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nr, nc = row + dr, col + dc
            while is_in_bounds(nr, nc):
                target = board[nr][nc]
                if not target:
                    moves.append((nr, nc))
                elif target.color == enemy:
                    moves.append((nr, nc))
                    break
                else:
                    break
                nr += dr
                nc += dc

    elif piece.piece_type == 'rook':
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            while is_in_bounds(nr, nc):
                target = board[nr][nc]
                if not target:
                    moves.append((nr, nc))
                elif target.color == enemy:
                    moves.append((nr, nc))
                    break
                else:
                    break
                nr += dr
                nc += dc

    elif piece.piece_type == 'queen':
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1),
                       (-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            while is_in_bounds(nr, nc):
                target = board[nr][nc]
                if not target:
                    moves.append((nr, nc))
                elif target.color == enemy:
                    moves.append((nr, nc))
                    break
                else:
                    break
                nr += dr
                nc += dc

    elif piece.piece_type == 'king':
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if is_in_bounds(nr, nc):
                    target = board[nr][nc]
                    if not target or target.color == enemy:
                        moves.append((nr, nc))
    return moves


def is_square_attacked(board, row, col, by_color):
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            piece = board[r][c]
            if piece and piece.color == by_color:
                if (row, col) in get_raw_moves(board, r, c, piece):
                    return True
    return False


def is_in_check(board, color):
    king_pos = find_king(board, color)
    if not king_pos:
        return False
    enemy = 'black' if color == 'white' else 'white'
    return is_square_attacked(board, king_pos[0], king_pos[1], enemy)


def get_legal_moves(board, row, col):
    piece = board[row][col]
    if not piece:
        return []
    raw_moves = get_raw_moves(board, row, col, piece)
    legal_moves = []
    for nr, nc in raw_moves:
        new_board = copy.deepcopy(board)
        new_board[nr][nc] = new_board[row][col]
        new_board[row][col] = None
        if not is_in_check(new_board, piece.color):
            legal_moves.append((nr, nc))
    return legal_moves


def has_any_legal_moves(board, color):
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            piece = board[row][col]
            if piece and piece.color == color:
                if get_legal_moves(board, row, col):
                    return True
    return False


def make_move(board, from_pos, to_pos):
    fr, fc = from_pos
    tr, tc = to_pos
    piece = board[fr][fc]
    board[tr][tc] = piece
    board[fr][fc] = None
    piece.has_moved = True
    if piece.piece_type == 'pawn':
        if (piece.color == 'white' and tr == 0) or (piece.color == 'black' and tr == 7):
            piece.piece_type = 'queen'


# ============ ПРОГРАММНАЯ ОТРИСОВКА ФИГУР ============

def draw_piece(screen, piece, row, col):
    """Рисует фигуру программно через pygame.draw"""
    cx = col * SQUARE_SIZE + SQUARE_SIZE // 2
    cy = row * SQUARE_SIZE + SQUARE_SIZE // 2
    
    fill = WHITE_PIECE if piece.color == 'white' else BLACK_PIECE
    outline = WHITE_OUTLINE if piece.color == 'white' else BLACK_OUTLINE
    
    # Базовая подставка (основание) для всех фигур
    base_rect = pygame.Rect(cx - 22, cy + 18, 44, 8)
    pygame.draw.rect(screen, fill, base_rect)
    pygame.draw.rect(screen, outline, base_rect, 2)
    
    if piece.piece_type == 'pawn':
        # Голова
        pygame.draw.circle(screen, fill, (cx, cy - 8), 12)
        pygame.draw.circle(screen, outline, (cx, cy - 8), 12, 2)
        # Тело
        pygame.draw.polygon(screen, fill, [(cx - 10, cy + 18), (cx + 10, cy + 18),
                                           (cx + 6, cy - 2), (cx - 6, cy - 2)])
        pygame.draw.polygon(screen, outline, [(cx - 10, cy + 18), (cx + 10, cy + 18),
                                              (cx + 6, cy - 2), (cx - 6, cy - 2)], 2)
    
    elif piece.piece_type == 'rook':
        # Тело
        pygame.draw.polygon(screen, fill, [(cx - 14, cy + 18), (cx + 14, cy + 18),
                                           (cx + 12, cy - 12), (cx - 12, cy - 12)])
        pygame.draw.polygon(screen, outline, [(cx - 14, cy + 18), (cx + 14, cy + 18),
                                              (cx + 12, cy - 12), (cx - 12, cy - 12)], 2)
        # Зубцы
        for dx in [-12, -4, 4, 12]:
            pygame.draw.rect(screen, fill, (cx + dx - 3, cy - 20, 6, 8))
            pygame.draw.rect(screen, outline, (cx + dx - 3, cy - 20, 6, 8), 2)
    
    elif piece.piece_type == 'knight':
        # Силуэт коня
        points = [(cx - 14, cy + 18), (cx + 14, cy + 18),
                  (cx + 14, cy - 2), (cx + 10, cy - 14),
                  (cx + 2, cy - 20), (cx - 8, cy - 18),
                  (cx - 14, cy - 8), (cx - 10, cy - 2)]
        pygame.draw.polygon(screen, fill, points)
        pygame.draw.polygon(screen, outline, points, 2)
        # Глаз
        pygame.draw.circle(screen, outline, (cx - 2, cy - 10), 2)
    
    elif piece.piece_type == 'bishop':
        # Тело
        pygame.draw.polygon(screen, fill, [(cx - 12, cy + 18), (cx + 12, cy + 18),
                                           (cx + 6, cy - 10), (cx - 6, cy - 10)])
        pygame.draw.polygon(screen, outline, [(cx - 12, cy + 18), (cx + 12, cy + 18),
                                              (cx + 6, cy - 10), (cx - 6, cy - 10)], 2)
        # Голова (овал)
        pygame.draw.ellipse(screen, fill, (cx - 8, cy - 22, 16, 16))
        pygame.draw.ellipse(screen, outline, (cx - 8, cy - 22, 16, 16), 2)
        # Шарик сверху
        pygame.draw.circle(screen, fill, (cx, cy - 24), 3)
        pygame.draw.circle(screen, outline, (cx, cy - 24), 3, 1)
        # Прорезь
        pygame.draw.line(screen, outline, (cx - 4, cy - 16), (cx + 4, cy - 16), 2)
    
    elif piece.piece_type == 'queen':
        # Тело
        pygame.draw.polygon(screen, fill, [(cx - 14, cy + 18), (cx + 14, cy + 18),
                                           (cx + 10, cy - 8), (cx - 10, cy - 8)])
        pygame.draw.polygon(screen, outline, [(cx - 14, cy + 18), (cx + 14, cy + 18),
                                              (cx + 10, cy - 8), (cx - 10, cy - 8)], 2)
        # Корона
        crown = [(cx - 12, cy - 8), (cx - 10, cy - 20), (cx - 5, cy - 12),
                 (cx, cy - 22), (cx + 5, cy - 12), (cx + 10, cy - 20),
                 (cx + 12, cy - 8)]
        pygame.draw.polygon(screen, fill, crown)
        pygame.draw.polygon(screen, outline, crown, 2)
        # Шарики на короне
        for dx in [-10, 0, 10]:
            pygame.draw.circle(screen, fill, (cx + dx, cy - 20), 3)
            pygame.draw.circle(screen, outline, (cx + dx, cy - 20), 3, 1)
    
    elif piece.piece_type == 'king':
        # Тело
        pygame.draw.polygon(screen, fill, [(cx - 14, cy + 18), (cx + 14, cy + 18),
                                           (cx + 10, cy - 8), (cx - 10, cy - 8)])
        pygame.draw.polygon(screen, outline, [(cx - 14, cy + 18), (cx + 14, cy + 18),
                                              (cx + 10, cy - 8), (cx - 10, cy - 8)], 2)
        # Голова
        pygame.draw.ellipse(screen, fill, (cx - 9, cy - 20, 18, 14))
        pygame.draw.ellipse(screen, outline, (cx - 9, cy - 20, 18, 14), 2)
        # Крест сверху
        pygame.draw.rect(screen, fill, (cx - 2, cy - 30, 4, 12))
        pygame.draw.rect(screen, fill, (cx - 6, cy - 26, 12, 4))
        pygame.draw.rect(screen, outline, (cx - 2, cy - 30, 4, 12), 1)
        pygame.draw.rect(screen, outline, (cx - 6, cy - 26, 12, 4), 1)


def draw_board(screen, board, selected, legal_moves, last_move, current_player, game_status):
    """Отрисовывает доску, фигуры и интерфейс"""
    screen.fill(BORDER_COLOR)
    
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            x = col * SQUARE_SIZE
            y = row * SQUARE_SIZE
            color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
            if last_move and (row, col) in last_move:
                color = LAST_MOVE
            pygame.draw.rect(screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))
    
    if selected:
        sr, sc = selected
        pygame.draw.rect(screen, SELECTED,
                        (sc * SQUARE_SIZE, sr * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
    
    if legal_moves:
        for mr, mc in legal_moves:
            center_x = mc * SQUARE_SIZE + SQUARE_SIZE // 2
            center_y = mr * SQUARE_SIZE + SQUARE_SIZE // 2
            if board[mr][mc]:
                pygame.draw.rect(screen, POSSIBLE_MOVE,
                                (mc * SQUARE_SIZE + 5, mr * SQUARE_SIZE + 5,
                                 SQUARE_SIZE - 10, SQUARE_SIZE - 10), 4)
            else:
                pygame.draw.circle(screen, POSSIBLE_MOVE, (center_x, center_y), 15)
    
    if is_in_check(board, current_player):
        king_pos = find_king(board, current_player)
        if king_pos:
            kr, kc = king_pos
            pygame.draw.rect(screen, CHECK_COLOR,
                            (kc * SQUARE_SIZE + 5, kr * SQUARE_SIZE + 5,
                             SQUARE_SIZE - 10, SQUARE_SIZE - 10), 5)
    
    # Рисуем фигуры программно
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            piece = board[row][col]
            if piece:
                draw_piece(screen, piece, row, col)
    
    # Нижняя панель
    pygame.draw.rect(screen, (40, 40, 40), (0, BOARD_PIXELS, WINDOW_WIDTH, 60))
    status_font = pygame.font.Font(None, 32)
    if game_status:
        status_text = status_font.render(game_status, True, (255, 200, 100))
    else:
        player_name = "Белые" if current_player == 'white' else "Чёрные"
        check_text = " (ШАХ!)" if is_in_check(board, current_player) else ""
        status_text = status_font.render(f"Ход: {player_name}{check_text}",
                                         True, WHITE_PIECE if current_player == 'white' else (200, 200, 200))
    status_rect = status_text.get_rect(center=(WINDOW_WIDTH // 2, BOARD_PIXELS + 30))
    screen.blit(status_text, status_rect)


def get_square_from_pos(pos):
    x, y = pos
    if y >= BOARD_PIXELS:
        return None
    col = x // SQUARE_SIZE
    row = y // SQUARE_SIZE
    if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
        return row, col
    return None


def main():
    board = create_initial_board()
    current_player = 'white'
    selected = None
    legal_moves = []
    last_move = None
    game_status = None
    game_over = False
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                if event.button == 1:
                    square = get_square_from_pos(event.pos)
                    if square is None:
                        continue
                    row, col = square
                    piece = board[row][col]
                    if selected:
                        sr, sc = selected
                        if (row, col) == (sr, sc):
                            selected = None
                            legal_moves = []
                        elif piece and piece.color == current_player:
                            selected = (row, col)
                            legal_moves = get_legal_moves(board, row, col)
                        elif (row, col) in legal_moves:
                            make_move(board, selected, (row, col))
                            last_move = (selected, (row, col))
                            selected = None
                            legal_moves = []
                            current_player = 'black' if current_player == 'white' else 'white'
                            if not has_any_legal_moves(board, current_player):
                                game_over = True
                                if is_in_check(board, current_player):
                                    winner = 'Чёрные' if current_player == 'white' else 'Белые'
                                    game_status = f"МАТ! Победили {winner}"
                                else:
                                    game_status = "ПАТ! Ничья"
                    else:
                        if piece and piece.color == current_player:
                            selected = (row, col)
                            legal_moves = get_legal_moves(board, row, col)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    board = create_initial_board()
                    current_player = 'white'
                    selected = None
                    legal_moves = []
                    last_move = None
                    game_status = None
                    game_over = False
        
        draw_board(screen, board, selected, legal_moves, last_move, current_player, game_status)
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()