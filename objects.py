import pygame

class Unit:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.image = pygame.image.load('./images/unit.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (40, 40))
        self.has_moved = False  # Флаг, указывающий, двигался ли юнит в этот ход
        self.cell = None  # Ссылка на клетку, на которой стоит юнит (добавим при создании)

class City:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.image = pygame.image.load('./images/village.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (50, 50))

class Fortress:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.image = pygame.image.load('./images/defence.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (50, 50))