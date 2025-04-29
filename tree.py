import pygame

class Tree:
    def __init__(self, x, y, size):
        self.x = x
        self.y = y
        self.size = size
        self.image = pygame.image.load('./images/tree.png')
        self.image = pygame.transform.scale(self.image, (size, size))

    def draw(self, surface):
        surface.blit(self.image, (self.x - self.size//2, self.y - self.size//2))