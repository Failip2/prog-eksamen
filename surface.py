import pygame

class Surface(pygame.sprite.Sprite):
    _registry = []
    def __init__(self, imageUrl, size):
        super().__init__()
        self._registry.append(self)
        self.image = pygame.transform.scale(pygame.image.load(imageUrl).convert_alpha(), size)

        self.rect = self.image.get_rect()

class textSurface(pygame.sprite.Sprite):
    