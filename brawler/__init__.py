"""
Brawler - A Brawl Ball style arena game.

Features 4 unique brawlers (Colt, Shelly, Piper, Edgar) in 2v2 matches.
"""

from .game import BrawlerGame
from .brawlers import Colt, Shelly, Piper, Edgar, BRAWLER_CLASSES

__all__ = ['BrawlerGame', 'Colt', 'Shelly', 'Piper', 'Edgar', 'BRAWLER_CLASSES']
