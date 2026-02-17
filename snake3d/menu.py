"""
Menu module for Snake3D.

Wraps the snake menu classes with Snake3D branding.
"""

# Re-export menu classes from snake package with same interface
# This allows Snake3D to use the same menu flow

import pygame
import sys
import os

# Add parent directory to path for snake imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from snake.menu import (
    NameInputScreen as BaseNameInputScreen,
    ModeSelectScreen as BaseModeSelectScreen,
    SandboxConfigScreen as BaseSandboxConfigScreen,
    StoryLevelSelectScreen as BaseStoryLevelSelectScreen
)
from snake.player import Leaderboard, PlayerProfile, get_existing_profiles


class NameInputScreen(BaseNameInputScreen):
    """Name input screen for Snake3D."""
    
    def __init__(self):
        super().__init__()
        pygame.display.set_caption("Snake 3D - Enter Your Name")


class ModeSelectScreen(BaseModeSelectScreen):
    """Mode selection screen for Snake3D."""
    
    def __init__(self, player_name):
        super().__init__(player_name)
        pygame.display.set_caption(f"Snake 3D - {player_name}")


class SandboxConfigScreen(BaseSandboxConfigScreen):
    """Sandbox configuration screen for Snake3D."""
    
    def __init__(self, profile):
        super().__init__(profile)
        pygame.display.set_caption("Snake 3D - Sandbox Setup")


class StoryLevelSelectScreen(BaseStoryLevelSelectScreen):
    """Story level selection screen for Snake3D."""
    
    def __init__(self, profile):
        super().__init__(profile)
        pygame.display.set_caption("Snake 3D - Story Mode")
