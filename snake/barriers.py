"""
Barriers module for the Snake Game.
Generates and manages wall/obstacle patterns based on difficulty settings.
"""

import random
from .assets import BARRIER_DENSITIES


class BarrierGenerator:
    """
    Generates barrier patterns based on density settings and map size.
    """
    
    def __init__(self, grid_width, grid_height, barrier_key):
        """
        Initialize the barrier generator.
        
        Args:
            grid_width: Width of the grid in cells
            grid_height: Height of the grid in cells
            barrier_key: Key from BARRIER_DENSITIES dict
        """
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.barrier_key = barrier_key
        self.barrier_config = BARRIER_DENSITIES.get(barrier_key, BARRIER_DENSITIES['none'])
        
        self.walls = set()  # Set of (x, y) tuples for wall positions
    
    def generate(self, snake_start_positions):
        """
        Generate barriers based on the configuration.
        
        Args:
            snake_start_positions: List of (x, y) positions where snake starts
                                   (to avoid placing walls there)
        
        Returns:
            Set of (x, y) tuples representing wall positions
        """
        self.walls = set()
        
        pattern = self.barrier_config['pattern']
        
        if pattern == 'none':
            return self.walls
        elif pattern == 'scattered':
            self._generate_scattered(snake_start_positions)
        elif pattern == 'structured':
            self._generate_structured(snake_start_positions)
        elif pattern == 'maze':
            self._generate_maze(snake_start_positions)
        
        return self.walls
    
    def _generate_scattered(self, snake_positions):
        """Generate randomly scattered small wall segments."""
        num_segments = max(2, self.grid_width * self.grid_height // 80)
        
        safe_zone = self._get_safe_zone(snake_positions)
        
        for _ in range(num_segments):
            self._place_small_wall(safe_zone)
    
    def _generate_structured(self, snake_positions):
        """Generate structured wall patterns with some symmetry."""
        safe_zone = self._get_safe_zone(snake_positions)
        
        # Create corner barriers
        self._place_corner_walls(safe_zone)
        
        # Add some center obstacles
        self._place_center_obstacles(safe_zone)
        
        # Add a few random small walls
        for _ in range(2):
            self._place_small_wall(safe_zone)
    
    def _generate_maze(self, snake_positions):
        """Generate a more maze-like pattern with corridors."""
        safe_zone = self._get_safe_zone(snake_positions)
        
        # Create corner walls (larger)
        self._place_corner_walls(safe_zone, size=4)
        
        # Create center cross or box
        self._place_center_structure(safe_zone)
        
        # Add corridor walls
        self._place_corridor_walls(safe_zone)
        
        # Add scattered walls in remaining space
        for _ in range(3):
            self._place_small_wall(safe_zone)
    
    def _get_safe_zone(self, snake_positions):
        """
        Get a set of positions that should remain clear.
        Includes snake starting area and a buffer around it.
        """
        safe = set()
        
        for pos in snake_positions:
            # Add the position and surrounding cells
            for dx in range(-3, 4):
                for dy in range(-3, 4):
                    safe.add((pos[0] + dx, pos[1] + dy))
        
        # Also keep edges partially clear for spawning food
        for x in range(self.grid_width):
            safe.add((x, 0))
            safe.add((x, self.grid_height - 1))
        for y in range(self.grid_height):
            safe.add((0, y))
            safe.add((self.grid_width - 1, y))
        
        return safe
    
    def _is_valid_wall_position(self, x, y, safe_zone):
        """Check if a position is valid for placing a wall."""
        if x < 1 or x >= self.grid_width - 1:
            return False
        if y < 1 or y >= self.grid_height - 1:
            return False
        if (x, y) in safe_zone:
            return False
        if (x, y) in self.walls:
            return False
        return True
    
    def _place_small_wall(self, safe_zone):
        """Place a small wall segment (2-4 cells)."""
        attempts = 0
        max_attempts = 50
        
        while attempts < max_attempts:
            x = random.randint(2, self.grid_width - 3)
            y = random.randint(2, self.grid_height - 3)
            
            if not self._is_valid_wall_position(x, y, safe_zone):
                attempts += 1
                continue
            
            # Choose orientation and length
            horizontal = random.choice([True, False])
            length = random.randint(2, 4)
            
            # Check if all positions are valid
            valid = True
            positions = []
            
            for i in range(length):
                if horizontal:
                    pos = (x + i, y)
                else:
                    pos = (x, y + i)
                
                if not self._is_valid_wall_position(pos[0], pos[1], safe_zone):
                    valid = False
                    break
                positions.append(pos)
            
            if valid:
                for pos in positions:
                    self.walls.add(pos)
                return
            
            attempts += 1
    
    def _place_corner_walls(self, safe_zone, size=3):
        """Place L-shaped walls in corners."""
        corners = [
            (3, 3, 1, 1),                                           # Top-left
            (self.grid_width - 4 - size, 3, -1, 1),                # Top-right
            (3, self.grid_height - 4 - size, 1, -1),               # Bottom-left
            (self.grid_width - 4 - size, self.grid_height - 4 - size, -1, -1)  # Bottom-right
        ]
        
        for base_x, base_y, dir_x, dir_y in corners:
            # Horizontal part of L
            for i in range(size):
                x = base_x + i * (1 if dir_x > 0 else -1) + (0 if dir_x > 0 else size - 1)
                y = base_y
                if self._is_valid_wall_position(x, y, safe_zone):
                    self.walls.add((x, y))
            
            # Vertical part of L
            for i in range(size):
                x = base_x
                y = base_y + i * (1 if dir_y > 0 else -1) + (0 if dir_y > 0 else size - 1)
                if self._is_valid_wall_position(x, y, safe_zone):
                    self.walls.add((x, y))
    
    def _place_center_obstacles(self, safe_zone):
        """Place obstacles in the center area."""
        center_x = self.grid_width // 2
        center_y = self.grid_height // 2
        
        # Place a small cross or box in center
        offsets = [(-2, 0), (-1, 0), (1, 0), (2, 0), (0, -2), (0, -1), (0, 1), (0, 2)]
        
        for dx, dy in offsets:
            x, y = center_x + dx, center_y + dy
            if self._is_valid_wall_position(x, y, safe_zone):
                self.walls.add((x, y))
    
    def _place_center_structure(self, safe_zone):
        """Place a larger center structure for maze mode."""
        center_x = self.grid_width // 2
        center_y = self.grid_height // 2
        
        # Create a hollow square
        size = min(5, min(self.grid_width, self.grid_height) // 6)
        
        for i in range(-size, size + 1):
            # Top and bottom edges
            for pos in [(center_x + i, center_y - size), (center_x + i, center_y + size)]:
                if self._is_valid_wall_position(pos[0], pos[1], safe_zone):
                    # Leave gaps for passage
                    if abs(i) != size // 2:
                        self.walls.add(pos)
            
            # Left and right edges
            for pos in [(center_x - size, center_y + i), (center_x + size, center_y + i)]:
                if self._is_valid_wall_position(pos[0], pos[1], safe_zone):
                    if abs(i) != size // 2:
                        self.walls.add(pos)
    
    def _place_corridor_walls(self, safe_zone):
        """Place walls that create corridor-like passages."""
        # Horizontal corridors at 1/3 and 2/3 height
        y_positions = [self.grid_height // 3, 2 * self.grid_height // 3]
        
        for y in y_positions:
            # Leave gaps for passage
            gap1 = self.grid_width // 4
            gap2 = 3 * self.grid_width // 4
            
            for x in range(3, self.grid_width - 3):
                if abs(x - gap1) > 2 and abs(x - gap2) > 2:
                    if self._is_valid_wall_position(x, y, safe_zone):
                        if random.random() < 0.6:  # Don't place every cell
                            self.walls.add((x, y))
        
        # Vertical corridors at 1/3 and 2/3 width
        x_positions = [self.grid_width // 3, 2 * self.grid_width // 3]
        
        for x in x_positions:
            gap1 = self.grid_height // 4
            gap2 = 3 * self.grid_height // 4
            
            for y in range(3, self.grid_height - 3):
                if abs(y - gap1) > 2 and abs(y - gap2) > 2:
                    if self._is_valid_wall_position(x, y, safe_zone):
                        if random.random() < 0.5:
                            self.walls.add((x, y))
    
    def is_wall(self, x, y):
        """Check if a position contains a wall."""
        return (x, y) in self.walls
    
    def get_walls(self):
        """Get the set of all wall positions."""
        return self.walls.copy()
