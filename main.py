import pygame
import config as c
import os
import surface
from collections import Counter
import noiseGen
import math
from pygame.locals import *
import random
import heapq

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
    K_w: (0, -c.PLAYER_SPEED),
    K_s: (0, c.PLAYER_SPEED),
    K_d: (c.PLAYER_SPEED, 0),
    K_a: (-c.PLAYER_SPEED, 0)
}

tile_size = 10
map_height = math.ceil(info.current_h / tile_size)
map_width = math.ceil(info.current_w / tile_size)
scale = 10.0

# Generate a biome map
biome_map = noiseGen.get_biome_map(map_width, map_height, scale)

# Sprite groups
playerGroup = pygame.sprite.RenderUpdates()
zombListTest = []

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
                print("cuh")
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

def compute_move_towards(pos, dest, speed):
    pos_x, pos_y = pos
    dest_x, dest_y = dest
    """
    Computes a movement step (dx, dy) so that a zombie (or any entity) at (pos_x, pos_y)
    moves towards (dest_x, dest_y) by up to 'speed' units.

    Returns:
       (move_x, move_y) - the step vector along the hypotenuse 
                          from the current position to the destination, 
                          with magnitude <= speed.
    """
    dx = dest_x - pos_x
    dy = dest_y - pos_y

    dist = math.hypot(dx, dy)
    if dist == 0:
        # Already at the destination
        return (0, 0)

    if dist <= speed:
        # We can directly reach or exceed the destination in one step
        return (dx, dy)
    else:
        # Scale the direction to have length exactly 'speed'
        scale = speed / dist
        return (dx * scale, dy * scale)

class Pathfinder:
    def __init__(self, world, chunk_size, tile_size):
        self.world = world
        self.chunk_size = chunk_size
        self.tile_size = tile_size

    def is_walkable(self, x, y):
        # Same implementation as above, but using self.world and self.chunk_size
        cx = x // self.chunk_size
        cy = y // self.chunk_size
        chunk = self.world.get_chunk(cx, cy)
        if chunk is None:
            return False
        local_x = int(x % self.chunk_size)
        local_y = int(y % self.chunk_size)
        if local_x < 0:
            local_x += self.chunk_size
        if local_y < 0:
            local_y += self.chunk_size
        #print(local_y, local_x)
        return not chunk.collision_map[local_y][local_x]

    def find_path(self, start_world, goal_world):
        start_x, start_y = start_world
        goal_x, goal_y = goal_world

        sx = int(start_x // self.tile_size)
        sy = int(start_y // self.tile_size)
        gx = int(goal_x // self.tile_size)
        gy = int(goal_y // self.tile_size)

        # Quick reject: if target tile is not walkable, return empty path
        if self.is_walkable(gx, gy) == False:
            return []
        # A* search initialization
        open_set = []
        heapq.heappush(open_set, (0 + math.hypot(gx - sx, gy - sy), 0, sx, sy))
        came_from = {}           # maps node (x,y) to parent (x,y)
        cost_so_far = { (sx, sy): 0 }
        # Directions (8-connected grid)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                      (-1, -1), (-1, 1), (1, -1), (1, 1)]
        while open_set:
            _, g, x, y = heapq.heappop(open_set)
            # If this node is the goal, reconstruct path
            if (x, y) == (gx, gy):
                path = [(gx, gy)]
                # Follow parents back to start
                while (x, y) in came_from:
                    (x, y) = came_from[(x, y)]
                    path.append((x, y))
                path.reverse()
                return path
            # Skip if we already processed this node with a lower cost
            if cost_so_far.get((x, y), float('inf')) < g:
                continue
            # Examine neighbors
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                # Check walkability
                if not self.is_walkable(nx, ny):
                    continue
                # Prevent diagonal moves through walls
                if dx != 0 and dy != 0:
                    if not self.is_walkable(x + dx, y) or not self.is_walkable(x, y + dy):
                        continue
                # Calculate new cost to neighbor
                step_cost = math.hypot(dx, dy)
                new_cost = g + step_cost
                # Only consider this new path if it's better than any prior known path to neighbor
                if new_cost < cost_so_far.get((nx, ny), float('inf')):
                    cost_so_far[(nx, ny)] = new_cost
                    priority = new_cost + math.hypot(gx - nx, gy - ny)  # f = g + h
                    heapq.heappush(open_set, (priority, new_cost, nx, ny))
                    came_from[(nx, ny)] = (x, y)
        # If open_set is empty and goal was never reached, return no path
        return []



chunk_manager = ChunkManager(chunk_width_tiles=50, chunk_height_tiles=50,
                                 tile_size=10, scale=150.0, seed=42)
obstacle_manager = ChunkManager(chunk_width_tiles=50, chunk_height_tiles=50,
                                 tile_size=10, scale=10.0, seed=42, isBiomeMap=False)


pathfinder = Pathfinder(obstacle_manager, obstacle_manager.chunk_height_tiles, obstacle_manager.tile_size)


########################################
# 2) Create a 'player' sprite
########################################
gun_surf = surface.Surface("assets/img/ak47.png", (25, 112.5), info.current_w // 2, info.current_h // 2, playerGroup)

testSurf = surface.Surface("assets/img/zomb.png", (100, 100), info.current_w // 2, info.current_h // 2, playerGroup)

gun_surf.rect.midbottom = (testSurf.world_x, testSurf.world_y)

# For demonstration, a text surface
testText = surface.textSurface()

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


def can_move_to(player_x, player_y, chunk_manager):
    # 1) Identify chunk coords
    chunk_pixel_w = chunk_manager.chunk_width_tiles * chunk_manager.tile_size
    chunk_pixel_h = chunk_manager.chunk_height_tiles * chunk_manager.tile_size

    cx = player_x // chunk_pixel_w
    cy = player_y // chunk_pixel_h

    chunk = chunk_manager.get_chunk(cx, cy)
    if not chunk:
        return False  # if chunk not loaded or out of range?

    # 2) local tile coords
    local_x = (player_x % chunk_pixel_w) // chunk_manager.tile_size
    local_y = (player_y % chunk_pixel_h) // chunk_manager.tile_size

    # 3) check collision
    if chunk.collision_map[local_y][local_x]:
        # It's blocked
        return False
    return True

def move_player(player, dx, dy, chunk_manager):
    if dx == 0 and dy == 0:
        print("no movement")
        return
    new_x = player.world_x + dx
    new_y = player.world_y + dy

    # Optionally check all corners if you do bounding-box collision
    if can_move_to(new_x, new_y, chunk_manager):
        # It's free, so move
        player.world_x = new_x
        player.world_y = new_y
    else:
        # Collides
        pass

def get_angle(x, y):
    """
    Returns the angle (in degrees) for the triangle sides x and y,
    i.e. the angle of the vector (x, y) relative to the positive X-axis.
    """
    angle_radians = math.atan2(y, x)      # angle in radians between -π and π
    angle_degrees = math.degrees(angle_radians)
    return angle_degrees

def circle_vs_aabb(cx, cy, r, box_x, box_y, box_w, box_h):
    """
    Resolve collision between a circle at (cx, cy, radius=r) and an axis-aligned box 
    at (box_x, box_y) with size (box_w, box_h).

    Returns (px, py) = minimal push vector to separate them, or (0, 0) if no collision.

    Steps:
      1) Find the closest point in the box to the circle center by clamping.
      2) If distance < r, compute overlap and push out by that overlap along the direction.
    """
    # Closest point on box to circle center
    closest_x = min(max(cx, box_x), box_x + box_w)
    closest_y = min(max(cy, box_y), box_y + box_h)

    # Dist from circle center to that point
    dist_x = cx - closest_x
    dist_y = cy - closest_y
    dist_sqr = dist_x*dist_x + dist_y*dist_y

    r_sqr = r*r
    if dist_sqr >= r_sqr:
        return (0, 0)  # No collision

    dist = math.sqrt(dist_sqr) or 0.000001
    overlap = r - dist
    # Normalize (dist_x, dist_y)
    nx = dist_x / dist
    ny = dist_y / dist

    # push vector
    px = nx * overlap
    py = ny * overlap
    return (px, py)

def update_zombie_movement():
    player_pos = (testSurf.world_x, testSurf.world_y)
    for zombie in zombListTest:
        zombie_position = (zombie.world_x, zombie.world_y)
        # Determine if we need to update the path for this zombie
        if zombie.path == [] or not zombie.path: 
            # no current path, compute one
            zombie.path = pathfinder.find_path(zombie_position, player_pos)
            zombie.target_last_seen = player_pos
        else:
            # If player has moved far from last seen position or at regular intervals, recompute path
            dist_to_last = math.hypot(player_pos[0] - zombie.target_last_seen[0],
                                       player_pos[1] - zombie.target_last_seen[1])
            if dist_to_last > 125:  # example threshold in tiles
                zombie.path = pathfinder.find_path(zombie_position, player_pos)
                zombie.target_last_seen = player_pos

        # If a path exists, move the zombie along the path
        if zombie.path:
            next_tile = zombie.path[0]
            next_tile_world = (next_tile[0]*10, next_tile[1]*10)
            # Move zombie towards next_tile (instant move or interpolate movement here)

            dx, dy = compute_move_towards(zombie_position, next_tile_world, c.PLAYER_SPEED+random.randint(0, 7))
            
            zombie.world_x += dx
            zombie.world_y += dy
            # If reached the next tile, remove it from path
            if zombie_position == next_tile_world:
                zombie.path.pop(0)

def move_circle_player(player, dx, dy, chunk_manager, passes=5):
    """
    Move a circle-based player by (dx, dy) with multiple resolution passes 
    for smooth sliding. We do chunk-based collision checks 
    so we correctly index collision_map in local tile space.
    """

    if dx == 0 and dy == 0:
        return
    
    # 1) Predict new center
    cx = player.world_x + dx
    cy = player.world_y + dy
    r = 35  # or a fixed 50 if that’s your circle radius

    # We'll do multiple passes for corner sliding
    for _ in range(passes):
        # (A) Circle bounding box in world coords
        circle_left   = cx - r
        circle_right  = cx + r
        circle_top    = cy - r
        circle_bottom = cy + r

        # (B) For each loaded chunk, check overlap + do collisions
        for (chunk_cx, chunk_cy), chunk in chunk_manager.chunks.items():
            # The chunk’s bounding box in world coords
            chunk_left   = chunk.rect.x
            chunk_top    = chunk.rect.y
            chunk_right  = chunk_left + chunk.rect.width
            chunk_bottom = chunk_top  + chunk.rect.height

            # If bounding boxes don’t intersect, skip
            if (circle_right < chunk_left or circle_left > chunk_right or
                circle_bottom < chunk_top or circle_top > chunk_bottom):
                continue

            # (C) find local tile range inside chunk
            chunk_w = chunk_manager.chunk_width_tiles
            chunk_h = chunk_manager.chunk_height_tiles
            tsize   = chunk_manager.tile_size

            # offset of chunk in world space
            ox = chunk.rect.x
            oy = chunk.rect.y

            # min/max tile index in chunk local coords
            local_left   = int((circle_left   - ox)//tsize)
            local_right  = int((circle_right  - ox)//tsize)
            local_top    = int((circle_top    - oy)//tsize)
            local_bottom = int((circle_bottom - oy)//tsize)

            # clamp to [0..chunk_w-1, 0..chunk_h-1]
            local_left   = max(0, min(local_left,   chunk_w-1))
            local_right  = max(0, min(local_right,  chunk_w-1))
            local_top    = max(0, min(local_top,    chunk_h-1))
            local_bottom = max(0, min(local_bottom, chunk_h-1))

            # (D) For each blocked tile in that local range, do circle–box
            for ty in range(local_top, local_bottom+1):
                for tx in range(local_left, local_right+1):
                    if chunk.collision_map[ty][tx]:
                        # tile bounding box in world coords
                        tile_world_x = ox + tx * tsize
                        tile_world_y = oy + ty * tsize

                        px, py = circle_vs_aabb(cx, cy, r,
                                                tile_world_x, tile_world_y,
                                                tsize, tsize)
                        if px != 0 or py != 0:
                            cx += px
                            cy += py
                            # Because circle center changed, we might overlap a new tile,
                            # but we rely on additional 'passes' to fix that.

    # 2) Commit final center
    player.world_x = cx
    player.world_y = cy

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
    player = testSurf
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
                pass
                #c.ZOOM_FACTOR += 0.05
                # Only re-scale once, not every frame
                #rescale_all(c.ZOOM_FACTOR)
        
        elif event.type == zombie_spawn_event:
            if len(zombListTest)<20:
                world_x, world_y = random_point_on_circle(testSurf.world_x, testSurf.world_y, 500)
                new_zomb = surface.Surface("assets/img/zomb.png", (100, 100), world_x, world_y, playerGroup)
                new_zomb.path = None
                zombListTest.append(new_zomb)
            
        elif event.type == game_tick_event:
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            for k, v in charControls.items():
                if keys[k]:
                    dx+=v[0]
                    dy+=v[1]
            move_circle_player(testSurf, dx, dy, obstacle_manager)
            gun_surf.world_x = testSurf.world_x+30
            gun_surf.world_y = testSurf.world_y-20
            update_zombie_movement()
            

    # Handle movement in world coords



    chunk_pixel_w = chunk_manager.chunk_width_tiles * chunk_manager.tile_size
    chunk_pixel_h = chunk_manager.chunk_height_tiles * chunk_manager.tile_size

    cx = testSurf.world_x // chunk_pixel_w
    cy = testSurf.world_y // chunk_pixel_h
    pchunk = chunk_manager.get_chunk(cx, cy)
    obs_chunk = obstacle_manager.get_chunk(cx, cy)

    local_x = (testSurf.world_x % chunk_pixel_w) // tile_size
    local_y = (testSurf.world_y % chunk_pixel_h) // tile_size

    mouse_x, mouse_y = pygame.mouse.get_pos()
    ang = get_angle(mouse_x-1/2*info.current_w, mouse_y-1/2*info.current_h)
    testSurf.scaled_image = pygame.transform.rotate(testSurf.original_image, -ang-90)
    
    #print(ang)
    #testSurf.image = pygame.transform.rotate(testSurf.image, ang)
    


    # ... rest of game loop ...

    #biome = pchunk.biome_data[local_y][local_x] 
    #collision_map = obs_chunk.collision_map[local_y][local_x]

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
        t.update_text(math.floor(clock.get_fps()))

    pygame.display.flip()
    clock.tick()

pygame.quit()