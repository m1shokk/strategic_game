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


# Инициализация деревьев (исключая территории всех столиц и их соседей)
trees = generate_trees(cells, 20, 50, None)  # Пока не исключаем столицы

# Создаем экономику для каждой страны
for country in countries:
    country.economy = Economy(country.capital, country.cells, trees)
    country.economy.calculate_income()

game_state = GameState(num_players=4)
ui_builder = UIBuilder(countries[0].economy)  # UI будет переключаться между игроками

# Переменные состояния
building_mode = None
dragging_unit = None
building_drag = None
selected_unit = None
highlighted_cells = []  # Для подсветки доступных клеток

# Главный игровой цикл
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    current_player_index = game_state.current_player
    player_country = countries[current_player_index]
    
    # Обновляем UI для текущего игрока
    ui_builder.economy = player_country.economy

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Левая кнопка мыши
                # Выход из режима строительства при клике вне UI
                if building_drag and not ui_builder.panel_rect.collidepoint(mouse_pos):
                    building_drag = None
                    continue
                
                # Проверка кнопки хода
                if game_state.handle_click(mouse_pos, cells, trees, countries):
                    for country in countries:
                        for unit in country.units:
                            unit.has_moved = False
                        country.economy.end_turn()
                    building_mode = None
                    ui_builder.visible = False
                    selected_unit = None
                    highlighted_cells = []
                
                # Проверка UI строительства
                elif ui_builder.visible and ui_builder.panel_rect.collidepoint(mouse_pos):
                    selected_option = ui_builder.handle_click(mouse_pos)
                    if selected_option:
                        building_drag = selected_option
                        selected_unit = None
                        highlighted_cells = []
                
                # Проверка клика по юниту текущего игрока
                else:
                    unit_clicked = False
                    for unit in player_country.units:
                        if math.dist((unit.x, unit.y), mouse_pos) < 20 and not unit.has_moved:
                            selected_unit = unit
                            unit_clicked = True
                            # Подсвечиваем доступные клетки
                            # В обработчике клика по юниту:
                            highlighted_cells = []
                            for cell in cells:
                                # Строгая проверка соседства (только 1 клетка)
                                if not game_state._are_neighbors(unit.cell, cell) or cell.unit:
                                    continue
                                
                                # Проверяем специальные случаи для клеток страны игрока
                                if cell in player_country.cells:
                                    # Нельзя перемещаться на столицу
                                    if cell == player_country.capital:
                                        continue
                                    
                                    # Проверяем наличие городов или крепостей
                                    has_city = any(city.x == cell.center[0] and city.y == cell.center[1] 
                                                for city in player_country.cities)
                                    has_fortress = any(fortress.x == cell.center[0] and fortress.y == cell.center[1] 
                                                    for fortress in player_country.fortresses)
                                    
                                    if has_city or has_fortress:
                                        continue
                                
                                # Если все проверки пройдены, добавляем клетку в подсвеченные
                                highlighted_cells.append(cell)  
                            break
                    
                    if not unit_clicked and selected_unit:
                        # Пытаемся переместить юнита на выбранную клетку
                        for cell in cells:
                            if point_in_hexagon(mouse_pos, cell.points) and cell in highlighted_cells:
                                if game_state.handle_unit_movement(selected_unit, cell, player_country, trees):
                                    selected_unit = None
                                    highlighted_cells = []
                                break
                        else:
                            # Клик вне доступных клеток - снимаем выделение
                            selected_unit = None
                            highlighted_cells = []
                    
                    elif not unit_clicked:
                        # Проверка клика по территории текущего игрока
                        clicked_on_country = any(
                            point_in_hexagon(mouse_pos, cell.points)
                            for cell in player_country.cells
                        )
                        if clicked_on_country:
                            if building_drag:
                                building_drag = None
                            else:
                                # Сбрасываем выделение у всех стран
                                for country in countries:
                                    country.selected = False
                                # Выделяем текущую страну
                                player_country.selected = True
                                ui_builder.visible = True
                                selected_unit = None
                                highlighted_cells = []
                        else:
                            # Клик вне страны - снимаем выделение
                            for country in countries:
                                country.selected = False
                            ui_builder.visible = False
                            selected_unit = None
                            highlighted_cells = []
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and building_drag:
                # Находим клетку, на которую отпустили
                for cell in cells:
                    if point_in_hexagon(mouse_pos, cell.points):
                        # Строительство объекта
                        if (cell in player_country.cells and 
                            player_country.is_cell_free(cell, trees)):
                            
                            if building_drag == "unit" and player_country.economy.balance >= 8:
                                unit = Unit(cell.center[0], cell.center[1])
                                unit.cell = cell
                                cell.unit = unit
                                player_country.units.append(unit)
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
                # Полный сброс всех режимов
                building_mode = None
                dragging_unit = None
                building_drag = None
                selected_unit = None
                ui_builder.visible = False
                for country in countries:
                    country.selected = False
                highlighted_cells = []

    # Отрисовка
    screen.fill(BG_COLOR)
    
    # Клетки (кроме стран игроков)
    for cell in cells:
        is_hovered = point_in_hexagon(mouse_pos, cell.points)
        cell.draw(screen, is_hovered)
    
    # Подсветка доступных клеток для перемещения
    for cell in highlighted_cells:
        pygame.draw.polygon(screen, (200, 200, 100), cell.points, 3)
    
    # Страны и их объекты (рисуем все страны)
    for country in countries:
        country.draw(screen)
    
    # Деревья
    for tree in trees:
        tree.draw(screen)
    
    # UI
    game_state.draw(screen)
    
    # Показываем экономику только для текущего игрока
    player_country.economy.draw(screen)
    
    # UI строительства (если страна выделена)
    ui_builder.draw(screen)
    
    # Отрисовка перетаскиваемого объекта строительства
    if building_drag:
        if building_drag == "unit":
            img = ui_builder.unit_img
        elif building_drag == "city":
            img = ui_builder.city_img
        else:
            img = ui_builder.fortress_img
        screen.blit(img, (mouse_pos[0] - 20, mouse_pos[1] - 20))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()