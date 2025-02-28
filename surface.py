import pygame

class Surface(pygame.sprite.Sprite):
    _registry = []
    def __init__(self):
        super().__init__()
        self._registry.append(self)
        self.image = pygame.transform.scale(pygame.image.load("assets/img/zomb.png").convert_alpha(), (300, 300))

        self.rect = self.image.get_rect()