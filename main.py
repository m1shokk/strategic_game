import pygame
from map_gen import generate_hex_cells, point_in_hexagon, BG_COLOR
from tree_gen import generate_trees
from game_mechanics import GameState
from country import Country
from eco import Economy
from ui_builder import UIBuilder
from objects import Unit, City, Fortress
import math
from itertools import chain
import time

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

# --- Новые переменные для статистики ---
show_stats = False
stats_button_rect = pygame.Rect(1920 - 220, 20, 200, 50)

# --- Система уведомлений ---
class EventNotification:
    def __init__(self, text, color=(255,255,255), duration=2.5):
        self.text = text
        self.color = color
        self.start_time = time.time()
        self.duration = duration
        self.alpha = 255
    def get_progress(self):
        return (time.time() - self.start_time) / self.duration

# Список активных уведомлений
# Каждый элемент: EventNotification
# Появляются по центру сверху, исчезают с затуханием
event_notifications = []

# --- Функция для добавления уведомления ---
def add_notification(text, color=(255,255,255), duration=2.5):
    event_notifications.append(EventNotification(text, color, duration))

# --- Для отслеживания событий ---
victory_notification = None  # Сохраняем победное уведомление
leader_country = None  # Для смены лидера по клеткам
first_unit_done = set()  # Индексы стран, у которых уже был первый юнит
first_city_done = set()  # Индексы стран, у которых уже был первый город
captured_capitals = set()  # id столиц, которые уже были захвачены
capitulated_countries = set()  # Индексы стран, которые уже капитулировали

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
    
    # --- Capitulation ---
    if player_country.is_defeated():
        if player_country.player_index not in capitulated_countries:
            add_notification(f"Country {player_country.player_index+1} has capitulated!", (255,100,100))
            capitulated_countries.add(player_country.player_index)
        game_state.players_ready[current_player_index] = True
        game_state.current_player = (game_state.current_player + 1) % game_state.num_players
        if all(country.is_defeated() for country in countries):
            # --- Victory ---
            alive = [c for c in countries if not c.is_defeated()]
            if alive:
                victory_notification = EventNotification(f"Country {alive[0].player_index+1} wins!", (100,255,100), 99999)
                event_notifications.append(victory_notification)
            running = False
        continue
    # --- Leader change ---
    max_cells = max(len(c.cells) for c in countries)
    leaders = [c for c in countries if len(c.cells) == max_cells and not c.is_defeated()]
    if leaders:
        if leader_country is None or leader_country != leaders[0]:
            if leader_country is not None:
                add_notification(f"New leader by cells: Country {leaders[0].player_index+1}!", (200,255,200))
            leader_country = leaders[0]
    
    # Обновляем UI для текущего игрока
    ui_builder.economy = player_country.economy

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if stats_button_rect.collidepoint(mouse_pos):
                    show_stats = not show_stats
                    continue
                if building_drag and not ui_builder.panel_rect.collidepoint(mouse_pos):
                    building_drag = None
                    continue
                
                if game_state.handle_click(mouse_pos, cells, trees, countries):
                    # Обработка конца хода
                    for country in countries:
                        for unit in country.units:
                            unit.has_moved = False
                        prev_units = len(country.units)
                        prev_balance = country.economy.balance
                        country.economy.end_turn()
                        country.economy.check_bankruptcy(country, trees)
                        if prev_balance < 0 and country.economy.balance == 0 and prev_units > 0 and len(country.units) == 0:
                            add_notification(f"Country {country.player_index+1} has gone bankrupt!", (255,180,100))
                    # --- Проверка захвата столицы ---
                    for country in countries:
                        if country.capital and id(country.capital) not in captured_capitals:
                            if hasattr(country.capital, 'country') and country.capital.country != country:
                                add_notification(f"Capital of Country {country.player_index+1} has been captured!", (255,120,255))
                                captured_capitals.add(id(country.capital))
                    building_mode = None
                    ui_builder.visible = False
                    selected_units = []
                    highlighted_cells = []
                    continue
                
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
                                    # --- Attack ---
                                    capital_captured = game_state.handle_attack(selected_units, cell, player_country, trees)
                                    if capital_captured:
                                        add_notification(f"Capital of Country {cell.country.player_index+1} has been captured!", (255,120,255))
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
                                
                                # --- Первый юнит ---
                                if player_country.player_index not in first_unit_done:
                                    add_notification(f"First unit for Country {player_country.player_index+1}!", (200,255,200))
                                    first_unit_done.add(player_country.player_index)
                                
                                if cell not in player_country.cells:
                                    cell.country = player_country
                                    player_country.cells.append(cell)
                                    player_country.economy.calculate_income()
                                
                                player_country.economy.balance -= 8
                            
                            elif building_drag == "city" and player_country.economy.balance >= 12:
                                player_country.cities.append(City(cell.center[0], cell.center[1]))
                                # --- Первый город ---
                                if player_country.player_index not in first_city_done:
                                    add_notification(f"First city for Country {player_country.player_index+1}!", (200,200,255))
                                    first_city_done.add(player_country.player_index)
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
    
    # --- Визуализация клеток ---
    # 1. Сначала рисуем все клетки (серый фон и подсветка выбора)
    for cell in cells:
        is_hovered = point_in_hexagon(mouse_pos, cell.points)
        # Если выбран юнит(ы), затемняем недоступные клетки, но не клетки выбранной страны
        cell_country = getattr(cell, 'country', None)
        is_selected_country = cell_country.selected if cell_country else False
        if selected_units and not is_selected_country:
            if cell in highlighted_cells:
                color = (100, 100, 100)
            else:
                color = (40, 40, 40)
        else:
            color = (160, 160, 160) if is_hovered else (100, 100, 100)
        pygame.draw.polygon(screen, color, cell.points)

    # 2. Затем рисуем заливку цветом страны (рандомный цвет из country.color)
    for country in countries:
        if not country.is_defeated():
            for cell in country.cells:
                pygame.draw.polygon(screen, country.color, cell.points)

    # 2. Жёлтая обводка для доступных клеток
    if selected_units:
        for cell in highlighted_cells:
            pygame.draw.polygon(screen, (255, 255, 0), cell.points, 4)

    # --- Вспомогательная функция для поиска внешних рёбер ---
    def get_outer_edges(cell_list):
        edge_count = {}
        for cell in cell_list:
            pts = cell.points
            for i in range(6):
                edge = (pts[i], pts[(i+1)%6])
                edge_rev = (pts[(i+1)%6], pts[i])
                if edge_rev in edge_count:
                    edge_count[edge_rev] += 1
                else:
                    edge_count[edge] = edge_count.get(edge, 0) + 1
        # Оставляем только те рёбра, которые встречаются один раз (внешние)
        return [edge for edge, count in edge_count.items() if count == 1]

    # 3. Белая полупрозрачная обводка по внешнему контуру всей карты
    map_edges = get_outer_edges(cells)
    for edge in map_edges:
        pygame.draw.line(screen, (255,255,255,180), edge[0], edge[1], 4)

    # 4. Чёрная обводка по внешнему контуру каждой страны (поверх всего)
    for country in countries:
        if not country.is_defeated() and len(country.cells) > 1:
            country_edges = get_outer_edges(country.cells)
            for edge in country_edges:
                pygame.draw.line(screen, (0,0,0), edge[0], edge[1], 5)

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
            f"Debug mode (F3)",
            f"Current player: {current_player_index + 1}",
            f"Player's cells: {len(player_country.cells)}",
            f"Player's units: {len(player_country.units)}",
            f"Occupied cells: {len(Country.occupied_cells)}",
            f"Cursor: {mouse_pos}",
            f"Trees on map: {len(trees)}",
            debug_info
        ]
        
        for i, text in enumerate(debug_text):
            text_surface = debug_font.render(text, True, (255, 255, 255))
            screen.blit(text_surface, (10, 10 + i * 25))
        
        for cell in cells:
            if point_in_hexagon(mouse_pos, cell.points):
                owner = cell.country.color if hasattr(cell, 'country') and cell.country else "None"
                debug_info = f"Cell {cell.id}, owner: {owner}"
                if cell.unit:
                    debug_info += f", unit: {cell.unit}"
                capitals = []
                for country in countries:
                    if cell == country.capital:
                        capitals.append(str(country.player_index + 1))
                if capitals:
                    debug_info += f", capital of: {', '.join(capitals)}"
                break

    # --- Рисуем кнопку статистики ---
    pygame.draw.rect(screen, (60, 60, 120), stats_button_rect, border_radius=12)
    pygame.draw.rect(screen, (200, 200, 255), stats_button_rect, 3, border_radius=12)
    font_stats = pygame.font.Font(None, 36)
    text_stats = font_stats.render('Stats', True, (255, 255, 255))
    text_rect_stats = text_stats.get_rect(center=stats_button_rect.center)
    screen.blit(text_stats, text_rect_stats)

    # --- Окно статистики ---
    if show_stats:
        # Полупрозрачный фон
        overlay = pygame.Surface((700, 400), pygame.SRCALPHA)
        overlay.fill((30, 30, 60, 230))
        screen.blit(overlay, (610, 120))
        # Заголовок
        title_font = pygame.font.Font(None, 48)
        title = title_font.render('Statistics', True, (255, 255, 255))
        screen.blit(title, (960 - title.get_width() // 2, 140))
        # Таблица
        table_font = pygame.font.Font(None, 36)
        header = table_font.render('Player   |   Income   |   Cells', True, (200, 220, 255))
        screen.blit(header, (670, 200))
        for i, country in enumerate(countries):
            # Чистый доход: только доход с клеток и городов, без расходов
            base_income = 0
            for cell in country.cells:
                if not hasattr(cell, 'country') or cell.country != country:
                    continue
                has_tree = any(tree.x == cell.center[0] and tree.y == cell.center[1] for tree in trees)
                if cell == country.capital:
                    base_income += 2
                elif not has_tree:
                    base_income += 1
            base_income += len(country.cities) * 4
            # Красивый цвет строки
            row_color = (220, 220, 255) if i % 2 == 0 else (180, 180, 220)
            row = table_font.render(f"{i+1:>5}   |   {base_income:>6}   |   {len(country.cells):>6}", True, row_color)
            screen.blit(row, (690, 240 + i * 40))

    # --- ОТРИСОВКА УВЕДОМЛЕНИЙ ---
    notif_font = pygame.font.Font(None, 54)
    notif_y = 40
    for notif in event_notifications[:]:
        if notif is victory_notification:
            alpha = 255
        else:
            progress = notif.get_progress()
            if progress > 1:
                event_notifications.remove(notif)
                continue
            # Fade in/out
            if progress < 0.15:
                alpha = int(255 * (progress/0.15))
            elif progress > 0.85:
                alpha = int(255 * (1 - (progress-0.85)/0.15))
            else:
                alpha = 255
        notif_surf = pygame.Surface((900, 70), pygame.SRCALPHA)
        notif_surf.fill((30,30,40, int(alpha*0.85)))
        text = notif_font.render(notif.text, True, notif.color)
        text.set_alpha(alpha)
        notif_surf.blit(text, (30, 20))
        shadow = pygame.Surface((900, 70), pygame.SRCALPHA)
        shadow.fill((0,0,0, int(alpha*0.25)))
        screen.blit(shadow, (510, notif_y+4))
        screen.blit(notif_surf, (510, notif_y))
        notif_y += 80

    pygame.display.flip()
    clock.tick(60)

pygame.quit()