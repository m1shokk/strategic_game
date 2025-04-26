import pygame
import random
import math
from tree_gen import Tree


class GameState:
    def __init__(self):
        self.current_turn = 1
        self.button_rect = pygame.Rect(1920 - 70, 1080 - 50, 50, 30)
        self.button_color = (100, 100, 100)
        self.button_hover_color = (150, 150, 150)
        self.button_text = "->"
        self.font = pygame.font.Font(None, 24)

    def draw(self, surface):
        # Рисуем кнопку
        mouse_pos = pygame.mouse.get_pos()
        button_color = self.button_hover_color if self.button_rect.collidepoint(mouse_pos) else self.button_color
        
        pygame.draw.rect(surface, button_color, self.button_rect)
        pygame.draw.rect(surface, (0, 0, 0), self.button_rect, 1)
        
        # Рисуем текст кнопки
        text_surface = self.font.render(self.button_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.button_rect.center)
        surface.blit(text_surface, text_rect)
        
        # Рисуем номер текущего хода
        turn_text = f"MOVE: {self.current_turn}"
        turn_surface = self.font.render(turn_text, True, (255, 255, 255))
        surface.blit(turn_surface, (20, 20))

    def handle_click(self, pos, cells, trees, capital_cell=None):
        if self.button_rect.collidepoint(pos):
            self.current_turn += 1
            self.propagate_trees(cells, trees, capital_cell)
            return True
        return False

    def propagate_trees(self, cells, trees, capital_cell=None):
        # Создаем множество занятых клеток
        occupied_cells = set()
        
        # Добавляем клетки с деревьями
        for cell in cells:
            if any(tree.x == cell.center[0] and tree.y == cell.center[1] for tree in trees):
                occupied_cells.add(cell.id)
        
        # Добавляем клетки с объектами страны (если есть)
        if capital_cell and hasattr(capital_cell, 'country'):
            country = capital_cell.country
            for unit in country.units:
                cell = self.find_cell_by_position(cells, unit.x, unit.y)
                if cell: occupied_cells.add(cell.id)
            for city in country.cities:
                cell = self.find_cell_by_position(cells, city.x, city.y)
                if cell: occupied_cells.add(cell.id)
            for fortress in country.fortresses:
                cell = self.find_cell_by_position(cells, fortress.x, fortress.y)
                if cell: occupied_cells.add(cell.id)
            # Добавляем саму столицу
            occupied_cells.add(capital_cell.id)

        # Создаем множество запрещенных клеток (только столица)
        forbidden_cells = set()
        if capital_cell:
            forbidden_cells.add(capital_cell.id)
        
        # Создаем список возможных новых позиций для деревьев
        new_positions = []
        
        # Для каждой занятой клетки проверяем соседей
        for cell in cells:
            if cell.id in occupied_cells:
                # Проверяем всех соседей
                for neighbor in cells:
                    if neighbor.id not in occupied_cells and neighbor.id not in forbidden_cells:
                        # Проверяем, являются ли клетки соседями
                        q_diff = abs(cell.q - neighbor.q)
                        r_diff = abs(cell.r - neighbor.r)
                        if (q_diff == 1 and r_diff == 0) or (q_diff == 0 and r_diff == 1) or (q_diff == 1 and r_diff == 1):
                            new_positions.append(neighbor)
        
        # Для каждой возможной новой позиции проверяем шанс 20%
        for position in new_positions:
            if random.random() < 0.2:  # 20% шанс
                trees.append(Tree(position.center[0], position.center[1], 50))

    def find_cell_by_position(self, cells, x, y):
        """Находит клетку по координатам точки"""
        for cell in cells:
            if self.point_in_hexagon((x, y), cell.points):
                return cell
        return None

    @staticmethod
    def point_in_hexagon(point, hexagon_points):
        """Проверяет, находится ли точка внутри шестиугольника"""
        x, y = point
        n = len(hexagon_points)
        inside = False
        p1x, p1y = hexagon_points[0]
        for i in range(1, n + 1):
            p2x, p2y = hexagon_points[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        return inside
    
    def handle_unit_movement(self, unit, target_cell, country, trees):
        if unit.has_moved:
            return False
        
        # Проверка соседства клеток
        if not self._are_neighbors(unit.cell, target_cell):
            return False
        
        # Движение внутри страны
        if target_cell in country.cells:
            if target_cell.unit or target_cell == country.capital:
                return False
            
            # Проверка на наличие построек
            for city in country.cities:
                if city.x == target_cell.center[0] and city.y == target_cell.center[1]:
                    return False
            for fortress in country.fortresses:
                if fortress.x == target_cell.center[0] and fortress.y == target_cell.center[1]:
                    return False
        
        # Обработка леса
        for tree in trees[:]:
            if tree.x == target_cell.center[0] and tree.y == target_cell.center[1]:
                trees.remove(tree)
                if target_cell in country.cells:  # Добавляем деньги только если лес в нашей стране
                    country.money += 2
                break
        
        # Перемещение
        unit.cell.unit = None
        unit.x, unit.y = target_cell.center
        unit.cell = target_cell
        target_cell.unit = unit
        unit.has_moved = True
        return True
        
        # В класс GameState добавим метод (перед handle_unit_movement)
    @staticmethod
    def _are_neighbors(cell1, cell2):
        """Проверяет, являются ли две клетки соседями"""
        q_diff = abs(cell1.q - cell2.q)
        r_diff = abs(cell1.r - cell2.r)
        return (q_diff == 1 and r_diff == 0) or (q_diff == 0 and r_diff == 1) or (q_diff == 1 and r_diff == 1)

