# Filip har skrevet noiseGen.py

import math, random

# ------------- GLOBAL GRADIENTS ---------------
# Dictionary to store gradients for each grid point
gradients = {}  # (ix, iy) -> (gx, gy)

# Initialize the world seed with a random value
WORLD_SEED = random.randint(1, 696969)

# Reset the noise generator by clearing the gradients and resetting the seed
def reset_noise():
    reset_seed()
    global gradients
    gradients = {}

# Reset the world seed to a new random value
def reset_seed():
    global WORLD_SEED
    WORLD_SEED = random.randint(1, 696969)

# Return the current world seed
def get_seed():
    return WORLD_SEED

# Get the gradient vector for a given grid point (ix, iy)
def get_gradient(ix, iy):
    if (ix, iy) in gradients:
        return gradients[(ix, iy)]
    # Generate a unique seed for the grid point based on its coordinates and the world seed
    int_seed = hash((ix, iy, get_seed()))  # -> integer
    rnd = random.Random(int_seed)
    # Generate a random angle and compute the gradient vector components
    angle = rnd.random() * 2 * math.pi
    gx, gy = math.cos(angle), math.sin(angle)
    # Store the gradient vector in the dictionary
    gradients[(ix, iy)] = (gx, gy)
    return (gx, gy)

# Fade function to smooth the interpolation
def fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)

# Linear interpolation with fading
def fade_lerp(a, b, t):
    return a + fade(t) * (b - a)

# Compute the dot product of the distance and gradient vectors
def dot_grid_gradient(ix, iy, x, y):
    gx, gy = get_gradient(ix, iy)
    dx = x - ix
    dy = y - iy
    return dx * gx + dy * gy

# Generate Perlin noise value for a given point (x, y)
def perlin_2d(x, y):
    # Determine grid cell coordinates
    x0 = int(math.floor(x))
    x1 = x0 + 1
    y0 = int(math.floor(y))
    y1 = y0 + 1

    # Determine interpolation weights
    sx = x - x0
    sy = y - y0

    # Interpolate between grid point gradients
    n0 = dot_grid_gradient(x0, y0, x, y)
    n1 = dot_grid_gradient(x1, y0, x, y)
    ix0 = fade_lerp(n0, n1, sx)

    n2 = dot_grid_gradient(x0, y1, x, y)
    n3 = dot_grid_gradient(x1, y1, x, y)
    ix1 = fade_lerp(n2, n3, sx)

    return fade_lerp(ix0, ix1, sy)

# ------------- UTILITY FOR CHUNK / TILES ---------------
# Generate a 2D array of Perlin noise values for a given width and height
def generate_perlin_noise(width, height, scale=15.0, offset_x=0, offset_y=0):
    """
    Create a 2D array of noise values for a chunk or region of size 'width x height' in tile space.
    offset_x, offset_y can be negative or positive, which places the chunk in world coordinates.
    """
    noise_grid = []
    for j in range(height):
        row = []
        for i in range(width):
            # Sample the noise plane at global coords (offset_x+i, offset_y+j) scaled by 'scale'.
            x_coord = (offset_x + i) / scale
            y_coord = (offset_y + j) / scale
            val = perlin_2d(x_coord, y_coord)
            row.append(val)
        noise_grid.append(row)
    return noise_grid

# Assign biome colors based on noise value
def assign_biome(value):
    if value < -0.3: return (0, 0, 150), False   # deep water
    elif value < 0.0: return (0, 0, 255), False  # shallow water
    elif value < 0.3: return (34, 139, 34), False # grass
    else: return (139, 137, 137), False          # mountain

# Assign obstacle colors based on noise value
def assign_obstacle(value):
    if value < -0.45: return (0, 100, 100, 200), True
    if value < -0.35: return (0, 100, 100, 200), True
    else: return (0, 0, 0, 0), False

# Generate a biome map and collision map based on Perlin noise values
def get_biome_map(map_width=50, map_height=50, scale=15.0, offset_x=0, offset_y=0, isBiomeMap=True):
    def get_biome_loop(func):
        biome_map = []
        collision_map = []
        for j in range(map_height):
            row = []
            collision_row = []
            for i in range(map_width):
                color, is_blocked = func(noise_values[j][i])
                row.append(color)
                collision_row.append(is_blocked)
            biome_map.append(row)
            collision_map.append(collision_row)
        return biome_map, collision_map

    # Get the Perlin noise values for the specified region
    noise_values = generate_perlin_noise(
        width=map_width,
        height=map_height,
        scale=scale,
        offset_x=offset_x,
        offset_y=offset_y
    )
    if isBiomeMap:
        biome_data, collision_map = get_biome_loop(assign_biome)
        return biome_data, collision_map
    
    biome_data, collision_map = get_biome_loop(assign_obstacle)
    return biome_data, collision_map