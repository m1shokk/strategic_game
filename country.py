import pygame
import random
from map_gen import HexCell


class Country:
    # Цвета для стран (пастельные оттенки) - расширенный список
    COUNTRY_COLORS = [
        (255, 86, 86),    # Красный
        (255, 204, 55),   # Желтый
        (132, 200, 37),   # Зеленый
        (24, 117, 195),   # Синий
        (111, 75, 146),   # Фиолетовый
        (255, 165, 0),    # Оранжевый
        (0, 191, 255),    # Голубой
        (147, 112, 219)   # Фиолетовый средний
    ]
    
    # Статические поля для отслеживания занятых цветов и клеток
    used_colors = set()
    occupied_cells = set()

    def __init__(self, cells):
        # Выбираем уникальный цвет
        available_colors = [c for c in self.COUNTRY_COLORS if c not in Country.used_colors]
        if not available_colors:
            # Если цвета закончились, очищаем использованные (на крайний случай)
            Country.used_colors = set()
            available_colors = self.COUNTRY_COLORS
            
        self.color = random.choice(available_colors)
        Country.used_colors.add(self.color)
        
        # Инициализируем территорию страны, избегая занятых клеток
        self.cells = self.initialize_country(cells)
        self.capital = self.cells[0]  # Первая клетка - столица
        self.capital.country = self  # Связываем клетку со страной
        self.money = 10  # Добавляем начальный баланс
        
        # Загружаем иконку столицы
        self.capital_icon = self._load_capital_icon()
        
        self.selected = False  # Флаг выделения страны
        self.units = []        # Список юнитов страны
        self.cities = []       # Список городов страны
        self.fortresses = []   # Список крепостей страны

    def _load_capital_icon(self):
        """Загружает и масштабирует иконку столицы"""
        try:
            icon = pygame.image.load('./images/capital.png')
            return pygame.transform.scale(icon, (60, 60))
        except:
            # Создаем простую замену, если изображение не найдено
            surf = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 215, 0), (30, 30), 30)
            pygame.draw.circle(surf, (255, 255, 0), (30, 30), 20)
            return surf

    def is_cell_free(self, cell, trees):
        """Проверяет, можно ли построить объект на клетке"""
        if cell not in self.cells:
            return False
            
        if cell == self.capital:
            return False
            
        if any(tree.x == cell.center[0] and tree.y == cell.center[1] for tree in trees):
            return False
            
        objects = self.units + self.cities + self.fortresses
        return not any(
            obj.x == cell.center[0] and obj.y == cell.center[1]
            for obj in objects
        )

    def initialize_country(self, all_cells):
        """Инициализирует территорию страны, избегая занятых клеток"""
        # Выбираем стартовую клетку из свободных
        free_cells = [cell for cell in all_cells if cell.id not in Country.occupied_cells]
        if not free_cells:
            free_cells = all_cells  # На крайний случай
            
        start_cell = random.choice(free_cells)
        occupied = {start_cell.id}
        country_cells = [start_cell]
        
        # Количество дополнительных клеток (2-4)
        num_additional_cells = random.randint(2, 4)
        
        for _ in range(num_additional_cells):
            last_cell = country_cells[-1]
            neighbors = [
                cell for cell in all_cells
                if (cell.id not in Country.occupied_cells and 
                    cell.id not in occupied and 
                    self._are_neighbors(last_cell, cell))
            ]
            
            if neighbors:
                new_cell = random.choice(neighbors)
                country_cells.append(new_cell)
                occupied.add(new_cell.id)
            else:
                break  # Если нет свободных соседей
        
        # Помечаем клетки как занятые
        for cell in country_cells:
            Country.occupied_cells.add(cell.id)
            
        return country_cells
    
    def _are_neighbors(self, cell1, cell2):
        """Проверяет, являются ли две клетки соседями"""
        q_diff = abs(cell1.q - cell2.q)
        r_diff = abs(cell1.r - cell2.r)
        return (q_diff == 1 and r_diff == 0) or (q_diff == 0 and r_diff == 1) or (q_diff == 1 and r_diff == 1)

    def draw(self, surface):
        """Отрисовывает страну и все её объекты"""
        if hasattr(self, 'player_index'):
            # Рисуем номер игрока в столице
            font = pygame.font.Font(None, 24)
            text = font.render(str(self.player_index + 1), True, (0, 0, 0))
            text_rect = text.get_rect(center=(self.capital.center[0], self.capital.center[1] - 10))
            surface.blit(text, text_rect)
            
        if self.selected:
            self._draw_selection_overlay(surface)
            
        # Рисуем клетки страны
        for cell in self.cells:
            pygame.draw.polygon(surface, self.color, cell.points)
            pygame.draw.polygon(surface, (0, 0, 0), cell.points, 2)
        
        # Рисуем объекты страны
        for city in self.cities:
            surface.blit(city.image, (city.x - 25, city.y - 25))
        for fortress in self.fortresses:
            surface.blit(fortress.image, (fortress.x - 25, fortress.y - 25))
        for unit in self.units:
            if not hasattr(self, 'dragging_unit') or unit != self.dragging_unit:
                surface.blit(unit.image, (unit.x - 20, unit.y - 20))
                if hasattr(self, 'selected_unit') and unit == self.selected_unit:
                    pygame.draw.circle(surface, (255, 255, 0), 
                          (self.selected_unit.x, self.selected_unit.y), 25, 2)
        
        # Рисуем столицу
        capital_pos = (self.capital.center[0] - 30, self.capital.center[1] - 30)
        surface.blit(self.capital_icon, capital_pos)

    def _draw_selection_overlay(self, surface):
        """Отрисовывает выделение страны"""
        overlay = pygame.Surface((1920, 1080), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        surface.blit(overlay, (0, 0))
        
        for cell in self.cells:
            pygame.draw.polygon(surface, (255, 255, 255), cell.points, 4)

    def _draw_objects(self, surface):
        """Отрисовывает все объекты страны"""
        for city in self.cities:
            surface.blit(city.image, (city.x - 25, city.y - 25))
        for fortress in self.fortresses:
            surface.blit(fortress.image, (fortress.x - 25, fortress.y - 25))
        for unit in self.units:
            surface.blit(unit.image, (unit.x - 20, unit.y - 20))