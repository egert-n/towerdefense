import pygame as pg
from enemy import Enemy
from turret import Turret, snap_to_tile, tile_center, load_turret_image
from bullet import Bullet
from button import Button
import constants as c

# -----------------------------------------------------------------------
# Init
# -----------------------------------------------------------------------
pg.init()
clock  = pg.time.Clock()
screen = pg.display.set_mode((c.SCREEN_WIDTH, c.SCREEN_HEIGHT))
pg.display.set_caption("Tower Defence")

# -----------------------------------------------------------------------
# Assets
# -----------------------------------------------------------------------
map_image    = pg.image.load("assets/images/levels/map.png").convert_alpha()
enemy_image  = pg.image.load("assets/images/enemies/enemy_1.png").convert_alpha()
turret_image = load_turret_image()

# -----------------------------------------------------------------------
# Fonts
# -----------------------------------------------------------------------
font_title  = pg.font.SysFont("arial", 16, bold=True)
font_normal = pg.font.SysFont("arial", 14)

# -----------------------------------------------------------------------
# Sprite groups
# -----------------------------------------------------------------------
enemy_group  = pg.sprite.Group()
turret_group = pg.sprite.Group()
bullet_group = pg.sprite.Group()

# -----------------------------------------------------------------------
# Waypoints
# -----------------------------------------------------------------------
WAYPOINTS = [
    (120,   0),
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
    (360, 720),
]

# -----------------------------------------------------------------------
# Game / economy state
# -----------------------------------------------------------------------
money           = c.STARTING_MONEY
money_ref       = [money]   # mutable list so Bullet.update() can add money
placing_turret  = False
selected_turret = None
game_over       = False
game_won        = False
lives           = 20

# -----------------------------------------------------------------------
# Wave state
# -----------------------------------------------------------------------
current_wave     = 0
wave_in_progress = False
enemies_to_spawn = 0
enemies_spawned  = 0
last_spawn_ms    = 0
wave_break_timer = 0


def wave_enemy_stats(wave):
    scale  = wave - 1
    hp     = c.ENEMY_BASE_HP     * (1 + c.ENEMY_HP_SCALE     * scale)
    reward = int(c.ENEMY_BASE_REWARD * (1 + c.ENEMY_REWARD_SCALE * scale))
    speed  = min(c.ENEMY_BASE_SPEED * (1 + c.ENEMY_SPEED_SCALE * scale), c.ENEMY_SPEED_CAP)
    return hp, reward, speed


def enemies_in_wave(wave):
    return c.ENEMIES_PER_WAVE_BASE + c.ENEMIES_PER_WAVE_INC * (wave - 1)


def start_wave():
    global current_wave, wave_in_progress, enemies_to_spawn, enemies_spawned
    global last_spawn_ms, wave_break_timer
    if current_wave >= c.MAX_WAVES:
        return
    current_wave     += 1
    wave_in_progress  = True
    enemies_to_spawn  = enemies_in_wave(current_wave)
    enemies_spawned   = 0
    last_spawn_ms     = pg.time.get_ticks()
    wave_break_timer  = 0


# -----------------------------------------------------------------------
# Sidebar layout
# -----------------------------------------------------------------------
SB_X    = c.MAP_WIDTH + 10
BTN_W   = c.SIDEBAR_WIDTH - 20
BTN_H   = 38
BTN_GAP = 10
_BY0    = 220

btn_start   = Button(SB_X, _BY0,                      BTN_W, BTN_H, "Start Wave",              (30, 120, 200))
btn_buy     = Button(SB_X, _BY0 + (BTN_H+BTN_GAP),   BTN_W, BTN_H, f"Buy Turret (${c.BUY_COST})", c.GREEN)
btn_upgrade = Button(SB_X, _BY0 + (BTN_H+BTN_GAP)*2, BTN_W, BTN_H, "Upgrade",                 c.GOLD)
btn_sell    = Button(SB_X, _BY0 + (BTN_H+BTN_GAP)*3, BTN_W, BTN_H, f"Sell (+${c.SELL_RETURN})", c.RED)
buttons     = [btn_start, btn_buy, btn_upgrade, btn_sell]


# -----------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------

def is_on_map(px, py):
    return 0 <= px < c.MAP_WIDTH and 0 <= py < c.SCREEN_HEIGHT


def tile_occupied(tx, ty):
    return any(t.tile_x == tx and t.tile_y == ty for t in turret_group)


def get_turret_at(px, py):
    for t in turret_group:
        if t.rect.collidepoint(px, py):
            return t
    return None


def draw_sidebar(surface):
    pg.draw.rect(surface, c.SIDEBAR_COLOUR, (c.MAP_WIDTH, 0, c.SIDEBAR_WIDTH, c.SCREEN_HEIGHT))
    pg.draw.line(surface, c.WHITE, (c.MAP_WIDTH, 0), (c.MAP_WIDTH, c.SCREEN_HEIGHT), 2)
    cx = c.MAP_WIDTH + c.SIDEBAR_WIDTH // 2

    # Header stats
    for y, text, col in [
        (12, "TOWER DEFENCE",             c.WHITE),
        (34, f"Wave  {current_wave} / {c.MAX_WAVES}", c.GOLD),
        (56, f"Lives: {lives}",           c.GREEN if lives > 5 else c.RED),
        (78, f"Money: ${money}",          c.GOLD),
    ]:
        s = font_title.render(text, True, col)
        surface.blit(s, (cx - s.get_width()//2, y))

    # Next wave preview (shown between waves)
    info_y = 110
    if not wave_in_progress and 0 < current_wave < c.MAX_WAVES:
        nw = current_wave + 1
        nh, nr, ns = wave_enemy_stats(nw)
        preview = [
            f"-- Wave {nw} preview --",
            f"Enemies : {enemies_in_wave(nw)}",
            f"HP      : {int(nh)}",
            f"Reward  : ${nr} each",
        ]
        for line in preview:
            s = font_normal.render(line, True, (180, 220, 255))
            surface.blit(s, (SB_X, info_y))
            info_y += 16
        info_y += 4

    # Placement hint
    if placing_turret:
        hs = font_normal.render("[ Click map to place ]", True, c.GREEN)
        surface.blit(hs, (cx - hs.get_width()//2, info_y))
        info_y += 20

    # Selected turret details
    if selected_turret and selected_turret.alive():
        rows = [
            ("-- Turret --",                                      c.GOLD),
            (f"Level : {selected_turret.level}/{selected_turret.max_level}", c.WHITE),
            (f"Range : {selected_turret.range}",                 c.WHITE),
            (f"Damage: {selected_turret.damage}",                c.WHITE),
            (f"Rate  : {selected_turret.fire_rate} ms",          c.WHITE),
            (f"Upgrade: ${selected_turret.upgrade_cost}" if selected_turret.can_upgrade
             else "MAX LEVEL",                                    c.GOLD),
        ]
        for text, col in rows:
            s = font_normal.render(text, True, col)
            surface.blit(s, (SB_X, info_y))
            info_y += 16

    # Button states
    btn_start.enabled = not wave_in_progress and current_wave < c.MAX_WAVES and not game_over and not game_won
    btn_start.text    = "Start Wave" if current_wave == 0 else f"Start Wave {current_wave+1}"

    btn_upgrade.enabled = (
        selected_turret is not None and selected_turret.alive()
        and selected_turret.can_upgrade
        and money >= selected_turret.upgrade_cost
    )
    btn_upgrade.text = (
        f"Upgrade (${selected_turret.upgrade_cost})"
        if selected_turret and selected_turret.can_upgrade else "Upgrade"
    )
    btn_sell.enabled = selected_turret is not None and selected_turret.alive()

    for btn in buttons:
        btn.draw(surface)

    hint = font_normal.render("ESC – cancel / deselect", True, c.GREY)
    surface.blit(hint, (SB_X, c.SCREEN_HEIGHT - 28))


def draw_overlay(surface, text, sub=""):
    overlay = pg.Surface((c.MAP_WIDTH, c.SCREEN_HEIGHT), pg.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))
    big = pg.font.SysFont("arial", 52, bold=True)
    sm  = pg.font.SysFont("arial", 24)
    ts = big.render(text, True, c.GOLD)
    surface.blit(ts, (c.MAP_WIDTH//2 - ts.get_width()//2, c.SCREEN_HEIGHT//2 - 40))
    if sub:
        ss = sm.render(sub, True, c.WHITE)
        surface.blit(ss, (c.MAP_WIDTH//2 - ss.get_width()//2, c.SCREEN_HEIGHT//2 + 30))


# -----------------------------------------------------------------------
# Game loop
# -----------------------------------------------------------------------
run = True
while run:
    dt  = clock.tick(c.FPS)
    now = pg.time.get_ticks()

    # Sync money from mutable wrapper (Bullet.update adds reward money)
    money = money_ref[0]

    # ----------------------------------------------------------------
    # Wave spawning
    # ----------------------------------------------------------------
    if wave_in_progress and not game_over:
        if enemies_spawned < enemies_to_spawn:
            if now - last_spawn_ms >= c.SPAWN_INTERVAL_MS:
                hp, reward, speed = wave_enemy_stats(current_wave)
                enemy_group.add(Enemy(WAYPOINTS, enemy_image, hp, reward, speed))
                enemies_spawned += 1
                last_spawn_ms    = now
        elif len(enemy_group) == 0:
            # All enemies spawned and cleared
            wave_in_progress = False
            wave_break_timer = c.WAVE_BREAK_MS
            if current_wave >= c.MAX_WAVES:
                game_won = True

    if not wave_in_progress and wave_break_timer > 0:
        wave_break_timer = max(0, wave_break_timer - dt)

    # ----------------------------------------------------------------
    # Events
    # ----------------------------------------------------------------
    for event in pg.event.get():
        if event.type == pg.QUIT:
            run = False

        if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            placing_turret  = False
            selected_turret = None

        if not game_over and not game_won:
            if btn_start.handle_event(event):
                start_wave()

            if btn_buy.handle_event(event) and money >= c.BUY_COST:
                placing_turret  = not placing_turret
                selected_turret = None

            if btn_upgrade.handle_event(event):
                if selected_turret and selected_turret.can_upgrade:
                    cost = selected_turret.upgrade_cost
                    if money >= cost:
                        selected_turret.upgrade()
                        money        -= cost
                        money_ref[0]  = money

            if btn_sell.handle_event(event) and selected_turret:
                money         += c.SELL_RETURN
                money_ref[0]   = money
                selected_turret.kill()
                selected_turret = None

        if event.type == pg.MOUSEMOTION:
            for btn in buttons:
                btn.handle_event(event)

        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if is_on_map(mx, my) and not game_over and not game_won:
                if placing_turret:
                    tx, ty = snap_to_tile(mx, my)
                    if not tile_occupied(tx, ty):
                        turret_group.add(Turret(tx, ty, turret_image))
                        money        -= c.BUY_COST
                        money_ref[0]  = money
                    placing_turret = False
                else:
                    selected_turret = get_turret_at(mx, my)

    # ----------------------------------------------------------------
    # Update
    # ----------------------------------------------------------------
    if not game_over and not game_won:
        # Keep a snapshot of live enemies before update to detect leakers
        alive_before = set(enemy_group.sprites())

        enemy_group.update()

        # Count enemies that left the group AND had leaked=True (reached the end)
        alive_after = set(enemy_group.sprites())
        removed     = alive_before - alive_after
        for e in removed:
            if getattr(e, "leaked", False):
                lives -= 1
                if lives <= 0:
                    lives     = 0
                    game_over = True

        # Turrets shoot
        for turret in turret_group:
            turret.update(enemy_group, bullet_group, money_ref)

        # Bullets travel
        bullet_group.update(money_ref)

        money = money_ref[0]

    # ----------------------------------------------------------------
    # Draw
    # ----------------------------------------------------------------
    screen.fill(c.SIDEBAR_COLOUR)
    screen.blit(map_image, (0, 0))

    if selected_turret and selected_turret.alive():
        selected_turret.draw_range(screen)
        selected_turret.draw_selection(screen)

    # Placement ghost
    if placing_turret:
        mx, my = pg.mouse.get_pos()
        if is_on_map(mx, my):
            tx, ty = snap_to_tile(mx, my)
            cx, cy = tile_center(tx, ty)
            ghost = turret_image.copy()
            ghost.set_alpha(140)
            screen.blit(ghost, ghost.get_rect(center=(cx, cy)))

    turret_group.draw(screen)
    bullet_group.draw(screen)
    enemy_group.draw(screen)

    for e in enemy_group:
        e.draw_health_bar(screen)

    draw_sidebar(screen)

    if game_over:
        draw_overlay(screen, "GAME OVER", "Close the window to exit")
    elif game_won:
        draw_overlay(screen, "YOU WIN!", f"All {c.MAX_WAVES} waves cleared!")

    pg.display.flip()

pg.quit()
