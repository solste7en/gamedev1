"""
Game Launcher - Main Entry Point

Select and launch different games from this project.
"""

import pygame
import sys


# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
MENU_BG = (20, 25, 30)
MENU_TITLE = (100, 200, 100)
MENU_SELECTED = (100, 255, 100)
MENU_UNSELECTED = (150, 150, 150)
MENU_HIGHLIGHT_BG = (40, 60, 40)
MENU_DESCRIPTION = (180, 180, 180)


class GameLauncher:
    """
    Main game launcher for selecting which game to play.
    """
    
    WINDOW_WIDTH = 550
    WINDOW_HEIGHT = 440
    
    def __init__(self):
        """Initialize the launcher."""
        pygame.init()
        
        self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        pygame.display.set_caption("Game Launcher")
        
        self.font_title = pygame.font.Font(None, 52)
        self.font_medium = pygame.font.Font(None, 30)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 20)
        
        self.games = [
            {
                'name': 'Snake Classic',
                'description': '2D snake with two game modes',
                'module': 'snake.snake_game',
                'available': True
            },
            {
                'name': 'Snake 3D',
                'description': 'Isometric 2.5D snake',
                'module': 'snake3d.snake_game',
                'available': True
            },
            {
                'name': 'Brawler',
                'description': '2v2 Brawl Ball arena game',
                'module': 'brawler.main',
                'available': True
            }
        ]
        
        self.selected_index = 0
        self.clock = pygame.time.Clock()
    
    def handle_events(self):
        """
        Handle input events.
        
        Returns:
            str or None: 'quit' to exit, game module name to launch, None to continue
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return 'quit'
                
                elif event.key == pygame.K_UP:
                    self.selected_index = max(0, self.selected_index - 1)
                
                elif event.key == pygame.K_DOWN:
                    self.selected_index = min(len(self.games) - 1, self.selected_index + 1)
                
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    game = self.games[self.selected_index]
                    if game['available']:
                        return game['module']
        
        return None
    
    def draw(self):
        """Draw the launcher screen."""
        self.screen.fill(MENU_BG)
        
        # Title
        title = self.font_title.render("GAME LAUNCHER", True, MENU_TITLE)
        title_rect = title.get_rect(centerx=self.WINDOW_WIDTH // 2, y=35)
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle = self.font_small.render("Select a game to play", True, MENU_DESCRIPTION)
        subtitle_rect = subtitle.get_rect(centerx=self.WINDOW_WIDTH // 2, y=85)
        self.screen.blit(subtitle, subtitle_rect)
        
        # Game list
        y = 130
        box_width = 400
        box_height = 60
        box_x = (self.WINDOW_WIDTH - box_width) // 2
        
        for i, game in enumerate(self.games):
            is_selected = i == self.selected_index
            is_available = game['available']
            
            # Box
            if is_selected:
                pygame.draw.rect(self.screen, MENU_HIGHLIGHT_BG,
                               (box_x, y, box_width, box_height), border_radius=8)
                pygame.draw.rect(self.screen, MENU_SELECTED,
                               (box_x, y, box_width, box_height), 2, border_radius=8)
            else:
                pygame.draw.rect(self.screen, (30, 35, 40),
                               (box_x, y, box_width, box_height), border_radius=8)
                pygame.draw.rect(self.screen, GRAY,
                               (box_x, y, box_width, box_height), 1, border_radius=8)
            
            # Game name
            if is_available:
                name_color = MENU_SELECTED if is_selected else WHITE
            else:
                name_color = GRAY
            
            name_text = self.font_medium.render(game['name'], True, name_color)
            self.screen.blit(name_text, (box_x + 15, y + 10))
            
            # Description
            desc_color = MENU_DESCRIPTION if is_available else (80, 80, 80)
            desc_text = self.font_tiny.render(game['description'], True, desc_color)
            self.screen.blit(desc_text, (box_x + 15, y + 36))
            
            # Status indicator for unavailable games
            if not is_available:
                status = self.font_tiny.render("[Soon]", True, (100, 100, 100))
                status_rect = status.get_rect(right=box_x + box_width - 12, centery=y + 20)
                self.screen.blit(status, status_rect)
            
            y += 75
        
        # Controls hint
        hint = self.font_tiny.render("Arrows: Navigate | ENTER: Launch | ESC: Quit", True, GRAY)
        hint_rect = hint.get_rect(centerx=self.WINDOW_WIDTH // 2, y=self.WINDOW_HEIGHT - 25)
        self.screen.blit(hint, hint_rect)
        
        pygame.display.flip()
    
    def run(self):
        """
        Run the launcher.
        
        Returns:
            str or None: Module to launch, or None if quit
        """
        while True:
            result = self.handle_events()
            
            if result == 'quit':
                return None
            elif result is not None:
                return result
            
            self.draw()
            self.clock.tick(30)


def launch_game(module_name):
    """
    Launch a game by its module name.
    
    Args:
        module_name: Name of the module to import and run
    """
    pygame.quit()  # Close launcher window
    
    if module_name == 'snake.snake_game':
        from snake import snake_game
        snake_game.main()
    elif module_name == 'snake3d.snake_game':
        from snake3d import snake_game
        snake_game.main()
    elif module_name == 'brawler.main':
        from brawler import main
        result = main.main()
        # Brawler returns 'back' if user wants to return to launcher
        return result


def main():
    """Main entry point."""
    print("=" * 50)
    print("GAME LAUNCHER")
    print("=" * 50)
    
    while True:
        launcher = GameLauncher()
        game_module = launcher.run()
        
        if game_module is None:
            break
        
        print(f"\nLaunching: {game_module}")
        launch_game(game_module)
        
        # Reinitialize pygame for launcher after game exits
        pygame.init()
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
