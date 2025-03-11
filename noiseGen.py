import math, random
import pygame

# ------------- GLOBAL GRADIENTS ---------------
gradients = {}  # (ix, iy) -> (gx, gy)
WORLD_SEED = random.randint(1, 696969)

def get_gradient(ix, iy):
    if (ix, iy) in gradients:
        return gradients[(ix, iy)]
    int_seed = hash((ix, iy, WORLD_SEED))  # -> integer
    rnd = random.Random(int_seed)
    angle = rnd.random() * 2 * math.pi
    gx, gy = math.cos(angle), math.sin(angle)
    gradients[(ix, iy)] = (gx, gy)
    return (gx, gy)

def fade(t):
    return t * t * t * (t * (t * 6 - 15) + 10)

def fade_lerp(a, b, t):
    return a + fade(t) * (b - a)

def dot_grid_gradient(ix, iy, x, y):
    gx, gy = get_gradient(ix, iy)
    dx = x - ix
    dy = y - iy
    return dx*gx + dy*gy

def perlin_2d(x, y):
    x0 = int(math.floor(x))
    x1 = x0 + 1
    y0 = int(math.floor(y))
    y1 = y0 + 1

    sx = x - x0
    sy = y - y0

    n0 = dot_grid_gradient(x0, y0, x, y)
    n1 = dot_grid_gradient(x1, y0, x, y)
    ix0 = fade_lerp(n0, n1, sx)

    n2 = dot_grid_gradient(x0, y1, x, y)
    n3 = dot_grid_gradient(x1, y1, x, y)
    ix1 = fade_lerp(n2, n3, sx)

    return fade_lerp(ix0, ix1, sy)

# ------------- UTILITY FOR CHUNK / TILES ---------------
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

def assign_biome(value):
    if value < -0.3: return (0, 0, 150)   # deep water
    elif value < 0.0: return (0, 0, 255) # shallow
    elif value < 0.3: return (34,139,34) # grass
    else: return (139,137,137)          # mountain

def get_biome_map(map_width=50, map_height=50, scale=15.0, offset_x=0, offset_y=0):
    # Get the perlin noise
    noise_values = generate_perlin_noise(
        width=map_width,
        height=map_height,
        scale=scale,
        offset_x=offset_x,
        offset_y=offset_y
    )
    # Convert noise to biome colors
    biome_map = []
    for j in range(map_height):
        row = []
        for i in range(map_width):
            color = assign_biome(noise_values[j][i])
            row.append(color)
        biome_map.append(row)
    return biome_map
