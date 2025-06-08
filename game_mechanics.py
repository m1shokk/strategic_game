import pygame
import random
import math
from tree import Tree
from country import Country  # Добавьте в начало файла


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

    def propagate_trees(self, cells, trees, country):
        # Собираем центры всех занятых клеток (деревья + постройки)
        occupied_centers = set()
        
        # Добавляем центры всех деревьев
        for tree in trees:
            occupied_centers.add((tree.x, tree.y))
        
        # Добавляем центры всех объектов (юниты, города, крепости, столицы)
        for cell in cells:
            if hasattr(cell, 'country') and cell.country:
                # Проверяем, есть ли на клетке юнит, город, крепость или столица
                has_unit = any(unit.x == cell.center[0] and unit.y == cell.center[1] for unit in cell.country.units)
                has_city = any(city.x == cell.center[0] and city.y == cell.center[1] for city in cell.country.cities)
                has_fortress = any(fortress.x == cell.center[0] and fortress.y == cell.center[1] for fortress in cell.country.fortresses)
                is_capital = cell == cell.country.capital
                
                if has_unit or has_city or has_fortress or is_capital:
                    occupied_centers.add((cell.center[0], cell.center[1]))
        
        new_trees = []
        for tree in trees[:]:
            tree_cell = self.find_cell_by_position(cells, tree.x, tree.y)
            if not tree_cell:
                continue
                
            for cell in cells:
                # Проверяем соседство
                if not self._are_neighbors(tree_cell, cell):
                    continue
                    
                # Проверяем, что клетка свободна (нет деревьев и построек)
                if (cell.center[0], cell.center[1]) in occupied_centers:
                    continue
                    
                # 3% шанс на рост нового дерева
                if random.random() < 0.03:
                    new_trees.append(Tree(cell.center[0], cell.center[1], tree.size))
                    occupied_centers.add((cell.center[0], cell.center[1]))  # Помечаем как занятую
        
        trees.extend(new_trees)

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
        q_diff = abs(unit.cell.q - target_cell.q)
        r_diff = abs(unit.cell.r - target_cell.r)
        if not ((q_diff == 1 and r_diff == 0) or (q_diff == 0 and r_diff == 1) or (q_diff == 1 and r_diff == 1)):
            return False
        
        # Вырубка дерева (теперь работает на любой клетке)
        for tree in trees[:]:
            if tree.x == target_cell.center[0] and tree.y == target_cell.center[1]:
                trees.remove(tree)
                # Бонус только если это своя территория
                if target_cell in country.cells:
                    country.money += 2
                    if hasattr(country, 'economy'):
                        country.economy.balance += 2
                break
        
        # Остальная логика перемещения остается без изменений
        if hasattr(target_cell, 'country') and target_cell.country and target_cell.country != country:
            return False  # Атака обрабатывается отдельно
        
        if target_cell not in country.cells:
            if hasattr(target_cell, 'country') and target_cell.country:
                old_owner = target_cell.country
                old_owner.remove_unit_at_cell(target_cell)
                old_owner.remove_city_at_cell(target_cell)
                old_owner.remove_fortress_at_cell(target_cell)
                old_owner.cells.remove(target_cell)
                if hasattr(old_owner, 'economy'):
                    old_owner.economy.calculate_income()
            
            target_cell.country = country
            country.cells.append(target_cell)
            if hasattr(country, 'economy'):
                country.economy.calculate_income()
        elif target_cell in country.cells:
            if (target_cell == country.capital or
                any(city.x == target_cell.center[0] and city.y == target_cell.center[1] for city in country.cities) or
                any(fortress.x == target_cell.center[0] and fortress.y == target_cell.center[1] for fortress in country.fortresses)):
                return False
        
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
    
    def check_attack(self, attacking_units, target_cell, attacking_country):
        """Проверяет возможность атаки и возвращает результат"""
        # Проверяем тип цели
        is_capital = target_cell == target_cell.country.capital
        has_fortress = any(f.x == target_cell.center[0] and f.y == target_cell.center[1] 
                        for f in target_cell.country.fortresses)
        
        # Определяем необходимый минимум юнитов
        required = 1
        if target_cell.unit:  # Против юнита
            required = 2
        elif has_fortress:    # Против крепости
            required = 3
        elif is_capital:      # Против столицы
            required = 2
        
        # Проверяем достаточно ли юнитов
        if len(attacking_units) < required:
            return False
        
        # Проверяем что все юниты могут атаковать эту клетку
        for unit in attacking_units:
            if not self._are_neighbors(unit.cell, target_cell):
                return False
        
        return True

    def handle_attack(self, attacking_units, target_cell, attacking_country, trees):
        # Удаляем всё с целевой клетки
        self.clear_cell_contents(target_cell, target_cell.country, trees)
        defending_country = target_cell.country
        capital_was_captured = False
        if target_cell == defending_country.capital:
            capital_was_captured = True
        for unit in attacking_units:
            unit.has_moved = True
        defending_country.completely_remove_cell(target_cell)
        if target_cell.id in Country.occupied_cells:
            Country.occupied_cells.remove(target_cell.id)
        if attacking_units:
            first_unit = attacking_units[0]
            first_unit.cell.unit = None
            first_unit.cell = target_cell
            first_unit.x, first_unit.y = target_cell.center
            first_unit.has_moved = True
            target_cell.unit = first_unit
        target_cell.country = attacking_country
        attacking_country.cells.append(target_cell)
        Country.occupied_cells.add(target_cell.id)
        # Улучшенная обработка переноса столицы
        if capital_was_captured:
            # Ищем полностью свободную клетку для новой столицы
            new_capital = None
            for cell in defending_country.cells:
                # Полная очистка клетки
                self._force_clear_cell(cell, defending_country, trees)
                # Проверяем, что клетка полностью свободна (нет юнитов, городов, крепостей, деревьев)
                has_tree = any(tree.x == cell.center[0] and tree.y == cell.center[1] for tree in trees)
                has_unit = any(unit.x == cell.center[0] and unit.y == cell.center[1] for unit in defending_country.units)
                has_city = any(city.x == cell.center[0] and city.y == cell.center[1] for city in defending_country.cities)
                has_fortress = any(f.x == cell.center[0] and f.y == cell.center[1] for f in defending_country.fortresses)
                if not (has_tree or has_unit or has_city or has_fortress):
                    new_capital = cell
                    break
            # Если не нашли свободную клетку — столица не назначается
            defending_country.capital = new_capital
        attacking_country.economy.calculate_income()
        defending_country.economy.calculate_income()
        return capital_was_captured

    def get_common_moves(self, units, cells, country):
        """Возвращает общие доступные клетки для группы юнитов, включая вражеские юниты для атаки"""
        if not units:
            return []
        
        common_cells = []
        for i, unit in enumerate(units):
            unit_cells = []
            for cell in cells:
                # Проверка соседства
                if not self._are_neighbors(unit.cell, cell):
                    continue
                    
                # Проверка для вражеских клеток
                if hasattr(cell, 'country') and cell.country and cell.country != country:
                    # Определяем требования для атаки
                    required = 1  # По умолчанию 1 юнит
                    
                    if cell.unit:  # Для атаки юнита нужно 2 юнита
                        required = 2
                    elif any(f.x == cell.center[0] and f.y == cell.center[1] 
                        for f in cell.country.fortresses):  # Для крепости нужно 3
                        required = 3
                    elif cell == cell.country.capital:  # Для столицы нужно 2
                        required = 2
                    
                    # Если достаточно юнитов для атаки - добавляем клетку
                    if len(units) >= required:
                        unit_cells.append(cell)
                    continue
                
                # Для своих/нейтральных клеток проверяем свободна ли клетка
                if cell.unit:
                    continue
                    
                # Проверка для клеток своей страны
                if cell in country.cells:
                    # Нельзя на столицу
                    if cell == country.capital:
                        continue
                    # Проверка городов и крепостей
                    if any(city.x == cell.center[0] and city.y == cell.center[1] 
                        for city in country.cities):
                        continue
                    if any(fortress.x == cell.center[0] and fortress.y == cell.center[1] 
                        for fortress in country.fortresses):
                        continue
                
                # Если все проверки пройдены - добавляем клетку
                unit_cells.append(cell)
            
            # Формируем список общих клеток для всех юнитов
            if i == 0:
                common_cells = unit_cells
            else:
                common_cells = [c for c in common_cells if c in unit_cells]
        
        return common_cells
    

    def clear_cell_contents(self, cell, country, trees):
        """Полностью очищает клетку от всех объектов перед размещением нового"""
        # Удаляем дерево
        for tree in trees[:]:
            if tree.x == cell.center[0] and tree.y == cell.center[1]:
                trees.remove(tree)
                break
        
        # Удаляем объекты страны-владельца
        if hasattr(cell, 'country') and cell.country:
            cell.country.remove_unit_at_cell(cell)
            cell.country.remove_city_at_cell(cell)
            cell.country.remove_fortress_at_cell(cell)
        
        # Очищаем ссылки в самой клетке
        if hasattr(cell, 'unit'):
            cell.unit = None

    def _force_clear_cell(self, cell, country, trees):
        """Агрессивно очищает клетку от всех объектов"""
        # Удаляем объекты страны
        country.remove_unit_at_cell(cell)
        country.remove_city_at_cell(cell)
        country.remove_fortress_at_cell(cell)
        
        # Удаляем деревья
        trees[:] = [t for t in trees if (t.x, t.y) != (cell.center[0], cell.center[1])]
        
        # Очищаем ссылки в клетке
        if hasattr(cell, 'unit'):
            cell.unit = None

    def _cell_has_objects(self, cell, country, trees):
        """Проверяет наличие объектов на клетке"""
        # Проверяем юнитов страны
        if any((u.x, u.y) == (cell.center[0], cell.center[1]) for u in country.units):
            return True
        # Проверяем города
        if any((c.x, c.y) == (cell.center[0], cell.center[1]) for c in country.cities):
            return True
        # Проверяем крепости
        if any((f.x, f.y) == (cell.center[0], cell.center[1]) for f in country.fortresses):
            return True
        # Проверяем деревья
        if any((t.x, t.y) == (cell.center[0], cell.center[1]) for t in trees):
            return True
        return False
