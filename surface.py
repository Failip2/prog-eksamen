# Filip har skrevet surface.py

import pygame
from weakref import WeakSet

# Cache for storing loaded textures to avoid reloading them multiple times
_texture_cache = {}

class SpriteHandler(pygame.sprite.Sprite):
    # WeakSet to keep track of all instances of SpriteHandler
    instances = WeakSet()

    def __new__(cls, *args, **kwargs):
        # Create a new instance of the class
        instance = object.__new__(cls)
        # Ensure the instances WeakSet is initialized for the class
        if "instances" not in cls.__dict__:
            cls.instances = WeakSet()
        # Add the new instance to the WeakSet
        cls.instances.add(instance)
        return instance

    def __init__(self, *groups, **kwargs):
        # Initialize the parent class (pygame.sprite.Sprite)
        super().__init__(*groups)

class Surface(SpriteHandler):
    def __init__(self, imageUrl, size, world_x=0, world_y=0, *groups):
        super().__init__(*groups)
        # Load and cache the image if it hasn't been loaded before
        if imageUrl not in _texture_cache:
            _texture_cache[imageUrl] = pygame.transform.scale(pygame.image.load(imageUrl).convert_alpha(), size)
        # Set the image and its properties
        self.original_image = _texture_cache[imageUrl]
        self.image = self.original_image
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
        # Set the font and initial text
        self.font = pygame.font.SysFont('Comic Sans MS', 30)
        self.text = text
        # Render the text onto the image
        self.image = self.font.render(str(self.text), False, (0, 0, 255), (0, 0, 0))

        # Get the rectangle for positioning the text
        self.rect = self.image.get_rect()
    
    def update_text(self, text):
        # Update the text and re-render the image
        self.text = text
        self.image = self.font.render(str(self.text), False, (0, 0, 255), (0, 0, 0))

class staticImage(SpriteHandler):
    def __init__(self, imageUrl, size, *groups):
        super().__init__(*groups)

        # Load and cache the image if it hasn't been loaded before
        if imageUrl not in _texture_cache:
            _texture_cache[imageUrl] = pygame.transform.scale(pygame.image.load(imageUrl).convert_alpha(), size)
        # Set the image and its properties
        self.original_image = _texture_cache[imageUrl]
        self.image = self.original_image
        self.rect = self.image.get_rect()