import pygame

class Economy:
    def __init__(self, capital, country_cells, trees):
        self.capital = capital
        self.country_cells = country_cells
        self.trees = trees
        self.balance = 10
        self.income = 0
        self.font = pygame.font.Font(None, 36)

    def calculate_income(self):
        """Считает доход игрока за ход."""
        self.income = 0
        
        for cell in self.country_cells:
            # Проверяем, что клетка всё ещё принадлежит стране
            if not hasattr(cell, 'country') or cell.country != self.capital.country:
                continue
                
            has_tree = any(tree.x == cell.center[0] and tree.y == cell.center[1] for tree in self.trees)
            if cell == self.capital:
                self.income += 2
            elif not has_tree:
                self.income += 1
        
        if hasattr(self.capital, 'country'):
            country = self.capital.country
            self.income += len(country.cities) * 4
            self.income -= len(country.units) * 2
            self.income -= len(country.fortresses) * 1

    def end_turn(self):
        """Вызывается в конце хода: добавляет доход."""
        self.calculate_income()
        self.balance += self.income

    def draw(self, surface):
        """Показывает баланс и доход."""
        balance_text = f"Balance: ${self.balance}"
        income_text = f"Income: ${self.income}/turn"
        balance_surface = self.font.render(balance_text, True, (255, 255, 255))
        income_surface = self.font.render(income_text, True, (255, 255, 255))
        surface.blit(balance_surface, (20, 60))
        surface.blit(income_surface, (20, 100))