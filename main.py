import pygame
import config as c
import os
import surface
import noiseGen
import math
from pygame.locals import *
import random
import heapq
import music
import time
import save

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

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle, speed, bullet_size = 5):
        super().__init__()
        self.image = pygame.Surface((bullet_size, bullet_size))  # Bullet size
        self.image.fill((255, 0, 0))  # Red bullet for simplicity
        self.radius = bullet_size/2
        self.scaled_image = self.image
        self.world_x = x
        self.world_y = y
        self.rect = self.image.get_rect()
        self.angle = angle
        self.speed = speed
        self.dx = speed * math.cos(math.radians(angle))
        self.dy = speed * math.sin(math.radians(angle))

    def update(self):
        # Move the bullet
        new_pos_x = self.world_x + self.dx
        new_pos_y = self.world_y + self.dy

        # Check if the next position is walkable
        if not can_move_to(new_pos_x, new_pos_y, obstacle_manager):
            self.kill()  # Kill the bullet if it hits an obstacle
            return
        
        for zomb in zombie_manager.zomb_list:
            if circle_collision(zomb, self):
                zomb.health-= c.AK47_DMG + c.AK47_DMG/4*random.random()
                if zomb.health <= 0:
                    updateScore(1)
                    zomb.kill()
                    zombie_manager.zomb_list.remove(zomb)
                self.kill()

        # If no collision, update the position
        self.world_x += self.dx
        self.world_y += self.dy

def updateScore(amt):
    global total_score
    total_score+=amt

    scoreText.update_text(total_score)


class BulletManager:
    def __init__(self):
        self.bullets = pygame.sprite.Group()

    def shoot(self, x, y, angle, speed):
        bullet = Bullet(x, y, angle, speed)
        music.sound_manager.playSound("ak47")
        self.bullets.add(bullet)

    def update(self):
        self.bullets.update()

class Zombie(surface.Surface):
    def __init__(self, imageUrl, size, world_x, world_y, radius, health, cooldown, *groups):
        super().__init__(imageUrl, size, world_x, world_y, *groups)
        self.world_x = world_x
        self.world_y = world_y
        self.health = health
        self.cooldown = cooldown
        self.time_last_attack = time.time()

        self.radius = radius
        self.path = None

class ZombieManager:
    def __init__(self):
        self.zomb_list = []

    def add_zombie(self, center_x, center_y, zombie=None):
        def get_x_and_y():
            while True:
                x, y = random_point_on_circle(center_x, center_y, c.ZOMBIE_SPAWN_DISTANCE)
                if can_move_to(x, y, obstacle_manager):
                    return x, y
        if zombie is None:

            x, y = get_x_and_y()              
            self.zomb_list.append(Zombie("assets/img/zomb.png", (c.ZOMBIE_RADIUS*2, c.ZOMBIE_RADIUS*2), x, y, c.ZOMBIE_RADIUS, c.ZOMBIE_HEALTH, c.ZOMBIE_COOLDOWN, playerGroup))
            return
        
        self.zomb_list.append(zombie)
    
    def check_for_player_collision(self, player, zombie):
        if circle_collision(player, zombie, c.ZOMBIE_REACH):
            current_time = time.time()
            if current_time-zombie.time_last_attack >= zombie.cooldown:
                #music.sound_manager.playSound("zombie")
                zombie.time_last_attack = current_time
                player.health -= c.ZOMBIE_DAMAGE + c.ZOMBIE_DAMAGE/3*random.random()
                if player.health <= 0:
                    c.GAME_IS_RUNNING = False
                    return # Do dead stuff
                health_bar.image = pygame.Surface((health_bar.w*player.health/c.PLAYER_HEALTH, health_bar.h))
                health_bar.image.fill((255, 0, 0))
    
    def update_zombie_movement(self):
        player_pos = (testSurf.world_x, testSurf.world_y)
        for zombie in self.zomb_list:
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

                dx, dy = compute_move_towards(zombie_position, next_tile_world, c.ZOMBIE_SPEED+random.randint(0, 7))
                
                zombie.world_x += dx
                zombie.world_y += dy
                # If reached the next tile, remove it from path
                if zombie_position == next_tile_world:
                    zombie.path.pop(0)
            
            self.check_for_player_collision(testSurf, zombie)
                

            

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

def circle_collision(spriteA, spriteB, extraRadius = 0):
    """
    Returns True if spriteA and spriteB collide based on their circular bounding boxes.
    The sprites should have the attributes: world_x, world_y, and radius.
    
    :param spriteA: First sprite
    :param spriteB: Second sprite
    :return: True if the circles overlap (collide), False otherwise
    """
    # Calculate the distance between the centers of the two circles
    dx = spriteB.world_x - spriteA.world_x
    dy = spriteB.world_y - spriteA.world_y
    distance = math.sqrt(dx**2 + dy**2)

    # Get the sum of the radii of both circles
    radius_sum = spriteA.radius + spriteB.radius + extraRadius

    # If the distance is less than or equal to the sum of the radii, they are colliding
    return distance <= radius_sum

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


total_score = 0  
scoreSaveArr = save.getRawData("saves/score.pickle")
highscore = dict(scoreSaveArr).get("Highscore", 0)
print(highscore)

chunk_manager = ChunkManager(chunk_width_tiles=50, chunk_height_tiles=50,
                                 tile_size=10, scale=150.0, seed=42)
obstacle_manager = ChunkManager(chunk_width_tiles=50, chunk_height_tiles=50,
                                 tile_size=10, scale=10.0, seed=42, isBiomeMap=False)


pathfinder = Pathfinder(obstacle_manager, obstacle_manager.chunk_height_tiles, obstacle_manager.tile_size)

bullet_manager = BulletManager()

zombie_manager = ZombieManager()

########################################
# 2) Create a 'player' sprite
########################################
gun_surf = surface.Surface("assets/img/ak47.png", (25, 112.5), info.current_w // 2, info.current_h // 2, playerGroup)

testSurf = surface.Surface("assets/img/player.png", (c.PLAYER_RADIUS*2, c.PLAYER_RADIUS*2), info.current_w // 2, info.current_h // 2, playerGroup)
testSurf.health = c.PLAYER_HEALTH
testSurf.radius = c.PLAYER_RADIUS

musicTest = music.MusicWithQueue("main")
musicTest.playMusic()

health_bar = surface.RectSprite(0, 0, 300, 50, (255, 0, 0))
health_bar.rect.topright = (info.current_w - 50, 50)

# For demonstration, a text surface
fps_text = surface.textSurface()

titleText = surface.textSurface(text="Goonz Royale")
titleText.rect.midtop = (info.current_w/2, 0)

scoreText = surface.textSurface(text=str(total_score))
scoreText.rect.midbottom = (info.current_w/2, info.current_h)

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


def can_move_to(obj_x, obj_y, chunk_manager):
    # 1) Identify chunk coords
    chunk_pixel_w = chunk_manager.chunk_width_tiles * chunk_manager.tile_size
    chunk_pixel_h = chunk_manager.chunk_height_tiles * chunk_manager.tile_size

    cx = obj_x // chunk_pixel_w
    cy = obj_y // chunk_pixel_h

    chunk = chunk_manager.get_chunk(cx, cy)
    if not chunk:
        return False  # if chunk not loaded or out of range?

    # 2) local tile coords
    local_x = int((obj_x % chunk_pixel_w) // chunk_manager.tile_size)
    local_y = int((obj_y % chunk_pixel_h) // chunk_manager.tile_size)

    # 3) check collision
    if chunk.collision_map[local_y][local_x]:
        # It's blocked
        return False
    return True

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




def update_gun_position(player, gun_surf, rotation_angle, offset_distance=35):
    """
    Updates the gun's position relative to the player and rotates the gun to face the player's direction.

    Parameters:
    - player: The player object (assumed to have `world_x` and `world_y` attributes).
    - gun_surf: The gun surface object (assumed to have `original_image`, `image`, and `rect` attributes).
    - rotation_angle: The angle in radians (the direction the player is facing).
    - offset_distance: The distance the gun should be offset from the player (default 30).
    """
    
    # Get the player's position
    player_x, player_y = player.world_x, player.world_y
    gun_surf.angle = rotation_angle-90

    # Calculate the gun's position based on the player's position and rotation
    gun_offset_x = offset_distance * math.cos(math.radians(rotation_angle))
    gun_offset_y = offset_distance * math.sin(math.radians(rotation_angle))

    # Update the gun's world position
    gun_surf.world_x = player_x + gun_offset_x
    gun_surf.world_y = player_y + gun_offset_y

    # Rotate the gun image to match the player's facing direction
    rotated_image = pygame.transform.rotate(gun_surf.original_image, -rotation_angle)

    # Update the gun's surface
    gun_surf.scaled_image = rotated_image

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

    def scale_and_blit_zoom_surface(sp):
        sw = sp.scaled_image.get_width()
        sh = sp.scaled_image.get_height()
        off_x = (sp.world_x - camera_x) * c.ZOOM_FACTOR
        off_y = (sp.world_y - camera_y) * c.ZOOM_FACTOR
        # Center the sprite on the offset
        sx = screen_center[0] + off_x - sw / 2
        sy = screen_center[1] + off_y - sh / 2
        zoomSurf.blit(sp.scaled_image, (sx, sy))

    zoomSurf.fill((0,0,0))
    chunk_manager.draw_chunks(screen, testSurf.world_x, testSurf.world_y, screen_center, zoom=c.ZOOM_FACTOR)
    obstacle_manager.draw_chunks(screen, testSurf.world_x, testSurf.world_y, screen_center, zoom=c.ZOOM_FACTOR)
    
    # We'll use the first player as the camera anchor
    player = testSurf
    camera_x = player.world_x
    camera_y = player.world_y


    for sp in bullet_manager.bullets.sprites():
        scale_and_blit_zoom_surface(sp)

    # 2) Draw each sprite in playerGroup
    for sp in playerGroup.sprites():
        scale_and_blit_zoom_surface(sp)

    # 3) Draw text
    for t in surface.textSurface.instances:
        zoomSurf.blit(t.image, t.rect)
    
    for r in surface.RectSprite.instances:
        zoomSurf.blit(r.image, r.rect)




########################################
# PyGame Custom Userevents
########################################
zombie_spawn_event = pygame.USEREVENT+1
pygame.time.set_timer(zombie_spawn_event, c.ZOMBIE_SPAWN_DELAY_MS)

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
                bullet_manager.shoot(gun_surf.world_x, gun_surf.world_y, gun_surf.angle, 15)  # shoot bullets
                
                """Example of how the zoom function could work if Space is pressed"""
                #c.ZOOM_FACTOR += 0.05
                # Only re-scale once, not every frame
                #rescale_all(c.ZOOM_FACTOR)
        
        elif event.type == zombie_spawn_event:
            if len(Zombie.instances)<c.ZOMBIES_PER_WAVE:
                zombie_manager.add_zombie(testSurf.world_x, testSurf.world_y)
            
        elif event.type == game_tick_event:
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            for k, v in charControls.items():
                if keys[k]:
                    dx+=v[0]
                    dy+=v[1]
            bullet_manager.update()
            move_circle_player(testSurf, dx, dy, obstacle_manager)
            zombie_manager.update_zombie_movement()
            

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
    ang = get_angle(mouse_x-1/2*info.current_w, mouse_y-1/2*info.current_h)+90
    testSurf.scaled_image = pygame.transform.rotate(testSurf.original_image, -ang)
    update_gun_position(testSurf, gun_surf, ang, 50)
    
    #biome = pchunk.biome_data[local_y][local_x] 
    #collision_map = obs_chunk.collision_map[local_y][local_x]


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
    fps_text.update_text("FPS: "+str(math.floor(clock.get_fps())))

    pygame.display.flip()
    clock.tick()


highscore_save = max(total_score, highscore)
save.saveData("saves/score.pickle", {("Highscore", highscore_save)})

pygame.quit()