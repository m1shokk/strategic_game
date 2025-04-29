import pygame
from map_gen import generate_hex_cells, point_in_hexagon, BG_COLOR
from tree_gen import generate_trees
from game_mechanics import GameState
from country import Country
from eco import Economy
from ui_builder import UIBuilder
from objects import Unit, City, Fortress
import math

# Инициализация Pygame
pygame.init()
screen = pygame.display.set_mode((1920, 1080))
pygame.display.set_caption("Hex Strategy Game - 4 Players")
clock = pygame.time.Clock()

# Сброс статических полей перед созданием стран
Country.used_colors = set()
Country.occupied_cells = set()

# Инициализация игровых объектов
cells = generate_hex_cells()

# Создаем 4 страны
countries = []
for i in range(4):
    country = Country(cells)
    country.player_index = i  # Добавляем индекс игрока
    countries.append(country)

# ========== УЛУЧШЕННАЯ ГЕНЕРАЦИЯ ДЕРЕВЬЕВ ==========
print("\n=== ГЕНЕРАЦИЯ ДЕРЕВЬЕВ ===")
print("Проверка столиц перед генерацией:")
for i, country in enumerate(countries):
    if hasattr(country, 'capital') and country.capital:
        print(f"Страна {i+1}: столица на клетке {country.capital.id}, центр: {country.capital.center}")
    else:
        print(f"Страна {i+1}: ОШИБКА - СТОЛИЦА НЕ НАЗНАЧЕНА!")

trees = generate_trees(cells, 20, 50, countries)

# Проверка после генерации
print("\nПроверка размещения деревьев:")
capital_centers = [c.capital.center for c in countries if hasattr(c, 'capital') and c.capital]
tree_centers = [(t.x, t.y) for t in trees]

trees_on_capitals = sum(1 for cap in capital_centers if cap in tree_centers)
print(f"Деревьев на столицах: {trees_on_capitals} (должно быть 0)")
print(f"Всего деревьев сгенерировано: {len(trees)}")
# ===================================================

# Создаем экономику для каждой страны
for country in countries:
    country.economy = Economy(country.capital, country.cells, trees)
    country.economy.calculate_income()

game_state = GameState(num_players=4)
ui_builder = UIBuilder(countries[0].economy)

# Переменные состояния
building_mode = None
dragging_unit = None
building_drag = None
selected_units = []
highlighted_cells = []  
highlight_color = (200, 200, 100, 150)

# Отладочные переменные
debug_font = pygame.font.Font(None, 24)
debug_mode = False
debug_info = ""

def can_build_on_neutral(cell, country):
    """Проверяет можно ли построить на нейтральной соседней клетке"""
    if hasattr(cell, 'country') and cell.country:
        return False
    return any(game_state._are_neighbors(c, cell) for c in country.cells)

def get_common_moves(units, cells, country):
    """Старая функция, больше не используется (оставлена для совместимости)"""
    return game_state.get_common_moves(units, cells, country) if game_state else []

# Главный игровой цикл
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    current_player_index = game_state.current_player
    player_country = countries[current_player_index]
    
    # Пропускаем побеждённых игроков
    if player_country.is_defeated():
        game_state.players_ready[current_player_index] = True
        game_state.current_player = (game_state.current_player + 1) % game_state.num_players
        if all(country.is_defeated() for country in countries):
            running = False
        continue
    
    # Обновляем UI для текущего игрока
    ui_builder.economy = player_country.economy

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Левая кнопка мыши
                if building_drag and not ui_builder.panel_rect.collidepoint(mouse_pos):
                    building_drag = None
                    continue
                
                if game_state.handle_click(mouse_pos, cells, trees, countries):
                    # Обработка конца хода
                    for country in countries:
                        for unit in country.units:
                            unit.has_moved = False
                        country.economy.end_turn()
                    
                    building_mode = None
                    ui_builder.visible = False
                    selected_units = []
                    highlighted_cells = []
                
                elif ui_builder.visible and ui_builder.panel_rect.collidepoint(mouse_pos):
                    selected_option = ui_builder.handle_click(mouse_pos)
                    if selected_option:
                        building_drag = selected_option
                        selected_units = []
                        highlighted_cells = []
                
                else:
                    unit_clicked = False
                    for unit in player_country.units:
                        if math.dist((unit.x, unit.y), mouse_pos) < 20 and not unit.has_moved:
                            if pygame.key.get_pressed()[pygame.K_LSHIFT]:
                                if unit not in selected_units:
                                    selected_units.append(unit)
                            else:
                                selected_units = [unit]
                            unit_clicked = True
                            break
                    
                    if not unit_clicked and selected_units:
                        for cell in cells:
                            if point_in_hexagon(mouse_pos, cell.points) and cell in highlighted_cells:
                                if hasattr(cell, 'country') and cell.country and cell.country != player_country:
                                    game_state.handle_attack(selected_units, cell, player_country, trees)
                                else:
                                    if game_state.handle_unit_movement(selected_units[0], cell, player_country, trees):
                                        for unit in selected_units[1:]:
                                            unit.has_moved = True
                                selected_units = []
                                highlighted_cells = []
                                break
                        else:
                            selected_units = []
                            highlighted_cells = []
                    
                    elif not unit_clicked:
                        clicked_on_country = any(
                            point_in_hexagon(mouse_pos, cell.points)
                            for cell in player_country.cells
                        )
                        if clicked_on_country:
                            if building_drag:
                                building_drag = None
                            else:
                                for country in countries:
                                    country.selected = False
                                player_country.selected = True
                                ui_builder.visible = True
                                selected_units = []
                                highlighted_cells = []
                        else:
                            for country in countries:
                                country.selected = False
                            ui_builder.visible = False
                            selected_units = []
                            highlighted_cells = []
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and building_drag:
                for cell in cells:
                    if point_in_hexagon(mouse_pos, cell.points):
                        can_build = False
                        
                        # Проверяем возможность строительства
                        if cell in player_country.cells:
                            # Для юнитов разрешаем строить на клетках с деревьями, но запрещаем на столицах и постройках
                            if building_drag == "unit":
                                # Проверяем, что не столица и нет других объектов
                                if (cell != player_country.capital and
                                    not any(u.x == cell.center[0] and u.y == cell.center[1] for u in player_country.units) and
                                    not any(c.x == cell.center[0] and c.y == cell.center[1] for c in player_country.cities) and
                                    not any(f.x == cell.center[0] and f.y == cell.center[1] for f in player_country.fortresses)):
                                    can_build = True
                            else:
                                # Для других построек используем стандартную проверку
                                if player_country.is_cell_free(cell, trees):
                                    can_build = True
                        elif building_drag == "unit" and can_build_on_neutral(cell, player_country):
                            can_build = True
                        
                        if can_build:
                            # Удаляем дерево, если оно есть (только для юнитов внутри страны)
                            if building_drag == "unit" and cell in player_country.cells:
                                for tree in trees[:]:
                                    if tree.x == cell.center[0] and tree.y == cell.center[1]:
                                        trees.remove(tree)
                                        player_country.economy.balance += 2  # Бонус за вырубку
                                        break
                            
                            # Очищаем клетку для всех случаев, кроме юнитов внутри страны
                            if not (building_drag == "unit" and cell in player_country.cells):
                                game_state.clear_cell_contents(cell, player_country, trees)
                            
                            if building_drag == "unit" and player_country.economy.balance >= 8:
                                unit = Unit(cell.center[0], cell.center[1])
                                unit.cell = cell
                                cell.unit = unit
                                player_country.units.append(unit)
                                
                                if cell not in player_country.cells:
                                    cell.country = player_country
                                    player_country.cells.append(cell)
                                    player_country.economy.calculate_income()
                                
                                player_country.economy.balance -= 8
                            
                            elif building_drag == "city" and player_country.economy.balance >= 12:
                                player_country.cities.append(City(cell.center[0], cell.center[1]))
                                player_country.economy.balance -= 12
                            
                            elif building_drag == "fortress" and player_country.economy.balance >= 15:
                                player_country.fortresses.append(Fortress(cell.center[0], cell.center[1]))
                                player_country.economy.balance -= 15
                        
                        break
                
                building_drag = None
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                building_mode = None
                dragging_unit = None
                building_drag = None
                selected_units = []
                ui_builder.visible = False
                for country in countries:
                    country.selected = False
                highlighted_cells = []
            
            elif event.key == pygame.K_F3:
                debug_mode = not debug_mode
                print(f"Отладочный режим {'включен' if debug_mode else 'выключен'}")

    # Обновляем подсвеченные клетки
    highlighted_cells = game_state.get_common_moves(selected_units, cells, player_country) if selected_units else []

    # Отрисовка
    screen.fill(BG_COLOR)
    
    for cell in cells:
        is_hovered = point_in_hexagon(mouse_pos, cell.points)
        cell.draw(screen, is_hovered)
    
    for cell in highlighted_cells:
        xs = [p[0] for p in cell.points]
        ys = [p[1] for p in cell.points]
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        if width > 0 and height > 0:
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            overlay.fill(highlight_color)
            screen.blit(overlay, (min(xs), min(ys)))
    
    for country in countries:
        if not country.is_defeated():
            country.draw(screen)
    
    for tree in trees:
        tree.draw(screen)
    
    for i, unit in enumerate(selected_units):
        pygame.draw.circle(screen, (0, 255, 0), (unit.x, unit.y), 15 + i*5, 2)
    
    game_state.draw(screen)
    player_country.economy.draw(screen)
    ui_builder.draw(screen)
    
    if building_drag:
        if building_drag == "unit":
            img = ui_builder.unit_img
        elif building_drag == "city":
            img = ui_builder.city_img
        else:
            img = ui_builder.fortress_img
        screen.blit(img, (mouse_pos[0] - 20, mouse_pos[1] - 20))

    if debug_mode:
        debug_text = [
            f"Отладочный режим (F3)",
            f"Текущий игрок: {current_player_index + 1}",
            f"Клеток у игрока: {len(player_country.cells)}",
            f"Юнитов у игрока: {len(player_country.units)}",
            f"Occupied cells: {len(Country.occupied_cells)}",
            f"Курсор: {mouse_pos}",
            f"Деревьев на карте: {len(trees)}",
            debug_info
        ]
        
        for i, text in enumerate(debug_text):
            text_surface = debug_font.render(text, True, (255, 255, 255))
            screen.blit(text_surface, (10, 10 + i * 25))
        
        for cell in cells:
            if point_in_hexagon(mouse_pos, cell.points):
                owner = cell.country.color if hasattr(cell, 'country') and cell.country else "None"
                debug_info = f"Клетка {cell.id}, владелец: {owner}"
                if cell.unit:
                    debug_info += f", юнит: {cell.unit}"
                if cell in player_country.cells:
                    debug_info += f", столица: {cell == player_country.capital}"
                break

    pygame.display.flip()
    clock.tick(60)

pygame.quit()