"""
Game manager for snake multiplayer game logic
"""

import asyncio
import random
import time
import math
from typing import Dict, Optional, List, Callable, Set, Tuple
from dataclasses import dataclass

from .models import (
    GameState, GameType, GameMode, Player, PlayerState, Snake, Food, Wall,
    Position, Direction, QuadrantBounds, PLAYER_COLORS, get_random_food,
    BARRIER_CONFIGS, MAP_SIZES, TIME_LIMIT_OPTIONS, AI_DIFFICULTY_SETTINGS
)
from .room_manager import Room


# AI name pool
AI_NAMES = [
    "Bot Alpha", "Bot Beta", "Bot Gamma", "Snakebot", 
    "AI Hunter", "Slither AI", "Bot Omega", "MechSnake"
]


class GameManager:
    """Manages game state and logic for a single game instance"""
    
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
        
        # Set mode-specific settings
        if self.state.mode == GameMode.SURVIVAL:
            self.state.next_shrink_time = self.state.shrink_interval
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
        for food in foods[:]:  # Copy list to allow removal
            # Check if head hit any cell of this food
            food_positions = food.get_all_positions()
            hit = any(new_head.x == fp.x and new_head.y == fp.y for fp in food_positions)
            
            if hit:
                food.health -= 1
                if food.health <= 0:
                    # Food eaten completely
                    score = food.value
                    
                    # Apply barrier multiplier
                    barrier_config = BARRIER_CONFIGS.get(self.state.barrier_density, BARRIER_CONFIGS["none"])
                    score = int(score * barrier_config["multiplier"])
                    
                    # Combo bonus (all modes)
                    if self.state.mode in [GameMode.HIGH_SCORE, GameMode.SINGLE_PLAYER, GameMode.SURVIVAL]:
                        snake.combo += 1
                        snake.combo_timer = 2.0  # 2 second combo window
                        score = int(score * (1 + snake.combo * 0.1))  # 10% bonus per combo

                    # Survival mode: eating food resets the decay timer
                    if self.state.mode == GameMode.SURVIVAL:
                        snake.decay_timer = self._get_survival_decay_interval()

                    snake.score += score
                    foods.remove(food)
                    self._spawn_food(player.quadrant)
                    
                    # Track high score in single player
                    if self.state.mode == GameMode.SINGLE_PLAYER:
                        if snake.score > self.state.single_player_high_score:
                            self.state.single_player_high_score = snake.score
                ate_food = True
                break
        
        # Remove tail if no food eaten
        if not ate_food:
            snake.body.pop()
    
    def _kill_snake(self, player: Player):
        """Kill a player's snake"""
        if not player.snake:
            return
        
        player.snake.alive = False
        player.state = PlayerState.DEAD
        player.death_time = time.time()
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
        
        # Get AI settings
        settings = AI_DIFFICULTY_SETTINGS.get(player.ai_difficulty, AI_DIFFICULTY_SETTINGS["amateur"])
        reaction_time = settings["reaction_time"] / 1000.0  # Convert ms to seconds
        
        # Check if enough time has passed since last decision
        if current_time - player.ai_last_decision < reaction_time:
            return
        
        player.ai_last_decision = current_time
        
        # Get the AI's decision
        new_direction = self._ai_decide_direction(player, settings)
        
        if new_direction:
            # Check it's not a 180 degree turn
            opposite = {
                Direction.UP: Direction.DOWN,
                Direction.DOWN: Direction.UP,
                Direction.LEFT: Direction.RIGHT,
                Direction.RIGHT: Direction.LEFT
            }
            if new_direction != opposite.get(player.snake.direction):
                player.snake.next_direction = new_direction
    
    def _ai_decide_direction(self, player: Player, settings: dict) -> Optional[Direction]:
        """AI decides the best direction to move"""
        snake = player.snake
        head = snake.body[0]
        quadrant = player.quadrant
        bounds = self.state.quadrant_bounds.get(quadrant)
        
        if not bounds:
            return None
        
        # Direction priority for deterministic tie-breaking: current direction first, then clockwise
        current_dir = snake.direction
        clockwise_order = [Direction.UP, Direction.RIGHT, Direction.DOWN, Direction.LEFT]
        
        # Build priority order: current direction first, then clockwise from current
        current_idx = clockwise_order.index(current_dir) if current_dir in clockwise_order else 0
        directions = [current_dir]
        for i in range(1, 4):
            directions.append(clockwise_order[(current_idx + i) % 4])
        
        # Calculate safe directions (avoid walls, boundaries, self, other snakes)
        look_ahead = settings["look_ahead"]
        safe_directions = []
        for direction in directions:
            if self._ai_is_direction_safe(player, direction, look_ahead):
                safe_directions.append(direction)
        
        if not safe_directions:
            # No safe direction - try current direction as last resort
            return snake.direction
        
        # Dead-end avoidance for higher difficulties
        if settings.get("dead_end_check", False) and len(safe_directions) > 1:
            safe_directions = self._ai_filter_dead_ends(player, safe_directions)
            if not safe_directions:
                # Fallback to original safe directions
                safe_directions = [d for d in directions if self._ai_is_direction_safe(player, d, look_ahead)]
        
        # Decide based on difficulty
        is_deterministic = settings.get("deterministic", False)
        food_seeking_chance = settings["food_seeking"]
        
        if is_deterministic or random.random() < food_seeking_chance:
            # Seek food (deterministic or by chance)
            return self._ai_direction_to_food(player, safe_directions, is_deterministic)
        else:
            # Random safe direction (only for lower difficulties)
            return random.choice(safe_directions)
    
    def _ai_is_direction_safe(self, player: Player, direction: Direction, look_ahead: int) -> bool:
        """Check if a direction is safe to move in"""
        snake = player.snake
        head = snake.body[0]
        bounds = self.state.quadrant_bounds.get(player.quadrant)
        
        if not bounds:
            return False
        
        # Calculate the positions we would be in
        dx, dy = {
            Direction.UP: (0, -1),
            Direction.DOWN: (0, 1),
            Direction.LEFT: (-1, 0),
            Direction.RIGHT: (1, 0)
        }[direction]
        
        # Get wall positions once (cached)
        wall_positions = self._get_wall_positions(player.quadrant)
        
        # Check each position ahead
        for i in range(1, look_ahead + 1):
            check_x = head.x + dx * i
            check_y = head.y + dy * i
            
            # Check boundaries
            if not (bounds.x_min <= check_x < bounds.x_max and 
                    bounds.y_min <= check_y < bounds.y_max):
                return False
            
            # Check walls
            if (check_x, check_y) in wall_positions:
                return False
            
            # Check self collision (only first step matters for 180 turns)
            if i == 1:
                for body_pos in snake.body[:-1]:  # Don't check tail as it will move
                    if body_pos.x == check_x and body_pos.y == check_y:
                        return False
                
                # Check other snakes in same quadrant
                for other_player in self.state.players.values():
                    if other_player.id != player.id and other_player.quadrant == player.quadrant:
                        if other_player.snake and other_player.snake.alive:
                            for body_pos in other_player.snake.body:
                                if body_pos.x == check_x and body_pos.y == check_y:
                                    return False
        
        return True
    
    def _ai_filter_dead_ends(self, player: Player, safe_directions: List[Direction]) -> List[Direction]:
        """Filter out directions that lead to dead ends (areas with few escape routes)"""
        snake = player.snake
        head = snake.body[0]
        bounds = self.state.quadrant_bounds.get(player.quadrant)
        
        if not bounds:
            return safe_directions
        
        wall_positions = self._get_wall_positions(player.quadrant)
        snake_positions = set((pos.x, pos.y) for pos in snake.body[:-1])
        
        # Count reachable cells for each direction using flood-fill (limited depth)
        direction_scores = []
        max_depth = 15  # Limit flood-fill depth for performance
        
        for direction in safe_directions:
            dx, dy = {
                Direction.UP: (0, -1),
                Direction.DOWN: (0, 1),
                Direction.LEFT: (-1, 0),
                Direction.RIGHT: (1, 0)
            }[direction]
            
            start_x = head.x + dx
            start_y = head.y + dy
            
            # Flood-fill to count reachable cells
            reachable = self._flood_fill_count(
                start_x, start_y, bounds, wall_positions, snake_positions, max_depth
            )
            direction_scores.append((direction, reachable))
        
        # Filter out directions with significantly fewer reachable cells
        if direction_scores:
            max_reachable = max(score for _, score in direction_scores)
            threshold = max_reachable * 0.3  # At least 30% of best
            filtered = [d for d, score in direction_scores if score >= threshold]
            if filtered:
                return filtered
        
        return safe_directions
    
    def _flood_fill_count(self, start_x: int, start_y: int, bounds: QuadrantBounds,
                          wall_positions: Set[Tuple[int, int]], 
                          snake_positions: Set[Tuple[int, int]],
                          max_depth: int) -> int:
        """Count reachable cells from a starting position"""
        visited = set()
        queue = [(start_x, start_y, 0)]
        count = 0
        
        while queue:
            x, y, depth = queue.pop(0)
            
            if (x, y) in visited or depth > max_depth:
                continue
            
            # Check if valid
            if not (bounds.x_min <= x < bounds.x_max and bounds.y_min <= y < bounds.y_max):
                continue
            if (x, y) in wall_positions or (x, y) in snake_positions:
                continue
            
            visited.add((x, y))
            count += 1
            
            # Add neighbors
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                queue.append((x + dx, y + dy, depth + 1))
        
        return count
    
    def _ai_direction_to_food(self, player: Player, safe_directions: List[Direction], 
                               deterministic: bool = False) -> Direction:
        """Find the best direction to move towards food"""
        snake = player.snake
        head = snake.body[0]
        quadrant = player.quadrant
        
        # Find nearest food
        foods = self.state.foods.get(quadrant, [])
        if not foods:
            # No food - use deterministic fallback (first safe direction) or random
            return safe_directions[0] if deterministic else random.choice(safe_directions)
        
        # Find closest food (prioritize by value/distance ratio for smarter targeting)
        nearest_food = None
        best_value = -float('inf')
        
        for food in foods:
            food_pos = food.position
            distance = abs(head.x - food_pos.x) + abs(head.y - food_pos.y)
            if distance == 0:
                distance = 0.5  # Avoid division by zero
            # Score by value per distance
            value = food.value / distance
            if value > best_value:
                best_value = value
                nearest_food = food
        
        if not nearest_food:
            return safe_directions[0] if deterministic else random.choice(safe_directions)
        
        food_pos = nearest_food.position
        
        # Determine which direction gets us closer
        # Use deterministic tie-breaking: prefer directions in order given (current dir first)
        best_direction = None
        best_score = float('inf')
        
        for direction in safe_directions:
            dx, dy = {
                Direction.UP: (0, -1),
                Direction.DOWN: (0, 1),
                Direction.LEFT: (-1, 0),
                Direction.RIGHT: (1, 0)
            }[direction]
            
            new_x = head.x + dx
            new_y = head.y + dy
            
            # Calculate new distance to food
            new_distance = abs(new_x - food_pos.x) + abs(new_y - food_pos.y)
            
            # For deterministic mode, only update if strictly better (not equal)
            # This preserves the direction priority order for ties
            if new_distance < best_score:
                best_score = new_distance
                best_direction = direction
        
        if best_direction:
            return best_direction
        
        # Fallback
        return safe_directions[0] if deterministic else random.choice(safe_directions)
    
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
            
            # Handle respawns in high score mode
            if self.state.mode == GameMode.HIGH_SCORE:
                for player in self.state.players.values():
                    if player.state == PlayerState.DEAD and player.death_time:
                        if time.time() - player.death_time >= 2:  # 2 second respawn
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
