"""
Menu module for the Snake Game.
Handles player name input, mode selection, game configuration, and leaderboards.
"""

import pygame
from .assets import (
    CELL_SIZE, BLACK, WHITE, GRAY, DARK_GRAY,
    MAP_SIZES, MAP_SIZE_ORDER, MAP_SIZE_MULTIPLIERS,
    BARRIER_DENSITIES, BARRIER_ORDER,
    MENU_BG, MENU_TITLE, MENU_TEXT, MENU_SELECTED, MENU_UNSELECTED,
    MENU_HIGHLIGHT_BG, MENU_DESCRIPTION,
    get_difficulty_label
)
from .player import Leaderboard, PlayerProfile, get_existing_profiles


class NameInputScreen:
    """
    Screen for entering player name.
    """
    
    MENU_WIDTH = 600
    MENU_HEIGHT = 520
    MAX_NAME_LENGTH = 12
    
    def __init__(self):
        """Initialize the name input screen."""
        self.screen = pygame.display.set_mode((self.MENU_WIDTH, self.MENU_HEIGHT))
        pygame.display.set_caption("Snake Game - Enter Your Name")
        
        self.font_title = pygame.font.Font(None, 52)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 26)
        self.font_tiny = pygame.font.Font(None, 20)
        
        self.player_name = ""
        self.existing_profiles = get_existing_profiles()
        self.selected_profile_index = -1  # -1 means new name input
        self.cursor_visible = True
        self.cursor_timer = 0
        
        # Delete confirmation state
        self.delete_confirm_step = 0  # 0 = none, 1 = first confirm, 2 = deleting
        self.delete_target_name = None
        
        self.clock = pygame.time.Clock()
    
    def handle_events(self):
        """Handle input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            
            elif event.type == pygame.KEYDOWN:
                # Handle delete confirmation state
                if self.delete_confirm_step > 0:
                    if event.key == pygame.K_ESCAPE:
                        # Cancel deletion
                        self.delete_confirm_step = 0
                        self.delete_target_name = None
                    elif event.key == pygame.K_y:
                        if self.delete_confirm_step == 1:
                            # Move to second confirmation
                            self.delete_confirm_step = 2
                        elif self.delete_confirm_step == 2:
                            # Actually delete the profile
                            self._delete_profile(self.delete_target_name)
                            self.delete_confirm_step = 0
                            self.delete_target_name = None
                    elif event.key == pygame.K_n:
                        # Cancel deletion
                        self.delete_confirm_step = 0
                        self.delete_target_name = None
                    continue
                
                if event.key == pygame.K_ESCAPE:
                    return 'quit'
                
                elif event.key == pygame.K_RETURN:
                    if self.selected_profile_index >= 0:
                        # Selected existing profile
                        return self.existing_profiles[self.selected_profile_index]
                    elif len(self.player_name) > 0:
                        return self.player_name
                
                elif event.key == pygame.K_UP:
                    if self.existing_profiles:
                        if self.selected_profile_index == -1:
                            self.selected_profile_index = len(self.existing_profiles) - 1
                        else:
                            self.selected_profile_index -= 1
                
                elif event.key == pygame.K_DOWN:
                    if self.existing_profiles:
                        if self.selected_profile_index < len(self.existing_profiles) - 1:
                            self.selected_profile_index += 1
                        else:
                            self.selected_profile_index = -1
                
                elif event.key == pygame.K_BACKSPACE:
                    if self.selected_profile_index == -1:
                        self.player_name = self.player_name[:-1]
                
                elif event.key == pygame.K_TAB:
                    # Switch between new input and existing profiles
                    if self.selected_profile_index == -1 and self.existing_profiles:
                        self.selected_profile_index = 0
                    else:
                        self.selected_profile_index = -1
                
                elif event.key == pygame.K_DELETE or event.key == pygame.K_d:
                    # Start delete confirmation for selected profile
                    if self.selected_profile_index >= 0 and self.selected_profile_index < len(self.existing_profiles):
                        self.delete_target_name = self.existing_profiles[self.selected_profile_index]
                        self.delete_confirm_step = 1
                
                else:
                    if self.selected_profile_index == -1:
                        # Only allow alphanumeric and some special chars
                        if event.unicode.isalnum() or event.unicode in ('_', '-', ' '):
                            if len(self.player_name) < self.MAX_NAME_LENGTH:
                                self.player_name += event.unicode
        
        return None
    
    def _delete_profile(self, profile_name):
        """Delete a profile and refresh the list."""
        import os
        profile_path = os.path.join('profiles', f'{profile_name}.json')
        if os.path.exists(profile_path):
            os.remove(profile_path)
        
        # Refresh profiles list
        self.existing_profiles = get_existing_profiles()
        
        # Reset selection if needed
        if self.selected_profile_index >= len(self.existing_profiles):
            self.selected_profile_index = len(self.existing_profiles) - 1 if self.existing_profiles else -1
    
    def draw(self):
        """Draw the name input screen."""
        self.screen.fill(MENU_BG)
        
        # Title
        title = self.font_title.render("SNAKE GAME", True, MENU_TITLE)
        title_rect = title.get_rect(centerx=self.MENU_WIDTH // 2, y=30)
        self.screen.blit(title, title_rect)
        
        # Prompt
        prompt = self.font_medium.render("Enter Your Name", True, WHITE)
        prompt_rect = prompt.get_rect(centerx=self.MENU_WIDTH // 2, y=100)
        self.screen.blit(prompt, prompt_rect)
        
        # Input box
        input_y = 150
        box_width = 320
        box_height = 42
        box_x = (self.MENU_WIDTH - box_width) // 2
        
        is_input_selected = self.selected_profile_index == -1
        box_color = MENU_SELECTED if is_input_selected else GRAY
        
        pygame.draw.rect(self.screen, DARK_GRAY, (box_x, input_y, box_width, box_height))
        pygame.draw.rect(self.screen, box_color, (box_x, input_y, box_width, box_height), 2)
        
        # Name text with cursor
        display_text = self.player_name
        if is_input_selected:
            self.cursor_timer += 1
            if self.cursor_timer >= 30:
                self.cursor_timer = 0
                self.cursor_visible = not self.cursor_visible
            if self.cursor_visible:
                display_text += "|"
        
        name_text = self.font_medium.render(display_text, True, WHITE)
        # Clip text to fit in box
        text_x = box_x + 12
        text_max_width = box_width - 24
        if name_text.get_width() > text_max_width:
            # Create a clipping surface
            clip_surface = pygame.Surface((text_max_width, box_height - 4))
            clip_surface.fill(DARK_GRAY)
            clip_surface.blit(name_text, (0, 1))
            self.screen.blit(clip_surface, (text_x, input_y + 8))
        else:
            self.screen.blit(name_text, (text_x, input_y + 8))
        
        # Existing profiles section
        if self.existing_profiles:
            profiles_y = 210
            
            header = self.font_small.render("Or select an existing profile:", True, MENU_DESCRIPTION)
            header_rect = header.get_rect(centerx=self.MENU_WIDTH // 2, y=profiles_y)
            self.screen.blit(header, header_rect)
            
            # Show max 5 profiles with spacing
            max_profiles = min(5, len(self.existing_profiles))
            for i, profile_name in enumerate(self.existing_profiles[:max_profiles]):
                y = profiles_y + 32 + i * 28
                is_selected = i == self.selected_profile_index
                
                # Truncate long profile names
                display_name = profile_name[:14] + ".." if len(profile_name) > 16 else profile_name
                
                if is_selected:
                    # Highlight background
                    highlight_rect = pygame.Rect(
                        (self.MENU_WIDTH - 220) // 2, y - 3,
                        220, 24
                    )
                    pygame.draw.rect(self.screen, MENU_HIGHLIGHT_BG, highlight_rect, border_radius=5)
                    pygame.draw.rect(self.screen, MENU_SELECTED, highlight_rect, 2, border_radius=5)
                
                color = MENU_SELECTED if is_selected else MENU_UNSELECTED
                text = self.font_small.render(display_name, True, color)
                text_rect = text.get_rect(centerx=self.MENU_WIDTH // 2, y=y)
                self.screen.blit(text, text_rect)
            
            # Show count if more profiles exist
            if len(self.existing_profiles) > 5:
                more_text = self.font_tiny.render(f"... and {len(self.existing_profiles) - 5} more", True, GRAY)
                more_rect = more_text.get_rect(centerx=self.MENU_WIDTH // 2, y=profiles_y + 32 + 5 * 28)
                self.screen.blit(more_text, more_rect)
        
        # Instructions - positioned at bottom with proper spacing
        instructions = [
            "Type your name and press ENTER",
            "UP/DOWN: Select existing profile",
            "TAB: Switch between input/profiles",
            "D or DEL: Delete selected profile",
            "ESC: Quit"
        ]
        
        y = self.MENU_HEIGHT - 110
        for instruction in instructions:
            text = self.font_tiny.render(instruction, True, GRAY)
            text_rect = text.get_rect(centerx=self.MENU_WIDTH // 2, y=y)
            self.screen.blit(text, text_rect)
            y += 20
        
        # Draw delete confirmation dialog if active
        if self.delete_confirm_step > 0:
            self._draw_delete_confirmation()
        
        pygame.display.flip()
    
    def _draw_delete_confirmation(self):
        """Draw the delete confirmation dialog."""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.MENU_WIDTH, self.MENU_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Dialog box
        dialog_width = 400
        dialog_height = 160 if self.delete_confirm_step == 1 else 180
        dialog_x = (self.MENU_WIDTH - dialog_width) // 2
        dialog_y = (self.MENU_HEIGHT - dialog_height) // 2
        
        # Background
        pygame.draw.rect(self.screen, (40, 40, 50), 
                        (dialog_x, dialog_y, dialog_width, dialog_height), 
                        border_radius=10)
        pygame.draw.rect(self.screen, (255, 100, 100), 
                        (dialog_x, dialog_y, dialog_width, dialog_height), 
                        2, border_radius=10)
        
        # Title
        title_color = (255, 100, 100)
        if self.delete_confirm_step == 1:
            title = self.font_medium.render("Delete Profile?", True, title_color)
        else:
            title = self.font_medium.render("ARE YOU SURE?", True, title_color)
        title_rect = title.get_rect(centerx=self.MENU_WIDTH // 2, y=dialog_y + 20)
        self.screen.blit(title, title_rect)
        
        # Message
        truncated_name = self.delete_target_name[:16] + ".." if len(self.delete_target_name) > 18 else self.delete_target_name
        if self.delete_confirm_step == 1:
            msg = self.font_small.render(f'Delete "{truncated_name}"?', True, WHITE)
        else:
            msg = self.font_small.render("This cannot be undone!", True, (255, 200, 100))
        msg_rect = msg.get_rect(centerx=self.MENU_WIDTH // 2, y=dialog_y + 60)
        self.screen.blit(msg, msg_rect)
        
        if self.delete_confirm_step == 2:
            msg2 = self.font_small.render(f'Profile: "{truncated_name}"', True, GRAY)
            msg2_rect = msg2.get_rect(centerx=self.MENU_WIDTH // 2, y=dialog_y + 90)
            self.screen.blit(msg2, msg2_rect)
        
        # Buttons hint
        hint_y = dialog_y + dialog_height - 40
        yes_text = self.font_small.render("[Y] Yes", True, (255, 100, 100))
        no_text = self.font_small.render("[N] No", True, (100, 255, 100))
        esc_text = self.font_tiny.render("ESC to cancel", True, GRAY)
        
        self.screen.blit(yes_text, (dialog_x + 60, hint_y))
        self.screen.blit(no_text, (dialog_x + dialog_width - 120, hint_y))
        
        esc_rect = esc_text.get_rect(centerx=self.MENU_WIDTH // 2, y=dialog_y + dialog_height - 18)
        self.screen.blit(esc_text, esc_rect)
    
    def run(self):
        """
        Run the name input screen.
        
        Returns:
            str: Player name, or None if quit
        """
        while True:
            result = self.handle_events()
            
            if result == 'quit':
                return None
            elif result is not None:
                return result
            
            self.draw()
            self.clock.tick(30)


class ModeSelectScreen:
    """
    Screen for selecting game mode (Sandbox or Story).
    """
    
    MENU_WIDTH = 650
    MENU_HEIGHT = 520
    
    def __init__(self, player_name):
        """Initialize the mode selection screen."""
        self.screen = pygame.display.set_mode((self.MENU_WIDTH, self.MENU_HEIGHT))
        pygame.display.set_caption(f"Snake Game - {player_name}")
        
        self.player_name = player_name
        self.profile = PlayerProfile(player_name)
        self.leaderboard = Leaderboard()
        
        self.font_title = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 30)
        self.font_small = pygame.font.Font(None, 24)
        self.font_tiny = pygame.font.Font(None, 20)
        
        # 0 = Sandbox, 1 = Story, 2 = Leaderboard, 3 = Quit
        self.selected_option = 0
        self.showing_leaderboard = False
        
        self.clock = pygame.time.Clock()
    
    def handle_events(self):
        """Handle input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return {'action': 'quit'}
            
            elif event.type == pygame.KEYDOWN:
                if self.showing_leaderboard:
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                        self.showing_leaderboard = False
                    return None
                
                if event.key == pygame.K_ESCAPE:
                    return {'action': 'quit'}
                
                elif event.key == pygame.K_UP:
                    self.selected_option = max(0, self.selected_option - 1)
                
                elif event.key == pygame.K_DOWN:
                    self.selected_option = min(3, self.selected_option + 1)
                
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.selected_option == 0:
                        return {'action': 'sandbox', 'profile': self.profile}
                    elif self.selected_option == 1:
                        return {'action': 'story', 'profile': self.profile}
                    elif self.selected_option == 2:
                        self.showing_leaderboard = True
                    elif self.selected_option == 3:
                        return {'action': 'quit'}
        
        return None
    
    def draw(self):
        """Draw the mode selection screen."""
        self.screen.fill(MENU_BG)
        
        if self.showing_leaderboard:
            self._draw_leaderboard()
        else:
            self._draw_menu()
        
        pygame.display.flip()
    
    def _draw_menu(self):
        """Draw the main mode selection menu."""
        # Title
        title = self.font_title.render("SNAKE GAME", True, MENU_TITLE)
        title_rect = title.get_rect(centerx=self.MENU_WIDTH // 2, y=30)
        self.screen.blit(title, title_rect)
        
        # Welcome message (truncate long names)
        display_name = self.player_name[:14] + ".." if len(self.player_name) > 16 else self.player_name
        welcome = self.font_small.render(f"Welcome, {display_name}!", True, WHITE)
        welcome_rect = welcome.get_rect(centerx=self.MENU_WIDTH // 2, y=85)
        self.screen.blit(welcome, welcome_rect)
        
        # Mode options
        options = [
            ("SANDBOX MODE", "Custom settings, high scores"),
            ("STORY MODE", f"Level {self.profile.get_current_level()}/99"),
            ("LEADERBOARD", "View top 10 scores"),
            ("QUIT", "Exit the game")
        ]
        
        y = 130
        for i, (name, desc) in enumerate(options):
            is_selected = i == self.selected_option
            
            # Option box
            box_width = 420
            box_height = 55
            box_x = (self.MENU_WIDTH - box_width) // 2
            
            if is_selected:
                pygame.draw.rect(self.screen, MENU_HIGHLIGHT_BG, 
                               (box_x, y, box_width, box_height), border_radius=8)
                pygame.draw.rect(self.screen, MENU_SELECTED, 
                               (box_x, y, box_width, box_height), 2, border_radius=8)
                name_color = MENU_SELECTED
            else:
                pygame.draw.rect(self.screen, (30, 35, 40), 
                               (box_x, y, box_width, box_height), border_radius=8)
                pygame.draw.rect(self.screen, GRAY, 
                               (box_x, y, box_width, box_height), 1, border_radius=8)
                name_color = MENU_UNSELECTED
            
            # Option name
            name_text = self.font_medium.render(name, True, name_color)
            self.screen.blit(name_text, (box_x + 18, y + 10))
            
            # Description
            desc_text = self.font_tiny.render(desc, True, MENU_DESCRIPTION)
            self.screen.blit(desc_text, (box_x + 18, y + 34))
            
            y += 68
        
        # Player stats
        stats_y = 420
        stats = [
            f"Games: {self.profile.data['stats']['games_played']}",
            f"Best: {self.profile.data['stats']['best_sandbox_score']}",
            f"Story: Lv.{self.profile.get_highest_level()}"
        ]
        
        pygame.draw.line(self.screen, GRAY, (80, stats_y - 10), (self.MENU_WIDTH - 80, stats_y - 10))
        
        # Calculate spacing to distribute stats evenly
        usable_width = self.MENU_WIDTH - 160
        stat_spacing = usable_width // len(stats)
        for i, stat in enumerate(stats):
            text = self.font_tiny.render(stat, True, MENU_DESCRIPTION)
            x = 80 + i * stat_spacing + (stat_spacing - text.get_width()) // 2
            self.screen.blit(text, (x, stats_y + 5))
        
        # Controls hint
        hint = self.font_tiny.render("UP/DOWN: Navigate | ENTER: Select | ESC: Quit", True, GRAY)
        hint_rect = hint.get_rect(centerx=self.MENU_WIDTH // 2, y=self.MENU_HEIGHT - 25)
        self.screen.blit(hint, hint_rect)
    
    def _draw_leaderboard(self):
        """Draw the leaderboard screen."""
        # Title
        title = self.font_title.render("LEADERBOARD", True, MENU_TITLE)
        title_rect = title.get_rect(centerx=self.MENU_WIDTH // 2, y=30)
        self.screen.blit(title, title_rect)
        
        subtitle = self.font_small.render("Top 10 Sandbox Scores", True, MENU_DESCRIPTION)
        subtitle_rect = subtitle.get_rect(centerx=self.MENU_WIDTH // 2, y=75)
        self.screen.blit(subtitle, subtitle_rect)
        
        entries = self.leaderboard.get_entries()
        
        if not entries:
            no_scores = self.font_medium.render("No scores yet!", True, GRAY)
            no_scores_rect = no_scores.get_rect(centerx=self.MENU_WIDTH // 2, y=200)
            self.screen.blit(no_scores, no_scores_rect)
            
            hint = self.font_small.render("Play Sandbox mode to set a high score!", True, MENU_DESCRIPTION)
            hint_rect = hint.get_rect(centerx=self.MENU_WIDTH // 2, y=250)
            self.screen.blit(hint, hint_rect)
        else:
            # Header
            y = 110
            headers = ["#", "NAME", "SCORE", "MODE", "DATE"]
            x_positions = [40, 80, 280, 400, 520]
            
            for header, x in zip(headers, x_positions):
                text = self.font_tiny.render(header, True, GRAY)
                self.screen.blit(text, (x, y))
            
            pygame.draw.line(self.screen, GRAY, (30, y + 22), (self.MENU_WIDTH - 30, y + 22))
            
            # Entries
            y = 140
            for i, entry in enumerate(entries):
                # Highlight if this is the current player
                is_player = entry['name'].lower() == self.player_name.lower()
                
                if is_player:
                    highlight_rect = pygame.Rect(30, y - 2, self.MENU_WIDTH - 60, 26)
                    pygame.draw.rect(self.screen, (40, 50, 40), highlight_rect, border_radius=3)
                
                color = MENU_SELECTED if is_player else WHITE
                
                # Rank
                rank_text = self.font_small.render(f"{i + 1}", True, color)
                self.screen.blit(rank_text, (40, y))
                
                # Name (truncate if needed)
                name = entry['name'][:10]
                name_text = self.font_small.render(name, True, color)
                self.screen.blit(name_text, (80, y))
                
                # Score
                score_text = self.font_small.render(str(entry['score']), True, color)
                self.screen.blit(score_text, (280, y))
                
                # Settings (abbreviated)
                map_size = entry.get('map_size', '?')[0].upper()
                barriers = entry.get('barriers', '?')[0].upper()
                settings_text = self.font_tiny.render(f"{map_size}/{barriers}", True, MENU_DESCRIPTION)
                self.screen.blit(settings_text, (400, y + 3))
                
                # Date (format from ISO)
                date_str = entry.get('date', '')
                if date_str:
                    try:
                        # Parse ISO date and format as MM/DD
                        date_parts = date_str.split('T')[0].split('-')
                        formatted_date = f"{date_parts[1]}/{date_parts[2]}"
                    except (IndexError, ValueError):
                        formatted_date = "--"
                else:
                    formatted_date = "--"
                date_text = self.font_tiny.render(formatted_date, True, MENU_DESCRIPTION)
                self.screen.blit(date_text, (520, y + 3))
                
                y += 28
        
        # Back hint
        hint = self.font_small.render("Press ENTER or ESC to go back", True, GRAY)
        hint_rect = hint.get_rect(centerx=self.MENU_WIDTH // 2, y=self.MENU_HEIGHT - 30)
        self.screen.blit(hint, hint_rect)
    
    def run(self):
        """
        Run the mode selection screen.
        
        Returns:
            dict: Action to take, or None if quit
        """
        while True:
            result = self.handle_events()
            
            if result is not None:
                return result
            
            self.draw()
            self.clock.tick(30)


class SandboxConfigScreen:
    """
    Screen for configuring sandbox mode settings.
    """
    
    MENU_WIDTH = 650
    MENU_HEIGHT = 560
    
    def __init__(self, profile):
        """Initialize the sandbox config screen."""
        self.screen = pygame.display.set_mode((self.MENU_WIDTH, self.MENU_HEIGHT))
        pygame.display.set_caption("Snake Game - Sandbox Setup")
        
        self.profile = profile
        
        self.font_title = pygame.font.Font(None, 46)
        self.font_header = pygame.font.Font(None, 32)
        self.font_option = pygame.font.Font(None, 26)
        self.font_desc = pygame.font.Font(None, 22)
        self.font_small = pygame.font.Font(None, 20)
        
        # Selection state
        self.current_section = 0  # 0 = map size, 1 = barriers, 2 = kids mode, 3 = start button
        self.map_size_index = 1   # Default: medium
        self.barrier_index = 0    # Default: none
        self.kids_mode = False    # Default: off
        
        self.clock = pygame.time.Clock()
    
    def get_selected_map_size(self):
        """Get the currently selected map size key."""
        return MAP_SIZE_ORDER[self.map_size_index]
    
    def get_selected_barrier(self):
        """Get the currently selected barrier density key."""
        return BARRIER_ORDER[self.barrier_index]
    
    def handle_events(self):
        """Handle input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return 'back'
                
                elif event.key == pygame.K_UP:
                    self.current_section = max(0, self.current_section - 1)
                
                elif event.key == pygame.K_DOWN:
                    self.current_section = min(3, self.current_section + 1)
                
                elif event.key == pygame.K_LEFT:
                    if self.current_section == 0:
                        self.map_size_index = max(0, self.map_size_index - 1)
                    elif self.current_section == 1:
                        self.barrier_index = max(0, self.barrier_index - 1)
                    elif self.current_section == 2:
                        self.kids_mode = not self.kids_mode
                
                elif event.key == pygame.K_RIGHT:
                    if self.current_section == 0:
                        self.map_size_index = min(len(MAP_SIZE_ORDER) - 1, self.map_size_index + 1)
                    elif self.current_section == 1:
                        self.barrier_index = min(len(BARRIER_ORDER) - 1, self.barrier_index + 1)
                    elif self.current_section == 2:
                        self.kids_mode = not self.kids_mode
                
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.current_section == 3:
                        return 'start'
                    elif self.current_section == 2:
                        self.kids_mode = not self.kids_mode
                    elif event.key == pygame.K_RETURN:
                        self.current_section = 3
        
        return None
    
    def draw(self):
        """Draw the configuration screen."""
        self.screen.fill(MENU_BG)
        
        y_offset = 30
        
        # Title
        title = self.font_title.render("SANDBOX MODE", True, MENU_TITLE)
        title_rect = title.get_rect(centerx=self.MENU_WIDTH // 2, y=y_offset)
        self.screen.blit(title, title_rect)
        
        y_offset += 50
        
        subtitle = self.font_desc.render("Configure your game settings", True, MENU_DESCRIPTION)
        subtitle_rect = subtitle.get_rect(centerx=self.MENU_WIDTH // 2, y=y_offset)
        self.screen.blit(subtitle, subtitle_rect)
        
        y_offset += 45
        
        # Map Size Section
        self._draw_section(
            y_offset,
            "MAP SIZE",
            MAP_SIZE_ORDER,
            self.map_size_index,
            self.current_section == 0,
            lambda key: MAP_SIZES[key]['name'],
            lambda key: MAP_SIZES[key]['description']
        )
        
        y_offset += 110
        
        # Barrier Section
        self._draw_section(
            y_offset,
            "OBSTACLES",
            BARRIER_ORDER,
            self.barrier_index,
            self.current_section == 1,
            lambda key: BARRIER_DENSITIES[key]['name'],
            lambda key: BARRIER_DENSITIES[key]['description']
        )
        
        y_offset += 100
        
        # Kids Mode Section
        self._draw_kids_mode_section(y_offset, self.current_section == 2)
        
        y_offset += 70
        
        # Difficulty indicator
        difficulty = get_difficulty_label(self.get_selected_map_size(), self.get_selected_barrier())
        barrier_mult = BARRIER_DENSITIES[self.get_selected_barrier()]['multiplier']
        map_mult = MAP_SIZE_MULTIPLIERS[self.get_selected_map_size()]
        total_mult = barrier_mult * map_mult
        
        # Apply kids mode penalty to displayed multiplier
        if self.kids_mode:
            total_mult *= 0.5  # 50% penalty
        
        diff_text = f"Difficulty: {difficulty} | Score: x{total_mult:.1f}"
        diff_color = self._get_difficulty_color(difficulty)
        diff_surface = self.font_option.render(diff_text, True, diff_color)
        diff_rect = diff_surface.get_rect(centerx=self.MENU_WIDTH // 2, y=y_offset)
        self.screen.blit(diff_surface, diff_rect)
        
        y_offset += 40
        
        # Start Button
        self._draw_start_button(y_offset, self.current_section == 3)
        
        # Controls hint
        self._draw_controls_hint()
        
        pygame.display.flip()
    
    def _draw_section(self, y, title, options, selected_index, is_active, get_name, get_desc):
        """Draw a selection section."""
        header_color = MENU_SELECTED if is_active else MENU_TEXT
        header = self.font_header.render(title, True, header_color)
        header_rect = header.get_rect(centerx=self.MENU_WIDTH // 2, y=y)
        self.screen.blit(header, header_rect)
        
        options_y = y + 35
        total_width = 0
        option_surfaces = []
        
        for i, key in enumerate(options):
            name = get_name(key)
            is_selected = (i == selected_index)
            
            if is_selected:
                color = MENU_SELECTED if is_active else WHITE
            else:
                color = MENU_UNSELECTED
            
            surface = self.font_option.render(name, True, color)
            option_surfaces.append((surface, is_selected))
            total_width += surface.get_width() + 40
        
        x = (self.MENU_WIDTH - total_width + 40) // 2
        
        for surface, is_selected in option_surfaces:
            if is_selected and is_active:
                highlight_rect = pygame.Rect(
                    x - 10, options_y - 5,
                    surface.get_width() + 20, surface.get_height() + 10
                )
                pygame.draw.rect(self.screen, MENU_HIGHLIGHT_BG, highlight_rect, border_radius=5)
                pygame.draw.rect(self.screen, MENU_SELECTED, highlight_rect, 2, border_radius=5)
            
            self.screen.blit(surface, (x, options_y))
            x += surface.get_width() + 40
        
        if is_active:
            arrow_y = options_y + 5
            if selected_index > 0:
                arrow = self.font_option.render("<", True, MENU_SELECTED)
                self.screen.blit(arrow, (30, arrow_y))
            if selected_index < len(options) - 1:
                arrow = self.font_option.render(">", True, MENU_SELECTED)
                self.screen.blit(arrow, (self.MENU_WIDTH - 50, arrow_y))
        
        desc_y = options_y + 40
        selected_key = options[selected_index]
        desc = get_desc(selected_key)
        desc_surface = self.font_desc.render(desc, True, MENU_DESCRIPTION)
        desc_rect = desc_surface.get_rect(centerx=self.MENU_WIDTH // 2, y=desc_y)
        self.screen.blit(desc_surface, desc_rect)
    
    def _draw_kids_mode_section(self, y, is_active):
        """Draw the kids mode toggle section."""
        header_color = MENU_SELECTED if is_active else MENU_TEXT
        header = self.font_header.render("KIDS MODE", True, header_color)
        header_rect = header.get_rect(centerx=self.MENU_WIDTH // 2, y=y)
        self.screen.blit(header, header_rect)
        
        # Toggle buttons
        toggle_y = y + 32
        options = ["OFF", "ON"]
        total_width = 0
        option_surfaces = []
        
        for i, opt in enumerate(options):
            is_selected = (i == 1 and self.kids_mode) or (i == 0 and not self.kids_mode)
            
            if is_selected:
                color = (150, 200, 255) if self.kids_mode else MENU_SELECTED if is_active else WHITE
            else:
                color = MENU_UNSELECTED
            
            surface = self.font_option.render(opt, True, color)
            option_surfaces.append((surface, is_selected))
            total_width += surface.get_width() + 60
        
        x = (self.MENU_WIDTH - total_width + 60) // 2
        
        for surface, is_selected in option_surfaces:
            if is_selected and is_active:
                highlight_rect = pygame.Rect(
                    x - 12, toggle_y - 5,
                    surface.get_width() + 24, surface.get_height() + 10
                )
                bg_color = (50, 80, 120) if self.kids_mode else MENU_HIGHLIGHT_BG
                border_color = (150, 200, 255) if self.kids_mode else MENU_SELECTED
                pygame.draw.rect(self.screen, bg_color, highlight_rect, border_radius=5)
                pygame.draw.rect(self.screen, border_color, highlight_rect, 2, border_radius=5)
            
            self.screen.blit(surface, (x, toggle_y))
            x += surface.get_width() + 60
        
        # Description
        if self.kids_mode:
            desc = "Speed -30%, Score -50% (beginner-friendly)"
            desc_color = (150, 200, 255)
        else:
            desc = "Normal game speed and scoring"
            desc_color = MENU_DESCRIPTION
        
        desc_surface = self.font_desc.render(desc, True, desc_color)
        desc_rect = desc_surface.get_rect(centerx=self.MENU_WIDTH // 2, y=toggle_y + 30)
        self.screen.blit(desc_surface, desc_rect)
    
    def _draw_start_button(self, y, is_active):
        """Draw the start button."""
        button_width = 200
        button_height = 50
        button_x = (self.MENU_WIDTH - button_width) // 2
        button_rect = pygame.Rect(button_x, y, button_width, button_height)
        
        if is_active:
            pygame.draw.rect(self.screen, MENU_SELECTED, button_rect, border_radius=10)
            text_color = MENU_BG
        else:
            pygame.draw.rect(self.screen, MENU_UNSELECTED, button_rect, 2, border_radius=10)
            text_color = MENU_UNSELECTED
        
        text = self.font_header.render("START GAME", True, text_color)
        text_rect = text.get_rect(center=button_rect.center)
        self.screen.blit(text, text_rect)
    
    def _draw_controls_hint(self):
        """Draw controls hint."""
        hints = "Arrows: Navigate/Change | ENTER: Start | ESC: Back"
        surface = self.font_small.render(hints, True, GRAY)
        rect = surface.get_rect(centerx=self.MENU_WIDTH // 2, y=self.MENU_HEIGHT - 25)
        self.screen.blit(surface, rect)
    
    def _get_difficulty_color(self, difficulty):
        """Get color for difficulty label."""
        colors = {
            'Easy': (100, 200, 100),
            'Normal': (200, 200, 100),
            'Hard': (255, 165, 0),
            'Very Hard': (255, 100, 50),
            'Extreme': (255, 50, 50)
        }
        return colors.get(difficulty, WHITE)
    
    def run(self):
        """
        Run the configuration screen.
        
        Returns:
            dict: Game config, 'back' to return, or None if quit
        """
        while True:
            result = self.handle_events()
            
            if result == 'quit':
                return None
            elif result == 'back':
                return 'back'
            elif result == 'start':
                return {
                    'map_size': self.get_selected_map_size(),
                    'barriers': self.get_selected_barrier(),
                    'kids_mode': self.kids_mode
                }
            
            self.draw()
            self.clock.tick(30)


class StoryLevelSelectScreen:
    """
    Screen for selecting story mode level.
    """
    
    MENU_WIDTH = 700
    MENU_HEIGHT = 520
    LEVELS_PER_PAGE = 10
    
    def __init__(self, profile):
        """Initialize the level select screen."""
        self.screen = pygame.display.set_mode((self.MENU_WIDTH, self.MENU_HEIGHT))
        pygame.display.set_caption("Snake Game - Story Mode")
        
        self.profile = profile
        self.highest_level = profile.get_highest_level()
        
        self.font_title = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 26)
        self.font_tiny = pygame.font.Font(None, 22)
        
        # Start at current level
        self.selected_level = profile.get_current_level()
        self.page = (self.selected_level - 1) // self.LEVELS_PER_PAGE
        
        self.clock = pygame.time.Clock()
    
    def handle_events(self):
        """Handle input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 'quit'
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return 'back'
                
                elif event.key == pygame.K_UP:
                    if self.selected_level > 1:
                        self.selected_level -= 1
                        self.page = (self.selected_level - 1) // self.LEVELS_PER_PAGE
                
                elif event.key == pygame.K_DOWN:
                    if self.selected_level < min(99, self.highest_level):
                        self.selected_level += 1
                        self.page = (self.selected_level - 1) // self.LEVELS_PER_PAGE
                
                elif event.key == pygame.K_LEFT:
                    if self.page > 0:
                        self.page -= 1
                        self.selected_level = self.page * self.LEVELS_PER_PAGE + 1
                
                elif event.key == pygame.K_RIGHT:
                    max_page = (min(99, self.highest_level) - 1) // self.LEVELS_PER_PAGE
                    if self.page < max_page:
                        self.page += 1
                        self.selected_level = min(
                            self.page * self.LEVELS_PER_PAGE + 1,
                            self.highest_level
                        )
                
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.selected_level <= self.highest_level:
                        return {'level': self.selected_level}
        
        return None
    
    def draw(self):
        """Draw the level select screen."""
        self.screen.fill(MENU_BG)
        
        # Title
        title = self.font_title.render("STORY MODE", True, MENU_TITLE)
        title_rect = title.get_rect(centerx=self.MENU_WIDTH // 2, y=20)
        self.screen.blit(title, title_rect)
        
        # Progress
        progress = f"Progress: Level {self.highest_level}/99 ({(self.highest_level-1)/99*100:.0f}%)"
        progress_text = self.font_small.render(progress, True, MENU_DESCRIPTION)
        progress_rect = progress_text.get_rect(centerx=self.MENU_WIDTH // 2, y=65)
        self.screen.blit(progress_text, progress_rect)
        
        # Progress bar
        bar_width = 400
        bar_height = 12
        bar_x = (self.MENU_WIDTH - bar_width) // 2
        bar_y = 90
        
        pygame.draw.rect(self.screen, DARK_GRAY, (bar_x, bar_y, bar_width, bar_height), border_radius=6)
        fill_width = int((self.highest_level - 1) / 99 * bar_width)
        if fill_width > 0:
            pygame.draw.rect(self.screen, MENU_SELECTED, (bar_x, bar_y, fill_width, bar_height), border_radius=6)
        pygame.draw.rect(self.screen, GRAY, (bar_x, bar_y, bar_width, bar_height), 1, border_radius=6)
        
        # Level grid
        start_level = self.page * self.LEVELS_PER_PAGE + 1
        end_level = min(start_level + self.LEVELS_PER_PAGE - 1, 99)
        
        grid_y = 130
        col_width = 130
        row_height = 60
        cols = 5
        box_width = 110
        box_height = 50
        
        # Center the grid
        grid_total_width = cols * col_width
        grid_start_x = (self.MENU_WIDTH - grid_total_width) // 2
        
        for i, level in enumerate(range(start_level, end_level + 1)):
            col = i % cols
            row = i // cols
            
            x = grid_start_x + col * col_width
            y = grid_y + row * row_height
            
            is_selected = level == self.selected_level
            is_unlocked = level <= self.highest_level
            is_completed = str(level) in self.profile.data['story_progress']['levels_completed']
            
            # Level box
            box_rect = pygame.Rect(x, y, box_width, box_height)
            
            if is_selected:
                pygame.draw.rect(self.screen, MENU_HIGHLIGHT_BG, box_rect, border_radius=5)
                pygame.draw.rect(self.screen, MENU_SELECTED, box_rect, 2, border_radius=5)
            elif is_unlocked:
                pygame.draw.rect(self.screen, (35, 40, 45), box_rect, border_radius=5)
                if is_completed:
                    pygame.draw.rect(self.screen, (60, 100, 60), box_rect, 1, border_radius=5)
                else:
                    pygame.draw.rect(self.screen, GRAY, box_rect, 1, border_radius=5)
            else:
                pygame.draw.rect(self.screen, (25, 25, 25), box_rect, border_radius=5)
            
            # Level number (centered in left portion of box)
            if is_unlocked:
                color = MENU_SELECTED if is_selected else WHITE
            else:
                color = (60, 60, 60)
            
            level_text = self.font_medium.render(str(level), True, color)
            level_rect = level_text.get_rect(centerx=x + 35, centery=y + 18)
            self.screen.blit(level_text, level_rect)
            
            # Status indicator (right side of box, inside)
            if is_completed:
                # Small checkmark symbol
                status = self.font_tiny.render("[OK]", True, (100, 200, 100))
                status_rect = status.get_rect(right=x + box_width - 5, centery=y + 18)
                self.screen.blit(status, status_rect)
            elif not is_unlocked:
                # Lock indicator
                status = self.font_tiny.render("[X]", True, (100, 100, 100))
                status_rect = status.get_rect(right=x + box_width - 5, centery=y + 18)
                self.screen.blit(status, status_rect)
            
            # Best score (bottom center of box)
            if is_completed:
                best = self.profile.get_level_best_score(level)
                if best > 0:
                    score_text = self.font_tiny.render(f"{best}", True, MENU_DESCRIPTION)
                    score_rect = score_text.get_rect(centerx=x + box_width // 2, y=y + 32)
                    self.screen.blit(score_text, score_rect)
        
        # Page indicator
        total_pages = 10  # 99 levels / 10 per page
        page_text = self.font_small.render(f"Page {self.page + 1}/{total_pages}", True, GRAY)
        page_rect = page_text.get_rect(centerx=self.MENU_WIDTH // 2, y=270)
        self.screen.blit(page_text, page_rect)
        
        # Selected level info
        if self.selected_level <= self.highest_level:
            from .story_mode import get_level_preview
            info = get_level_preview(self.selected_level)
            
            info_y = 320
            pygame.draw.line(self.screen, GRAY, (50, info_y), (self.MENU_WIDTH - 50, info_y))
            
            info_y += 15
            header = self.font_medium.render(f"Level {self.selected_level}", True, WHITE)
            self.screen.blit(header, (50, info_y))
            
            info_y += 35
            details = [
                f"Size: {info['grid_size']}",
                f"Goal: {info['food_required']}",
                f"Spd: {info['speed']}",
                f"Mult: {info['multiplier']}",
                f"+{info['completion_bonus']}"
            ]
            
            # Calculate even spacing for details
            detail_spacing = (self.MENU_WIDTH - 100) // len(details)
            x = 50
            for detail in details:
                text = self.font_small.render(detail, True, MENU_DESCRIPTION)
                self.screen.blit(text, (x, info_y))
                x += detail_spacing
        
        # Controls hint
        hints = "Arrows: Navigate | ENTER: Play | ESC: Back"
        hint_text = self.font_tiny.render(hints, True, GRAY)
        hint_rect = hint_text.get_rect(centerx=self.MENU_WIDTH // 2, y=self.MENU_HEIGHT - 25)
        self.screen.blit(hint_text, hint_rect)
        
        pygame.display.flip()
    
    def run(self):
        """
        Run the level select screen.
        
        Returns:
            dict with 'level' key, 'back', or None if quit
        """
        while True:
            result = self.handle_events()
            
            if result == 'quit':
                return None
            elif result == 'back':
                return 'back'
            elif result is not None:
                return result
            
            self.draw()
            self.clock.tick(30)


# Legacy compatibility - redirect to new flow
class GameMenu:
    """Legacy menu class for backward compatibility."""
    
    def __init__(self):
        pass
    
    def run(self):
        """Run the full menu flow."""
        # This is now handled by the main game loop
        return None
