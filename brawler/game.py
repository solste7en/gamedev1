"""
Main game module for Brawler.

Manages game state, main loop, collision detection, and rendering.
"""

import pygame
import random
import math
from .assets import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS,
    MATCH_DURATION, GOALS_TO_WIN, RESPAWN_TIME,
    BRAWLER_STATS, SUPER_CHARGE_MAX
)
from .arena import Arena
from .ball import Ball
from .brawlers import BRAWLER_CLASSES
from .ai import BrawlerAI as BotAI
from .hud import HUD
from .menu import Menu, MenuState
from . import graphics


class GameState:
    """Game state constants."""
    MENU = 'menu'
    COUNTDOWN = 'countdown'
    PLAYING = 'playing'
    GOAL = 'goal'
    GAME_OVER = 'game_over'
    PAUSED = 'paused'


class ProjectileManager:
    """Simple wrapper to allow list-like operations with add() method."""
    
    def __init__(self, projectile_list):
        self._list = projectile_list
    
    def add(self, projectile):
        """Add a projectile to the list."""
        self._list.append(projectile)
    
    def __iter__(self):
        return iter(self._list)
    
    def __len__(self):
        return len(self._list)


class BrawlerGame:
    """
    Main Brawler game class.
    
    Handles game loop, state management, and coordinates all game systems.
    """
    
    def __init__(self):
        """Initialize the game."""
        pygame.init()
        
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Brawler - Brawl Ball")
        
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game state
        self.state = GameState.MENU
        
        # Game objects
        self.arena = None
        self.ball = None
        self.brawlers = []
        self.projectiles = []
        self.bots = []
        
        # Teams
        self.teams = {0: [], 1: []}  # 0 = blue, 1 = red
        
        # Match state
        self.score = [0, 0]
        self.time_left = MATCH_DURATION
        self.overtime = False
        
        # Countdown
        self.countdown = 3
        self.countdown_timer = 0
        
        # Goal celebration
        self.goal_timer = 0
        self.goal_duration = 2.0
        self.scoring_team = None
        
        # Game mode
        self.game_mode = None  # '2p', 'ai', 'practice'
        
        # UI components
        self.menu = Menu()
        self.hud = HUD()
        
        # Camera
        self.camera_x = 0
        self.camera_y = 0
    
    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0  # Convert to seconds
            
            self._handle_events()
            self._update(dt)
            self._draw()
            
            pygame.display.flip()
        
        return 'menu'
    
    def _handle_events(self):
        """Handle input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.MENU:
                        self.running = False
                    elif self.state == GameState.PLAYING:
                        self.state = GameState.PAUSED
                    elif self.state == GameState.PAUSED:
                        self.state = GameState.PLAYING
                    elif self.state == GameState.GAME_OVER:
                        self._reset_to_menu()
                
                elif self.state == GameState.GAME_OVER:
                    if event.key == pygame.K_SPACE:
                        self._start_match()
            
            # Pass events to menu
            if self.state == GameState.MENU:
                result = self.menu.handle_event(event)
                if result == MenuState.BACK:
                    self.running = False
                elif result == MenuState.READY:
                    self._start_match()
    
    def _update(self, dt):
        """Update game state."""
        if self.state == GameState.MENU:
            self.menu.update(dt)
        
        elif self.state == GameState.COUNTDOWN:
            self._update_countdown(dt)
        
        elif self.state == GameState.PLAYING:
            self._update_match(dt)
        
        elif self.state == GameState.GOAL:
            self._update_goal_celebration(dt)
        
        elif self.state == GameState.PAUSED:
            pass  # Do nothing while paused
    
    def _update_countdown(self, dt):
        """Update countdown before match."""
        self.countdown_timer += dt
        
        if self.countdown_timer >= 1.0:
            self.countdown_timer = 0
            self.countdown -= 1
            
            if self.countdown < 0:
                self.state = GameState.PLAYING
    
    def _update_match(self, dt):
        """Update match gameplay."""
        # Update timer
        if self.game_mode != 'practice':
            self.time_left -= dt
            
            # Check overtime
            if self.time_left <= 0:
                if self.score[0] == self.score[1]:
                    # Tied - overtime
                    self.overtime = True
                else:
                    # Game over
                    self._end_match()
                    return
        
        # Handle player input
        self._handle_player_input()
        
        # Update AI bots
        proj_manager = ProjectileManager(self.projectiles)
        for bot in self.bots:
            team = bot.brawler.team
            teammates = [b for b in self.teams[team] if b != bot.brawler]
            enemies = self.teams[1 - team]
            bot.update(dt, self.ball, teammates, enemies, proj_manager)
        
        # Update brawlers
        for brawler in self.brawlers:
            brawler.update(dt, self.arena, proj_manager, self.ball)
        
        # Update projectiles
        self._update_projectiles(dt)
        
        # Update ball
        goal = self.ball.update(dt, self.arena, self.brawlers)
        if goal:
            self._on_goal(0 if goal == 'blue' else 1)
        
        # Handle ball carrier kicking
        self._handle_ball_kicking()
        
        # Update camera
        self._update_camera()
    
    def _update_projectiles(self, dt):
        """Update all projectiles and check collisions."""
        projectiles_to_remove = []
        
        for proj in self.projectiles:
            # Update projectile
            should_remove = proj.update(dt, self.arena)
            if should_remove:
                projectiles_to_remove.append(proj)
                continue
            
            # Check brawler collisions
            for brawler in self.brawlers:
                if proj.check_hit(brawler):
                    # Deal damage
                    brawler.take_damage(proj.damage, proj.owner)
                    
                    # Apply knockback if projectile has it
                    knockback = proj.get_knockback_dir()
                    if knockback:
                        brawler.apply_knockback(proj.angle, knockback[0] if isinstance(knockback, tuple) else knockback)
                    
                    # Charge attacker's super
                    if proj.owner:
                        proj.owner.charge_super(proj.owner.super_charge_per_hit)
                        
                        # Edgar lifesteal
                        if hasattr(proj.owner, 'on_damage_dealt'):
                            proj.owner.on_damage_dealt(proj.damage)
                    
                    if not getattr(proj, 'piercing', False):
                        projectiles_to_remove.append(proj)
                        break
            
            # Check ball collision (Shelly super)
            if hasattr(proj, 'is_super') and proj.is_super:
                if proj.check_ball_hit(self.ball):
                    self.ball.push(proj.angle, proj.knockback or 300)
        
        # Remove dead projectiles
        for proj in projectiles_to_remove:
            if proj in self.projectiles:
                self.projectiles.remove(proj)
    
    def _handle_player_input(self):
        """Handle player movement and actions."""
        keys = pygame.key.get_pressed()
        proj_manager = ProjectileManager(self.projectiles)
        
        # Player 1 (Blue team, index 0)
        if len(self.teams[0]) > 0:
            p1 = self.teams[0][0]
            if p1.player_controlled and p1.alive:
                # Movement
                dx = 0
                dy = 0
                if keys[pygame.K_w]:
                    dy -= 1
                if keys[pygame.K_s]:
                    dy += 1
                if keys[pygame.K_a]:
                    dx -= 1
                if keys[pygame.K_d]:
                    dx += 1
                
                p1.set_movement(dx, dy)
                
                # Attack
                if keys[pygame.K_SPACE]:
                    p1.try_attack(proj_manager)
                
                # Super
                if keys[pygame.K_e]:
                    target = self._get_aim_target(p1)
                    p1.try_super(proj_manager, target[0], target[1])
        
        # Player 2 (Red team, index 0) - only in 2P mode
        if self.game_mode == '2p' and len(self.teams[1]) > 0:
            p2 = self.teams[1][0]
            if p2.player_controlled and p2.alive:
                # Movement
                dx = 0
                dy = 0
                if keys[pygame.K_UP]:
                    dy -= 1
                if keys[pygame.K_DOWN]:
                    dy += 1
                if keys[pygame.K_LEFT]:
                    dx -= 1
                if keys[pygame.K_RIGHT]:
                    dx += 1
                
                p2.set_movement(dx, dy)
                
                # Attack
                if keys[pygame.K_RETURN]:
                    p2.try_attack(proj_manager)
                
                # Super
                if keys[pygame.K_RSHIFT]:
                    target = self._get_aim_target(p2)
                    p2.try_super(proj_manager, target[0], target[1])
    
    def _handle_ball_kicking(self):
        """Handle ball kicking when carrier attacks."""
        for brawler in self.brawlers:
            if brawler.has_ball:
                # Check if player is attacking (via attack timer recently activated)
                if brawler.attack_timer > 0.2:  # Just started attacking
                    self.ball.kick()
    
    def _get_aim_target(self, brawler):
        """Get aim target position for super ability."""
        # For now, just aim in facing direction
        dist = 200
        return (
            brawler.x + math.cos(brawler.facing_angle) * dist,
            brawler.y + math.sin(brawler.facing_angle) * dist
        )
    
    def _get_ai_game_state(self):
        """Get game state dict for AI decision making."""
        return {
            'ball': self.ball,
            'arena': self.arena,
            'projectiles': self.projectiles,
            'teammates': [],  # Filled per bot
            'enemies': [],    # Filled per bot
            'my_goal': None,
            'enemy_goal': None
        }
    
    def _update_goal_celebration(self, dt):
        """Update goal celebration animation."""
        self.goal_timer += dt
        
        if self.goal_timer >= self.goal_duration:
            # Check for win
            if self.score[self.scoring_team] >= GOALS_TO_WIN:
                self._end_match()
            else:
                # Reset for next round
                self._reset_round()
                self.state = GameState.COUNTDOWN
                self.countdown = 3
                self.countdown_timer = 0
    
    def _update_camera(self):
        """Update camera to follow action."""
        # Center camera on ball
        target_x = self.ball.x
        target_y = self.ball.y
        
        # Smooth follow
        self.camera_x += (target_x - self.camera_x) * 0.1
        self.camera_y += (target_y - self.camera_y) * 0.1
    
    def _on_goal(self, scoring_team):
        """Handle goal scored."""
        self.score[scoring_team] += 1
        self.scoring_team = scoring_team
        self.goal_timer = 0
        self.state = GameState.GOAL
        
        # In overtime, any goal ends game
        if self.overtime:
            self._end_match()
    
    def _end_match(self):
        """End the match."""
        self.state = GameState.GAME_OVER
    
    def _start_match(self):
        """Start a new match."""
        self.game_mode = self.menu.get_game_mode()
        p1_brawler, p2_brawler = self.menu.get_selected_brawlers()
        
        # Initialize arena
        self.arena = Arena()
        
        # Initialize ball
        center = self.arena.get_center()
        self.ball = Ball(center[0], center[1])
        
        # Clear existing
        self.brawlers = []
        self.projectiles = []
        self.bots = []
        self.teams = {0: [], 1: []}
        
        # Create brawlers
        self._create_team_brawlers(p1_brawler, p2_brawler)
        
        # Reset match state
        self.score = [0, 0]
        self.time_left = MATCH_DURATION
        self.overtime = False
        
        # Start countdown
        self.state = GameState.COUNTDOWN
        self.countdown = 3
        self.countdown_timer = 0
    
    def _create_team_brawlers(self, p1_brawler, p2_brawler):
        """Create brawlers for both teams."""
        # Blue team (team 0)
        # Player 1
        spawn = self.arena.get_spawn_point(0, 0)
        BrawlerClass = BRAWLER_CLASSES[p1_brawler]
        p1 = BrawlerClass(0, spawn[0], spawn[1], player_controlled=True)
        self.brawlers.append(p1)
        self.teams[0].append(p1)
        
        # Blue AI teammate
        spawn = self.arena.get_spawn_point(0, 1)
        ai_brawler = random.choice(list(BRAWLER_CLASSES.keys()))
        BrawlerClass = BRAWLER_CLASSES[ai_brawler]
        blue_ai = BrawlerClass(0, spawn[0], spawn[1], player_controlled=False)
        self.brawlers.append(blue_ai)
        self.teams[0].append(blue_ai)
        self.bots.append(BotAI(blue_ai, self.arena))
        
        # Red team (team 1)
        if self.game_mode == '2p':
            # Player 2
            spawn = self.arena.get_spawn_point(1, 0)
            BrawlerClass = BRAWLER_CLASSES[p2_brawler]
            p2 = BrawlerClass(1, spawn[0], spawn[1], player_controlled=True)
            self.brawlers.append(p2)
            self.teams[1].append(p2)
        else:
            # AI opponent
            spawn = self.arena.get_spawn_point(1, 0)
            ai_brawler = random.choice(list(BRAWLER_CLASSES.keys()))
            BrawlerClass = BRAWLER_CLASSES[ai_brawler]
            red_ai1 = BrawlerClass(1, spawn[0], spawn[1], player_controlled=False)
            self.brawlers.append(red_ai1)
            self.teams[1].append(red_ai1)
            self.bots.append(BotAI(red_ai1, self.arena))
        
        # Red AI teammate
        spawn = self.arena.get_spawn_point(1, 1)
        ai_brawler = random.choice(list(BRAWLER_CLASSES.keys()))
        BrawlerClass = BRAWLER_CLASSES[ai_brawler]
        red_ai2 = BrawlerClass(1, spawn[0], spawn[1], player_controlled=False)
        self.brawlers.append(red_ai2)
        self.teams[1].append(red_ai2)
        self.bots.append(BotAI(red_ai2, self.arena))
        
        # Set up AI game state references
        for bot in self.bots:
            team = bot.brawler.team
            bot_state = {
                'ball': self.ball,
                'arena': self.arena,
                'projectiles': self.projectiles,
                'teammates': [b for b in self.teams[team] if b != bot.brawler],
                'enemies': self.teams[1 - team],
                'my_goal': (0 if team == 0 else self.arena.world_width,
                           self.arena.world_height // 2),
                'enemy_goal': (self.arena.world_width if team == 0 else 0,
                              self.arena.world_height // 2)
            }
            # Store reference for updates
            bot._game_state_ref = bot_state
    
    def _reset_round(self):
        """Reset for next round after goal."""
        # Reset ball
        self.ball.reset()
        
        # Reset brawler positions
        for team in [0, 1]:
            for i, brawler in enumerate(self.teams[team]):
                spawn = self.arena.get_spawn_point(team, i)
                brawler.set_spawn_position(spawn[0], spawn[1])
                brawler.health = brawler.max_health
                brawler.ammo = brawler.max_ammo
                brawler.has_ball = False
                brawler.alive = True
        
        # Clear projectiles
        self.projectiles = []
        
        # Reset arena walls
        self.arena.reset_walls()
    
    def _reset_to_menu(self):
        """Reset game to menu."""
        self.state = GameState.MENU
        self.menu.reset()
    
    def _draw(self):
        """Draw current game state."""
        if self.state == GameState.MENU:
            self.menu.draw(self.screen)
        else:
            self._draw_game()
    
    def _draw_game(self):
        """Draw the game scene."""
        # Clear screen
        self.screen.fill((20, 25, 30))
        
        # Draw arena
        graphics.draw_arena_floor(self.screen, self.arena, self.camera_x, self.camera_y)
        graphics.draw_arena_lines(self.screen, self.arena, self.camera_x, self.camera_y)
        graphics.draw_goals(self.screen, self.arena, self.camera_x, self.camera_y)
        graphics.draw_walls(self.screen, self.arena, self.camera_x, self.camera_y)
        
        # Sort entities by Y position for proper depth
        entities = []
        
        # Add brawlers
        for brawler in self.brawlers:
            if brawler.alive:
                entities.append(('brawler', brawler.y, brawler))
        
        # Add ball
        if not self.ball.is_held:
            entities.append(('ball', self.ball.y, self.ball))
        
        # Add projectiles
        for proj in self.projectiles:
            entities.append(('projectile', proj.y, proj))
        
        # Sort by Y
        entities.sort(key=lambda e: e[1])
        
        # Draw entities
        for entity_type, _, entity in entities:
            if entity_type == 'brawler':
                graphics.draw_brawler(self.screen, entity, self.camera_x, self.camera_y)
                graphics.draw_brawler_health_bar(self.screen, entity, self.camera_x, self.camera_y)
                graphics.draw_super_ready_effect(self.screen, entity, self.camera_x, self.camera_y)
            elif entity_type == 'ball':
                graphics.draw_ball(self.screen, entity, self.camera_x, self.camera_y)
            elif entity_type == 'projectile':
                self._draw_projectile(entity)
        
        # Draw HUD
        hud_state = self._get_hud_state()
        self.hud.draw(self.screen, hud_state)
        
        # Draw countdown
        if self.state == GameState.COUNTDOWN:
            count = self.countdown if self.countdown > 0 else "GO"
            self.hud.draw_countdown(self.screen, count)
        
        # Draw goal celebration
        elif self.state == GameState.GOAL:
            progress = self.goal_timer / self.goal_duration
            self.hud.draw_goal_celebration(self.screen, self.scoring_team, progress)
        
        # Draw game over
        elif self.state == GameState.GAME_OVER:
            winner = None
            if self.score[0] > self.score[1]:
                winner = 0
            elif self.score[1] > self.score[0]:
                winner = 1
            self.hud.draw_game_over(self.screen, winner, self.score)
        
        # Draw pause overlay
        elif self.state == GameState.PAUSED:
            self._draw_pause_overlay()
    
    def _draw_projectile(self, proj):
        """Draw a projectile based on its type."""
        proj_type = getattr(proj, 'projectile_type', 'bullet')
        
        if proj_type == 'bullet':
            graphics.draw_bullet(self.screen, proj, self.camera_x, self.camera_y)
        elif proj_type == 'pellet':
            graphics.draw_pellet(self.screen, proj, self.camera_x, self.camera_y)
        elif proj_type == 'sniper':
            graphics.draw_sniper_bullet(self.screen, proj, self.camera_x, self.camera_y)
        elif proj_type == 'melee':
            if proj.active:
                graphics.draw_melee_arc(self.screen, proj.owner, self.camera_x, self.camera_y)
        elif proj_type == 'grenade':
            sx, sy = graphics.world_to_screen(proj.x, proj.y, self.camera_x, self.camera_y)
            if proj.exploded:
                # Draw explosion
                radius = int(proj.explosion_radius * (1 - proj.explosion_timer / proj.explosion_duration))
                pygame.draw.circle(self.screen, (255, 200, 100), (sx, sy), radius)
                pygame.draw.circle(self.screen, (255, 100, 50), (sx, sy), radius, 3)
            else:
                # Draw grenade
                pygame.draw.circle(self.screen, (100, 100, 100), (sx, sy), proj.radius)
                pygame.draw.circle(self.screen, (50, 50, 50), (sx, sy), proj.radius, 2)
    
    def _draw_pause_overlay(self):
        """Draw pause screen overlay."""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        font = pygame.font.Font(None, 72)
        text = font.render("PAUSED", True, (255, 255, 255))
        text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 30))
        self.screen.blit(text, text_rect)
        
        font_small = pygame.font.Font(None, 32)
        hint = font_small.render("Press ESC to resume", True, (200, 200, 200))
        hint_rect = hint.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 30))
        self.screen.blit(hint, hint_rect)
    
    def _get_hud_state(self):
        """Get state dict for HUD rendering."""
        players = []
        for team in [0, 1]:
            for brawler in self.teams[team]:
                players.append({
                    'team': team,
                    'name': 'P1' if brawler.player_controlled and team == 0 else 
                            'P2' if brawler.player_controlled else 'AI',
                    'brawler': brawler.name,
                    'health': brawler.health,
                    'max_health': brawler.max_health,
                    'super_charge': brawler.super_charge
                })
        
        return {
            'score': self.score,
            'time_left': max(0, self.time_left),
            'overtime': self.overtime,
            'players': players,
            'message': None
        }
