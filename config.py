# Filip har skrevet config.py
# A python file with constants for the game to run.
# This file is to be imported anywhere where the value of the constants is needed.
# This file includes settings, run conditions, and values of the game.

# Player settings
PLAYER_SPEED = 4  # Speed at which the player moves
PLAYER_HEALTH = 100  # Initial health of the player
PLAYER_RADIUS = 50  # Radius of the player for collision detection

# Terrain conditions
CHUNK_SIZE_IN_TILES = 50  # Number of tiles in each chunk
CHUNK_TILE_SIZE = 10  # Size of each tile in pixels

# Gameplay conditions
ZOMBIES_PER_WAVE_BASE = 15  # Base number of zombies per wave
ZOMBIES_MAX_AT_ONCE = 18  # Maximum number of zombies that can be present at once
ZOMBIES_PER_WAVE_MULTIPLIER = 1.1  # Multiplier for the number of zombies per wave
ZOMBIE_SPAWN_DISTANCE = 1050  # Distance from the player at which zombies spawn
ZOMBIE_RADIUS = 50  # Radius of the zombie for collision detection
ZOMBIE_REACH = 5  # Distance at which a zombie can attack the player
ZOMBIE_DAMAGE = 20  # Damage dealt by a zombie to the player
ZOMBIE_HEALTH = 100  # Initial health of a zombie
ZOMBIE_COOLDOWN = 1  # Cooldown time between zombie attacks in seconds
ZOMBIE_SPEED = 5  # Base speed of a zombie
ZOMBIE_SPEED_VARIABILITY = 2  # Variability in zombie speed
ZOMBIE_SPAWN_DELAY_MS = 750  # Delay between zombie spawns in milliseconds
ZOMBIE_INITIAL_SPAWN_DELAY = 2  # Initial delay before zombies start spawning in seconds

# Pathfinder settings
PATHFINDER_DISTANCE_FOR_RECALC = 125  # Distance at which the pathfinder recalculates the path

# Gun settings
AK47_DMG = 23  # Base damage of the AK47, with added randomness
AK47_RPM = 350  # Rounds per minute for the AK47
AK47_SIZE = (25, 112.5)  # Size of the AK47 sprite

# UI constants
ZOOM_FACTOR = 1  # Initial zoom factor for the game display

# Run conditions
GAME_IS_RUNNING = True  # Flag to indicate if the game is running