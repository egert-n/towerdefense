import pygame as pg
from pygame.math import Vector2
import constants as c
from bullet import Bullet


def _make_placeholder(size=40):
    """Create a simple grey circle turret image for when no PNG is available."""
    surf = pg.Surface((size, size), pg.SRCALPHA)
    cx, cy = size // 2, size // 2
    pg.draw.circle(surf, (80, 80, 120), (cx, cy), size // 2)        # base
    pg.draw.circle(surf, (140, 140, 180), (cx, cy), size // 2, 2)   # rim
    # barrel pointing right
    pg.draw.rect(surf, (160, 160, 200), (cx, cy - 3, cx - 4, 6))
    return surf


class Turret(pg.sprite.Sprite):
    """A placeable, upgradeable tower.

    Levels 1-3 are defined in constants.TURRET_DATA.
    Call update(enemy_group, bullet_group, money_ref) each frame.
    """

    _images: dict = {}    # level -> Surface cache (shared across instances)

    def __init__(self, tile_x: int, tile_y: int, base_image: pg.Surface):
        super().__init__()

        self.tile_x = tile_x
        self.tile_y = tile_y
        self.pos = Vector2(
            tile_x * c.TILE_SIZE + c.TILE_SIZE // 2,
            tile_y * c.TILE_SIZE + c.TILE_SIZE // 2,
        )

        self.level    = 1
        self.selected = False

        # Build per-level scaled images from the supplied base
        if not Turret._images:
            for lvl in range(1, 4):
                size = 32 + (lvl - 1) * 6
                scaled = pg.transform.smoothscale(base_image, (size, size))
                Turret._images[lvl] = scaled

        self.image = Turret._images[self.level]
        self.rect  = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

        # Fire-rate timer (ms since last shot)
        self._last_shot_ms: int = 0

        # Range circle cache
        self._range_surf: dict = {}

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def stats(self):
        return c.TURRET_DATA[self.level]

    @property
    def range(self):
        return self.stats["range"]

    @property
    def damage(self):
        return self.stats["damage"]

    @property
    def fire_rate(self):
        return self.stats["fire_rate"]

    @property
    def max_level(self):
        return max(c.TURRET_DATA.keys())

    @property
    def can_upgrade(self):
        return self.level < self.max_level

    @property
    def upgrade_cost(self):
        if self.can_upgrade:
            return c.TURRET_DATA[self.level + 1]["cost"]
        return 0

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def upgrade(self):
        if self.can_upgrade:
            self.level += 1
            self.image = Turret._images[self.level]
            self.rect  = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
            return True
        return False

    def update(self, enemy_group=None, bullet_group=None, money_ref=None):
        """Find the nearest enemy in range and fire if cooldown is ready."""
        if enemy_group is None or bullet_group is None:
            return

        now = pg.time.get_ticks()
        if now - self._last_shot_ms < self.fire_rate:
            return

        target = self._pick_target(enemy_group)
        if target is None:
            return

        bullet = Bullet(self.pos, target, self.damage)
        bullet_group.add(bullet)
        self._last_shot_ms = now

    def draw_range(self, surface):
        r = self.range
        if r not in self._range_surf:
            diam = r * 2
            rs = pg.Surface((diam, diam), pg.SRCALPHA)
            pg.draw.circle(rs, c.RANGE_COLOUR, (r, r), r)
            self._range_surf[r] = rs
        surf = self._range_surf[r]
        surface.blit(surf, (int(self.pos.x) - r, int(self.pos.y) - r))

    def draw_selection(self, surface):
        pg.draw.rect(surface, c.WHITE, self.rect.inflate(6, 6), width=2)

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _pick_target(self, enemy_group):
        """Return the enemy that has progressed furthest along the path
        (highest target_waypoint, tie-broken by distance to next waypoint)
        and is within this turret's range, or None."""
        best = None
        best_progress = -1
        r2 = self.range ** 2

        for enemy in enemy_group:
            dx = enemy.pos.x - self.pos.x
            dy = enemy.pos.y - self.pos.y
            if dx * dx + dy * dy <= r2:
                # Use waypoint index as primary progress metric
                progress = enemy.target_waypoint
                if progress > best_progress:
                    best_progress = progress
                    best = enemy

        return best



# ------------------------------------------------------------------
# Helpers used by game.py
# ------------------------------------------------------------------

def snap_to_tile(pixel_x: int, pixel_y: int):
    """Return the (tile_x, tile_y) for a pixel position."""
    return pixel_x // c.TILE_SIZE, pixel_y // c.TILE_SIZE


def tile_center(tile_x: int, tile_y: int):
    """Return the pixel centre of a tile."""
    return (
        tile_x * c.TILE_SIZE + c.TILE_SIZE // 2,
        tile_y * c.TILE_SIZE + c.TILE_SIZE // 2,
    )


def load_turret_image() -> pg.Surface:
    """Load turret PNG or fall back to a procedurally generated placeholder."""
    try:
        img = pg.image.load("assets/images/turrets/turret.png").convert_alpha()
    except (pg.error, FileNotFoundError):
        img = _make_placeholder(40)
    return img
