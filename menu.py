import pygame
import sys
import subprocess

pygame.init()

WIDTH, HEIGHT = 900, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hex Strategy Game - Menu")
clock = pygame.time.Clock()

BG_COLOR = (28, 32, 40)
TITLE_COLOR = (220, 240, 255)
SUBTITLE_COLOR = (120, 140, 180)
BUTTON_COLOR = (60, 70, 100)
BUTTON_HOVER = (100, 120, 180)
BUTTON_TEXT = (255, 255, 255)

font_title = pygame.font.Font(None, 90)
font_sub = pygame.font.Font(None, 32)
font_btn = pygame.font.Font(None, 48)
font_cred = pygame.font.Font(None, 28)

# Кнопки: (текст, y-координата, действие)
buttons = [
    ("New Game", 270, "new_game"),
    ("Settings", 350, "settings"),
    ("Exit", 430, "exit")
]

button_rects = []

for i, (text, y, _) in enumerate(buttons):
    rect = pygame.Rect(WIDTH//2 - 160, y, 320, 60)
    button_rects.append(rect)

def draw_menu():
    screen.fill(BG_COLOR)
    # Title
    title = font_title.render("Hex Strategy Game", True, TITLE_COLOR)
    title_rect = title.get_rect(center=(WIDTH//2, 120))
    screen.blit(title, title_rect)
    # Subtitle
    subtitle = font_cred.render("by Ch0kz Games", True, SUBTITLE_COLOR)
    subtitle_rect = subtitle.get_rect(center=(WIDTH//2, HEIGHT - 40))
    screen.blit(subtitle, subtitle_rect)
    # Buttons
    mouse_pos = pygame.mouse.get_pos()
    for i, (text, y, _) in enumerate(buttons):
        rect = button_rects[i]
        hovered = rect.collidepoint(mouse_pos)
        color = BUTTON_HOVER if hovered else BUTTON_COLOR
        pygame.draw.rect(screen, color, rect, border_radius=16)
        pygame.draw.rect(screen, (180, 200, 255), rect, 2, border_radius=16)
        btn_text = font_btn.render(text, True, BUTTON_TEXT)
        btn_rect = btn_text.get_rect(center=rect.center)
        screen.blit(btn_text, btn_rect)
    pygame.display.flip()

def run_menu():
    while True:
        draw_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for i, rect in enumerate(button_rects):
                    if rect.collidepoint(event.pos):
                        action = buttons[i][2]
                        if action == "new_game":
                            pygame.quit()
                            subprocess.Popen([sys.executable, "main.py"])
                            sys.exit()
                        elif action == "settings":
                            pygame.quit()
                            subprocess.Popen([sys.executable, "settings.py"])
                            sys.exit()
                        elif action == "exit":
                            pygame.quit()
                            sys.exit()
        clock.tick(60)

if __name__ == "__main__":
    run_menu() 