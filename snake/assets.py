"""
Game assets and constants for the Snake Game.
Contains colors, dimensions, and other game configuration.
"""

# Cell size (pixels per grid cell)
CELL_SIZE = 20

# Game speed (frames per second)
FPS = 10

# HUD (Heads-Up Display) dimensions
HUD_TOP_HEIGHT = 55      # Space above play area for score/info
HUD_RIGHT_WIDTH = 150    # Space to the right for additional info
HUD_PADDING = 8          # Padding within HUD areas

# Directions
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# ============== Map Size Configurations ==============

MAP_SIZES = {
    'small': {
        'name': 'Small',
        'width': 15,    # 300px
        'height': 12,   # 240px
        'description': 'Tight quarters - Quick games'
    },
    'medium': {
        'name': 'Medium',
        'width': 25,    # 500px
        'height': 18,   # 360px
        'description': 'Balanced gameplay'
    },
    'large': {
        'name': 'Large',
        'width': 35,    # 700px
        'height': 22,   # 440px
        'description': 'Room to roam'
    },
    'extra_large': {
        'name': 'Extra Large',
        'width': 45,    # 900px
        'height': 28,   # 560px
        'description': 'Wide open spaces'
    }
}

MAP_SIZE_ORDER = ['small', 'medium', 'large', 'extra_large']

# ============== Barrier/Wall Configurations ==============

BARRIER_DENSITIES = {
    'none': {
        'name': 'None',
        'description': 'Classic mode - No obstacles',
        'multiplier': 1.0,
        'wall_count': 0,
        'pattern': 'none'
    },
    'sparse': {
        'name': 'Sparse',
        'description': 'A few scattered walls',
        'multiplier': 1.25,
        'wall_count': 4,
        'pattern': 'scattered'
    },
    'moderate': {
        'name': 'Moderate',
        'description': 'Strategic wall placement',
        'multiplier': 1.5,
        'wall_count': 8,
        'pattern': 'structured'
    },
    'dense': {
        'name': 'Dense',
        'description': 'Maze-like challenge',
        'multiplier': 2.0,
        'wall_count': 12,
        'pattern': 'maze'
    }
}

BARRIER_ORDER = ['none', 'sparse', 'moderate', 'dense']

# Map size also affects difficulty (smaller = harder)
MAP_SIZE_MULTIPLIERS = {
    'small': 1.5,
    'medium': 1.25,
    'large': 1.0,
    'extra_large': 0.9
}

# ============== Colors - Basic ==============

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (180, 180, 180)

# ============== Colors - Snake ==============

SNAKE_HEAD_PRIMARY = (34, 139, 34)      # Forest green
SNAKE_HEAD_SECONDARY = (0, 100, 0)       # Dark green
SNAKE_HEAD_ACCENT = (144, 238, 144)      # Light green for highlights
SNAKE_EYE_WHITE = (255, 255, 255)
SNAKE_EYE_PUPIL = (0, 0, 0)
SNAKE_TONGUE = (255, 50, 50)

SNAKE_BODY_PRIMARY = (46, 125, 50)       # Green
SNAKE_BODY_SECONDARY = (27, 94, 32)      # Darker green
SNAKE_BODY_PATTERN = (56, 142, 60)       # Pattern green
SNAKE_BODY_HIGHLIGHT = (76, 175, 80)     # Light scale highlight
SNAKE_BODY_SHADOW = (20, 70, 25)         # Scale shadow

# ============== Colors - Barriers/Walls ==============

WALL_PRIMARY = (101, 67, 33)        # Brown brick
WALL_SECONDARY = (139, 90, 43)      # Lighter brown
WALL_HIGHLIGHT = (160, 120, 80)     # Brick highlight
WALL_SHADOW = (70, 45, 20)          # Brick shadow
WALL_MORTAR = (80, 80, 80)          # Mortar between bricks

# ============== Colors - Animals (Food) ==============

MOUSE_BODY = (169, 169, 169)
MOUSE_EAR = (255, 182, 193)
MOUSE_TAIL = (255, 160, 160)

FROG_BODY = (50, 205, 50)
FROG_BELLY = (144, 238, 144)
FROG_EYE = (255, 215, 0)

BUG_BODY = (139, 69, 19)
BUG_SHELL = (160, 82, 45)
BUG_LEGS = (101, 67, 33)

CRICKET_BODY = (85, 55, 35)
CRICKET_LEGS = (60, 40, 25)

WORM_BODY = (255, 150, 150)
WORM_SEGMENT = (255, 120, 120)

BUTTERFLY_WING1 = (255, 105, 180)
BUTTERFLY_WING2 = (255, 182, 193)
BUTTERFLY_BODY = (70, 50, 40)

SPIDER_BODY = (40, 40, 40)
SPIDER_LEGS = (30, 30, 30)

SNAIL_SHELL = (210, 180, 140)
SNAIL_BODY = (255, 218, 185)

# ============== Animal Types and Scores ==============

# Small animals (1 cell, 1 health)
SMALL_ANIMAL_TYPES = [
    'mouse',
    'frog', 
    'bug',
    'cricket',
    'worm',
    'butterfly',
    'spider',
    'snail',
    'ant',
    'bee',
    'ladybug',
    'firefly'
]

# Medium animals (2-3 cells, 2-3 health)
MEDIUM_ANIMAL_TYPES = [
    'rabbit',    # 2 cells horizontal
    'lizard',    # 3 cells horizontal
    'fish',      # 2 cells horizontal
    'snake_prey',# 3 cells horizontal (small snake as prey)
    'turtle',    # 2x2 cells but only 3 health
    'duck',      # 3 cells horizontal
]

# Large animals (4-5 cells, 4-5 health)
LARGE_ANIMAL_TYPES = [
    'bird',      # 2x2 cells (4 cells)
    'fox',       # 4 cells L-shape
    'wolf',      # 5 cells cross shape
    'deer',      # 4 cells vertical
    'pig',       # 4 cells (2x2)
]

# Huge animals (6-8 cells, 6-8 health)
HUGE_ANIMAL_TYPES = [
    'tiger',     # 6 cells (3x2)
    'lion',      # 6 cells (3x2)
    'bear',      # 6 cells (2x3)
    'crocodile', # 6 cells horizontal
    'hippo',     # 8 cells (4x2)
    'elephant',  # 8 cells (2x4)
]

# All animal types combined
ANIMAL_TYPES = SMALL_ANIMAL_TYPES + MEDIUM_ANIMAL_TYPES + LARGE_ANIMAL_TYPES + HUGE_ANIMAL_TYPES

# Animal sizes - cell offsets from anchor position (0,0)
# Format: list of (dx, dy) tuples representing each cell
ANIMAL_SIZES = {
    # Small animals (single cell)
    'mouse': [(0, 0)],
    'frog': [(0, 0)],
    'bug': [(0, 0)],
    'cricket': [(0, 0)],
    'worm': [(0, 0)],
    'butterfly': [(0, 0)],
    'spider': [(0, 0)],
    'snail': [(0, 0)],
    'ant': [(0, 0)],
    'bee': [(0, 0)],
    'ladybug': [(0, 0)],
    'firefly': [(0, 0)],
    # Medium animals (2-3 cells)
    'rabbit': [(0, 0), (1, 0)],
    'lizard': [(0, 0), (1, 0), (2, 0)],
    'fish': [(0, 0), (1, 0)],
    'snake_prey': [(0, 0), (1, 0), (2, 0)],
    'turtle': [(0, 0), (1, 0), (0, 1)],
    'duck': [(0, 0), (1, 0), (2, 0)],
    # Large animals (4-5 cells)
    'bird': [(0, 0), (1, 0), (0, 1), (1, 1)],
    'fox': [(0, 0), (1, 0), (2, 0), (0, 1)],
    'wolf': [(1, 0), (0, 1), (1, 1), (2, 1), (1, 2)],
    'deer': [(0, 0), (0, 1), (0, 2), (0, 3)],
    'pig': [(0, 0), (1, 0), (0, 1), (1, 1)],
    # Huge animals (6-8 cells)
    'tiger': [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)],
    'lion': [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)],
    'bear': [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2)],
    'crocodile': [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0)],
    'hippo': [(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1), (3, 1)],
    'elephant': [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2), (0, 3), (1, 3)],
}

# Animal health (equals number of cells/hits required)
ANIMAL_HEALTH = {
    # Small (1 health)
    'mouse': 1, 'frog': 1, 'bug': 1, 'cricket': 1,
    'worm': 1, 'butterfly': 1, 'spider': 1, 'snail': 1,
    'ant': 1, 'bee': 1, 'ladybug': 1, 'firefly': 1,
    # Medium (2-3 health)
    'rabbit': 2, 'fish': 2, 'lizard': 3, 'snake_prey': 3, 'turtle': 3, 'duck': 3,
    # Large (4-5 health)
    'bird': 4, 'fox': 4, 'pig': 4, 'wolf': 5, 'deer': 4,
    # Huge (6-8 health)
    'tiger': 6, 'lion': 6, 'bear': 6, 'crocodile': 6, 'hippo': 8, 'elephant': 8
}

# Base score values for different animals (before multipliers)
ANIMAL_BASE_SCORES = {
    # Small animals
    'mouse': 15, 'frog': 20, 'bug': 10, 'cricket': 10,
    'worm': 5, 'butterfly': 25, 'spider': 15, 'snail': 10,
    'ant': 5, 'bee': 20, 'ladybug': 15, 'firefly': 30,
    # Medium animals
    'rabbit': 40, 'fish': 35, 'lizard': 60, 'snake_prey': 70,
    'turtle': 50, 'duck': 55,
    # Large animals
    'bird': 100, 'fox': 120, 'pig': 90, 'wolf': 150, 'deer': 130,
    # Huge animals (big rewards!)
    'tiger': 250, 'lion': 280, 'bear': 220, 'crocodile': 200,
    'hippo': 350, 'elephant': 400
}

# ============== Colors - Small Animals (new) ==============

ANT_BODY = (40, 30, 20)
ANT_LEGS = (30, 20, 10)

BEE_BODY = (255, 200, 50)
BEE_STRIPES = (40, 30, 20)
BEE_WINGS = (200, 220, 255)

LADYBUG_SHELL = (220, 40, 40)
LADYBUG_SPOTS = (20, 20, 20)
LADYBUG_HEAD = (30, 30, 30)

FIREFLY_BODY = (60, 50, 40)
FIREFLY_GLOW = (200, 255, 100)

# ============== Colors - Medium Animals ==============

RABBIT_BODY = (220, 200, 180)
RABBIT_EAR_INNER = (255, 182, 193)
RABBIT_NOSE = (255, 150, 150)
RABBIT_EYE = (50, 50, 50)

LIZARD_BODY = (60, 120, 60)
LIZARD_BELLY = (140, 180, 100)
LIZARD_SPOTS = (40, 80, 40)
LIZARD_EYE = (255, 200, 0)

FISH_BODY = (100, 180, 220)
FISH_SCALES = (80, 160, 200)
FISH_FIN = (60, 140, 180)
FISH_EYE = (30, 30, 30)

SNAKE_PREY_BODY = (120, 100, 80)
SNAKE_PREY_PATTERN = (100, 80, 60)
SNAKE_PREY_BELLY = (160, 140, 120)

TURTLE_SHELL = (80, 120, 60)
TURTLE_SHELL_PATTERN = (60, 100, 40)
TURTLE_SKIN = (100, 140, 80)
TURTLE_EYE = (30, 30, 30)

DUCK_BODY = (180, 140, 80)
DUCK_HEAD = (50, 120, 50)
DUCK_BEAK = (255, 165, 0)
DUCK_EYE = (30, 30, 30)

# ============== Colors - Large Animals ==============

BIRD_BODY = (100, 149, 237)
BIRD_BELLY = (173, 216, 230)
BIRD_WING = (65, 105, 225)
BIRD_BEAK = (255, 165, 0)
BIRD_EYE = (30, 30, 30)

FOX_BODY = (210, 105, 30)
FOX_BELLY = (255, 220, 180)
FOX_TAIL_TIP = (255, 255, 255)
FOX_EYE = (40, 30, 20)

WOLF_BODY = (120, 120, 130)
WOLF_BELLY = (180, 180, 190)
WOLF_MUZZLE = (100, 100, 110)
WOLF_EYE = (200, 180, 50)

DEER_BODY = (180, 140, 100)
DEER_BELLY = (220, 200, 170)
DEER_SPOTS = (200, 160, 120)
DEER_ANTLERS = (100, 80, 60)

PIG_BODY = (255, 180, 180)
PIG_SNOUT = (255, 150, 150)
PIG_EYE = (30, 30, 30)

# ============== Colors - Huge Animals ==============

TIGER_BODY = (255, 165, 50)
TIGER_STRIPES = (40, 30, 20)
TIGER_BELLY = (255, 220, 180)
TIGER_EYE = (200, 180, 50)

LION_BODY = (220, 180, 100)
LION_MANE = (180, 120, 50)
LION_BELLY = (240, 220, 180)
LION_EYE = (150, 120, 50)

BEAR_BODY = (100, 70, 50)
BEAR_SNOUT = (140, 100, 70)
BEAR_BELLY = (120, 90, 70)
BEAR_EYE = (30, 25, 20)

CROCODILE_BODY = (70, 100, 60)
CROCODILE_BELLY = (140, 160, 120)
CROCODILE_SCALES = (50, 80, 40)
CROCODILE_EYE = (200, 200, 50)

HIPPO_BODY = (130, 110, 120)
HIPPO_BELLY = (180, 160, 170)
HIPPO_MOUTH = (200, 150, 160)
HIPPO_EYE = (40, 35, 40)

ELEPHANT_BODY = (140, 140, 150)
ELEPHANT_EAR = (160, 140, 150)
ELEPHANT_TUSK = (255, 255, 240)
ELEPHANT_EYE = (50, 45, 50)

# ============== Health Color Palette ==============

HEALTH_COLORS = {
    'full': (50, 205, 50),        # Green - 100%
    'high': (144, 238, 144),      # Light green - 75%+
    'medium': (255, 255, 0),      # Yellow - 50%+
    'low': (255, 165, 0),         # Orange - 25%+
    'critical': (255, 50, 50)     # Red - below 25%
}

def get_health_color(current_health, max_health):
    """Get the color for health bar based on current/max health ratio."""
    if max_health <= 0:
        return HEALTH_COLORS['critical']
    
    ratio = current_health / max_health
    
    if ratio >= 1.0:
        return HEALTH_COLORS['full']
    elif ratio >= 0.75:
        return HEALTH_COLORS['high']
    elif ratio >= 0.5:
        return HEALTH_COLORS['medium']
    elif ratio >= 0.25:
        return HEALTH_COLORS['low']
    else:
        return HEALTH_COLORS['critical']

# ============== UI Colors ==============

SCORE_COLOR = WHITE
GAME_OVER_COLOR = (255, 50, 50)
OVERLAY_COLOR = BLACK

# Menu colors
MENU_BG = (20, 25, 30)
MENU_TITLE = (100, 200, 100)
MENU_TEXT = WHITE
MENU_SELECTED = (100, 255, 100)
MENU_UNSELECTED = (150, 150, 150)
MENU_HIGHLIGHT_BG = (40, 60, 40)
MENU_DESCRIPTION = (180, 180, 180)

# HUD colors
HUD_BG = (25, 30, 35)
HUD_BORDER = (60, 70, 80)
HUD_TEXT = WHITE
HUD_LABEL = (150, 150, 150)
HUD_VALUE = (100, 255, 100)
HUD_WARNING = (255, 200, 100)

# Level progress colors
PROGRESS_BG = (40, 40, 40)
PROGRESS_FILL = (100, 200, 100)
PROGRESS_BORDER = (80, 80, 80)

# ============== Helper Functions ==============

def get_window_dimensions(map_size_key, include_hud=True):
    """
    Get window dimensions for a given map size.
    
    Args:
        map_size_key: Key from MAP_SIZES dict
        include_hud: Whether to include HUD space (default True)
        
    Returns:
        Tuple of (width, height) in pixels
    """
    config = MAP_SIZES.get(map_size_key, MAP_SIZES['medium'])
    play_width = config['width'] * CELL_SIZE
    play_height = config['height'] * CELL_SIZE
    
    if include_hud:
        return (play_width + HUD_RIGHT_WIDTH, play_height + HUD_TOP_HEIGHT)
    return (play_width, play_height)


def get_window_dimensions_custom(grid_width, grid_height, include_hud=True):
    """
    Get window dimensions for custom grid size.
    
    Args:
        grid_width: Grid width in cells
        grid_height: Grid height in cells
        include_hud: Whether to include HUD space
        
    Returns:
        Tuple of (width, height) in pixels
    """
    play_width = grid_width * CELL_SIZE
    play_height = grid_height * CELL_SIZE
    
    if include_hud:
        return (play_width + HUD_RIGHT_WIDTH, play_height + HUD_TOP_HEIGHT)
    return (play_width, play_height)


def get_play_area_rect(window_width, window_height):
    """
    Get the rectangle defining the play area within a window.
    
    Args:
        window_width: Total window width
        window_height: Total window height
        
    Returns:
        Tuple of (x, y, width, height) for play area
    """
    play_width = window_width - HUD_RIGHT_WIDTH
    play_height = window_height - HUD_TOP_HEIGHT
    return (0, HUD_TOP_HEIGHT, play_width, play_height)


def get_grid_dimensions(map_size_key):
    """
    Get grid dimensions for a given map size.
    
    Args:
        map_size_key: Key from MAP_SIZES dict
        
    Returns:
        Tuple of (grid_width, grid_height) in cells
    """
    config = MAP_SIZES.get(map_size_key, MAP_SIZES['medium'])
    return (config['width'], config['height'])


def calculate_score(animal_type, map_size_key, barrier_key):
    """
    Calculate the score for eating an animal based on difficulty settings.
    
    Args:
        animal_type: Type of animal eaten
        map_size_key: Current map size
        barrier_key: Current barrier density
        
    Returns:
        Integer score value
    """
    base_score = ANIMAL_BASE_SCORES.get(animal_type, 10)
    
    map_multiplier = MAP_SIZE_MULTIPLIERS.get(map_size_key, 1.0)
    barrier_config = BARRIER_DENSITIES.get(barrier_key, BARRIER_DENSITIES['none'])
    barrier_multiplier = barrier_config['multiplier']
    
    # Combined multiplier
    total_multiplier = map_multiplier * barrier_multiplier
    
    return int(base_score * total_multiplier)


def get_difficulty_label(map_size_key, barrier_key):
    """
    Get a human-readable difficulty label based on settings.
    
    Returns:
        String describing the overall difficulty
    """
    map_mult = MAP_SIZE_MULTIPLIERS.get(map_size_key, 1.0)
    barrier_config = BARRIER_DENSITIES.get(barrier_key, BARRIER_DENSITIES['none'])
    barrier_mult = barrier_config['multiplier']
    
    total = map_mult * barrier_mult
    
    if total <= 1.0:
        return "Easy"
    elif total <= 1.5:
        return "Normal"
    elif total <= 2.0:
        return "Hard"
    elif total <= 2.5:
        return "Very Hard"
    else:
        return "Extreme"
