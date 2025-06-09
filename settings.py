import pygame
import sys
import json
import subprocess

pygame.init()

WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Settings")
clock = pygame.time.Clock()

BG_COLOR = (28, 32, 40)
TITLE_COLOR = (220, 240, 255)
LABEL_COLOR = (180, 200, 255)
BTN_COLOR = (60, 70, 100)
BTN_HOVER = (100, 120, 180)
BTN_TEXT = (255, 255, 255)

font_title = pygame.font.Font(None, 64)
font_label = pygame.font.Font(None, 36)
font_btn = pygame.font.Font(None, 36)

# Настройки (загрузка из файла)
def load_settings():
    try:
        with open("settings.json", "r") as f:
            data = json.load(f)
            return data.get("num_players", 4), data.get("map_size_idx", 1)
    except Exception:
        return 4, 1

def save_settings(num_players, map_size_idx):
    with open("settings.json", "w") as f:
        json.dump({"num_players": num_players, "map_size_idx": map_size_idx}, f)

num_players, map_size_idx = load_settings()
map_sizes = ["Small", "Medium", "Large"]

# Кнопки: (текст, rect)
btn_back = pygame.Rect(WIDTH//2 - 80, HEIGHT - 70, 160, 50)
btn_minus = pygame.Rect(270, 120, 40, 40)
btn_plus = pygame.Rect(370, 120, 40, 40)
btn_left = pygame.Rect(270, 200, 40, 40)
btn_right = pygame.Rect(370, 200, 40, 40)

def draw_settings():
    screen.fill(BG_COLOR)
    # Title
    title = font_title.render("Settings", True, TITLE_COLOR)
    title_rect = title.get_rect(center=(WIDTH//2, 50))
    screen.blit(title, title_rect)
    # Number of Players
    label1 = font_label.render("Number of Players:", True, LABEL_COLOR)
    screen.blit(label1, (80, 125))
    pygame.draw.rect(screen, BTN_COLOR, btn_minus, border_radius=8)
    pygame.draw.rect(screen, BTN_COLOR, btn_plus, border_radius=8)
    minus_text = font_btn.render("-", True, BTN_TEXT)
    plus_text = font_btn.render("+", True, BTN_TEXT)
    screen.blit(minus_text, minus_text.get_rect(center=btn_minus.center))
    screen.blit(plus_text, plus_text.get_rect(center=btn_plus.center))
    value1 = font_label.render(str(num_players), True, BTN_TEXT)
    screen.blit(value1, (330, 125))
    # Map Size
    label2 = font_label.render("Map Size:", True, LABEL_COLOR)
    screen.blit(label2, (80, 205))
    pygame.draw.rect(screen, BTN_COLOR, btn_left, border_radius=8)
    pygame.draw.rect(screen, BTN_COLOR, btn_right, border_radius=8)
    left_text = font_btn.render("<", True, BTN_TEXT)
    right_text = font_btn.render(">", True, BTN_TEXT)
    screen.blit(left_text, left_text.get_rect(center=btn_left.center))
    screen.blit(right_text, right_text.get_rect(center=btn_right.center))
    value2 = font_label.render(map_sizes[map_size_idx], True, BTN_TEXT)
    screen.blit(value2, (330, 205))
    # Back button
    mouse_pos = pygame.mouse.get_pos()
    color = BTN_HOVER if btn_back.collidepoint(mouse_pos) else BTN_COLOR
    pygame.draw.rect(screen, color, btn_back, border_radius=12)
    pygame.draw.rect(screen, (180, 200, 255), btn_back, 2, border_radius=12)
    back_text = font_btn.render("Back", True, BTN_TEXT)
    screen.blit(back_text, back_text.get_rect(center=btn_back.center))
    pygame.display.flip()

def run_settings():
    global num_players, map_size_idx
    running = True
    while running:
        draw_settings()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if btn_back.collidepoint(event.pos):
                    save_settings(num_players, map_size_idx)
                    pygame.quit()
                    subprocess.Popen([sys.executable, "menu.py"])
                    sys.exit()
                elif btn_minus.collidepoint(event.pos):
                    if num_players > 2:
                        num_players -= 1
                        save_settings(num_players, map_size_idx)
                elif btn_plus.collidepoint(event.pos):
                    if num_players < 4:
                        num_players += 1
                        save_settings(num_players, map_size_idx)
                elif btn_left.collidepoint(event.pos):
                    if map_size_idx > 0:
                        map_size_idx -= 1
                        save_settings(num_players, map_size_idx)
                elif btn_right.collidepoint(event.pos):
                    if map_size_idx < len(map_sizes) - 1:
                        map_size_idx += 1
                        save_settings(num_players, map_size_idx)
        clock.tick(60)
    pygame.quit()

if __name__ == "__main__":
    run_settings() 