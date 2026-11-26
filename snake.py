import pygame
import sys
import random

pygame.init()

# Константы
CELL_SIZE = 25
GRID_W = 20
GRID_H = 24
HEADER_HEIGHT = 60
WIDTH = GRID_W * CELL_SIZE
HEIGHT = GRID_H * CELL_SIZE + HEADER_HEIGHT

# Цвета
BG = (30, 30, 40)
GRID_COLOR = (40, 40, 55)
SNAKE_HEAD = (80, 220, 100)
SNAKE_BODY = (50, 180, 70)
FOOD_COLOR = (230, 70, 70)
TEXT_COLOR = (240, 240, 240)
HEADER_BG = (50, 50, 65)

# Направления
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Змейка")
clock = pygame.time.Clock()


def spawn_food(snake):
    """Спавнит еду в случайной свободной клетке"""
    while True:
        pos = (random.randint(0, GRID_W - 1), random.randint(0, GRID_H - 1))
        if pos not in snake:
            return pos


def main():
    # Начальное состояние
    snake = [(GRID_W // 2, GRID_H // 2)]  # Список сегментов (голова — первый)
    direction = RIGHT
    next_direction = RIGHT
    food = spawn_food(snake)
    score = 0
    game_over = False
    move_timer = 0
    move_delay = 120  # мс между движениями (чем меньше — тем быстрее)
    
    font = pygame.font.Font(None, 36)
    big_font = pygame.font.Font(None, 72)
    small_font = pygame.font.Font(None, 28)
    
    running = True
    while running:
        dt = clock.tick(60)
        move_timer += dt
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if game_over:
                    if event.key == pygame.K_r:
                        snake = [(GRID_W // 2, GRID_H // 2)]
                        direction = RIGHT
                        next_direction = RIGHT
                        food = spawn_food(snake)
                        score = 0
                        game_over = False
                        move_delay = 120
                else:
                    if event.key == pygame.K_UP and direction != DOWN:
                        next_direction = UP
                    elif event.key == pygame.K_DOWN and direction != UP:
                        next_direction = DOWN
                    elif event.key == pygame.K_LEFT and direction != RIGHT:
                        next_direction = LEFT
                    elif event.key == pygame.K_RIGHT and direction != LEFT:
                        next_direction = RIGHT
        
        if not game_over and move_timer >= move_delay:
            move_timer = 0
            direction = next_direction
            
            # Новая позиция головы
            head_x, head_y = snake[0]
            dx, dy = direction
            new_head = (head_x + dx, head_y + dy)
            
            # Проверка столкновения со стеной
            if (new_head[0] < 0 or new_head[0] >= GRID_W or
                    new_head[1] < 0 or new_head[1] >= GRID_H):
                game_over = True
            # Проверка столкновения с собой
            elif new_head in snake:
                game_over = True
            else:
                snake.insert(0, new_head)
                # Еда
                if new_head == food:
                    score += 10
                    food = spawn_food(snake)
                    # Ускорение каждые 50 очков
                    if score % 50 == 0 and move_delay > 50:
                        move_delay -= 10
                else:
                    snake.pop()
        
        # Отрисовка
        screen.fill(BG)
        
        # Шапка
        pygame.draw.rect(screen, HEADER_BG, (0, 0, WIDTH, HEADER_HEIGHT))
        pygame.draw.line(screen, (80, 80, 100), (0, HEADER_HEIGHT - 1), (WIDTH, HEADER_HEIGHT - 1), 2)
        
        score_text = font.render(f"Счёт: {score}", True, TEXT_COLOR)
        screen.blit(score_text, (15, HEADER_HEIGHT // 2 - 18))
        
        length_text = font.render(f"Длина: {len(snake)}", True, TEXT_COLOR)
        screen.blit(length_text, (WIDTH - length_text.get_width() - 15, HEADER_HEIGHT // 2 - 18))
        
        # Игровое поле — сетка
        for x in range(GRID_W):
            for y in range(GRID_H):
                rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE + HEADER_HEIGHT,
                                   CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, GRID_COLOR, rect, 1)
        
        # Еда
        fx, fy = food
        food_rect = pygame.Rect(fx * CELL_SIZE + 3, fy * CELL_SIZE + HEADER_HEIGHT + 3,
                                CELL_SIZE - 6, CELL_SIZE - 6)
        pygame.draw.ellipse(screen, FOOD_COLOR, food_rect)
        pygame.draw.ellipse(screen, (180, 40, 40), food_rect, 2)
        
        # Змейка
        for i, (sx, sy) in enumerate(snake):
            rect = pygame.Rect(sx * CELL_SIZE + 1, sy * CELL_SIZE + HEADER_HEIGHT + 1,
                               CELL_SIZE - 2, CELL_SIZE - 2)
            color = SNAKE_HEAD if i == 0 else SNAKE_BODY
            pygame.draw.rect(screen, color, rect, border_radius=6)
            pygame.draw.rect(screen, (30, 100, 40), rect, 2, border_radius=6)
            
            # Глаза на голове
            if i == 0:
                cx, cy = rect.centerx, rect.centery
                dx, dy = direction
                # Смещение глаз в сторону движения
                eye_offset = 5
                eye_r = 3
                if dx == 0:  # вертикально
                    e1 = (cx - eye_offset, cy + dy * 3)
                    e2 = (cx + eye_offset, cy + dy * 3)
                else:  # горизонтально
                    e1 = (cx + dx * 3, cy - eye_offset)
                    e2 = (cx + dx * 3, cy + eye_offset)
                pygame.draw.circle(screen, (255, 255, 255), e1, eye_r)
                pygame.draw.circle(screen, (255, 255, 255), e2, eye_r)
                pygame.draw.circle(screen, (0, 0, 0), e1, 1)
                pygame.draw.circle(screen, (0, 0, 0), e2, 1)
        
        # Game over
        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT - HEADER_HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, HEADER_HEIGHT))
            
            text = big_font.render("GAME OVER", True, (255, 100, 100))
            text_rect = text.get_rect(center=(WIDTH // 2, HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT) // 2 - 40))
            screen.blit(text, text_rect)
            
            score_final = font.render(f"Счёт: {score}", True, TEXT_COLOR)
            screen.blit(score_final, score_final.get_rect(
                center=(WIDTH // 2, HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT) // 2 + 10)))
            
            hint = small_font.render("R — новая игра", True, (200, 200, 200))
            screen.blit(hint, hint.get_rect(
                center=(WIDTH // 2, HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT) // 2 + 50)))
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
