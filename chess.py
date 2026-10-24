import pygame
import sys
import copy

pygame.init()

BOARD_SIZE = 8
SQUARE_SIZE = 80
BOARD_PIXELS = BOARD_SIZE * SQUARE_SIZE
WINDOW_WIDTH = BOARD_PIXELS
WINDOW_HEIGHT = BOARD_PIXELS + 60

LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
SELECTED = (106, 170, 100)
POSSIBLE_MOVE = (130, 151, 130)
LAST_MOVE = (247, 236, 92)
CHECK_COLOR = (220, 50, 50)
BORDER_COLOR = (50, 50, 50)

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Шахматы")
clock = pygame.time.Clock()


class Piece:
    def __init__(self, color, piece_type):
        self.color = color
        self.piece_type = piece_type
        self.has_moved = False


def create_initial_board():
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


def get_raw_moves(board, row, col, piece, en_passant_target=None, check_castling=True):
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
            if is_in_bounds(nr, nc):
                target = board[nr][nc]
                if target and target.color == enemy:
                    moves.append((nr, nc))
                if en_passant_target and (nr, nc) == en_passant_target:
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

        if check_castling and not piece.has_moved and not is_in_check(board, color):
            base_row = 7 if color == 'white' else 0
            if row == base_row:
                rook_k = board[base_row][7]
                if (rook_k and rook_k.piece_type == 'rook' and
                        not rook_k.has_moved and
                        board[base_row][5] is None and
                        board[base_row][6] is None):
                    if (not is_square_attacked(board, base_row, 5, enemy) and
                            not is_square_attacked(board, base_row, 6, enemy)):
                        moves.append((base_row, 6))

                rook_q = board[base_row][0]
                if (rook_q and rook_q.piece_type == 'rook' and
                        not rook_q.has_moved and
                        board[base_row][1] is None and
                        board[base_row][2] is None and
                        board[base_row][3] is None):
                    if (not is_square_attacked(board, base_row, 3, enemy) and
                            not is_square_attacked(board, base_row, 2, enemy)):
                        moves.append((base_row, 2))

    return moves


def is_square_attacked(board, row, col, by_color):
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            piece = board[r][c]
            if piece and piece.color == by_color:
                if (row, col) in get_raw_moves(board, r, c, piece, check_castling=False):
                    return True
    return False


def is_in_check(board, color):
    king_pos = find_king(board, color)
    if not king_pos:
        return False
    enemy = 'black' if color == 'white' else 'white'
    return is_square_attacked(board, king_pos[0], king_pos[1], enemy)


def get_legal_moves(board, row, col, en_passant_target=None):
    piece = board[row][col]
    if not piece:
        return []

    raw_moves = get_raw_moves(board, row, col, piece, en_passant_target, check_castling=True)
    legal_moves = []

    for nr, nc in raw_moves:
        new_board = copy.deepcopy(board)
        new_board[nr][nc] = new_board[row][col]
        new_board[row][col] = None

        if piece.piece_type == 'king' and abs(nc - col) == 2:
            base_row = row
            if nc == 6:
                new_board[base_row][5] = new_board[base_row][7]
                new_board[base_row][7] = None
            elif nc == 2:
                new_board[base_row][3] = new_board[base_row][0]
                new_board[base_row][0] = None

        if not is_in_check(new_board, piece.color):
            legal_moves.append((nr, nc))

    return legal_moves


def has_any_legal_moves(board, color, en_passant_target=None):
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            piece = board[row][col]
            if piece and piece.color == color:
                if get_legal_moves(board, row, col, en_passant_target):
                    return True
    return False


def make_move(board, from_pos, to_pos, en_passant_target=None):
    fr, fc = from_pos
    tr, tc = to_pos
    piece = board[fr][fc]
    new_en_passant = None

    if (piece.piece_type == 'pawn' and en_passant_target and
            (tr, tc) == en_passant_target):
        direction = -1 if piece.color == 'white' else 1
        captured_row = tr - direction
        board[captured_row][tc] = None

    if piece.piece_type == 'king' and abs(tc - fc) == 2:
        base_row = fr
        if tc == 6:
            rook = board[base_row][7]
            board[base_row][5] = rook
            board[base_row][7] = None
            if rook:
                rook.has_moved = True
        elif tc == 2:
            rook = board[base_row][0]
            board[base_row][3] = rook
            board[base_row][0] = None
            if rook:
                rook.has_moved = True

    board[tr][tc] = piece
    board[fr][fc] = None
    piece.has_moved = True

    if piece.piece_type == 'pawn':
        if (piece.color == 'white' and tr == 0) or (piece.color == 'black' and tr == 7):
            piece.piece_type = 'queen'
        if abs(tr - fr) == 2:
            new_en_passant = ((fr + tr) // 2, fc)

    return new_en_passant


def draw_piece(surface, row, col, piece, sq):
    """Рисует шахматную фигуру примитивами Pygame"""
    k = sq / 100.0
    ox, oy = col * sq, row * sq

    if piece.color == 'white':
        fill, edge, detail = (242, 240, 232), (30, 30, 30), (70, 70, 70)
    else:
        fill, edge, detail = (48, 48, 56), (12, 12, 16), (205, 205, 210)

    lw = max(2, round(2.2 * k))

    def P(p):
        return (ox + p[0] * k, oy + p[1] * k)

    def poly(points, f=fill, e=edge, w=lw):
        pts = [P(p) for p in points]
        if f:
            pygame.draw.polygon(surface, f, pts)
        if e:
            pygame.draw.polygon(surface, e, pts, w)

    def circ(x, y, r, f=fill, e=edge, w=lw):
        c = P((x, y))
        rad = max(1, round(r * k))
        if f:
            pygame.draw.circle(surface, f, c, rad)
        if e:
            pygame.draw.circle(surface, e, c, rad, w)

    def ell(x, y, rx, ry, f=fill, e=edge, w=lw):
        r = pygame.Rect(0, 0, max(1, round(2 * rx * k)), max(1, round(2 * ry * k)))
        r.center = (round(P((x, y))[0]), round(P((x, y))[1]))
        if f:
            pygame.draw.ellipse(surface, f, r)
        if e:
            pygame.draw.ellipse(surface, e, r, w)

    def line(points, color=detail, w=lw):
        pygame.draw.lines(surface, color, False, [P(p) for p in points], max(1, round(w)))

    def base(rx):
        ell(50, 78, rx - 6, 5)
        ell(50, 85, rx, 7)

    t = piece.piece_type
    rx = 28

    if t == 'pawn':
        rx = 21
        poly([(43, 50), (57, 50), (62, 80), (38, 80)])
        circ(50, 40, 13)
        ell(50, 53, 13, 4)

    elif t == 'rook':
        poly([(40, 40), (60, 40), (64, 80), (36, 80)])
        poly([(32, 42), (32, 22), (41, 22), (41, 30),
              (46, 30), (46, 22), (54, 22), (54, 30),
              (59, 30), (59, 22), (68, 22), (68, 42)])
        ell(50, 43, 16, 4)

    elif t == 'knight':
        rx = 25
        poly([(36, 80), (34, 60), (27, 54), (22, 46), (24, 39),
              (33, 34), (39, 26), (40, 14), (48, 24), (58, 26),
              (66, 36), (70, 52), (68, 80)])
        line([(48, 27), (58, 35), (62, 47), (62, 64)], w=max(1, round(1.5 * k)))
        circ(35, 38, 2.6, f=detail, e=None)
        circ(27, 45, 1.8, f=detail, e=None)

    elif t == 'bishop':
        poly([(43, 50), (57, 50), (63, 80), (37, 80)])
        poly([(50, 16), (61, 29), (66, 42), (60, 52),
              (40, 52), (34, 42), (39, 29)])
        circ(50, 15, 4.5)
        ell(50, 52, 15, 5)
        line([(53, 27), (44, 43)], w=max(2, round(2.5 * k)))

    elif t == 'queen':
        rx = 29
        poly([(40, 46), (60, 46), (68, 80), (32, 80)])
        poly([(34, 46), (28, 22), (38, 34), (44, 16), (50, 30),
              (56, 16), (62, 34), (72, 22), (66, 46)])
        for bx, by in [(28, 20), (44, 14), (56, 14), (72, 20)]:
            circ(bx, by, 4)
        ell(50, 47, 17, 5)
        circ(50, 65, 3, f=detail, e=None)

    elif t == 'king':
        rx = 29
        poly([(41, 50), (59, 50), (67, 80), (33, 80)])
        poly([(36, 50), (34, 34), (42, 25), (50, 31),
              (58, 25), (66, 34), (64, 50)])
        poly([(47, 6), (53, 6), (53, 12), (60, 12), (60, 18), (53, 18),
              (53, 26), (47, 26), (47, 18), (40, 18), (40, 12), (47, 12)])
        ell(50, 50, 18, 5)
        line([(50, 34), (50, 46)], w=max(1, round(1.5 * k)))

    base(rx)


def draw_board(screen, board, selected, legal_moves, last_move, current_player, game_status):
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

    # Рисуем фигуры вектором
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            piece = board[row][col]
            if piece:
                draw_piece(screen, row, col, piece, SQUARE_SIZE)

    pygame.draw.rect(screen, (40, 40, 40), (0, BOARD_PIXELS, WINDOW_WIDTH, 60))
    status_font = pygame.font.Font(None, 32)
    if game_status:
        status_text = status_font.render(game_status, True, (255, 200, 100))
    else:
        player_name = "Белые" if current_player == 'white' else "Чёрные"
        check_text = " (ШАХ!)" if is_in_check(board, current_player) else ""
        status_text = status_font.render(f"Ход: {player_name}{check_text}",
                                         True, (255, 255, 255) if current_player == 'white' else (200, 200, 200))
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
    en_passant_target = None

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
                            legal_moves = get_legal_moves(board, row, col, en_passant_target)
                        elif (row, col) in legal_moves:
                            new_en_passant = make_move(board, selected, (row, col), en_passant_target)
                            last_move = (selected, (row, col))
                            selected = None
                            legal_moves = []
                            en_passant_target = new_en_passant
                            current_player = 'black' if current_player == 'white' else 'white'

                            if not has_any_legal_moves(board, current_player, en_passant_target):
                                game_over = True
                                if is_in_check(board, current_player):
                                    winner = 'Чёрные' if current_player == 'white' else 'Белые'
                                    game_status = f"МАТ! Победили {winner}"
                                else:
                                    game_status = "ПАТ! Ничья"
                    else:
                        if piece and piece.color == current_player:
                            selected = (row, col)
                            legal_moves = get_legal_moves(board, row, col, en_passant_target)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    board = create_initial_board()
                    current_player = 'white'
                    selected = None
                    legal_moves = []
                    last_move = None
                    game_status = None
                    game_over = False
                    en_passant_target = None

        draw_board(screen, board, selected, legal_moves, last_move, current_player, game_status)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()