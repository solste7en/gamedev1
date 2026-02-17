"""
Arena module for Brawler game.

Defines the map layout, walls, goals, and collision detection.
"""

import pygame
from .assets import (
    TILE_SIZE, ARENA_WIDTH, ARENA_HEIGHT,
    GOAL_WIDTH, GOAL_DEPTH, BRAWLER_RADIUS, BALL_RADIUS
)


class Arena:
    """
    Represents the Brawl Ball arena.
    
    Manages map layout, walls, goals, and collision detection.
    """
    
    def __init__(self):
        self.width = ARENA_WIDTH
        self.height = ARENA_HEIGHT
        self.tile_size = TILE_SIZE
        
        # World dimensions in pixels
        self.world_width = self.width * TILE_SIZE
        self.world_height = self.height * TILE_SIZE
        
        # Goal areas (must be set before _create_default_layout)
        self.goal_width = GOAL_WIDTH * TILE_SIZE
        self.goal_depth = GOAL_DEPTH * TILE_SIZE
        
        # Initialize walls and goals
        self.walls = []
        self.grass_tiles = set()
        self._create_default_layout()
        
        # Blue goal (left side)
        self.blue_goal = pygame.Rect(
            -self.goal_depth,
            (self.world_height - self.goal_width) // 2,
            self.goal_depth,
            self.goal_width
        )
        
        # Red goal (right side)
        self.red_goal = pygame.Rect(
            self.world_width,
            (self.world_height - self.goal_width) // 2,
            self.goal_depth,
            self.goal_width
        )
        
        # Spawn points
        self.spawn_points = {
            0: [  # Blue team spawns (left side)
                (self.world_width * 0.15, self.world_height * 0.35),
                (self.world_width * 0.15, self.world_height * 0.65),
            ],
            1: [  # Red team spawns (right side)
                (self.world_width * 0.85, self.world_height * 0.35),
                (self.world_width * 0.85, self.world_height * 0.65),
            ]
        }
        
        # Ball spawn point
        self.ball_spawn = (self.world_width // 2, self.world_height // 2)
    
    def _create_default_layout(self):
        """
        Create the default Brawl Ball arena layout.
        """
        # Clear existing walls
        self.walls = []
        
        wall_thickness = TILE_SIZE
        
        # Top wall
        self.walls.append((0, -wall_thickness, self.world_width, wall_thickness))
        
        # Bottom wall
        self.walls.append((0, self.world_height, self.world_width, wall_thickness))
        
        # Left wall (top section, above goal)
        goal_top = (self.world_height - self.goal_width) // 2
        goal_bottom = goal_top + self.goal_width
        self.walls.append((-wall_thickness, 0, wall_thickness, goal_top))
        
        # Left wall (bottom section, below goal)
        self.walls.append((-wall_thickness, goal_bottom, wall_thickness, 
                          self.world_height - goal_bottom))
        
        # Right wall (top section, above goal)
        self.walls.append((self.world_width, 0, wall_thickness, goal_top))
        
        # Right wall (bottom section, below goal)
        self.walls.append((self.world_width, goal_bottom, wall_thickness,
                          self.world_height - goal_bottom))
        
        # Center obstacles (decorative walls near center)
        center_x = self.world_width // 2
        center_y = self.world_height // 2
        
        # Two small walls near center
        obstacle_size = TILE_SIZE * 2
        self.walls.append((center_x - obstacle_size // 2, center_y - TILE_SIZE * 4,
                          obstacle_size, obstacle_size))
        self.walls.append((center_x - obstacle_size // 2, center_y + TILE_SIZE * 2,
                          obstacle_size, obstacle_size))
        
        # Set grass tiles near goals
        for ty in range(self.height):
            for tx in range(3):  # Left grass
                self.grass_tiles.add((tx, ty))
            for tx in range(self.width - 3, self.width):  # Right grass
                self.grass_tiles.add((tx, ty))
    
    def is_grass(self, tile_x, tile_y):
        """
        Check if a tile is grass (near goals).
        """
        return (tile_x, tile_y) in self.grass_tiles
    
    def get_spawn_point(self, team, index):
        """
        Get spawn point for a team member.
        """
        spawns = self.spawn_points.get(team, [])
        if index < len(spawns):
            return spawns[index]
        return self.ball_spawn  # Fallback
    
    def check_wall_collision(self, x, y, radius):
        """
        Check if a circular entity collides with walls.
        Returns (collision, normal_x, normal_y) where normal is the push direction.
        """
        entity_rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
        
        for wall in self.walls:
            wall_rect = pygame.Rect(wall)
            if entity_rect.colliderect(wall_rect):
                # Calculate push direction
                cx = x
                cy = y
                
                # Find closest point on wall to entity center
                closest_x = max(wall_rect.left, min(cx, wall_rect.right))
                closest_y = max(wall_rect.top, min(cy, wall_rect.bottom))
                
                dx = cx - closest_x
                dy = cy - closest_y
                dist = (dx * dx + dy * dy) ** 0.5
                
                if dist < radius:
                    if dist == 0:
                        # Entity center is inside wall
                        dx = cx - wall_rect.centerx
                        dy = cy - wall_rect.centery
                        dist = (dx * dx + dy * dy) ** 0.5
                        if dist == 0:
                            dx, dy = 1, 0
                            dist = 1
                    
                    nx = dx / dist
                    ny = dy / dist
                    return (True, nx, ny)
        
        return (False, 0, 0)
    
    def check_bounds(self, x, y, radius):
        """
        Check if entity is within arena bounds.
        Returns clamped position.
        """
        # Allow some overflow for goal areas
        min_x = radius
        max_x = self.world_width - radius
        min_y = radius
        max_y = self.world_height - radius
        
        # Check if in goal area (allow different bounds)
        in_goal = self._is_in_goal_area(x, y)
        
        if in_goal == 'blue':
            min_x = -self.goal_depth + radius
        elif in_goal == 'red':
            max_x = self.world_width + self.goal_depth - radius
        
        new_x = max(min_x, min(x, max_x))
        new_y = max(min_y, min(y, max_y))
        
        return (new_x, new_y)
    
    def _is_in_goal_area(self, x, y):
        """
        Check if position is in a goal area.
        """
        goal_top = (self.world_height - self.goal_width) // 2
        goal_bottom = goal_top + self.goal_width
        
        if goal_top <= y <= goal_bottom:
            if x < TILE_SIZE:
                return 'blue'
            elif x > self.world_width - TILE_SIZE:
                return 'red'
        
        return None
    
    def check_goal(self, x, y, radius):
        """
        Check if ball has entered a goal.
        Returns 'blue' or 'red' for the team that SCORED (opposite of goal entered).
        Returns None if no goal.
        """
        if self.blue_goal.collidepoint(x, y):
            return 'red'  # Red team scored in blue's goal
        elif self.red_goal.collidepoint(x, y):
            return 'blue'  # Blue team scored in red's goal
        return None
    
    def get_center(self):
        """
        Get center point of arena.
        """
        return (self.world_width // 2, self.world_height // 2)
    
    def point_in_arena(self, x, y):
        """
        Check if a point is within the playable arena.
        """
        return 0 <= x <= self.world_width and 0 <= y <= self.world_height
    
    def get_closest_point_in_bounds(self, x, y):
        """
        Get the closest point inside arena bounds.
        """
        return (
            max(0, min(x, self.world_width)),
            max(0, min(y, self.world_height))
        )
    
    def destroy_wall(self, wall_index):
        """
        Remove a wall (for super abilities that destroy walls).
        """
        if 0 <= wall_index < len(self.walls):
            # Only allow destroying non-boundary walls (index >= 6)
            if wall_index >= 6:
                self.walls.pop(wall_index)
                return True
        return False
    
    def reset_walls(self):
        """
        Reset walls to default layout (after round ends).
        """
        self._create_default_layout()
