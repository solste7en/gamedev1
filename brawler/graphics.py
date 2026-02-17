"""
Graphics module for Brawler game.

Provides isometric rendering functions for arena, characters, and effects.
Uses a Brawl Stars-style angled top-down view.
"""

import pygame
import math
from .assets import *


# ============== Isometric Projection ==============

# Isometric projection constants
ISO_X_SCALE = 1.0
ISO_Y_SCALE = 0.5  # Vertical compression for 3/4 view

def world_to_screen(world_x, world_y, camera_x=0, camera_y=0):
    """
    Convert world coordinates to screen coordinates.
    Uses a simple 3/4 top-down view (not full isometric).
    """
    screen_x = (world_x - camera_x) * ISO_X_SCALE + WINDOW_WIDTH // 2
    screen_y = (world_y - camera_y) * ISO_Y_SCALE + WINDOW_HEIGHT // 2 - HUD_HEIGHT // 2
    return (int(screen_x), int(screen_y))


def screen_to_world(screen_x, screen_y, camera_x=0, camera_y=0):
    """
    Convert screen coordinates back to world coordinates.
    """
    world_x = (screen_x - WINDOW_WIDTH // 2) / ISO_X_SCALE + camera_x
    world_y = (screen_y - WINDOW_HEIGHT // 2 + HUD_HEIGHT // 2) / ISO_Y_SCALE + camera_y
    return (world_x, world_y)


# ============== Arena Drawing ==============

def draw_arena_floor(surface, arena, camera_x=0, camera_y=0):
    """
    Draw the arena floor tiles.
    """
    tile_w = TILE_SIZE
    tile_h = int(TILE_SIZE * ISO_Y_SCALE)
    
    # Calculate visible tile range
    start_x = max(0, int((camera_x - WINDOW_WIDTH // 2) / TILE_SIZE) - 1)
    end_x = min(arena.width, int((camera_x + WINDOW_WIDTH // 2) / TILE_SIZE) + 2)
    start_y = max(0, int((camera_y - WINDOW_HEIGHT) / TILE_SIZE) - 1)
    end_y = min(arena.height, int((camera_y + WINDOW_HEIGHT) / TILE_SIZE) + 2)
    
    for ty in range(start_y, end_y):
        for tx in range(start_x, end_x):
            world_x = tx * TILE_SIZE
            world_y = ty * TILE_SIZE
            sx, sy = world_to_screen(world_x, world_y, camera_x, camera_y)
            
            # Checkerboard pattern
            if (tx + ty) % 2 == 0:
                color = ARENA_FLOOR
            else:
                color = ARENA_FLOOR_ALT
            
            # Check for grass zones (near goals)
            if arena.is_grass(tx, ty):
                color = ARENA_GRASS if (tx + ty) % 2 == 0 else ARENA_GRASS_ALT
            
            # Draw tile
            rect = pygame.Rect(sx, sy, tile_w + 1, tile_h + 1)
            pygame.draw.rect(surface, color, rect)


def draw_arena_lines(surface, arena, camera_x=0, camera_y=0):
    """
    Draw field markings (center line, goal areas, etc.).
    """
    # Center line
    center_x = arena.width * TILE_SIZE // 2
    top_y = 0
    bottom_y = arena.height * TILE_SIZE
    
    start = world_to_screen(center_x, top_y, camera_x, camera_y)
    end = world_to_screen(center_x, bottom_y, camera_x, camera_y)
    pygame.draw.line(surface, ARENA_LINE, start, end, 3)
    
    # Center circle
    cx, cy = world_to_screen(center_x, arena.height * TILE_SIZE // 2, camera_x, camera_y)
    radius_x = int(TILE_SIZE * 3)
    radius_y = int(TILE_SIZE * 3 * ISO_Y_SCALE)
    pygame.draw.ellipse(surface, ARENA_LINE, 
                       (cx - radius_x, cy - radius_y, radius_x * 2, radius_y * 2), 3)


def draw_walls(surface, arena, camera_x=0, camera_y=0):
    """
    Draw arena walls with 3D effect.
    """
    wall_height = int(TILE_SIZE * 0.8)
    
    for wall in arena.walls:
        wx, wy, ww, wh = wall
        
        # Convert to screen coordinates
        sx, sy = world_to_screen(wx, wy, camera_x, camera_y)
        sw = int(ww * ISO_X_SCALE)
        sh = int(wh * ISO_Y_SCALE)
        
        # Draw wall shadow
        shadow_offset = 4
        shadow_rect = pygame.Rect(sx + shadow_offset, sy + shadow_offset, sw, sh)
        pygame.draw.rect(surface, (0, 0, 0, 50), shadow_rect)
        
        # Draw wall top
        wall_rect = pygame.Rect(sx, sy - wall_height // 2, sw, sh + wall_height // 2)
        pygame.draw.rect(surface, ARENA_WALL_TOP, wall_rect)
        
        # Draw wall front face
        front_rect = pygame.Rect(sx, sy + sh - wall_height // 2, sw, wall_height // 2)
        pygame.draw.rect(surface, ARENA_WALL, front_rect)
        
        # Outline
        pygame.draw.rect(surface, ARENA_WALL_DARK, wall_rect, 2)


def draw_goals(surface, arena, camera_x=0, camera_y=0):
    """
    Draw goal areas for both teams.
    """
    goal_depth = GOAL_DEPTH * TILE_SIZE
    goal_width = GOAL_WIDTH * TILE_SIZE
    
    # Blue goal (left side)
    blue_x = 0
    blue_y = (arena.height * TILE_SIZE - goal_width) // 2
    bx, by = world_to_screen(blue_x, blue_y, camera_x, camera_y)
    bw = int(goal_depth * ISO_X_SCALE)
    bh = int(goal_width * ISO_Y_SCALE)
    
    # Goal background (net)
    pygame.draw.rect(surface, GOAL_BLUE_NET, (bx - bw, by, bw, bh))
    # Goal frame
    pygame.draw.rect(surface, GOAL_BLUE, (bx - bw, by, bw, bh), 4)
    # Posts
    pygame.draw.line(surface, GOAL_BLUE, (bx, by), (bx, by + bh), 6)
    
    # Red goal (right side)
    red_x = arena.width * TILE_SIZE
    red_y = (arena.height * TILE_SIZE - goal_width) // 2
    rx, ry = world_to_screen(red_x, red_y, camera_x, camera_y)
    rw = int(goal_depth * ISO_X_SCALE)
    rh = int(goal_width * ISO_Y_SCALE)
    
    # Goal background (net)
    pygame.draw.rect(surface, GOAL_RED_NET, (rx, ry, rw, rh))
    # Goal frame
    pygame.draw.rect(surface, GOAL_RED, (rx, ry, rw, rh), 4)
    # Posts
    pygame.draw.line(surface, GOAL_RED, (rx, ry), (rx, ry + rh), 6)


# ============== Character Drawing ==============

def draw_brawler(surface, brawler, camera_x=0, camera_y=0):
    """
    Draw a brawler character with team indicator and effects.
    """
    sx, sy = world_to_screen(brawler.x, brawler.y, camera_x, camera_y)
    
    colors = brawler.colors
    team_color, team_light, team_dark = get_team_colors(brawler.team)
    
    # Draw shadow
    shadow_rx = int(BRAWLER_RADIUS * 1.2)
    shadow_ry = int(BRAWLER_RADIUS * 0.6)
    shadow_surface = pygame.Surface((shadow_rx * 2, shadow_ry * 2), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surface, (0, 0, 0, 60), (0, 0, shadow_rx * 2, shadow_ry * 2))
    surface.blit(shadow_surface, (sx - shadow_rx, sy - shadow_ry // 2))
    
    # Body offset for jumping
    body_offset = 0
    if hasattr(brawler, 'jump_height'):
        body_offset = -brawler.jump_height
    
    body_y = sy + int(body_offset * ISO_Y_SCALE)
    
    # Draw team ring under character
    ring_rx = int(BRAWLER_RADIUS * 1.1)
    ring_ry = int(BRAWLER_RADIUS * 0.55)
    pygame.draw.ellipse(surface, team_color, 
                       (sx - ring_rx, sy - ring_ry // 2, ring_rx * 2, ring_ry * 2), 3)
    
    # Draw body (simple capsule shape)
    body_width = int(BRAWLER_RADIUS * 1.6)
    body_height = int(BRAWLER_HEIGHT * ISO_Y_SCALE)
    
    # Body fill
    body_rect = pygame.Rect(sx - body_width // 2, body_y - body_height, body_width, body_height)
    pygame.draw.ellipse(surface, colors['primary'], body_rect)
    
    # Draw head
    head_radius = int(BRAWLER_RADIUS * 0.7)
    head_y = body_y - body_height + head_radius // 2
    pygame.draw.circle(surface, colors['skin'], (sx, head_y), head_radius)
    
    # Draw hair
    hair_rect = pygame.Rect(sx - head_radius, head_y - head_radius, head_radius * 2, head_radius)
    pygame.draw.ellipse(surface, colors['hair'], hair_rect)
    
    # Draw facing direction indicator
    if hasattr(brawler, 'facing_angle'):
        indicator_dist = BRAWLER_RADIUS + 5
        ind_x = sx + int(math.cos(brawler.facing_angle) * indicator_dist)
        ind_y = body_y - body_height // 2 + int(math.sin(brawler.facing_angle) * indicator_dist * ISO_Y_SCALE)
        pygame.draw.circle(surface, team_light, (ind_x, ind_y), 4)
    
    # Draw name tag
    if hasattr(brawler, 'name'):
        font = pygame.font.Font(None, 18)
        name_text = font.render(brawler.name, True, WHITE)
        name_rect = name_text.get_rect(center=(sx, body_y - body_height - 15))
        surface.blit(name_text, name_rect)


def draw_brawler_health_bar(surface, brawler, camera_x=0, camera_y=0):
    """
    Draw health bar above brawler.
    """
    sx, sy = world_to_screen(brawler.x, brawler.y, camera_x, camera_y)
    
    bar_width = 40
    bar_height = 6
    bar_y = sy - int(BRAWLER_HEIGHT * ISO_Y_SCALE) - 25
    
    # Background
    bg_rect = pygame.Rect(sx - bar_width // 2 - 1, bar_y - 1, bar_width + 2, bar_height + 2)
    pygame.draw.rect(surface, HEALTH_BAR_BG, bg_rect)
    
    # Health fill
    health_percent = brawler.health / brawler.max_health
    fill_width = int(bar_width * health_percent)
    if fill_width > 0:
        fill_color = get_health_color(health_percent)
        fill_rect = pygame.Rect(sx - bar_width // 2, bar_y, fill_width, bar_height)
        pygame.draw.rect(surface, fill_color, fill_rect)
    
    # Border
    pygame.draw.rect(surface, WHITE, bg_rect, 1)


# ============== Projectile Drawing ==============

def draw_bullet(surface, projectile, camera_x=0, camera_y=0):
    """
    Draw a bullet projectile.
    """
    sx, sy = world_to_screen(projectile.x, projectile.y, camera_x, camera_y)
    
    # Bullet trail
    trail_length = 15
    trail_x = sx - int(math.cos(projectile.angle) * trail_length)
    trail_y = sy - int(math.sin(projectile.angle) * trail_length * ISO_Y_SCALE)
    
    pygame.draw.line(surface, projectile.color, (trail_x, trail_y), (sx, sy), 3)
    pygame.draw.circle(surface, projectile.color, (sx, sy), projectile.radius)
    pygame.draw.circle(surface, WHITE, (sx, sy), projectile.radius - 2)


def draw_pellet(surface, projectile, camera_x=0, camera_y=0):
    """
    Draw a shotgun pellet.
    """
    sx, sy = world_to_screen(projectile.x, projectile.y, camera_x, camera_y)
    pygame.draw.circle(surface, projectile.color, (sx, sy), projectile.radius)
    pygame.draw.circle(surface, (255, 255, 200), (sx - 1, sy - 1), 2)


def draw_sniper_bullet(surface, projectile, camera_x=0, camera_y=0):
    """
    Draw Piper's sniper bullet with trail.
    """
    sx, sy = world_to_screen(projectile.x, projectile.y, camera_x, camera_y)
    
    # Long trail
    trail_length = 30
    trail_x = sx - int(math.cos(projectile.angle) * trail_length)
    trail_y = sy - int(math.sin(projectile.angle) * trail_length * ISO_Y_SCALE)
    
    # Draw gradient trail
    for i in range(5):
        t = i / 5
        tx = int(lerp(trail_x, sx, t))
        ty = int(lerp(trail_y, sy, t))
        alpha = int(255 * t)
        pygame.draw.circle(surface, projectile.color, (tx, ty), int(projectile.radius * t) + 2)
    
    pygame.draw.circle(surface, projectile.color, (sx, sy), projectile.radius)
    pygame.draw.circle(surface, WHITE, (sx, sy), projectile.radius - 3)


def draw_melee_arc(surface, brawler, camera_x=0, camera_y=0):
    """
    Draw Edgar's melee attack arc.
    """
    sx, sy = world_to_screen(brawler.x, brawler.y, camera_x, camera_y)
    
    if not hasattr(brawler, 'attack_timer') or brawler.attack_timer <= 0:
        return
    
    # Draw arc effect
    arc_radius = int(RANGE_MELEE * ISO_X_SCALE)
    arc_start = brawler.facing_angle - math.radians(MELEE_ARC_ANGLE / 2)
    arc_end = brawler.facing_angle + math.radians(MELEE_ARC_ANGLE / 2)
    
    # Draw slash lines
    alpha = int(255 * brawler.attack_timer / 0.2)
    for i in range(3):
        angle = arc_start + (arc_end - arc_start) * i / 2
        end_x = sx + int(math.cos(angle) * arc_radius)
        end_y = sy + int(math.sin(angle) * arc_radius * ISO_Y_SCALE)
        pygame.draw.line(surface, EDGAR_SLASH, (sx, sy), (end_x, end_y), 4)


# ============== Ball Drawing ==============

def draw_ball(surface, ball, camera_x=0, camera_y=0):
    """
    Draw the soccer ball.
    """
    sx, sy = world_to_screen(ball.x, ball.y, camera_x, camera_y)
    
    # Ball offset for bouncing effect
    bounce_offset = 0
    if hasattr(ball, 'bounce_height'):
        bounce_offset = -ball.bounce_height
    
    ball_y = sy + int(bounce_offset * ISO_Y_SCALE)
    
    # Draw shadow
    shadow_rx = int(BALL_RADIUS * 1.2)
    shadow_ry = int(BALL_RADIUS * 0.6)
    shadow_surface = pygame.Surface((shadow_rx * 2, shadow_ry * 2), pygame.SRCALPHA)
    shadow_alpha = max(30, 80 - int(abs(bounce_offset)))
    pygame.draw.ellipse(shadow_surface, (0, 0, 0, shadow_alpha), 
                       (0, 0, shadow_rx * 2, shadow_ry * 2))
    surface.blit(shadow_surface, (sx - shadow_rx, sy - shadow_ry // 2))
    
    # Draw ball
    pygame.draw.circle(surface, BALL_COLOR, (sx, ball_y), BALL_RADIUS)
    
    # Draw pattern (pentagon pattern simplified)
    pattern_offsets = [
        (0, 0),
        (-8, -5), (8, -5),
        (-6, 6), (6, 6)
    ]
    for ox, oy in pattern_offsets:
        px = sx + ox
        py = ball_y + int(oy * 0.7)
        pygame.draw.circle(surface, BALL_PATTERN, (px, py), 4)
    
    # Outline
    pygame.draw.circle(surface, BALL_OUTLINE, (sx, ball_y), BALL_RADIUS, 2)


# ============== Effect Drawing ==============

def draw_spawn_effect(surface, x, y, progress, team, camera_x=0, camera_y=0):
    """
    Draw respawn animation effect.
    """
    sx, sy = world_to_screen(x, y, camera_x, camera_y)
    team_color = TEAM_BLUE if team == 0 else TEAM_RED
    
    # Expanding rings
    for i in range(3):
        ring_progress = (progress + i * 0.3) % 1.0
        ring_radius = int(BRAWLER_RADIUS * 2 * ring_progress)
        ring_alpha = int(255 * (1 - ring_progress))
        
        ring_surface = pygame.Surface((ring_radius * 2, ring_radius), pygame.SRCALPHA)
        pygame.draw.ellipse(ring_surface, (*team_color, ring_alpha),
                           (0, 0, ring_radius * 2, ring_radius), 3)
        surface.blit(ring_surface, (sx - ring_radius, sy - ring_radius // 2))


def draw_goal_effect(surface, scoring_team, progress):
    """
    Draw goal celebration effect.
    """
    team_color = TEAM_BLUE if scoring_team == 0 else TEAM_RED
    
    # Flash effect
    if progress < 0.5:
        alpha = int(100 * (1 - progress * 2))
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*team_color, alpha))
        surface.blit(overlay, (0, 0))
    
    # Goal text
    font = pygame.font.Font(None, 120)
    text = font.render("GOAL!", True, team_color)
    text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
    
    # Text shadow
    shadow = font.render("GOAL!", True, BLACK)
    shadow_rect = shadow.get_rect(center=(WINDOW_WIDTH // 2 + 4, WINDOW_HEIGHT // 2 - 46))
    
    # Scale effect
    scale = 1.0 + 0.3 * math.sin(progress * math.pi * 4)
    
    surface.blit(shadow, shadow_rect)
    surface.blit(text, text_rect)


def draw_super_ready_effect(surface, brawler, camera_x=0, camera_y=0):
    """
    Draw effect when super is ready.
    """
    if brawler.super_charge < SUPER_CHARGE_MAX:
        return
    
    sx, sy = world_to_screen(brawler.x, brawler.y, camera_x, camera_y)
    
    # Pulsing glow
    pulse = abs(math.sin(pygame.time.get_ticks() * 0.005))
    glow_radius = int(BRAWLER_RADIUS * 1.5 + pulse * 10)
    
    glow_surface = pygame.Surface((glow_radius * 2, glow_radius), pygame.SRCALPHA)
    pygame.draw.ellipse(glow_surface, (*SUPER_BAR_READY, int(100 * pulse)),
                       (0, 0, glow_radius * 2, glow_radius))
    surface.blit(glow_surface, (sx - glow_radius, sy - glow_radius // 2))
