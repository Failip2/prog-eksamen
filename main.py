import pygame
import config as c
import os

pygame.init()

os.environ['SDL_VIDEO_WINDOW_POS'] = "0,0"

info = pygame.display.Info()

clock = pygame.time.Clock()
screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.NOFRAME)


zoomSurf = 

surf = pygame.image.load("assets/img/slefenheimer.png").convert_alpha()
surf = pygame.transform.scale(surf, (300, 300))


while c.GAME_IS_RUNNING:
    for event in pygame.event.get(): 
        if event.type == pygame.QUIT: 
            c.GAME_IS_RUNNING = False


    screen.blit(surf, (0, 0))
    pygame.display.flip()
    pygame.display.update()
    
    clock.tick(60)

    




pygame.quit()