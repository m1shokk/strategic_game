import pygame
from map_gen import generate_hex_cells, point_in_hexagon, HexCell, BG_COLOR, CELL_COLOR, HOVER_COLOR, BORDER_COLOR
from tree_gen import generate_trees
from game_mechanics import GameState
from country import Country
from eco import Economy
from ui_builder import UIBuilder
from objects import Unit, City, Fortress


# Инициализация Pygame
pygame.init()
screen = pygame.display.set_mode((1920, 1080))
pygame.display.set_caption("Hex Grid with Trees")
clock = pygame.time.Clock()

# Генерация карты
cells = generate_hex_cells()

# Создание страны игрока
player_country = Country(cells)

# Генерация деревьев
trees = generate_trees(cells, 20, 50, player_country.capital)

# Экономика
economy = Economy(player_country.capital, player_country.cells, trees)
economy.calculate_income()  # Первоначальный расчет дохода

# Инициализация состояния игры
game_state = GameState()

ui_builder = UIBuilder(economy)
building_mode = None  # Режим строительства: None, "unit", "city" или "fortress"

# Главный игровой цикл
running = True
while running:
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Левая кнопка мыши
                # Сначала проверяем кнопку хода
                if game_state.handle_click(mouse_pos, cells, trees, player_country.capital):
                    economy.end_turn()
                    building_mode = None
                    ui_builder.visible = False
                else:
                    # Проверяем клик по UI строительства
                    selected_option = ui_builder.handle_click(mouse_pos)
                    if selected_option:
                        building_mode = selected_option
                        player_country.selected = True  # Подсвечиваем страну при выборе постройки
                    else:
                        # Проверяем клик по территории страны
                        clicked_on_country = False
                        for cell in player_country.cells:
                            if point_in_hexagon(mouse_pos, cell.points):
                                clicked_on_country = True
                                break
                        
                        if clicked_on_country:
                            # Если кликнули по стране и не в режиме строительства - показываем UI
                            if not building_mode:
                                player_country.selected = True
                                ui_builder.visible = True
                            else:
                                # Режим строительства - пытаемся построить
                                for cell in player_country.cells:
                                    if point_in_hexagon(mouse_pos, cell.points):
                                        if player_country.is_cell_free(cell, trees):  # Добавим trees как параметр
                                            if building_mode == "unit" and economy.balance >= 8:
                                                player_country.units.append(Unit(cell.center[0], cell.center[1]))
                                                economy.balance -= 8
                                                building_mode = None
                                            elif building_mode == "city" and economy.balance >= 12:
                                                player_country.cities.append(City(cell.center[0], cell.center[1]))
                                                economy.balance -= 12
                                                building_mode = None
                                            elif building_mode == "fortress" and economy.balance >= 15:
                                                player_country.fortresses.append(Fortress(cell.center[0], cell.center[1]))
                                                economy.balance -= 15
                                                building_mode = None
                                            elif event.type == pygame.KEYDOWN:
                                                if event.key == pygame.K_ESCAPE:
                                                    building_mode = None
                                        break
                        else:
                            # Клик вне страны - снимаем выделение
                            player_country.selected = False
                            ui_builder.visible = False
                            building_mode = None

    # Отображение клеток
    screen.fill(BG_COLOR)

    # Отображение клеток (кроме клеток страны)
    for cell in cells:
        if cell not in player_country.cells:
            is_hovered = point_in_hexagon(mouse_pos, cell.points)
            cell.draw(screen, is_hovered)

    # Отображение страны игрока
    player_country.draw(screen)

    # Отображение деревьев
    for tree in trees:
        tree.draw(screen)

    # Отображение UI игры
    game_state.draw(screen)

    # Отображение экономики
    economy.draw(screen)

    # Отображение UI строительства
    ui_builder.draw(screen)

    # Отрисовка курсора в режиме строительства
    if building_mode:
        pygame.draw.circle(screen, (100, 255, 100), mouse_pos, 15, 2)
        mode_text = ui_builder.font.render(f"Place {building_mode} (Esc - cancel)", True, (100, 255, 100))
        screen.blit(mode_text, (mouse_pos[0] + 20, mouse_pos[1] - 10))


    pygame.display.flip()
    clock.tick(60)

pygame.quit()