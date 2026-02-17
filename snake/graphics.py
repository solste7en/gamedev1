"""
Graphics module for the Snake Game.
Contains all drawing functions for snake, animals, and UI elements.
"""

import pygame
import math
from .assets import *


def draw_snake_head(surface, x, y, direction, cell_size):
    """
    Draw a realistic snake head with eyes and tongue.
    
    Args:
        surface: Pygame surface to draw on
        x: X pixel position (top-left)
        y: Y pixel position (top-left)
        direction: Tuple indicating direction (e.g., RIGHT, LEFT, UP, DOWN)
        cell_size: Size of each cell in pixels
    """
    # Calculate center and dimensions
    center_x = x + cell_size // 2
    center_y = y + cell_size // 2
    head_width = cell_size - 2
    head_height = cell_size - 2
    
    # Determine rotation based on direction
    if direction == RIGHT:
        angle = 0
    elif direction == LEFT:
        angle = 180
    elif direction == UP:
        angle = 90
    elif direction == DOWN:
        angle = 270
    else:
        angle = 0
    
    # Create a surface for the head that we can rotate
    head_surface = pygame.Surface((cell_size * 2, cell_size * 2), pygame.SRCALPHA)
    head_center = cell_size
    
    # Draw head base (elongated oval shape pointing right)
    head_rect = pygame.Rect(
        head_center - head_width // 2,
        head_center - head_height // 2,
        head_width + 4,
        head_height
    )
    
    # Main head shape - slightly pointed
    points = [
        (head_center - head_width // 2, head_center - head_height // 3),
        (head_center - head_width // 2, head_center + head_height // 3),
        (head_center + head_width // 2 + 2, head_center + head_height // 4),
        (head_center + head_width // 2 + 4, head_center),
        (head_center + head_width // 2 + 2, head_center - head_height // 4),
    ]
    pygame.draw.polygon(head_surface, SNAKE_HEAD_PRIMARY, points)
    
    # Head highlight (top gradient effect)
    highlight_points = [
        (head_center - head_width // 2 + 2, head_center - head_height // 3 + 2),
        (head_center + head_width // 4, head_center - head_height // 4),
        (head_center + head_width // 4, head_center - head_height // 6),
        (head_center - head_width // 2 + 2, head_center - head_height // 6),
    ]
    pygame.draw.polygon(head_surface, SNAKE_HEAD_ACCENT, highlight_points)
    
    # Draw scales pattern on head
    for i in range(2):
        scale_x = head_center - head_width // 4 + i * 6
        scale_y = head_center - 2
        pygame.draw.ellipse(
            head_surface, 
            SNAKE_HEAD_SECONDARY,
            (scale_x, scale_y, 5, 4)
        )
    
    # Draw eyes
    eye_offset_x = head_width // 4
    eye_offset_y = head_height // 4
    eye_radius = 4
    pupil_radius = 2
    
    # Right eye (top when facing right)
    eye_x = head_center + eye_offset_x - 2
    eye_y_top = head_center - eye_offset_y
    
    # Eye white
    pygame.draw.circle(head_surface, SNAKE_EYE_WHITE, (eye_x, eye_y_top), eye_radius)
    # Pupil (slightly forward-looking)
    pygame.draw.circle(head_surface, SNAKE_EYE_PUPIL, (eye_x + 1, eye_y_top), pupil_radius)
    # Eye shine
    pygame.draw.circle(head_surface, WHITE, (eye_x + 2, eye_y_top - 1), 1)
    
    # Left eye (bottom when facing right)
    eye_y_bottom = head_center + eye_offset_y
    pygame.draw.circle(head_surface, SNAKE_EYE_WHITE, (eye_x, eye_y_bottom), eye_radius)
    pygame.draw.circle(head_surface, SNAKE_EYE_PUPIL, (eye_x + 1, eye_y_bottom), pupil_radius)
    pygame.draw.circle(head_surface, WHITE, (eye_x + 2, eye_y_bottom - 1), 1)
    
    # Draw forked tongue
    tongue_start_x = head_center + head_width // 2 + 4
    tongue_start_y = head_center
    tongue_length = 6
    fork_length = 3
    
    # Main tongue
    pygame.draw.line(
        head_surface, 
        SNAKE_TONGUE,
        (tongue_start_x, tongue_start_y),
        (tongue_start_x + tongue_length, tongue_start_y),
        2
    )
    # Fork top
    pygame.draw.line(
        head_surface,
        SNAKE_TONGUE,
        (tongue_start_x + tongue_length, tongue_start_y),
        (tongue_start_x + tongue_length + fork_length, tongue_start_y - 3),
        1
    )
    # Fork bottom
    pygame.draw.line(
        head_surface,
        SNAKE_TONGUE,
        (tongue_start_x + tongue_length, tongue_start_y),
        (tongue_start_x + tongue_length + fork_length, tongue_start_y + 3),
        1
    )
    
    # Nostril
    nostril_x = head_center + head_width // 3
    pygame.draw.circle(head_surface, SNAKE_HEAD_SECONDARY, (nostril_x, head_center - 2), 1)
    pygame.draw.circle(head_surface, SNAKE_HEAD_SECONDARY, (nostril_x, head_center + 2), 1)
    
    # Rotate the head surface
    rotated_head = pygame.transform.rotate(head_surface, angle)
    
    # Get the rect and center it on the original position
    rotated_rect = rotated_head.get_rect(center=(center_x, center_y))
    
    # Blit to main surface
    surface.blit(rotated_head, rotated_rect.topleft)


def draw_snake_body_segment(surface, x, y, cell_size, segment_index, total_segments):
    """
    Draw a snake body segment with realistic scale pattern.
    
    Args:
        surface: Pygame surface to draw on
        x: X pixel position
        y: Y pixel position
        cell_size: Size of each cell
        segment_index: Index of this segment (0 = closest to head)
        total_segments: Total number of body segments
    """
    # Calculate color gradient (darker towards tail)
    fade_factor = 1 - (segment_index / (total_segments + 5)) * 0.3
    
    base_r = int(SNAKE_BODY_PRIMARY[0] * fade_factor)
    base_g = int(SNAKE_BODY_PRIMARY[1] * fade_factor)
    base_b = int(SNAKE_BODY_PRIMARY[2] * fade_factor)
    base_color = (base_r, base_g, base_b)
    
    # Draw base segment
    segment_rect = pygame.Rect(x + 1, y + 1, cell_size - 2, cell_size - 2)
    pygame.draw.rect(surface, base_color, segment_rect, border_radius=3)
    
    # Draw scale pattern
    draw_scales(surface, x, y, cell_size, segment_index, fade_factor)
    
    # Add highlight on top edge
    highlight_rect = pygame.Rect(x + 2, y + 2, cell_size - 4, 3)
    highlight_color = (
        min(255, int(SNAKE_BODY_HIGHLIGHT[0] * fade_factor)),
        min(255, int(SNAKE_BODY_HIGHLIGHT[1] * fade_factor)),
        min(255, int(SNAKE_BODY_HIGHLIGHT[2] * fade_factor))
    )
    pygame.draw.rect(surface, highlight_color, highlight_rect, border_radius=2)


def draw_scales(surface, x, y, cell_size, segment_index, fade_factor):
    """
    Draw diamond/hexagonal scale pattern on a snake segment.
    """
    scale_size = 4
    offset = (segment_index % 2) * (scale_size // 2)
    
    pattern_color = (
        int(SNAKE_BODY_PATTERN[0] * fade_factor),
        int(SNAKE_BODY_PATTERN[1] * fade_factor),
        int(SNAKE_BODY_PATTERN[2] * fade_factor)
    )
    
    shadow_color = (
        int(SNAKE_BODY_SHADOW[0] * fade_factor),
        int(SNAKE_BODY_SHADOW[1] * fade_factor),
        int(SNAKE_BODY_SHADOW[2] * fade_factor)
    )
    
    # Draw diamond pattern
    for row in range(3):
        for col in range(3):
            scale_x = x + 3 + col * 5 + offset
            scale_y = y + 4 + row * 5
            
            if scale_x < x + cell_size - 3 and scale_y < y + cell_size - 3:
                # Diamond shape for each scale
                points = [
                    (scale_x + scale_size // 2, scale_y),
                    (scale_x + scale_size, scale_y + scale_size // 2),
                    (scale_x + scale_size // 2, scale_y + scale_size),
                    (scale_x, scale_y + scale_size // 2)
                ]
                pygame.draw.polygon(surface, pattern_color, points)
                # Scale edge/shadow
                pygame.draw.polygon(surface, shadow_color, points, 1)


def draw_snake_tail(surface, x, y, cell_size, direction):
    """
    Draw a pointed snake tail.
    """
    center_x = x + cell_size // 2
    center_y = y + cell_size // 2
    
    # Determine tail direction (opposite of movement)
    if direction == RIGHT:
        points = [
            (x + cell_size - 2, y + 2),
            (x + cell_size - 2, y + cell_size - 2),
            (x + 2, center_y)
        ]
    elif direction == LEFT:
        points = [
            (x + 2, y + 2),
            (x + 2, y + cell_size - 2),
            (x + cell_size - 2, center_y)
        ]
    elif direction == UP:
        points = [
            (x + 2, y + 2),
            (x + cell_size - 2, y + 2),
            (center_x, y + cell_size - 2)
        ]
    else:  # DOWN
        points = [
            (x + 2, y + cell_size - 2),
            (x + cell_size - 2, y + cell_size - 2),
            (center_x, y + 2)
        ]
    
    pygame.draw.polygon(surface, SNAKE_BODY_SECONDARY, points)
    # Add slight highlight
    pygame.draw.polygon(surface, SNAKE_BODY_PATTERN, points, 1)


# ============== Animal Drawing Functions ==============

def draw_animal(surface, x, y, cell_size, animal_type):
    """
    Draw the specified animal type at the given position.
    For single-cell animals, draws at (x, y).
    For multi-cell animals, draws the complete animal spanning multiple cells.
    """
    draw_functions = {
        # Small animals
        'mouse': draw_mouse,
        'frog': draw_frog,
        'bug': draw_bug,
        'cricket': draw_cricket,
        'worm': draw_worm,
        'butterfly': draw_butterfly,
        'spider': draw_spider,
        'snail': draw_snail,
        'ant': draw_ant,
        'bee': draw_bee,
        'ladybug': draw_ladybug,
        'firefly': draw_firefly,
        # Medium animals
        'rabbit': draw_rabbit,
        'lizard': draw_lizard,
        'fish': draw_fish,
        'snake_prey': draw_snake_prey,
        'turtle': draw_turtle,
        'duck': draw_duck,
        # Large animals
        'bird': draw_bird,
        'fox': draw_fox,
        'wolf': draw_wolf,
        'deer': draw_deer,
        'pig': draw_pig,
        # Huge animals
        'tiger': draw_tiger,
        'lion': draw_lion,
        'bear': draw_bear,
        'crocodile': draw_crocodile,
        'hippo': draw_hippo,
        'elephant': draw_elephant,
    }
    
    if animal_type in draw_functions:
        draw_functions[animal_type](surface, x, y, cell_size)


def draw_mouse(surface, x, y, cell_size):
    """Draw a cute mouse."""
    center_x = x + cell_size // 2
    center_y = y + cell_size // 2
    
    # Body (oval)
    body_rect = pygame.Rect(x + 3, y + 6, cell_size - 6, cell_size - 8)
    pygame.draw.ellipse(surface, MOUSE_BODY, body_rect)
    
    # Ears
    pygame.draw.circle(surface, MOUSE_EAR, (x + 5, y + 5), 4)
    pygame.draw.circle(surface, MOUSE_EAR, (x + cell_size - 5, y + 5), 4)
    pygame.draw.circle(surface, MOUSE_BODY, (x + 5, y + 5), 2)
    pygame.draw.circle(surface, MOUSE_BODY, (x + cell_size - 5, y + 5), 2)
    
    # Eyes
    pygame.draw.circle(surface, BLACK, (x + 7, y + 9), 2)
    pygame.draw.circle(surface, BLACK, (x + cell_size - 7, y + 9), 2)
    pygame.draw.circle(surface, WHITE, (x + 8, y + 8), 1)
    pygame.draw.circle(surface, WHITE, (x + cell_size - 6, y + 8), 1)
    
    # Nose
    pygame.draw.circle(surface, (255, 150, 150), (center_x, y + 11), 2)
    
    # Whiskers
    pygame.draw.line(surface, GRAY, (x + 3, y + 10), (x + 7, y + 11), 1)
    pygame.draw.line(surface, GRAY, (x + 3, y + 12), (x + 7, y + 12), 1)
    pygame.draw.line(surface, GRAY, (x + cell_size - 3, y + 10), (x + cell_size - 7, y + 11), 1)
    pygame.draw.line(surface, GRAY, (x + cell_size - 3, y + 12), (x + cell_size - 7, y + 12), 1)
    
    # Tail
    pygame.draw.arc(surface, MOUSE_TAIL, (x - 2, y + 8, 10, 10), 0, 3.14, 2)


def draw_frog(surface, x, y, cell_size):
    """Draw a cute frog."""
    center_x = x + cell_size // 2
    center_y = y + cell_size // 2
    
    # Body
    body_rect = pygame.Rect(x + 2, y + 6, cell_size - 4, cell_size - 6)
    pygame.draw.ellipse(surface, FROG_BODY, body_rect)
    
    # Belly
    belly_rect = pygame.Rect(x + 5, y + 10, cell_size - 10, cell_size - 12)
    pygame.draw.ellipse(surface, FROG_BELLY, belly_rect)
    
    # Eyes (bulging)
    pygame.draw.circle(surface, FROG_BODY, (x + 5, y + 5), 5)
    pygame.draw.circle(surface, FROG_BODY, (x + cell_size - 5, y + 5), 5)
    pygame.draw.circle(surface, FROG_EYE, (x + 5, y + 5), 3)
    pygame.draw.circle(surface, FROG_EYE, (x + cell_size - 5, y + 5), 3)
    pygame.draw.circle(surface, BLACK, (x + 5, y + 5), 2)
    pygame.draw.circle(surface, BLACK, (x + cell_size - 5, y + 5), 2)
    
    # Mouth (smile)
    pygame.draw.arc(surface, BLACK, (x + 5, y + 8, 10, 6), 3.14, 0, 1)
    
    # Front legs
    pygame.draw.ellipse(surface, FROG_BODY, (x, y + cell_size - 6, 6, 4))
    pygame.draw.ellipse(surface, FROG_BODY, (x + cell_size - 6, y + cell_size - 6, 6, 4))


def draw_bug(surface, x, y, cell_size):
    """Draw a beetle/ladybug."""
    center_x = x + cell_size // 2
    center_y = y + cell_size // 2
    
    # Shell
    shell_rect = pygame.Rect(x + 3, y + 4, cell_size - 6, cell_size - 6)
    pygame.draw.ellipse(surface, BUG_SHELL, shell_rect)
    
    # Shell line
    pygame.draw.line(surface, BUG_BODY, (center_x, y + 4), (center_x, y + cell_size - 3), 1)
    
    # Spots
    pygame.draw.circle(surface, BLACK, (x + 7, y + 8), 2)
    pygame.draw.circle(surface, BLACK, (x + cell_size - 7, y + 8), 2)
    pygame.draw.circle(surface, BLACK, (x + 7, y + 13), 2)
    pygame.draw.circle(surface, BLACK, (x + cell_size - 7, y + 13), 2)
    
    # Head
    pygame.draw.circle(surface, BUG_BODY, (center_x, y + 3), 4)
    
    # Antennae
    pygame.draw.line(surface, BUG_LEGS, (center_x - 2, y + 1), (center_x - 4, y - 2), 1)
    pygame.draw.line(surface, BUG_LEGS, (center_x + 2, y + 1), (center_x + 4, y - 2), 1)
    
    # Legs
    for i in range(3):
        leg_y = y + 7 + i * 4
        pygame.draw.line(surface, BUG_LEGS, (x + 3, leg_y), (x, leg_y + 2), 1)
        pygame.draw.line(surface, BUG_LEGS, (x + cell_size - 3, leg_y), (x + cell_size, leg_y + 2), 1)


def draw_cricket(surface, x, y, cell_size):
    """Draw a cricket."""
    center_x = x + cell_size // 2
    center_y = y + cell_size // 2
    
    # Body
    body_rect = pygame.Rect(x + 4, y + 6, cell_size - 8, cell_size - 8)
    pygame.draw.ellipse(surface, CRICKET_BODY, body_rect)
    
    # Head
    pygame.draw.circle(surface, CRICKET_BODY, (center_x, y + 5), 4)
    
    # Eyes
    pygame.draw.circle(surface, BLACK, (center_x - 2, y + 4), 1)
    pygame.draw.circle(surface, BLACK, (center_x + 2, y + 4), 1)
    
    # Antennae (long)
    pygame.draw.line(surface, CRICKET_LEGS, (center_x - 2, y + 2), (x, y - 3), 1)
    pygame.draw.line(surface, CRICKET_LEGS, (center_x + 2, y + 2), (x + cell_size, y - 3), 1)
    
    # Back legs (big jumping legs)
    pygame.draw.line(surface, CRICKET_LEGS, (x + 5, y + 12), (x, y + 8), 2)
    pygame.draw.line(surface, CRICKET_LEGS, (x, y + 8), (x - 2, y + cell_size), 2)
    pygame.draw.line(surface, CRICKET_LEGS, (x + cell_size - 5, y + 12), (x + cell_size, y + 8), 2)
    pygame.draw.line(surface, CRICKET_LEGS, (x + cell_size, y + 8), (x + cell_size + 2, y + cell_size), 2)
    
    # Front legs
    pygame.draw.line(surface, CRICKET_LEGS, (x + 6, y + 10), (x + 2, y + 14), 1)
    pygame.draw.line(surface, CRICKET_LEGS, (x + cell_size - 6, y + 10), (x + cell_size - 2, y + 14), 1)


def draw_worm(surface, x, y, cell_size):
    """Draw a wiggly worm."""
    center_y = y + cell_size // 2
    
    # Draw segmented worm body
    segment_width = 4
    for i in range(4):
        seg_x = x + 2 + i * 4
        seg_y = center_y + (2 if i % 2 == 0 else -2)
        color = WORM_BODY if i % 2 == 0 else WORM_SEGMENT
        pygame.draw.circle(surface, color, (seg_x + 2, seg_y), 4)
    
    # Head
    pygame.draw.circle(surface, WORM_BODY, (x + cell_size - 4, center_y), 5)
    
    # Eyes
    pygame.draw.circle(surface, BLACK, (x + cell_size - 4, center_y - 2), 1)
    pygame.draw.circle(surface, BLACK, (x + cell_size - 2, center_y - 2), 1)
    
    # Cheeks
    pygame.draw.circle(surface, (255, 180, 180), (x + cell_size - 6, center_y + 1), 2)


def draw_butterfly(surface, x, y, cell_size):
    """Draw a colorful butterfly."""
    center_x = x + cell_size // 2
    center_y = y + cell_size // 2
    
    # Wings (top)
    pygame.draw.ellipse(surface, BUTTERFLY_WING1, (x + 1, y + 2, 8, 10))
    pygame.draw.ellipse(surface, BUTTERFLY_WING1, (x + cell_size - 9, y + 2, 8, 10))
    
    # Wings (bottom)
    pygame.draw.ellipse(surface, BUTTERFLY_WING2, (x + 2, y + 10, 6, 7))
    pygame.draw.ellipse(surface, BUTTERFLY_WING2, (x + cell_size - 8, y + 10, 6, 7))
    
    # Wing patterns
    pygame.draw.circle(surface, WHITE, (x + 5, y + 7), 2)
    pygame.draw.circle(surface, WHITE, (x + cell_size - 5, y + 7), 2)
    
    # Body
    pygame.draw.ellipse(surface, BUTTERFLY_BODY, (center_x - 2, y + 3, 4, 14))
    
    # Antennae
    pygame.draw.line(surface, BUTTERFLY_BODY, (center_x - 1, y + 3), (center_x - 3, y), 1)
    pygame.draw.line(surface, BUTTERFLY_BODY, (center_x + 1, y + 3), (center_x + 3, y), 1)
    pygame.draw.circle(surface, BUTTERFLY_BODY, (center_x - 3, y), 1)
    pygame.draw.circle(surface, BUTTERFLY_BODY, (center_x + 3, y), 1)


def draw_spider(surface, x, y, cell_size):
    """Draw a spider."""
    center_x = x + cell_size // 2
    center_y = y + cell_size // 2
    
    # Abdomen (back)
    pygame.draw.ellipse(surface, SPIDER_BODY, (center_x - 4, center_y, 8, 8))
    
    # Cephalothorax (front)
    pygame.draw.circle(surface, SPIDER_BODY, (center_x, center_y - 2), 5)
    
    # Eyes (8 eyes in 2 rows)
    for i in range(4):
        pygame.draw.circle(surface, (200, 0, 0), (center_x - 3 + i * 2, center_y - 4), 1)
    for i in range(2):
        pygame.draw.circle(surface, (200, 0, 0), (center_x - 1 + i * 2, center_y - 2), 1)
    
    # Legs (8 legs)
    leg_positions = [
        (-5, -2), (-6, 0), (-6, 2), (-5, 4),
        (5, -2), (6, 0), (6, 2), (5, 4)
    ]
    for lx, ly in leg_positions:
        start = (center_x + lx // 2, center_y + ly)
        mid = (center_x + lx, center_y + ly - 2)
        end = (center_x + lx + (3 if lx > 0 else -3), center_y + ly + 3)
        pygame.draw.line(surface, SPIDER_LEGS, start, mid, 1)
        pygame.draw.line(surface, SPIDER_LEGS, mid, end, 1)


def draw_snail(surface, x, y, cell_size):
    """Draw a snail with shell."""
    center_x = x + cell_size // 2
    center_y = y + cell_size // 2
    
    # Shell (spiral)
    pygame.draw.circle(surface, SNAIL_SHELL, (center_x + 2, center_y), 7)
    pygame.draw.circle(surface, (180, 150, 120), (center_x + 2, center_y), 5)
    pygame.draw.circle(surface, SNAIL_SHELL, (center_x + 2, center_y), 3)
    
    # Body
    body_rect = pygame.Rect(x + 1, center_y + 2, 12, 6)
    pygame.draw.ellipse(surface, SNAIL_BODY, body_rect)
    
    # Head
    pygame.draw.circle(surface, SNAIL_BODY, (x + 4, center_y + 2), 4)
    
    # Eye stalks
    pygame.draw.line(surface, SNAIL_BODY, (x + 3, center_y), (x + 1, center_y - 5), 1)
    pygame.draw.line(surface, SNAIL_BODY, (x + 5, center_y), (x + 6, center_y - 5), 1)
    
    # Eyes
    pygame.draw.circle(surface, BLACK, (x + 1, center_y - 5), 2)
    pygame.draw.circle(surface, BLACK, (x + 6, center_y - 5), 2)


def draw_ant(surface, x, y, cell_size):
    """Draw an ant."""
    center_x = x + cell_size // 2
    center_y = y + cell_size // 2
    
    # Body segments
    pygame.draw.ellipse(surface, ANT_BODY, (center_x - 2, center_y + 2, 8, 6))  # abdomen
    pygame.draw.circle(surface, ANT_BODY, (center_x - 2, center_y + 2), 4)  # thorax
    pygame.draw.circle(surface, ANT_BODY, (center_x - 5, center_y), 3)  # head
    
    # Legs
    for i in range(3):
        pygame.draw.line(surface, ANT_LEGS, (center_x - 2 + i*2, center_y + 4), 
                        (center_x - 4 + i*2, center_y + 8), 1)
        pygame.draw.line(surface, ANT_LEGS, (center_x - 2 + i*2, center_y + 4), 
                        (center_x + i*2, center_y + 8), 1)
    
    # Antennae
    pygame.draw.line(surface, ANT_LEGS, (center_x - 6, center_y - 1), (center_x - 9, center_y - 4), 1)
    pygame.draw.line(surface, ANT_LEGS, (center_x - 4, center_y - 1), (center_x - 3, center_y - 5), 1)


def draw_bee(surface, x, y, cell_size):
    """Draw a bee."""
    center_x = x + cell_size // 2
    center_y = y + cell_size // 2
    
    # Wings
    pygame.draw.ellipse(surface, BEE_WINGS, (center_x - 6, center_y - 6, 8, 5))
    pygame.draw.ellipse(surface, BEE_WINGS, (center_x + 2, center_y - 6, 8, 5))
    
    # Body
    pygame.draw.ellipse(surface, BEE_BODY, (center_x - 5, center_y - 2, 14, 10))
    
    # Stripes
    pygame.draw.line(surface, BEE_STRIPES, (center_x - 2, center_y - 1), (center_x - 2, center_y + 6), 2)
    pygame.draw.line(surface, BEE_STRIPES, (center_x + 2, center_y - 1), (center_x + 2, center_y + 6), 2)
    pygame.draw.line(surface, BEE_STRIPES, (center_x + 6, center_y), (center_x + 6, center_y + 5), 2)
    
    # Head
    pygame.draw.circle(surface, BEE_STRIPES, (center_x - 6, center_y + 2), 4)
    
    # Eyes
    pygame.draw.circle(surface, WHITE, (center_x - 7, center_y + 1), 2)
    pygame.draw.circle(surface, BLACK, (center_x - 7, center_y + 1), 1)


def draw_ladybug(surface, x, y, cell_size):
    """Draw a ladybug."""
    center_x = x + cell_size // 2
    center_y = y + cell_size // 2
    
    # Shell
    pygame.draw.ellipse(surface, LADYBUG_SHELL, (x + 3, y + 4, cell_size - 6, cell_size - 6))
    
    # Shell line
    pygame.draw.line(surface, LADYBUG_HEAD, (center_x, y + 4), (center_x, y + cell_size - 3), 1)
    
    # Spots
    pygame.draw.circle(surface, LADYBUG_SPOTS, (center_x - 4, center_y), 2)
    pygame.draw.circle(surface, LADYBUG_SPOTS, (center_x + 4, center_y), 2)
    pygame.draw.circle(surface, LADYBUG_SPOTS, (center_x - 2, center_y + 4), 2)
    pygame.draw.circle(surface, LADYBUG_SPOTS, (center_x + 2, center_y + 4), 2)
    
    # Head
    pygame.draw.circle(surface, LADYBUG_HEAD, (center_x, y + 3), 4)
    
    # Eyes
    pygame.draw.circle(surface, WHITE, (center_x - 2, y + 2), 1)
    pygame.draw.circle(surface, WHITE, (center_x + 2, y + 2), 1)


def draw_firefly(surface, x, y, cell_size):
    """Draw a firefly with glowing abdomen."""
    center_x = x + cell_size // 2
    center_y = y + cell_size // 2
    
    # Glow effect
    for r in range(6, 2, -1):
        alpha = 50 + (6 - r) * 30
        glow_color = (FIREFLY_GLOW[0], FIREFLY_GLOW[1], FIREFLY_GLOW[2])
        pygame.draw.circle(surface, glow_color, (center_x + 2, center_y + 3), r)
    
    # Body
    pygame.draw.ellipse(surface, FIREFLY_BODY, (center_x - 4, center_y - 2, 8, 6))
    
    # Glowing abdomen
    pygame.draw.ellipse(surface, FIREFLY_GLOW, (center_x, center_y, 6, 6))
    
    # Head
    pygame.draw.circle(surface, FIREFLY_BODY, (center_x - 5, center_y + 1), 3)
    
    # Wings
    pygame.draw.ellipse(surface, (100, 90, 80), (center_x - 6, center_y - 5, 6, 4))
    pygame.draw.ellipse(surface, (100, 90, 80), (center_x + 2, center_y - 5, 6, 4))
    
    # Antennae
    pygame.draw.line(surface, FIREFLY_BODY, (center_x - 6, center_y - 1), (center_x - 8, center_y - 4), 1)
    pygame.draw.line(surface, FIREFLY_BODY, (center_x - 4, center_y - 1), (center_x - 3, center_y - 4), 1)


# ============== Medium Animal Drawing Functions ==============

def draw_rabbit(surface, x, y, cell_size):
    """
    Draw a rabbit spanning 2 cells horizontally.
    The anchor cell (x, y) contains the head, (x + cell_size, y) contains the body.
    """
    # Body (right cell)
    body_x = x + cell_size
    body_rect = pygame.Rect(body_x + 2, y + 4, cell_size - 4, cell_size - 6)
    pygame.draw.ellipse(surface, RABBIT_BODY, body_rect)
    
    # Fluffy tail
    pygame.draw.circle(surface, WHITE, (body_x + cell_size - 5, y + cell_size // 2), 5)
    pygame.draw.circle(surface, (240, 235, 230), (body_x + cell_size - 5, y + cell_size // 2), 3)
    
    # Head (left cell)
    head_rect = pygame.Rect(x + 3, y + 5, cell_size - 6, cell_size - 7)
    pygame.draw.ellipse(surface, RABBIT_BODY, head_rect)
    
    # Ears (long)
    ear_left = [(x + 5, y + 5), (x + 3, y - 4), (x + 8, y + 2)]
    ear_right = [(x + cell_size - 5, y + 5), (x + cell_size - 3, y - 4), (x + cell_size - 8, y + 2)]
    pygame.draw.polygon(surface, RABBIT_BODY, ear_left)
    pygame.draw.polygon(surface, RABBIT_BODY, ear_right)
    
    # Inner ears
    pygame.draw.line(surface, RABBIT_EAR_INNER, (x + 5, y + 3), (x + 4, y - 1), 2)
    pygame.draw.line(surface, RABBIT_EAR_INNER, (x + cell_size - 5, y + 3), (x + cell_size - 4, y - 1), 2)
    
    # Eyes
    pygame.draw.circle(surface, BLACK, (x + 6, y + 9), 3)
    pygame.draw.circle(surface, BLACK, (x + cell_size - 6, y + 9), 3)
    pygame.draw.circle(surface, WHITE, (x + 7, y + 8), 1)
    pygame.draw.circle(surface, WHITE, (x + cell_size - 5, y + 8), 1)
    
    # Nose
    pygame.draw.circle(surface, RABBIT_NOSE, (x + cell_size // 2, y + 13), 3)
    
    # Whiskers
    center_x = x + cell_size // 2
    pygame.draw.line(surface, GRAY, (x + 2, y + 12), (x + 6, y + 14), 1)
    pygame.draw.line(surface, GRAY, (x + 2, y + 14), (x + 6, y + 15), 1)
    pygame.draw.line(surface, GRAY, (x + cell_size - 2, y + 12), (x + cell_size - 6, y + 14), 1)
    pygame.draw.line(surface, GRAY, (x + cell_size - 2, y + 14), (x + cell_size - 6, y + 15), 1)
    
    # Front paws
    pygame.draw.ellipse(surface, RABBIT_BODY, (x + 2, y + cell_size - 6, 6, 5))
    pygame.draw.ellipse(surface, RABBIT_BODY, (x + cell_size - 8, y + cell_size - 6, 6, 5))
    
    # Back legs (on body)
    pygame.draw.ellipse(surface, RABBIT_BODY, (body_x + 2, y + cell_size - 8, 10, 7))


def draw_lizard(surface, x, y, cell_size):
    """
    Draw a lizard spanning 3 cells horizontally.
    Layout: [tail] [body] [head] - anchor at head (x, y)
    """
    # Colors
    body_color = LIZARD_BODY
    belly_color = LIZARD_BELLY
    spots_color = LIZARD_SPOTS
    
    # Head (anchor cell at x, y)
    head_center_x = x + cell_size // 2
    head_center_y = y + cell_size // 2
    
    # Head shape
    head_points = [
        (x + cell_size - 2, head_center_y - 4),  # right top
        (x + cell_size - 2, head_center_y + 4),  # right bottom
        (x + 2, head_center_y + 6),              # left bottom
        (x + 2, head_center_y - 6),              # left top
    ]
    pygame.draw.polygon(surface, body_color, head_points)
    
    # Eyes
    pygame.draw.circle(surface, LIZARD_EYE, (x + 6, head_center_y - 3), 3)
    pygame.draw.circle(surface, LIZARD_EYE, (x + 6, head_center_y + 3), 3)
    pygame.draw.circle(surface, BLACK, (x + 5, head_center_y - 3), 2)
    pygame.draw.circle(surface, BLACK, (x + 5, head_center_y + 3), 2)
    
    # Tongue
    pygame.draw.line(surface, (255, 100, 100), (x + 2, head_center_y), (x - 3, head_center_y - 2), 1)
    pygame.draw.line(surface, (255, 100, 100), (x + 2, head_center_y), (x - 3, head_center_y + 2), 1)
    
    # Body (middle cell)
    body_x = x + cell_size
    body_rect = pygame.Rect(body_x + 1, y + 4, cell_size - 2, cell_size - 8)
    pygame.draw.ellipse(surface, body_color, body_rect)
    
    # Belly
    belly_rect = pygame.Rect(body_x + 4, y + 6, cell_size - 8, cell_size - 12)
    pygame.draw.ellipse(surface, belly_color, belly_rect)
    
    # Body spots
    pygame.draw.circle(surface, spots_color, (body_x + 5, y + 7), 2)
    pygame.draw.circle(surface, spots_color, (body_x + cell_size - 5, y + 7), 2)
    pygame.draw.circle(surface, spots_color, (body_x + cell_size // 2, y + 5), 2)
    
    # Legs from body
    pygame.draw.ellipse(surface, body_color, (body_x - 2, y + 2, 8, 5))      # front left
    pygame.draw.ellipse(surface, body_color, (body_x - 2, y + cell_size - 7, 8, 5))  # back left
    pygame.draw.ellipse(surface, body_color, (body_x + cell_size - 6, y + 2, 8, 5))  # front right
    pygame.draw.ellipse(surface, body_color, (body_x + cell_size - 6, y + cell_size - 7, 8, 5))  # back right
    
    # Tail (right cell)
    tail_x = x + cell_size * 2
    tail_points = [
        (tail_x + 2, y + cell_size // 2 - 4),
        (tail_x + 2, y + cell_size // 2 + 4),
        (tail_x + cell_size - 2, y + cell_size // 2)
    ]
    pygame.draw.polygon(surface, body_color, tail_points)
    
    # Tail pattern
    pygame.draw.line(surface, spots_color, (tail_x + 5, y + cell_size // 2 - 2),
                     (tail_x + 5, y + cell_size // 2 + 2), 2)
    pygame.draw.line(surface, spots_color, (tail_x + 10, y + cell_size // 2 - 1),
                     (tail_x + 10, y + cell_size // 2 + 1), 2)


def draw_fish(surface, x, y, cell_size):
    """Draw a fish spanning 2 cells horizontally."""
    center_y = y + cell_size // 2
    
    # Tail (right cell)
    tail_x = x + cell_size
    tail_points = [
        (tail_x + cell_size - 2, center_y),
        (tail_x + 2, center_y - 6),
        (tail_x + 2, center_y + 6)
    ]
    pygame.draw.polygon(surface, FISH_FIN, tail_points)
    
    # Body (left cell)
    body_rect = pygame.Rect(x + 2, y + 3, cell_size + 4, cell_size - 6)
    pygame.draw.ellipse(surface, FISH_BODY, body_rect)
    
    # Scales
    for i in range(3):
        pygame.draw.arc(surface, FISH_SCALES, 
                       (x + 6 + i*5, center_y - 3, 6, 6), 0.5, 2.5, 1)
    
    # Eye
    pygame.draw.circle(surface, WHITE, (x + 5, center_y - 1), 3)
    pygame.draw.circle(surface, FISH_EYE, (x + 4, center_y - 1), 2)
    
    # Fins
    pygame.draw.polygon(surface, FISH_FIN, [
        (x + cell_size // 2, y + 4),
        (x + cell_size // 2 - 4, y - 2),
        (x + cell_size // 2 + 4, y - 2)
    ])


def draw_snake_prey(surface, x, y, cell_size):
    """Draw a small snake as prey, spanning 3 cells horizontally."""
    center_y = y + cell_size // 2
    
    # Head (left cell)
    pygame.draw.ellipse(surface, SNAKE_PREY_BODY, (x + 2, center_y - 4, cell_size - 4, 10))
    pygame.draw.circle(surface, BLACK, (x + 5, center_y - 1), 2)
    pygame.draw.circle(surface, BLACK, (x + 5, center_y + 3), 2)
    
    # Body (middle cell)
    body_x = x + cell_size
    pygame.draw.ellipse(surface, SNAKE_PREY_BODY, (body_x, center_y - 5, cell_size, 12))
    pygame.draw.ellipse(surface, SNAKE_PREY_BELLY, (body_x + 3, center_y - 2, cell_size - 6, 6))
    
    # Pattern
    for i in range(3):
        pygame.draw.circle(surface, SNAKE_PREY_PATTERN, (body_x + 4 + i*5, center_y - 3), 2)
    
    # Tail (right cell)
    tail_x = x + cell_size * 2
    pygame.draw.polygon(surface, SNAKE_PREY_BODY, [
        (tail_x, center_y - 4),
        (tail_x, center_y + 4),
        (tail_x + cell_size - 2, center_y)
    ])


def draw_turtle(surface, x, y, cell_size):
    """Draw a turtle spanning 3 cells (2 wide, 1 tall + leg cell)."""
    # Shell (main cells)
    shell_rect = pygame.Rect(x + 2, y + 2, cell_size * 2 - 4, cell_size - 4)
    pygame.draw.ellipse(surface, TURTLE_SHELL, shell_rect)
    
    # Shell pattern
    center_x = x + cell_size
    center_y = y + cell_size // 2
    pygame.draw.ellipse(surface, TURTLE_SHELL_PATTERN, (center_x - 6, center_y - 4, 12, 8))
    pygame.draw.line(surface, TURTLE_SHELL_PATTERN, (x + 6, center_y), (x + cell_size * 2 - 6, center_y), 1)
    
    # Head
    pygame.draw.circle(surface, TURTLE_SKIN, (x + 2, center_y), 5)
    pygame.draw.circle(surface, TURTLE_EYE, (x, center_y - 1), 2)
    
    # Legs
    leg_y = y + cell_size
    pygame.draw.ellipse(surface, TURTLE_SKIN, (x + 2, leg_y - 2, 6, 8))
    pygame.draw.ellipse(surface, TURTLE_SKIN, (x + cell_size - 2, leg_y - 2, 6, 8))
    
    # Tail
    pygame.draw.polygon(surface, TURTLE_SKIN, [
        (x + cell_size * 2 - 4, center_y),
        (x + cell_size * 2 + 2, center_y - 2),
        (x + cell_size * 2 + 2, center_y + 2)
    ])


def draw_duck(surface, x, y, cell_size):
    """Draw a duck spanning 3 cells horizontally."""
    center_y = y + cell_size // 2
    
    # Body (middle cell)
    body_x = x + cell_size
    pygame.draw.ellipse(surface, DUCK_BODY, (body_x - 2, y + 3, cell_size + 4, cell_size - 4))
    
    # Head (left cell)
    pygame.draw.circle(surface, DUCK_HEAD, (x + cell_size // 2, center_y - 2), 7)
    
    # Eye
    pygame.draw.circle(surface, WHITE, (x + cell_size // 2 - 2, center_y - 4), 2)
    pygame.draw.circle(surface, DUCK_EYE, (x + cell_size // 2 - 2, center_y - 4), 1)
    
    # Beak
    pygame.draw.polygon(surface, DUCK_BEAK, [
        (x + 3, center_y),
        (x - 3, center_y - 2),
        (x - 3, center_y + 2)
    ])
    
    # Tail (right cell)
    tail_x = x + cell_size * 2
    pygame.draw.polygon(surface, DUCK_BODY, [
        (tail_x, center_y - 3),
        (tail_x, center_y + 3),
        (tail_x + cell_size // 2, center_y - 5),
        (tail_x + cell_size // 2, center_y)
    ])
    
    # Wing
    pygame.draw.ellipse(surface, (160, 120, 60), (body_x + 2, y + 5, cell_size - 6, cell_size - 10))


# ============== Large Animal Drawing Functions ==============

def draw_bird(surface, x, y, cell_size):
    """
    Draw a bird spanning 2x2 cells.
    Layout:
      [head] [wing_right]   <- y
      [body] [wing_left]    <- y + cell_size
    Anchor at top-left (head position).
    """
    # Calculate positions
    head_x, head_y = x, y
    wing_r_x, wing_r_y = x + cell_size, y
    body_x, body_y = x, y + cell_size
    wing_l_x, wing_l_y = x + cell_size, y + cell_size
    
    # Body (bottom-left cell)
    body_rect = pygame.Rect(body_x + 2, body_y + 2, cell_size - 4, cell_size - 4)
    pygame.draw.ellipse(surface, BIRD_BODY, body_rect)
    
    # Belly
    belly_rect = pygame.Rect(body_x + 4, body_y + 5, cell_size - 8, cell_size - 8)
    pygame.draw.ellipse(surface, BIRD_BELLY, belly_rect)
    
    # Head (top-left cell)
    pygame.draw.circle(surface, BIRD_BODY, (head_x + cell_size // 2, head_y + cell_size // 2 + 2), cell_size // 2 - 3)
    
    # Eyes
    pygame.draw.circle(surface, WHITE, (head_x + 6, head_y + cell_size // 2), 4)
    pygame.draw.circle(surface, WHITE, (head_x + cell_size - 6, head_y + cell_size // 2), 4)
    pygame.draw.circle(surface, BIRD_EYE, (head_x + 5, head_y + cell_size // 2), 2)
    pygame.draw.circle(surface, BIRD_EYE, (head_x + cell_size - 5, head_y + cell_size // 2), 2)
    
    # Beak
    beak_points = [
        (head_x + cell_size // 2, head_y + cell_size - 3),
        (head_x + cell_size // 2 - 4, head_y + cell_size + 3),
        (head_x + cell_size // 2 + 4, head_y + cell_size + 3)
    ]
    pygame.draw.polygon(surface, BIRD_BEAK, beak_points)
    
    # Right wing (top-right cell)
    wing_r_points = [
        (wing_r_x + 2, wing_r_y + cell_size // 2),
        (wing_r_x + cell_size - 2, wing_r_y + 3),
        (wing_r_x + cell_size - 2, wing_r_y + cell_size - 3)
    ]
    pygame.draw.polygon(surface, BIRD_WING, wing_r_points)
    
    # Wing feather details
    pygame.draw.line(surface, BIRD_BODY, (wing_r_x + 4, wing_r_y + cell_size // 2),
                     (wing_r_x + cell_size - 4, wing_r_y + cell_size // 3), 1)
    pygame.draw.line(surface, BIRD_BODY, (wing_r_x + 4, wing_r_y + cell_size // 2 + 3),
                     (wing_r_x + cell_size - 4, wing_r_y + cell_size * 2 // 3), 1)
    
    # Left wing (bottom-right cell)
    wing_l_points = [
        (wing_l_x + 2, wing_l_y + cell_size // 2),
        (wing_l_x + cell_size - 2, wing_l_y + 3),
        (wing_l_x + cell_size - 2, wing_l_y + cell_size - 3)
    ]
    pygame.draw.polygon(surface, BIRD_WING, wing_l_points)
    
    # Wing feather details
    pygame.draw.line(surface, BIRD_BODY, (wing_l_x + 4, wing_l_y + cell_size // 2),
                     (wing_l_x + cell_size - 4, wing_l_y + cell_size // 3), 1)
    pygame.draw.line(surface, BIRD_BODY, (wing_l_x + 4, wing_l_y + cell_size // 2 + 3),
                     (wing_l_x + cell_size - 4, wing_l_y + cell_size * 2 // 3), 1)
    
    # Tail feathers (extend from body)
    tail_y = body_y + cell_size - 4
    pygame.draw.line(surface, BIRD_WING, (body_x + 3, tail_y), (body_x - 5, tail_y + 8), 2)
    pygame.draw.line(surface, BIRD_WING, (body_x + cell_size // 2, tail_y), (body_x + cell_size // 2, tail_y + 10), 2)
    pygame.draw.line(surface, BIRD_WING, (body_x + cell_size - 3, tail_y), (body_x + cell_size + 5, tail_y + 8), 2)
    
    # Feet
    pygame.draw.line(surface, BIRD_BEAK, (body_x + 5, body_y + cell_size - 2), (body_x + 3, body_y + cell_size + 4), 2)
    pygame.draw.line(surface, BIRD_BEAK, (body_x + cell_size - 5, body_y + cell_size - 2), (body_x + cell_size - 3, body_y + cell_size + 4), 2)


def draw_fox(surface, x, y, cell_size):
    """Draw a fox spanning 4 cells (L-shape: 3 horizontal + 1 below left)."""
    center_y = y + cell_size // 2
    
    # Body (cells 0,1,2 horizontally)
    body_rect = pygame.Rect(x + 2, y + 3, cell_size * 3 - 4, cell_size - 5)
    pygame.draw.ellipse(surface, FOX_BODY, body_rect)
    
    # Belly
    belly_rect = pygame.Rect(x + cell_size, y + 6, cell_size, cell_size - 10)
    pygame.draw.ellipse(surface, FOX_BELLY, belly_rect)
    
    # Head (leftmost)
    pygame.draw.circle(surface, FOX_BODY, (x + cell_size // 2, center_y - 2), 8)
    
    # Ears
    pygame.draw.polygon(surface, FOX_BODY, [
        (x + 3, center_y - 6), (x, y - 2), (x + 8, center_y - 8)
    ])
    pygame.draw.polygon(surface, FOX_BODY, [
        (x + cell_size - 3, center_y - 6), (x + cell_size, y - 2), (x + cell_size - 8, center_y - 8)
    ])
    
    # Eyes
    pygame.draw.circle(surface, FOX_EYE, (x + 5, center_y - 4), 2)
    pygame.draw.circle(surface, FOX_EYE, (x + cell_size - 5, center_y - 4), 2)
    
    # Snout
    pygame.draw.ellipse(surface, FOX_BELLY, (x + 4, center_y - 1, 12, 8))
    pygame.draw.circle(surface, BLACK, (x + cell_size // 2, center_y + 1), 2)
    
    # Tail (rightmost)
    tail_x = x + cell_size * 2
    pygame.draw.ellipse(surface, FOX_BODY, (tail_x + 2, center_y - 6, cell_size - 2, 12))
    pygame.draw.circle(surface, FOX_TAIL_TIP, (tail_x + cell_size - 4, center_y - 2), 4)
    
    # Legs (bottom cell at 0,1)
    leg_y = y + cell_size
    pygame.draw.rect(surface, FOX_BODY, (x + 3, leg_y - 2, 5, cell_size - 2))
    pygame.draw.rect(surface, FOX_BODY, (x + cell_size - 8, leg_y - 2, 5, cell_size - 2))


def draw_wolf(surface, x, y, cell_size):
    """Draw a wolf spanning 5 cells (cross shape)."""
    # Layout: top center, middle row of 3, bottom center
    # Positions: (1,0), (0,1), (1,1), (2,1), (1,2)
    
    # Head (top center at 1,0)
    head_x = x + cell_size
    pygame.draw.circle(surface, WOLF_BODY, (head_x + cell_size // 2, y + cell_size // 2), 9)
    
    # Ears
    pygame.draw.polygon(surface, WOLF_BODY, [
        (head_x + 2, y + 6), (head_x - 2, y - 4), (head_x + 8, y + 2)
    ])
    pygame.draw.polygon(surface, WOLF_BODY, [
        (head_x + cell_size - 2, y + 6), (head_x + cell_size + 2, y - 4), (head_x + cell_size - 8, y + 2)
    ])
    
    # Eyes
    pygame.draw.circle(surface, WOLF_EYE, (head_x + 5, y + 8), 3)
    pygame.draw.circle(surface, WOLF_EYE, (head_x + cell_size - 5, y + 8), 3)
    pygame.draw.circle(surface, BLACK, (head_x + 5, y + 8), 1)
    pygame.draw.circle(surface, BLACK, (head_x + cell_size - 5, y + 8), 1)
    
    # Snout
    pygame.draw.ellipse(surface, WOLF_MUZZLE, (head_x + 4, y + 10, 12, 8))
    pygame.draw.circle(surface, BLACK, (head_x + cell_size // 2, y + 12), 2)
    
    # Body (middle row)
    body_y = y + cell_size
    pygame.draw.ellipse(surface, WOLF_BODY, (x + 2, body_y + 2, cell_size * 3 - 4, cell_size - 4))
    pygame.draw.ellipse(surface, WOLF_BELLY, (x + cell_size, body_y + 4, cell_size, cell_size - 8))
    
    # Tail (bottom center at 1,2)
    tail_y = y + cell_size * 2
    pygame.draw.ellipse(surface, WOLF_BODY, (x + cell_size + 2, tail_y, cell_size - 4, cell_size - 2))


def draw_deer(surface, x, y, cell_size):
    """Draw a deer spanning 4 cells vertically."""
    center_x = x + cell_size // 2
    
    # Antlers (top cell)
    pygame.draw.line(surface, DEER_ANTLERS, (center_x - 4, y + cell_size - 4), (center_x - 8, y + 2), 2)
    pygame.draw.line(surface, DEER_ANTLERS, (center_x - 8, y + 6), (center_x - 12, y + 2), 2)
    pygame.draw.line(surface, DEER_ANTLERS, (center_x + 4, y + cell_size - 4), (center_x + 8, y + 2), 2)
    pygame.draw.line(surface, DEER_ANTLERS, (center_x + 8, y + 6), (center_x + 12, y + 2), 2)
    
    # Head (cell 0)
    pygame.draw.ellipse(surface, DEER_BODY, (x + 3, y + 4, cell_size - 6, cell_size - 2))
    
    # Eyes
    pygame.draw.circle(surface, BLACK, (center_x - 4, y + 10), 2)
    pygame.draw.circle(surface, BLACK, (center_x + 4, y + 10), 2)
    
    # Nose
    pygame.draw.circle(surface, (60, 40, 30), (center_x, y + 16), 2)
    
    # Neck and body (cells 1,2)
    body_y = y + cell_size
    pygame.draw.ellipse(surface, DEER_BODY, (x + 2, body_y, cell_size - 4, cell_size * 2))
    pygame.draw.ellipse(surface, DEER_BELLY, (x + 4, body_y + cell_size // 2, cell_size - 8, cell_size))
    
    # Spots
    pygame.draw.circle(surface, DEER_SPOTS, (center_x - 3, body_y + cell_size // 2), 2)
    pygame.draw.circle(surface, DEER_SPOTS, (center_x + 3, body_y + cell_size), 2)
    
    # Legs (cell 3)
    leg_y = y + cell_size * 3
    pygame.draw.rect(surface, DEER_BODY, (x + 3, leg_y, 4, cell_size - 2))
    pygame.draw.rect(surface, DEER_BODY, (x + cell_size - 7, leg_y, 4, cell_size - 2))


def draw_pig(surface, x, y, cell_size):
    """Draw a pig spanning 4 cells (2x2)."""
    # Body covers all 4 cells
    pygame.draw.ellipse(surface, PIG_BODY, (x + 2, y + 2, cell_size * 2 - 4, cell_size * 2 - 4))
    
    # Head area (top-left emphasis)
    pygame.draw.circle(surface, PIG_BODY, (x + cell_size // 2, y + cell_size // 2), 8)
    
    # Ears
    pygame.draw.ellipse(surface, PIG_BODY, (x + 2, y + 2, 8, 10))
    pygame.draw.ellipse(surface, PIG_BODY, (x + cell_size - 8, y + 2, 8, 10))
    
    # Eyes
    pygame.draw.circle(surface, PIG_EYE, (x + 6, y + cell_size // 2), 2)
    pygame.draw.circle(surface, PIG_EYE, (x + cell_size - 6, y + cell_size // 2), 2)
    
    # Snout
    pygame.draw.ellipse(surface, PIG_SNOUT, (x + cell_size // 2 - 5, y + cell_size // 2 + 2, 10, 8))
    pygame.draw.circle(surface, (200, 120, 120), (x + cell_size // 2 - 2, y + cell_size // 2 + 5), 2)
    pygame.draw.circle(surface, (200, 120, 120), (x + cell_size // 2 + 2, y + cell_size // 2 + 5), 2)
    
    # Curly tail (bottom-right)
    tail_x = x + cell_size + cell_size // 2
    tail_y = y + cell_size + cell_size // 2
    pygame.draw.arc(surface, PIG_SNOUT, (tail_x, tail_y - 4, 10, 10), 0, 4, 2)


# ============== Huge Animal Drawing Functions ==============

def draw_tiger(surface, x, y, cell_size):
    """Draw a tiger spanning 6 cells (3x2)."""
    # Body
    pygame.draw.ellipse(surface, TIGER_BODY, (x + 2, y + 2, cell_size * 3 - 4, cell_size * 2 - 4))
    pygame.draw.ellipse(surface, TIGER_BELLY, (x + cell_size, y + cell_size, cell_size, cell_size - 6))
    
    # Stripes
    for i in range(5):
        stripe_x = x + 15 + i * 12
        pygame.draw.line(surface, TIGER_STRIPES, (stripe_x, y + 4), (stripe_x - 3, y + cell_size * 2 - 6), 3)
    
    # Head (left side)
    pygame.draw.circle(surface, TIGER_BODY, (x + 10, y + cell_size), 12)
    
    # Ears
    pygame.draw.polygon(surface, TIGER_BODY, [(x + 2, y + cell_size - 8), (x - 2, y + 4), (x + 10, y + cell_size - 10)])
    pygame.draw.polygon(surface, TIGER_BODY, [(x + 18, y + cell_size - 8), (x + 22, y + 4), (x + 10, y + cell_size - 10)])
    
    # Eyes
    pygame.draw.circle(surface, TIGER_EYE, (x + 6, y + cell_size - 2), 3)
    pygame.draw.circle(surface, TIGER_EYE, (x + 14, y + cell_size - 2), 3)
    pygame.draw.circle(surface, BLACK, (x + 6, y + cell_size - 2), 1)
    pygame.draw.circle(surface, BLACK, (x + 14, y + cell_size - 2), 1)
    
    # Nose
    pygame.draw.polygon(surface, (200, 100, 100), [(x + 10, y + cell_size + 2), (x + 7, y + cell_size + 6), (x + 13, y + cell_size + 6)])
    
    # Tail
    tail_x = x + cell_size * 3 - 8
    pygame.draw.arc(surface, TIGER_BODY, (tail_x, y + cell_size - 8, 16, 20), -1.5, 1.5, 4)


def draw_lion(surface, x, y, cell_size):
    """Draw a lion spanning 6 cells (3x2)."""
    # Body
    pygame.draw.ellipse(surface, LION_BODY, (x + cell_size, y + 4, cell_size * 2 - 4, cell_size * 2 - 8))
    pygame.draw.ellipse(surface, LION_BELLY, (x + cell_size + 10, y + cell_size, cell_size - 10, cell_size - 8))
    
    # Mane (covers head area)
    pygame.draw.circle(surface, LION_MANE, (x + cell_size // 2 + 4, y + cell_size), 16)
    
    # Head
    pygame.draw.circle(surface, LION_BODY, (x + cell_size // 2 + 4, y + cell_size), 10)
    
    # Ears
    pygame.draw.circle(surface, LION_MANE, (x + 2, y + cell_size - 10), 6)
    pygame.draw.circle(surface, LION_MANE, (x + cell_size - 2, y + cell_size - 10), 6)
    
    # Eyes
    pygame.draw.circle(surface, LION_EYE, (x + 8, y + cell_size - 2), 3)
    pygame.draw.circle(surface, LION_EYE, (x + cell_size - 4, y + cell_size - 2), 3)
    pygame.draw.circle(surface, BLACK, (x + 8, y + cell_size - 2), 1)
    pygame.draw.circle(surface, BLACK, (x + cell_size - 4, y + cell_size - 2), 1)
    
    # Nose
    pygame.draw.circle(surface, (60, 40, 30), (x + cell_size // 2 + 4, y + cell_size + 4), 3)
    
    # Tail with tuft
    tail_x = x + cell_size * 3 - 10
    pygame.draw.line(surface, LION_BODY, (tail_x, y + cell_size), (tail_x + 12, y + 4), 3)
    pygame.draw.circle(surface, LION_MANE, (tail_x + 12, y + 4), 5)


def draw_bear(surface, x, y, cell_size):
    """Draw a bear spanning 6 cells (2x3)."""
    # Body (main bulk)
    pygame.draw.ellipse(surface, BEAR_BODY, (x + 2, y + cell_size // 2, cell_size * 2 - 4, cell_size * 2))
    pygame.draw.ellipse(surface, BEAR_BELLY, (x + cell_size // 2, y + cell_size, cell_size, cell_size))
    
    # Head (top)
    pygame.draw.circle(surface, BEAR_BODY, (x + cell_size, y + cell_size // 2), 12)
    
    # Ears
    pygame.draw.circle(surface, BEAR_BODY, (x + 6, y + 4), 6)
    pygame.draw.circle(surface, BEAR_BODY, (x + cell_size * 2 - 6, y + 4), 6)
    pygame.draw.circle(surface, BEAR_BELLY, (x + 6, y + 4), 3)
    pygame.draw.circle(surface, BEAR_BELLY, (x + cell_size * 2 - 6, y + 4), 3)
    
    # Snout
    pygame.draw.ellipse(surface, BEAR_SNOUT, (x + cell_size - 6, y + cell_size // 2 + 2, 12, 10))
    pygame.draw.circle(surface, BLACK, (x + cell_size, y + cell_size // 2 + 4), 3)
    
    # Eyes
    pygame.draw.circle(surface, BEAR_EYE, (x + cell_size - 5, y + cell_size // 2 - 4), 3)
    pygame.draw.circle(surface, BEAR_EYE, (x + cell_size + 5, y + cell_size // 2 - 4), 3)
    
    # Legs (bottom row)
    leg_y = y + cell_size * 2
    pygame.draw.ellipse(surface, BEAR_BODY, (x + 2, leg_y, cell_size - 4, cell_size - 2))
    pygame.draw.ellipse(surface, BEAR_BODY, (x + cell_size + 2, leg_y, cell_size - 4, cell_size - 2))


def draw_crocodile(surface, x, y, cell_size):
    """Draw a crocodile spanning 6 cells horizontally."""
    center_y = y + cell_size // 2
    
    # Body (long)
    pygame.draw.ellipse(surface, CROCODILE_BODY, (x + cell_size, y + 2, cell_size * 4, cell_size - 4))
    pygame.draw.ellipse(surface, CROCODILE_BELLY, (x + cell_size + cell_size // 2, y + 5, cell_size * 3, cell_size - 10))
    
    # Head (leftmost cells)
    pygame.draw.ellipse(surface, CROCODILE_BODY, (x, y + 3, cell_size + 10, cell_size - 6))
    
    # Snout/jaw
    pygame.draw.polygon(surface, CROCODILE_BODY, [
        (x + cell_size, center_y - 3),
        (x + cell_size, center_y + 3),
        (x - 4, center_y)
    ])
    
    # Eyes
    pygame.draw.circle(surface, CROCODILE_EYE, (x + cell_size - 6, y + 5), 4)
    pygame.draw.circle(surface, BLACK, (x + cell_size - 6, y + 5), 2)
    
    # Teeth hint
    for i in range(4):
        pygame.draw.line(surface, WHITE, (x + 2 + i*4, center_y - 1), (x + 2 + i*4, center_y + 1), 1)
    
    # Scales/ridges
    for i in range(8):
        scale_x = x + cell_size + 10 + i * 8
        pygame.draw.polygon(surface, CROCODILE_SCALES, [
            (scale_x, y + 2), (scale_x - 3, y + 6), (scale_x + 3, y + 6)
        ])
    
    # Tail (rightmost)
    tail_x = x + cell_size * 5
    pygame.draw.polygon(surface, CROCODILE_BODY, [
        (tail_x, center_y - 4),
        (tail_x, center_y + 4),
        (tail_x + cell_size - 2, center_y)
    ])
    
    # Legs
    pygame.draw.ellipse(surface, CROCODILE_BODY, (x + cell_size + 4, y + cell_size - 6, 8, 6))
    pygame.draw.ellipse(surface, CROCODILE_BODY, (x + cell_size * 3, y + cell_size - 6, 8, 6))


def draw_hippo(surface, x, y, cell_size):
    """Draw a hippo spanning 8 cells (4x2)."""
    # Massive body
    pygame.draw.ellipse(surface, HIPPO_BODY, (x + cell_size // 2, y + 2, cell_size * 3, cell_size * 2 - 4))
    pygame.draw.ellipse(surface, HIPPO_BELLY, (x + cell_size, y + cell_size, cell_size * 2, cell_size - 6))
    
    # Head (leftmost)
    pygame.draw.ellipse(surface, HIPPO_BODY, (x, y + cell_size // 2, cell_size + 6, cell_size))
    
    # Nostrils/mouth area
    pygame.draw.ellipse(surface, HIPPO_MOUTH, (x - 2, y + cell_size - 4, cell_size // 2 + 4, cell_size // 2 + 4))
    pygame.draw.circle(surface, (100, 80, 90), (x + 4, y + cell_size + 2), 2)
    pygame.draw.circle(surface, (100, 80, 90), (x + 12, y + cell_size + 2), 2)
    
    # Eyes (small, on top of head)
    pygame.draw.circle(surface, HIPPO_EYE, (x + 8, y + cell_size // 2 + 2), 3)
    pygame.draw.circle(surface, HIPPO_EYE, (x + cell_size - 2, y + cell_size // 2 + 2), 3)
    
    # Ears
    pygame.draw.ellipse(surface, HIPPO_BODY, (x + 4, y + cell_size // 2 - 6, 6, 8))
    pygame.draw.ellipse(surface, HIPPO_BODY, (x + cell_size - 4, y + cell_size // 2 - 6, 6, 8))
    
    # Tail
    tail_x = x + cell_size * 3 + cell_size // 2
    pygame.draw.line(surface, HIPPO_BODY, (tail_x, y + cell_size), (tail_x + 10, y + cell_size - 8), 3)
    
    # Stubby legs (bottom row)
    for i in range(4):
        leg_x = x + cell_size // 2 + i * (cell_size - 2)
        pygame.draw.rect(surface, HIPPO_BODY, (leg_x, y + cell_size + cell_size // 2, cell_size // 2, cell_size // 2))


def draw_elephant(surface, x, y, cell_size):
    """Draw an elephant spanning 8 cells (2x4)."""
    center_x = x + cell_size
    
    # Body (massive, spans middle cells)
    pygame.draw.ellipse(surface, ELEPHANT_BODY, (x + 2, y + cell_size // 2, cell_size * 2 - 4, cell_size * 2 + cell_size // 2))
    
    # Head (top)
    pygame.draw.circle(surface, ELEPHANT_BODY, (center_x, y + cell_size // 2), 14)
    
    # Ears (large, distinctive)
    pygame.draw.ellipse(surface, ELEPHANT_EAR, (x - 6, y + 2, 16, cell_size))
    pygame.draw.ellipse(surface, ELEPHANT_EAR, (x + cell_size * 2 - 10, y + 2, 16, cell_size))
    
    # Inner ear
    pygame.draw.ellipse(surface, (180, 160, 170), (x - 2, y + 6, 10, cell_size - 10))
    pygame.draw.ellipse(surface, (180, 160, 170), (x + cell_size * 2 - 6, y + 6, 10, cell_size - 10))
    
    # Eyes
    pygame.draw.circle(surface, ELEPHANT_EYE, (center_x - 6, y + cell_size // 2 - 2), 3)
    pygame.draw.circle(surface, ELEPHANT_EYE, (center_x + 6, y + cell_size // 2 - 2), 3)
    
    # Trunk (extends down)
    trunk_points = [
        (center_x - 4, y + cell_size // 2 + 6),
        (center_x + 4, y + cell_size // 2 + 6),
        (center_x + 6, y + cell_size * 2),
        (center_x + 2, y + cell_size * 2 + 10),
        (center_x - 2, y + cell_size * 2 + 10),
        (center_x - 6, y + cell_size * 2),
    ]
    pygame.draw.polygon(surface, ELEPHANT_BODY, trunk_points)
    
    # Tusks
    pygame.draw.polygon(surface, ELEPHANT_TUSK, [
        (center_x - 8, y + cell_size // 2 + 8),
        (center_x - 12, y + cell_size + 10),
        (center_x - 6, y + cell_size + 8)
    ])
    pygame.draw.polygon(surface, ELEPHANT_TUSK, [
        (center_x + 8, y + cell_size // 2 + 8),
        (center_x + 12, y + cell_size + 10),
        (center_x + 6, y + cell_size + 8)
    ])
    
    # Legs (bottom 2 cells)
    leg_y = y + cell_size * 3
    pygame.draw.rect(surface, ELEPHANT_BODY, (x + 2, leg_y - cell_size // 2, cell_size // 2 + 2, cell_size + cell_size // 2))
    pygame.draw.rect(surface, ELEPHANT_BODY, (x + cell_size - 2, leg_y - cell_size // 2, cell_size // 2 + 2, cell_size + cell_size // 2))
    
    # Tail
    pygame.draw.line(surface, ELEPHANT_BODY, (center_x, y + cell_size * 2 + cell_size // 2), 
                    (center_x + 8, y + cell_size * 3 + 4), 2)


def draw_health_bar(surface, x, y, width, height, current_health, max_health):
    """
    Draw a health bar for multi-cell animals.
    
    Args:
        surface: Pygame surface
        x, y: Top-left position
        width, height: Bar dimensions
        current_health: Current health value
        max_health: Maximum health value
    """
    # Background
    bg_rect = pygame.Rect(x, y, width, height)
    pygame.draw.rect(surface, (40, 40, 40), bg_rect)
    
    # Health fill
    if max_health > 0:
        fill_width = int((current_health / max_health) * (width - 2))
        if fill_width > 0:
            health_color = get_health_color(current_health, max_health)
            fill_rect = pygame.Rect(x + 1, y + 1, fill_width, height - 2)
            pygame.draw.rect(surface, health_color, fill_rect)
    
    # Border
    pygame.draw.rect(surface, (100, 100, 100), bg_rect, 1)


def draw_multi_cell_animal(surface, anchor_x, anchor_y, cell_size, animal_type, 
                           current_health, max_health, play_offset=(0, 0)):
    """
    Draw a multi-cell animal with health bar.
    
    Args:
        surface: Pygame surface
        anchor_x, anchor_y: Grid position of anchor cell
        cell_size: Size of each cell
        animal_type: Type of animal
        current_health: Current health
        max_health: Maximum health
        play_offset: (x, y) offset for play area
    """
    from .assets import ANIMAL_SIZES
    
    # Calculate pixel position
    px = anchor_x * cell_size + play_offset[0]
    py = anchor_y * cell_size + play_offset[1]
    
    # Draw the animal
    draw_animal(surface, px, py, cell_size, animal_type)
    
    # Draw health bar above the animal if it has more than 1 health
    if max_health > 1:
        # Calculate health bar position (above the animal)
        cells = ANIMAL_SIZES.get(animal_type, [(0, 0)])
        
        # Find bounding box
        min_x = min(c[0] for c in cells)
        max_x = max(c[0] for c in cells)
        min_y = min(c[1] for c in cells)
        
        # Health bar centered above animal
        bar_width = (max_x - min_x + 1) * cell_size - 4
        bar_x = px + min_x * cell_size + 2
        bar_y = py + min_y * cell_size - 8
        
        draw_health_bar(surface, bar_x, bar_y, bar_width, 6, current_health, max_health)


# ============== Wall/Barrier Drawing Functions ==============

def draw_wall(surface, x, y, cell_size):
    """
    Draw a single wall/barrier cell with brick texture.
    
    Args:
        surface: Pygame surface to draw on
        x: X pixel position
        y: Y pixel position
        cell_size: Size of each cell
    """
    # Base wall color
    wall_rect = pygame.Rect(x, y, cell_size, cell_size)
    pygame.draw.rect(surface, WALL_PRIMARY, wall_rect)
    
    # Draw brick pattern
    brick_height = cell_size // 3
    brick_width = cell_size // 2
    
    for row in range(3):
        offset = (row % 2) * (brick_width // 2)
        brick_y = y + row * brick_height
        
        for col in range(-1, 3):
            brick_x = x + col * brick_width + offset
            
            # Brick rectangle (clipped to cell)
            if brick_x < x:
                bw = brick_width - (x - brick_x)
                bx = x
            else:
                bw = brick_width
                bx = brick_x
            
            if bx + bw > x + cell_size:
                bw = x + cell_size - bx
            
            if bw > 0 and bx >= x:
                # Draw brick
                brick_rect = pygame.Rect(bx + 1, brick_y + 1, bw - 2, brick_height - 2)
                if brick_rect.width > 0 and brick_rect.height > 0:
                    pygame.draw.rect(surface, WALL_SECONDARY, brick_rect)
                    
                    # Highlight on top edge
                    pygame.draw.line(
                        surface, WALL_HIGHLIGHT,
                        (brick_rect.left, brick_rect.top),
                        (brick_rect.right - 1, brick_rect.top)
                    )
                    
                    # Shadow on bottom edge
                    pygame.draw.line(
                        surface, WALL_SHADOW,
                        (brick_rect.left, brick_rect.bottom - 1),
                        (brick_rect.right - 1, brick_rect.bottom - 1)
                    )
    
    # Outer border
    pygame.draw.rect(surface, WALL_SHADOW, wall_rect, 1)


def draw_walls(surface, walls, cell_size):
    """
    Draw all walls from a set of positions.
    
    Args:
        surface: Pygame surface to draw on
        walls: Set of (x, y) grid positions
        cell_size: Size of each cell
    """
    for wall_x, wall_y in walls:
        draw_wall(surface, wall_x * cell_size, wall_y * cell_size, cell_size)


# ============== UI Drawing Functions ==============

def draw_score(surface, score, font, position=(10, 10)):
    """Draw the current score."""
    score_text = font.render(f"Score: {score}", True, SCORE_COLOR)
    surface.blit(score_text, position)


def draw_animal_indicator(surface, animal_type, score_value, font, position=(10, 40)):
    """
    Draw indicator showing what animal the food is and its point value.
    
    Args:
        surface: Pygame surface to draw on
        animal_type: Type of animal
        score_value: Actual score value (with multipliers applied)
        font: Font to use
        position: (x, y) position to draw at
    """
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
    text = font.render(f"Prey: {name} (+{score_value})", True, WHITE)
    surface.blit(text, position)


def draw_game_over(surface, score, font_large, font_small, window_size, play_area_rect=None):
    """Draw the game over overlay."""
    width, height = window_size
    
    # If play area is specified, center on play area
    if play_area_rect:
        center_x = play_area_rect[0] + play_area_rect[2] // 2
        center_y = play_area_rect[1] + play_area_rect[3] // 2
    else:
        center_x = width // 2
        center_y = height // 2
    
    # Semi-transparent overlay
    overlay = pygame.Surface((width, height))
    overlay.set_alpha(200)
    overlay.fill(OVERLAY_COLOR)
    surface.blit(overlay, (0, 0))
    
    # Game over text
    game_over_text = font_large.render("GAME OVER", True, GAME_OVER_COLOR)
    text_rect = game_over_text.get_rect(center=(center_x, center_y - 40))
    surface.blit(game_over_text, text_rect)
    
    # Final score
    final_score_text = font_small.render(f"Final Score: {score}", True, WHITE)
    score_rect = final_score_text.get_rect(center=(center_x, center_y + 10))
    surface.blit(final_score_text, score_rect)
    
    # Instructions
    instruction_text = font_small.render("Press SPACE to retry or ESC for menu", True, WHITE)
    instruction_rect = instruction_text.get_rect(center=(center_x, center_y + 50))
    surface.blit(instruction_text, instruction_rect)


# ============== HUD Drawing Functions ==============

def draw_hud_top(surface, fonts, player_name, score, difficulty, sound_enabled, 
                 play_area_width, hud_height):
    """
    Draw the top HUD bar with player info, score, and settings.
    
    Args:
        surface: Pygame surface to draw on
        fonts: Dict with 'small' and 'medium' fonts
        player_name: Name of the player
        score: Current score
        difficulty: Difficulty label string
        sound_enabled: Whether sound is on
        play_area_width: Width of play area
        hud_height: Height of HUD bar
    """
    from .assets import HUD_BG, HUD_BORDER, HUD_TEXT, HUD_LABEL, HUD_VALUE
    
    # Background
    hud_rect = pygame.Rect(0, 0, surface.get_width(), hud_height)
    pygame.draw.rect(surface, HUD_BG, hud_rect)
    pygame.draw.line(surface, HUD_BORDER, (0, hud_height - 1), 
                     (surface.get_width(), hud_height - 1), 2)
    
    padding = 12
    
    # Player name (left) - truncate long names
    name_label = fonts['tiny'].render("Player:", True, HUD_LABEL)
    surface.blit(name_label, (padding, 8))
    display_name = player_name[:12] + ".." if len(player_name) > 14 else player_name
    name_text = fonts['small'].render(display_name, True, HUD_VALUE)
    surface.blit(name_text, (padding, 26))
    
    # Score (center-left)
    score_x = play_area_width // 3
    score_label = fonts['tiny'].render("Score:", True, HUD_LABEL)
    surface.blit(score_label, (score_x, 8))
    score_text = fonts['small'].render(str(score), True, HUD_VALUE)
    surface.blit(score_text, (score_x, 26))
    
    # Difficulty (center-right) - truncate long difficulty text
    diff_x = play_area_width * 2 // 3
    diff_label = fonts['tiny'].render("Mode:", True, HUD_LABEL)
    surface.blit(diff_label, (diff_x, 8))
    # Abbreviate difficulty if too long
    if len(difficulty) > 12:
        difficulty = difficulty[:10] + ".."
    diff_text = fonts['tiny'].render(difficulty, True, HUD_TEXT)
    surface.blit(diff_text, (diff_x, 28))
    
    # Sound indicator (far right of play area)
    sound_status = "ON" if sound_enabled else "OFF"
    sound_text = fonts['tiny'].render(f"[{sound_status}] M", True, HUD_LABEL)
    sound_x = play_area_width - sound_text.get_width() - padding
    surface.blit(sound_text, (sound_x, 20))


def draw_hud_right(surface, fonts, animal_type, animal_score, snake_length,
                   play_area_width, play_area_height, hud_width, hud_top_height,
                   extra_info=None, food_health=None, food_max_health=None):
    """
    Draw the right HUD panel with game info.
    
    Args:
        surface: Pygame surface to draw on
        fonts: Dict with 'small', 'medium', 'tiny' fonts
        animal_type: Current food animal type
        animal_score: Score value for current animal
        snake_length: Current snake length
        play_area_width: Width of play area
        play_area_height: Height of play area
        hud_width: Width of HUD panel
        hud_top_height: Height of top HUD
        extra_info: Optional dict with additional info to display
        food_health: Current health of the food animal
        food_max_health: Maximum health of the food animal
    """
    from .assets import HUD_BG, HUD_BORDER, HUD_TEXT, HUD_LABEL, HUD_VALUE, HUD_WARNING
    
    # Background
    hud_x = play_area_width
    hud_y = hud_top_height
    panel_height = play_area_height
    
    hud_rect = pygame.Rect(hud_x, hud_y, hud_width, panel_height)
    pygame.draw.rect(surface, HUD_BG, hud_rect)
    pygame.draw.line(surface, HUD_BORDER, (hud_x, hud_y), (hud_x, hud_y + panel_height), 2)
    
    padding = 8
    y = hud_y + padding
    
    # Current prey section
    prey_label = fonts['tiny'].render("PREY", True, HUD_LABEL)
    surface.blit(prey_label, (hud_x + padding, y))
    y += 18
    
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
    y += 22
    
    score_text = fonts['tiny'].render(f"+{animal_score} pts", True, HUD_TEXT)
    surface.blit(score_text, (hud_x + padding, y))
    y += 20
    
    # Health bar for multi-hit animals
    if food_max_health is not None and food_max_health > 1:
        health_label = fonts['tiny'].render(f"HP: {food_health}/{food_max_health}", True, HUD_LABEL)
        surface.blit(health_label, (hud_x + padding, y))
        y += 16
        
        # Health bar
        bar_width = hud_width - padding * 2
        draw_health_bar(surface, hud_x + padding, y, bar_width, 8, food_health, food_max_health)
        y += 16
    else:
        y += 8
    
    # Divider
    pygame.draw.line(surface, HUD_BORDER, (hud_x + padding, y), 
                     (hud_x + hud_width - padding, y))
    y += 12
    
    # Snake length
    len_label = fonts['tiny'].render("LENGTH", True, HUD_LABEL)
    surface.blit(len_label, (hud_x + padding, y))
    y += 18
    len_text = fonts['small'].render(str(snake_length), True, HUD_VALUE)
    surface.blit(len_text, (hud_x + padding, y))
    y += 30
    
    # Extra info section (for story mode progress, etc.)
    if extra_info:
        pygame.draw.line(surface, HUD_BORDER, (hud_x + padding, y), 
                         (hud_x + hud_width - padding, y))
        y += 10
        
        if 'level' in extra_info:
            level_label = fonts['tiny'].render("LEVEL", True, HUD_LABEL)
            surface.blit(level_label, (hud_x + padding, y))
            y += 16
            level_text = fonts['small'].render(str(extra_info['level']), True, HUD_VALUE)
            surface.blit(level_text, (hud_x + padding, y))
            y += 25
        
        if 'food_progress' in extra_info:
            food_eaten, food_required = extra_info['food_progress']
            prog_label = fonts['tiny'].render("GOAL", True, HUD_LABEL)
            surface.blit(prog_label, (hud_x + padding, y))
            y += 16
            prog_text = fonts['small'].render(f"{food_eaten}/{food_required}", True, HUD_VALUE)
            surface.blit(prog_text, (hud_x + padding, y))
            y += 22
            
            # Progress bar
            bar_width = hud_width - padding * 2
            bar_height = 10
            pygame.draw.rect(surface, (40, 40, 40), 
                           (hud_x + padding, y, bar_width, bar_height), border_radius=4)
            
            if food_required > 0:
                fill_width = int((food_eaten / food_required) * bar_width)
                if fill_width > 0:
                    pygame.draw.rect(surface, HUD_VALUE, 
                                   (hud_x + padding, y, fill_width, bar_height), border_radius=4)
            
            pygame.draw.rect(surface, HUD_BORDER, 
                           (hud_x + padding, y, bar_width, bar_height), 1, border_radius=4)
            y += 20
        
        if 'multiplier' in extra_info:
            mult_text = fonts['tiny'].render(f"x{extra_info['multiplier']}", True, HUD_LABEL)
            surface.blit(mult_text, (hud_x + padding, y))
            y += 18
    
    # Controls hint at bottom
    hint_y = hud_y + panel_height - 55
    pygame.draw.line(surface, HUD_BORDER, (hud_x + padding, hint_y), 
                     (hud_x + hud_width - padding, hint_y))
    hint_y += 8
    
    controls = ["Arrows: Move", "M: Sound", "ESC: Menu"]
    for control in controls:
        text = fonts['tiny'].render(control, True, GRAY)
        surface.blit(text, (hud_x + padding, hint_y))
        hint_y += 14


def draw_level_complete(surface, fonts, level, score, bonus, total, play_area_rect):
    """
    Draw level complete overlay for story mode.
    
    Args:
        surface: Pygame surface
        fonts: Dict with font objects
        level: Completed level number
        score: Score earned
        bonus: Completion bonus
        total: Total score
        play_area_rect: (x, y, width, height) of play area
    """
    from .assets import OVERLAY_COLOR, HUD_VALUE
    
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
    text_rect = complete_text.get_rect(center=(center_x, center_y - 60))
    surface.blit(complete_text, text_rect)
    
    # Stats
    level_text = fonts['medium'].render(f"Level {level}", True, WHITE)
    level_rect = level_text.get_rect(center=(center_x, center_y - 10))
    surface.blit(level_text, level_rect)
    
    score_text = fonts['small'].render(f"Level Score: {score}", True, WHITE)
    score_rect = score_text.get_rect(center=(center_x, center_y + 25))
    surface.blit(score_text, score_rect)
    
    bonus_text = fonts['small'].render(f"Completion Bonus: +{bonus}", True, WHITE)
    bonus_rect = bonus_text.get_rect(center=(center_x, center_y + 50))
    surface.blit(bonus_text, bonus_rect)
    
    total_text = fonts['medium'].render(f"Total: {total}", True, HUD_VALUE)
    total_rect = total_text.get_rect(center=(center_x, center_y + 85))
    surface.blit(total_text, total_rect)
    
    # Instructions
    hint_text = fonts['small'].render("Press SPACE for next level or ESC for menu", True, WHITE)
    hint_rect = hint_text.get_rect(center=(center_x, center_y + 130))
    surface.blit(hint_text, hint_rect)


def draw_play_area_border(surface, play_area_rect, border_color=None):
    """
    Draw a border around the play area.
    
    Args:
        surface: Pygame surface
        play_area_rect: (x, y, width, height) of play area
        border_color: Color for border (default: HUD_BORDER)
    """
    from .assets import HUD_BORDER
    
    if border_color is None:
        border_color = HUD_BORDER
    
    x, y, width, height = play_area_rect
    pygame.draw.rect(surface, border_color, (x, y, width, height), 2)
