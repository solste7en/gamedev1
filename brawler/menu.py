"""
Menu system for Brawler game.

Includes mode selection and character selection screens.
"""

import pygame
from .assets import (
    WINDOW_WIDTH, WINDOW_HEIGHT, BRAWLER_STATS,
    TEAM_BLUE, TEAM_BLUE_LIGHT, TEAM_RED, TEAM_RED_LIGHT,
    WHITE, BLACK, GRAY, get_team_colors
)


class MenuState:
    """Menu states."""
    MODE_SELECT = 'mode_select'
    CHARACTER_SELECT = 'character_select'
    READY = 'ready'
    BACK = 'back'


class Menu:
    """
    Main menu for Brawler game.
    
    Handles mode selection (2P Local, vs AI) and character selection.
    """
    
    def __init__(self):
        """Initialize menu."""
        self.state = MenuState.MODE_SELECT
        
        # Fonts
        self.font_title = pygame.font.Font(None, 64)
        self.font_large = pygame.font.Font(None, 42)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        # Mode selection
        self.game_modes = [
            {'name': '2 Player Local', 'description': 'Play against a friend', 'mode': '2p'},
            {'name': 'VS AI', 'description': 'Play against computer bots', 'mode': 'ai'},
            {'name': 'Practice', 'description': 'Free practice (no score)', 'mode': 'practice'}
        ]
        self.selected_mode_index = 0
        
        # Character selection
        self.brawlers = ['colt', 'shelly', 'piper', 'edgar']
        self.player_selections = {
            0: {'brawler': 0, 'confirmed': False},  # Player 1 (blue)
            1: {'brawler': 1, 'confirmed': False}   # Player 2 (red)
        }
        
        # Selected game mode
        self.selected_game_mode = None
        
        # Visual effects
        self.pulse_timer = 0
    
    def update(self, dt):
        """Update menu animations."""
        self.pulse_timer += dt
    
    def handle_event(self, event):
        """
        Handle menu input events.
        
        Args:
            event: Pygame event
            
        Returns:
            MenuState or None: New state if changed
        """
        if event.type != pygame.KEYDOWN:
            return None
        
        if self.state == MenuState.MODE_SELECT:
            return self._handle_mode_select(event)
        elif self.state == MenuState.CHARACTER_SELECT:
            return self._handle_character_select(event)
        
        return None
    
    def _handle_mode_select(self, event):
        """Handle mode selection input."""
        if event.key == pygame.K_ESCAPE:
            return MenuState.BACK
        
        elif event.key == pygame.K_UP:
            self.selected_mode_index = (self.selected_mode_index - 1) % len(self.game_modes)
        
        elif event.key == pygame.K_DOWN:
            self.selected_mode_index = (self.selected_mode_index + 1) % len(self.game_modes)
        
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            self.selected_game_mode = self.game_modes[self.selected_mode_index]['mode']
            self.state = MenuState.CHARACTER_SELECT
            # Reset character selections
            self.player_selections = {
                0: {'brawler': 0, 'confirmed': False},
                1: {'brawler': 1, 'confirmed': False}
            }
        
        return None
    
    def _handle_character_select(self, event):
        """Handle character selection input."""
        if event.key == pygame.K_ESCAPE:
            # Check if any player confirmed, unconfirm first
            if self.player_selections[0]['confirmed']:
                self.player_selections[0]['confirmed'] = False
            elif self.player_selections[1]['confirmed']:
                self.player_selections[1]['confirmed'] = False
            else:
                self.state = MenuState.MODE_SELECT
            return None
        
        # Player 1 controls (WASD + Space)
        if not self.player_selections[0]['confirmed']:
            if event.key == pygame.K_a:
                self._change_brawler(0, -1)
            elif event.key == pygame.K_d:
                self._change_brawler(0, 1)
            elif event.key == pygame.K_SPACE:
                self.player_selections[0]['confirmed'] = True
        
        # Player 2 controls (Arrows + Enter) - only in 2P mode
        if self.selected_game_mode == '2p':
            if not self.player_selections[1]['confirmed']:
                if event.key == pygame.K_LEFT:
                    self._change_brawler(1, -1)
                elif event.key == pygame.K_RIGHT:
                    self._change_brawler(1, 1)
                elif event.key == pygame.K_RETURN:
                    self.player_selections[1]['confirmed'] = True
        else:
            # In AI mode, auto-confirm player 2
            self.player_selections[1]['confirmed'] = True
        
        # Check if all players confirmed
        if (self.player_selections[0]['confirmed'] and 
            self.player_selections[1]['confirmed']):
            return MenuState.READY
        
        return None
    
    def _change_brawler(self, player, direction):
        """Change selected brawler for a player."""
        current = self.player_selections[player]['brawler']
        new_index = (current + direction) % len(self.brawlers)
        self.player_selections[player]['brawler'] = new_index
    
    def get_selected_brawlers(self):
        """
        Get the selected brawler types for each player.
        
        Returns:
            tuple: (player1_brawler, player2_brawler)
        """
        return (
            self.brawlers[self.player_selections[0]['brawler']],
            self.brawlers[self.player_selections[1]['brawler']]
        )
    
    def get_game_mode(self):
        """Get selected game mode."""
        return self.selected_game_mode
    
    def draw(self, surface):
        """Draw menu screen."""
        # Background
        surface.fill((25, 25, 35))
        
        if self.state == MenuState.MODE_SELECT:
            self._draw_mode_select(surface)
        elif self.state == MenuState.CHARACTER_SELECT:
            self._draw_character_select(surface)
    
    def _draw_mode_select(self, surface):
        """Draw mode selection screen."""
        # Title
        title = self.font_title.render("BRAWLER", True, WHITE)
        title_rect = title.get_rect(centerx=WINDOW_WIDTH // 2, y=60)
        surface.blit(title, title_rect)
        
        subtitle = self.font_medium.render("Brawl Ball", True, GRAY)
        subtitle_rect = subtitle.get_rect(centerx=WINDOW_WIDTH // 2, y=120)
        surface.blit(subtitle, subtitle_rect)
        
        # Mode options
        y = 200
        box_width = 350
        box_height = 80
        
        for i, mode in enumerate(self.game_modes):
            is_selected = i == self.selected_mode_index
            box_x = (WINDOW_WIDTH - box_width) // 2
            
            # Draw box
            if is_selected:
                # Pulsing effect
                pulse = abs(pygame.time.get_ticks() % 1000 - 500) / 500
                border_color = (
                    int(100 + 100 * pulse),
                    int(200 + 55 * pulse),
                    int(100 + 100 * pulse)
                )
                pygame.draw.rect(surface, (40, 50, 40),
                               (box_x, y, box_width, box_height), border_radius=10)
                pygame.draw.rect(surface, border_color,
                               (box_x, y, box_width, box_height), 3, border_radius=10)
            else:
                pygame.draw.rect(surface, (35, 35, 45),
                               (box_x, y, box_width, box_height), border_radius=10)
                pygame.draw.rect(surface, (60, 60, 70),
                               (box_x, y, box_width, box_height), 2, border_radius=10)
            
            # Mode name
            name_color = (150, 255, 150) if is_selected else WHITE
            name = self.font_large.render(mode['name'], True, name_color)
            surface.blit(name, (box_x + 20, y + 15))
            
            # Description
            desc_color = (150, 150, 150) if is_selected else (100, 100, 100)
            desc = self.font_small.render(mode['description'], True, desc_color)
            surface.blit(desc, (box_x + 20, y + 50))
            
            y += 95
        
        # Controls hint
        hint = self.font_small.render("UP/DOWN: Select | ENTER: Confirm | ESC: Back", True, GRAY)
        hint_rect = hint.get_rect(centerx=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT - 40)
        surface.blit(hint, hint_rect)
    
    def _draw_character_select(self, surface):
        """Draw character selection screen."""
        # Title
        title = self.font_large.render("SELECT YOUR BRAWLER", True, WHITE)
        title_rect = title.get_rect(centerx=WINDOW_WIDTH // 2, y=30)
        surface.blit(title, title_rect)
        
        # Draw player selection panels
        panel_width = 400
        panel_height = 450
        panel_y = 80
        
        # Player 1 (Blue) - left side
        self._draw_player_select_panel(surface, 0, 
                                       (50, panel_y), panel_width, panel_height)
        
        # Player 2 (Red) - right side
        if self.selected_game_mode == '2p':
            self._draw_player_select_panel(surface, 1,
                                           (WINDOW_WIDTH - panel_width - 50, panel_y),
                                           panel_width, panel_height)
        else:
            # Show AI indicator
            self._draw_ai_panel(surface,
                               (WINDOW_WIDTH - panel_width - 50, panel_y),
                               panel_width, panel_height)
        
        # VS in middle
        vs_text = self.font_title.render("VS", True, GRAY)
        vs_rect = vs_text.get_rect(center=(WINDOW_WIDTH // 2, panel_y + panel_height // 2))
        surface.blit(vs_text, vs_rect)
        
        # Controls hint
        if self.selected_game_mode == '2p':
            hint1 = "P1: A/D to select, SPACE to confirm"
            hint2 = "P2: LEFT/RIGHT to select, ENTER to confirm"
        else:
            hint1 = "A/D to select, SPACE to confirm"
            hint2 = ""
        
        hint1_text = self.font_small.render(hint1, True, TEAM_BLUE)
        hint1_rect = hint1_text.get_rect(centerx=WINDOW_WIDTH // 4, y=WINDOW_HEIGHT - 60)
        surface.blit(hint1_text, hint1_rect)
        
        if hint2:
            hint2_text = self.font_small.render(hint2, True, TEAM_RED)
            hint2_rect = hint2_text.get_rect(centerx=3 * WINDOW_WIDTH // 4, y=WINDOW_HEIGHT - 60)
            surface.blit(hint2_text, hint2_rect)
        
        back_hint = self.font_small.render("ESC: Back", True, GRAY)
        back_rect = back_hint.get_rect(centerx=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT - 30)
        surface.blit(back_hint, back_rect)
    
    def _draw_player_select_panel(self, surface, player, pos, width, height):
        """Draw character selection panel for a player."""
        x, y = pos
        team_color, team_light, team_dark = get_team_colors(player)
        selection = self.player_selections[player]
        brawler_type = self.brawlers[selection['brawler']]
        stats = BRAWLER_STATS[brawler_type]
        confirmed = selection['confirmed']
        
        # Panel background
        bg_color = (50, 60, 50) if confirmed else (30, 35, 40)
        pygame.draw.rect(surface, bg_color, (x, y, width, height), border_radius=15)
        
        # Border
        border_color = team_light if confirmed else team_color
        border_width = 4 if confirmed else 2
        pygame.draw.rect(surface, border_color, (x, y, width, height), 
                        border_width, border_radius=15)
        
        # Player label
        player_label = f"PLAYER {player + 1}" if player == 0 else "PLAYER 2"
        team_label = "BLUE TEAM" if player == 0 else "RED TEAM"
        
        label = self.font_medium.render(player_label, True, team_light)
        label_rect = label.get_rect(centerx=x + width // 2, y=y + 15)
        surface.blit(label, label_rect)
        
        team_text = self.font_small.render(team_label, True, team_color)
        team_rect = team_text.get_rect(centerx=x + width // 2, y=y + 45)
        surface.blit(team_text, team_rect)
        
        # Brawler portrait area
        portrait_y = y + 80
        portrait_size = 150
        portrait_x = x + (width - portrait_size) // 2
        
        # Portrait background
        pygame.draw.rect(surface, (20, 20, 30),
                        (portrait_x, portrait_y, portrait_size, portrait_size),
                        border_radius=10)
        pygame.draw.rect(surface, stats['colors']['primary'],
                        (portrait_x, portrait_y, portrait_size, portrait_size),
                        3, border_radius=10)
        
        # Simple brawler representation (colored circle)
        center_x = portrait_x + portrait_size // 2
        center_y = portrait_y + portrait_size // 2
        pygame.draw.circle(surface, stats['colors']['primary'], (center_x, center_y), 50)
        pygame.draw.circle(surface, stats['colors']['skin'], (center_x, center_y - 15), 25)
        pygame.draw.circle(surface, stats['colors']['hair'], (center_x, center_y - 30), 20)
        
        # Selection arrows (if not confirmed)
        if not confirmed:
            arrow_y = portrait_y + portrait_size // 2
            # Left arrow
            pygame.draw.polygon(surface, GRAY,
                              [(portrait_x - 25, arrow_y),
                               (portrait_x - 10, arrow_y - 15),
                               (portrait_x - 10, arrow_y + 15)])
            # Right arrow
            pygame.draw.polygon(surface, GRAY,
                              [(portrait_x + portrait_size + 25, arrow_y),
                               (portrait_x + portrait_size + 10, arrow_y - 15),
                               (portrait_x + portrait_size + 10, arrow_y + 15)])
        
        # Brawler name
        name = self.font_large.render(stats['name'].upper(), True, WHITE)
        name_rect = name.get_rect(centerx=x + width // 2, y=portrait_y + portrait_size + 15)
        surface.blit(name, name_rect)
        
        # Stats
        stats_y = portrait_y + portrait_size + 55
        self._draw_stat_bar(surface, x + 20, stats_y, width - 40, "Health",
                           stats['max_health'], 6000)
        self._draw_stat_bar(surface, x + 20, stats_y + 30, width - 40, "Speed",
                           stats['speed'], 300)
        self._draw_stat_bar(surface, x + 20, stats_y + 60, width - 40, "Range",
                           stats['attack_range'], 500)
        
        # Description
        desc = self.font_small.render(stats['description'], True, GRAY)
        desc_rect = desc.get_rect(centerx=x + width // 2, y=stats_y + 100)
        surface.blit(desc, desc_rect)
        
        # Confirmed indicator
        if confirmed:
            ready = self.font_medium.render("READY!", True, (100, 255, 100))
            ready_rect = ready.get_rect(centerx=x + width // 2, y=y + height - 35)
            surface.blit(ready, ready_rect)
    
    def _draw_ai_panel(self, surface, pos, width, height):
        """Draw AI opponent panel."""
        x, y = pos
        
        # Panel background
        pygame.draw.rect(surface, (30, 30, 40), (x, y, width, height), border_radius=15)
        pygame.draw.rect(surface, TEAM_RED, (x, y, width, height), 2, border_radius=15)
        
        # AI label
        label = self.font_large.render("AI OPPONENT", True, TEAM_RED_LIGHT)
        label_rect = label.get_rect(centerx=x + width // 2, y=y + height // 2 - 40)
        surface.blit(label, label_rect)
        
        desc = self.font_medium.render("Computer Controlled", True, GRAY)
        desc_rect = desc.get_rect(centerx=x + width // 2, y=y + height // 2)
        surface.blit(desc, desc_rect)
        
        # Show AI will pick random brawlers
        info = self.font_small.render("AI will select brawlers", True, GRAY)
        info_rect = info.get_rect(centerx=x + width // 2, y=y + height // 2 + 40)
        surface.blit(info, info_rect)
    
    def _draw_stat_bar(self, surface, x, y, width, label, value, max_val):
        """Draw a stat bar."""
        # Label
        label_text = self.font_small.render(label, True, GRAY)
        surface.blit(label_text, (x, y))
        
        # Bar background
        bar_x = x + 70
        bar_width = width - 70
        bar_height = 12
        
        pygame.draw.rect(surface, (40, 40, 50), 
                        (bar_x, y + 2, bar_width, bar_height), border_radius=3)
        
        # Fill
        fill_width = int(bar_width * (value / max_val))
        pygame.draw.rect(surface, (100, 180, 100),
                        (bar_x, y + 2, fill_width, bar_height), border_radius=3)
    
    def reset(self):
        """Reset menu to initial state."""
        self.state = MenuState.MODE_SELECT
        self.selected_mode_index = 0
        self.selected_game_mode = None
        self.player_selections = {
            0: {'brawler': 0, 'confirmed': False},
            1: {'brawler': 1, 'confirmed': False}
        }
