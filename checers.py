import pygame
import sys

# Инициализация
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
MOVE_HINT = (130, 151, 130)
CAPTURE_HINT = (220, 80, 80)
LAST_MOVE = (247, 236, 92)
BORDER_COLOR = (50, 50, 50)

WHITE_PIECE_FILL = (245, 235, 220)
WHITE_PIECE_EDGE = (60, 40, 20)
BLACK_PIECE_FILL = (60, 40, 30)
BLACK_PIECE_EDGE = (10, 10, 10)
KING_MARK = (220, 180, 60)

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Русские шашки")
clock = pygame.time.Clock()


class Piece:
    def __init__(self, color):
        self.color = color        # 'white' или 'black'
        self.is_king = False      # дамка


def create_initial_board():
    """Начальная расстановка: по 12 шашек на тёмных клетках"""
    board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    for row in range(3):                  # чёрные — верхние 3 ряда
        for col in range(BOARD_SIZE):
            if (row + col) % 2 == 1:
                board[row][col] = Piece('black')
    for row in range(5, 8):               # белые — нижние 3 ряда
        for col in range(BOARD_SIZE):
            if (row + col) % 2 == 1:
                board[row][col] = Piece('white')
    return board


def in_bounds(r, c):
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE


def get_captures_for_piece(board, row, col, piece, visited=None):
    """
    Возвращает все цепочки взятий, начинающиеся с этой шашки.
    Каждая цепочка — список клеток, куда шашка приземлится (включая промежуточные).
    """
    if visited is None:
        visited = set()
    visited.add((row, col))

    chains = []
    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    if piece.is_king:
        # Дамка: летит по диагонали, находит первого врага, и может сесть
        # на любую пустую клетку за ним (до края или до следующей фигуры).
        for dr, dc in directions:
            r, c = row + dr, col + dc
            enemy_found = None
            while in_bounds(r, c):
                target = board[r][c]
                if target is None:
                    if enemy_found is not None:
                        # Пробуем сесть сюда и продолжить цепочку
                        er, ec = enemy_found
                        # Симулируем ход: убираем врага и перемещаем шашку
                        board[r][c] = piece
                        board[row][col] = None
                        captured = board[er][ec]
                        board[er][ec] = None

                        sub_chains = get_captures_for_piece(board, r, c, piece, visited.copy())
                        if sub_chains:
                            for sc in sub_chains:
                                chains.append([(r, c)] + sc)
                        else:
                            chains.append([(r, c)])

                        # Откат
                        board[row][col] = piece
                        board[r][c] = None
                        board[er][ec] = captured
                    # Иначе — пустая клетка до врага, летим дальше
                elif target.color == piece.color:
                    break  # своя фигура — стоп
                else:
                    if enemy_found is not None:
                        break  # уже был враг в этом направлении — больше нельзя
                    enemy_found = (r, c)
                r += dr
                c += dc
    else:
        # Обычная шашка: бьёт в любом направлении (русские правила — и назад тоже)
        for dr, dc in directions:
            er, ec = row + dr, col + dc
            lr, lc = row + 2 * dr, col + 2 * dc
            if not in_bounds(lr, lc):
                continue
            enemy = board[er][ec]
            landing = board[lr][lc]
            if enemy and enemy.color != piece.color and landing is None and (er, ec) not in visited:
                # Симулируем
                board[lr][lc] = piece
                board[row][col] = None
                captured = board[er][ec]
                board[er][ec] = None

                sub_chains = get_captures_for_piece(board, lr, lc, piece, visited.copy())
                if sub_chains:
                    for sc in sub_chains:
                        chains.append([(lr, lc)] + sc)
                else:
                    chains.append([(lr, lc)])

                # Откат
                board[row][col] = piece
                board[lr][lc] = None
                board[er][ec] = captured

    return chains


def get_simple_moves(board, row, col, piece):
    """Тихие ходы (без взятия). Для дамки — на любое расстояние по диагонали."""
    moves = []
    if piece.is_king:
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            r, c = row + dr, col + dc
            while in_bounds(r, c) and board[r][c] is None:
                moves.append((r, c))
                r += dr
                c += dc
    else:
        direction = -1 if piece.color == 'white' else 1
        for dc in [-1, 1]:
            r, c = row + direction, col + dc
            if in_bounds(r, c) and board[r][c] is None:
                moves.append((r, c))
    return moves


def get_all_actions(board, color):
    """
    Возвращает (captures, simple_moves).
    captures: dict {(r,c): [список цепочек]} — для каждой шашки, которая может бить.
    simple_moves: dict {(r,c): [список клеток]} — тихие ходы (только если нет взятий вообще).
    """
    captures = {}
    simple = {}
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            p = board[r][c]
            if p and p.color == color:
                caps = get_captures_for_piece(board, r, c, p)
                if caps:
                    captures[(r, c)] = caps
                else:
                    mv = get_simple_moves(board, r, c, p)
                    if mv:
                        simple[(r, c)] = mv
    return captures, simple


def apply_capture_chain(board, start, chain):
    """
    Применяет цепочку взятий. Возвращает список съеденных фигур ( Piece )
    и список клеток, по которым прошла шашка (для подсветки).
    """
    piece = board[start[0]][start[1]]
    board[start[0]][start[1]] = None
    captured_pieces = []
    path = [start]
    cur = start
    for landing in chain:
        # Находим врага между cur и landing (ровно одна клетка по диагонали для обычной,
        # для дамки — первый враг на линии)
        dr = 1 if landing[0] > cur[0] else -1
        dc = 1 if landing[1] > cur[1] else -1
        r, c = cur[0] + dr, cur[1] + dc
        enemy_pos = None
        if piece.is_king:
            while in_bounds(r, c) and (r, c) != landing:
                if board[r][c] and board[r][c].color != piece.color:
                    enemy_pos = (r, c)
                    break
                r += dr
                c += dc
        else:
            enemy_pos = (r, c)

        if enemy_pos:
            captured_pieces.append((enemy_pos, board[enemy_pos[0]][enemy_pos[1]]))
            board[enemy_pos[0]][enemy_pos[1]] = None

        board[landing[0]][landing[1]] = piece
        path.append(landing)
        cur = landing

    # Превращение в дамку: если дошла до последнего ряда
    final = chain[-1]
    if not piece.is_king:
        if (piece.color == 'white' and final[0] == 0) or (piece.color == 'black' and final[0] == 7):
            piece.is_king = True

    return path


def apply_simple_move(board, start, end):
    piece = board[start[0]][start[1]]
    board[end[0]][end[1]] = piece
    board[start[0]][start[1]] = None
    if not piece.is_king:
        if (piece.color == 'white' and end[0] == 0) or (piece.color == 'black' and end[0] == 7):
            piece.is_king = True
    return [start, end]


def draw_piece(surface, row, col, piece, sq):
    """Рисуем шашку кругами. Дамка — с золотой короной-звёздочкой."""
    cx = col * sq + sq // 2
    cy = row * sq + sq // 2
    r_outer = int(sq * 0.38)
    r_inner = int(sq * 0.28)

    if piece.color == 'white':
        fill, edge = WHITE_PIECE_FILL, WHITE_PIECE_EDGE
    else:
        fill, edge = BLACK_PIECE_FILL, BLACK_PIECE_EDGE

    # Тень
    pygame.draw.circle(surface, (0, 0, 0, 80), (cx + 2, cy + 3), r_outer)
    # Основа
    pygame.draw.circle(surface, edge, (cx, cy), r_outer)
    pygame.draw.circle(surface, fill, (cx, cy), r_outer - 3)
    # Внутренний круг
    pygame.draw.circle(surface, edge, (cx, cy), r_inner, 2)

    if piece.is_king:
        # Звёздочка-корона
        import math
        n = 8
        pts = []
        for i in range(n * 2):
            ang = math.pi * i / n - math.pi / 2
            rad = r_inner * 0.9 if i % 2 == 0 else r_inner * 0.45
            pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
        pygame.draw.polygon(surface, KING_MARK, pts)
        pygame.draw.polygon(surface, edge, pts, 2)


def draw_board(screen, board, selected, highlights, last_path, current_player, game_status, must_capture_from):
    screen.fill(BORDER_COLOR)

    # Клетки
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            x, y = col * SQUARE_SIZE, row * SQUARE_SIZE
            color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
            if last_path and (row, col) in last_path:
                color = LAST_MOVE
            pygame.draw.rect(screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))

    # Подсветка клетки, которая обязана бить
    if must_capture_from:
        for (mr, mc) in must_capture_from:
            pygame.draw.rect(screen, (255, 180, 60),
                             (mc * SQUARE_SIZE + 4, mr * SQUARE_SIZE + 4,
                              SQUARE_SIZE - 8, SQUARE_SIZE - 8), 4)

    # Выбранная шашка
    if selected:
        sr, sc = selected
        pygame.draw.rect(screen, SELECTED,
                         (sc * SQUARE_SIZE + 3, sr * SQUARE_SIZE + 3,
                          SQUARE_SIZE - 6, SQUARE_SIZE - 6), 4)

    # Подсветка возможных ходов/взятий
    for (mr, mc), kind in highlights.items():
        cx = mc * SQUARE_SIZE + SQUARE_SIZE // 2
        cy = mr * SQUARE_SIZE + SQUARE_SIZE // 2
        if kind == 'capture':
            pygame.draw.rect(screen, CAPTURE_HINT,
                             (mc * SQUARE_SIZE + 10, mr * SQUARE_SIZE + 10,
                              SQUARE_SIZE - 20, SQUARE_SIZE - 20), 4)
        else:
            pygame.draw.circle(screen, MOVE_HINT, (cx, cy), 14)

    # Фигуры
    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            p = board[row][col]
            if p:
                draw_piece(screen, row, col, p, SQUARE_SIZE)

    # Нижняя панель
    pygame.draw.rect(screen, (40, 40, 40), (0, BOARD_PIXELS, WINDOW_WIDTH, 60))
    font = pygame.font.Font(None, 34)
    if game_status:
        txt = font.render(game_status, True, (255, 200, 100))
    else:
        name = "Белые" if current_player == 'white' else "Чёрные"
        fill = WHITE_PIECE_FILL if current_player == 'white' else (200, 200, 200)
        txt = font.render(f"Ход: {name}", True, fill)
    rect = txt.get_rect(center=(WINDOW_WIDTH // 2, BOARD_PIXELS + 30))
    screen.blit(txt, rect)


def get_square(pos):
    x, y = pos
    if y >= BOARD_PIXELS:
        return None
    col, row = x // SQUARE_SIZE, y // SQUARE_SIZE
    if 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE:
        return row, col
    return None


def main():
    board = create_initial_board()
    current_player = 'white'
    selected = None
    highlights = {}          # {(r,c): 'move'|'capture'}
    current_chain_options = []   # цепочки для выбранной шашки (если она в процессе боя)
    last_path = None
    game_status = None
    game_over = False

    running = True
    while running:
        # Считаем доступные действия текущего игрока
        if not game_over:
            captures, simple = get_all_actions(board, current_player)
            must_capture_from = list(captures.keys()) if captures else []
            if not captures and not simple:
                game_over = True
                winner = "Чёрные" if current_player == 'white' else "Белые"
                game_status = f"Нет ходов. Победили {winner}!"
        else:
            captures, simple = {}, {}
            must_capture_from = []

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and not game_over and event.button == 1:
                sq = get_square(event.pos)
                if sq is None:
                    continue
                row, col = sq

                # Если шашка в процессе цепочки боя — можно двигать только её
                if current_chain_options:
                    # Ищем среди цепочек ту, что заканчивается на (row,col)
                    for chain in current_chain_options:
                        if chain[-1] == (row, col):
                            path = apply_capture_chain(board, selected, chain)
                            last_path = path
                            # После боя: проверяем, сменился ли ход.
                            # В русских шашках смена хода происходит, когда цепочка закончилась.
                            # Мы уже закончили цепочку → ход переходит.
                            current_player = 'black' if current_player == 'white' else 'white'
                            selected = None
                            highlights = {}
                            current_chain_options = []
                            break
                    continue

                piece = board[row][col]

                # Клик по своей шашке
                if piece and piece.color == current_player:
                    # Если есть обязательные взятия — можно выбрать только шашку, которая может бить
                    if must_capture_from and (row, col) not in captures:
                        continue
                    selected = (row, col)
                    highlights = {}
                    if (row, col) in captures:
                        # Собираем все конечные клетки всех цепочек
                        seen = set()
                        for chain in captures[(row, col)]:
                            end = chain[-1]
                            if end not in seen:
                                highlights[end] = 'capture'
                                seen.add(end)
                        current_chain_options = captures[(row, col)]
                    else:
                        for cell in simple.get((row, col), []):
                            highlights[cell] = 'move'
                        current_chain_options = []
                    continue

                # Клик по клетке назначения
                if selected and (row, col) in highlights:
                    if highlights[(row, col)] == 'capture':
                        # Выбираем цепочку, ведущую в эту клетку.
                        # Если несколько цепочек ведут в одну клетку — правила русских шашек:
                        # нужно выбрать максимальную по длине (взять максимум шашек).
                        candidates = [ch for ch in current_chain_options if ch[-1] == (row, col)]
                        candidates.sort(key=len, reverse=True)
                        chosen = candidates[0]
                        path = apply_capture_chain(board, selected, chosen)
                        last_path = path
                        current_player = 'black' if current_player == 'white' else 'white'
                    else:
                        path = apply_simple_move(board, selected, (row, col))
                        last_path = path
                        current_player = 'black' if current_player == 'white' else 'white'
                    selected = None
                    highlights = {}
                    current_chain_options = []

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    board = create_initial_board()
                    current_player = 'white'
                    selected = None
                    highlights = {}
                    current_chain_options = []
                    last_path = None
                    game_status = None
                    game_over = False

        draw_board(screen, board, selected, highlights, last_path,
                   current_player, game_status, must_capture_from if not game_over else [])
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()