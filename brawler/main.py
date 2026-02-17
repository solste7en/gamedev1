"""
Brawler Game - Main Entry Point

A 2v2 Brawl Ball arena game with 4 unique brawlers.
"""

import pygame
from .game import BrawlerGame


def main():
    """Entry point for the brawler game."""
    game = BrawlerGame()
    result = game.run()
    pygame.quit()
    return result


if __name__ == "__main__":
    main()
