import pygame
from weakref import WeakSet

class SpriteHandler(pygame.sprite.Sprite):
    def __new__(cls, *args, **kwargs):
        instance = object.__new__(cls)
        if "instances" not in cls.__dict__:
            cls.instances = WeakSet()
        cls.instances.add(instance)
        return instance

    def __init__(self, *groups, **kwargs):
        super().__init__(*groups)
        

class Surface(SpriteHandler):
    def __init__(self, imageUrl, size, *groups):
        super().__init__(*groups)
        self.image = pygame.transform.scale(
            pygame.image.load(imageUrl).convert_alpha(),
            size
        )
        self.rect = self.image.get_rect()

class RectSprite(SpriteHandler):
    def __init__(self, x, y, w, h, color, *groups, **kwargs):
        super().__init__(*groups, **kwargs)
        
        # Create a Surface of the given width/height
        self.image = pygame.Surface((w, h))

        # Fill the entire Surface with the given color
        self.image.fill(color)

        # Position the sprite on-screen at (x, y)
        self.rect = pygame.Rect(x, y, w, h)

class textSurface(SpriteHandler):
    def __init__(self, *groups):
        super().__init__(*groups)
        self.font = pygame.font.SysFont('Comic Sans MS', 30)
        self.text = "cuh"
        self.image = self.font.render(str(self.text), False, (0, 0, 255), (0,0,0))

        self.rect = self.image.get_rect()
    
    def update_text(self, text):
        self.text = text
        self.image = self.font.render(str(self.text), False, (0, 0, 255), (0,0,0))
        self.rect = self.image.get_rect()