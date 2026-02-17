"""
Base Brawler class for Brawler game.

Defines shared functionality for all brawler characters.
"""

import math
from ..assets import (
    BRAWLER_STATS, BRAWLER_RADIUS, SUPER_CHARGE_MAX, FPS,
    FRICTION, KNOCKBACK_FORCE, distance, angle_to, normalize
)


class Brawler:
    """
    Base class for all brawler characters.
    
    Handles movement, health, ammo, super charge, and basic combat mechanics.
    Specific brawlers override attack() and super_ability() methods.
    """
    
    # Override in subclasses
    BRAWLER_ID = 'base'
    
    def __init__(self, team, spawn_x, spawn_y, player_controlled=True, player_id=None):
        """
        Initialize a brawler.
        
        Args:
            team: 0 (blue) or 1 (red)
            spawn_x, spawn_y: Starting position
            player_controlled: True if controlled by player, False for AI
            player_id: 'player1' or 'player2' for control mapping
        """
        # Get stats from assets
        self.stats = BRAWLER_STATS.get(self.BRAWLER_ID, BRAWLER_STATS['colt'])
        
        # Identity
        self.name = self.stats['name']
        self.team = team
        self.player_controlled = player_controlled
        self.player_id = player_id
        
        # Position and movement
        self.x = spawn_x
        self.y = spawn_y
        self.vx = 0
        self.vy = 0
        self.speed = self.stats['speed']
        self.radius = BRAWLER_RADIUS
        
        # Facing direction
        self.facing_angle = 0 if team == 0 else math.pi  # Face center
        
        # Health
        self.max_health = self.stats['max_health']
        self.health = self.max_health
        
        # Ammo system
        self.max_ammo = self.stats['max_ammo']
        self.ammo = self.max_ammo
        self.reload_time = self.stats['reload_time']
        self.reload_timer = 0
        
        # Super ability
        self.super_charge = 0
        self.super_charge_per_hit = self.stats.get('super_charge_per_hit', 10)
        self.super_charge_per_damage = self.stats.get('super_charge_per_damage', 10)
        
        # Combat state
        self.attack_cooldown = 0
        self.attack_timer = 0
        self.is_attacking = False
        
        # Colors for rendering
        self.colors = self.stats['colors']
        
        # State flags
        self.alive = True
        self.respawn_timer = 0
        self.invincible_timer = 0
        
        # Jump state (for Edgar and Piper supers)
        self.jumping = False
        self.jump_height = 0
        self.jump_target = None
        
        # Movement input
        self.move_x = 0
        self.move_y = 0
        
        # Spawn point for respawning
        self.spawn_x = spawn_x
        self.spawn_y = spawn_y
    
    def update(self, dt, arena, projectile_manager, ball=None):
        """
        Update brawler state.
        """
        # Update respawn
        if not self.alive:
            self._update_respawn(dt)
            return
        
        # Update invincibility
        if self.invincible_timer > 0:
            self.invincible_timer -= dt
        
        # Update jumping
        if self.jumping:
            self._update_jump(dt)
            return  # Can't act while jumping
        
        # Update cooldowns
        self._update_cooldowns(dt)
        
        # Update movement
        self._update_movement(dt, arena)
        
        # Update attack timer
        if self.attack_timer > 0:
            self.attack_timer -= dt
        
        # Auto-charge super (for Edgar)
        self._update_auto_charge(dt)
    
    def _update_cooldowns(self, dt):
        """
        Update reload and attack cooldowns.
        """
        # Reload ammo
        if self.ammo < self.max_ammo:
            self.reload_timer += dt
            if self.reload_timer >= self.reload_time:
                self.ammo += 1
                self.reload_timer = 0
        
        # Attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
    
    def _update_movement(self, dt, arena):
        """
        Update position based on movement input.
        """
        # Calculate movement vector
        if self.move_x != 0 or self.move_y != 0:
            # Normalize diagonal movement
            length = math.sqrt(self.move_x ** 2 + self.move_y ** 2)
            nx = self.move_x / length
            ny = self.move_y / length
            
            # Apply speed
            target_vx = nx * self.speed
            target_vy = ny * self.speed
            
            # Smooth acceleration
            self.vx = self.vx * 0.8 + target_vx * 0.2
            self.vy = self.vy * 0.8 + target_vy * 0.2
            
            # Update facing direction
            self.facing_angle = math.atan2(ny, nx)
        else:
            # Apply friction when not moving
            self.vx *= FRICTION
            self.vy *= FRICTION
            
            # Stop if very slow
            if abs(self.vx) < 1:
                self.vx = 0
            if abs(self.vy) < 1:
                self.vy = 0
        
        # Apply velocity
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Check wall collision
        collision, nx, ny = arena.check_wall_collision(self.x, self.y, self.radius)
        if collision:
            # Push out of wall
            self.x += nx * 5
            self.y += ny * 5
            # Stop velocity in that direction
            dot = self.vx * nx + self.vy * ny
            if dot < 0:
                self.vx -= dot * nx
                self.vy -= dot * ny
        
        # Keep in bounds
        self.x, self.y = arena.check_bounds(self.x, self.y, self.radius)
    
    def _update_auto_charge(self, dt):
        """
        Update auto-charging super (override in Edgar).
        """
        pass
    
    def _update_respawn(self, dt):
        """
        Update respawn timer.
        """
        self.respawn_timer -= dt
        if self.respawn_timer <= 0:
            self.respawn()
    
    def _update_jump(self, dt):
        """
        Update jump movement.
        """
        if self.jump_target is None:
            self.jumping = False
            return
        
        # Move towards target
        dx = self.jump_target[0] - self.x
        dy = self.jump_target[1] - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        jump_speed = 800 * dt
        
        if dist <= jump_speed:
            # Arrived
            self.x = self.jump_target[0]
            self.y = self.jump_target[1]
            self.jumping = False
            self.jump_target = None
            self.jump_height = 0
            self._on_land()
        else:
            # Move towards target
            self.x += (dx / dist) * jump_speed
            self.y += (dy / dist) * jump_speed
            
            # Arc height
            progress = 1 - (dist / self._jump_total_dist)
            self.jump_height = 40 * math.sin(progress * math.pi)
    
    def _on_land(self):
        """
        Called when landing from a jump. Override for Piper grenades.
        """
        pass
    
    def set_movement(self, x, y):
        """
        Set movement input (-1 to 1 for each axis).
        """
        self.move_x = max(-1, min(1, x))
        self.move_y = max(-1, min(1, y))
    
    def try_attack(self, projectile_manager):
        """
        Attempt to fire basic attack.
        Returns list of created projectiles.
        """
        if not self.alive or self.jumping:
            return []
        
        if self.ammo <= 0:
            return []
        
        if self.attack_cooldown > 0:
            return []
        
        # Use ammo
        self.ammo -= 1
        self.reload_timer = 0  # Reset reload
        
        # Set attack state
        self.is_attacking = True
        self.attack_timer = 0.2
        
        # Create projectiles (override in subclasses)
        return self.attack(projectile_manager)
    
    def try_super(self, projectile_manager, target_x=None, target_y=None):
        """
        Attempt to use super ability.
        """
        if not self.alive or self.jumping:
            return []
        
        if self.super_charge < SUPER_CHARGE_MAX:
            return []
        
        # Use super
        self.super_charge = 0
        
        # Execute super (override in subclasses)
        return self.super_ability(projectile_manager, target_x, target_y)
    
    def attack(self, projectile_manager):
        """
        Execute basic attack. Override in subclasses.
        Returns list of created projectiles.
        """
        return []
    
    def super_ability(self, projectile_manager, target_x=None, target_y=None):
        """
        Execute super ability. Override in subclasses.
        """
        return []
    
    def take_damage(self, amount, attacker=None):
        """
        Take damage from an attack.
        """
        if not self.alive:
            return
        
        if self.invincible_timer > 0:
            return
        
        if self.jumping:
            return  # Invincible while jumping
        
        self.health -= amount
        
        # Charge super from taking damage
        super_gain = (amount / 1000) * self.super_charge_per_damage
        self.charge_super(super_gain)
        
        # Check death
        if self.health <= 0:
            self.die()
    
    def heal(self, amount):
        """
        Heal health.
        """
        if not self.alive:
            return
        
        self.health = min(self.max_health, self.health + amount)
    
    def charge_super(self, amount):
        """
        Add to super charge.
        """
        self.super_charge = min(SUPER_CHARGE_MAX, self.super_charge + amount)
    
    def die(self):
        """
        Handle death.
        """
        self.alive = False
        self.health = 0
        self.respawn_timer = 3.0  # 3 second respawn
        
        # Drop ball if carrying
        # (handled by game loop)
    
    def respawn(self):
        """
        Respawn at spawn point.
        """
        self.alive = True
        self.health = self.max_health
        self.x = self.spawn_x
        self.y = self.spawn_y
        self.vx = 0
        self.vy = 0
        self.ammo = self.max_ammo
        self.invincible_timer = 2.0  # 2 seconds of invincibility
        self.jumping = False
        self.jump_height = 0
    
    def apply_knockback(self, angle, force):
        """
        Apply knockback force.
        """
        self.vx += math.cos(angle) * force
        self.vy += math.sin(angle) * force
    
    def start_jump(self, target_x, target_y, max_range):
        """
        Start a jump to target location.
        """
        # Limit jump distance
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist > max_range:
            # Clamp to max range
            dx = dx / dist * max_range
            dy = dy / dist * max_range
            target_x = self.x + dx
            target_y = self.y + dy
            dist = max_range
        
        self.jumping = True
        self.jump_target = (target_x, target_y)
        self._jump_total_dist = dist
    
    def get_aim_target(self, max_range=None):
        """
        Get target position for aiming based on facing direction.
        """
        if max_range is None:
            max_range = self.stats.get('attack_range', 300)
        
        target_x = self.x + math.cos(self.facing_angle) * max_range
        target_y = self.y + math.sin(self.facing_angle) * max_range
        return (target_x, target_y)
    
    def aim_at(self, target_x, target_y):
        """
        Set facing direction towards a target.
        """
        self.facing_angle = angle_to((self.x, self.y), (target_x, target_y))
    
    def is_super_ready(self):
        """
        Check if super ability is ready.
        """
        return self.super_charge >= SUPER_CHARGE_MAX
