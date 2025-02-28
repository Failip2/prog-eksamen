import pygame
import config as c
import os
import surface

pygame.init()

os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"

info = pygame.display.Info()

clock = pygame.time.Clock()
screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.NOFRAME)

from pygame.locals import (
    RLEACCEL,
    K_UP,
    K_DOWN,
    K_LEFT,
    K_RIGHT,
    K_w,
    K_a,
    K_s,
    K_d,
    K_ESCAPE,
    KEYDOWN,
    QUIT,
)

testSurf = surface.Surface()
testGroup = pygame.sprite.Group(testSurf)

zoomSurf = pygame.Surface((info.current_w, info.current_h))
zoomRect = zoomSurf.fill((255,0,0))


charControls = {K_UP: (0, c.PLAYER_SPEED), K_DOWN: (0, -c.PLAYER_SPEED), K_RIGHT: (c.PLAYER_SPEED, 0), K_LEFT: (-c.PLAYER_SPEED, 0)}


testBool = True

while c.GAME_IS_RUNNING:
    for event in pygame.event.get(): 
        if event.type == pygame.QUIT: 
            c.GAME_IS_RUNNING = False

    ## Clear everything drawn (zoomSurf) in place of green placeholder color.
    zoomSurf.fill((0,255,0))
    testGroup.draw(zoomSurf)
    



    drawSurf = pygame.transform.smoothscale_by(zoomSurf, 0.5)
    drawSurfRect = drawSurf.get_rect()

    print(zoomRect)
    # Blits the fully compiled zoomSurf layer (players, terrain, etc.) to 'screen' surface

    screen.blit(drawSurf, (info.current_w/2-drawSurfRect[2]/2, info.current_h/2-drawSurfRect[3]/2))

    testSurf.rect.move_ip(1,1)
    
    pygame.display.flip()
    pygame.display.update()
    
    clock.tick(60)

    




pygame.quit()