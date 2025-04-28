import random
import pygame
import math
from map_gen import HexCell

class Tree:
    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.size = size
        self.image = pygame.image.load('./images/tree.png')
        self.image = pygame.transform.scale(self.image, (size, size))

    def draw(self, surface):
        surface.blit(self.image, (self.x - self.size//2, self.y - self.size//2))

def generate_trees(cells, num_trees, tree_size=50, countries=None):
    trees = []
    if countries is None:
        countries = []
    
    # Собираем все занятые клетки (столицы и их соседи)
    forbidden_cells = set()
    for country in countries:
        if hasattr(country, 'capital') and country.capital:
            forbidden_cells.add(country.capital)
            # Добавляем соседей столицы
            for cell in cells:
                if GameState._are_neighbors(country.capital, cell):
                    forbidden_cells.add(cell)
    
    # Доступные клетки
    available_cells = [cell for cell in cells if cell not in forbidden_cells]
    
    for _ in range(num_trees):
        if not available_cells:
            break
        cell = random.choice(available_cells)
        trees.append(Tree(cell.center[0], cell.center[1], tree_size))
        available_cells.remove(cell)
    
    return trees
    
    # Функция для проверки соседних клеток
    def has_tree_neighbor(cell):
        for other_cell in cells:
            if other_cell.id in occupied_cells:
                # Проверяем, являются ли клетки соседями
                q_diff = abs(cell.q - other_cell.q)
                r_diff = abs(cell.r - other_cell.r)
                if (q_diff == 1 and r_diff == 0) or (q_diff == 0 and r_diff == 1) or (q_diff == 1 and r_diff == 1):
                    return True
        return False
    
    # Генерируем деревья
    while len(trees) < num_trees and available_cells:
        # Сначала пытаемся разместить дерево рядом с существующим
        if trees:
            # Создаем список клеток, соседствующих с существующими деревьями
            neighbor_cells = [cell for cell in available_cells if has_tree_neighbor(cell)]
            if neighbor_cells:
                cell = random.choice(neighbor_cells)
            else:
                cell = random.choice(available_cells)
        else:
            cell = random.choice(available_cells)
        
        # Размещаем дерево точно по центру клетки
        trees.append(Tree(cell.center[0], cell.center[1], tree_size))
        occupied_cells.add(cell.id)
        available_cells.remove(cell)
    
    return trees 