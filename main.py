import pygame
import config as c
import os
import surface
from collections import Counter
import noiseGen
import math
from pygame.locals import *
import random

pygame.init()
pygame.font.init()
pygame.event.set_allowed([QUIT, KEYDOWN, KEYUP, WINDOWRESIZED])

os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
info = pygame.display.Info()
clock = pygame.time.Clock()

flags = DOUBLEBUF
screen = pygame.display.set_mode((info.current_w, info.current_h), flags)
screen_center = (info.current_w // 2, info.current_h // 2)

# This offscreen surface is where we'll draw everything each frame.
zoomSurf = pygame.Surface((info.current_w, info.current_h))

charControls = {
    K_UP: (0, -c.PLAYER_SPEED),
    K_DOWN: (0, c.PLAYER_SPEED),
    K_RIGHT: (c.PLAYER_SPEED, 0),
    K_LEFT: (-c.PLAYER_SPEED, 0)
}

tile_size = 10
map_height = math.ceil(info.current_h / tile_size)
map_width = math.ceil(info.current_w / tile_size)
scale = 10.0

# Generate a biome map
biome_map = noiseGen.get_biome_map(map_width, map_height, scale)

# Sprite groups
playerGroup = pygame.sprite.RenderUpdates()

def generate_island_surface(cx, cy, chunk_w=50, chunk_h=50, tile_size=10, scale=15.0, isBiomeMap=True):
    offset_x = cx * chunk_w  # chunk coords -> tile offset
    offset_y = cy * chunk_h
    biome_data, collision_map = noiseGen.get_biome_map(chunk_w,chunk_h, scale, 
                                        offset_x, offset_y, isBiomeMap=isBiomeMap)

    chunk_pixel_w = chunk_w * tile_size
    chunk_pixel_h = chunk_h * tile_size
    surf = pygame.Surface((chunk_pixel_w, chunk_pixel_h)).convert_alpha()

    for j in range(chunk_h):
        for i in range(chunk_w):
            rect = pygame.Rect(i*tile_size, j*tile_size, tile_size, tile_size)
            surf.fill(biome_data[j][i], rect)

    chunk_rect = pygame.Rect(cx*chunk_pixel_w, cy*chunk_pixel_h, chunk_pixel_w, chunk_pixel_h)
    return surf, chunk_rect, biome_data, collision_map


class Chunk:
    def __init__(self, cx, cy, surface, rect, biome_data, collision_map):
        self.cx = cx
        self.cy = cy
        self.surface = surface
        self.rect = rect
        self.biome_data = biome_data
        self.collision_map = collision_map 


class ChunkManager:
    def __init__(self, chunk_width_tiles=50, chunk_height_tiles=50,
                 tile_size=10, scale=15.0, seed=None, isBiomeMap=True):
        """
        :param chunk_width_tiles: # of tiles horizontally in each chunk
        :param chunk_height_tiles: # of tiles vertically in each chunk
        :param tile_size: pixel size of each tile (e.g., 10)
        :param scale: Perlin scale factor
        :param seed: for consistent noise
        """
        self.chunk_width_tiles = chunk_width_tiles
        self.chunk_height_tiles = chunk_height_tiles
        self.tile_size = tile_size
        self.scale = scale
        self.seed = seed
        self.isBiomeMap = isBiomeMap

        # Stores (cx, cy) -> Chunk instance
        self.chunks = {}

    def get_chunk(self, cx, cy):
        """
        Return the Chunk at (cx, cy). If it doesn't exist, generate it.
        """
        if (cx, cy) in self.chunks:
            return self.chunks[(cx, cy)]
        else:
            surface, rect, biome_data, collision_map = generate_island_surface(
                cx=cx,
                cy=cy,
                chunk_w=self.chunk_width_tiles,
                chunk_h=self.chunk_height_tiles,
                tile_size=self.tile_size,
                scale=self.scale,
                isBiomeMap=self.isBiomeMap
            )
            new_chunk = Chunk(cx, cy, surface, rect, biome_data, collision_map)
            self.chunks[(cx, cy)] = new_chunk
            return new_chunk

    def draw_chunks(self, screen, camera_x, camera_y, screen_center, zoom=1.0):
        """
        Draw all loaded chunks that might be visible,
        using a camera anchored at (camera_x, camera_y) in world coords,
        so the camera is placed at screen_center with given zoom.
        """

        camera_cx = camera_x // chunk_pixel_w
        camera_cy = camera_y // chunk_pixel_h

        # Potentially cull or just draw all for demonstration
        for (cx, cy), chunk in self.chunks.items():
            if abs(cx - camera_cx) > 4 or abs(cy - camera_cy) > 4:
                #print("skipped chunk with coords: "+str(cx)+": "+str(cy))
                #print("player pos is: "+str(camera_cx)+": "+str(camera_cy))
                continue

            # Where does this chunk appear on screen?
            off_x = (chunk.rect.x - camera_x) * zoom
            off_y = (chunk.rect.y - camera_y) * zoom
            screen_x = screen_center[0] + off_x
            screen_y = screen_center[1] + off_y

            # Scale the chunk if you want chunk-based zoom
            # For performance, you could store pre-scaled surfaces 
            # or just do one big scale if the chunk is large.
            # We'll do a naive approach for demonstration:
            if zoom != 1.0:
                scaled_w = int(chunk.rect.width * zoom)
                scaled_h = int(chunk.rect.height * zoom)
                scaled_surf = pygame.transform.scale(chunk.surface, (scaled_w, scaled_h))
                zoomSurf.blit(scaled_surf, (screen_x, screen_y))
            else:
                # no scaling needed
                zoomSurf.blit(chunk.surface, (screen_x, screen_y))


def random_point_on_circle(center_x, center_y, radius):
    """
    Returns (x, y) coordinates on the circumference of 
    a circle of radius `radius` centered at (center_x, center_y).
    """
    angle = random.random() * 2 * math.pi
    x = center_x + radius * math.cos(angle)
    y = center_y + radius * math.sin(angle)
    return (x, y)


chunk_manager = ChunkManager(chunk_width_tiles=50, chunk_height_tiles=50,
                                 tile_size=10, scale=150.0, seed=42)
obstacle_manager = ChunkManager(chunk_width_tiles=50, chunk_height_tiles=50,
                                 tile_size=10, scale=10.0, seed=42, isBiomeMap=False)

########################################
# 2) Create a 'player' sprite
########################################
testSurf = surface.Surface("assets/img/zomb.png", (100, 100), info.current_w // 2, info.current_h // 2, playerGroup)

zombSurf = surface.Surface("assets/img/zomb.png", (100, 100), info.current_w // 2, info.current_h // 2, playerGroup)

# For demonstration, a text surface
testText = surface.textSurface()

########################################
# Initialize zoom
########################################
c.ZOOM_FACTOR = 1.0

########################################
# Function to scale everything ONCE
########################################
def rescale_all(zoom):
    """
    Re-scale the island background and all sprites from their original images.
    This is called only when zoom changes.
    """
    # Scale island background

    # Scale each sprite in playerGroup
    for sp in playerGroup.sprites():
        ow = sp.original_image.get_width()
        oh = sp.original_image.get_height()
        nw = int(ow * zoom)
        nh = int(oh * zoom)
        sp.scaled_image = pygame.transform.smoothscale(sp.original_image, (nw, nh))

########################################
# Function to draw everything each frame
########################################
def draw_all():
    """
    Compose the island background, player(s), etc. onto zoomSurf.
    The player is the camera center so it stays near screen_center.
    """
    zoomSurf.fill((0,0,0))
    chunk_manager.draw_chunks(screen, testSurf.world_x, testSurf.world_y, screen_center, zoom=1)
    obstacle_manager.draw_chunks(screen, testSurf.world_x, testSurf.world_y, screen_center, zoom=1)

    # If there's no player, just draw the island plainly
    players = list(playerGroup.sprites())
    
    

    # We'll use the first player as the camera anchor
    player = players[0]
    camera_x = player.world_x
    camera_y = player.world_y


    # 2) Draw each sprite in playerGroup
    for sp in playerGroup.sprites():
        sw = sp.scaled_image.get_width()
        sh = sp.scaled_image.get_height()
        off_x = (sp.world_x - camera_x) * c.ZOOM_FACTOR
        off_y = (sp.world_y - camera_y) * c.ZOOM_FACTOR
        # Center the sprite on the offset
        sx = screen_center[0] + off_x - sw / 2
        sy = screen_center[1] + off_y - sh / 2
        zoomSurf.blit(sp.scaled_image, (sx, sy))

    # 3) Draw text
    for t in surface.textSurface.instances:
        zoomSurf.blit(t.image, t.rect)






########################################
# PyGame Custom Userevents
########################################
zombie_spawn_event = pygame.USEREVENT+1
pygame.time.set_timer(zombie_spawn_event, 1000)

game_tick_event = pygame.USEREVENT+2
pygame.time.set_timer(game_tick_event, math.floor(1000/60))





########################################
# Main Loop
########################################
while c.GAME_IS_RUNNING:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            c.GAME_IS_RUNNING = False

        elif event.type == pygame.WINDOWRESIZED:
            info = pygame.display.Info()
            screen = pygame.display.set_mode((info.current_w, info.current_h), flags)
            zoomSurf = pygame.Surface((info.current_w, info.current_h))
            screen_center = (info.current_w // 2, info.current_h // 2)

        elif event.type == pygame.KEYUP:
            # Press SPACE to zoom in
            if event.key == pygame.K_SPACE:
                c.ZOOM_FACTOR += 0.05
                # Only re-scale once, not every frame
                rescale_all(c.ZOOM_FACTOR)
        
        elif event.type == zombie_spawn_event:
            world_x, world_y = random_point_on_circle(testSurf.world_x, testSurf.world_y, 500)
            surface.Surface("assets/img/zomb.png", (100, 100), world_x, world_y, playerGroup)
            
        elif event.type == game_tick_event:
            keys = pygame.key.get_pressed()
            if keys[K_UP]:
                testSurf.world_y += charControls[K_UP][1]
            if keys[K_DOWN]:
                testSurf.world_y += charControls[K_DOWN][1]
            if keys[K_LEFT]:
                testSurf.world_x += charControls[K_LEFT][0]
            if keys[K_RIGHT]:
                testSurf.world_x += charControls[K_RIGHT][0]
            

    # Handle movement in world coords



    chunk_pixel_w = chunk_manager.chunk_width_tiles * chunk_manager.tile_size
    chunk_pixel_h = chunk_manager.chunk_height_tiles * chunk_manager.tile_size

    cx = testSurf.world_x // chunk_pixel_w
    cy = testSurf.world_y // chunk_pixel_h
    #pchunk = chunk_manager.get_chunk(cx, cy)
    #obs_chunk = obstacle_manager.get_chunk(cx, cy)

    local_x = (testSurf.world_x % chunk_pixel_w) // tile_size
    local_y = (testSurf.world_y % chunk_pixel_h) // tile_size

    #biome = pchunk.biome_data[local_y][local_x] 
    #collision_map = obs_chunk.collision_map[local_y][local_x]
    #print(pchunk.collision_map)

    #print(collision_map)
    #print(biome)

    for nx in [cx-2, cx-1, cx, cx+1, cx+2]:
        for ny in [cy-2, cy-1, cy, cy+1, cy+2]:
            chunk_manager.get_chunk(nx, ny)
            obstacle_manager.get_chunk(nx, ny)

    # Build the frame
    draw_all()

    
    # Blit the result to the screen
    screen.blit(zoomSurf, (0,0))
    #screen.blit(s, (0,0))

    # Update text surfaces
    for t in surface.textSurface.instances:
        t.update_text(clock.get_fps())

    pygame.display.flip()
    clock.tick()

pygame.quit()