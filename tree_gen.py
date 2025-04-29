import random
from tree import Tree  # Импортируем Tree из нового файла
from game_mechanics import GameState  # Импортируем для проверки соседства

# Изменить generate_trees
def generate_trees(cells, num_trees, tree_size=50, countries=None):
    trees = []
    if countries is None:
        countries = []
    
    # Собираем центры клеток, где нельзя размещать деревья (столицы)
    forbidden_centers = set()
    for country in countries:
        # Проверяем, что страна имеет столицу и она не None
        if hasattr(country, 'capital') and country.capital is not None:
            capital_cell = country.capital
            # Запрещаем саму столицу
            forbidden_centers.add((capital_cell.center[0], capital_cell.center[1]))
    
    # Доступные клетки (где нет запрещённых центров)
    available_cells = [
        cell for cell in cells 
        if (cell.center[0], cell.center[1]) not in forbidden_centers
    ]
    
    # Генерируем деревья
    for _ in range(num_trees):
        if not available_cells:
            break
        cell = random.choice(available_cells)
        trees.append(Tree(cell.center[0], cell.center[1], tree_size))
        available_cells.remove(cell)
    
    return trees
    