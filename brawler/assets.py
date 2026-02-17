"""
Assets and constants for Brawler game.

Contains brawler stats, colors, arena dimensions, and game configuration.
"""

import math

# ============== Display Settings ==============

TILE_SIZE = 32          # Base tile size for isometric grid
ISO_ANGLE = 30          # Degrees for isometric projection
FPS = 60                # Game runs at 60 FPS for smooth action

# Window dimensions
WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768

# Arena dimensions (in tiles)
ARENA_WIDTH = 21        # Odd number for center line
ARENA_HEIGHT = 15

# Goal dimensions
GOAL_WIDTH = 3          # Width of goal opening
GOAL_DEPTH = 2          # Depth of goal area

# HUD dimensions
HUD_HEIGHT = 80
SCOREBOARD_HEIGHT = 50

# ============== Game Settings ==============

MATCH_DURATION = 120    # 2 minutes in seconds
GOALS_TO_WIN = 2        # First to 2 goals wins
RESPAWN_TIME = 3.0      # Seconds to respawn after death
SUPER_CHARGE_MAX = 100  # Super meter maximum

# ============== Physics ==============

FRICTION = 0.92         # Movement friction
BALL_FRICTION = 0.98    # Ball slows down slower
BALL_KICK_FORCE = 12    # Force when kicking ball
KNOCKBACK_FORCE = 8     # Knockback from attacks

# ============== Colors ==============

# Basic colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (192, 192, 192)

# Team colors
TEAM_BLUE = (70, 130, 230)
TEAM_BLUE_LIGHT = (100, 160, 255)
TEAM_BLUE_DARK = (40, 90, 180)

TEAM_RED = (230, 70, 70)
TEAM_RED_LIGHT = (255, 100, 100)
TEAM_RED_DARK = (180, 40, 40)

# Arena colors (sandy/desert like Brawl Stars)
ARENA_FLOOR = (220, 180, 120)
ARENA_FLOOR_ALT = (200, 160, 100)
ARENA_FLOOR_DARK = (160, 130, 85)
ARENA_WALL = (140, 100, 60)
ARENA_WALL_DARK = (100, 70, 40)
ARENA_WALL_TOP = (180, 140, 90)
ARENA_GRASS = (100, 160, 80)
ARENA_GRASS_ALT = (80, 140, 60)
ARENA_LINE = (255, 255, 255)

# Goal colors
GOAL_BLUE = (50, 100, 200)
GOAL_BLUE_NET = (30, 70, 150)
GOAL_RED = (200, 50, 50)
GOAL_RED_NET = (150, 30, 30)

# Ball color
BALL_COLOR = (255, 255, 255)
BALL_OUTLINE = (50, 50, 50)
BALL_PATTERN = (200, 200, 200)

# UI colors
UI_BG = (30, 30, 40)
UI_BORDER = (80, 80, 100)
UI_TEXT = WHITE
UI_TEXT_SHADOW = (20, 20, 30)
HEALTH_BAR_BG = (40, 40, 40)
HEALTH_BAR_GREEN = (80, 200, 80)
HEALTH_BAR_YELLOW = (220, 200, 50)
HEALTH_BAR_RED = (220, 60, 60)
SUPER_BAR_COLOR = (255, 220, 50)
SUPER_BAR_READY = (255, 180, 0)

# ============== Brawler Colors ==============

# Colt - Blue outfit, brown hair
COLT_PRIMARY = (70, 120, 200)
COLT_SECONDARY = (50, 90, 160)
COLT_HAIR = (120, 80, 40)
COLT_SKIN = (240, 200, 160)
COLT_BULLET = (255, 220, 100)

# Shelly - Purple outfit, dark hair
SHELLY_PRIMARY = (160, 80, 180)
SHELLY_SECONDARY = (120, 50, 140)
SHELLY_HAIR = (60, 40, 30)
SHELLY_SKIN = (220, 180, 140)
SHELLY_PELLET = (255, 200, 150)

# Piper - Pink dress, blonde hair
PIPER_PRIMARY = (255, 150, 180)
PIPER_SECONDARY = (220, 100, 140)
PIPER_HAIR = (255, 220, 150)
PIPER_SKIN = (255, 220, 200)
PIPER_BULLET = (255, 100, 150)

# Edgar - Red hoodie, dark spiky hair
EDGAR_PRIMARY = (200, 50, 50)
EDGAR_SECONDARY = (150, 30, 30)
EDGAR_HAIR = (40, 30, 50)
EDGAR_SKIN = (240, 200, 170)
EDGAR_SLASH = (255, 100, 100)

# ============== Brawler Stats ==============

# Speed values (pixels per second at 60 FPS)
SPEED_SLOW = 180
SPEED_NORMAL = 220
SPEED_FAST = 260
SPEED_VERY_FAST = 300

# Range values (in pixels)
RANGE_MELEE = 60
RANGE_SHORT = 150
RANGE_MEDIUM = 250
RANGE_LONG = 350
RANGE_VERY_LONG = 450

BRAWLER_STATS = {
    'colt': {
        'name': 'Colt',
        'max_health': 3600,
        'speed': SPEED_FAST,
        'attack_range': RANGE_LONG,
        'attack_damage': 420,       # Per bullet
        'attack_projectiles': 6,    # Bullets per attack
        'attack_spread': 0.05,      # Radians spread
        'reload_time': 1.3,         # Seconds
        'max_ammo': 3,
        'projectile_speed': 600,
        'super_damage': 420,
        'super_projectiles': 12,
        'super_charge_per_hit': 8,  # Percent per hit dealt
        'super_charge_per_damage': 10,  # Percent per 1000 damage taken
        'description': 'Long-range sharpshooter with rapid-fire bullets',
        'colors': {
            'primary': COLT_PRIMARY,
            'secondary': COLT_SECONDARY,
            'hair': COLT_HAIR,
            'skin': COLT_SKIN,
            'projectile': COLT_BULLET
        }
    },
    'shelly': {
        'name': 'Shelly',
        'max_health': 5100,
        'speed': SPEED_NORMAL,
        'attack_range': RANGE_MEDIUM,
        'attack_damage': 420,       # Per pellet
        'attack_projectiles': 5,    # Pellets per attack
        'attack_spread': 0.4,       # Wide spread (radians)
        'reload_time': 1.5,
        'max_ammo': 3,
        'projectile_speed': 500,
        'super_damage': 480,
        'super_projectiles': 9,
        'super_knockback': 300,     # Knockback force
        'super_charge_per_hit': 7,
        'super_charge_per_damage': 12,
        'description': 'Close-range brawler with devastating spread shot',
        'colors': {
            'primary': SHELLY_PRIMARY,
            'secondary': SHELLY_SECONDARY,
            'hair': SHELLY_HAIR,
            'skin': SHELLY_SKIN,
            'projectile': SHELLY_PELLET
        }
    },
    'piper': {
        'name': 'Piper',
        'max_health': 2800,
        'speed': SPEED_SLOW,
        'attack_range': RANGE_VERY_LONG,
        'attack_damage_min': 1400,  # Damage at point blank
        'attack_damage_max': 2800,  # Damage at max range
        'attack_projectiles': 1,
        'attack_spread': 0,
        'reload_time': 2.3,
        'max_ammo': 3,
        'projectile_speed': 700,
        'super_grenades': 4,
        'super_grenade_damage': 900,
        'super_jump_range': 300,
        'super_charge_per_hit': 15,
        'super_charge_per_damage': 15,
        'description': 'Long-range sniper, damage increases with distance',
        'colors': {
            'primary': PIPER_PRIMARY,
            'secondary': PIPER_SECONDARY,
            'hair': PIPER_HAIR,
            'skin': PIPER_SKIN,
            'projectile': PIPER_BULLET
        }
    },
    'edgar': {
        'name': 'Edgar',
        'max_health': 4200,
        'speed': SPEED_VERY_FAST,
        'attack_range': RANGE_MELEE,
        'attack_damage': 756,       # Per punch
        'attack_projectiles': 2,    # Double punch
        'attack_spread': 0.6,       # Wide melee arc
        'reload_time': 0.7,         # Very fast
        'max_ammo': 2,
        'heal_percent': 0.35,       # Heals 35% of damage dealt
        'super_jump_range': 350,
        'super_auto_charge': 2.5,   # Percent per second auto-charge
        'super_charge_per_hit': 5,
        'super_charge_per_damage': 8,
        'description': 'Assassin that heals when dealing damage',
        'colors': {
            'primary': EDGAR_PRIMARY,
            'secondary': EDGAR_SECONDARY,
            'hair': EDGAR_HAIR,
            'skin': EDGAR_SKIN,
            'projectile': EDGAR_SLASH
        }
    }
}

# ============== Projectile Settings ==============

BULLET_RADIUS = 6
PELLET_RADIUS = 5
SNIPER_RADIUS = 8
MELEE_ARC_ANGLE = 90    # Degrees

# ============== Ball Settings ==============

BALL_RADIUS = 18
BALL_PICKUP_RANGE = 30
BALL_SHOOT_SPEED = 400

# ============== Character Dimensions ==============

BRAWLER_RADIUS = 20     # Collision radius
BRAWLER_HEIGHT = 48     # Visual height for drawing

# ============== AI Settings ==============

AI_REACTION_TIME = 0.15  # Seconds delay before AI reacts
AI_AIM_ERROR = 0.15      # Radians of random aim error
AI_AGGRESSION = {
    'colt': 0.6,
    'shelly': 0.8,
    'piper': 0.3,
    'edgar': 0.9
}

# ============== Controls ==============

CONTROLS = {
    'player1': {
        'up': 'w',
        'down': 's',
        'left': 'a',
        'right': 'd',
        'attack': 'space',
        'super': 'e'
    },
    'player2': {
        'up': 'up',
        'down': 'down',
        'left': 'left',
        'right': 'right',
        'attack': 'return',
        'super': 'rshift'
    }
}

# ============== Helper Functions ==============

def get_health_color(health_percent):
    """Get health bar color based on percentage."""
    if health_percent > 0.6:
        return HEALTH_BAR_GREEN
    elif health_percent > 0.3:
        return HEALTH_BAR_YELLOW
    else:
        return HEALTH_BAR_RED


def get_team_colors(team):
    """Get team colors tuple (main, light, dark)."""
    if team == 0:
        return (TEAM_BLUE, TEAM_BLUE_LIGHT, TEAM_BLUE_DARK)
    else:
        return (TEAM_RED, TEAM_RED_LIGHT, TEAM_RED_DARK)


def lerp(a, b, t):
    """Linear interpolation."""
    return a + (b - a) * t


def distance(pos1, pos2):
    """Calculate distance between two points."""
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    return math.sqrt(dx * dx + dy * dy)


def angle_to(pos1, pos2):
    """Calculate angle from pos1 to pos2."""
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    return math.atan2(dy, dx)


def normalize(x, y):
    """Normalize a vector."""
    length = math.sqrt(x * x + y * y)
    if length == 0:
        return (0, 0)
    return (x / length, y / length)
