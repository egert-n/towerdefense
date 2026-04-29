import pygame as pg
from pygame.math import Vector2
import math
import constants as c

class Enemy(pg.sprite.Sprite):
  def __init__(self, waypoints, image, hp: float, reward: int, speed: float):
    pg.sprite.Sprite.__init__(self)
    self.waypoints = waypoints
    self.pos = Vector2(self.waypoints[0])
    self.target_waypoint = 1
    self.speed = speed
    self.angle = 0
    self.original_image = image
    self.image = pg.transform.rotate(self.original_image, self.angle)
    self.rect = self.image.get_rect()
    self.rect.center = self.pos

    # Combat stats
    self.max_hp = hp
    self.hp     = hp
    self.reward = reward
    self.leaked = False   # set True when the enemy reaches the end of the path

  # ------------------------------------------------------------------

  def take_damage(self, amount: float) -> bool:
    """Reduce HP by amount. Returns True if the enemy dies."""
    self.hp -= amount
    if self.hp <= 0:
      self.hp = 0
      return True
    return False

  def update(self):
    self.move()
    self.rotate()

  def move(self):
    if self.target_waypoint < len(self.waypoints):
      self.target = Vector2(self.waypoints[self.target_waypoint])
      self.movement = self.target - self.pos
    else:
      self.leaked = True
      self.kill()
      return

    dist = self.movement.length()
    if dist >= self.speed:
      self.pos += self.movement.normalize() * self.speed
    else:
      if dist != 0:
        self.pos += self.movement.normalize() * dist
      self.target_waypoint += 1

  def rotate(self):
    dist = self.target - self.pos
    self.angle = math.degrees(math.atan2(-dist[1], dist[0]))
    self.image = pg.transform.rotate(self.original_image, self.angle)
    self.rect = self.image.get_rect()
    self.rect.center = self.pos

  def draw_health_bar(self, surface):
    """Draw an HP bar just above the enemy sprite."""
    BAR_W = 36
    BAR_H = 5
    bx = int(self.pos.x) - BAR_W // 2
    by = int(self.pos.y) - self.rect.height // 2 - 8
    pg.draw.rect(surface, c.RED,   (bx, by, BAR_W, BAR_H))
    fill_w = int(BAR_W * max(self.hp / self.max_hp, 0))
    pg.draw.rect(surface, c.GREEN, (bx, by, fill_w, BAR_H))
