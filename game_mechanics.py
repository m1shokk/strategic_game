import pygame
import random
import math
from tree_gen import Tree


class GameState:
    def __init__(self, num_players=4):
        self.current_turn = 1
        self.num_players = num_players
        self.current_player = 0  # 0-3 для 4 игроков
        self.players_ready = [False] * num_players
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
        
        # Рисуем номер текущего хода и игрока
        turn_text = f"MOVE: {self.current_turn} | Player: {self.current_player + 1}"
        turn_surface = self.font.render(turn_text, True, (255, 255, 255))
        surface.blit(turn_surface, (20, 20))

    def handle_click(self, pos, cells, trees, countries):
        if self.button_rect.collidepoint(pos):
            # Помечаем текущего игрока как готового
            self.players_ready[self.current_player] = True
            
            # Проверяем, все ли игроки готовы
            if all(self.players_ready):
                self.current_turn += 1
                self.players_ready = [False] * self.num_players
                
                # Распространяем деревья для всех стран
                for country in countries:
                    self.propagate_trees(cells, trees, country.capital)
                
                # Переключаем на следующего игрока
                self.current_player = (self.current_player + 1) % self.num_players
                return True
            else:
                # Переключаем на следующего игрока
                self.current_player = (self.current_player + 1) % self.num_players
                return False
        return False

    def propagate_trees(self, cells, trees, capital_cell=None):
        # Создаем множество занятых клеток (включая все объекты)
        occupied_cells = set()
        
        # Добавляем клетки с деревьями
        for cell in cells:
            if any(tree.x == cell.center[0] and tree.y == cell.center[1] for tree in trees):
                occupied_cells.add(cell.id)
        
        # Добавляем клетки с любыми объектами всех стран
        for cell in cells:
            if hasattr(cell, 'country') and cell.country:
                # Проверяем юниты, города, крепости и столицу
                country = cell.country
                if any(unit.x == cell.center[0] and unit.y == cell.center[1] for unit in country.units):
                    occupied_cells.add(cell.id)
                if any(city.x == cell.center[0] and city.y == cell.center[1] for city in country.cities):
                    occupied_cells.add(cell.id)
                if any(fortress.x == cell.center[0] and fortress.y == cell.center[1] for fortress in country.fortresses):
                    occupied_cells.add(cell.id)
                if cell == country.capital:
                    occupied_cells.add(cell.id)
        
        # Создаем список возможных новых позиций для деревьев
        new_positions = []
        
        # Для каждого дерева проверяем строго соседние клетки
        for tree in trees[:]:  # Используем копию списка
            tree_cell = self.find_cell_by_position(cells, tree.x, tree.y)
            if not tree_cell:
                continue
                
            for cell in cells:
                # Проверяем строгое соседство (только 1 клетка в разнице координат)
                q_diff = abs(tree_cell.q - cell.q)
                r_diff = abs(tree_cell.r - cell.r)
                is_neighbor = (q_diff == 1 and r_diff == 0) or (q_diff == 0 and r_diff == 1) or (q_diff == 1 and r_diff == 1)
                
                if is_neighbor and cell.id not in occupied_cells:
                    new_positions.append(cell)
        
        # Для каждой возможной новой позиции проверяем шанс 7%
        for position in new_positions:
            if random.random() < 0.07:  # 7% шанс вместо 20%
                # Проверяем, что на этой клетке ещё нет дерева
                if not any(tree.x == position.center[0] and tree.y == position.center[1] for tree in trees):
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
        
        # Проверка соседства клеток (строго 1 клетка разницы)
        q_diff = abs(unit.cell.q - target_cell.q)
        r_diff = abs(unit.cell.r - target_cell.r)
        if not ((q_diff == 1 and r_diff == 0) or (q_diff == 0 and r_diff == 1) or (q_diff == 1 and r_diff == 1)):
            return False
        
        # Проверка на другие юниты (везде)
        if target_cell.unit:
            return False
        
        # Обработка леса (вырубка)
        for tree in trees[:]:
            if tree.x == target_cell.center[0] and tree.y == target_cell.center[1]:
                trees.remove(tree)
                if target_cell in country.cells:  # Деньги только за вырубку в своей стране
                    country.money += 2
                    if hasattr(country, 'economy'):
                        country.economy.balance += 2  # Немедленное добавление денег
                break
        
        # Движение внутри страны
        if target_cell in country.cells:
            # Нельзя перемещаться на столицу и постройки
            if (target_cell == country.capital or
                any(city.x == target_cell.center[0] and city.y == target_cell.center[1] for city in country.cities) or
                any(fortress.x == target_cell.center[0] and fortress.y == target_cell.center[1] for fortress in country.fortresses)):
                return False
        
        # Захват нейтральной/вражеской клетки
        if target_cell not in country.cells:
            # Если у клетки был предыдущий владелец, удаляем из его территории
            if hasattr(target_cell, 'country') and target_cell.country:
                target_cell.country.cells.remove(target_cell)
            
            # Устанавливаем нового владельца
            target_cell.country = country
            country.cells.append(target_cell)
        
        # Перемещение юнита
        unit.cell.unit = None
        unit.x, unit.y = target_cell.center
        unit.cell = target_cell
        target_cell.unit = unit
        unit.has_moved = True
        return True
        
    @staticmethod
    def _are_neighbors(cell1, cell2):
        """Проверяет, являются ли две клетки строго соседями (1 клетка разницы)"""
        q_diff = abs(cell1.q - cell2.q)
        r_diff = abs(cell1.r - cell2.r)
        return (q_diff == 1 and r_diff == 0) or (q_diff == 0 and r_diff == 1) or (q_diff == 1 and r_diff == 1)