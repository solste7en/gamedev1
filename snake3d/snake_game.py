"""
Snake3D - Main Game Module

A Stardew Valley-style 2.5D snake game with oblique projection graphics.
"""

import pygame
import random
import sys

from .assets import (
    CELL_SIZE, DEPTH_HEIGHT, FPS, UP, DOWN, LEFT, RIGHT, BLACK,
    HUD_TOP_HEIGHT, HUD_RIGHT_WIDTH,
    ANIMAL_TYPES, ANIMAL_BASE_SCORES, ANIMAL_SIZES, ANIMAL_HEALTH,
    SMALL_ANIMAL_TYPES, MEDIUM_ANIMAL_TYPES, LARGE_ANIMAL_TYPES, HUGE_ANIMAL_TYPES,
    MAP_SIZES, BARRIER_DENSITIES,
    calculate_score, get_difficulty_label, get_health_color
)
from .graphics import (
    draw_floor, draw_walls, draw_snake, draw_food, draw_multi_cell_food,
    draw_hud_top, draw_hud_right, draw_game_over, draw_level_complete
)
from .oblique import grid_to_screen, calculate_window_size

# Import shared modules from snake package
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from snake.sounds import SoundManager
from snake.barriers import BarrierGenerator
from snake.player import Leaderboard, PlayerProfile
from snake.story_mode import StoryModeManager, StoryLevel


class Snake3DGame:
    """
    Stardew Valley-style 2.5D Snake Game with oblique projection.
    """
    
    def __init__(self, profile, mode='sandbox', config=None):
        """
        Initialize the game.
        
        Args:
            profile: PlayerProfile instance
            mode: 'sandbox' or 'story'
            config: Configuration dict
        """
        self.profile = profile
        self.mode = mode
        self.config = config or {}
        
        # Initialize mode-specific settings
        if mode == 'story':
            self._init_story_mode()
        else:
            self._init_sandbox_mode()
        
        # Calculate window dimensions for oblique view
        window_w, window_h, self.origin_x, self.origin_y = calculate_window_size(
            self.grid_width, self.grid_height,
            CELL_SIZE, DEPTH_HEIGHT,
            padding=10, hud_width=HUD_RIGHT_WIDTH, hud_top=HUD_TOP_HEIGHT
        )
        
        self.window_width = window_w
        self.window_height = window_h
        
        # Play area dimensions
        self.play_width = self.grid_width * CELL_SIZE + 20  # Grid + padding
        self.play_height = self.grid_height * CELL_SIZE + DEPTH_HEIGHT + 20
        
        # Create window
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption(f"Snake 3D - {profile.name}")
        
        self.play_area_rect = (0, HUD_TOP_HEIGHT, self.play_width, self.play_height)
        
        self.clock = pygame.time.Clock()
        
        # Fonts
        self.fonts = {
            'tiny': pygame.font.Font(None, 18),
            'small': pygame.font.Font(None, 22),
            'medium': pygame.font.Font(None, 28),
            'large': pygame.font.Font(None, 48)
        }
        
        # Sound manager
        self.sound_manager = SoundManager(enabled=True)
        
        # Game state
        self.reset_game()
    
    def _init_sandbox_mode(self):
        """Initialize sandbox mode settings."""
        self.map_size_key = self.config.get('map_size', 'medium')
        self.barrier_key = self.config.get('barriers', 'none')
        self.kids_mode = self.config.get('kids_mode', False)
        
        map_config = MAP_SIZES.get(self.map_size_key, MAP_SIZES['medium'])
        self.grid_width = map_config['width']
        self.grid_height = map_config['height']
        
        # Kids mode: 30% slower speed, 50% score penalty
        if self.kids_mode:
            self.game_speed = int(FPS * 0.7)  # 30% slower
            self.kids_score_multiplier = 0.5  # 50% score penalty
        else:
            self.game_speed = FPS
            self.kids_score_multiplier = 1.0
        
        self.barrier_generator = BarrierGenerator(
            self.grid_width, self.grid_height, self.barrier_key
        )
        
        self.difficulty_label = get_difficulty_label(self.map_size_key, self.barrier_key)
        
        self.story_manager = None
        self.story_level = None
        self.leaderboard_rank = 0
    
    def _init_story_mode(self):
        """Initialize story mode settings."""
        level_num = self.config.get('level', 1)
        
        self.story_manager = StoryModeManager(self.profile)
        self.story_level = StoryLevel(level_num)
        
        self.grid_width = self.story_level.grid_width
        self.grid_height = self.story_level.grid_height
        
        self.game_speed = self.story_level.speed
        self.score_multiplier = self.story_level.score_multiplier
        
        self.barrier_generator = BarrierGenerator(
            self.grid_width, self.grid_height, 'none'
        )
        self.barrier_generator.barrier_config = {
            'pattern': self.story_level.barrier_pattern,
            'wall_count': self.story_level.barrier_count
        }
        
        self.map_size_key = 'custom'
        self.barrier_key = self.story_level.barrier_pattern
        self.difficulty_label = f"Level {level_num}"
        self.level_complete = False
    
    def reset_game(self):
        """Reset game state."""
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
        
        if self.story_manager and self.story_level:
            self.story_manager.food_eaten = 0
            self.story_manager.level_score = 0
        
        self.sound_manager.play('start')
        self.profile.record_game()
    
    def spawn_food(self):
        """Spawn food at random position."""
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
        
        animal_cells = ANIMAL_SIZES.get(self.food_animal, [(0, 0)])
        max_dx = max(c[0] for c in animal_cells)
        max_dy = max(c[1] for c in animal_cells)
        
        attempts = 0
        max_attempts = 1000
        
        while attempts < max_attempts:
            anchor_x = random.randint(0, self.grid_width - 1 - max_dx)
            anchor_y = random.randint(0, self.grid_height - 1 - max_dy)
            
            food_cells = set()
            for dx, dy in animal_cells:
                food_cells.add((anchor_x + dx, anchor_y + dy))
            
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
        
        self.food_max_health = ANIMAL_HEALTH.get(self.food_animal, 1)
        self.food_health = self.food_max_health
        
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
                    elif event.key == pygame.K_m:
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
        
        # Check food
        if new_head in self.food_cells:
            self._handle_food_hit()
        else:
            self.snake.pop()
    
    def _handle_death(self):
        """Handle snake death."""
        self.game_over = True
        self.sound_manager.play('game_over')
        
        if self.mode == 'sandbox':
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
        """Handle snake hitting food."""
        self.food_health -= 1
        self.sound_manager.play('move')
        
        if self.food_health <= 0:
            self._handle_food_eaten()
    
    def _handle_food_eaten(self):
        """Handle food being fully eaten."""
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
        
        # Draw floor with grass tiles
        draw_floor(self.screen, self.grid_width, self.grid_height,
                   CELL_SIZE, DEPTH_HEIGHT, self.origin_x, self.origin_y)
        
        # Collect all drawable objects for depth sorting (by Y position)
        draw_items = []
        
        # Add walls
        for wall_x, wall_y in self.walls:
            draw_items.append(('wall', wall_x, wall_y))
        
        # Add food (all cells for multi-cell animals)
        for cell in self.food_cells:
            draw_items.append(('food', cell[0], cell[1]))
        
        # Add snake segments
        for idx, (sx, sy) in enumerate(self.snake):
            draw_items.append(('snake', sx, sy, idx))
        
        # Sort by Y (draw back rows first)
        draw_items.sort(key=lambda item: item[2])
        
        # Draw walls separately (they need Y sorting among themselves)
        draw_walls(self.screen, self.walls, CELL_SIZE, DEPTH_HEIGHT,
                   self.origin_x, self.origin_y)
        
        # Draw food
        if self.food_max_health > 1:
            draw_multi_cell_food(self.screen, self.food_position[0], self.food_position[1],
                                CELL_SIZE, DEPTH_HEIGHT, self.origin_x, self.origin_y,
                                self.food_animal, self.food_health, self.food_max_health)
        else:
            draw_food(self.screen, self.food_position[0], self.food_position[1],
                     CELL_SIZE, DEPTH_HEIGHT, self.origin_x, self.origin_y,
                     self.food_animal)
        
        # Draw snake (handles its own sorting)
        draw_snake(self.screen, self.snake, CELL_SIZE, DEPTH_HEIGHT,
                  self.origin_x, self.origin_y, self.direction)
        
        # Draw HUD
        draw_hud_top(self.screen, self.fonts, self.profile.name,
                     self.score, self.difficulty_label,
                     self.sound_manager.enabled, self.play_width, HUD_TOP_HEIGHT)
        
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
        
        draw_hud_right(self.screen, self.fonts,
                       self.food_animal, self.food_score_value,
                       len(self.snake),
                       self.play_width, self.play_height,
                       HUD_RIGHT_WIDTH, HUD_TOP_HEIGHT,
                       extra_info,
                       self.food_health, self.food_max_health)
        
        # Draw overlays
        if self.game_over:
            draw_game_over(self.screen, self.score,
                          self.fonts['large'], self.fonts['small'],
                          (self.window_width, self.window_height),
                          self.play_area_rect)
        
        elif self.level_complete and hasattr(self, 'completion_data'):
            draw_level_complete(self.screen, self.fonts,
                               self.story_level.level,
                               self.completion_data['level_score'],
                               self.completion_data['bonus'],
                               self.completion_data['total'],
                               self.play_area_rect)
        
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
        hint1_rect = hint1.get_rect(center=(center_x, center_y + 15))
        self.screen.blit(hint1, hint1_rect)
        
        hint2 = self.fonts['small'].render("ESC to return to menu", True, (180, 180, 180))
        hint2_rect = hint2.get_rect(center=(center_x, center_y + 40))
        self.screen.blit(hint2, hint2_rect)
        
        # Show kids mode indicator if active
        if hasattr(self, 'kids_mode') and self.kids_mode:
            kids_text = self.fonts['tiny'].render("Kids Mode: ON (Speed -30%, Score -50%)", True, (150, 200, 255))
            kids_rect = kids_text.get_rect(center=(center_x, center_y + 70))
            self.screen.blit(kids_text, kids_rect)
    
    def run(self):
        """Main game loop."""
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
    """Entry point for standalone Snake3D game."""
    pygame.init()
    
    # Import menu classes from snake package
    from snake.menu import (
        NameInputScreen, ModeSelectScreen,
        SandboxConfigScreen, StoryLevelSelectScreen
    )
    
    print("=" * 50)
    print("SNAKE 3D - Stardew Valley Style")
    print("=" * 50)
    
    # Get player name
    name_screen = NameInputScreen()
    player_name = name_screen.run()
    
    if player_name is None:
        pygame.quit()
        return
    
    while True:
        # Mode selection
        mode_screen = ModeSelectScreen(player_name)
        result = mode_screen.run()
        
        if result is None or result.get('action') == 'quit':
            break
        
        profile = result.get('profile')
        action = result.get('action')
        
        if action == 'sandbox':
            # Sandbox config
            config_screen = SandboxConfigScreen(profile)
            config_result = config_screen.run()
            
            if config_result == 'quit':
                break
            elif config_result == 'back':
                continue
            
            # Run game
            game = Snake3DGame(profile, 'sandbox', config_result)
            game_result = game.run()
            
            if game_result == 'quit':
                break
        
        elif action == 'story':
            # Story level select
            level_screen = StoryLevelSelectScreen(profile)
            level_result = level_screen.run()
            
            if level_result is None:
                break
            elif level_result == 'back':
                continue
            
            # Run story levels
            current_level = level_result.get('level', 1)
            
            while current_level <= 99:
                config = {'level': current_level}
                game = Snake3DGame(profile, 'story', config)
                game_result = game.run()
                
                if game_result == 'quit':
                    pygame.quit()
                    return
                elif game_result == 'menu':
                    break
                elif game_result == 'next_level':
                    current_level += 1
                    profile.complete_level(current_level - 1)
    
    pygame.quit()


if __name__ == "__main__":
    main()
