import pygame as pg
from pygame.math import Vector2
import math
import constants as c
from bullet import Bullet

# -----------------------------------------------------------------------
# Shoot sound (loaded once at module level)
# -----------------------------------------------------------------------
_shoot_sound = None
try:
    _shoot_sound = pg.mixer.Sound("assets/audio/freesound_community-shoot-6-81136.mp3")
    _shoot_sound.set_volume(0.1)
except Exception:
    pass  # mixer not ready yet or file missing — will retry on first shot

def _get_shoot_sound():
    global _shoot_sound
    if _shoot_sound is None:
        try:
            _shoot_sound = pg.mixer.Sound("assets/audio/freesound_community-shoot-6-81136.mp3")
            _shoot_sound.set_volume(0.1)
        except Exception:
            pass
    return _shoot_sound


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

    _images: dict = {}         # level -> large VISUAL image (unrotated)
    _hit_sizes    = {1: 32, 2: 38, 3: 44}    # hitbox size per level (px)
    _visual_sizes = {1: 160, 2: 168, 3: 176} # visual size per level (px)

    def __init__(self, tile_x: int, tile_y: int, base_images: dict):
        super().__init__()

        self.tile_x = tile_x
        self.tile_y = tile_y
        self.pos = Vector2(
            tile_x * c.TILE_SIZE + c.TILE_SIZE // 2,
            tile_y * c.TILE_SIZE + c.TILE_SIZE // 2,
        )

        self.level    = 1
        self.selected = False
        self.angle    = 0  # current facing angle in degrees

        # Rebuild image cache using per-level source PNGs
        Turret._images = {}
        for lvl in range(1, 4):
            size = Turret._visual_sizes[lvl]
            Turret._images[lvl] = pg.transform.smoothscale(base_images[lvl], (size, size))

        # self.image = visual image drawn on screen (rotated in _apply_rotation)
        # self.hit_rect = small rect used for click / selection detection
        self.image = Turret._images[self.level]
        self.rect  = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))

        hs = Turret._hit_sizes[self.level]
        self.hit_rect = pg.Rect(0, 0, hs, hs)
        self.hit_rect.center = self.rect.center

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
            hs = Turret._hit_sizes[self.level]
            self.hit_rect = pg.Rect(0, 0, hs, hs)
            self.hit_rect.center = (int(self.pos.x), int(self.pos.y))
            self._apply_rotation(self.angle)
            return True
        return False

    def update(self, enemy_group=None, bullet_group=None, money_ref=None):
        """Rotate toward the best target; fire if cooldown is ready."""
        if enemy_group is None or bullet_group is None:
            return

        target = self._pick_target(enemy_group)

        # Always rotate toward the current target (smooth tracking)
        if target is not None:
            dx = target.pos.x - self.pos.x
            dy = target.pos.y - self.pos.y
            new_angle = math.degrees(math.atan2(-dy, dx))
            if new_angle != self.angle:
                self.angle = new_angle
                self._apply_rotation(self.angle)

            # Fire if cooldown elapsed
            now = pg.time.get_ticks()
            if now - self._last_shot_ms >= self.fire_rate:
                bullet = Bullet(self.pos, target, self.damage)
                bullet_group.add(bullet)
                self._last_shot_ms = now
                snd = _get_shoot_sound()
                if snd:
                    snd.play()

    def draw_turret(self, surface):
        """Blit the visual image (self.image) centred on pos."""
        surface.blit(self.image, self.rect)

    def draw_selection(self, surface):
        """Draw selection outline around the small hit_rect."""
        pg.draw.rect(surface, c.WHITE, self.hit_rect.inflate(6, 6), width=2)
        r = self.range
        if r not in self._range_surf:
            diam = r * 2
            rs = pg.Surface((diam, diam), pg.SRCALPHA)
            pg.draw.circle(rs, c.RANGE_COLOUR, (r, r), r)
            self._range_surf[r] = rs
        surf = self._range_surf[r]
        surface.blit(surf, (int(self.pos.x) - r, int(self.pos.y) - r))

    def draw_range(self, surface):
        r = self.range
        if r not in self._range_surf:
            diam = r * 2
            rs = pg.Surface((diam, diam), pg.SRCALPHA)
            pg.draw.circle(rs, c.RANGE_COLOUR, (r, r), r)
            self._range_surf[r] = rs
        surf = self._range_surf[r]
        surface.blit(surf, (int(self.pos.x) - r, int(self.pos.y) - r))

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _apply_rotation(self, angle: float):
        """Rotate self.image to face the given angle; keep hit_rect centred."""
        original = Turret._images[self.level]
        self.image = pg.transform.rotate(original, angle)
        self.rect  = self.image.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        self.hit_rect.center = self.rect.center

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


def load_turret_images() -> dict:
    """Load one PNG per turret level. Falls back to placeholder if missing.
    Returns {1: Surface, 2: Surface, 3: Surface}."""
    images = {}
    for lvl in range(1, 4):
        path = f"assets/images/turrets/pixil-frame-{lvl - 1}.png"
        try:
            images[lvl] = pg.image.load(path).convert_alpha()
        except (pg.error, FileNotFoundError):
            images[lvl] = _make_placeholder(40)
    return images


# Keep old name as alias so existing code doesn't break
def load_turret_image() -> pg.Surface:
    return load_turret_images()[1]
