"""
HUD (Heads-Up Display) for Brawler game.

Renders score, timer, health bars, super meters, and other UI elements.
"""

import pygame
import math
from .assets import (
    WINDOW_WIDTH, WINDOW_HEIGHT, HUD_HEIGHT, SCOREBOARD_HEIGHT,
    MATCH_DURATION, SUPER_CHARGE_MAX,
    TEAM_BLUE, TEAM_BLUE_LIGHT, TEAM_RED, TEAM_RED_LIGHT,
    UI_BG, UI_BORDER, UI_TEXT, UI_TEXT_SHADOW,
    HEALTH_BAR_BG, HEALTH_BAR_GREEN, HEALTH_BAR_YELLOW, HEALTH_BAR_RED,
    SUPER_BAR_COLOR, SUPER_BAR_READY, WHITE, BLACK, GRAY,
    get_health_color, get_team_colors
)


class HUD:
    """
    Game HUD for displaying match information.
    """
    
    def __init__(self):
        """Initialize HUD fonts and surfaces."""
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 18)
        
        # Cached surfaces for performance
        self._score_surface = None
        self._timer_surface = None
        self._last_score = None
        self._last_time = None
    
    def draw(self, surface, game_state):
        """
        Draw all HUD elements.
        
        Args:
            surface: Pygame surface to draw on
            game_state: Dict with game info (score, time, players, etc.)
        """
        # Draw scoreboard at top
        self._draw_scoreboard(surface, game_state)
        
        # Draw player info panels
        self._draw_player_panels(surface, game_state)
        
        # Draw match timer
        self._draw_timer(surface, game_state)
        
        # Draw game messages (goal, overtime, etc.)
        if game_state.get('message'):
            self._draw_message(surface, game_state['message'])
    
    def _draw_scoreboard(self, surface, game_state):
        """Draw score display at top of screen."""
        score = game_state.get('score', [0, 0])
        
        # Background bar
        bar_height = SCOREBOARD_HEIGHT
        bar_rect = pygame.Rect(0, 0, WINDOW_WIDTH, bar_height)
        pygame.draw.rect(surface, UI_BG, bar_rect)
        pygame.draw.line(surface, UI_BORDER, (0, bar_height), (WINDOW_WIDTH, bar_height), 2)
        
        center_x = WINDOW_WIDTH // 2
        
        # Blue score (left)
        blue_text = self.font_large.render(str(score[0]), True, TEAM_BLUE_LIGHT)
        blue_rect = blue_text.get_rect(right=center_x - 60, centery=bar_height // 2)
        surface.blit(blue_text, blue_rect)
        
        # Team labels
        blue_label = self.font_small.render("BLUE", True, TEAM_BLUE)
        blue_label_rect = blue_label.get_rect(right=center_x - 65, centery=bar_height // 2 - 15)
        surface.blit(blue_label, blue_label_rect)
        
        # Dash separator
        dash = self.font_large.render("-", True, WHITE)
        dash_rect = dash.get_rect(center=(center_x, bar_height // 2))
        surface.blit(dash, dash_rect)
        
        # Red score (right)
        red_text = self.font_large.render(str(score[1]), True, TEAM_RED_LIGHT)
        red_rect = red_text.get_rect(left=center_x + 60, centery=bar_height // 2)
        surface.blit(red_text, red_rect)
        
        # Red label
        red_label = self.font_small.render("RED", True, TEAM_RED)
        red_label_rect = red_label.get_rect(left=center_x + 65, centery=bar_height // 2 - 15)
        surface.blit(red_label, red_label_rect)
    
    def _draw_timer(self, surface, game_state):
        """Draw match timer."""
        time_left = game_state.get('time_left', MATCH_DURATION)
        overtime = game_state.get('overtime', False)
        
        # Format time
        minutes = int(time_left) // 60
        seconds = int(time_left) % 60
        time_str = f"{minutes}:{seconds:02d}"
        
        # Timer color (red if low time)
        if overtime:
            color = TEAM_RED_LIGHT
        elif time_left < 30:
            color = TEAM_RED_LIGHT
        elif time_left < 60:
            color = HEALTH_BAR_YELLOW
        else:
            color = WHITE
        
        # Draw timer
        timer_text = self.font_medium.render(time_str, True, color)
        timer_rect = timer_text.get_rect(centerx=WINDOW_WIDTH // 2, 
                                         centery=SCOREBOARD_HEIGHT // 2 + 12)
        surface.blit(timer_text, timer_rect)
        
        # Draw overtime indicator
        if overtime:
            ot_text = self.font_tiny.render("OVERTIME", True, TEAM_RED_LIGHT)
            ot_rect = ot_text.get_rect(centerx=WINDOW_WIDTH // 2,
                                       centery=SCOREBOARD_HEIGHT // 2 + 28)
            surface.blit(ot_text, ot_rect)
    
    def _draw_player_panels(self, surface, game_state):
        """Draw player info panels at bottom."""
        players = game_state.get('players', [])
        
        panel_width = 200
        panel_height = HUD_HEIGHT - 10
        panel_y = WINDOW_HEIGHT - HUD_HEIGHT + 5
        
        # Position panels based on team
        positions = []
        for i, player in enumerate(players):
            if player['team'] == 0:  # Blue team
                x = 10 + (i % 2) * (panel_width + 10)
            else:  # Red team
                x = WINDOW_WIDTH - panel_width - 10 - ((i % 2)) * (panel_width + 10)
            positions.append((x, panel_y))
        
        # Draw each player panel
        for i, player in enumerate(players):
            if i < len(positions):
                self._draw_player_panel(surface, player, positions[i], panel_width, panel_height)
    
    def _draw_player_panel(self, surface, player, pos, width, height):
        """Draw individual player info panel."""
        x, y = pos
        team_color, team_light, team_dark = get_team_colors(player['team'])
        
        # Background
        panel_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, UI_BG, panel_rect, border_radius=5)
        pygame.draw.rect(surface, team_color, panel_rect, 2, border_radius=5)
        
        # Player name and brawler
        name_str = f"{player.get('name', 'Player')}"
        name_text = self.font_small.render(name_str, True, team_light)
        surface.blit(name_text, (x + 8, y + 5))
        
        brawler_str = player.get('brawler', 'Unknown')
        brawler_text = self.font_tiny.render(brawler_str, True, GRAY)
        surface.blit(brawler_text, (x + 8, y + 25))
        
        # Health bar
        health = player.get('health', 0)
        max_health = player.get('max_health', 1)
        health_percent = health / max_health if max_health > 0 else 0
        
        bar_x = x + 8
        bar_y = y + 42
        bar_width = width - 16
        bar_height = 12
        
        # Background
        pygame.draw.rect(surface, HEALTH_BAR_BG, 
                        (bar_x, bar_y, bar_width, bar_height), border_radius=3)
        
        # Health fill
        if health_percent > 0:
            fill_width = int(bar_width * health_percent)
            fill_color = get_health_color(health_percent)
            pygame.draw.rect(surface, fill_color,
                           (bar_x, bar_y, fill_width, bar_height), border_radius=3)
        
        # Health text
        health_str = f"{int(health)}"
        health_text = self.font_tiny.render(health_str, True, WHITE)
        text_rect = health_text.get_rect(center=(bar_x + bar_width // 2, bar_y + bar_height // 2))
        surface.blit(health_text, text_rect)
        
        # Super meter
        super_charge = player.get('super_charge', 0)
        super_ready = super_charge >= SUPER_CHARGE_MAX
        
        super_y = bar_y + bar_height + 4
        super_height = 6
        
        pygame.draw.rect(surface, HEALTH_BAR_BG,
                        (bar_x, super_y, bar_width, super_height), border_radius=2)
        
        if super_charge > 0:
            super_width = int(bar_width * (super_charge / SUPER_CHARGE_MAX))
            super_color = SUPER_BAR_READY if super_ready else SUPER_BAR_COLOR
            pygame.draw.rect(surface, super_color,
                           (bar_x, super_y, super_width, super_height), border_radius=2)
        
        # "SUPER!" indicator if ready
        if super_ready:
            super_text = self.font_tiny.render("SUPER!", True, SUPER_BAR_READY)
            surface.blit(super_text, (x + width - 50, y + 5))
    
    def _draw_message(self, surface, message):
        """Draw centered game message."""
        # Shadow
        shadow = self.font_large.render(message, True, BLACK)
        shadow_rect = shadow.get_rect(center=(WINDOW_WIDTH // 2 + 2, 
                                              WINDOW_HEIGHT // 2 - 100 + 2))
        surface.blit(shadow, shadow_rect)
        
        # Text
        text = self.font_large.render(message, True, WHITE)
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 100))
        surface.blit(text, text_rect)
    
    def draw_controls_hint(self, surface, player_num):
        """Draw control hints for player."""
        if player_num == 1:
            hints = "WASD: Move | SPACE: Attack | E: Super"
            x = 10
        else:
            hints = "Arrows: Move | ENTER: Attack | SHIFT: Super"
            x = WINDOW_WIDTH - 300
        
        hint_text = self.font_tiny.render(hints, True, GRAY)
        surface.blit(hint_text, (x, WINDOW_HEIGHT - 20))
    
    def draw_goal_celebration(self, surface, team, progress):
        """
        Draw goal celebration overlay.
        
        Args:
            surface: Surface to draw on
            team: Scoring team (0=blue, 1=red)
            progress: Animation progress 0-1
        """
        team_color = TEAM_BLUE_LIGHT if team == 0 else TEAM_RED_LIGHT
        
        # Flash
        if progress < 0.3:
            alpha = int(150 * (1 - progress / 0.3))
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((*team_color, alpha))
            surface.blit(overlay, (0, 0))
        
        # GOAL text
        scale = 1 + 0.3 * math.sin(progress * math.pi * 4)
        
        goal_text = self.font_large.render("GOAL!", True, team_color)
        goal_rect = goal_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 80))
        
        # Shadow
        shadow = self.font_large.render("GOAL!", True, BLACK)
        shadow_rect = shadow.get_rect(center=(WINDOW_WIDTH // 2 + 3, WINDOW_HEIGHT // 2 - 77))
        surface.blit(shadow, shadow_rect)
        surface.blit(goal_text, goal_rect)
        
        # Team name
        team_name = "BLUE SCORES!" if team == 0 else "RED SCORES!"
        team_text = self.font_medium.render(team_name, True, team_color)
        team_rect = team_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 30))
        surface.blit(team_text, team_rect)
    
    def draw_game_over(self, surface, winner, score):
        """
        Draw game over screen.
        
        Args:
            surface: Surface to draw on
            winner: Winning team (0=blue, 1=red) or None for tie
            score: Final score [blue, red]
        """
        # Overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # Winner text
        if winner == 0:
            winner_text = "BLUE TEAM WINS!"
            color = TEAM_BLUE_LIGHT
        elif winner == 1:
            winner_text = "RED TEAM WINS!"
            color = TEAM_RED_LIGHT
        else:
            winner_text = "DRAW!"
            color = WHITE
        
        # Title
        title = self.font_large.render(winner_text, True, color)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 60))
        surface.blit(title, title_rect)
        
        # Score
        score_str = f"{score[0]} - {score[1]}"
        score_text = self.font_large.render(score_str, True, WHITE)
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        surface.blit(score_text, score_rect)
        
        # Instructions
        inst_text = self.font_small.render("Press SPACE to play again | ESC for menu", True, GRAY)
        inst_rect = inst_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 80))
        surface.blit(inst_text, inst_rect)
    
    def draw_countdown(self, surface, count):
        """
        Draw countdown before match starts.
        
        Args:
            surface: Surface to draw on
            count: Countdown number (3, 2, 1, GO)
        """
        if isinstance(count, int) and count > 0:
            text_str = str(count)
            color = WHITE
        else:
            text_str = "GO!"
            color = HEALTH_BAR_GREEN
        
        # Large centered text
        font = pygame.font.Font(None, 120)
        
        # Shadow
        shadow = font.render(text_str, True, BLACK)
        shadow_rect = shadow.get_rect(center=(WINDOW_WIDTH // 2 + 4, WINDOW_HEIGHT // 2 + 4))
        surface.blit(shadow, shadow_rect)
        
        # Text
        text = font.render(text_str, True, color)
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        surface.blit(text, text_rect)
