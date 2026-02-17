"""
Player module for the Snake Game.
Handles player profiles, save data, and leaderboard management.
"""

import json
import os
from datetime import datetime


# Save file locations
SAVE_DIR = os.path.join(os.path.dirname(__file__), 'saves')
LEADERBOARD_FILE = os.path.join(SAVE_DIR, 'leaderboard.json')
PROFILES_DIR = os.path.join(SAVE_DIR, 'profiles')


def ensure_save_directories():
    """Create save directories if they don't exist."""
    os.makedirs(SAVE_DIR, exist_ok=True)
    os.makedirs(PROFILES_DIR, exist_ok=True)


class Leaderboard:
    """
    Manages the sandbox mode leaderboard.
    Stores top 10 scores with player names.
    """
    
    MAX_ENTRIES = 10
    
    def __init__(self):
        """Initialize and load the leaderboard."""
        ensure_save_directories()
        self.entries = []
        self.load()
    
    def load(self):
        """Load leaderboard from file."""
        try:
            if os.path.exists(LEADERBOARD_FILE):
                with open(LEADERBOARD_FILE, 'r') as f:
                    data = json.load(f)
                    self.entries = data.get('entries', [])
        except (json.JSONDecodeError, IOError):
            self.entries = []
    
    def save(self):
        """Save leaderboard to file."""
        try:
            with open(LEADERBOARD_FILE, 'w') as f:
                json.dump({'entries': self.entries}, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save leaderboard: {e}")
    
    def add_score(self, player_name, score, map_size, barriers):
        """
        Add a score to the leaderboard if it qualifies.
        
        Args:
            player_name: Name of the player
            score: Score achieved
            map_size: Map size setting used
            barriers: Barrier setting used
            
        Returns:
            int: Rank achieved (1-10), or 0 if didn't make the board
        """
        entry = {
            'name': player_name,
            'score': score,
            'map_size': map_size,
            'barriers': barriers,
            'date': datetime.now().isoformat()
        }
        
        # Find position to insert
        rank = 0
        for i, existing in enumerate(self.entries):
            if score > existing['score']:
                rank = i + 1
                break
        else:
            if len(self.entries) < self.MAX_ENTRIES:
                rank = len(self.entries) + 1
        
        if rank > 0:
            self.entries.insert(rank - 1, entry)
            # Keep only top 10
            self.entries = self.entries[:self.MAX_ENTRIES]
            self.save()
        
        return rank
    
    def get_entries(self):
        """Get all leaderboard entries."""
        return self.entries.copy()
    
    def is_high_score(self, score):
        """Check if a score would make the leaderboard."""
        if len(self.entries) < self.MAX_ENTRIES:
            return True
        return score > self.entries[-1]['score']


class PlayerProfile:
    """
    Manages a player's profile and story mode progress.
    """
    
    def __init__(self, name):
        """
        Initialize or load a player profile.
        
        Args:
            name: Player's name (used as identifier)
        """
        ensure_save_directories()
        self.name = name
        self.filename = self._get_profile_filename(name)
        
        # Default profile data
        self.data = {
            'name': name,
            'created': datetime.now().isoformat(),
            'story_progress': {
                'current_level': 1,
                'highest_level': 1,
                'total_score': 0,
                'levels_completed': {}
            },
            'stats': {
                'games_played': 0,
                'total_food_eaten': 0,
                'total_deaths': 0,
                'best_sandbox_score': 0
            }
        }
        
        self.load()
    
    def _get_profile_filename(self, name):
        """Get the filename for a player profile."""
        # Sanitize name for filename
        safe_name = "".join(c for c in name if c.isalnum() or c in ('_', '-'))
        safe_name = safe_name.lower()[:20]  # Limit length
        if not safe_name:
            safe_name = "player"
        return os.path.join(PROFILES_DIR, f"{safe_name}.json")
    
    def load(self):
        """Load profile from file if it exists."""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as f:
                    saved_data = json.load(f)
                    # Merge with defaults to handle new fields
                    self._merge_data(saved_data)
        except (json.JSONDecodeError, IOError):
            pass  # Use defaults
    
    def _merge_data(self, saved_data):
        """Merge saved data with defaults, preserving saved values."""
        self.data['name'] = saved_data.get('name', self.name)
        self.data['created'] = saved_data.get('created', self.data['created'])
        
        # Story progress
        saved_progress = saved_data.get('story_progress', {})
        self.data['story_progress']['current_level'] = saved_progress.get('current_level', 1)
        self.data['story_progress']['highest_level'] = saved_progress.get('highest_level', 1)
        self.data['story_progress']['total_score'] = saved_progress.get('total_score', 0)
        self.data['story_progress']['levels_completed'] = saved_progress.get('levels_completed', {})
        
        # Stats
        saved_stats = saved_data.get('stats', {})
        self.data['stats']['games_played'] = saved_stats.get('games_played', 0)
        self.data['stats']['total_food_eaten'] = saved_stats.get('total_food_eaten', 0)
        self.data['stats']['total_deaths'] = saved_stats.get('total_deaths', 0)
        self.data['stats']['best_sandbox_score'] = saved_stats.get('best_sandbox_score', 0)
    
    def save(self):
        """Save profile to file."""
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.data, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save profile: {e}")
    
    # Story mode methods
    
    def get_current_level(self):
        """Get the current story mode level."""
        return self.data['story_progress']['current_level']
    
    def get_highest_level(self):
        """Get the highest level reached."""
        return self.data['story_progress']['highest_level']
    
    def get_total_story_score(self):
        """Get total score accumulated in story mode."""
        return self.data['story_progress']['total_score']
    
    def complete_level(self, level, score, food_eaten):
        """
        Mark a level as completed.
        
        Args:
            level: Level number completed
            score: Score achieved on this level
            food_eaten: Number of food items eaten
            
        Returns:
            bool: True if this was a new level completion
        """
        level_key = str(level)
        is_new = level_key not in self.data['story_progress']['levels_completed']
        
        # Update level data
        existing = self.data['story_progress']['levels_completed'].get(level_key, {})
        best_score = max(score, existing.get('best_score', 0))
        
        self.data['story_progress']['levels_completed'][level_key] = {
            'best_score': best_score,
            'completed_at': datetime.now().isoformat()
        }
        
        # Update progress
        self.data['story_progress']['total_score'] += score
        
        if level >= self.data['story_progress']['highest_level']:
            self.data['story_progress']['highest_level'] = level + 1
            self.data['story_progress']['current_level'] = level + 1
        
        # Update stats
        self.data['stats']['total_food_eaten'] += food_eaten
        
        self.save()
        return is_new
    
    def record_death(self):
        """Record a death in stats."""
        self.data['stats']['total_deaths'] += 1
        self.save()
    
    def record_game(self):
        """Record a game played."""
        self.data['stats']['games_played'] += 1
        self.save()
    
    def update_best_sandbox_score(self, score):
        """Update best sandbox score if this is higher."""
        if score > self.data['stats']['best_sandbox_score']:
            self.data['stats']['best_sandbox_score'] = score
            self.save()
            return True
        return False
    
    def can_play_level(self, level):
        """Check if player can play a specific level."""
        return level <= self.data['story_progress']['highest_level']
    
    def get_level_best_score(self, level):
        """Get best score for a specific level."""
        level_key = str(level)
        level_data = self.data['story_progress']['levels_completed'].get(level_key, {})
        return level_data.get('best_score', 0)


def get_existing_profiles():
    """
    Get list of existing player profile names.
    
    Returns:
        List of player names with saved profiles
    """
    ensure_save_directories()
    profiles = []
    
    try:
        for filename in os.listdir(PROFILES_DIR):
            if filename.endswith('.json'):
                filepath = os.path.join(PROFILES_DIR, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        profiles.append(data.get('name', filename[:-5]))
                except (json.JSONDecodeError, IOError):
                    pass
    except OSError:
        pass
    
    return profiles
