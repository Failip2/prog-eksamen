import pygame
import config as c
import os
import surface

pygame.init()
pygame.font.init()
from pygame.locals import *
pygame.event.set_allowed([QUIT, KEYDOWN, KEYUP, WINDOWRESIZED])

os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"

info = pygame.display.Info()

clock = pygame.time.Clock()


flags = FULLSCREEN | DOUBLEBUF
screen = pygame.display.set_mode((info.current_w, info.current_h), flags)

testSurf = surface.Surface("assets/img/zomb.png", (300, 300))
testSurf2 = surface.Surface("assets/img/zomb.png", (300, 300))
testSurf3 = surface.Surface("assets/img/zomb.png", (300, 300))
testSurf4 = surface.Surface("assets/img/zomb.png", (300, 300))
testBG = surface.Surface("assets/img/nig.png", (info.current_w, info.current_h))
testGroup = pygame.sprite.RenderUpdates(testBG, testSurf, testSurf2, testSurf3, testSurf4)

zoomSurf = pygame.Surface((info.current_w, info.current_h))
zoomRect = zoomSurf.fill((255,0,0))

my_font = pygame.font.SysFont('Comic Sans MS', 30)
testText = my_font.render(str(clock.get_fps()), False, (0, 0, 0)), (0,0)
testTextRect = testText


charControls = {K_UP: (0, c.PLAYER_SPEED), K_DOWN: (0, -c.PLAYER_SPEED), K_RIGHT: (c.PLAYER_SPEED, 0), K_LEFT: (-c.PLAYER_SPEED, 0)}


testBool = True
oldrects = []

while c.GAME_IS_RUNNING:
    for event in pygame.event.get(): 
        if event.type == pygame.QUIT: 
            c.GAME_IS_RUNNING = False
        if event.type == pygame.WINDOWRESIZED:
            info = pygame.display.Info()
            screen = pygame.display.set_mode((info.current_w, info.current_h), flags)
            zoomSurf = pygame.Surface((info.current_w, info.current_h))
            print("nigger")

    ## Clear everything drawn (zoomSurf) in place of green placeholder color.
    #zoomSurf.fill((0,255,0))
    
    rects = testGroup.draw(zoomSurf)
    activerects = []
    for x in rects:
        for y in oldrects:
            if x==y:
                continue
            activerects.extend([x, y])
    #activerects = [x for x in rects if x not in oldrects]
    print(activerects)
    pygame.display.update(activerects)
    oldrects = rects[:]
    


    drawSurf = pygame.transform.smoothscale_by(zoomSurf, 1)
    drawSurfRect = drawSurf.get_rect()
    drawSurfRect.center = ((info.current_w/2, info.current_h/2))

    # Blits the fully compiled zoomSurf layer (players, terrain, etc.) to 'screen' surface and accounts for zoom offsets
    screen.blit(drawSurf, drawSurfRect)

    testSurf.rect.move_ip(2,1)
    testSurf2.rect.move_ip(3,1)
    testSurf3.rect.move_ip(1,0)
    testSurf4.rect.move_ip(0, 1)
    
    clock.tick()
    #print(clock.get_fps())
    if testBool:
        pygame.display.flip()
        testBool = False
    




pygame.quit()