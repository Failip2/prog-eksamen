import pygame
import config as c
import os
import surface
from collections import Counter
import noiseGen
import math

pygame.init()
pygame.font.init()
from pygame.locals import *
pygame.event.set_allowed([QUIT, KEYDOWN, KEYUP, WINDOWRESIZED])

os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"

info = pygame.display.Info()
screen_center = (info.current_w // 2, info.current_h // 2)

clock = pygame.time.Clock()


#flags = FULLSCREEN | DOUBLEBUF
flags = DOUBLEBUF
screen = pygame.display.set_mode((info.current_w, info.current_h), flags)

zoomSurf = pygame.Surface((info.current_w, info.current_h))
zoomRect = zoomSurf.fill((255,0,0))

drawSurf = screen



charControls = {K_UP: (0, -c.PLAYER_SPEED), K_DOWN: (0, c.PLAYER_SPEED), K_RIGHT: (c.PLAYER_SPEED, 0), K_LEFT: (-c.PLAYER_SPEED, 0)}


testBool = True
oldrects = []

def rect_key(rect):
    """Returns a tuple of the rect's position and size."""
    return (rect[0], rect[1], rect[2], rect[3])

def merge_and_filter_uniques(list1, list2):
    """
    Merges two lists of pygame.Rect (or mixture) and
    removes items that appear more than once. 
    Items are 'the same' if their (x, y, width, height) are identical.
    """
    combined = list1 + list2
    # Convert rects to hashable tuples
    combined_as_keys = [rect_key(r) for r in combined]

    counts = Counter(combined_as_keys)
    
    # Filter out any rect whose key appears more than once
    result = [
        r for r in combined 
        if counts[rect_key(r)] == 1
    ]
    return result

tile_size = 10
map_height = math.ceil(info.current_h/tile_size)
map_width = math.ceil(info.current_w/tile_size)
scale = 10.0
biome_map = noiseGen.get_biome_map(map_width, map_height, scale)
island_group = pygame.sprite.RenderUpdates()

def get_chunk_coords(world_x, world_y):
    cx = world_x // c.CHUNK_SIZE
    cy = world_y // c.CHUNK_SIZE
    return (cx, cy)

for j in range(map_height):
    for i in range(map_width):
        color = biome_map[j][i]
        surf = surface.RectSprite(i*tile_size, j*tile_size, tile_size, tile_size, color, island_group)

island_surf = surface.RectSprite(0, 0, info.current_w, info.current_h, (0,0,0))
island_group.draw(island_surf.image)
print(island_group)

playerGroup = pygame.sprite.RenderUpdates()

testGroup = pygame.sprite.RenderUpdates()
testGroup.add(island_surf)
testSurf = surface.Surface("assets/img/zomb.png", (300, 300), testGroup, playerGroup)
testText = surface.textSurface(testGroup)


class GameObject:
    def __init__(self, image, center):
        self.image = image
        self.rect = image.get_rect(center=center)

island_surfDraw = GameObject(island_surf.image, screen_center)

while c.GAME_IS_RUNNING:
    for event in pygame.event.get(): 
        if event.type == pygame.QUIT: 
            c.GAME_IS_RUNNING = False

        if event.type == pygame.WINDOWRESIZED:
            info = pygame.display.Info()
            screen = pygame.display.set_mode((info.current_w, info.current_h), flags)
            zoomSurf = pygame.Surface((info.current_w, info.current_h))

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_z:      # Zoom in
                zoom_factor = 1.1           # e.g., 110% of current size
            elif event.key == pygame.K_x:    # Zoom out
                zoom_factor = 0.9           # e.g., 90% of current size
            else:
                zoom_factor = 1.0

            if zoom_factor != 1.0:
                # 1. Scale the background (island) image around its center
                island_surfDraw.image = pygame.transform.rotozoom(island_surfDraw.image, 0, zoom_factor)
                island_surfDraw.rect = island_surfDraw.image.get_rect(center=screen_center)

                # 2. Scale each sprite in playerGroup around the center
                for sprite in playerGroup.sprites():
                    # Calculate offset of sprite from screen center
                    offset_x = sprite.rect.centerx - screen_center[0]
                    offset_y = sprite.rect.centery - screen_center[1]
                    # Scale the offset by the same zoom factor
                    new_offset_x = offset_x * zoom_factor
                    new_offset_y = offset_y * zoom_factor
                    # Scale the sprite's image from its current size
                    sprite.image = pygame.transform.rotozoom(sprite.image, 0, zoom_factor)
                    # Update the sprite's rect, keeping the new center relative to screen center
                    new_center = (screen_center[0] + int(new_offset_x), screen_center[1] + int(new_offset_y))
                    sprite.rect = sprite.image.get_rect(center=new_center)
                    

    keys = pygame.key.get_pressed()
    if keys[K_UP]:
        testSurf.rect.move_ip(charControls[K_UP])
    if keys[K_DOWN]:
        testSurf.rect.move_ip(charControls[K_DOWN])
    if keys[K_LEFT]:
        testSurf.rect.move_ip(charControls[K_LEFT])
    if keys[K_RIGHT]:
        testSurf.rect.move_ip(charControls[K_RIGHT])

    #rects = testGroup.draw(zoomSurf)


    # Blits the fully compiled zoomSurf layer (players, terrain, etc.) to 'screen' surface and accounts for zoom offsets
    #screen.blit(zoomSurf, zoomRect)

    screen.fill((0, 0, 0))  # fill background black or any color
    # Blit the island background
    screen.blit(island_surfDraw.image, island_surfDraw.rect)
    # Blit all sprites in the playerGroup
    for sprite in playerGroup:
        screen.blit(sprite.image, sprite.rect)

    screen.blit(testText.image, testText.rect)

    for t in surface.textSurface.instances:
        t.update_text(clock.get_fps())
    
    pygame.display.flip()
    
    clock.tick()




pygame.quit()