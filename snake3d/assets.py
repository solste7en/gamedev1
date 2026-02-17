"""
Assets and constants for Snake3D oblique/Stardew Valley-style game.

Contains tile dimensions, colors with 3D shading, and game configurations.
Uses square tiles with depth faces for a 3/4 top-down perspective.
"""

# ============== Oblique Tile Dimensions ==============

CELL_SIZE = 24          # Square tile size (width and height)
DEPTH_HEIGHT = 8        # Height of front/depth face for 3D effect

# Legacy compatibility (kept for any remaining isometric references)
TILE_WIDTH = CELL_SIZE
TILE_HEIGHT = CELL_SIZE
TILE_DEPTH = DEPTH_HEIGHT

# Game speed
FPS = 10

# Directions (same as 2D)
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# HUD dimensions
HUD_RIGHT_WIDTH = 140
HUD_TOP_HEIGHT = 55
HUD_PADDING = 8

# ============== Map Size Configurations ==============

MAP_SIZES = {
    'small': {
        'name': 'Small',
        'width': 12,
        'height': 12,
        'description': 'Quick match'
    },
    'medium': {
        'name': 'Medium',
        'width': 18,
        'height': 16,
        'description': 'Balanced gameplay'
    },
    'large': {
        'name': 'Large',
        'width': 24,
        'height': 20,
        'description': 'Spacious arena'
    },
    'extra_large': {
        'name': 'Extra Large',
        'width': 30,
        'height': 24,
        'description': 'Epic adventure'
    }
}

MAP_SIZE_ORDER = ['small', 'medium', 'large', 'extra_large']

# ============== Barrier Configurations ==============

BARRIER_DENSITIES = {
    'none': {
        'name': 'None',
        'description': 'Classic mode',
        'multiplier': 1.0,
        'wall_count': 0,
        'pattern': 'none'
    },
    'sparse': {
        'name': 'Sparse',
        'description': 'Light obstacles',
        'multiplier': 1.25,
        'wall_count': 4,
        'pattern': 'scattered'
    },
    'moderate': {
        'name': 'Moderate',
        'description': 'Strategic walls',
        'multiplier': 1.5,
        'wall_count': 8,
        'pattern': 'structured'
    },
    'dense': {
        'name': 'Dense',
        'description': 'Maze challenge',
        'multiplier': 2.0,
        'wall_count': 12,
        'pattern': 'maze'
    }
}

BARRIER_ORDER = ['none', 'sparse', 'moderate', 'dense']

MAP_SIZE_MULTIPLIERS = {
    'small': 1.5,
    'medium': 1.25,
    'large': 1.0,
    'extra_large': 0.9
}

# ============== Basic Colors ==============

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (180, 180, 180)

# ============== Floor/Tile Colors (Stardew Valley Grass Style) ==============

# Grass tones - warm, earthy greens
FLOOR_TOP = (110, 160, 70)            # Main grass color (light)
FLOOR_TOP_ALT = (95, 145, 60)         # Alternate grass (slightly darker)
FLOOR_FRONT = (70, 110, 45)           # Front face (shadowed)
FLOOR_FRONT_ALT = (60, 100, 40)       # Alternate front face
FLOOR_OUTLINE = (80, 120, 50)         # Subtle grid lines

# Dirt/path tones (for variety)
DIRT_TOP = (180, 140, 100)
DIRT_TOP_ALT = (165, 125, 85)
DIRT_FRONT = (130, 95, 65)

# ============== Snake Colors (Vibrant Green with Depth) ==============

# Snake head - bright, friendly green
SNAKE_HEAD_TOP = (80, 200, 80)        # Top face - bright green
SNAKE_HEAD_FRONT = (45, 130, 45)      # Front face - darker
SNAKE_HEAD_HIGHLIGHT = (150, 255, 150) # Eye highlight
SNAKE_EYE_WHITE = (255, 255, 255)
SNAKE_EYE_PUPIL = (20, 20, 20)
SNAKE_TONGUE = (255, 80, 80)

# Snake body - rich green with pattern
SNAKE_BODY_TOP = (70, 180, 70)        # Top face
SNAKE_BODY_TOP_ALT = (60, 165, 60)    # Alternate for pattern
SNAKE_BODY_FRONT = (40, 120, 40)      # Front face
SNAKE_BODY_FRONT_ALT = (35, 105, 35)  # Alternate front
SNAKE_BODY_PATTERN = (90, 200, 90)    # Scale highlights
SNAKE_BODY_HIGHLIGHT = (100, 220, 100)

# Snake tail - tapers off
SNAKE_TAIL_TOP = (55, 150, 55)
SNAKE_TAIL_FRONT = (30, 100, 30)

# Legacy compatibility
SNAKE_HEAD_LEFT = SNAKE_HEAD_FRONT
SNAKE_HEAD_RIGHT = SNAKE_HEAD_FRONT
SNAKE_BODY_LEFT = SNAKE_BODY_FRONT
SNAKE_BODY_RIGHT = SNAKE_BODY_FRONT
SNAKE_TAIL_LEFT = SNAKE_TAIL_FRONT
SNAKE_TAIL_RIGHT = SNAKE_TAIL_FRONT

# ============== Wall Colors (Wooden/Stone Blocks) ==============

# Wood style walls (warm brown)
WALL_TOP = (160, 120, 80)             # Top face - lighter wood
WALL_FRONT = (100, 70, 45)            # Front face - darker wood
WALL_HIGHLIGHT = (190, 150, 110)      # Wood grain highlights
WALL_OUTLINE = (70, 50, 30)           # Block outline

# Stone style (alternative)
STONE_TOP = (140, 140, 145)
STONE_FRONT = (90, 90, 95)
STONE_OUTLINE = (60, 60, 65)

# Legacy compatibility
WALL_LEFT = WALL_FRONT
WALL_RIGHT = WALL_FRONT

# ============== Food/Animal Colors (Warm, Pixel Art Style) ==============

# Small animals
MOUSE_BODY = (180, 170, 165)
MOUSE_EAR = (255, 190, 200)
MOUSE_TAIL = (255, 170, 175)

FROG_BODY = (80, 200, 80)
FROG_BELLY = (160, 230, 160)
FROG_EYE = (255, 220, 50)

BUG_BODY = (150, 85, 35)
BUG_SHELL = (180, 100, 55)
BUG_LEGS = (110, 75, 40)

CRICKET_BODY = (100, 70, 45)
CRICKET_LEGS = (75, 50, 30)

WORM_BODY = (255, 165, 165)
WORM_SEGMENT = (255, 135, 135)

BUTTERFLY_WING1 = (255, 130, 200)
BUTTERFLY_WING2 = (255, 190, 220)
BUTTERFLY_BODY = (80, 60, 50)

SPIDER_BODY = (55, 50, 50)
SPIDER_LEGS = (40, 35, 35)

SNAIL_SHELL = (220, 190, 150)
SNAIL_BODY = (255, 225, 195)

ANT_BODY = (50, 40, 30)
ANT_LEGS = (35, 25, 15)

BEE_BODY = (255, 210, 70)
BEE_STRIPES = (50, 40, 25)
BEE_WINGS = (220, 235, 255)

LADYBUG_SHELL = (230, 60, 60)
LADYBUG_SPOTS = (25, 25, 25)
LADYBUG_HEAD = (35, 35, 35)

FIREFLY_BODY = (70, 60, 50)
FIREFLY_GLOW = (220, 255, 130)

# Medium animals
RABBIT_BODY = (235, 215, 195)
RABBIT_EAR_INNER = (255, 195, 205)
RABBIT_NOSE = (255, 160, 165)
RABBIT_EYE = (60, 50, 50)

LIZARD_BODY = (75, 140, 75)
LIZARD_BELLY = (155, 195, 120)
LIZARD_SPOTS = (50, 100, 50)
LIZARD_EYE = (255, 210, 50)

FISH_BODY = (120, 195, 235)
FISH_SCALES = (95, 175, 215)
FISH_FIN = (75, 155, 195)
FISH_EYE = (40, 40, 40)

SNAKE_PREY_BODY = (135, 115, 95)
SNAKE_PREY_PATTERN = (115, 95, 75)
SNAKE_PREY_BELLY = (175, 155, 135)

TURTLE_SHELL = (95, 140, 75)
TURTLE_SHELL_PATTERN = (75, 115, 55)
TURTLE_SKIN = (115, 155, 95)
TURTLE_EYE = (40, 40, 40)

DUCK_BODY = (195, 155, 95)
DUCK_HEAD = (65, 140, 65)
DUCK_BEAK = (255, 180, 50)
DUCK_EYE = (35, 35, 35)

# Large animals
BIRD_BODY = (115, 165, 250)
BIRD_BELLY = (190, 225, 245)
BIRD_WING = (80, 120, 240)
BIRD_BEAK = (255, 180, 50)
BIRD_EYE = (35, 35, 35)

FOX_BODY = (225, 125, 50)
FOX_BELLY = (255, 235, 195)
FOX_TAIL_TIP = (255, 255, 255)
FOX_EYE = (50, 40, 30)

WOLF_BODY = (135, 135, 145)
WOLF_BELLY = (195, 195, 205)
WOLF_MUZZLE = (115, 115, 125)
WOLF_EYE = (215, 195, 65)

DEER_BODY = (195, 155, 115)
DEER_BELLY = (235, 215, 185)
DEER_SPOTS = (215, 175, 135)
DEER_ANTLERS = (115, 95, 75)

PIG_BODY = (255, 195, 195)
PIG_SNOUT = (255, 165, 165)
PIG_EYE = (40, 40, 40)

# Huge animals
TIGER_BODY = (255, 180, 70)
TIGER_STRIPES = (50, 40, 25)
TIGER_BELLY = (255, 235, 195)
TIGER_EYE = (215, 195, 65)

LION_BODY = (235, 195, 115)
LION_MANE = (195, 135, 65)
LION_BELLY = (255, 235, 195)
LION_EYE = (165, 135, 65)

BEAR_BODY = (115, 85, 65)
BEAR_SNOUT = (155, 115, 85)
BEAR_BELLY = (135, 105, 85)
BEAR_EYE = (40, 35, 30)

CROCODILE_BODY = (85, 115, 75)
CROCODILE_BELLY = (155, 175, 135)
CROCODILE_SCALES = (65, 95, 55)
CROCODILE_EYE = (215, 215, 65)

HIPPO_BODY = (145, 125, 135)
HIPPO_BELLY = (195, 175, 185)
HIPPO_MOUTH = (215, 165, 175)
HIPPO_EYE = (50, 45, 50)

ELEPHANT_BODY = (155, 155, 165)
ELEPHANT_EAR = (175, 155, 165)
ELEPHANT_TUSK = (255, 255, 245)
ELEPHANT_EYE = (60, 55, 60)

# ============== Shadow/Highlight Colors ==============

SHADOW_COLOR = (0, 0, 0, 80)          # Semi-transparent shadow
HIGHLIGHT_COLOR = (255, 255, 255, 60)  # Semi-transparent highlight

# ============== Animal Types and Scores ==============

SMALL_ANIMAL_TYPES = [
    'mouse', 'frog', 'bug', 'cricket', 
    'worm', 'butterfly', 'spider', 'snail',
    'ant', 'bee', 'ladybug', 'firefly'
]

MEDIUM_ANIMAL_TYPES = [
    'rabbit', 'lizard', 'fish', 'snake_prey', 'turtle', 'duck'
]

LARGE_ANIMAL_TYPES = [
    'bird', 'fox', 'wolf', 'deer', 'pig'
]

HUGE_ANIMAL_TYPES = [
    'tiger', 'lion', 'bear', 'crocodile', 'hippo', 'elephant'
]

ANIMAL_TYPES = SMALL_ANIMAL_TYPES + MEDIUM_ANIMAL_TYPES + LARGE_ANIMAL_TYPES + HUGE_ANIMAL_TYPES

ANIMAL_SIZES = {
    # Small animals (single cell)
    'mouse': [(0, 0)], 'frog': [(0, 0)], 'bug': [(0, 0)], 'cricket': [(0, 0)],
    'worm': [(0, 0)], 'butterfly': [(0, 0)], 'spider': [(0, 0)], 'snail': [(0, 0)],
    'ant': [(0, 0)], 'bee': [(0, 0)], 'ladybug': [(0, 0)], 'firefly': [(0, 0)],
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
    # Huge animals
    'tiger': 250, 'lion': 280, 'bear': 220, 'crocodile': 200,
    'hippo': 350, 'elephant': 400
}

# ============== Health Colors ==============

HEALTH_COLORS = {
    'full': (80, 220, 80),
    'high': (160, 240, 160),
    'medium': (255, 255, 80),
    'low': (255, 180, 80),
    'critical': (255, 80, 80)
}

def get_health_color(current_health, max_health):
    """Get color based on health ratio."""
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

# ============== UI Colors (Warmer tones) ==============

SCORE_COLOR = WHITE
GAME_OVER_COLOR = (255, 80, 80)
OVERLAY_COLOR = (10, 10, 10)

MENU_BG = (35, 30, 25)
MENU_TITLE = (120, 200, 120)
MENU_TEXT = WHITE
MENU_SELECTED = (130, 255, 130)
MENU_UNSELECTED = (160, 155, 150)
MENU_HIGHLIGHT_BG = (55, 70, 55)
MENU_DESCRIPTION = (190, 185, 180)

HUD_BG = (40, 35, 30)
HUD_BORDER = (80, 75, 65)
HUD_TEXT = WHITE
HUD_LABEL = (160, 155, 150)
HUD_VALUE = (130, 255, 130)
HUD_WARNING = (255, 210, 120)

# ============== Helper Functions ==============

def calculate_score(animal_type, map_size_key, barrier_key):
    """Calculate score with multipliers."""
    base_score = ANIMAL_BASE_SCORES.get(animal_type, 10)
    map_mult = MAP_SIZE_MULTIPLIERS.get(map_size_key, 1.0)
    barrier_config = BARRIER_DENSITIES.get(barrier_key, BARRIER_DENSITIES['none'])
    barrier_mult = barrier_config['multiplier']
    return int(base_score * map_mult * barrier_mult)

def get_difficulty_label(map_size_key, barrier_key):
    """Get difficulty label string."""
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
