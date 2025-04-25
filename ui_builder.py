import pygame

class UIBuilder:
    def __init__(self, economy):
        self.economy = economy
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.visible = False
        self.selected_option = None
        
        # Загрузка изображений
        self.unit_img = pygame.image.load('./images/unit.png').convert_alpha()
        self.city_img = pygame.image.load('./images/village.png').convert_alpha()
        self.fortress_img = pygame.image.load('./images/defence.png').convert_alpha()
        
        # Позиции и размеры
        self.panel_rect = pygame.Rect(0, 950, 1920, 130)
        self.unit_rect = pygame.Rect(200, 970, 40, 40)
        self.city_rect = pygame.Rect(300, 970, 40, 40)
        self.fortress_rect = pygame.Rect(400, 970, 40, 40)

        # Изменяем размеры изображений
        self.unit_img = pygame.transform.scale(self.unit_img, (40, 40))  # Было (80, 80)
        self.city_img = pygame.transform.scale(self.city_img, (40, 40))
        self.fortress_img = pygame.transform.scale(self.fortress_img, (40, 40))
        

    def draw(self, surface):
        if not self.visible:
            return
            
        # Рисуем панель
        pygame.draw.rect(surface, (50, 50, 70), self.panel_rect)
        pygame.draw.rect(surface, (100, 100, 120), self.panel_rect, 2)
        
        # Рисуем варианты строительства
        surface.blit(self.unit_img, self.unit_rect)
        surface.blit(self.city_img, self.city_rect)
        surface.blit(self.fortress_img, self.fortress_rect)
        
        # Цены
        unit_text = self.small_font.render("8$", True, (100, 255, 100))
        city_text = self.small_font.render("12$", True, (100, 255, 100))
        fortress_text = self.small_font.render("15$", True, (100, 255, 100))
        
        surface.blit(unit_text, (self.unit_rect.x + 30, self.unit_rect.y + 85))
        surface.blit(city_text, (self.city_rect.x + 30, self.city_rect.y + 85))
        surface.blit(fortress_text, (self.fortress_rect.x + 25, self.fortress_rect.y + 85))

    def handle_click(self, pos):
        if not self.visible:
            return None
            
        if self.unit_rect.collidepoint(pos) and self.economy.balance >= 8:
            return "unit"
        elif self.city_rect.collidepoint(pos) and self.economy.balance >= 12:
            return "city"
        elif self.fortress_rect.collidepoint(pos) and self.economy.balance >= 15:
            return "fortress"
        return None