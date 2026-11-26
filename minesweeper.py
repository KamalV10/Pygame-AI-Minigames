import pygame
import sys
import random
import time

pygame.init()

# Константы
GRID_SIZE = 10
CELL_SIZE = 50
MINE_COUNT = 15
BORDER = 100  # место под счёт и кнопки
WIDTH = GRID_SIZE * CELL_SIZE
HEIGHT = GRID_SIZE * CELL_SIZE + BORDER

# Цвета
BG = (200, 200, 200)
CELL_CLOSED = (180, 180, 200)
CELL_OPEN = (220, 220, 230)
CELL_MINE = (220, 80, 80)
CELL_FLAG = (255, 200, 100)
TEXT_COLOR = (30, 30, 30)
BORDER_COLOR = (80, 80, 80)
BUTTON_COLOR = (100, 150, 200)
BUTTON_HOVER = (130, 180, 230)

# Цвета цифр (классические)
NUM_COLORS = {
    1: (0, 0, 255),
    2: (0, 128, 0),
    3: (255, 0, 0),
    4: (0, 0, 128),
    5: (128, 0, 0),
    6: (0, 128, 128),
    7: (0, 0, 0),
    8: (128, 128, 128),
}

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Сапёр")
clock = pygame.time.Clock()


class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.is_mine = False
        self.is_open = False
        self.is_flagged = False
        self.neighbors_count = 0


def create_board():
    return [[Cell(r, c) for c in range(GRID_SIZE)] for r in range(GRID_SIZE)]


def place_mines(board, exclude_r, exclude_c):
    """Размещает мины, исключая клетку первого клика и её соседей"""
    excluded = set()
    for dr in [-1, 0, 1]:
        for dc in [-1, 1, 1]:
            nr, nc = exclude_r + dr, exclude_c + dc
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                excluded.add((nr, nc))
    
    all_cells = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)
                 if (r, c) not in excluded]
    mines = random.sample(all_cells, min(MINE_COUNT, len(all_cells)))
    
    for r, c in mines:
        board[r][c].is_mine = True


def count_neighbors(board):
    """Считает мины вокруг каждой клетки"""
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if board[r][c].is_mine:
                continue
            count = 0
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                        if board[nr][nc].is_mine:
                            count += 1
            board[r][c].neighbors_count = count


def open_cell(board, r, c):
    """Открывает клетку с рекурсивным раскрытием пустых"""
    if not (0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE):
        return
    cell = board[r][c]
    if cell.is_open or cell.is_flagged:
        return
    cell.is_open = True
    if cell.neighbors_count == 0 and not cell.is_mine:
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                open_cell(board, r + dr, c + dc)


def check_win(board):
    """Проверяет, открыты ли все безопасные клетки"""
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            cell = board[r][c]
            if not cell.is_mine and not cell.is_open:
                return False
    return True


def draw_cell(screen, cell, x, y, font):
    """Рисует одну клетку"""
    rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
    
    if cell.is_open:
        if cell.is_mine:
            pygame.draw.rect(screen, CELL_MINE, rect)
            # Рисуем мину
            cx, cy = x + CELL_SIZE // 2, y + CELL_SIZE // 2
            pygame.draw.circle(screen, (20, 20, 20), (cx, cy), CELL_SIZE // 4)
            # Лучи
            for angle in [0, 45, 90, 135]:
                import math
                rad = math.radians(angle)
                x1 = cx + int((CELL_SIZE // 3) * math.cos(rad))
                y1 = cy + int((CELL_SIZE // 3) * math.sin(rad))
                x2 = cx - int((CELL_SIZE // 3) * math.cos(rad))
                y2 = cy - int((CELL_SIZE // 3) * math.sin(rad))
                pygame.draw.line(screen, (20, 20, 20), (x1, y1), (x2, y2), 2)
        else:
            pygame.draw.rect(screen, CELL_OPEN, rect)
            if cell.neighbors_count > 0:
                text = font.render(str(cell.neighbors_count), True,
                                   NUM_COLORS.get(cell.neighbors_count, TEXT_COLOR))
                text_rect = text.get_rect(center=rect.center)
                screen.blit(text, text_rect)
    else:
        color = CELL_FLAG if cell.is_flagged else CELL_CLOSED
        pygame.draw.rect(screen, color, rect)
        if cell.is_flagged:
            # Рисуем флаг
            cx, cy = x + CELL_SIZE // 2, y + CELL_SIZE // 2
            # Древко
            pygame.draw.line(screen, (60, 40, 20),
                             (cx - 2, cy - 12), (cx - 2, cy + 12), 2)
            # Флажок
            pygame.draw.polygon(screen, (220, 40, 40),
                                [(cx - 2, cy - 12), (cx + 10, cy - 6), (cx - 2, cy)])
            # Основание
            pygame.draw.line(screen, (60, 40, 20),
                             (cx - 8, cy + 12), (cx + 4, cy + 12), 2)
    
    pygame.draw.rect(screen, BORDER_COLOR, rect, 1)


def draw_header(screen, font, flags_left, game_status, start_time):
    """Рисует верхнюю панель со счётом и таймером"""
    header_rect = pygame.Rect(0, 0, WIDTH, BORDER)
    pygame.draw.rect(screen, BG, header_rect)
    pygame.draw.line(screen, BORDER_COLOR, (0, BORDER - 1), (WIDTH, BORDER - 1), 2)
    
    # Счётчик флагов (мины)
    mines_text = font.render(f"💣 {flags_left}", True, TEXT_COLOR)
    screen.blit(mines_text, (15, BORDER // 2 - 15))
    
    # Статус / смайлик
    if game_status == 'lost':
        emoji = "💀"
    elif game_status == 'won':
        emoji = "🏆"
    else:
        emoji = "🙂"
    emoji_text = font.render(emoji, True, TEXT_COLOR)
    emoji_rect = emoji_text.get_rect(center=(WIDTH // 2, BORDER // 2))
    screen.blit(emoji_text, emoji_rect)
    
    # Таймер
    elapsed = int(time.time() - start_time) if start_time else 0
    time_text = font.render(f"⏱ {elapsed}", True, TEXT_COLOR)
    time_rect = time_text.get_rect(right=WIDTH - 15, centery=BORDER // 2)
    screen.blit(time_text, time_rect)


def main():
    board = create_board()
    mines_placed = False
    game_status = None  # None, 'won', 'lost'
    start_time = None
    flags_left = MINE_COUNT
    
    # Шрифт для цифр
    num_font = pygame.font.Font(None, 36)
    header_font = pygame.font.Font(None, 32)
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN and game_status is None:
                mx, my = event.pos
                if my < BORDER:
                    continue
                col = mx // CELL_SIZE
                row = (my - BORDER) // CELL_SIZE
                
                if not (0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE):
                    continue
                
                # Первый клик — размещаем мины
                if not mines_placed:
                    place_mines(board, row, col)
                    count_neighbors(board)
                    mines_placed = True
                    start_time = time.time()
                
                cell = board[row][col]
                
                if event.button == 1:  # ЛКМ — открыть
                    if not cell.is_flagged:
                        open_cell(board, row, col)
                        if cell.is_mine:
                            game_status = 'lost'
                            # Открываем все мины
                            for r in range(GRID_SIZE):
                                for c in range(GRID_SIZE):
                                    if board[r][c].is_mine:
                                        board[r][c].is_open = True
                        elif check_win(board):
                            game_status = 'won'
                
                elif event.button == 3:  # ПКМ — флаг
                    if not cell.is_open:
                        if cell.is_flagged:
                            cell.is_flagged = False
                            flags_left += 1
                        else:
                            if flags_left > 0:
                                cell.is_flagged = True
                                flags_left -= 1
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    board = create_board()
                    mines_placed = False
                    game_status = None
                    start_time = None
                    flags_left = MINE_COUNT
        
        # Отрисовка
        screen.fill(BG)
        draw_header(screen, header_font, flags_left, game_status, start_time)
        
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                x = c * CELL_SIZE
                y = r * CELL_SIZE + BORDER
                draw_cell(screen, board[r][c], x, y, num_font)
        
        # Оверлей при конце игры
        if game_status:
            overlay = pygame.Surface((WIDTH, HEIGHT - BORDER))
            overlay.set_alpha(150)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, BORDER))
            
            big_font = pygame.font.Font(None, 72)
            if game_status == 'lost':
                text = big_font.render("БУМ!", True, (255, 100, 100))
            else:
                text = big_font.render("ПОБЕДА!", True, (100, 255, 100))
            text_rect = text.get_rect(center=(WIDTH // 2, BORDER + (HEIGHT - BORDER) // 2 - 30))
            screen.blit(text, text_rect)
            
            hint_font = pygame.font.Font(None, 28)
            hint = hint_font.render("Нажмите R для новой игры", True, (255, 255, 255))
            hint_rect = hint.get_rect(center=(WIDTH // 2, BORDER + (HEIGHT - BORDER) // 2 + 30))
            screen.blit(hint, hint_rect)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
