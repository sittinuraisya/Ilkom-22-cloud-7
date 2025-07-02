import pygame
import random
import sys

# Inisialisasi pygame
pygame.init()

# Ukuran layar
WIDTH = 600
HEIGHT = 400
GRID = 20

# Warna
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED   = (255, 0, 0)
BLUE  = (0, 0, 255)

# Setup layar dan clock
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("🐍 Game Ular Sederhana")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 24)

# Fungsi untuk menggambar grid
def draw_grid():
    for x in range(0, WIDTH, GRID):
        pygame.draw.line(screen, (40, 40, 40), (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT, GRID):
        pygame.draw.line(screen, (40, 40, 40), (0, y), (WIDTH, y))

# Kelas Ular
class Snake:
    def __init__(self):
        self.body = [(5, 5), (4, 5), (3, 5)]
        self.direction = (1, 0)
        self.grow = False

    def move(self):
        head = self.body[0]
        dx, dy = self.direction
        new_head = (head[0] + dx, head[1] + dy)
        if self.grow:
            self.body = [new_head] + self.body
            self.grow = False
        else:
            self.body = [new_head] + self.body[:-1]

    def change_direction(self, dx, dy):
        if (dx, dy) == (-self.direction[0], -self.direction[1]):
            return
        self.direction = (dx, dy)

    def eat(self):
        self.grow = True

    def draw(self):
        for segment in self.body:
            pygame.draw.rect(screen, GREEN, (segment[0]*GRID, segment[1]*GRID, GRID, GRID))

    def collide_self(self):
        return self.body[0] in self.body[1:]

    def get_head(self):
        return self.body[0]

# Kelas Makanan
class Food:
    def __init__(self):
        self.position = self.random_position()

    def random_position(self):
        return (random.randint(0, (WIDTH - GRID) // GRID),
                random.randint(0, (HEIGHT - GRID) // GRID))

    def draw(self):
        pygame.draw.rect(screen, RED, (self.position[0]*GRID, self.position[1]*GRID, GRID, GRID))

# Fungsi Game Over
def game_over_screen(score):
    screen.fill(BLACK)
    text1 = font.render(f"Game Over! Skor kamu: {score}", True, WHITE)
    text2 = font.render("Tekan [R] untuk restart atau [Q] untuk keluar", True, WHITE)
    screen.blit(text1, (WIDTH//2 - text1.get_width()//2, HEIGHT//2 - 30))
    screen.blit(text2, (WIDTH//2 - text2.get_width()//2, HEIGHT//2 + 10))
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True
                elif event.key == pygame.K_q:
                    pygame.quit(); sys.exit()

# Fungsi utama game
def main():
    snake = Snake()
    food = Food()
    score = 0
    speed = 10

    while True:
        clock.tick(speed)
        screen.fill(BLACK)
        draw_grid()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    snake.change_direction(0, -1)
                elif event.key == pygame.K_DOWN:
                    snake.change_direction(0, 1)
                elif event.key == pygame.K_LEFT:
                    snake.change_direction(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    snake.change_direction(1, 0)

        snake.move()
        if snake.get_head() == food.position:
            snake.eat()
            score += 1
            speed = min(20, speed + 0.1)
            food = Food()

        # Cek tabrak dinding
        head_x, head_y = snake.get_head()
        if head_x < 0 or head_x >= WIDTH//GRID or head_y < 0 or head_y >= HEIGHT//GRID:
            if not game_over_screen(score):
                break
            return main()

        # Cek tabrak badan sendiri
        if snake.collide_self():
            if not game_over_screen(score):
                break
            return main()

        snake.draw()
        food.draw()

        # Skor tampil
        score_text = font.render(f"Skor: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        pygame.display.update()

if __name__ == "__main__":
    main()
