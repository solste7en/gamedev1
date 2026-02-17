"""
Ball physics for Brawl Ball game mode.

Handles ball movement, kicking, and goal detection.
"""

import math
from .assets import (
    BALL_RADIUS, BALL_PICKUP_RANGE, BALL_SHOOT_SPEED,
    BALL_FRICTION, BRAWLER_RADIUS
)


class Ball:
    """
    The ball in Brawl Ball.
    
    Can be picked up by walking into it, kicked toward aim direction,
    and pushed by Shelly's super.
    """
    
    def __init__(self, x, y):
        """
        Initialize ball at position.
        
        Args:
            x, y: Starting world position
        """
        self.x = x
        self.y = y
        self.spawn_x = x
        self.spawn_y = y
        
        self.vx = 0
        self.vy = 0
        
        self.radius = BALL_RADIUS
        
        # State
        self.carrier = None  # Brawler carrying the ball
        self.last_carrier = None  # For tracking who scored
        
        # Visual effects
        self.bounce_height = 0
        self.bounce_velocity = 0
        self.rotation = 0
    
    @property
    def is_held(self):
        """Check if ball is being carried."""
        return self.carrier is not None
    
    def is_moving(self):
        """Check if ball is currently moving."""
        return self.vx != 0 or self.vy != 0
    
    def get_speed(self):
        """Get current ball speed."""
        return math.sqrt(self.vx * self.vx + self.vy * self.vy)
    
    def try_pickup(self, brawler):
        """
        Try to have a brawler pick up the ball.
        
        Args:
            brawler: Brawler attempting pickup
            
        Returns:
            True if successful, False otherwise
        """
        if self.carrier is not None:
            return False
        
        if not brawler.alive:
            return False
        
        dx = self.x - brawler.x
        dy = self.y - brawler.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist < BALL_PICKUP_RANGE + brawler.radius:
            self.pickup(brawler)
            return True
        return False
    
    def update(self, dt, arena, brawlers):
        """
        Update ball physics.
        
        Args:
            dt: Delta time in seconds
            arena: Arena for collision/goal checking
            brawlers: List of all brawlers (for pickup detection)
            
        Returns:
            str or None: 'blue' or 'red' if goal scored, else None
        """
        if self.carrier:
            # Ball follows carrier
            self._follow_carrier()
        else:
            # Free ball physics
            self._update_physics(dt, arena)
            
            # Check for pickup
            self._check_pickup(brawlers)
        
        # Update visual bounce
        self._update_bounce(dt)
        
        # Check for goal (only when not held)
        if not self.carrier:
            goal = arena.check_goal(self.x, self.y, self.radius)
            if goal:
                return goal
        
        return None
    
    def _follow_carrier(self):
        """Update position to follow carrier."""
        if not self.carrier or not self.carrier.alive:
            self.drop()
            return
        
        # Ball position slightly in front of carrier
        offset = BRAWLER_RADIUS + self.radius + 5
        self.x = self.carrier.x + math.cos(self.carrier.facing_angle) * offset
        self.y = self.carrier.y + math.sin(self.carrier.facing_angle) * offset
        
        # Zero velocity while held
        self.vx = 0
        self.vy = 0
    
    def _update_physics(self, dt, arena):
        """Update ball physics when free."""
        # Apply velocity
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Apply friction
        self.vx *= BALL_FRICTION
        self.vy *= BALL_FRICTION
        
        # Stop if very slow
        if abs(self.vx) < 5:
            self.vx = 0
        if abs(self.vy) < 5:
            self.vy = 0
        
        # Update rotation based on movement
        speed = math.sqrt(self.vx * self.vx + self.vy * self.vy)
        self.rotation += speed * dt * 0.05
        
        # Wall collision
        collision, nx, ny = arena.check_wall_collision(self.x, self.y, self.radius)
        if collision:
            # Bounce off wall
            dot = self.vx * nx + self.vy * ny
            self.vx = self.vx - 2 * dot * nx
            self.vy = self.vy - 2 * dot * ny
            
            # Push out of wall
            self.x += nx * 5
            self.y += ny * 5
            
            # Trigger bounce effect
            self._trigger_bounce()
        
        # Bounds check
        self.x, self.y = arena.check_bounds(self.x, self.y, self.radius)
    
    def _check_pickup(self, brawlers):
        """Check if any brawler picks up the ball."""
        for brawler in brawlers:
            if not brawler.alive or brawler.has_ball:
                continue
            
            # Check distance
            dx = self.x - brawler.x
            dy = self.y - brawler.y
            dist = math.sqrt(dx * dx + dy * dy)
            
            if dist < BALL_PICKUP_RANGE + brawler.radius:
                self.pickup(brawler)
                break
    
    def _update_bounce(self, dt):
        """Update visual bounce effect."""
        if self.bounce_height > 0 or self.bounce_velocity != 0:
            self.bounce_velocity -= 500 * dt  # Gravity
            self.bounce_height += self.bounce_velocity * dt
            
            if self.bounce_height <= 0:
                self.bounce_height = 0
                # Small bounce back
                if abs(self.bounce_velocity) > 50:
                    self.bounce_velocity = -self.bounce_velocity * 0.4
                else:
                    self.bounce_velocity = 0
    
    def _trigger_bounce(self):
        """Trigger a small visual bounce."""
        speed = math.sqrt(self.vx * self.vx + self.vy * self.vy)
        self.bounce_velocity = min(speed * 0.3, 150)
    
    def pickup(self, brawler):
        """
        Brawler picks up the ball.
        
        Args:
            brawler: Brawler picking up the ball
        """
        self.carrier = brawler
        self.last_carrier = brawler
        brawler.pick_up_ball()
    
    def drop(self):
        """Drop the ball (carrier died or scored)."""
        if self.carrier:
            self.carrier.drop_ball()
            self.carrier = None
    
    def kick(self, angle=None, speed=None):
        """
        Kick the ball in a direction.
        
        Args:
            angle: Direction angle (radians), defaults to carrier's facing
            speed: Kick speed, defaults to BALL_SHOOT_SPEED
        """
        if not self.carrier:
            return
        
        if angle is None:
            angle = self.carrier.facing_angle
        if speed is None:
            speed = BALL_SHOOT_SPEED
        
        # Set velocity
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        
        # Release from carrier
        self.drop()
        
        # Trigger bounce effect
        self.bounce_velocity = 100
    
    def push(self, angle, force):
        """
        Push the ball (from Shelly super).
        
        Args:
            angle: Push direction
            force: Push force
        """
        if self.carrier:
            self.drop()
        
        self.vx += math.cos(angle) * force
        self.vy += math.sin(angle) * force
        
        # Trigger bounce
        self.bounce_velocity = 80
    
    def reset(self, x=None, y=None):
        """
        Reset ball to spawn position.
        
        Args:
            x, y: Optional new position, defaults to spawn
        """
        if x is None:
            x = self.spawn_x
        if y is None:
            y = self.spawn_y
        
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.carrier = None
        self.bounce_height = 0
        self.bounce_velocity = 0
        self.rotation = 0
    
    def get_state(self):
        """
        Get serializable state.
        
        Returns:
            dict with ball state
        """
        return {
            'x': self.x,
            'y': self.y,
            'vx': self.vx,
            'vy': self.vy,
            'carrier': self.carrier.name if self.carrier else None,
            'carrier_team': self.carrier.team if self.carrier else None
        }
