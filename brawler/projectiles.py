"""
Projectile classes for Brawler game.

Includes bullets, pellets, sniper shots, melee attacks, and grenades.
"""

import math
import pygame
from .assets import (
    BULLET_RADIUS, PELLET_RADIUS, SNIPER_RADIUS,
    BRAWLER_RADIUS, BALL_RADIUS
)


class Projectile:
    """
    Base class for all projectiles.
    """
    
    def __init__(self, x, y, angle, speed, damage, owner, color, max_range):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.angle = angle
        self.speed = speed
        self.damage = damage
        self.owner = owner
        self.color = color
        self.max_range = max_range
        self.radius = BULLET_RADIUS
        
        # Velocity
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        
        # State
        self.alive = True
        self.distance_traveled = 0
        self.piercing = False
        self.destroys_walls = False
        self.knockback = 0
        self.is_super = False
        self.hit_targets = set()  # Track hit targets for piercing
    
    def update(self, dt, arena):
        """
        Update projectile position.
        
        Args:
            dt: Delta time in seconds
            arena: Arena for collision checking
            
        Returns:
            bool: True if projectile should be removed
        """
        if not self.alive:
            return True
        
        # Move
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Track distance
        dx = self.x - self.start_x
        dy = self.y - self.start_y
        self.distance_traveled = math.sqrt(dx * dx + dy * dy)
        
        # Check range
        if self.distance_traveled >= self.max_range:
            self.alive = False
            return True
        
        # Check wall collision
        collision, nx, ny = arena.check_wall_collision(self.x, self.y, self.radius)
        if collision:
            if self.destroys_walls:
                # Could trigger wall destruction here
                pass
            else:
                self.alive = False
                return True
        
        # Check bounds
        if not arena.point_in_arena(self.x, self.y):
            self.alive = False
            return True
        
        return False
    
    def check_hit(self, target):
        """
        Check if projectile hits a target brawler.
        
        Args:
            target: Brawler to check collision with
            
        Returns:
            bool: True if hit
        """
        if not self.alive or not target.alive:
            return False
        
        # Don't hit same team
        if target.team == self.owner.team:
            return False
        
        # Don't hit invulnerable targets
        if target.is_invulnerable:
            return False
        
        # Don't hit same target twice (for piercing)
        if id(target) in self.hit_targets:
            return False
        
        # Circle collision
        dx = target.x - self.x
        dy = target.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist < self.radius + target.radius:
            self.hit_targets.add(id(target))
            if not self.piercing:
                self.alive = False
            return True
        
        return False
    
    def check_ball_hit(self, ball):
        """
        Check if projectile hits the ball (for Shelly super).
        
        Args:
            ball: Ball object
            
        Returns:
            bool: True if hit
        """
        if not self.alive or not self.is_super:
            return False
        
        dx = ball.x - self.x
        dy = ball.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist < self.radius + ball.radius:
            return True
        
        return False
    
    def get_knockback_dir(self):
        """Get knockback direction vector."""
        if self.knockback > 0:
            return (math.cos(self.angle) * self.knockback,
                    math.sin(self.angle) * self.knockback)
        return None


class Bullet(Projectile):
    """
    Standard bullet (Colt's attack).
    """
    
    def __init__(self, x, y, angle, speed, damage, owner, color, max_range,
                 piercing=False, destroys_walls=False):
        super().__init__(x, y, angle, speed, damage, owner, color, max_range)
        self.radius = BULLET_RADIUS
        self.piercing = piercing
        self.destroys_walls = destroys_walls
        self.projectile_type = 'bullet'


class Pellet(Projectile):
    """
    Shotgun pellet (Shelly's attack).
    """
    
    def __init__(self, x, y, angle, speed, damage, owner, color, max_range,
                 knockback=0, is_super=False):
        super().__init__(x, y, angle, speed, damage, owner, color, max_range)
        self.radius = PELLET_RADIUS
        self.knockback = knockback
        self.is_super = is_super
        self.projectile_type = 'pellet'


class SniperBullet(Projectile):
    """
    Sniper shot (Piper's attack).
    Damage scales with distance traveled.
    """
    
    def __init__(self, x, y, angle, speed, damage_min, damage_max, owner, color, max_range):
        # Start with minimum damage
        super().__init__(x, y, angle, speed, damage_min, owner, color, max_range)
        self.radius = SNIPER_RADIUS
        self.damage_min = damage_min
        self.damage_max = damage_max
        self.projectile_type = 'sniper'
    
    @property
    def current_damage(self):
        """Calculate damage based on distance traveled."""
        # Damage scales from min to max over the range
        progress = min(1.0, self.distance_traveled / self.max_range)
        return self.damage_min + (self.damage_max - self.damage_min) * progress
    
    def check_hit(self, target):
        """Override to use scaled damage."""
        if super().check_hit(target):
            # Update damage to current scaled value
            self.damage = self.current_damage
            return True
        return False


class MeleeAttack:
    """
    Melee attack hitbox (Edgar's attack).
    Creates a temporary arc-shaped hitbox.
    """
    
    def __init__(self, owner, angle, damage, range, arc_angle, duration,
                 delay=0, heal_percent=0):
        self.owner = owner
        self.angle = angle
        self.damage = damage
        self.range = range
        self.arc_angle = arc_angle  # Half-angle of the arc
        self.duration = duration
        self.delay = delay
        self.heal_percent = heal_percent
        
        # State
        self.alive = True
        self.timer = 0
        self.active = False
        self.hit_targets = set()
        
        # For compatibility with projectile list
        self.x = owner.x
        self.y = owner.y
        self.projectile_type = 'melee'
    
    def update(self, dt, arena):
        """
        Update melee attack state.
        """
        if not self.alive:
            return True
        
        self.timer += dt
        
        # Handle delay before becoming active
        if self.timer < self.delay:
            return False
        
        # Become active
        if not self.active:
            self.active = True
            self.timer = 0
        
        # Update position to follow owner
        self.x = self.owner.x
        self.y = self.owner.y
        self.angle = self.owner.facing_angle
        
        # Check duration
        if self.timer >= self.duration:
            self.alive = False
            return True
        
        return False
    
    def check_hit(self, target):
        """
        Check if target is within melee arc.
        """
        if not self.alive or not self.active or not target.alive:
            return False
        
        # Don't hit same team
        if target.team == self.owner.team:
            return False
        
        # Don't hit invulnerable
        if target.is_invulnerable:
            return False
        
        # Don't hit same target twice
        if id(target) in self.hit_targets:
            return False
        
        # Check distance
        dx = target.x - self.owner.x
        dy = target.y - self.owner.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist > self.range + target.radius:
            return False
        
        # Check angle
        target_angle = math.atan2(dy, dx)
        angle_diff = abs(self._angle_diff(target_angle, self.angle))
        
        if angle_diff <= self.arc_angle:
            self.hit_targets.add(id(target))
            return True
        
        return False
    
    def _angle_diff(self, a1, a2):
        """Calculate smallest angle difference."""
        diff = a1 - a2
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        return diff
    
    def check_ball_hit(self, ball):
        """Melee attacks don't hit the ball."""
        return False
    
    def get_knockback_dir(self):
        """Get knockback direction for melee."""
        return (math.cos(self.angle) * 200, math.sin(self.angle) * 200)


class Grenade:
    """
    Grenade projectile (Piper's super).
    Explodes after a delay.
    """
    
    def __init__(self, x, y, damage, owner, delay):
        self.x = x
        self.y = y
        self.damage = damage
        self.owner = owner
        self.delay = delay
        self.radius = 10
        self.explosion_radius = 60
        
        # State
        self.alive = True
        self.timer = 0
        self.exploded = False
        self.explosion_timer = 0
        self.explosion_duration = 0.3
        
        self.projectile_type = 'grenade'
        self.hit_targets = set()
    
    def update(self, dt, arena):
        """Update grenade state."""
        if not self.alive:
            return True
        
        self.timer += dt
        
        if not self.exploded:
            # Wait for delay
            if self.timer >= self.delay:
                self.exploded = True
                self.timer = 0
        else:
            # Explosion active
            self.explosion_timer += dt
            if self.explosion_timer >= self.explosion_duration:
                self.alive = False
                return True
        
        return False
    
    def check_hit(self, target):
        """Check if target is in explosion radius."""
        if not self.alive or not self.exploded or not target.alive:
            return False
        
        # Don't hit same team
        if target.team == self.owner.team:
            return False
        
        # Don't hit invulnerable
        if target.is_invulnerable:
            return False
        
        # Don't hit same target twice
        if id(target) in self.hit_targets:
            return False
        
        # Check explosion radius
        dx = target.x - self.x
        dy = target.y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist <= self.explosion_radius + target.radius:
            self.hit_targets.add(id(target))
            return True
        
        return False
    
    def check_ball_hit(self, ball):
        """Grenades don't hit the ball."""
        return False
    
    def get_knockback_dir(self):
        """No knockback from grenades."""
        return None
