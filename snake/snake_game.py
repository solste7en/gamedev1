"""
Snake Game - Main Game Module

A classic snake game with enhanced graphics featuring:
- Realistic snake head with eyes and forked tongue
- Scale pattern on snake body
- Various animals as food (mouse, frog, bug, etc.)
- Sound effects for eating, game over, and more
- Two game modes: Sandbox (free play) and Story (99 levels)
- Player profiles and leaderboard

Controls:
- Arrow keys: Move the snake
- SPACE: Restart/Continue
- ESC: Return to menu
- M: Toggle sound on/off
"""

import pygame
import random
import sys

from .assets import (
    CELL_SIZE, FPS, UP, DOWN, LEFT, RIGHT, BLACK,
    HUD_TOP_HEIGHT, HUD_RIGHT_WIDTH,
    ANIMAL_TYPES, ANIMAL_BASE_SCORES, ANIMAL_SIZES, ANIMAL_HEALTH,
    SMALL_ANIMAL_TYPES, MEDIUM_ANIMAL_TYPES, LARGE_ANIMAL_TYPES, HUGE_ANIMAL_TYPES,
    get_window_dimensions, get_window_dimensions_custom,
    get_grid_dimensions, get_play_area_rect,
    calculate_score, get_difficulty_label, get_health_color
)
from .graphics import (
    draw_snake_head, draw_snake_body_segment, draw_snake_tail,
    draw_animal, draw_walls, draw_game_over, draw_level_complete,
    draw_hud_top, draw_hud_right, draw_play_area_border,
    draw_multi_cell_animal, draw_health_bar
)
from .sounds import SoundManager
from .barriers import BarrierGenerator
from .player import Leaderboard, PlayerProfile
from .story_mode import StoryModeManager, StoryLevel
from .menu import (
    NameInputScreen, ModeSelectScreen, 
    SandboxConfigScreen, StoryLevelSelectScreen
)


class SnakeGame:
    """
    Main Snake Game class.
    Handles game logic, input, and rendering for both Sandbox and Story modes.
    """
    
    def __init__(self, profile, mode='sandbox', config=None):
        """
        Initialize the game.
        
        Args:
            profile: PlayerProfile instance
            mode: 'sandbox' or 'story'
            config: Configuration dict (sandbox settings or story level)
        """
        self.profile = profile
        self.mode = mode
        self.config = config or {}
        
        # Initialize mode-specific settings
        if mode == 'story':
            self._init_story_mode()
        else:
            self._init_sandbox_mode()
        
        # Calculate window dimensions with HUD
        self.window_width = self.play_width + HUD_RIGHT_WIDTH
        self.window_height = self.play_height + HUD_TOP_HEIGHT
        
        # Create window
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption(f"Snake Game - {profile.name}")
        
        # Play area rectangle (x, y, width, height)
        self.play_area_rect = (0, HUD_TOP_HEIGHT, self.play_width, self.play_height)
        
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.fonts = {
            'tiny': pygame.font.Font(None, 20),
            'small': pygame.font.Font(None, 24),
            'medium': pygame.font.Font(None, 32),
            'large': pygame.font.Font(None, 56)
        }
        
        # Initialize sound manager
        self.sound_manager = SoundManager(enabled=True)
        
        # Game state
        self.reset_game()
    
    def _init_sandbox_mode(self):
        """Initialize sandbox mode settings."""
        self.map_size_key = self.config.get('map_size', 'medium')
        self.barrier_key = self.config.get('barriers', 'none')
        self.kids_mode = self.config.get('kids_mode', False)
        
        self.grid_width, self.grid_height = get_grid_dimensions(self.map_size_key)
        self.play_width = self.grid_width * CELL_SIZE
        self.play_height = self.grid_height * CELL_SIZE
        
        # Kids mode: 30% slower speed, 50% score penalty
        if self.kids_mode:
            self.game_speed = int(FPS * 0.7)  # 30% slower
            self.kids_score_multiplier = 0.5  # 50% score penalty
        else:
            self.game_speed = FPS
            self.kids_score_multiplier = 1.0
        
        self.score_multiplier = 1.0  # Handled by calculate_score
        
        self.barrier_generator = BarrierGenerator(
            self.grid_width, self.grid_height, self.barrier_key
        )
        
        self.story_manager = None
        self.level_complete = False
    
    def _init_story_mode(self):
        """Initialize story mode settings."""
        level_num = self.config.get('level', 1)
        
        self.story_manager = StoryModeManager(self.profile)
        self.story_level = self.story_manager.start_level(level_num)
        
        if not self.story_level:
            # Fallback to level 1
            self.story_level = self.story_manager.start_level(1)
        
        self.grid_width = self.story_level.grid_width
        self.grid_height = self.story_level.grid_height
        self.play_width = self.grid_width * CELL_SIZE
        self.play_height = self.grid_height * CELL_SIZE
        
        self.game_speed = self.story_level.speed
        self.score_multiplier = self.story_level.score_multiplier
        
        # Create barrier generator for story mode
        self.barrier_generator = BarrierGenerator(
            self.grid_width, self.grid_height, 'none'
        )
        self.barrier_generator.barrier_config = {
            'pattern': self.story_level.barrier_pattern,
            'wall_count': self.story_level.barrier_count
        }
        
        self.map_size_key = 'custom'
        self.barrier_key = self.story_level.barrier_pattern
        self.level_complete = False
    
    def reset_game(self):
        """Reset the game state to start a new game."""
        # Start snake in the center with 3 segments
        center_x = self.grid_width // 2
        center_y = self.grid_height // 2
        
        self.snake = [
            (center_x, center_y),
            (center_x - 1, center_y),
            (center_x - 2, center_y),
        ]
        
        self.direction = RIGHT
        self.next_direction = RIGHT
        self.score = 0
        self.game_over = False
        self.level_complete = False
        self.food_eaten_count = 0
        self.paused = True  # Start paused so players can get ready
        
        # Generate barriers
        self.walls = self.barrier_generator.generate(self.snake)
        
        self.spawn_food()
        
        # Reset story mode if applicable
        if self.story_manager and self.story_level:
            self.story_manager.food_eaten = 0
            self.story_manager.level_score = 0
        
        # Play start sound
        self.sound_manager.play('start')
        
        # Record game started
        self.profile.record_game()
    
    def spawn_food(self):
        """Spawn food at a random position."""
        # Choose animal type with weighted distribution
        roll = random.random()
        if roll < 0.50:  # 50% chance for small animal (1 health)
            self.food_animal = random.choice(SMALL_ANIMAL_TYPES)
        elif roll < 0.75:  # 25% chance for medium animal (2-3 health)
            self.food_animal = random.choice(MEDIUM_ANIMAL_TYPES)
        elif roll < 0.90:  # 15% chance for large animal (4-5 health)
            self.food_animal = random.choice(LARGE_ANIMAL_TYPES)
        else:  # 10% chance for huge animal (6-8 health)
            self.food_animal = random.choice(HUGE_ANIMAL_TYPES)
        
        # Get animal size info
        animal_cells = ANIMAL_SIZES.get(self.food_animal, [(0, 0)])
        
        # Calculate bounding box needed for this animal
        max_dx = max(c[0] for c in animal_cells)
        max_dy = max(c[1] for c in animal_cells)
        
        attempts = 0
        max_attempts = 1000
        
        while attempts < max_attempts:
            # Generate anchor position that keeps animal in bounds
            anchor_x = random.randint(0, self.grid_width - 1 - max_dx)
            anchor_y = random.randint(0, self.grid_height - 1 - max_dy)
            
            # Calculate all cells this animal would occupy
            food_cells = set()
            for dx, dy in animal_cells:
                food_cells.add((anchor_x + dx, anchor_y + dy))
            
            # Check if all cells are valid (not on snake or walls)
            valid = True
            for cell in food_cells:
                if cell in self.snake or cell in self.walls:
                    valid = False
                    break
            
            if valid:
                self.food_position = (anchor_x, anchor_y)
                self.food_cells = food_cells
                break
            
            attempts += 1
        
        # Fallback to simple small animal if can't place large one
        if attempts >= max_attempts:
            self.food_animal = random.choice(SMALL_ANIMAL_TYPES)
            while attempts < max_attempts + 500:
                self.food_position = (
                    random.randint(0, self.grid_width - 1),
                    random.randint(0, self.grid_height - 1),
                )
                if (self.food_position not in self.snake and 
                    self.food_position not in self.walls):
                    self.food_cells = {self.food_position}
                    break
                attempts += 1
        
        # Set health based on animal type
        self.food_max_health = ANIMAL_HEALTH.get(self.food_animal, 1)
        self.food_health = self.food_max_health
        
        # Calculate score value
        if self.mode == 'story':
            base = ANIMAL_BASE_SCORES.get(self.food_animal, 10)
            self.food_score_value = int(base * self.score_multiplier)
        else:
            base_score = calculate_score(
                self.food_animal, self.map_size_key, self.barrier_key
            )
            # Apply kids mode penalty if active
            if hasattr(self, 'kids_score_multiplier'):
                self.food_score_value = int(base_score * self.kids_score_multiplier)
            else:
                self.food_score_value = base_score
    
    def handle_events(self):
        """Handle input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            
            elif event.type == pygame.KEYDOWN:
                if self.game_over:
                    if event.key == pygame.K_SPACE:
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE:
                        return 'menu'
                
                elif self.level_complete:
                    if event.key == pygame.K_SPACE:
                        return 'next_level'
                    elif event.key == pygame.K_ESCAPE:
                        return 'menu'
                
                elif self.paused:
                    # When paused, any key unpauses (or ESC goes to menu)
                    if event.key == pygame.K_ESCAPE:
                        return 'menu'
                    elif event.key == pygame.K_p or event.key == pygame.K_SPACE:
                        self.paused = False
                    elif event.key == pygame.K_m:
                        self.sound_manager.toggle()
                    # Arrow keys also unpause and set direction
                    elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                        self.paused = False
                        if event.key == pygame.K_UP and self.direction != DOWN:
                            self.next_direction = UP
                        elif event.key == pygame.K_DOWN and self.direction != UP:
                            self.next_direction = DOWN
                        elif event.key == pygame.K_LEFT and self.direction != RIGHT:
                            self.next_direction = LEFT
                        elif event.key == pygame.K_RIGHT and self.direction != LEFT:
                            self.next_direction = RIGHT
                
                else:
                    # Direction controls
                    if event.key == pygame.K_UP and self.direction != DOWN:
                        self.next_direction = UP
                    elif event.key == pygame.K_DOWN and self.direction != UP:
                        self.next_direction = DOWN
                    elif event.key == pygame.K_LEFT and self.direction != RIGHT:
                        self.next_direction = LEFT
                    elif event.key == pygame.K_RIGHT and self.direction != LEFT:
                        self.next_direction = RIGHT
                    elif event.key == pygame.K_p:
                        self.paused = True
                    elif event.key == pygame.K_ESCAPE:
                        return 'menu'
                
                # Sound toggle (works anytime)
                if event.key == pygame.K_m:
                    self.sound_manager.toggle()
        
        return 'continue'
    
    def update(self):
        """Update game state."""
        if self.game_over or self.level_complete or self.paused:
            return
        
        self.direction = self.next_direction
        
        head_x, head_y = self.snake[0]
        dir_x, dir_y = self.direction
        new_head = (head_x + dir_x, head_y + dir_y)
        
        # Check collisions
        if (new_head[0] < 0 or new_head[0] >= self.grid_width or
            new_head[1] < 0 or new_head[1] >= self.grid_height):
            self._handle_death()
            return
        
        if new_head in self.walls:
            self._handle_death()
            return
        
        if new_head in self.snake:
            self._handle_death()
            return
        
        # Move snake
        self.snake.insert(0, new_head)
        
        # Check food collision (check all cells of multi-cell animals)
        food_hit = new_head in self.food_cells
        
        if food_hit:
            self._handle_food_hit()
        else:
            self.snake.pop()
    
    def _handle_death(self):
        """Handle snake death."""
        self.game_over = True
        self.sound_manager.play('game_over')
        
        if self.mode == 'sandbox':
            # Update leaderboard
            leaderboard = Leaderboard()
            rank = leaderboard.add_score(
                self.profile.name, self.score,
                self.map_size_key, self.barrier_key
            )
            self.leaderboard_rank = rank
            self.profile.update_best_sandbox_score(self.score)
        else:
            self.story_manager.fail_level()
            self.profile.record_death()
    
    def _handle_food_hit(self):
        """Handle snake hitting the food animal."""
        # Decrement health
        self.food_health -= 1
        
        # Play hit sound
        self.sound_manager.play('move')  # Use move sound for hit
        
        if self.food_health <= 0:
            # Animal fully consumed
            self._handle_food_eaten()
        # else: animal damaged but not consumed, snake still grows on hit
    
    def _handle_food_eaten(self):
        """Handle food being fully eaten (health depleted)."""
        self.food_eaten_count += 1
        
        if self.mode == 'story':
            actual_score, eaten, required, is_complete = \
                self.story_manager.record_food_eaten(
                    ANIMAL_BASE_SCORES.get(self.food_animal, 10)
                )
            self.score += actual_score
            
            if is_complete:
                self.level_complete = True
                self.completion_data = self.story_manager.complete_level()
                self.sound_manager.play('bonus')
                return
        else:
            self.score += self.food_score_value
        
        self.sound_manager.play_eat_sound(self.food_animal)
        self.spawn_food()
    
    def draw(self):
        """Draw the game state."""
        self.screen.fill(BLACK)
        
        # Draw play area background
        play_x, play_y, play_w, play_h = self.play_area_rect
        pygame.draw.rect(self.screen, (10, 10, 10), self.play_area_rect)
        
        # Draw grid
        self._draw_grid()
        
        # Draw walls
        for wall_x, wall_y in self.walls:
            from .graphics import draw_wall
            draw_wall(self.screen, 
                     wall_x * CELL_SIZE + play_x,
                     wall_y * CELL_SIZE + play_y, 
                     CELL_SIZE)
        
        # Draw food (with health bar for multi-cell animals)
        food_screen_x = self.food_position[0] * CELL_SIZE + play_x
        food_screen_y = self.food_position[1] * CELL_SIZE + play_y
        
        if self.food_max_health > 1:
            # Multi-cell animal with health bar
            draw_multi_cell_animal(
                self.screen, self.food_position[0], self.food_position[1],
                CELL_SIZE, self.food_animal,
                self.food_health, self.food_max_health,
                play_offset=(play_x, play_y)
            )
        else:
            # Single-cell animal
            draw_animal(self.screen, food_screen_x, food_screen_y, CELL_SIZE, self.food_animal)
        
        # Draw snake
        self._draw_snake()
        
        # Draw play area border
        draw_play_area_border(self.screen, self.play_area_rect)
        
        # Draw HUD
        self._draw_hud()
        
        # Draw overlays
        if self.game_over:
            draw_game_over(
                self.screen, self.score,
                self.fonts['large'], self.fonts['medium'],
                (self.window_width, self.window_height),
                self.play_area_rect
            )
        elif self.level_complete and self.mode == 'story':
            draw_level_complete(
                self.screen, self.fonts,
                self.completion_data['level'],
                self.completion_data['level_score'],
                self.completion_data['completion_bonus'],
                self.completion_data['total_score'],
                self.play_area_rect
            )
        elif self.paused:
            self._draw_paused()
        
        pygame.display.flip()
    
    def _draw_paused(self):
        """Draw the pause overlay."""
        play_x, play_y, play_w, play_h = self.play_area_rect
        center_x = play_x + play_w // 2
        center_y = play_y + play_h // 2
        
        # Semi-transparent overlay
        overlay = pygame.Surface((self.window_width, self.window_height))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Pause text
        pause_text = self.fonts['large'].render("PAUSED", True, (255, 255, 100))
        text_rect = pause_text.get_rect(center=(center_x, center_y - 30))
        self.screen.blit(pause_text, text_rect)
        
        # Instructions
        hint1 = self.fonts['small'].render("Press P, SPACE, or any arrow key to continue", True, (255, 255, 255))
        hint1_rect = hint1.get_rect(center=(center_x, center_y + 20))
        self.screen.blit(hint1, hint1_rect)
        
        hint2 = self.fonts['small'].render("ESC to return to menu", True, (180, 180, 180))
        hint2_rect = hint2.get_rect(center=(center_x, center_y + 50))
        self.screen.blit(hint2, hint2_rect)
        
        # Show kids mode indicator if active
        if hasattr(self, 'kids_mode') and self.kids_mode:
            kids_text = self.fonts['tiny'].render("Kids Mode: ON (Speed -30%, Score -50%)", True, (150, 200, 255))
            kids_rect = kids_text.get_rect(center=(center_x, center_y + 85))
            self.screen.blit(kids_text, kids_rect)
    
    def _draw_grid(self):
        """Draw subtle grid pattern."""
        grid_color = (20, 20, 20)
        play_x, play_y, play_w, play_h = self.play_area_rect
        
        for x in range(0, play_w + 1, CELL_SIZE):
            pygame.draw.line(self.screen, grid_color,
                           (play_x + x, play_y),
                           (play_x + x, play_y + play_h))
        
        for y in range(0, play_h + 1, CELL_SIZE):
            pygame.draw.line(self.screen, grid_color,
                           (play_x, play_y + y),
                           (play_x + play_w, play_y + y))
    
    def _draw_snake(self):
        """Draw the snake."""
        play_x, play_y = self.play_area_rect[0], self.play_area_rect[1]
        total_segments = len(self.snake)
        
        for i in range(total_segments - 1, -1, -1):
            segment = self.snake[i]
            x = segment[0] * CELL_SIZE + play_x
            y = segment[1] * CELL_SIZE + play_y
            
            if i == 0:
                draw_snake_head(self.screen, x, y, self.direction, CELL_SIZE)
            elif i == total_segments - 1:
                prev_segment = self.snake[i - 1]
                tail_dir = (
                    prev_segment[0] - segment[0],
                    prev_segment[1] - segment[1]
                )
                draw_snake_tail(self.screen, x, y, CELL_SIZE, tail_dir)
            else:
                draw_snake_body_segment(self.screen, x, y, CELL_SIZE, i, total_segments)
    
    def _draw_hud(self):
        """Draw all HUD elements."""
        # Get difficulty label
        if self.mode == 'story':
            difficulty = self.story_level.get_description()
        else:
            difficulty = get_difficulty_label(self.map_size_key, self.barrier_key)
        
        # Top HUD
        draw_hud_top(
            self.screen, self.fonts,
            self.profile.name, self.score, difficulty,
            self.sound_manager.enabled,
            self.play_width, HUD_TOP_HEIGHT
        )
        
        # Right HUD
        extra_info = None
        if self.mode == 'story' and self.story_level:
            extra_info = {
                'level': self.story_level.level,
                'food_progress': (
                    self.story_manager.food_eaten,
                    self.story_level.food_required
                ),
                'multiplier': f"x{self.story_level.score_multiplier:.2f}"
            }
        
        draw_hud_right(
            self.screen, self.fonts,
            self.food_animal, self.food_score_value,
            len(self.snake),
            self.play_width, self.play_height,
            HUD_RIGHT_WIDTH, HUD_TOP_HEIGHT,
            extra_info,
            self.food_health, self.food_max_health
        )
    
    def run(self):
        """
        Main game loop.
        
        Returns:
            str: 'menu', 'next_level', or 'quit'
        """
        while True:
            result = self.handle_events()
            
            if result == 'quit':
                self.sound_manager.cleanup()
                return 'quit'
            elif result == 'menu':
                return 'menu'
            elif result == 'next_level':
                if self.mode == 'story':
                    return 'next_level'
            
            self.update()
            self.draw()
            self.clock.tick(self.game_speed)


def main():
    """Entry point for the game."""
    pygame.init()
    
    print("=" * 50)
    print("SNAKE GAME - Enhanced Edition")
    print("=" * 50)
    print("\nStarting game...")
    
    # Main game loop
    current_profile = None
    
    while True:
        # Name input (if no profile)
        if current_profile is None:
            name_screen = NameInputScreen()
            player_name = name_screen.run()
            
            if player_name is None:
                break
            
            current_profile = PlayerProfile(player_name)
        
        # Mode selection
        mode_screen = ModeSelectScreen(current_profile.name)
        mode_result = mode_screen.run()
        
        if mode_result is None or mode_result.get('action') == 'quit':
            break
        
        action = mode_result.get('action')
        profile = mode_result.get('profile', current_profile)
        
        if action == 'sandbox':
            # Sandbox config
            config_screen = SandboxConfigScreen(profile)
            config = config_screen.run()
            
            if config is None:
                break
            elif config == 'back':
                continue
            
            # Play sandbox
            game = SnakeGame(profile, mode='sandbox', config=config)
            result = game.run()
            
            if result == 'quit':
                break
            # 'menu' continues the loop
        
        elif action == 'story':
            # Story level select
            level_screen = StoryLevelSelectScreen(profile)
            level_result = level_screen.run()
            
            if level_result is None:
                break
            elif level_result == 'back':
                continue
            
            # Play story mode levels
            current_level = level_result['level']
            
            while True:
                config = {'level': current_level}
                game = SnakeGame(profile, mode='story', config=config)
                result = game.run()
                
                if result == 'quit':
                    pygame.quit()
                    sys.exit()
                elif result == 'menu':
                    break
                elif result == 'next_level':
                    current_level = min(99, current_level + 1)
                    if current_level > profile.get_highest_level():
                        break
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
