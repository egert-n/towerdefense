import pygame as pg
import json
from enemy import Enemy
from world import World
import constants as c

#initialise pygame
pg.init()

#create clock
clock = pg.time.Clock()

#create game window
screen = pg.display.set_mode((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
pg.display.set_caption("Tower Defence")

#load images
#map
map_image = pg.image.load('assets/images/levels/map.png').convert_alpha()
#enemy
enemy_image = pg.image.load('assets/images/enemies/enemy_1.png').convert_alpha()

#create groups
enemy_group = pg.sprite.Group()

waypoints = [
(120, 0),
(120, 120),
(600, 120),
(600, 360),
(360, 360),
(360, 264),
(216, 264),
(216, 360),
(120, 360),
(120, 504),
(600, 504),
(600, 648),
(360, 648),
(360, 720)
]

enemy = Enemy(waypoints, enemy_image)
enemy_group.add(enemy)

#game loop
run = True
while run:

  clock.tick(c.FPS)

  screen.fill("grey100")

  screen.blit(map_image, (0, 0))

  #draw enemy path
  pg.draw.lines(screen, "grey0", False, waypoints)

  #update groups
  enemy_group.update()

  #draw groups
  enemy_group.draw(screen)

  #event handler
  for event in pg.event.get():
    #quit program
    if event.type == pg.QUIT:
      run = False

  #update display
  pg.display.flip()

pg.quit()
