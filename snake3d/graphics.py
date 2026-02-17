"""
Graphics module for Snake3D - Stardew Valley-style oblique projection.

Contains all drawing functions for square tiles with depth faces,
creating a charming 3/4 top-down perspective.
"""

import pygame
from .oblique import grid_to_screen, get_cube_rects
from .assets import *


# ============== Basic Drawing Primitives ==============

def draw_tile(surface, x, y, width, height, color_top, color_outline=None):
    """
    Draw a simple square tile.
    
    Args:
        surface: Pygame surface
        x, y: Screen position
        width, height: Tile dimensions
        color_top: Fill color
        color_outline: Optional outline color
    """
    pygame.draw.rect(surface, color_top, (x, y, width, height))
    if color_outline:
        pygame.draw.rect(surface, color_outline, (x, y, width, height), 1)


def draw_cube(surface, x, y, width, height, depth, color_top, color_front, 
              color_outline=None, shrink=0):
    """
    Draw a cube with top face and front (depth) face.
    
    The cube appears as:
        ┌───────┐  <- top face (lighter)
        │       │
        ├───────┤
        │       │  <- front face (darker, shows depth)
        └───────┘
    
    Args:
        surface: Pygame surface
        x, y: Top-left screen position
        width, height: Top face dimensions
        depth: Height of front face
        color_top: Color for top face
        color_front: Color for front face
        color_outline: Optional outline color
        shrink: Pixels to shrink from edges (for smaller items)
    """
    x += shrink
    y += shrink
    width -= shrink * 2
    height -= shrink * 2
    
    if width <= 0 or height <= 0:
        return
    
    # Draw front face first (below top)
    pygame.draw.rect(surface, color_front, (x, y + height, width, depth))
    
    # Draw top face
    pygame.draw.rect(surface, color_top, (x, y, width, height))
    
    # Outline
    if color_outline:
        # Top face outline
        pygame.draw.rect(surface, color_outline, (x, y, width, height), 1)
        # Front face outline
        pygame.draw.rect(surface, color_outline, (x, y + height, width, depth), 1)


# ============== Floor/Ground Drawing ==============

def draw_floor(surface, grid_width, grid_height, cell_size, depth_height,
               origin_x, origin_y):
    """
    Draw the grass floor with checkerboard pattern.
    
    Args:
        surface: Pygame surface
        grid_width, grid_height: Grid dimensions
        cell_size: Size of each cell
        depth_height: Height of depth effect (for bottom row)
        origin_x, origin_y: Screen origin
    """
    for y in range(grid_height):
        for x in range(grid_width):
            screen_x, screen_y = grid_to_screen(x, y, cell_size, origin_x, origin_y)
            
            # Checkerboard pattern
            if (x + y) % 2 == 0:
                color_top = FLOOR_TOP
                color_front = FLOOR_FRONT
            else:
                color_top = FLOOR_TOP_ALT
                color_front = FLOOR_FRONT_ALT
            
            # Draw top tile
            pygame.draw.rect(surface, color_top, (screen_x, screen_y, cell_size, cell_size))
            
            # Draw subtle grid lines
            pygame.draw.rect(surface, FLOOR_OUTLINE, (screen_x, screen_y, cell_size, cell_size), 1)
            
            # Add grass texture (subtle dots)
            if (x + y * 3) % 7 == 0:
                dot_x = screen_x + cell_size // 3
                dot_y = screen_y + cell_size // 2
                pygame.draw.circle(surface, FLOOR_OUTLINE, (dot_x, dot_y), 1)
            if (x * 2 + y) % 5 == 0:
                dot_x = screen_x + cell_size * 2 // 3
                dot_y = screen_y + cell_size // 3
                pygame.draw.circle(surface, FLOOR_OUTLINE, (dot_x, dot_y), 1)
    
    # Draw front edge of bottom row (shows depth)
    for x in range(grid_width):
        screen_x, screen_y = grid_to_screen(x, grid_height - 1, cell_size, origin_x, origin_y)
        color_front = FLOOR_FRONT if (x + grid_height - 1) % 2 == 0 else FLOOR_FRONT_ALT
        pygame.draw.rect(surface, color_front, 
                        (screen_x, screen_y + cell_size, cell_size, depth_height))


# ============== Wall Drawing ==============

def draw_wall(surface, grid_x, grid_y, cell_size, depth_height, origin_x, origin_y):
    """
    Draw a wall block at grid position.
    """
    screen_x, screen_y = grid_to_screen(grid_x, grid_y, cell_size, origin_x, origin_y)
    
    # Walls are taller cubes
    wall_depth = depth_height * 2
    
    draw_cube(surface, screen_x, screen_y - wall_depth + depth_height, 
              cell_size, cell_size, wall_depth,
              WALL_TOP, WALL_FRONT, WALL_OUTLINE)
    
    # Add wood grain pattern
    grain_y = screen_y - wall_depth + depth_height + cell_size // 3
    pygame.draw.line(surface, WALL_HIGHLIGHT, 
                    (screen_x + 3, grain_y), 
                    (screen_x + cell_size - 3, grain_y), 1)
    pygame.draw.line(surface, WALL_HIGHLIGHT, 
                    (screen_x + 5, grain_y + cell_size // 3), 
                    (screen_x + cell_size - 5, grain_y + cell_size // 3), 1)


def draw_walls(surface, walls, cell_size, depth_height, origin_x, origin_y):
    """
    Draw all walls sorted by depth (Y position).
    """
    sorted_walls = sorted(walls, key=lambda w: w[1])
    for wall_x, wall_y in sorted_walls:
        draw_wall(surface, wall_x, wall_y, cell_size, depth_height, origin_x, origin_y)


# ============== Snake Drawing ==============

def draw_snake_head(surface, grid_x, grid_y, cell_size, depth_height, 
                    origin_x, origin_y, direction):
    """
    Draw the snake head with cute pixel-art eyes.
    """
    screen_x, screen_y = grid_to_screen(grid_x, grid_y, cell_size, origin_x, origin_y)
    
    # Main head cube
    draw_cube(surface, screen_x, screen_y, cell_size, cell_size, depth_height,
              SNAKE_HEAD_TOP, SNAKE_HEAD_FRONT, None, shrink=1)
    
    # Calculate center of head
    cx = screen_x + cell_size // 2
    cy = screen_y + cell_size // 2
    
    # Eye positions based on direction
    eye_spacing = cell_size // 4
    eye_size = max(2, cell_size // 8)
    pupil_size = max(1, eye_size - 1)
    
    if direction == RIGHT:
        eye1_pos = (cx + eye_spacing // 2, cy - eye_spacing // 2)
        eye2_pos = (cx + eye_spacing // 2, cy + eye_spacing // 2)
    elif direction == LEFT:
        eye1_pos = (cx - eye_spacing // 2, cy - eye_spacing // 2)
        eye2_pos = (cx - eye_spacing // 2, cy + eye_spacing // 2)
    elif direction == UP:
        eye1_pos = (cx - eye_spacing // 2, cy - eye_spacing // 2)
        eye2_pos = (cx + eye_spacing // 2, cy - eye_spacing // 2)
    else:  # DOWN
        eye1_pos = (cx - eye_spacing // 2, cy + eye_spacing // 2)
        eye2_pos = (cx + eye_spacing // 2, cy + eye_spacing // 2)
    
    # Draw eyes with white and pupils
    pygame.draw.circle(surface, SNAKE_EYE_WHITE, eye1_pos, eye_size)
    pygame.draw.circle(surface, SNAKE_EYE_WHITE, eye2_pos, eye_size)
    pygame.draw.circle(surface, SNAKE_EYE_PUPIL, eye1_pos, pupil_size)
    pygame.draw.circle(surface, SNAKE_EYE_PUPIL, eye2_pos, pupil_size)
    
    # Small highlight on head
    highlight_pos = (screen_x + cell_size // 4, screen_y + cell_size // 4)
    pygame.draw.circle(surface, SNAKE_HEAD_HIGHLIGHT, highlight_pos, 2)


def draw_snake_body(surface, grid_x, grid_y, cell_size, depth_height,
                    origin_x, origin_y, segment_index):
    """
    Draw a snake body segment with alternating colors.
    """
    screen_x, screen_y = grid_to_screen(grid_x, grid_y, cell_size, origin_x, origin_y)
    
    # Alternate colors for scale pattern
    if segment_index % 2 == 0:
        color_top = SNAKE_BODY_TOP
        color_front = SNAKE_BODY_FRONT
    else:
        color_top = SNAKE_BODY_TOP_ALT
        color_front = SNAKE_BODY_FRONT_ALT
    
    draw_cube(surface, screen_x, screen_y, cell_size, cell_size, depth_height,
              color_top, color_front, None, shrink=2)
    
    # Scale pattern dot
    cx = screen_x + cell_size // 2
    cy = screen_y + cell_size // 2
    pygame.draw.circle(surface, SNAKE_BODY_PATTERN, (cx, cy), 2)


def draw_snake_tail(surface, grid_x, grid_y, cell_size, depth_height,
                    origin_x, origin_y):
    """
    Draw the snake tail (smaller/tapered).
    """
    screen_x, screen_y = grid_to_screen(grid_x, grid_y, cell_size, origin_x, origin_y)
    
    # Tail is smaller
    shrink = cell_size // 6
    tail_depth = max(2, depth_height - 2)
    
    draw_cube(surface, screen_x, screen_y, cell_size, cell_size, tail_depth,
              SNAKE_TAIL_TOP, SNAKE_TAIL_FRONT, None, shrink=shrink)


def draw_snake(surface, snake, cell_size, depth_height, origin_x, origin_y, direction):
    """
    Draw the entire snake, sorted by Y for proper overlap.
    
    Args:
        surface: Pygame surface
        snake: List of (x, y) grid positions (head first)
        cell_size: Size of each cell
        depth_height: Height of depth face
        origin_x, origin_y: Screen origin
        direction: Current head direction
    """
    # Sort by Y (draw back to front) with index preservation
    indexed = [(i, pos) for i, pos in enumerate(snake)]
    sorted_snake = sorted(indexed, key=lambda item: item[1][1])
    
    for idx, (grid_x, grid_y) in sorted_snake:
        if idx == 0:
            draw_snake_head(surface, grid_x, grid_y, cell_size, depth_height,
                           origin_x, origin_y, direction)
        elif idx == len(snake) - 1:
            draw_snake_tail(surface, grid_x, grid_y, cell_size, depth_height,
                           origin_x, origin_y)
        else:
            draw_snake_body(surface, grid_x, grid_y, cell_size, depth_height,
                           origin_x, origin_y, idx)


# ============== Animal/Food Drawing ==============

def draw_food_shadow(surface, screen_x, screen_y, cell_size):
    """Draw a cute shadow beneath food."""
    shadow_surface = pygame.Surface((cell_size - 4, 4), pygame.SRCALPHA)
    shadow_surface.fill((0, 0, 0, 50))
    surface.blit(shadow_surface, (screen_x + 2, screen_y + cell_size - 2))


def draw_small_animal(surface, grid_x, grid_y, cell_size, depth_height,
                      origin_x, origin_y, animal_type):
    """
    Draw a small single-cell animal with cute pixel art style.
    """
    screen_x, screen_y = grid_to_screen(grid_x, grid_y, cell_size, origin_x, origin_y)
    
    # Shadow
    draw_food_shadow(surface, screen_x, screen_y, cell_size)
    
    # Get animal colors
    animal_colors = {
        'mouse': (MOUSE_BODY, (140, 135, 130)),
        'frog': (FROG_BODY, (55, 140, 55)),
        'bug': (BUG_SHELL, (120, 70, 40)),
        'cricket': (CRICKET_BODY, (70, 50, 35)),
        'worm': (WORM_BODY, (230, 130, 130)),
        'butterfly': (BUTTERFLY_WING1, (230, 110, 180)),
        'spider': (SPIDER_BODY, (40, 40, 40)),
        'snail': (SNAIL_SHELL, (170, 150, 120)),
        'ant': (ANT_BODY, (35, 28, 18)),
        'bee': (BEE_BODY, (230, 185, 55)),
        'ladybug': (LADYBUG_SHELL, (200, 50, 50)),
        'firefly': (FIREFLY_BODY, (55, 48, 40)),
    }
    
    colors = animal_colors.get(animal_type, (GRAY, DARK_GRAY))
    color_top, color_front = colors
    
    # Draw animal cube (smaller than cell)
    shrink = cell_size // 5
    small_depth = max(3, depth_height - 3)
    
    draw_cube(surface, screen_x, screen_y, cell_size, cell_size, small_depth,
              color_top, color_front, None, shrink=shrink)
    
    # Add animal-specific details
    cx = screen_x + cell_size // 2
    cy = screen_y + cell_size // 2
    
    if animal_type == 'mouse':
        # Ears
        pygame.draw.circle(surface, MOUSE_EAR, (cx - 4, cy - 4), 3)
        pygame.draw.circle(surface, MOUSE_EAR, (cx + 4, cy - 4), 3)
        # Eyes
        pygame.draw.circle(surface, BLACK, (cx - 2, cy), 1)
        pygame.draw.circle(surface, BLACK, (cx + 2, cy), 1)
        
    elif animal_type == 'frog':
        # Big eyes
        pygame.draw.circle(surface, FROG_EYE, (cx - 4, cy - 3), 3)
        pygame.draw.circle(surface, FROG_EYE, (cx + 4, cy - 3), 3)
        pygame.draw.circle(surface, BLACK, (cx - 4, cy - 3), 1)
        pygame.draw.circle(surface, BLACK, (cx + 4, cy - 3), 1)
        
    elif animal_type == 'butterfly':
        # Wings
        pygame.draw.ellipse(surface, BUTTERFLY_WING2, (cx - 8, cy - 3, 6, 10))
        pygame.draw.ellipse(surface, BUTTERFLY_WING2, (cx + 2, cy - 3, 6, 10))
        
    elif animal_type == 'bee':
        # Stripes
        pygame.draw.line(surface, BEE_STRIPES, (cx - 3, cy - 2), (cx + 3, cy - 2), 1)
        pygame.draw.line(surface, BEE_STRIPES, (cx - 3, cy + 1), (cx + 3, cy + 1), 1)
        
    elif animal_type == 'ladybug':
        # Spots
        pygame.draw.circle(surface, LADYBUG_SPOTS, (cx - 2, cy - 2), 2)
        pygame.draw.circle(surface, LADYBUG_SPOTS, (cx + 2, cy + 1), 2)
        
    elif animal_type == 'snail':
        # Shell spiral (simple line)
        pygame.draw.arc(surface, (160, 130, 100), (cx - 3, cy - 3, 6, 6), 0, 4.7, 1)
        
    elif animal_type == 'firefly':
        # Glow
        pygame.draw.circle(surface, FIREFLY_GLOW, (cx, cy + 2), 3)


def draw_medium_animal(surface, grid_x, grid_y, cell_size, depth_height,
                       origin_x, origin_y, animal_type):
    """
    Draw a medium multi-cell animal.
    """
    screen_x, screen_y = grid_to_screen(grid_x, grid_y, cell_size, origin_x, origin_y)
    
    animal_colors = {
        'rabbit': (RABBIT_BODY, (200, 180, 165)),
        'lizard': (LIZARD_BODY, (55, 100, 55)),
        'fish': (FISH_BODY, (90, 165, 200)),
        'snake_prey': (SNAKE_PREY_BODY, (100, 85, 70)),
        'turtle': (TURTLE_SHELL, (70, 105, 55)),
        'duck': (DUCK_BODY, (170, 135, 80)),
    }
    
    colors = animal_colors.get(animal_type, (GRAY, DARK_GRAY))
    color_top, color_front = colors
    
    shrink = cell_size // 6
    
    draw_cube(surface, screen_x, screen_y, cell_size, cell_size, depth_height - 2,
              color_top, color_front, None, shrink=shrink)
    
    cx = screen_x + cell_size // 2
    cy = screen_y + cell_size // 2
    
    # Animal-specific details
    if animal_type == 'rabbit':
        # Ears
        pygame.draw.ellipse(surface, RABBIT_EAR_INNER, (cx - 6, cy - 8, 4, 8))
        pygame.draw.ellipse(surface, RABBIT_EAR_INNER, (cx + 2, cy - 8, 4, 8))
        # Eyes
        pygame.draw.circle(surface, BLACK, (cx - 2, cy - 1), 2)
        pygame.draw.circle(surface, BLACK, (cx + 2, cy - 1), 2)
        
    elif animal_type == 'fish':
        # Eye and fin
        pygame.draw.circle(surface, FISH_EYE, (cx + 2, cy - 2), 2)
        pygame.draw.polygon(surface, FISH_FIN, [(cx - 6, cy), (cx - 10, cy - 4), (cx - 10, cy + 4)])
        
    elif animal_type == 'duck':
        # Head (green)
        pygame.draw.circle(surface, DUCK_HEAD, (cx + 3, cy - 2), 4)
        # Beak
        pygame.draw.polygon(surface, DUCK_BEAK, [(cx + 7, cy - 2), (cx + 10, cy - 1), (cx + 7, cy)])


def draw_large_animal(surface, grid_x, grid_y, cell_size, depth_height,
                      origin_x, origin_y, animal_type):
    """
    Draw a large multi-cell animal.
    """
    screen_x, screen_y = grid_to_screen(grid_x, grid_y, cell_size, origin_x, origin_y)
    
    animal_colors = {
        'bird': (BIRD_BODY, (75, 135, 215)),
        'fox': (FOX_BODY, (195, 105, 40)),
        'wolf': (WOLF_BODY, (115, 115, 125)),
        'deer': (DEER_BODY, (170, 135, 100)),
        'pig': (PIG_BODY, (230, 170, 170)),
        'tiger': (TIGER_BODY, (230, 160, 55)),
        'lion': (LION_BODY, (210, 175, 100)),
        'bear': (BEAR_BODY, (100, 75, 55)),
        'crocodile': (CROCODILE_BODY, (70, 100, 60)),
        'hippo': (HIPPO_BODY, (130, 110, 120)),
        'elephant': (ELEPHANT_BODY, (140, 140, 150)),
    }
    
    colors = animal_colors.get(animal_type, (GRAY, DARK_GRAY))
    color_top, color_front = colors
    
    shrink = cell_size // 8
    
    draw_cube(surface, screen_x, screen_y, cell_size, cell_size, depth_height - 1,
              color_top, color_front, None, shrink=shrink)
    
    cx = screen_x + cell_size // 2
    cy = screen_y + cell_size // 2
    
    # Animal-specific details
    if animal_type == 'tiger':
        # Stripes
        pygame.draw.line(surface, TIGER_STRIPES, (cx - 4, cy - 3), (cx - 2, cy + 3), 2)
        pygame.draw.line(surface, TIGER_STRIPES, (cx + 2, cy - 3), (cx + 4, cy + 3), 2)
        
    elif animal_type == 'lion':
        # Mane
        pygame.draw.circle(surface, LION_MANE, (cx, cy), cell_size // 3)
        pygame.draw.circle(surface, LION_BODY, (cx, cy), cell_size // 4)
        
    elif animal_type == 'elephant':
        # Trunk hint
        pygame.draw.line(surface, (130, 130, 140), (cx, cy + 2), (cx, cy + 6), 2)


def draw_food(surface, grid_x, grid_y, cell_size, depth_height,
              origin_x, origin_y, animal_type):
    """
    Draw food item (animal) at grid position.
    """
    if animal_type in SMALL_ANIMAL_TYPES:
        draw_small_animal(surface, grid_x, grid_y, cell_size, depth_height,
                         origin_x, origin_y, animal_type)
    elif animal_type in MEDIUM_ANIMAL_TYPES:
        draw_medium_animal(surface, grid_x, grid_y, cell_size, depth_height,
                          origin_x, origin_y, animal_type)
    else:
        draw_large_animal(surface, grid_x, grid_y, cell_size, depth_height,
                         origin_x, origin_y, animal_type)


def draw_multi_cell_food(surface, grid_x, grid_y, cell_size, depth_height,
                         origin_x, origin_y, animal_type, current_health, max_health):
    """
    Draw a multi-cell animal with health bar.
    """
    cells = ANIMAL_SIZES.get(animal_type, [(0, 0)])
    
    # Sort cells by Y for proper overlap
    sorted_cells = sorted(cells, key=lambda c: c[1])
    
    # Draw each cell
    for dx, dy in sorted_cells:
        draw_food(surface, grid_x + dx, grid_y + dy, cell_size, depth_height,
                 origin_x, origin_y, animal_type)
    
    # Draw health bar if multi-health
    if max_health > 1:
        screen_x, screen_y = grid_to_screen(grid_x, grid_y, cell_size, origin_x, origin_y)
        
        # Center health bar above the animal
        max_dx = max(c[0] for c in cells)
        bar_width = (max_dx + 1) * cell_size - 4
        bar_x = screen_x + 2
        bar_y = screen_y - 10
        
        draw_health_bar(surface, bar_x, bar_y, bar_width, 6, current_health, max_health)


# ============== Health Bar ==============

def draw_health_bar(surface, x, y, width, height, current_health, max_health):
    """Draw a health bar."""
    # Background
    pygame.draw.rect(surface, (30, 25, 25), (x, y, width, height))
    
    # Health fill
    if max_health > 0:
        fill_width = int((current_health / max_health) * (width - 2))
        if fill_width > 0:
            health_color = get_health_color(current_health, max_health)
            pygame.draw.rect(surface, health_color, (x + 1, y + 1, fill_width, height - 2))
    
    # Border
    pygame.draw.rect(surface, (80, 75, 70), (x, y, width, height), 1)


# ============== HUD Drawing ==============

def draw_hud_top(surface, fonts, player_name, score, difficulty, sound_enabled,
                 play_area_width, hud_height):
    """Draw the top HUD bar."""
    # Background
    pygame.draw.rect(surface, HUD_BG, (0, 0, surface.get_width(), hud_height))
    pygame.draw.line(surface, HUD_BORDER, (0, hud_height - 1),
                     (surface.get_width(), hud_height - 1), 2)
    
    padding = 10
    
    # Player name
    name_label = fonts['tiny'].render("Player:", True, HUD_LABEL)
    surface.blit(name_label, (padding, 6))
    display_name = player_name[:12] + ".." if len(player_name) > 14 else player_name
    name_text = fonts['small'].render(display_name, True, HUD_VALUE)
    surface.blit(name_text, (padding, 22))
    
    # Score
    score_x = play_area_width // 3
    score_label = fonts['tiny'].render("Score:", True, HUD_LABEL)
    surface.blit(score_label, (score_x, 6))
    score_text = fonts['small'].render(str(score), True, HUD_VALUE)
    surface.blit(score_text, (score_x, 22))
    
    # Difficulty
    diff_x = play_area_width * 2 // 3
    diff_label = fonts['tiny'].render("Mode:", True, HUD_LABEL)
    surface.blit(diff_label, (diff_x, 6))
    diff_text = fonts['tiny'].render(difficulty[:12], True, HUD_TEXT)
    surface.blit(diff_text, (diff_x, 24))
    
    # Sound
    sound_status = "ON" if sound_enabled else "OFF"
    sound_text = fonts['tiny'].render(f"[{sound_status}] M", True, HUD_LABEL)
    sound_x = play_area_width - sound_text.get_width() - padding
    surface.blit(sound_text, (sound_x, 18))


def draw_hud_right(surface, fonts, animal_type, animal_score, snake_length,
                   play_area_width, play_area_height, hud_width, hud_top_height,
                   extra_info=None, food_health=None, food_max_health=None):
    """Draw the right HUD panel."""
    hud_x = play_area_width
    hud_y = hud_top_height
    panel_height = surface.get_height() - hud_top_height
    
    # Background
    pygame.draw.rect(surface, HUD_BG, (hud_x, hud_y, hud_width, panel_height))
    pygame.draw.line(surface, HUD_BORDER, (hud_x, hud_y), (hud_x, hud_y + panel_height), 2)
    
    padding = 6
    y = hud_y + padding
    
    # Prey section
    prey_label = fonts['tiny'].render("PREY", True, HUD_LABEL)
    surface.blit(prey_label, (hud_x + padding, y))
    y += 16
    
    animal_names = {
        'mouse': 'Mouse', 'frog': 'Frog', 'bug': 'Bug', 'cricket': 'Cricket',
        'worm': 'Worm', 'butterfly': 'Butterfly', 'spider': 'Spider', 'snail': 'Snail',
        'ant': 'Ant', 'bee': 'Bee', 'ladybug': 'Ladybug', 'firefly': 'Firefly',
        'rabbit': 'Rabbit', 'lizard': 'Lizard', 'fish': 'Fish', 'snake_prey': 'Snake',
        'turtle': 'Turtle', 'duck': 'Duck',
        'bird': 'Bird', 'fox': 'Fox', 'wolf': 'Wolf', 'deer': 'Deer', 'pig': 'Pig',
        'tiger': 'Tiger', 'lion': 'Lion', 'bear': 'Bear', 'crocodile': 'Croc',
        'hippo': 'Hippo', 'elephant': 'Elephant'
    }
    name = animal_names.get(animal_type, animal_type.title())
    
    prey_text = fonts['small'].render(name, True, HUD_VALUE)
    surface.blit(prey_text, (hud_x + padding, y))
    y += 20
    
    score_text = fonts['tiny'].render(f"+{animal_score} pts", True, HUD_TEXT)
    surface.blit(score_text, (hud_x + padding, y))
    y += 18
    
    # Health bar for multi-hit animals
    if food_max_health is not None and food_max_health > 1:
        health_label = fonts['tiny'].render(f"HP: {food_health}/{food_max_health}", True, HUD_LABEL)
        surface.blit(health_label, (hud_x + padding, y))
        y += 14
        
        bar_width = hud_width - padding * 2
        draw_health_bar(surface, hud_x + padding, y, bar_width, 6, food_health, food_max_health)
        y += 12
    else:
        y += 6
    
    # Divider
    pygame.draw.line(surface, HUD_BORDER, (hud_x + padding, y),
                     (hud_x + hud_width - padding, y))
    y += 10
    
    # Snake length
    len_label = fonts['tiny'].render("LENGTH", True, HUD_LABEL)
    surface.blit(len_label, (hud_x + padding, y))
    y += 16
    len_text = fonts['small'].render(str(snake_length), True, HUD_VALUE)
    surface.blit(len_text, (hud_x + padding, y))
    y += 26
    
    # Extra info (story mode)
    if extra_info:
        pygame.draw.line(surface, HUD_BORDER, (hud_x + padding, y),
                         (hud_x + hud_width - padding, y))
        y += 8
        
        if 'level' in extra_info:
            level_label = fonts['tiny'].render("LEVEL", True, HUD_LABEL)
            surface.blit(level_label, (hud_x + padding, y))
            y += 14
            level_text = fonts['small'].render(str(extra_info['level']), True, HUD_VALUE)
            surface.blit(level_text, (hud_x + padding, y))
            y += 22
        
        if 'food_progress' in extra_info:
            food_eaten, food_required = extra_info['food_progress']
            prog_label = fonts['tiny'].render("GOAL", True, HUD_LABEL)
            surface.blit(prog_label, (hud_x + padding, y))
            y += 14
            prog_text = fonts['small'].render(f"{food_eaten}/{food_required}", True, HUD_VALUE)
            surface.blit(prog_text, (hud_x + padding, y))
            y += 20
    
    # Controls hint at bottom
    hint_y = hud_y + panel_height - 50
    pygame.draw.line(surface, HUD_BORDER, (hud_x + padding, hint_y),
                     (hud_x + hud_width - padding, hint_y))
    hint_y += 6
    
    controls = ["Arrows: Move", "P: Pause", "M: Sound"]
    for control in controls:
        text = fonts['tiny'].render(control, True, GRAY)
        surface.blit(text, (hud_x + padding, hint_y))
        hint_y += 13


# ============== Overlay Drawing ==============

def draw_game_over(surface, score, font_large, font_small, window_size, play_area_rect=None):
    """Draw game over overlay."""
    width, height = window_size
    
    if play_area_rect:
        center_x = play_area_rect[0] + play_area_rect[2] // 2
        center_y = play_area_rect[1] + play_area_rect[3] // 2
    else:
        center_x = width // 2
        center_y = height // 2
    
    # Overlay
    overlay = pygame.Surface((width, height))
    overlay.set_alpha(200)
    overlay.fill(OVERLAY_COLOR)
    surface.blit(overlay, (0, 0))
    
    # Game over text
    game_over_text = font_large.render("GAME OVER", True, GAME_OVER_COLOR)
    text_rect = game_over_text.get_rect(center=(center_x, center_y - 35))
    surface.blit(game_over_text, text_rect)
    
    # Score
    final_text = font_small.render(f"Final Score: {score}", True, WHITE)
    score_rect = final_text.get_rect(center=(center_x, center_y + 10))
    surface.blit(final_text, score_rect)
    
    # Instructions
    inst_text = font_small.render("SPACE: Retry | ESC: Menu", True, WHITE)
    inst_rect = inst_text.get_rect(center=(center_x, center_y + 45))
    surface.blit(inst_text, inst_rect)


def draw_level_complete(surface, fonts, level, score, bonus, total, play_area_rect):
    """Draw level complete overlay."""
    x, y, width, height = play_area_rect
    center_x = x + width // 2
    center_y = y + height // 2
    
    # Overlay
    overlay = pygame.Surface((surface.get_width(), surface.get_height()))
    overlay.set_alpha(200)
    overlay.fill(OVERLAY_COLOR)
    surface.blit(overlay, (0, 0))
    
    # Level complete text
    complete_text = fonts['large'].render("LEVEL COMPLETE!", True, HUD_VALUE)
    text_rect = complete_text.get_rect(center=(center_x, center_y - 55))
    surface.blit(complete_text, text_rect)
    
    # Stats
    level_text = fonts['medium'].render(f"Level {level}", True, WHITE)
    level_rect = level_text.get_rect(center=(center_x, center_y - 10))
    surface.blit(level_text, level_rect)
    
    score_text = fonts['small'].render(f"Score: {score}", True, WHITE)
    score_rect = score_text.get_rect(center=(center_x, center_y + 20))
    surface.blit(score_text, score_rect)
    
    bonus_text = fonts['small'].render(f"Bonus: +{bonus}", True, WHITE)
    bonus_rect = bonus_text.get_rect(center=(center_x, center_y + 45))
    surface.blit(bonus_text, bonus_rect)
    
    total_text = fonts['medium'].render(f"Total: {total}", True, HUD_VALUE)
    total_rect = total_text.get_rect(center=(center_x, center_y + 80))
    surface.blit(total_text, total_rect)
    
    # Instructions
    hint_text = fonts['small'].render("SPACE: Next | ESC: Menu", True, WHITE)
    hint_rect = hint_text.get_rect(center=(center_x, center_y + 120))
    surface.blit(hint_text, hint_rect)


# ============== Legacy Compatibility (for existing code) ==============

def draw_iso_tile(*args, **kwargs):
    """Legacy wrapper - redirects to new tile drawing."""
    pass  # Floor tiles are drawn differently now


def draw_iso_cube(*args, **kwargs):
    """Legacy wrapper - redirects to new cube drawing."""
    pass  # Cubes are drawn differently now


def draw_iso_wall(surface, grid_x, grid_y, tile_width, tile_height, tile_depth,
                  origin_x, origin_y):
    """Legacy wrapper for wall drawing."""
    draw_wall(surface, grid_x, grid_y, CELL_SIZE, DEPTH_HEIGHT, origin_x, origin_y)


def draw_iso_walls(surface, walls, tile_width, tile_height, tile_depth,
                   origin_x, origin_y):
    """Legacy wrapper for walls drawing."""
    draw_walls(surface, walls, CELL_SIZE, DEPTH_HEIGHT, origin_x, origin_y)


def draw_iso_snake_segment(surface, grid_x, grid_y, tile_width, tile_height, tile_depth,
                           origin_x, origin_y, is_head=False, is_tail=False,
                           direction=None, prev_dir=None):
    """Legacy wrapper for snake segment drawing."""
    if is_head:
        draw_snake_head(surface, grid_x, grid_y, CELL_SIZE, DEPTH_HEIGHT,
                       origin_x, origin_y, direction or RIGHT)
    elif is_tail:
        draw_snake_tail(surface, grid_x, grid_y, CELL_SIZE, DEPTH_HEIGHT,
                       origin_x, origin_y)
    else:
        draw_snake_body(surface, grid_x, grid_y, CELL_SIZE, DEPTH_HEIGHT,
                       origin_x, origin_y, 1)


def draw_iso_snake(surface, snake, tile_width, tile_height, tile_depth,
                   origin_x, origin_y, direction):
    """Legacy wrapper for snake drawing."""
    draw_snake(surface, snake, CELL_SIZE, DEPTH_HEIGHT, origin_x, origin_y, direction)


def draw_iso_food(surface, grid_x, grid_y, tile_width, tile_height, tile_depth,
                  origin_x, origin_y, animal_type):
    """Legacy wrapper for food drawing."""
    draw_food(surface, grid_x, grid_y, CELL_SIZE, DEPTH_HEIGHT, origin_x, origin_y, animal_type)


def draw_iso_large_food(surface, grid_x, grid_y, tile_width, tile_height, tile_depth,
                        origin_x, origin_y, animal_type, current_health, max_health):
    """Legacy wrapper for large food drawing."""
    draw_multi_cell_food(surface, grid_x, grid_y, CELL_SIZE, DEPTH_HEIGHT,
                        origin_x, origin_y, animal_type, current_health, max_health)
