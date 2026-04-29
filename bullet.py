import pygame as pg
from pygame.math import Vector2
import constants as c


class Bullet(pg.sprite.Sprite):
    """A projectile that homes toward a target enemy and deals damage on hit.

    The bullet is owned by a turret but lives in a shared bullet_group so it
    can be drawn and updated independently.  When the target is already dead
    (killed by another bullet) the bullet simply removes itself.
    """

    def __init__(self, origin: Vector2, target, damage: float):
        super().__init__()
        self.pos    = Vector2(origin)
        self.target = target          # Enemy sprite; may be killed before we arrive
        self.damage = damage

        # Build a small circle surface for the bullet
        d = c.BULLET_RADIUS * 2
        self.image = pg.Surface((d, d), pg.SRCALPHA)
        pg.draw.circle(self.image, c.BULLET_COLOUR, (c.BULLET_RADIUS, c.BULLET_RADIUS), c.BULLET_RADIUS)
        # bright white core
        pg.draw.circle(self.image, (255, 255, 255), (c.BULLET_RADIUS, c.BULLET_RADIUS), max(1, c.BULLET_RADIUS // 2))

        self.rect = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

    # ------------------------------------------------------------------

    def update(self, money_ref: list):
        """Move toward target.  money_ref is a one-element list so we can
        mutate the caller's money value without a global."""

        # Target was killed before we arrived
        if not self.target.alive():
            self.kill()
            return

        direction = Vector2(self.target.pos) - self.pos
        dist = direction.length()

        if dist <= c.BULLET_SPEED:
            # Hit!
            self.pos = Vector2(self.target.pos)
            died = self.target.take_damage(self.damage)
            if died:
                money_ref[0] += self.target.reward
                self.target.kill()
            self.kill()
        else:
            self.pos += direction.normalize() * c.BULLET_SPEED
            self.rect.center = (int(self.pos.x), int(self.pos.y))
