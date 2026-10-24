import pygame
import sys

pygame.init()

BOARD_SIZE = 8
SQUARE_SIZE = 80
BOARD_PIXELS = BOARD_SIZE * SQUARE_SIZE
WINDOW_WIDTH = BOARD_PIXELS
WINDOW_HEIGHT = BOARD_PIXELS + 60

LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
SELECTED = (106, 170, 100)
MOVE_HINT = (130, 151, 130)
CAPTURE_HINT = (220, 80, 80)
LAST_MOVE = (247, 236, 92)
BORDER_COLOR = (50, 50, 50)
MUST_CAPTURE_BG = (255, 200, 100)

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
    for r in range(3):
        for c in range(BOARD_SIZE):
            if (r + c) % 2 == 1:
                board[r][c] = Piece('black')
    for r in range(5, 8):
        for c in range(BOARD_SIZE):
            if (r + c) % 2 == 1:
                board[r][c] = Piece('white')
    return board


def in_bounds(r, c):
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE


def find_capture_chains(board, r, c, piece, visited=None, current_chain_landings=None, current_captured=None):
    if visited is None:
        visited = set()
    if current_chain_landings is None:
        current_chain_landings = []
    if current_captured is None:
        current_captured = []

    visited.add((r, c))
    results = []

    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    if piece.is_king:
        for dr, dc in directions:
            enemy_r, enemy_c = None, None
            step_r, step_c = r + dr, c + dc
            
            while in_bounds(step_r, step_c):
                target = board[step_r][step_c]
                if target:
                    if target.color != piece.color and (step_r, step_c) not in visited:
                        enemy_r, enemy_c = step_r, step_c
                    break
                step_r += dr
                step_c += dc
            
            if enemy_r is not None:
                land_r, land_c = enemy_r + dr, enemy_c + dc
                while in_bounds(land_r, land_c):
                    if board[land_r][land_c] is None:
                        original_target = board[enemy_r][enemy_c]
                        board[enemy_r][enemy_c] = None
                        board[land_r][land_c] = piece
                        board[r][c] = None

                        sub_results = find_capture_chains(
                            board, land_r, land_c, piece, 
                            visited.copy(), 
                            current_chain_landings + [(land_r, land_c)],
                            current_captured + [(enemy_r, enemy_c)]
                        )
                        
                        if sub_results:
                            results.extend(sub_results)
                        else:
                            results.append((current_chain_landings + [(land_r, land_c)], 
                                            current_captured + [(enemy_r, enemy_c)]))

                        board[r][c] = piece
                        board[land_r][land_c] = None
                        board[enemy_r][enemy_c] = original_target
                    else:
                        break
                    land_r += dr
                    land_c += dc
    else:
        for dr, dc in directions:
            mid_r, mid_c = r + dr, c + dc
            land_r, land_c = r + 2*dr, c + 2*dc
            
            if in_bounds(land_r, land_c):
                mid_piece = board[mid_r][mid_c]
                land_piece = board[land_r][land_c]
                
                if (mid_piece and mid_piece.color != piece.color and 
                    land_piece is None and 
                    (mid_r, mid_c) not in visited):
                    
                    original_mid = board[mid_r][mid_c]
                    board[mid_r][mid_c] = None
                    board[land_r][land_c] = piece
                    board[r][c] = None
                    
                    sub_results = find_capture_chains(
                        board, land_r, land_c, piece,
                        visited.copy(),
                        current_chain_landings + [(land_r, land_c)],
                        current_captured + [(mid_r, mid_c)]
                    )
                    
                    if sub_results:
                        results.extend(sub_results)
                    else:
                        results.append((current_chain_landings + [(land_r, land_c)],
                                        current_captured + [(mid_r, mid_c)]))
                    
                    board[r][c] = piece
                    board[land_r][land_c] = None
                    board[mid_r][mid_c] = original_mid

    return results


def get_simple_moves_for_piece(board, r, c, piece):
    moves = []
    if piece.is_king:
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nr, nc = r + dr, c + dc
            while in_bounds(nr, nc):
                if board[nr][nc] is None:
                    moves.append((nr, nc))
                else:
                    break
                nr += dr
                nc += dc
    else:
        direction = -1 if piece.color == 'white' else 1
        for dc in [-1, 1]:
            nr, nc = r + direction, c + dc
            if in_bounds(nr, nc) and board[nr][nc] is None:
                moves.append((nr, nc))
    return moves


def apply_move(board, start, end_landings, captured_coords):
    """Применяет ход (тихий или с взятием)"""
    piece = board[start[0]][start[1]]
    board[start[0]][start[1]] = None
    
    final_pos = start
    if end_landings:
        # Перемещаем фигуру по цепочке
        for i, pos in enumerate(end_landings):
            board[pos[0]][pos[1]] = piece
            # Очищаем предыдущую позицию (кроме первой итерации)
            if i > 0:
                prev_pos = end_landings[i-1]
                board[prev_pos[0]][prev_pos[1]] = None
            final_pos = pos
        
        # Удаляем съеденные фигуры
        for cr, cc in captured_coords:
            board[cr][cc] = None

    # Превращение в дамку
    if not piece.is_king:
        if (piece.color == 'white' and final_pos[0] == 0) or \
           (piece.color == 'black' and final_pos[0] == 7):
            piece.is_king = True
            
    return final_pos


def draw_piece(surface, row, col, piece, sq):
    cx = col * sq + sq // 2
    cy = row * sq + sq // 2
    r_outer = int(sq * 0.38)
    r_inner = int(sq * 0.28)

    if piece.color == 'white':
        fill, edge = WHITE_PIECE_FILL, WHITE_PIECE_EDGE
    else:
        fill, edge = BLACK_PIECE_FILL, BLACK_PIECE_EDGE

    pygame.draw.circle(surface, (0, 0, 0, 80), (cx + 2, cy + 3), r_outer)
    pygame.draw.circle(surface, edge, (cx, cy), r_outer)
    pygame.draw.circle(surface, fill, (cx, cy), r_outer - 3)
    pygame.draw.circle(surface, edge, (cx, cy), r_inner, 2)

    if piece.is_king:
        import math
        n = 8
        pts = []
        for i in range(n * 2):
            ang = math.pi * i / n - math.pi / 2
            rad = r_inner * 0.9 if i % 2 == 0 else r_inner * 0.45
            pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
        pygame.draw.polygon(surface, KING_MARK, pts)
        pygame.draw.polygon(surface, edge, pts, 2)


def draw_board(screen, board, selected, highlights, last_path, current_player, game_status, must_capture_pieces):
    screen.fill(BORDER_COLOR)

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            x, y = col * SQUARE_SIZE, row * SQUARE_SIZE
            color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
            
            if last_path and (row, col) in last_path:
                color = LAST_MOVE
            
            if must_capture_pieces and (row, col) in must_capture_pieces:
                pygame.draw.rect(screen, MUST_CAPTURE_BG, (x+2, y+2, SQUARE_SIZE-4, SQUARE_SIZE-4), 3)

            pygame.draw.rect(screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))

    if selected:
        sr, sc = selected
        pygame.draw.rect(screen, SELECTED, (sc * SQUARE_SIZE + 3, sr * SQUARE_SIZE + 3, SQUARE_SIZE - 6, SQUARE_SIZE - 6), 4)

    for (mr, mc), kind in highlights.items():
        cx = mc * SQUARE_SIZE + SQUARE_SIZE // 2
        cy = mr * SQUARE_SIZE + SQUARE_SIZE // 2
        if kind == 'capture':
            pygame.draw.rect(screen, CAPTURE_HINT, (mc * SQUARE_SIZE + 10, mr * SQUARE_SIZE + 10, SQUARE_SIZE - 20, SQUARE_SIZE - 20), 4)
        else:
            pygame.draw.circle(screen, MOVE_HINT, (cx, cy), 14)

    for row in range(BOARD_SIZE):
        for col in range(BOARD_SIZE):
            p = board[row][col]
            if p:
                draw_piece(screen, row, col, p, SQUARE_SIZE)

    pygame.draw.rect(screen, (40, 40, 40), (0, BOARD_PIXELS, WINDOW_WIDTH, 60))
    font = pygame.font.Font(None, 34)
    if game_status:
        txt = font.render(game_status, True, (255, 200, 100))
    else:
        name = "Белые" if current_player == 'white' else "Чёрные"
        fill = WHITE_PIECE_FILL if current_player == 'white' else (200, 200, 200)
        check_text = " (Бей!)" if must_capture_pieces else ""
        txt = font.render(f"Ход: {name}{check_text}", True, fill)
        
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
    highlights = {} 
    available_actions = []
    last_path = None
    game_status = None
    game_over = False
    must_capture_set = set()

    running = True
    while running:
        if not game_over:
            caps = []
            simples = []
            
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    p = board[r][c]
                    if p and p.color == current_player:
                        found_caps = find_capture_chains(board, r, c, p)
                        if found_caps:
                            for chain, captured in found_caps:
                                caps.append(((r, c), chain, captured))
                        else:
                            found_simples = get_simple_moves_for_piece(board, r, c, p)
                            for m in found_simples:
                                simples.append(((r, c), m))
            
            if caps:
                must_capture_set = {start for start, _, _ in caps}
            else:
                must_capture_set = set()
                
            if not caps and not simples:
                game_over = True
                winner = "Чёрные" if current_player == 'white' else "Белые"
                game_status = f"Нет ходов. Победили {winner}!"

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and not game_over and event.button == 1:
                sq = get_square(event.pos)
                if sq is None:
                    continue
                row, col = sq
                piece = board[row][col]

                if piece and piece.color == current_player:
                    if must_capture_set and (row, col) not in must_capture_set:
                        continue
                    
                    selected = (row, col)
                    highlights = {}
                    available_actions = []
                    
                    local_caps = find_capture_chains(board, row, col, piece)
                    if local_caps:
                        for chain_landings, captured_coords in local_caps:
                            final_cell = chain_landings[-1]
                            highlights[final_cell] = 'capture'
                            available_actions.append({
                                'type': 'capture',
                                'end_landings': chain_landings,
                                'captured': captured_coords,
                                'target': final_cell
                            })
                    else:
                        if not must_capture_set:
                            simple_moves = get_simple_moves_for_piece(board, row, col, piece)
                            for m in simple_moves:
                                highlights[m] = 'move'
                                available_actions.append({
                                    'type': 'simple',
                                    'end_landings': [m],  # ИСПРАВЛЕНО: передаём целевую клетку
                                    'captured': [],
                                    'target': m
                                })

                elif selected and (row, col) in highlights:
                    action = next(a for a in available_actions if a['target'] == (row, col))
                    
                    start_pos = selected
                    end_landings = action['end_landings']
                    captured_coords = action['captured']
                    
                    final_pos = apply_move(board, start_pos, end_landings, captured_coords)
                    
                    path = [start_pos] + end_landings
                    last_path = path
                    
                    current_player = 'black' if current_player == 'white' else 'white'
                    selected = None
                    highlights = {}
                    available_actions = []

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    board = create_initial_board()
                    current_player = 'white'
                    selected = None
                    highlights = {}
                    available_actions = []
                    last_path = None
                    game_status = None
                    game_over = False
                    must_capture_set = set()

        draw_board(screen, board, selected, highlights, last_path, current_player, game_status, must_capture_set)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()