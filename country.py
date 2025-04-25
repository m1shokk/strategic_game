import pygame
import random
from map_gen import HexCell


class Country:
    # Цвета для стран (пастельные оттенки)
    COUNTRY_COLORS = [
        (255, 86, 86),    # Красный
        (255, 204, 55),   # Желтый
        (132, 200, 37),   # Зеленый
        (24, 117, 195),   # Синий
        (111, 75, 146)    # Фиолетовый
    ]

    def __init__(self, cells):
        self.color = random.choice(self.COUNTRY_COLORS)
        self.cells = self.initialize_country(cells)
        self.capital = self.cells[0]  # Первая клетка - столица
        self.capital.country = self  # Связываем клетку со страной
        
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
        """
        Проверяет, можно ли построить объект на клетке.
        Возвращает True, если клетка свободна.
        """
        # Проверяем, что клетка принадлежит стране
        if cell not in self.cells:
            return False
            
        # Запрещаем строительство на столице
        if cell == self.capital:
            return False
            
        # Проверяем наличие деревьев
        if any(tree.x == cell.center[0] and tree.y == cell.center[1] for tree in trees):
            return False
            
        # Проверяем наличие других объектов
        objects = self.units + self.cities + self.fortresses
        return not any(
            obj.x == cell.center[0] and obj.y == cell.center[1]
            for obj in objects
        )

    def initialize_country(self, all_cells):
        """
        Инициализирует территорию страны, начиная со случайной клетки
        и добавляя соседние клетки.
        """
        start_cell = random.choice(all_cells)
        occupied = {start_cell.id}
        country_cells = [start_cell]
        
        # Количество дополнительных клеток (2-4)
        num_additional_cells = random.randint(2, 4)
        
        for _ in range(num_additional_cells):
            # Находим всех доступных соседей последней добавленной клетки
            last_cell = country_cells[-1]
            neighbors = [
                cell for cell in all_cells
                if cell.id not in occupied and self._are_neighbors(last_cell, cell)
            ]
            
            if neighbors:
                new_cell = random.choice(neighbors)
                country_cells.append(new_cell)
                occupied.add(new_cell.id)
            else:
                # Если нет доступных соседей, начинаем заново
                return self.initialize_country(all_cells)
        
        return country_cells
    
    def _are_neighbors(self, cell1, cell2):
        """Проверяет, являются ли две клетки соседями"""
        q_diff = abs(cell1.q - cell2.q)
        r_diff = abs(cell1.r - cell2.r)
        return (q_diff == 1 and r_diff == 0) or (q_diff == 0 and r_diff == 1) or (q_diff == 1 and r_diff == 1)

    def draw(self, surface):
        """Отрисовывает страну и все её объекты на поверхности"""
        # Рисуем затемнение, если страна выделена
        if self.selected:
            self._draw_selection_overlay(surface)
            
        # Рисуем клетки страны
        for cell in self.cells:
            pygame.draw.polygon(surface, self.color, cell.points)
            pygame.draw.polygon(surface, (0, 0, 0), cell.points, 2)
            
        # Рисуем объекты страны
        self._draw_objects(surface)
        
        # Рисуем столицу
        capital_pos = (self.capital.center[0] - 30, self.capital.center[1] - 30)
        surface.blit(self.capital_icon, capital_pos)

    def _draw_selection_overlay(self, surface):
        """Отрисовывает выделение страны"""
        overlay = pygame.Surface((1920, 1080), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Полупрозрачный черный
        surface.blit(overlay, (0, 0))
        
        # Обводка выделенных клеток
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