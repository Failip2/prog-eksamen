import pygame

pygame.init()
# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Player-Centered Zoom")

# Load background (island) image and get its rect for size
island_img = pygame.image.load("assets/img/nig.png").convert()          # original background image
island_rect = island_img.get_rect()
# Set the world's top-left coordinate of the background
island_world_x = 0
island_world_y = 0

# Load player sprite image
player_img = pygame.image.load("assets/img/zomb.png").convert_alpha()    # original player image
player_rect = player_img.get_rect()
# Initialize player sprite with a Sprite class
player = pygame.sprite.Sprite()
player.image = player_img
player.rect = player_rect.copy()   # will be updated each frame
# Store player's world coordinates (start at center of background, for example)
player.world_x = island_rect.width // 2 - player_rect.width // 2
player.world_y = island_rect.height // 2 - player_rect.height // 2
# Keep original image for scaling to prevent quality loss
player.original_image = player_img

# Create sprite group for the player (and other sprites if any)
playerGroup = pygame.sprite.Group(player)

# Initial zoom level (1.0 = 100%)
zoom = 1.0
zoom_speed = 1.1  # zoom increment factor for in/out

clock = pygame.time.Clock()
running = True
while running:
    dt = clock.tick(60)  # limit to 60 FPS
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            # Zoom in (e.g., press Z or +)
            if event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS or event.key == pygame.K_z:
                zoom *= zoom_speed
                # Limit zoom to avoid too far (optional)
                if zoom > 5: 
                    zoom = 5
            # Zoom out (e.g., press X or -)
            if event.key == pygame.K_MINUS or event.key == pygame.K_x:
                zoom /= zoom_speed
                # Limit zoom to avoid too far out (optional)
                if zoom < 0.2: 
                    zoom = 0.2

    # Movement input (WASD or arrow keys) – adjusts player world position
    keys = pygame.key.get_pressed()
    move_speed = 5  # movement speed in world units (pixels at zoom 1)
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        player.world_x -= move_speed
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        player.world_x += move_speed
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        player.world_y -= move_speed
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        player.world_y += move_speed

    # --- Drawing section ---
    # Fill background with a color (black) in case the scaled background doesn't cover the screen
    screen.fill((0, 0, 0))  

    # Scale the background image according to current zoom
    new_bg_width = int(island_rect.width * zoom)
    new_bg_height = int(island_rect.height * zoom)
    island_surf = pygame.transform.smoothscale(island_img, (new_bg_width, new_bg_height))
    # Calculate background draw position so that the player stays centered
    bg_screen_x = WIDTH/2 + (island_world_x - player.world_x) * zoom
    bg_screen_y = HEIGHT/2 + (island_world_y - player.world_y) * zoom
    # Blit the scaled background
    screen.blit(island_surf, (bg_screen_x, bg_screen_y))

    # Update and draw all sprites
    for sprite in playerGroup:
        # Re-scale sprite image from its original image based on zoom
        orig_rect = sprite.original_image.get_rect()
        new_width = int(orig_rect.width * zoom)
        new_height = int(orig_rect.height * zoom)
        sprite.image = pygame.transform.smoothscale(sprite.original_image, (new_width, new_height))
        # Update the sprite's rect with the new size, and position it relative to player
        sprite.rect = sprite.image.get_rect()
        sprite.rect.x = int(WIDTH/2 + (sprite.world_x - player.world_x) * zoom)
        sprite.rect.y = int(HEIGHT/2 + (sprite.world_y - player.world_y) * zoom)
    # Draw sprite group to screen
    playerGroup.draw(screen)

    pygame.display.flip()

pygame.quit()
