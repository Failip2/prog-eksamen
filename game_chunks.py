# Filip har skrevet game_chunks.py

import pygame
import noiseGen

# Define the Chunk class to store chunk-related data
class Chunk:
    def __init__(self, cx, cy, surface, rect, biome_data, collision_map):
        self.cx = cx
        self.cy = cy
        self.surface = surface
        self.rect = rect
        self.biome_data = biome_data
        self.collision_map = collision_map 

# Define the ChunkManager class to manage chunks in the game
class ChunkManager:
    def __init__(self, task_queue, chunk_width_tiles=50, chunk_height_tiles=50,
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
        self.chunk_pixel_w = self.chunk_width_tiles * self.tile_size
        self.chunk_pixel_h = self.chunk_height_tiles * self.tile_size

        # Stores (cx, cy) -> Chunk instance
        self.chunks = {}
        self.pending_chunks = set()
        self.task_queue = task_queue

    # Generate chunk data for the given chunk coordinates (cx, cy)
    def generate_chunk_data(self, cx, cy):
        offset_x = cx * self.chunk_width_tiles  # chunk coords -> tile offset
        offset_y = cy * self.chunk_height_tiles
        biome_data, collision_map = noiseGen.get_biome_map(self.chunk_width_tiles, self.chunk_height_tiles, self.scale, 
                                            offset_x, offset_y, isBiomeMap=self.isBiomeMap)

        chunk_pixel_w = self.chunk_width_tiles * self.tile_size
        chunk_pixel_h = self.chunk_height_tiles * self.tile_size

        # Create a surface for the chunk
        if self.isBiomeMap:
            surface = pygame.Surface((chunk_pixel_w, chunk_pixel_h)).convert()
        else:
            surface = pygame.Surface((chunk_pixel_w, chunk_pixel_h), flags=pygame.SRCALPHA).convert_alpha()

        tile_count = 0

        # Fill the surface with biome data
        for j in range(self.chunk_height_tiles):
            for i in range(self.chunk_width_tiles):
                rect = pygame.Rect(i * self.tile_size, j * self.tile_size, self.tile_size, self.tile_size)
                surface.fill(biome_data[j][i], rect)
                tile_count += 1

                # Yield periodically to avoid blocking the main thread
                if tile_count % 500 == 0:
                    yield

        chunk_rect = pygame.Rect(cx * self.chunk_pixel_w, cy * self.chunk_pixel_h, self.chunk_pixel_w, self.chunk_pixel_h)

        # Create a new chunk and store it in the chunks dictionary
        new_chunk = Chunk(cx, cy, surface, chunk_rect, biome_data, collision_map)
        self.chunks[(cx, cy)] = new_chunk
        self.pending_chunks.discard((cx, cy))

    # Retrieve the chunk at the given coordinates (cx, cy)
    # If the chunk is not loaded, start generating it
    def get_chunk(self, cx: int, cy: int):
        if (cx, cy) in self.chunks:
            return self.chunks[(cx, cy)]
        # Only queue generation if chunk is not already loaded or pending
        if (cx, cy) not in self.pending_chunks:
            self.pending_chunks.add((cx, cy))  # mark chunk as being generated
            self.task_queue.add_task(self.generate_chunk_data(cx, cy), priority=1)
        return None  # chunk not immediately available (generation in progress)

    # Draw all loaded chunks that might be visible
    def draw_chunks(self, surface, camera_x, camera_y, screen_center, zoom=1.0):
        """
        Draw all loaded chunks that might be visible,
        using a camera anchored at (camera_x, camera_y) in world coords,
        so the camera is placed at screen_center with given zoom.
        """

        camera_cx = camera_x // self.chunk_pixel_w
        camera_cy = camera_y // self.chunk_pixel_h

        # Potentially cull or just draw all for demonstration
        for (cx, cy), chunk in self.chunks.items():
            if abs(cx - camera_cx) > 4 or abs(cy - camera_cy) > 4:
                continue

            # Calculate where this chunk appears on screen
            off_x = (chunk.rect.x - camera_x) * zoom
            off_y = (chunk.rect.y - camera_y) * zoom
            screen_x = screen_center[0] + off_x
            screen_y = screen_center[1] + off_y

            # Scale the chunk if zoom is not 1.0
            if zoom != 1.0:
                scaled_w = int(chunk.rect.width * zoom)
                scaled_h = int(chunk.rect.height * zoom)
                scaled_surf = pygame.transform.scale(chunk.surface, (scaled_w, scaled_h))
                surface.blit(scaled_surf, (screen_x, screen_y))
            else:
                # No scaling needed
                surface.blit(chunk.surface, (screen_x, screen_y))

    # Unload all chunks to free up memory
    def unload_all_chunks(self):
        self.chunks.clear()

    # Update chunks based on the player's position
    # Unload chunks that are too far from the center chunk
    def update_chunks(self, center_cx, center_cy):
        to_unload = []
        for (cx, cy) in self.chunks:
            if abs(cx - center_cx) > 3 or abs(cy - center_cy) > 3:
                to_unload.append((cx, cy))
        for key in to_unload:
            del self.chunks[key]