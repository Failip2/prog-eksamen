import math
import random
import matplotlib.pyplot as plt
from collections import Counter
import config

def fade(t):
    """ Smoothstep function to ease coordinate t (0 <= t <= 1). """
    return t * t * t * (t * (t * 6 - 15) + 10)

def lerp(a, b, t):
    """ Linear interpolation between a and b by t. """
    return a + t * (b - a)

def dot_grid_gradient(ix, iy, x, y, grad_grid):
    """
    Compute the dot product of the distance and gradient vectors.
    - (ix, iy): integer coordinates of the corner
    - (x, y): point at which noise is evaluated
    - grad_grid: dictionary or 2D array storing gradient vectors
    """
    dx = x - ix
    dy = y - iy
    gx, gy = grad_grid[(ix, iy)]
    return dx * gx + dy * gy

def generate_gradient_grid(width, height, seed=None):
    """
    Generate random gradient vectors for each integer point 
    in the [0..width] x [0..height] grid.
    """
    if seed is not None:
        random.seed(seed)
    
    grad_grid = {}
    for i in range(width + 1):
        for j in range(height + 1):
            angle = random.random() * 2 * math.pi
            gx = math.cos(angle)
            gy = math.sin(angle)
            grad_grid[(i, j)] = (gx, gy)
    return grad_grid

def perlin_2d(x, y, grad_grid):
    """
    Compute 2D Perlin noise at coordinates (x, y) using the precomputed
    gradient grid.
    """
    x0 = int(math.floor(x))
    x1 = x0 + 1
    y0 = int(math.floor(y))
    y1 = y0 + 1

    sx = x - x0
    sy = y - y0

    n0 = dot_grid_gradient(x0, y0, x, y, grad_grid)
    n1 = dot_grid_gradient(x1, y0, x, y, grad_grid)
    ix0 = lerp(n0, n1, fade(sx))

    n2 = dot_grid_gradient(x0, y1, x, y, grad_grid)
    n3 = dot_grid_gradient(x1, y1, x, y, grad_grid)
    ix1 = lerp(n2, n3, fade(sx))

    return lerp(ix0, ix1, fade(sy))

def generate_perlin_noise(width, height, scale=1.0, seed=None):
    """
    Generate a 2D list (width x height) of Perlin noise values in [-1, 1].
    'scale' controls the spatial frequency of the noise.
    """
    grad_grid = generate_gradient_grid(width, height, seed=seed)

    noise_grid = []
    for j in range(height):
        row = []
        for i in range(width):
            # i+1 and j+1 to offset coords (0, 0), as this, when inserted into face function, will always return 0
            nx = (i+1) / scale
            ny = (j+1) / scale
            val = perlin_2d(nx, ny, grad_grid)
            row.append(val)
        noise_grid.append(row)
    return noise_grid

def assign_biome(value):
    """
    Given a noise value (roughly in [-1, 1]),
    return a string or color representing the biome.
    Adjust thresholds as you wish.
    """
    if value < -0.3:
        return (0, 0, 150)     # Deep water (dark blue)
    elif value < 0.0:
        return (0, 0, 255)     # Shallow water (lighter blue)
    elif value < 0.3:
        return (34, 139, 34)   # Grassland (green)
    else:
        return (139, 137, 137) # Mountain (gray)


def get_biome_map(map_width=50, map_height=50, scale=15.0, seed=None):
    # Parameters for the noise
    # Desired map size in tiles
        
    # Pixel size of each tile
    tile_size = 10

    # Window size

    # Generate noise map
    noise_map = generate_perlin_noise(map_width, map_height, scale=scale, seed=seed)

    # Pre-compute biome colors for each tile
    biome_map = []
    for j in range(map_height):
        row = []
        for i in range(map_width):
            color = assign_biome(noise_map[j][i])
            row.append(color)
        biome_map.append(row)
    
    return biome_map


# Visualize using matplotlib
#plt.imshow(noise_map)     # or add: cmap='gray' if you want grayscale
#plt.colorbar()            # Show a color scale
#plt.title("2D Perlin Noise Visualization")
#plt.show()


