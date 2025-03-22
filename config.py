# Config.py
# A python file with constants for the game to run.
# This file is to be imported anywhere where the value of the constants is needed.
# This file includes settings, run conditions, and values of the game.

# Player
PLAYER_SPEED = 4
PLAYER_HEALTH = 100
PLAYER_RADIUS = 50

# Terrain Conditions
CHUNK_SIZE_IN_TILES = 50
CHUNK_TILE_SIZE = 10

#Gameplay Conditions
ZOMBIES_PER_WAVE = 15
ZOMBIE_SPAWN_DISTANCE = 800
ZOMBIE_RADIUS = 50
ZOMBIE_REACH = 5
ZOMBIE_DAMAGE = 20
ZOMBIE_HEALTH = 100
ZOMBIE_COOLDOWN = 1
ZOMBIE_SPEED = 3
ZOMBIE_SPEED_VARIABILITY = 2
ZOMBIE_SPAWN_DELAY_MS = 750

#Pathfinder
PATHFINDER_DISTANCE_FOR_RECALC = 125


## Guns
AK47_DMG = 23 # Base dmg + randomness
AK47_RPM = 350

#UI Constants
ZOOM_FACTOR = 1


# Run Conditions
GAME_IS_RUNNING = True
