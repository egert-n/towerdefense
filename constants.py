SCREEN_WIDTH = 920   # 720 map + 200 sidebar
SCREEN_HEIGHT = 720
FPS = 60
MAP_WIDTH = 720

# Sidebar
SIDEBAR_WIDTH = 200
SIDEBAR_COLOUR = (60, 60, 80)

# Tile snapping (used when placing turrets)
TILE_SIZE = 48

# Turret stats per level  [range, damage, cost_to_reach_this_level, fire_rate_ms]
TURRET_DATA = {
    1: {"range": 120, "damage": 15,  "cost": 0,   "fire_rate": 1200},
    2: {"range": 160, "damage": 28,  "cost": 150, "fire_rate": 900},
    3: {"range": 220, "damage": 50,  "cost": 250, "fire_rate": 600},
}

# Economy
BUY_COST     = 100
SELL_RETURN  = 50
STARTING_MONEY = 650

# ---- Wave system -------------------------------------------------------
MAX_WAVES               = 20
ENEMIES_PER_WAVE_BASE   = 5     # enemies in wave 1
ENEMIES_PER_WAVE_INC    = 2     # +2 per wave
SPAWN_INTERVAL_MS       = 1400  # ms between individual spawns
WAVE_BREAK_MS           = 4000  # ms break between waves

# Enemy base stats (wave 1)
ENEMY_BASE_HP     = 80
ENEMY_BASE_REWARD = 15          # money earned per kill
ENEMY_BASE_SPEED  = 2.0

# Scaling factors applied each wave  (value *= 1 + SCALE * (wave-1))
ENEMY_HP_SCALE     = 0.20   # +20 % HP per wave
ENEMY_REWARD_SCALE = 0.12   # +12 % reward per wave
ENEMY_SPEED_SCALE  = 0.04   # +4  % speed per wave (caps out quickly)
ENEMY_SPEED_CAP    = 4.5

# ---- Bullet ------------------------------------------------------------
BULLET_SPEED  = 7
BULLET_COLOUR = (255, 220, 40)
BULLET_RADIUS = 5

# Colours
WHITE    = (255, 255, 255)
BLACK    = (0,   0,   0)
GREY     = (100, 100, 120)
RED      = (200, 50,  50)
GREEN    = (50,  180, 50)
GOLD     = (220, 180, 50)
RANGE_COLOUR = (100, 200, 255, 60)   # RGBA for range circle surface
