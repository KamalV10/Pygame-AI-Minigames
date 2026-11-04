import pygame
import sys

pygame.init()

# Константы
WIDTH = 400
HEIGHT = 600
PADDLE_WIDTH = 75
PADDLE_HEIGHT = 10
BALL_SIZE = 10
PADDLE_SPEED = 5
BALL_SPEED_X = 3
BALL_SPEED_Y = 3

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 100, 255)

# Настройка окна
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Пинг-понг")
clock = pygame.time.Clock()

# Платформы
bottom_paddle = pygame.Rect(WIDTH // 2 - PADDLE_WIDTH // 2, HEIGHT - 30, PADDLE_WIDTH, PADDLE_HEIGHT)
top_paddle = pygame.Rect(WIDTH // 2 - PADDLE_WIDTH // 2, 20, PADDLE_WIDTH, PADDLE_HEIGHT)

# Мяч
ball = pygame.Rect(WIDTH // 2 - BALL_SIZE // 2, HEIGHT // 2 - BALL_SIZE // 2, BALL_SIZE, BALL_SIZE)
ball_speed_x = BALL_SPEED_X
ball_speed_y = BALL_SPEED_Y

# Счёт
score_top = 0
score_bottom = 0
font = pygame.font.Font(None, 36)

def reset_ball():
    """Сбрасывает мяч в центр"""
    global ball_speed_x, ball_speed_y
    ball.x = WIDTH // 2 - BALL_SIZE // 2
    ball.y = HEIGHT // 2 - BALL_SIZE // 2
    ball_speed_x = BALL_SPEED_X * (1 if pygame.time.get_ticks() % 2 == 0 else -1)
    ball_speed_y = BALL_SPEED_Y * (1 if pygame.time.get_ticks() % 3 == 0 else -1)

def main():
    global ball_speed_x, ball_speed_y, score_top, score_bottom
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_ball()
                    score_top = 0
                    score_bottom = 0
        
        # Управление нижней платформой (A/D)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a] and bottom_paddle.left > 0:
            bottom_paddle.x -= PADDLE_SPEED
        if keys[pygame.K_d] and bottom_paddle.right < WIDTH:
            bottom_paddle.x += PADDLE_SPEED
        
        # Управление верхней платформой (стрелки)
        if keys[pygame.K_LEFT] and top_paddle.left > 0:
            top_paddle.x -= PADDLE_SPEED
        if keys[pygame.K_RIGHT] and top_paddle.right < WIDTH:
            top_paddle.x += PADDLE_SPEED
        
        # Движение мяча
        ball.x += ball_speed_x
        ball.y += ball_speed_y
        
        # Отскок от левой и правой стен
        if ball.left <= 0 or ball.right >= WIDTH:
            ball_speed_x = -ball_speed_x
        
        # Отскок от верхней платформы
        if ball.top <= top_paddle.bottom and ball.colliderect(top_paddle):
            ball_speed_y = -ball_speed_y
            ball.y = top_paddle.bottom
        
        # Отскок от нижней платформы
        if ball.bottom >= bottom_paddle.top and ball.colliderect(bottom_paddle):
            ball_speed_y = -ball_speed_y
            ball.y = bottom_paddle.top - BALL_SIZE
        
        # Голы
        if ball.top <= 0:
            score_bottom += 1
            reset_ball()
        elif ball.bottom >= HEIGHT:
            score_top += 1
            reset_ball()
        
        # Отрисовка
        screen.fill(BLACK)
        
        # Платформы
        pygame.draw.rect(screen, BLUE, bottom_paddle)
        pygame.draw.rect(screen, RED, top_paddle)
        
        # Мяч
        pygame.draw.ellipse(screen, WHITE, ball)
        
        # Счёт
        score_text = font.render(f"{score_top} : {score_bottom}", True, WHITE)
        score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(score_text, score_rect)
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()