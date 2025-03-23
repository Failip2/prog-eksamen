# Loke har skrevet ZombieManager og Zombie class (ikke pathfinding til zombierne)
# Filip har skrevet resten

# Import necessary modules and libraries
import pygame
import config as c
import os
import surface
import math
from pygame.locals import *
import random
import heapq
import music
import time
import save
import game_chunks
import types
import noiseGen
from itertools import count

# Define the Player class, inheriting from surface.Surface
# This class is used to store health and radius values for the player
class Player(surface.Surface):
    def __init__(self, *groups):
        # Initialize the parent class with player image, size, and position
        super().__init__("assets/img/player.png", 
                        (c.PLAYER_RADIUS*2, c.PLAYER_RADIUS*2),
                        info.current_w // 2, info.current_h // 2,
                        *groups)
        # Set the player's health and radius from the config
        self.health = c.PLAYER_HEALTH
        self.radius = c.PLAYER_RADIUS

# Define the Weapon class, inheriting from surface.Surface
# This class is used to simplify code and make it more expandable
class Weapon(surface.Surface):
    def __init__(self, *groups):
        # Initialize the parent class with weapon image, size, and position
        super().__init__("assets/img/ak47.png", 
                        c.AK47_SIZE,
                        info.current_w // 2, info.current_h // 2,
                        *groups)

# On game start or restart -> reset_game(). This is so we can easily reset all the given global variables, and clear all the Manager classes.
def reset_game(game_player, bullet_manager, zombie_manager, chunk_manager, obstacle_manager, health_bar):
    # Define what global variables we are working with
    global task_queue, timeAtStart, total_score

    # Reset the total score to 0 and record the current time to track game duration
    total_score = 0
    timeAtStart = time.time()
    
    # Reposition the player to the center of the screen and reset their health
    game_player.world_x = info.current_w // 2
    game_player.world_y = info.current_h // 2
    game_player.health = c.PLAYER_HEALTH

    # Reset the health bar image to its original state
    health_bar.image = health_bar.original_image
    
    # Update the score text to reflect the reset score
    scoreText.update_text("Score: "+str(total_score))
    
    # Clear all zombies and bullets to ensure a fresh start
    zombie_manager.reset()
    if hasattr(Zombie, 'instances'):
        for zomb in Zombie.instances:
            zomb.kill()

    bullet_manager.bullets.empty()

    # Initialize a new task queue and assign it to chunk and obstacle managers
    # This ensures that all tasks are reset and managed consistently
    task_queue = TaskQueue(high_priority_cutoff=0)
    chunk_manager.task_queue = task_queue
    obstacle_manager.task_queue = task_queue

    # Unload all chunks to free up memory and allow new chunks to be generated with a new seed
    chunk_manager.unload_all_chunks()

# Reset cached gradients in noise generator to allow new generation of gradients with a new WORLD_SEED
# This ensures that the noise patterns used for terrain generation are fresh and unique for each game session
noiseGen.reset_noise()

# Define player controls to avoid code duplication
# This dictionary maps key presses to player movement vectors, making it easier to handle movement logic
charControls = {
    K_w: (0, -c.PLAYER_SPEED),
    K_s: (0, c.PLAYER_SPEED),
    K_d: (c.PLAYER_SPEED, 0),
    K_a: (-c.PLAYER_SPEED, 0)
}

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle, speed, bullet_size=5):
        super().__init__()
        # Create a surface for the bullet with the specified size
        self.image = pygame.Surface((bullet_size, bullet_size))
        # Fill the bullet surface with red color for visibility
        self.image.fill((255, 0, 0))
        self.radius = bullet_size / 2
        self.scaled_image = self.image
        self.world_x = x
        self.world_y = y
        self.rect = self.image.get_rect()
        self.angle = angle
        self.speed = speed
        # Calculate the change in position per update based on the angle and speed
        self.dx = speed * math.cos(math.radians(angle))
        self.dy = speed * math.sin(math.radians(angle))

    def update(self):
        # Calculate the new position of the bullet
        new_pos_x = self.world_x + self.dx
        new_pos_y = self.world_y + self.dy

        # Check if the next position is walkable to prevent the bullet from moving through obstacles
        if not can_move_to(new_pos_x, new_pos_y, obstacle_manager):
            # Play a sound effect when the bullet hits a wall
            music.sound_manager.playSound("bullet_wall")
            # Remove the bullet from the game if it hits an obstacle
            self.kill()
            return

        # Check for collisions with zombies
        for zomb in zombie_manager.zomb_list:
            if circle_collision(zomb, self):
                # Play a sound effect when the bullet hits a zombie
                music.sound_manager.playSound("zomb_hit")
                # Reduce the zombie's health by a random amount within a specified range
                zomb.health -= c.AK47_DMG + c.AK47_DMG / 4 * random.random()
                if zomb.health <= 0:
                    # Play a sound effect when the zombie dies
                    music.sound_manager.playSound("zomb_death")
                    # Update the score when a zombie is killed
                    updateScore(1)
                    # Remove the zombie from the game and the zombie manager's list
                    zomb.kill()
                    zombie_manager.zomb_list.remove(zomb)
                # Remove the bullet after it hits a zombie
                self.kill()

        # If no collision occurs, update the bullet's position
        self.world_x += self.dx
        self.world_y += self.dy

def updateScore(amt):
    global total_score
    # Increment the total score by the specified amount
    total_score += amt
    # Update the score display text
    scoreText.update_text("Score: " + str(total_score))

class BulletManager:
    def __init__(self):
        # Initialize a group to manage all bullets
        self.bullets = pygame.sprite.Group()
        # Track the time since the last bullet was fired
        self.time_since_last_bullet = 0

    def shoot(self, x, y, angle, speed):
        # Record the current time to manage bullet firing rate
        current_time = time.time()

        # Check if enough time has passed since the last bullet was fired
        # This ensures that the firing rate of the weapon is respected
        if current_time - self.time_since_last_bullet > 1 / (c.AK47_RPM / 60):
            # Create a new bullet instance with the given position, angle, and speed
            bullet = Bullet(x, y, angle, speed)
            # Play the sound effect for firing the weapon
            music.sound_manager.playSound("ak47")
            # Add the new bullet to the bullet manager's group
            self.bullets.add(bullet)
            # Update the time of the last bullet fired to the current time
            self.time_since_last_bullet = current_time

    def update(self):
        # Update the position and state of all bullets managed by the bullet manager
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

        # Set the interval for path updates to balance performance and responsiveness
        self.path_update_interval = 0.5
        self.last_path_update = 0

        # Add a small random variation to the path update interval to avoid synchronization issues
        self.path_update_interval += random.uniform(-0.1, 0.1)

class ZombieManager:
    def __init__(self, zombies_per_wave, wave_multiplier):
        self.zomb_list = []
        self.zombies_spawned = 0
        self.zombies_per_wave_original = zombies_per_wave
        self.zombies_per_wave = self.zombies_per_wave_original
        self.wave_multiplier = wave_multiplier

    def add_new_path_task(self, zombie, zombie_position, player_pos):
        """Helper function to be sent into TaskQueue"""
        zombie.path = pathfinder.find_path(zombie_position, player_pos)

    def add_zombie(self, center_x, center_y, zombie=None):
        """Try to add a new zombie at a random point (x, y) based off a random circle radius from (center_x, center_y)"""
        def get_x_and_y():
            while True:
                x, y = random_point_on_circle(center_x, center_y, c.ZOMBIE_SPAWN_DISTANCE)
                if can_move_to(x, y, obstacle_manager):
                    return x, y
                else:
                    return None, None
        if self.zombies_spawned >= self.zombies_per_wave:
            if self.zomb_list:
                return
            self.zombies_spawned = 0
            self.zombies_per_wave = math.ceil(self.zombies_per_wave*self.wave_multiplier)

        if zombie is None:
            
            x, y = get_x_and_y()  
            if x == None:
                return            
            self.zomb_list.append(Zombie("assets/img/zomb.png", (c.ZOMBIE_RADIUS*2, c.ZOMBIE_RADIUS*2), x, y, c.ZOMBIE_RADIUS, c.ZOMBIE_HEALTH, c.ZOMBIE_COOLDOWN, playerGroup))
            self.zombies_spawned+=1
            return
        self.zombies_spawned+=1
        self.zomb_list.append(zombie)
    
    def reset(self):
        self.zomb_list.clear()
        self.zombies_spawned = 0
        self.zombies_per_wave = self.zombies_per_wave_original
    
    def check_for_player_collision(self, player, zombie):
        if circle_collision(player, zombie, c.ZOMBIE_REACH):
            current_time = time.time()
            if current_time-zombie.time_last_attack >= zombie.cooldown:
                music.sound_manager.playSound("zombie")
                zombie.time_last_attack = current_time

                # Random damage variation (1/3 of base damage) prevents
                # perfectly predictable combat outcomes
                player.health -= c.ZOMBIE_DAMAGE + c.ZOMBIE_DAMAGE/3*random.random()

                if player.health <= 0:
                    # Player is dead
                    global highscore, current_scene
                    highscore = max(highscore, total_score)

                    current_scene = END_SCREEN
                    return
                
                health_bar.image = pygame.Surface((health_bar.w*player.health/c.PLAYER_HEALTH, health_bar.h))
                health_bar.image.fill((255, 0, 0))
    
    def update_zombie_movement(self):
        current_time = time.time()
        player_pos = (game_player.world_x, game_player.world_y)
        
        for zombie in self.zomb_list:
            # Only recalculate path if cooldown expired
            if current_time - zombie.last_path_update > zombie.path_update_interval:
                self.update_zombie_path(zombie, player_pos)
                zombie.last_path_update = current_time
                
            self.move_zombie(zombie)
            self.check_for_player_collision(game_player, zombie)

    def update_zombie_path(self, zombie, player_pos):
        """Handle path recalculation for a single zombie"""
        zombie_position = (zombie.world_x, zombie.world_y)
        
        # Existing pathfinding logic
        if zombie.path == [] or not zombie.path:
            task_queue.add_task(lambda: self.add_new_path_task(zombie, zombie_position, player_pos))
            zombie.target_last_seen = player_pos
        else:
            dist_to_last = math.hypot(player_pos[0] - zombie.target_last_seen[0],
                                    player_pos[1] - zombie.target_last_seen[1])
            if dist_to_last > c.PATHFINDER_DISTANCE_FOR_RECALC:
                task_queue.add_task(lambda: self.add_new_path_task(zombie, zombie_position, player_pos))
                zombie.target_last_seen = player_pos

    def move_zombie(self, zombie):
        """Handle movement for a single zombie"""
        if zombie.path:
            next_tile = zombie.path[0]
            next_tile_world = (next_tile[0]*10, next_tile[1]*10)
            
            dx, dy = compute_move_towards((zombie.world_x, zombie.world_y), 
                                         next_tile_world, 
                                         c.ZOMBIE_SPEED+random.randint(0, c.ZOMBIE_SPEED_VARIABILITY))
            
            zombie.world_x += dx
            zombie.world_y += dy
            
            if (zombie.world_x, zombie.world_y) == next_tile_world:
                zombie.path.pop(0)
                

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

# A class that is made to distrubute workload over time, instead of all at once. In-built priority selection makes high priority tasks run first and low priority after
class TaskQueue:
    def __init__(self, high_priority_cutoff=0):
        self.high_queue = []
        self.low_queue = []
        self._counter = count()
        self.high_priority_cutoff = high_priority_cutoff  # <= this value = high priority

    def add_task(self, task, priority=0):
        """Add task to appropriate queue based on priority"""
        entry = (priority, next(self._counter), task)
        if priority <= self.high_priority_cutoff:
            heapq.heappush(self.high_queue, entry)
        else:
            heapq.heappush(self.low_queue, entry)

    def _process_queue(self, queue, max_tasks):
        tasks_run = 0
        temp_requeue = []
        
        while queue and tasks_run < max_tasks:
            priority, _, task = heapq.heappop(queue)
            
            # Handle generator tasks
            if isinstance(task, types.GeneratorType):
                try:
                    next(task)
                    # Requeue with original priority
                    new_entry = (priority, next(self._counter), task)
                    temp_requeue.append(new_entry)
                except StopIteration:
                    pass
            else:
                task()
            
            tasks_run += 1
        
        # Re-add paused generators to original queue
        for entry in temp_requeue:
            if entry[0] <= self.high_priority_cutoff:
                heapq.heappush(self.high_queue, entry)
            else:
                heapq.heappush(self.low_queue, entry)
        
        return tasks_run

    def process_tasks(self, max_high=0, max_low=0):
        """Process up to max_high high-priority and max_low low-priority tasks"""
        high_run = self._process_queue(self.high_queue, max_high)
        low_run = self._process_queue(self.low_queue, max_low)
        
        #print(f"High tasks: {high_run}, Low tasks: {low_run}")
        return high_run + low_run

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
    """
    Computes a movement step (dx, dy) so that a zombie (or any entity) at (pos_x, pos_y)
    moves towards (dest_x, dest_y) by up to 'speed' units.

    Returns:
       (move_x, move_y) - the step vector along the hypotenuse 
                          from the current position to the destination, 
                          with magnitude <= speed.
    """
    pos_x, pos_y = pos
    dest_x, dest_y = dest

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
        # Extract start and goal coordinates from the input tuples
        start_x, start_y = start_world
        goal_x, goal_y = goal_world

        # Convert world coordinates to tile coordinates
        sx = int(start_x // self.tile_size)
        sy = int(start_y // self.tile_size)
        gx = int(goal_x // self.tile_size)
        gy = int(goal_y // self.tile_size)

        # Quick reject: if the goal tile is not walkable, return an empty path
        if self.is_walkable(gx, gy) == False:
            return []

        # Initialize the A* search algorithm
        open_set = []
        # Push the start node into the open set with the heuristic cost
        heapq.heappush(open_set, (0 + math.hypot(gx - sx, gy - sy), 0, sx, sy))
        came_from = {}  # Dictionary to map nodes to their parent nodes
        cost_so_far = {(sx, sy): 0}  # Dictionary to store the cost to reach each node

        # Define possible movement directions (8-connected grid)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                    (-1, -1), (-1, 1), (1, -1), (1, 1)]

        # Main loop of the A* algorithm
        while open_set:
            # Pop the node with the lowest cost from the open set
            _, g, x, y = heapq.heappop(open_set)

            # If the goal node is reached, reconstruct the path
            if (x, y) == (gx, gy):
                path = [(gx, gy)]
                # Follow the parent nodes back to the start node
                while (x, y) in came_from:
                    (x, y) = came_from[(x, y)]
                    path.append((x, y))
                path.reverse()
                return path

            # Skip processing if this node has already been processed with a lower cost
            if cost_so_far.get((x, y), float('inf')) < g:
                continue

            # Examine each neighbor of the current node
            for dx, dy in directions:
                nx, ny = x + dx, y + dy

                # Check if the neighbor is walkable
                if not self.is_walkable(nx, ny):
                    continue

                # Prevent diagonal moves through walls
                if dx != 0 and dy != 0:
                    if not self.is_walkable(x + dx, y) or not self.is_walkable(x, y + dy):
                        continue

                # Calculate the cost to move to the neighbor
                step_cost = math.hypot(dx, dy)
                new_cost = g + step_cost

                # Only consider this path if it is better than any previously known path to the neighbor
                if new_cost < cost_so_far.get((nx, ny), float('inf')):
                    cost_so_far[(nx, ny)] = new_cost
                    priority = new_cost + math.hypot(gx - nx, gy - ny)  # f = g + h
                    heapq.heappush(open_set, (priority, new_cost, nx, ny))
                    came_from[(nx, ny)] = (x, y)

        # If the open set is empty and the goal was not reached, return an empty path
        return []

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
    # Identify chunk coordinates based on object position
    cx = obj_x // chunk_manager.chunk_pixel_w
    cy = obj_y // chunk_manager.chunk_pixel_h

    # If the chunk is pending, return immediately
    if (cx, cy) in chunk_manager.pending_chunks:
        return

    # Retrieve the chunk from the chunk manager
    chunk = chunk_manager.get_chunk(cx, cy)
    if not chunk:
        return False  # If the chunk is not loaded or out of range

    # Calculate local tile coordinates within the chunk
    local_x = int((obj_x % chunk_manager.chunk_pixel_w) // chunk_manager.tile_size)
    local_y = int((obj_y % chunk_manager.chunk_pixel_h) // chunk_manager.tile_size)

    # Check the collision map for the tile
    if chunk.collision_map[local_y][local_x]:
        # The tile is blocked
        return False
    return True

def get_angle(x, y):
    """
    Returns the angle (in degrees) for the triangle sides x and y,
    i.e. the angle of the vector (x, y) relative to the positive X-axis.
    """
    angle_radians = math.atan2(y, x)  # Calculate the angle in radians between -π and π
    angle_degrees = math.degrees(angle_radians)  # Convert the angle to degrees
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
    # Find the closest point on the box to the circle center
    closest_x = min(max(cx, box_x), box_x + box_w)
    closest_y = min(max(cy, box_y), box_y + box_h)

    # Calculate the distance from the circle center to the closest point
    dist_x = cx - closest_x
    dist_y = cy - closest_y
    dist_sqr = dist_x * dist_x + dist_y * dist_y

    # Check if the distance is less than the radius squared
    r_sqr = r * r
    if dist_sqr >= r_sqr:
        return (0, 0)  # No collision

    # Calculate the overlap and normalize the distance vector
    dist = math.sqrt(dist_sqr) or 0.000001
    overlap = r - dist
    nx = dist_x / dist
    ny = dist_y / dist

    # Calculate the push vector
    px = nx * overlap
    py = ny * overlap
    return (px, py)

def update_rotations(game_player, gun_surf):
    # Get the current mouse position
    mouse_x, mouse_y = pygame.mouse.get_pos()
    # Calculate the angle between the player and the mouse position
    ang = get_angle(mouse_x - 1/2 * info.current_w, mouse_y - 1/2 * info.current_h) + 90
    # Rotate the player's image to face the mouse position
    game_player.scaled_image = pygame.transform.rotate(game_player.original_image, -ang)
    # Update the gun's position and rotation to match the player's direction
    update_gun_position(game_player, gun_surf, ang)

def update_gun_position(player, gun_surf, rotation_angle, offset_distance=50):
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
    gun_surf.angle = rotation_angle - 90

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
    
    # Predict the new center of the player
    cx = player.world_x + dx
    cy = player.world_y + dy
    r = 35  # or a fixed 50 if that’s your circle radius

    # Perform multiple passes for corner sliding
    for _ in range(passes):
        # Circle bounding box in world coordinates
        circle_left = cx - r
        circle_right = cx + r
        circle_top = cy - r
        circle_bottom = cy + r

        # Check each loaded chunk for overlap and collisions
        for (chunk_cx, chunk_cy), chunk in chunk_manager.chunks.items():
            # The chunk’s bounding box in world coordinates
            chunk_left = chunk.rect.x
            chunk_top = chunk.rect.y
            chunk_right = chunk_left + chunk.rect.width
            chunk_bottom = chunk_top + chunk.rect.height

            # Skip if bounding boxes don’t intersect
            if (circle_right < chunk_left or circle_left > chunk_right or
                circle_bottom < chunk_top or circle_top > chunk_bottom):
                continue

            # Find the local tile range inside the chunk
            chunk_w = chunk_manager.chunk_width_tiles
            chunk_h = chunk_manager.chunk_height_tiles
            tsize = chunk_manager.tile_size

            # Offset of the chunk in world space
            ox = chunk.rect.x
            oy = chunk.rect.y

            # Min/max tile index in chunk local coordinates
            local_left = int((circle_left - ox) // tsize)
            local_right = int((circle_right - ox) // tsize)
            local_top = int((circle_top - oy) // tsize)
            local_bottom = int((circle_bottom - oy) // tsize)

            # Clamp to [0..chunk_w-1, 0..chunk_h-1]
            local_left = max(0, min(local_left, chunk_w - 1))
            local_right = max(0, min(local_right, chunk_w - 1))
            local_top = max(0, min(local_top, chunk_h - 1))
            local_bottom = max(0, min(local_bottom, chunk_h - 1))

            # Check each blocked tile in the local range for collisions
            for ty in range(local_top, local_bottom + 1):
                for tx in range(local_left, local_right + 1):
                    if chunk.collision_map[ty][tx]:
                        # Tile bounding box in world coordinates
                        tile_world_x = ox + tx * tsize
                        tile_world_y = oy + ty * tsize

                        # Resolve collision between the player and the tile
                        px, py = circle_vs_aabb(cx, cy, r,
                                                tile_world_x, tile_world_y,
                                                tsize, tsize)
                        if px != 0 or py != 0:
                            cx += px
                            cy += py
                            # Because the circle center changed, we might overlap a new tile,
                            # but we rely on additional 'passes' to fix that.

    # Commit the final center position of the player
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
        # Scale and blit each sprite onto the zoom surface
        sw = sp.scaled_image.get_width()
        sh = sp.scaled_image.get_height()
        off_x = (sp.world_x - camera_x) * c.ZOOM_FACTOR
        off_y = (sp.world_y - camera_y) * c.ZOOM_FACTOR
        # Center the sprite on the offset
        sx = screen_center[0] + off_x - sw / 2
        sy = screen_center[1] + off_y - sh / 2
        zoomSurf.blit(sp.scaled_image, (sx, sy))

    # Clear the zoom surface
    zoomSurf.fill((0, 0, 0))
    # Draw chunks and obstacles onto the zoom surface
    chunk_manager.draw_chunks(zoomSurf, game_player.world_x, game_player.world_y, screen_center, zoom=c.ZOOM_FACTOR)
    obstacle_manager.draw_chunks(zoomSurf, game_player.world_x, game_player.world_y, screen_center, zoom=c.ZOOM_FACTOR)
    
    # Use the first player as the camera anchor
    player = game_player
    camera_x = player.world_x
    camera_y = player.world_y

    # Draw each bullet onto the zoom surface
    for sp in bullet_manager.bullets.sprites():
        scale_and_blit_zoom_surface(sp)

    # Draw each sprite in playerGroup
    for sp in playerGroup.sprites():
        scale_and_blit_zoom_surface(sp)
    
    # Draw each sprite in UIGroup
    for sp in UIGroup.sprites():
        zoomSurf.blit(sp.image, sp.rect)

################################################
# Initialize global variables, instances, etc.
################################################

# Initialize the pygame modules
pygame.init()
pygame.font.init()

# Set allowed events to improve performance
pygame.event.set_allowed([QUIT, KEYDOWN, KEYUP, WINDOWRESIZED])

# Set the window position
os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"
info = pygame.display.Info()  # Get display info
clock = pygame.time.Clock()

# Set flags for double buffering and fullscreen to improve performance
flags = DOUBLEBUF | FULLSCREEN
screen = pygame.display.set_mode((info.current_w, info.current_h), flags)
screen_center = (info.current_w // 2, info.current_h // 2)

# Create an offscreen surface for drawing each frame
zoomSurf = pygame.Surface((info.current_w, info.current_h))

# Initialize scene constants for readability and fast integer lookup
TUTORIAL = 1
MAIN_GAME = 2
END_SCREEN = 3

# Start on the tutorial scene
current_scene = TUTORIAL

# Load tutorial images and center them on the screen
TUTORIAL_1 = surface.staticImage("assets/img/tut1.png", (8001 * info.current_h / 4166, info.current_h))
TUTORIAL_1.rect.center = (screen_center[0] - 50, screen_center[1])
TUTORIAL_2 = surface.staticImage("assets/img/tut2.png", (8001 * info.current_h / 4166, info.current_h))
TUTORIAL_2.rect.center = (screen_center[0] - 50, screen_center[1])

# Set the first tutorial page
tutorial_scene = TUTORIAL_1

# Initialize the game score as a global variable
total_score = 0

# Load the highscore from a save file
scoreSaveArr = save.getRawData("saves/score.pickle")
highscore = dict(scoreSaveArr).get("Highscore", 0)

# Initialize sprite groups for different layers and scenes
playerGroup = pygame.sprite.RenderUpdates()
UIGroup = pygame.sprite.RenderUpdates()
end_screen_group = pygame.sprite.RenderUpdates()

# Create the player and gun objects
game_player = Player(playerGroup)
gun_surf = Weapon(playerGroup)

# Create the health bar and icon
health_bar = surface.RectSprite(0, 0, 300, 50, (255, 0, 0), UIGroup)
health_bar.rect.topright = (info.current_w - 50, 50)

health_icon = surface.staticImage("assets/img/heart.png", (50, 50), UIGroup)
health_icon.rect.topright = (info.current_w - 55 - health_bar.w, 50)

# Create the FPS text display
fps_text = surface.textSurface("placeholder", UIGroup)

# Load and set the logo image with transparency
logoImage = surface.staticImage("assets/img/goonz_text_only.png", (187, 174), UIGroup)
logoImage.image.fill((255, 255, 255, 210), None, pygame.BLEND_RGBA_MULT)
logoImage.rect.midtop = (info.current_w / 2, 0)

# Load the background image for the end screen
backgroundImg = surface.staticImage("assets/img/goonz_background.png", (4360 * info.current_h / 2200, info.current_h), end_screen_group)
backgroundImg.rect.center = screen_center

# Create the score text display
scoreText = surface.textSurface(str(total_score), UIGroup)
scoreText.rect.midbottom = (info.current_w / 2, info.current_h)

# Initialize managers for various game elements
task_queue = TaskQueue(high_priority_cutoff=0)

chunk_manager = game_chunks.ChunkManager(task_queue, chunk_width_tiles=50, chunk_height_tiles=50,
                                         tile_size=10, scale=150.0, seed=42)

obstacle_manager = game_chunks.ChunkManager(task_queue, chunk_width_tiles=50, chunk_height_tiles=50,
                                            tile_size=10, scale=10.0, seed=42, isBiomeMap=False)

pathfinder = Pathfinder(obstacle_manager, obstacle_manager.chunk_height_tiles, obstacle_manager.tile_size)

bullet_manager = BulletManager()

zombie_manager = ZombieManager(c.ZOMBIES_PER_WAVE_BASE, c.ZOMBIES_PER_WAVE_MULTIPLIER)

# Initialize background music to play throughout the game
musicManager = music.MusicWithQueue()
musicManager.playMusic()

# Record the start time for zombie logic
timeAtStart = time.time()

########################################
# PyGame Custom Userevents
########################################
zombie_spawn_event = pygame.USEREVENT + 1
pygame.time.set_timer(zombie_spawn_event, c.ZOMBIE_SPAWN_DELAY_MS)

# Set up a custom event for game ticks to control the game loop timing
game_tick_event = pygame.USEREVENT + 2
pygame.time.set_timer(game_tick_event, math.floor(1000 / 60))  # 60 FPS

########################################
# Main Loop
########################################
while c.GAME_IS_RUNNING:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            # Exit the game loop if the window is closed
            c.GAME_IS_RUNNING = False

        elif event.type == pygame.WINDOWRESIZED:
            # Handle window resize events to adjust the game display
            info = pygame.display.Info()
            screen = pygame.display.set_mode((info.current_w, info.current_h), flags)
            zoomSurf = pygame.Surface((info.current_w, info.current_h))
            screen_center = (info.current_w // 2, info.current_h // 2)
        
        else:
            # Handle other events, such as music management
            musicManager.handle_event(event)
    
    if current_scene == TUTORIAL:
        # Tutorial Screen
        screen.blit(tutorial_scene.image, tutorial_scene.rect)
        
        keys = pygame.key.get_pressed()
        for event in events:
            if event.type == KEYUP:
                if event.key == K_SPACE:
                    if tutorial_scene == TUTORIAL_1:
                        # Move to the next tutorial scene
                        tutorial_scene = TUTORIAL_2
                        continue
                    
                    # Start the main game after the tutorial
                    reset_game(game_player, bullet_manager, zombie_manager, chunk_manager, obstacle_manager, health_bar)
                    current_scene = MAIN_GAME
                    timeAtStart = time.time()
        pygame.display.flip()
        clock.tick(60)

    elif current_scene == MAIN_GAME:
        for event in events:
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    # Example of how the zoom function could work if Space is pressed
                    pass 
                    # c.ZOOM_FACTOR += 0.05
                    # Only re-scale once, not every frame
                    # rescale_all(c.ZOOM_FACTOR)
            
            elif event.type == zombie_spawn_event:
                # Spawn zombies after the initial delay and if the maximum number of zombies is not reached
                if time.time() - timeAtStart > c.ZOMBIE_INITIAL_SPAWN_DELAY:
                    if len(zombie_manager.zomb_list) < c.ZOMBIES_MAX_AT_ONCE:
                        zombie_manager.add_zombie(game_player.world_x, game_player.world_y)
            
            elif event.type == game_tick_event:
                # Handle game tick events for updating game state
                keys = pygame.key.get_pressed()
                dx, dy = 0, 0
                for k, v in charControls.items():
                    if keys[k]:
                        dx += v[0]
                        dy += v[1]
                bullet_manager.update()
                move_circle_player(game_player, dx, dy, obstacle_manager)
                zombie_manager.update_zombie_movement()

                if keys[K_SPACE]:
                    # Shoot bullets when the space key is pressed
                    bullet_manager.shoot(gun_surf.world_x, gun_surf.world_y, gun_surf.angle, 15)

        # Determine the chunk coordinates of the player
        cx = game_player.world_x // chunk_manager.chunk_pixel_w
        cy = game_player.world_y // chunk_manager.chunk_pixel_h

        # Get the current chunk and obstacle chunk based on player position
        pchunk = chunk_manager.get_chunk(cx, cy)
        obs_chunk = obstacle_manager.get_chunk(cx, cy)

        # Calculate local coordinates within the chunk
        local_x = (game_player.world_x % chunk_manager.chunk_pixel_w) // chunk_manager.tile_size
        local_y = (game_player.world_y % chunk_manager.chunk_pixel_h) // chunk_manager.tile_size

        # Update rotations for the player and gun
        update_rotations(game_player, gun_surf)

        # Load surrounding chunks to ensure smooth gameplay
        for nx in [cx - 3, cx - 2, cx - 1, cx, cx + 1, cx + 2, cx + 3]:
            for ny in [cy - 2, cy - 1, cy, cy + 1, cy + 2]:
                chunk_manager.get_chunk(nx, ny)
                obstacle_manager.get_chunk(nx, ny)

        # Update the chunks and process tasks
        chunk_manager.update_chunks(cx, cy)
        task_queue.process_tasks(max_high=3, max_low=80)

        # Draw all game elements
        draw_all()

        # Update the FPS display
        fps_text.update_text("FPS: " + str(math.floor(clock.get_fps())))

        # Blit the zoom surface to the screen
        screen.blit(zoomSurf, (0, 0))

        # Update the display and tick the clock
        pygame.display.flip()
        clock.tick()
    
    elif current_scene == END_SCREEN:
        # End Screen
        screen.blit(backgroundImg.image, backgroundImg.rect)
        title_font = pygame.font.Font(None, 74)
        text = title_font.render('Game Over', True, (255, 255, 255))
        text_rect = text.get_rect(center=(screen_center[0], screen_center[1] + 100))
        screen.blit(text, text_rect)
        score_font = pygame.font.Font(None, 36)
        score_text = score_font.render(f'Score: {total_score}  High Score: {highscore}', True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(screen_center[0], screen_center[1] + 150))
        screen.blit(score_text, score_rect)
        restart_text = score_font.render('Press R to restart or Q to quit. Press K to reset highscore', True, (255, 255, 255))
        restart_rect = restart_text.get_rect(center=(screen_center[0], screen_center[1] + 185))
        screen.blit(restart_text, restart_rect)
        
        keys = pygame.key.get_pressed()
        if keys[K_r]:
            # Restart the game
            reset_game(game_player, bullet_manager, zombie_manager, chunk_manager, obstacle_manager, health_bar)
            current_scene = MAIN_GAME
        elif keys[K_q]:
            # Quit the game
            c.GAME_IS_RUNNING = False
        elif keys[K_k]:
            # Reset the high score
            highscore = 0

        pygame.display.flip()
        clock.tick(60)
        
# Save the high score before exiting
save.saveData("saves/score.pickle", {("Highscore", highscore)})

# Quit pygame
pygame.quit()