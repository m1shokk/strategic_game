import pygame
import random
import math

# --- Настройки ---
WIDTH, HEIGHT = 1920, 1080
HEX_SIZE = 40  # Радиус шестиугольника
NUM_CELLS = 100

BG_COLOR = (30, 30, 80)          # Нормальный цвет моря (сине-фиолетовый)
CELL_COLOR = (100, 100, 100)      # Серая заливка клеток
HOVER_COLOR = (160, 160, 160)     # Подсветка при наведении
BORDER_COLOR = (255, 255, 255)    # Белая обводка клеток

# --- Инициализация Pygame ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Стратегия: Генератор Провинций v6 (Исправленная версия)")
clock = pygame.time.Clock()

HEX_WIDTH = HEX_SIZE * 2
HEX_HEIGHT = math.sqrt(3) * HEX_SIZE
HORIZ_SPACING = HEX_WIDTH * 0.75
VERT_SPACING = HEX_HEIGHT

# --- Класс клетки ---
class HexCell:
    def __init__(self, q, r, cell_id):
        self.q = q  # ось q
        self.r = r  # ось r
        self.id = cell_id
        self.center = self.hex_to_pixel(q, r)
        self.points = self.calculate_corners(self.center)

    def hex_to_pixel(self, q, r):
        x = WIDTH // 2 + HORIZ_SPACING * q
        y = HEIGHT // 2 + VERT_SPACING * (r + 0.5 * (q % 2))
        return (int(x), int(y))

    def calculate_corners(self, center):
        corners = []
        for i in range(6):
            angle_deg = 60 * i
            angle_rad = math.radians(angle_deg)
            x = center[0] + HEX_SIZE * math.cos(angle_rad)
            y = center[1] + HEX_SIZE * math.sin(angle_rad)
            corners.append((x, y))
        return corners

    def draw(self, surface, is_hovered):
        color = HOVER_COLOR if is_hovered else CELL_COLOR
        pygame.draw.polygon(surface, color, self.points)
        pygame.draw.polygon(surface, BORDER_COLOR, self.points, 2)

# --- Генерация карты с ограничением по экрану ---
def generate_hex_cells():
    occupied = set()
    cells = []
    cell_id = 0

    q, r = 0, 0
    occupied.add((q, r))
    cells.append(HexCell(q, r, cell_id))
    cell_id += 1

    directions = [(1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)]

    # Определим максимальные координаты для клеток, чтобы они не выходили за пределы экрана
    max_q = WIDTH // HEX_WIDTH
    max_r = HEIGHT // HEX_HEIGHT

    while len(cells) < NUM_CELLS:
        base_cell = random.choice(cells)
        random.shuffle(directions)

        for dq, dr in directions:
            nq, nr = base_cell.q + dq, base_cell.r + dr

            # Получаем центр клетки
            center = HexCell(nq, nr, 0).hex_to_pixel(nq, nr)
            # Получаем углы клетки
            points = HexCell(nq, nr, 0).calculate_corners(center)

            # Проверяем, что все углы клетки находятся внутри экрана
            if all(0 <= x <= WIDTH and 0 <= y <= HEIGHT for x, y in points):
                if (nq, nr) not in occupied:
                    neighbors = 0
                    for ndq, ndr in directions:
                        if (nq + ndq, nr + ndr) in occupied:
                            neighbors += 1
                    if neighbors >= 1:
                        occupied.add((nq, nr))
                        cells.append(HexCell(nq, nr, cell_id))
                        cell_id += 1
                        break

    return cells

# --- Проверка наведения курсора ---
def point_in_hexagon(point, hex_points):
    x, y = point
    inside = False
    j = len(hex_points) - 1
    for i in range(len(hex_points)):
        xi, yi = hex_points[i]
        xj, yj = hex_points[j]
        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-10) + xi):
            inside = not inside
        j = i
    return inside
