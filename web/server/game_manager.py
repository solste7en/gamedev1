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
    BARRIER_CONFIGS, MAP_SIZES, TIME_LIMIT_OPTIONS
)
from .room_manager import Room


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
        
    def setup_game(self):
        """Initialize game state for all players"""
        num_players = len(self.room.players)
        is_single_player = self.state.mode == GameMode.SINGLE_PLAYER or num_players == 1
        
        # Get map size from room settings
        map_size_key = getattr(self.room, 'map_size', 'medium')
        map_config = MAP_SIZES.get(map_size_key, MAP_SIZES['medium'])
        base_width = map_config['width']
        base_height = map_config['height']
        
        # Setup grid based on player count and map size
        if is_single_player:
            # Single player gets the full map size
            self.state.grid_width = base_width
            self.state.grid_height = base_height
            self.state.quadrant_width = base_width
            self.state.quadrant_height = base_height
        elif num_players <= 2:
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
        self._setup_quadrants(num_players if not is_single_player else 1)
        
        # Generate walls for each quadrant based on barrier density
        for quadrant in self.state.quadrant_bounds.keys():
            self.state.walls[quadrant] = []
            self._generate_walls(quadrant)
        
        # Initialize players with snakes
        for i, (player_id, player) in enumerate(self.room.players.items()):
            player.state = PlayerState.PLAYING
            self.state.players[player_id] = player
            
            # For single player, always use quadrant 0
            if is_single_player:
                player.quadrant = 0
            
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
                player_id=player_id,
                body=[Position(start_x - vx * j, start_y - vy * j) for j in range(3)],
                direction=direction,
                next_direction=direction,
                color=PLAYER_COLORS[i % len(PLAYER_COLORS)]
            )
            player.snake = snake
            
            # Spawn initial food in each quadrant
            self.state.foods[player.quadrant] = []
            self._spawn_food(player.quadrant)
            self._spawn_food(player.quadrant)  # Spawn 2 food items initially
        
        self.state.alive_count = num_players
        self.state.start_time = time.time()
        self.state.running = True
        
        # Set mode-specific settings
        if self.state.mode == GameMode.SURVIVAL:
            self.state.next_shrink_time = self.state.shrink_interval
        elif self.state.mode == GameMode.HIGH_SCORE:
            # Set time limit based on room settings
            time_option = TIME_LIMIT_OPTIONS.get(self.room.time_limit, TIME_LIMIT_OPTIONS["1m"])
            self.state.time_limit = time_option["seconds"]
        elif self.state.mode == GameMode.SINGLE_PLAYER:
            # Single player has no time limit, just practice
            self.state.time_limit = 0  # No limit
    
    def _generate_walls(self, quadrant: int):
        """Generate walls in a quadrant based on barrier density"""
        bounds = self.state.quadrant_bounds.get(quadrant)
        if not bounds:
            return
        
        config = BARRIER_CONFIGS.get(self.state.barrier_density, BARRIER_CONFIGS["none"])
        wall_count = config["wall_count"]
        
        if wall_count == 0:
            return
        
        width = bounds.x_max - bounds.x_min
        height = bounds.y_max - bounds.y_min
        
        # Generate different wall patterns based on density
        walls = []
        
        if self.state.barrier_density == "sparse":
            # A few random small walls
            for _ in range(wall_count):
                w = random.randint(2, 4)
                h = 1 if random.random() > 0.3 else random.randint(1, 2)
                if random.random() > 0.5:
                    w, h = h, w  # Swap for variety
                
                x = random.randint(bounds.x_min + 3, bounds.x_max - w - 3)
                y = random.randint(bounds.y_min + 3, bounds.y_max - h - 3)
                walls.append(Wall(Position(x, y), w, h))
        
        elif self.state.barrier_density == "moderate":
            # Structured walls - create some strategic barriers
            center_x = (bounds.x_min + bounds.x_max) // 2
            center_y = (bounds.y_min + bounds.y_max) // 2
            
            # Cross pattern with gaps
            walls.append(Wall(Position(center_x - 3, center_y), 2, 1))
            walls.append(Wall(Position(center_x + 2, center_y), 2, 1))
            walls.append(Wall(Position(center_x, center_y - 3), 1, 2))
            walls.append(Wall(Position(center_x, center_y + 2), 1, 2))
            
            # Corner obstacles
            walls.append(Wall(Position(bounds.x_min + 3, bounds.y_min + 3), 2, 2))
            walls.append(Wall(Position(bounds.x_max - 5, bounds.y_min + 3), 2, 2))
            walls.append(Wall(Position(bounds.x_min + 3, bounds.y_max - 5), 2, 2))
            walls.append(Wall(Position(bounds.x_max - 5, bounds.y_max - 5), 2, 2))
        
        elif self.state.barrier_density == "dense":
            # Maze-like pattern
            # Horizontal walls
            for i in range(3):
                y = bounds.y_min + 4 + i * 5
                if y < bounds.y_max - 4:
                    gap = random.randint(bounds.x_min + 3, bounds.x_max - 6)
                    # Left segment
                    if gap > bounds.x_min + 4:
                        walls.append(Wall(Position(bounds.x_min + 2, y), gap - bounds.x_min - 4, 1))
                    # Right segment
                    if gap + 3 < bounds.x_max - 2:
                        walls.append(Wall(Position(gap + 3, y), bounds.x_max - gap - 5, 1))
            
            # Vertical walls
            for i in range(2):
                x = bounds.x_min + 5 + i * 7
                if x < bounds.x_max - 4:
                    gap = random.randint(bounds.y_min + 3, bounds.y_max - 6)
                    # Top segment  
                    if gap > bounds.y_min + 4:
                        walls.append(Wall(Position(x, bounds.y_min + 2), 1, gap - bounds.y_min - 4))
                    # Bottom segment
                    if gap + 3 < bounds.y_max - 2:
                        walls.append(Wall(Position(x, gap + 3), 1, bounds.y_max - gap - 5))
        
        self.state.walls[quadrant] = walls
    
    def _get_wall_positions(self, quadrant: int) -> Set[Tuple[int, int]]:
        """Get all positions occupied by walls in a quadrant"""
        positions = set()
        for wall in self.state.walls.get(quadrant, []):
            for pos in wall.get_all_positions():
                positions.add((pos.x, pos.y))
        return positions
    
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
    
    def _update_survival(self, dt: float):
        """Update survival mode specifics"""
        # Shrink arena periodically
        if self.state.elapsed_time >= self.state.next_shrink_time:
            self._shrink_arena()
            self.state.next_shrink_time += self.state.shrink_interval
    
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
                    
                    # Apply combo in high score mode or single player
                    if self.state.mode in [GameMode.HIGH_SCORE, GameMode.SINGLE_PLAYER]:
                        snake.combo += 1
                        snake.combo_timer = 2.0  # 2 second combo window
                        score = int(score * (1 + snake.combo * 0.1))  # 10% bonus per combo
                    
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
    
    async def run_game_loop(self):
        """Main game loop"""
        self.setup_game()
        
        # Send initial state
        await self.broadcast({
            "type": "game_start",
            "state": self.state.to_dict()
        })
        
        tick_rate = 1 / 60  # 60 FPS for updates
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
