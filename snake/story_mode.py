"""
Story Mode module for the Snake Game.
Handles level progression from level 1 to 99 with increasing difficulty.
"""

from .assets import CELL_SIZE


class StoryLevel:
    """
    Represents a single story mode level configuration.
    """
    
    def __init__(self, level_number):
        """
        Generate level configuration based on level number.
        
        Args:
            level_number: Level number (1-99)
        """
        self.level = level_number
        self._calculate_parameters()
    
    def _calculate_parameters(self):
        """Calculate level parameters based on level number."""
        level = self.level
        
        # Map size decreases as levels increase (larger number = harder)
        # Levels 1-20: Large map
        # Levels 21-40: Medium-large
        # Levels 41-60: Medium
        # Levels 61-80: Medium-small
        # Levels 81-99: Small
        
        if level <= 20:
            self.grid_width = 35 - (level // 5)  # 35 down to 31
            self.grid_height = 22 - (level // 7)  # 22 down to 19
        elif level <= 40:
            self.grid_width = 30 - ((level - 20) // 4)  # 30 down to 25
            self.grid_height = 18 - ((level - 20) // 7)  # 18 down to 15
        elif level <= 60:
            self.grid_width = 25 - ((level - 40) // 5)  # 25 down to 21
            self.grid_height = 15 - ((level - 40) // 10)  # 15 down to 13
        elif level <= 80:
            self.grid_width = 20 - ((level - 60) // 7)  # 20 down to 17
            self.grid_height = 13 - ((level - 60) // 15)  # 13 down to 11
        else:  # 81-99
            self.grid_width = 17 - ((level - 80) // 10)  # 17 down to 15
            self.grid_height = 11  # Fixed at 11
        
        # Minimum sizes
        self.grid_width = max(12, self.grid_width)
        self.grid_height = max(10, self.grid_height)
        
        # Barrier density increases with level
        if level <= 10:
            self.barrier_pattern = 'none'
            self.barrier_count = 0
        elif level <= 25:
            self.barrier_pattern = 'scattered'
            self.barrier_count = 2 + (level - 10) // 5
        elif level <= 50:
            self.barrier_pattern = 'structured'
            self.barrier_count = 4 + (level - 25) // 5
        elif level <= 75:
            self.barrier_pattern = 'moderate_maze'
            self.barrier_count = 6 + (level - 50) // 4
        else:
            self.barrier_pattern = 'maze'
            self.barrier_count = 10 + (level - 75) // 3
        
        # Food requirement to complete level
        # Starts at 5, increases gradually
        self.food_required = 5 + (level // 5)
        self.food_required = min(30, self.food_required)  # Cap at 30
        
        # Game speed (FPS) - increases with level
        # Level 1: 8 FPS, Level 99: 15 FPS
        self.speed = 8 + (level // 15)
        self.speed = min(15, self.speed)
        
        # Score multiplier based on level
        self.score_multiplier = 1.0 + (level * 0.02)  # +2% per level
        
        # Bonus points for completing level
        self.completion_bonus = level * 50
    
    def get_window_size(self):
        """Get the window size in pixels (including HUD)."""
        play_width = self.grid_width * CELL_SIZE
        play_height = self.grid_height * CELL_SIZE
        # Add HUD space
        return (play_width + 200, play_height + 60)
    
    def get_play_area_size(self):
        """Get the play area size in pixels."""
        return (self.grid_width * CELL_SIZE, self.grid_height * CELL_SIZE)
    
    def get_description(self):
        """Get a description of this level."""
        if self.level <= 10:
            difficulty = "Tutorial"
        elif self.level <= 25:
            difficulty = "Easy"
        elif self.level <= 50:
            difficulty = "Medium"
        elif self.level <= 75:
            difficulty = "Hard"
        elif self.level <= 90:
            difficulty = "Very Hard"
        else:
            difficulty = "Extreme"
        
        return f"Level {self.level} - {difficulty}"
    
    def get_level_info(self):
        """Get detailed level information."""
        return {
            'level': self.level,
            'grid_size': f"{self.grid_width}x{self.grid_height}",
            'food_required': self.food_required,
            'speed': self.speed,
            'multiplier': f"x{self.score_multiplier:.2f}",
            'completion_bonus': self.completion_bonus
        }


class StoryModeManager:
    """
    Manages story mode progression and level generation.
    """
    
    MAX_LEVEL = 99
    
    def __init__(self, player_profile):
        """
        Initialize story mode manager.
        
        Args:
            player_profile: PlayerProfile instance
        """
        self.profile = player_profile
        self.current_level = None
        self.food_eaten = 0
        self.level_score = 0
    
    def start_level(self, level_number):
        """
        Start a specific level.
        
        Args:
            level_number: Level to start (1-99)
            
        Returns:
            StoryLevel: Level configuration, or None if can't play
        """
        if not self.profile.can_play_level(level_number):
            return None
        
        if level_number < 1 or level_number > self.MAX_LEVEL:
            return None
        
        self.current_level = StoryLevel(level_number)
        self.food_eaten = 0
        self.level_score = 0
        
        return self.current_level
    
    def record_food_eaten(self, base_score):
        """
        Record food eaten and calculate score.
        
        Args:
            base_score: Base score for the food item
            
        Returns:
            tuple: (actual_score, food_eaten, food_required, is_complete)
        """
        if not self.current_level:
            return (base_score, 0, 0, False)
        
        # Apply level multiplier
        actual_score = int(base_score * self.current_level.score_multiplier)
        self.level_score += actual_score
        self.food_eaten += 1
        
        is_complete = self.food_eaten >= self.current_level.food_required
        
        return (
            actual_score,
            self.food_eaten,
            self.current_level.food_required,
            is_complete
        )
    
    def complete_level(self):
        """
        Complete the current level.
        
        Returns:
            dict: Completion summary
        """
        if not self.current_level:
            return None
        
        # Add completion bonus
        bonus = self.current_level.completion_bonus
        total_score = self.level_score + bonus
        
        # Save progress
        is_new = self.profile.complete_level(
            self.current_level.level,
            total_score,
            self.food_eaten
        )
        
        summary = {
            'level': self.current_level.level,
            'food_eaten': self.food_eaten,
            'level_score': self.level_score,
            'completion_bonus': bonus,
            'total_score': total_score,
            'is_new_completion': is_new,
            'next_level': min(self.current_level.level + 1, self.MAX_LEVEL)
        }
        
        return summary
    
    def fail_level(self):
        """Record a failed level attempt."""
        self.profile.record_death()
        
        return {
            'level': self.current_level.level if self.current_level else 0,
            'food_eaten': self.food_eaten,
            'score_lost': self.level_score
        }
    
    def get_progress_summary(self):
        """Get player's overall story progress."""
        return {
            'current_level': self.profile.get_current_level(),
            'highest_level': self.profile.get_highest_level(),
            'total_score': self.profile.get_total_story_score(),
            'completion_percent': (self.profile.get_highest_level() - 1) / self.MAX_LEVEL * 100
        }


def get_level_preview(level_number):
    """
    Get a preview of level parameters without starting it.
    
    Args:
        level_number: Level number (1-99)
        
    Returns:
        dict: Level parameters
    """
    if level_number < 1 or level_number > 99:
        return None
    
    level = StoryLevel(level_number)
    return level.get_level_info()
