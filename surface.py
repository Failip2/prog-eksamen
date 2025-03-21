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
    def __init__(self, imageUrl, size, world_x=0, world_y=0, *groups):
        super().__init__(*groups)
        self.image = pygame.transform.scale(
            pygame.image.load(imageUrl).convert_alpha(),
            size
        )
        self.world_x = world_x
        self.world_y = world_y
        self.rect = self.image.get_rect()
        self.original_image = self.image.copy()
        self.scaled_image = self.original_image.copy()

class RectSprite(SpriteHandler):
    def __init__(self, x, y, w, h, color, *groups, **kwargs):
        super().__init__(*groups, **kwargs)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        
        # Create a Surface of the given width/height
        self.image = pygame.Surface((w, h))

        # Fill the entire Surface with the given color
        self.image.fill(color)

        self.original_image = self.image

        # Position the sprite on-screen at (x, y)
        self.rect = pygame.Rect(x, y, w, h)

class textSurface(SpriteHandler):
    def __init__(self, text="placeholder", *groups):
        super().__init__(*groups)
        self.font = pygame.font.SysFont('Comic Sans MS', 30)
        self.text = text
        self.image = self.font.render(str(self.text), False, (0, 0, 255), (0,0,0))

        self.rect = self.image.get_rect()
    
    def update_text(self, text):
        self.text = text
        self.image = self.font.render(str(self.text), False, (0, 0, 255), (0,0,0))