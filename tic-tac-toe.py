import pygame
import sys

# Инициализация Pygame
pygame.init()

# Константы
WINDOW_SIZE = 600
GRID_SIZE = 3
CELL_SIZE = WINDOW_SIZE // GRID_SIZE
LINE_WIDTH = 5
CIRCLE_RADIUS = CELL_SIZE // 3
CROSS_WIDTH = 10

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (200, 200, 200)
LIGHT_GRAY = (240, 240, 240)

# Настройка окна
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("Крестики-нолики")
clock = pygame.time.Clock()

def draw_grid():
    """Рисует сетку игрового поля"""
    for i in range(1, GRID_SIZE):
        # Вертикальные линии
        pygame.draw.line(screen, BLACK, 
                        (i * CELL_SIZE, 0), 
                        (i * CELL_SIZE, WINDOW_SIZE), 
                        LINE_WIDTH)
        # Горизонтальные линии
        pygame.draw.line(screen, BLACK, 
                        (0, i * CELL_SIZE), 
                        (WINDOW_SIZE, i * CELL_SIZE), 
                        LINE_WIDTH)

def draw_x(row, col):
    """Рисует крестик в указанной ячейке"""
    x_start = col * CELL_SIZE + 20
    y_start = row * CELL_SIZE + 20
    x_end = (col + 1) * CELL_SIZE - 20
    y_end = (row + 1) * CELL_SIZE - 20
    
    pygame.draw.line(screen, RED, (x_start, y_start), (x_end, y_end), CROSS_WIDTH)
    pygame.draw.line(screen, RED, (x_start, y_end), (x_end, y_start), CROSS_WIDTH)

def draw_o(row, col):
    """Рисует нолик в указанной ячейке"""
    center_x = col * CELL_SIZE + CELL_SIZE // 2
    center_y = row * CELL_SIZE + CELL_SIZE // 2
    
    pygame.draw.circle(screen, BLUE, (center_x, center_y), CIRCLE_RADIUS, CROSS_WIDTH)

def check_winner(board):
    """Проверяет наличие победителя"""
    # Проверка строк
    for row in board:
        if row[0] == row[1] == row[2] and row[0] != '':
            return row[0]
    
    # Проверка столбцов
    for col in range(GRID_SIZE):
        if board[0][col] == board[1][col] == board[2][col] and board[0][col] != '':
            return board[0][col]
    
    # Проверка диагоналей
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] != '':
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] != '':
        return board[0][2]
    
    return None

def is_board_full(board):
    """Проверяет, заполнено ли поле"""
    for row in board:
        for cell in row:
            if cell == '':
                return False
    return True

def get_cell_from_pos(pos):
    """Определяет ячейку по позиции мыши"""
    x, y = pos
    col = x // CELL_SIZE
    row = y // CELL_SIZE
    return row, col

def reset_game():
    """Сбрасывает игру"""
    board = [['' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    current_player = 'X'
    game_over = False
    winner = None
    return board, current_player, game_over, winner

def draw_text(text, size, color, x, y):
    """Рисует текст на экране"""
    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect(center=(x, y))
    screen.blit(text_surface, text_rect)

def main():
    # Начальное состояние игры
    board, current_player, game_over, winner = reset_game()
    
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                if event.button == 1:  # Левая кнопка мыши
                    row, col = get_cell_from_pos(event.pos)
                    
                    if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
                        if board[row][col] == '':
                            board[row][col] = current_player
                            
                            # Проверяем победителя
                            winner = check_winner(board)
                            if winner:
                                game_over = True
                            elif is_board_full(board):
                                game_over = True
                                winner = 'Ничья'
                            else:
                                # Меняем игрока
                                current_player = 'O' if current_player == 'X' else 'X'
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    # Перезапуск игры
                    board, current_player, game_over, winner = reset_game()
        
        # Отрисовка
        screen.fill(LIGHT_GRAY)
        
        # Рисуем сетку
        draw_grid()
        
        # Рисуем символы
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if board[row][col] == 'X':
                    draw_x(row, col)
                elif board[row][col] == 'O':
                    draw_o(row, col)
        
        # Отображаем статус игры
        if game_over:
            if winner == 'Ничья':
                draw_text("НИЧЬЯ!", 80, BLACK, WINDOW_SIZE // 2, WINDOW_SIZE // 2)
            else:
                color = RED if winner == 'X' else BLUE
                draw_text(f"ПОБЕДИЛ {winner}!", 80, color, WINDOW_SIZE // 2, WINDOW_SIZE // 2)
            
            draw_text("Нажмите R для новой игры", 40, GRAY, WINDOW_SIZE // 2, WINDOW_SIZE - 50)
        else:
            color = RED if current_player == 'X' else BLUE
            draw_text(f"Ходит: {current_player}", 50, color, WINDOW_SIZE // 2, 30)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()