"""
Game manager for snake multiplayer game logic
"""

import asyncio
import random
import time
import math
from collections import deque
from typing import Dict, Optional, List, Callable, Set, Tuple
from dataclasses import dataclass

from .models import (
    GameState, GameType, GameMode, Player, PlayerState, Snake, Food, Wall,
    Position, Direction, QuadrantBounds, PLAYER_COLORS, get_random_food,
    BARRIER_CONFIGS, MAP_SIZES, TIME_LIMIT_OPTIONS, AI_DIFFICULTY_SETTINGS,
    FOOD_HIT_RECOVERY
)
from .room_manager import Room


# AI name pool
AI_NAMES = [
    "Bot Alpha", "Bot Beta", "Bot Gamma", "Snakebot", 
    "AI Hunter", "Slither AI", "Bot Omega", "MechSnake"
]


class GameManager:
    """Manages game state and logic for a single game instance"""

    _DIR_VECTORS = {
        Direction.UP: (0, -1),
        Direction.DOWN: (0, 1),
        Direction.LEFT: (-1, 0),
        Direction.RIGHT: (1, 0),
    }
    _OPPOSITE = {
        Direction.UP: Direction.DOWN,
        Direction.DOWN: Direction.UP,
        Direction.LEFT: Direction.RIGHT,
        Direction.RIGHT: Direction.LEFT,
    }

    def __init__(self, room: Room, broadcast_callback: Callable):
        self.room = room
        self.broadcast = broadcast_callback
        self.state = GameState(
            game_type=room.game_type,
            mode=room.game_mode,
            barrier_density=getattr(room, 'barrier_density', 'none')
        )
        self.game_task: Optional[asyncio.Task] = None
        self.last_update = time.time()
        
        # Cache for wall positions (built once, used many times per tick)
        self._wall_position_cache: Dict[int, Set[Tuple[int, int]]] = {}
        
    def setup_game(self):
        """Initialize game state for all players"""
        num_human_players = len(self.room.players)
        ai_count = getattr(self.room, 'ai_count', 0)
        ai_difficulties = getattr(self.room, 'ai_difficulties', [])
        
        # Total players including AI
        total_players = num_human_players + ai_count
        # Treat as single player when only 1 person is playing (no AI, or mode explicitly set)
        # This prevents survival win condition from firing immediately with only 1 player
        if total_players <= 1 and self.state.mode == GameMode.SURVIVAL:
            self.state.mode = GameMode.SINGLE_PLAYER
        is_single_player = self.state.mode == GameMode.SINGLE_PLAYER and ai_count == 0
        
        # Get map size from room settings
        map_size_key = getattr(self.room, 'map_size', 'medium')
        map_config = MAP_SIZES.get(map_size_key, MAP_SIZES['medium'])
        self.state.map_size = map_size_key
        base_width = map_config['width']
        base_height = map_config['height']
        
        # Setup grid based on total player count and map size
        if is_single_player:
            # Single player with no AI gets the full map size
            self.state.grid_width = base_width
            self.state.grid_height = base_height
            self.state.quadrant_width = base_width
            self.state.quadrant_height = base_height
        elif total_players <= 2:
            # Side by side - each player gets the full height
            self.state.grid_width = base_width * 2
            self.state.grid_height = base_height
            self.state.quadrant_width = base_width
            self.state.quadrant_height = base_height
        else:
            # 2x2 grid
            self.state.grid_width = base_width * 2
            self.state.grid_height = base_height * 2
            self.state.quadrant_width = base_width
            self.state.quadrant_height = base_height
        
        # Setup quadrant bounds
        self._setup_quadrants(total_players if not is_single_player else 1)
        
        # Generate walls for each quadrant based on barrier density
        for quadrant in self.state.quadrant_bounds.keys():
            self.state.walls[quadrant] = []
            self._generate_walls(quadrant)
        
        # Track assigned quadrants
        used_quadrants = set()
        player_index = 0
        
        # Initialize human players with snakes
        for player_id, player in self.room.players.items():
            player.state = PlayerState.PLAYING
            self.state.players[player_id] = player
            
            # For single player with no AI, always use quadrant 0
            if is_single_player:
                player.quadrant = 0
            
            used_quadrants.add(player.quadrant)
            self._setup_snake_for_player(player, player_index)
            player_index += 1
        
        # Create AI players
        self._next_ai_id = -1  # AI players get negative IDs
        for i in range(ai_count):
            ai_quadrant = self._get_next_quadrant(used_quadrants, total_players)
            used_quadrants.add(ai_quadrant)
            
            # Use per-AI difficulty if available, fallback to 'amateur'
            per_ai_difficulty = ai_difficulties[i] if i < len(ai_difficulties) else 'amateur'
            
            ai_names_custom = self.room.ai_names if hasattr(self.room, 'ai_names') else []
            raw_name = ai_names_custom[i] if i < len(ai_names_custom) and ai_names_custom[i].strip() else None
            ai_name = raw_name or AI_NAMES[i % len(AI_NAMES)]
            ai_player = Player(
                id=self._next_ai_id,
                name=ai_name,
                websocket=None,
                state=PlayerState.PLAYING,
                quadrant=ai_quadrant,
                is_ai=True,
                ai_difficulty=per_ai_difficulty,
                ai_last_decision=time.time()
            )
            self._next_ai_id -= 1
            
            self.state.players[ai_player.id] = ai_player
            self._setup_snake_for_player(ai_player, player_index)
            player_index += 1
        
        self.state.alive_count = total_players
        self.state.start_time = time.time()
        self.state.running = True
        
        # Always reset speed to base to prevent carryover across games
        self.state.current_speed = self.state.base_speed
        self.state.elapsed_time = 0
        
        # Set mode-specific settings
        if self.state.mode == GameMode.SURVIVAL:
            self.state.next_shrink_time = self.state.shrink_interval
            self.state.survival_speed_next_increase = self.state.survival_speed_increase_interval
            self.state.survival_decay_current_interval = 6.0
            # Give every snake a full initial decay interval
            for player in self.state.players.values():
                if player.snake:
                    player.snake.decay_timer = 6.0  # Starting interval
        elif self.state.mode == GameMode.HIGH_SCORE:
            # Set time limit based on room settings
            time_option = TIME_LIMIT_OPTIONS.get(self.room.time_limit, TIME_LIMIT_OPTIONS["1m"])
            self.state.time_limit = time_option["seconds"]
        elif self.state.mode == GameMode.SINGLE_PLAYER:
            # Single player has no time limit, just practice
            self.state.time_limit = 0  # No limit
    
    def _get_next_quadrant(self, used_quadrants: Set[int], total_players: int) -> int:
        """Get the next available quadrant for a player"""
        for q in range(min(total_players, 4)):
            if q not in used_quadrants:
                return q
        return 0
    
    def _setup_snake_for_player(self, player: Player, player_index: int):
        """Setup snake for a player in their quadrant"""
        # Create snake in player's quadrant with safe spawn position
        wall_positions = self._get_wall_positions(player.quadrant)
        start_x, start_y, direction = self._find_safe_spawn(player.quadrant, wall_positions)
        
        # Get direction vector for body placement (body is behind head)
        dir_vectors = {
            Direction.RIGHT: (1, 0),
            Direction.LEFT: (-1, 0),
            Direction.UP: (0, -1),
            Direction.DOWN: (0, 1)
        }
        vx, vy = dir_vectors[direction]
        
        snake = Snake(
            player_id=player.id,
            body=[Position(start_x - vx * j, start_y - vy * j) for j in range(3)],
            direction=direction,
            next_direction=direction,
            color=PLAYER_COLORS[player_index % len(PLAYER_COLORS)]
        )
        player.snake = snake
        
        # Spawn initial food in quadrant if not already done
        if player.quadrant not in self.state.foods:
            self.state.foods[player.quadrant] = []
            self._spawn_food(player.quadrant)
            self._spawn_food(player.quadrant)  # Spawn 2 food items initially
    
    def _generate_walls(self, quadrant: int):
        """Generate walls in a quadrant based on barrier density"""
        bounds = self.state.quadrant_bounds.get(quadrant)
        if not bounds:
            return
        
        config = BARRIER_CONFIGS.get(self.state.barrier_density, BARRIER_CONFIGS["none"])
        wall_count = config["wall_count"]
        
        if wall_count == 0:
            return
        
        # Try to generate walls with connectivity, retry if needed
        max_attempts = 5
        for attempt in range(max_attempts):
            walls = self._generate_walls_random(quadrant, bounds, wall_count)
            self.state.walls[quadrant] = walls
            
            # Clear wall cache before checking connectivity
            self._invalidate_wall_cache(quadrant)
            
            # Check if spawn area is still reachable
            if self._check_wall_connectivity(quadrant, bounds):
                return
        
        # If all attempts fail, fall back to sparse pattern
        self.state.walls[quadrant] = self._generate_sparse_walls(bounds, max(2, wall_count // 2))
        self._invalidate_wall_cache(quadrant)
    
    def _generate_walls_random(self, quadrant: int, bounds: QuadrantBounds, wall_count: int) -> List[Wall]:
        """Generate random walls based on density level"""
        walls = []
        width = bounds.x_max - bounds.x_min
        height = bounds.y_max - bounds.y_min
        
        # Define spawn-safe zone (center area where snake starts)
        center_x = (bounds.x_min + bounds.x_max) // 2
        center_y = (bounds.y_min + bounds.y_max) // 2
        safe_zone = (center_x - 3, center_y - 3, center_x + 3, center_y + 3)
        
        if self.state.barrier_density == "sparse":
            walls = self._generate_sparse_walls(bounds, wall_count)
        
        elif self.state.barrier_density == "moderate":
            # Random medium-sized obstacles scattered around
            placed_walls = []
            attempts = 0
            target_walls = wall_count
            
            while len(placed_walls) < target_walls and attempts < target_walls * 10:
                attempts += 1
                
                # Random wall size
                w = random.randint(2, 4)
                h = random.randint(1, 3)
                if random.random() > 0.6:
                    w, h = h, w  # Swap for variety
                
                # Random position (avoid edges and spawn zone)
                x = random.randint(bounds.x_min + 2, bounds.x_max - w - 2)
                y = random.randint(bounds.y_min + 2, bounds.y_max - h - 2)
                
                # Check spawn zone
                if self._wall_overlaps_zone(x, y, w, h, safe_zone):
                    continue
                
                # Check overlap with existing walls (with margin)
                if self._wall_overlaps_existing(x, y, w, h, placed_walls, margin=2):
                    continue
                
                placed_walls.append(Wall(Position(x, y), w, h))
            
            walls = placed_walls
        
        elif self.state.barrier_density == "dense":
            # Random maze-like pattern with lines and blocks
            
            # Random number of horizontal lines (2-4)
            num_h_lines = random.randint(2, 4)
            h_spacing = (height - 6) // (num_h_lines + 1)
            
            for i in range(num_h_lines):
                y_offset = random.randint(-1, 1)  # Add randomness to position
                y = bounds.y_min + 3 + (i + 1) * h_spacing + y_offset
                if bounds.y_min + 3 < y < bounds.y_max - 3:
                    # Random gap position and size
                    gap_size = random.randint(3, 5)
                    gap_start = random.randint(bounds.x_min + 4, bounds.x_max - gap_size - 4)
                    
                    # Left segment
                    left_len = gap_start - bounds.x_min - 2
                    if left_len >= 2:
                        walls.append(Wall(Position(bounds.x_min + 2, y), left_len, 1))
                    
                    # Right segment  
                    right_start = gap_start + gap_size
                    right_len = bounds.x_max - right_start - 2
                    if right_len >= 2:
                        walls.append(Wall(Position(right_start, y), right_len, 1))
            
            # Random number of vertical lines (1-3)
            num_v_lines = random.randint(1, 3)
            v_spacing = (width - 6) // (num_v_lines + 1)
            
            for i in range(num_v_lines):
                x_offset = random.randint(-1, 1)
                x = bounds.x_min + 3 + (i + 1) * v_spacing + x_offset
                if bounds.x_min + 3 < x < bounds.x_max - 3:
                    gap_size = random.randint(3, 5)
                    gap_start = random.randint(bounds.y_min + 4, bounds.y_max - gap_size - 4)
                    
                    # Top segment
                    top_len = gap_start - bounds.y_min - 2
                    if top_len >= 2:
                        walls.append(Wall(Position(x, bounds.y_min + 2), 1, top_len))
                    
                    # Bottom segment
                    bottom_start = gap_start + gap_size
                    bottom_len = bounds.y_max - bottom_start - 2
                    if bottom_len >= 2:
                        walls.append(Wall(Position(x, bottom_start), 1, bottom_len))
            
            # Add a few random blocks for variety
            num_blocks = random.randint(1, 3)
            for _ in range(num_blocks):
                w = random.randint(2, 3)
                h = random.randint(2, 3)
                x = random.randint(bounds.x_min + 3, bounds.x_max - w - 3)
                y = random.randint(bounds.y_min + 3, bounds.y_max - h - 3)
                
                if not self._wall_overlaps_zone(x, y, w, h, safe_zone):
                    walls.append(Wall(Position(x, y), w, h))
        
        return walls
    
    def _generate_sparse_walls(self, bounds: QuadrantBounds, wall_count: int) -> List[Wall]:
        """Generate sparse random walls"""
        walls = []
        for _ in range(wall_count):
            w = random.randint(2, 4)
            h = 1 if random.random() > 0.3 else random.randint(1, 2)
            if random.random() > 0.5:
                w, h = h, w
            
            x = random.randint(bounds.x_min + 3, bounds.x_max - w - 3)
            y = random.randint(bounds.y_min + 3, bounds.y_max - h - 3)
            walls.append(Wall(Position(x, y), w, h))
        return walls
    
    def _wall_overlaps_zone(self, x: int, y: int, w: int, h: int, 
                            zone: Tuple[int, int, int, int]) -> bool:
        """Check if a wall overlaps with a protected zone"""
        zone_x1, zone_y1, zone_x2, zone_y2 = zone
        return not (x + w <= zone_x1 or x >= zone_x2 or y + h <= zone_y1 or y >= zone_y2)
    
    def _wall_overlaps_existing(self, x: int, y: int, w: int, h: int, 
                                 existing: List[Wall], margin: int = 0) -> bool:
        """Check if a wall overlaps with existing walls (with optional margin)"""
        for wall in existing:
            wx, wy = wall.position.x, wall.position.y
            ww, wh = wall.width, wall.height
            
            # Check overlap with margin
            if not (x + w + margin <= wx or x >= wx + ww + margin or 
                    y + h + margin <= wy or y >= wy + wh + margin):
                return True
        return False
    
    def _check_wall_connectivity(self, quadrant: int, bounds: QuadrantBounds) -> bool:
        """Check if spawn area is connected to rest of map (can reach edges)"""
        center_x = (bounds.x_min + bounds.x_max) // 2
        center_y = (bounds.y_min + bounds.y_max) // 2
        
        wall_positions = self._get_wall_positions(quadrant)
        
        # Flood-fill from center to check we can reach sufficient area
        visited = set()
        queue = [(center_x, center_y)]
        
        while queue:
            x, y = queue.pop(0)
            
            if (x, y) in visited:
                continue
            if not (bounds.x_min <= x < bounds.x_max and bounds.y_min <= y < bounds.y_max):
                continue
            if (x, y) in wall_positions:
                continue
            
            visited.add((x, y))
            
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                queue.append((x + dx, y + dy))
        
        # Check we can reach at least 50% of the map
        total_cells = (bounds.x_max - bounds.x_min) * (bounds.y_max - bounds.y_min)
        required_cells = total_cells * 0.5
        
        return len(visited) >= required_cells
    
    def _get_wall_positions(self, quadrant: int) -> Set[Tuple[int, int]]:
        """Get all positions occupied by walls in a quadrant (cached for performance)"""
        if quadrant not in self._wall_position_cache:
            positions = set()
            for wall in self.state.walls.get(quadrant, []):
                for pos in wall.get_all_positions():
                    positions.add((pos.x, pos.y))
            self._wall_position_cache[quadrant] = positions
        return self._wall_position_cache[quadrant]
    
    def _invalidate_wall_cache(self, quadrant: int = None):
        """Invalidate wall position cache (call when walls change)"""
        if quadrant is not None:
            self._wall_position_cache.pop(quadrant, None)
        else:
            self._wall_position_cache.clear()
    
    def _find_safe_spawn(self, quadrant: int, wall_positions: Set[Tuple[int, int]]) -> Tuple[int, int, Direction]:
        """Find a safe spawn position and direction with no walls within 3 spaces ahead"""
        bounds = self.state.quadrant_bounds.get(quadrant)
        if not bounds:
            return (0, 0, Direction.RIGHT)
        
        # Start from center
        center_x = (bounds.x_min + bounds.x_max) // 2
        center_y = (bounds.y_min + bounds.y_max) // 2
        
        # Direction vectors for checking ahead
        direction_vectors = {
            Direction.RIGHT: (1, 0),
            Direction.LEFT: (-1, 0),
            Direction.UP: (0, -1),
            Direction.DOWN: (0, 1)
        }
        
        # Try positions in a spiral pattern from center
        for offset in range(0, max(bounds.x_max - bounds.x_min, bounds.y_max - bounds.y_min)):
            for dx in range(-offset, offset + 1):
                for dy in range(-offset, offset + 1):
                    if abs(dx) != offset and abs(dy) != offset:
                        continue  # Only check perimeter of spiral
                    
                    test_x = center_x + dx
                    test_y = center_y + dy
                    
                    # Check bounds (need space for snake body behind)
                    if test_x < bounds.x_min + 4 or test_x > bounds.x_max - 4:
                        continue
                    if test_y < bounds.y_min + 4 or test_y > bounds.y_max - 4:
                        continue
                    
                    # Try each direction
                    for direction, (vx, vy) in direction_vectors.items():
                        # Check if snake body positions are clear
                        body_clear = True
                        for j in range(3):
                            body_x = test_x - vx * j
                            body_y = test_y - vy * j
                            if (body_x, body_y) in wall_positions:
                                body_clear = False
                                break
                        
                        if not body_clear:
                            continue
                        
                        # Check 3 spaces ahead of head
                        ahead_clear = True
                        for i in range(1, 4):
                            ahead_x = test_x + vx * i
                            ahead_y = test_y + vy * i
                            if (ahead_x, ahead_y) in wall_positions:
                                ahead_clear = False
                                break
                        
                        if ahead_clear:
                            return (test_x, test_y, direction)
        
        # Fallback to center facing right (shouldn't happen with reasonable maps)
        return (center_x, center_y, Direction.RIGHT)
        
    def _setup_quadrants(self, num_players: int):
        """Setup quadrant bounds based on player count"""
        w = self.state.quadrant_width
        h = self.state.quadrant_height
        
        if num_players == 1:
            self.state.quadrant_bounds[0] = QuadrantBounds(0, w, 0, h)
        elif num_players == 2:
            self.state.quadrant_bounds[0] = QuadrantBounds(0, w, 0, h)
            self.state.quadrant_bounds[1] = QuadrantBounds(w, w * 2, 0, h)
        elif num_players == 3:
            self.state.quadrant_bounds[0] = QuadrantBounds(0, w, 0, h)
            self.state.quadrant_bounds[1] = QuadrantBounds(w, w * 2, 0, h)
            self.state.quadrant_bounds[2] = QuadrantBounds(0, w, h, h * 2)
        else:  # 4 players
            self.state.quadrant_bounds[0] = QuadrantBounds(0, w, 0, h)
            self.state.quadrant_bounds[1] = QuadrantBounds(w, w * 2, 0, h)
            self.state.quadrant_bounds[2] = QuadrantBounds(0, w, h, h * 2)
            self.state.quadrant_bounds[3] = QuadrantBounds(w, w * 2, h, h * 2)
    
    def _spawn_food(self, quadrant: int):
        """Spawn food in a quadrant"""
        bounds = self.state.quadrant_bounds.get(quadrant)
        if not bounds:
            return
        
        # Get positions occupied by snake
        occupied = set()
        for player in self.state.players.values():
            if player.snake and player.quadrant == quadrant:
                for pos in player.snake.body:
                    occupied.add((pos.x, pos.y))
        
        # Also exclude existing food (all cells of multi-cell food)
        for food in self.state.foods.get(quadrant, []):
            for pos in food.get_all_positions():
                occupied.add((pos.x, pos.y))
        
        # Exclude walls
        wall_positions = self._get_wall_positions(quadrant)
        occupied.update(wall_positions)
        
        # Find valid position for multi-cell food
        attempts = 0
        while attempts < 100:
            try:
                food_data = get_random_food()
                cells = food_data.get("cells", [(0, 0)])
                
                # Calculate required space
                max_dx = max(c[0] for c in cells)
                max_dy = max(c[1] for c in cells)
                
                # Calculate spawn bounds
                x_min_bound = bounds.x_min + 2
                x_max_bound = bounds.x_max - max_dx - 3
                y_min_bound = bounds.y_min + 2
                y_max_bound = bounds.y_max - max_dy - 3
                
                # Check if bounds are valid before randint (animal may be too large)
                if x_max_bound < x_min_bound or y_max_bound < y_min_bound:
                    attempts += 1
                    continue
                
                # Ensure food fits within bounds
                x = random.randint(x_min_bound, x_max_bound)
                y = random.randint(y_min_bound, y_max_bound)
            except Exception:
                attempts += 1
                continue
            
            # Check all cells are free
            all_free = True
            for dx, dy in cells:
                if (x + dx, y + dy) in occupied:
                    all_free = False
                    break
            
            if all_free:
                food = Food(
                    position=Position(x, y),
                    value=food_data["value"],
                    health=food_data["health"],
                    max_health=food_data["max_health"],
                    color=food_data["color"],
                    colors=food_data.get("colors", {}),
                    food_type=food_data["type"],
                    size=food_data["size"],
                    cells=cells,
                    category=food_data.get("category", "small")
                )
                if quadrant not in self.state.foods:
                    self.state.foods[quadrant] = []
                self.state.foods[quadrant].append(food)
                return
            attempts += 1
    
    def handle_input(self, player_id: int, direction: str):
        """Handle player input"""
        player = self.state.players.get(player_id)
        if not player or not player.snake or not player.snake.alive:
            return
        
        try:
            new_dir = Direction(direction)
        except ValueError:
            return
        
        # Prevent 180-degree turns
        current = player.snake.direction
        opposite = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT
        }
        
        if new_dir != opposite.get(current):
            player.snake.next_direction = new_dir
    
    def update(self, dt: float):
        """Update game state"""
        if not self.state.running or self.state.paused or self.state.game_over:
            return
        
        self.state.elapsed_time += dt
        
        # Tick down hit-recovery windows on all food (non-consecutive hit enforcement)
        for quadrant_foods in self.state.foods.values():
            for food in quadrant_foods:
                if food.hit_recovery > 0:
                    food.hit_recovery = max(0.0, food.hit_recovery - dt)
        
        # Mode-specific updates
        if self.state.mode == GameMode.SURVIVAL:
            self._update_survival(dt)
        elif self.state.mode == GameMode.HIGH_SCORE:
            self._update_high_score(dt)
        elif self.state.mode == GameMode.SINGLE_PLAYER:
            self._update_single_player(dt)
        
        # Update AI players
        current_time = time.time()
        for player in self.state.players.values():
            if player.is_ai and player.snake and player.snake.alive:
                self._update_ai_snake(player, current_time)
        
        # Move snakes
        for player in self.state.players.values():
            if player.snake and player.snake.alive:
                self._move_snake(player)
        
        # Check win conditions
        self._check_win_conditions()
    
    def _update_single_player(self, dt: float):
        """Update single player mode specifics"""
        # Update combo timers
        for player in self.state.players.values():
            if player.snake and player.snake.alive:
                if player.snake.combo_timer > 0:
                    player.snake.combo_timer -= dt
                    if player.snake.combo_timer <= 0:
                        player.snake.combo = 0
        
        # Gradually increase speed based on score
        for player in self.state.players.values():
            if player.snake:
                # Increase speed every 500 points
                speed_increases = player.snake.score // 500
                new_speed = self.state.base_speed * (0.95 ** speed_increases)
                self.state.current_speed = max(50, new_speed)
    
    def _get_survival_decay_interval(self) -> float:
        """Decay interval shrinks over time — more pressure as the game progresses."""
        t = self.state.elapsed_time
        if t < 30:   return 6.0
        elif t < 60: return 5.0
        elif t < 120: return 4.0
        else:        return 3.0

    def _apply_tail_decay(self, player: Player):
        """Remove last tail segment; kill snake if body drops below minimum length."""
        snake = player.snake
        if not snake or not snake.alive:
            return
        if len(snake.body) > self.state.survival_decay_min_length:
            snake.body.pop()
        else:
            # Too short — starved to death
            self._kill_snake(player)

    def _update_survival(self, dt: float):
        """Update survival mode: arena shrink + speed ramp + tail decay."""
        # --- Arena shrink (existing) ---
        if self.state.elapsed_time >= self.state.next_shrink_time:
            self._shrink_arena()
            self.state.next_shrink_time += self.state.shrink_interval

        # --- Speed ramp: every 15 s the snake moves ~5% faster ---
        if self.state.elapsed_time >= self.state.survival_speed_next_increase:
            new_speed = self.state.current_speed * self.state.survival_speed_factor
            # Cap: no faster than 50 ms (2× base speed)
            self.state.current_speed = max(self.state.base_speed * 0.5, new_speed)
            self.state.survival_speed_next_increase += self.state.survival_speed_increase_interval

        # --- Tail decay: each living snake loses a segment periodically ---
        decay_interval = self._get_survival_decay_interval()
        self.state.survival_decay_current_interval = decay_interval

        for player in self.state.players.values():
            if player.snake and player.snake.alive:
                player.snake.decay_timer -= dt
                if player.snake.decay_timer <= 0:
                    self._apply_tail_decay(player)
                    # Reset timer only if still alive after decay
                    if player.snake and player.snake.alive:
                        player.snake.decay_timer = decay_interval
    
    def _update_high_score(self, dt: float):
        """Update high score mode specifics"""
        # Speed increase
        intervals_passed = int(self.state.elapsed_time / self.state.speed_increase_interval)
        expected_speed = self.state.base_speed * (self.state.speed_increase_factor ** intervals_passed)
        if self.state.current_speed > expected_speed:
            self.state.current_speed = max(50, expected_speed)  # Min 50ms
        
        # Update combo timers
        for player in self.state.players.values():
            if player.snake and player.snake.alive:
                if player.snake.combo_timer > 0:
                    player.snake.combo_timer -= dt
                    if player.snake.combo_timer <= 0:
                        player.snake.combo = 0
        
        # Check time limit
        if self.state.elapsed_time >= self.state.time_limit:
            self._end_game_high_score()
    
    def _shrink_arena(self):
        """Shrink all quadrant boundaries"""
        for q, bounds in self.state.quadrant_bounds.items():
            bounds.x_min += self.state.shrink_amount
            bounds.x_max -= self.state.shrink_amount
            bounds.y_min += self.state.shrink_amount
            bounds.y_max -= self.state.shrink_amount
            
            # Check if any snakes are now outside bounds
            for player in self.state.players.values():
                if player.quadrant == q and player.snake and player.snake.alive:
                    head = player.snake.body[0]
                    if not bounds.contains(head):
                        self._kill_snake(player)
    
    def _move_snake(self, player: Player):
        """Move a player's snake"""
        snake = player.snake
        if not snake:
            return
        
        # Apply next direction
        snake.direction = snake.next_direction
        
        # Calculate new head position
        head = snake.body[0]
        new_head = Position(head.x, head.y)
        
        if snake.direction == Direction.UP:
            new_head.y -= 1
        elif snake.direction == Direction.DOWN:
            new_head.y += 1
        elif snake.direction == Direction.LEFT:
            new_head.x -= 1
        elif snake.direction == Direction.RIGHT:
            new_head.x += 1
        
        # Check collisions
        bounds = self.state.quadrant_bounds.get(player.quadrant)
        if bounds:
            # Boundary collision
            if not bounds.contains(new_head):
                self._kill_snake(player)
                return
        
        # Wall collision
        wall_positions = self._get_wall_positions(player.quadrant)
        if (new_head.x, new_head.y) in wall_positions:
            self._kill_snake(player)
            return
        
        # Self collision
        if new_head in snake.body[:-1]:
            self._kill_snake(player)
            return
        
        # Add new head
        snake.body.insert(0, new_head)
        
        # Check food collision (check all cells of multi-cell food)
        ate_food = False
        foods = self.state.foods.get(player.quadrant, [])
        barrier_config = BARRIER_CONFIGS.get(self.state.barrier_density, BARRIER_CONFIGS["none"])
        
        for food in foods[:]:  # Copy list to allow removal
            # Skip animals that are in their hit-recovery window (non-consecutive rule)
            if food.hit_recovery > 0:
                continue
            
            # Check if head hit any cell of this food
            food_positions = food.get_all_positions()
            hit = any(new_head.x == fp.x and new_head.y == fp.y for fp in food_positions)
            
            if hit:
                # Score per hit = base_value_per_hit × barrier_multiplier (× combo if last hit)
                base_pts_per_hit = food.value // food.max_health
                
                food.health -= 1
                
                if food.health <= 0:
                    # Final hit — food is consumed; award remaining points + combo bonus
                    score = int(base_pts_per_hit * barrier_config["multiplier"])
                    
                    # Combo bonus applies on the kill hit only
                    if self.state.mode in [GameMode.HIGH_SCORE, GameMode.SINGLE_PLAYER, GameMode.SURVIVAL]:
                        snake.combo += 1
                        snake.combo_timer = 2.0
                        score = int(score * (1 + snake.combo * 0.1))  # 10% per combo streak
                    
                    # Survival mode: eating resets the decay timer
                    if self.state.mode == GameMode.SURVIVAL:
                        snake.decay_timer = self._get_survival_decay_interval()
                    
                    snake.score += score
                    foods.remove(food)
                    self._spawn_food(player.quadrant)
                    
                    if self.state.mode == GameMode.SINGLE_PLAYER:
                        if snake.score > self.state.single_player_high_score:
                            self.state.single_player_high_score = snake.score
                else:
                    # Partial hit — award per-hit score immediately, start recovery window
                    score = int(base_pts_per_hit * barrier_config["multiplier"])
                    snake.score += score
                    
                    # Begin recovery: snake must leave and re-approach for next hit
                    recovery_duration = FOOD_HIT_RECOVERY.get(food.category, 0.0)
                    food.hit_recovery = recovery_duration
                    
                    if self.state.mode == GameMode.SINGLE_PLAYER:
                        if snake.score > self.state.single_player_high_score:
                            self.state.single_player_high_score = snake.score
                
                ate_food = True
                break
        
        # Remove tail if no food eaten
        if not ate_food:
            snake.body.pop()
    
    # Fibonacci respawn delays (seconds): 2, 3, 5, 8, 13, 21 then capped
    _RESPAWN_FIBONACCI = [2, 3, 5, 8, 13, 21]
    
    def _get_respawn_delay(self, death_count: int) -> float:
        """Return fibonacci-based respawn delay for the nth death (1-indexed)."""
        idx = min(death_count - 1, len(self._RESPAWN_FIBONACCI) - 1)
        return float(self._RESPAWN_FIBONACCI[max(0, idx)])
    
    def _kill_snake(self, player: Player):
        """Kill a player's snake"""
        if not player.snake:
            return
        
        player.snake.alive = False
        player.state = PlayerState.DEAD
        player.death_time = time.time()
        player.death_count += 1
        
        # Progressive respawn penalty in high score mode (fibonacci sequence)
        if self.state.mode == GameMode.HIGH_SCORE:
            player.respawn_delay = self._get_respawn_delay(player.death_count)
        
        self.state.alive_count -= 1
        
        # Assign rank (for survival mode)
        if self.state.mode == GameMode.SURVIVAL:
            player.rank = self.state.alive_count + 1
    
    def _respawn_snake(self, player: Player):
        """Respawn a snake (for high score mode)"""
        bounds = self.state.quadrant_bounds.get(player.quadrant)
        if not bounds:
            return
        
        # Find safe spawn position with no walls in front
        wall_positions = self._get_wall_positions(player.quadrant)
        start_x, start_y, direction = self._find_safe_spawn(player.quadrant, wall_positions)
        
        # Get direction vector for body placement
        dir_vectors = {
            Direction.RIGHT: (1, 0),
            Direction.LEFT: (-1, 0),
            Direction.UP: (0, -1),
            Direction.DOWN: (0, 1)
        }
        vx, vy = dir_vectors[direction]
        
        player.snake.body = [Position(start_x - vx * j, start_y - vy * j) for j in range(3)]
        player.snake.direction = direction
        player.snake.next_direction = direction
        player.snake.alive = True
        player.snake.combo = 0
        player.state = PlayerState.PLAYING
        self.state.alive_count += 1
    
    def _check_win_conditions(self):
        """Check if game should end"""
        if self.state.mode == GameMode.SURVIVAL:
            if self.state.alive_count <= 1:
                # Find winner
                for player in self.state.players.values():
                    if player.snake and player.snake.alive:
                        player.rank = 1
                        self.state.winner_id = player.id
                        break
                self.state.game_over = True
                self.state.running = False
        
        elif self.state.mode == GameMode.SINGLE_PLAYER:
            # Single player ends when snake dies
            if self.state.alive_count <= 0:
                for player in self.state.players.values():
                    player.rank = 1
                    self.state.winner_id = player.id
                self.state.game_over = True
                self.state.running = False
        
        # High score mode ends by time limit (handled in _update_high_score)
    
    def _end_game_high_score(self):
        """End high score mode game"""
        self.state.game_over = True
        self.state.running = False
        
        # Sort by score and assign ranks
        players_sorted = sorted(
            self.state.players.values(),
            key=lambda p: p.snake.score if p.snake else 0,
            reverse=True
        )
        
        for i, player in enumerate(players_sorted):
            player.rank = i + 1
        
        if players_sorted:
            self.state.winner_id = players_sorted[0].id
    
    # ==================== AI Snake Logic ====================

    def _update_ai_snake(self, player: Player, current_time: float):
        """Update AI snake decision making"""
        if not player.snake or not player.snake.alive:
            return

        settings = AI_DIFFICULTY_SETTINGS.get(
            player.ai_difficulty, AI_DIFFICULTY_SETTINGS["amateur"]
        )
        reaction_time = settings["reaction_time"] / 1000.0

        if current_time - player.ai_last_decision < reaction_time:
            return

        player.ai_last_decision = current_time
        new_direction = self._ai_decide_direction(player, settings)

        if new_direction and new_direction != self._OPPOSITE.get(player.snake.direction):
            player.snake.next_direction = new_direction

    # ---- helpers ----

    def _ai_build_blocked(self, player: Player) -> Set[Tuple[int, int]]:
        """All cells that would kill the snake on the next step."""
        quadrant = player.quadrant
        blocked = set(self._get_wall_positions(quadrant))
        for pos in player.snake.body[:-1]:
            blocked.add((pos.x, pos.y))
        for other in self.state.players.values():
            if other.id != player.id and other.quadrant == quadrant:
                if other.snake and other.snake.alive:
                    for pos in other.snake.body:
                        blocked.add((pos.x, pos.y))
        return blocked

    def _ai_safe_dirs(self, player: Player, bounds: QuadrantBounds,
                      blocked: Set[Tuple[int, int]]) -> List[Direction]:
        """Directions where the immediate next cell is in-bounds and unblocked."""
        head = player.snake.body[0]
        current = player.snake.direction
        safe = []
        for d, (dx, dy) in self._DIR_VECTORS.items():
            if d == self._OPPOSITE.get(current):
                continue
            nx, ny = head.x + dx, head.y + dy
            if (bounds.x_min <= nx < bounds.x_max
                    and bounds.y_min <= ny < bounds.y_max
                    and (nx, ny) not in blocked):
                safe.append(d)
        return safe

    def _flood_fill_count(self, sx: int, sy: int, bounds: QuadrantBounds,
                          blocked: Set[Tuple[int, int]], max_depth: int) -> int:
        """BFS flood-fill counting reachable cells (uses deque for O(n) performance)."""
        visited = {(sx, sy)}
        q = deque()
        q.append((sx, sy, 0))
        if (not (bounds.x_min <= sx < bounds.x_max and bounds.y_min <= sy < bounds.y_max)
                or (sx, sy) in blocked):
            return 0
        count = 1
        while q:
            x, y, depth = q.popleft()
            if depth >= max_depth:
                continue
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                nx, ny = x + dx, y + dy
                if (nx, ny) not in visited:
                    visited.add((nx, ny))
                    if (bounds.x_min <= nx < bounds.x_max
                            and bounds.y_min <= ny < bounds.y_max
                            and (nx, ny) not in blocked):
                        count += 1
                        q.append((nx, ny, depth + 1))
        return count

    def _ai_bfs_to_food(self, hx: int, hy: int,
                         target_cells: Set[Tuple[int, int]],
                         bounds: QuadrantBounds,
                         blocked: Set[Tuple[int, int]],
                         max_depth: int) -> Optional[Direction]:
        """BFS shortest path from head to any target cell; returns the first-step direction."""
        visited = {(hx, hy)}
        q = deque()
        for d, (dx, dy) in self._DIR_VECTORS.items():
            nx, ny = hx + dx, hy + dy
            if (nx, ny) in target_cells:
                return d
            if ((nx, ny) not in visited
                    and bounds.x_min <= nx < bounds.x_max
                    and bounds.y_min <= ny < bounds.y_max
                    and (nx, ny) not in blocked):
                visited.add((nx, ny))
                q.append((nx, ny, d, 1))
        while q:
            x, y, first_dir, depth = q.popleft()
            if depth >= max_depth:
                continue
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                nx, ny = x + dx, y + dy
                if (nx, ny) in target_cells:
                    return first_dir
                if ((nx, ny) not in visited
                        and bounds.x_min <= nx < bounds.x_max
                        and bounds.y_min <= ny < bounds.y_max
                        and (nx, ny) not in blocked):
                    visited.add((nx, ny))
                    q.append((nx, ny, first_dir, depth + 1))
        return None

    # ---- food selection (mode-aware) ----

    def _ai_pick_food(self, player: Player, settings: dict,
                      bounds: QuadrantBounds) -> Optional[Food]:
        """Choose the best food target considering game mode, difficulty, and food state."""
        foods = self.state.foods.get(player.quadrant, [])
        if not foods:
            return None

        edible = [f for f in foods if f.hit_recovery <= 0]
        if not edible:
            edible = sorted(foods, key=lambda f: f.hit_recovery)[:1]
        if not edible:
            return None

        head = player.snake.body[0]
        mode = self.state.mode
        value_power = settings.get("value_power", 1.0)
        combo_aware = settings.get("combo_aware", False)
        survival_aware = settings.get("survival_awareness", False)
        body_len = len(player.snake.body)

        best = None
        best_score = -1e9

        for food in edible:
            food_cells = food.get_all_positions()
            dist = min(abs(head.x - p.x) + abs(head.y - p.y) for p in food_cells)
            if dist == 0:
                dist = 0.5

            pts_per_hit = food.value / max(food.max_health, 1)

            if mode == GameMode.SURVIVAL and survival_aware:
                # Survival: eating resets decay timer -- prefer quick one-shot food.
                # When body is short, urgency skyrockets.
                urgency = 3.0 if body_len <= 5 else (1.5 if body_len <= 8 else 1.0)
                if food.max_health == 1:
                    score = (pts_per_hit ** value_power) / dist * 2.0 * urgency
                else:
                    score = (pts_per_hit ** value_power) / dist * 0.4 * urgency

            elif mode == GameMode.HIGH_SCORE and combo_aware:
                # High-score: maximise score-per-second. One-shot food = quick combo building.
                combo_mult = 1.0 + player.snake.combo * 0.12
                if food.max_health == 1:
                    score = (pts_per_hit ** value_power) * combo_mult / dist * 1.8
                else:
                    score = (pts_per_hit ** value_power) / dist
            else:
                score = (pts_per_hit ** value_power) / dist

            if score > best_score:
                best_score = score
                best = food

        return best

    # ---- core decision ----

    def _ai_decide_direction(self, player: Player, settings: dict) -> Optional[Direction]:
        """Score every safe direction and pick the best one."""
        snake = player.snake
        head = snake.body[0]
        bounds = self.state.quadrant_bounds.get(player.quadrant)
        if not bounds:
            return None

        blocked = self._ai_build_blocked(player)
        safe_dirs = self._ai_safe_dirs(player, bounds, blocked)

        if not safe_dirs:
            return snake.direction
        if len(safe_dirs) == 1:
            return safe_dirs[0]

        scores = {d: 0.0 for d in safe_dirs}

        # ── 1. Space evaluation (flood fill or straight-line clearance) ──
        if settings.get("dead_end_check", False):
            flood_depth = settings.get("flood_fill_depth", 15)
            flood = {}
            for d in safe_dirs:
                dx, dy = self._DIR_VECTORS[d]
                flood[d] = self._flood_fill_count(
                    head.x + dx, head.y + dy, bounds, blocked, flood_depth
                )
            max_flood = max(flood.values()) if flood else 1
            if max_flood > 0:
                threshold = max_flood * settings.get("dead_end_threshold", 0.3)
                for d in safe_dirs:
                    if flood[d] < threshold:
                        scores[d] -= 10000
                    else:
                        scores[d] += (flood[d] / max_flood) * 60
        else:
            for d in safe_dirs:
                dx, dy = self._DIR_VECTORS[d]
                clear = 0
                for step in range(1, 7):
                    cx, cy = head.x + dx * step, head.y + dy * step
                    if (bounds.x_min <= cx < bounds.x_max
                            and bounds.y_min <= cy < bounds.y_max
                            and (cx, cy) not in blocked):
                        clear += 1
                    else:
                        break
                scores[d] += clear * 8

        # ── 2. Food targeting ──
        food_seeking_chance = settings.get("food_seeking", 0.7)
        seek_food = settings.get("deterministic", False) or random.random() < food_seeking_chance

        if seek_food:
            target = self._ai_pick_food(player, settings, bounds)
            if target:
                target_cells = set(
                    (p.x, p.y) for p in target.get_all_positions()
                )
                nearest = min(target_cells,
                              key=lambda c: abs(head.x - c[0]) + abs(head.y - c[1]))

                bfs_dir = None
                if settings.get("use_pathfinding", False):
                    bfs_dir = self._ai_bfs_to_food(
                        head.x, head.y, target_cells, bounds, blocked,
                        max_depth=settings.get("pathfinding_depth", 40)
                    )

                if bfs_dir and bfs_dir in safe_dirs:
                    scores[bfs_dir] += 300
                else:
                    for d in safe_dirs:
                        dx, dy = self._DIR_VECTORS[d]
                        nx, ny = head.x + dx, head.y + dy
                        new_dist = abs(nx - nearest[0]) + abs(ny - nearest[1])
                        old_dist = abs(head.x - nearest[0]) + abs(head.y - nearest[1])
                        if new_dist < old_dist:
                            scores[d] += 120
                        elif new_dist == old_dist:
                            scores[d] += 30

        # ── 3. Survival urgency boost ──
        if (settings.get("survival_awareness", False)
                and self.state.mode == GameMode.SURVIVAL
                and len(snake.body) <= 5):
            for d in safe_dirs:
                if scores[d] > 0:
                    scores[d] *= 2.0

        # ── 4. Prefer continuing straight (smooth movement) ──
        if snake.direction in safe_dirs:
            scores[snake.direction] += 10

        # ── 5. Randomness (lower difficulties) ──
        randomness = settings.get("randomness", 0)
        if randomness > 0:
            for d in safe_dirs:
                scores[d] += random.uniform(0, randomness)

        return max(safe_dirs, key=lambda d: scores[d])
    
    async def run_game_loop(self):
        """Main game loop"""
        self.setup_game()
        
        # Send initial state
        await self.broadcast({
            "type": "game_start",
            "state": self.state.to_dict()
        })
        
        tick_rate = 1 / 30  # 30 FPS for updates (reduced from 60 for performance)
        move_accumulator = 0
        
        while self.state.running and not self.state.game_over:
            loop_start = time.time()
            
            # Accumulate time for snake movement
            move_accumulator += tick_rate * 1000  # Convert to ms
            
            # Move snakes at game speed
            while move_accumulator >= self.state.current_speed:
                self.update(self.state.current_speed / 1000)  # Convert to seconds
                move_accumulator -= self.state.current_speed
            
            # Broadcast state
            await self.broadcast({
                "type": "game_state",
                "state": self.state.to_dict()
            })
            
            # Handle respawns in high score mode (fibonacci-increasing delay per death)
            if self.state.mode == GameMode.HIGH_SCORE:
                for player in self.state.players.values():
                    if player.state == PlayerState.DEAD and player.death_time:
                        if time.time() - player.death_time >= player.respawn_delay:
                            self._respawn_snake(player)
            
            # Sleep to maintain tick rate
            elapsed = time.time() - loop_start
            if elapsed < tick_rate:
                await asyncio.sleep(tick_rate - elapsed)
        
        # Send game over
        await self.broadcast({
            "type": "game_over",
            "winner_id": self.state.winner_id,
            "final_state": self.state.to_dict()
        })
    
    def start(self):
        """Start the game loop"""
        self.game_task = asyncio.create_task(self.run_game_loop())
    
    def stop(self):
        """Stop the game"""
        self.state.running = False
        if self.game_task:
            self.game_task.cancel()
    
    def pause(self):
        """Pause the game"""
        self.state.paused = True
    
    def resume(self):
        """Resume the game"""
        self.state.paused = False
