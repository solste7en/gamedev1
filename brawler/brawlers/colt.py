"""
Colt brawler for Brawler game.

Long-range sharpshooter with rapid-fire bullets.
- Attack: Fires 6 bullets in a tight line
- Super: Fires 12 piercing bullets that destroy walls
"""

import math
from .base import Brawler
from ..projectiles import Bullet
from ..assets import BRAWLER_STATS


class Colt(Brawler):
    """
    Colt - Long-range sharpshooter.
    
    High DPS if all bullets land, but requires good aim.
    """
    
    BRAWLER_ID = 'colt'
    
    def __init__(self, team, spawn_x, spawn_y, player_controlled=True, player_id=None):
        super().__init__(team, spawn_x, spawn_y, player_controlled, player_id)
        
        # Colt-specific properties
        self.bullet_count = self.stats['attack_projectiles']
        self.bullet_damage = self.stats['attack_damage']
        self.bullet_speed = self.stats['projectile_speed']
        self.bullet_spread = self.stats['attack_spread']
        self.attack_range = self.stats['attack_range']
        
        # Super properties
        self.super_bullet_count = self.stats['super_projectiles']
        self.super_damage = self.stats['super_damage']
    
    def attack(self, projectile_manager):
        """
        Fire 6 bullets in a tight spread.
        """
        projectiles = []
        
        for i in range(self.bullet_count):
            # Spread bullets across the line
            angle_offset = (i - (self.bullet_count - 1) / 2) * self.bullet_spread
            angle = self.facing_angle + angle_offset
            
            # Spawn position
            spawn_dist = self.radius + 10
            bullet_x = self.x + math.cos(self.facing_angle) * spawn_dist
            bullet_y = self.y + math.sin(self.facing_angle) * spawn_dist
            
            bullet = Bullet(
                bullet_x, bullet_y, angle,
                self.bullet_speed, self.bullet_damage,
                self, self.colors['projectile'],
                self.attack_range
            )
            
            projectile_manager.add(bullet)
            projectiles.append(bullet)
        
        # Set attack cooldown
        self.attack_cooldown = 0.25
        
        return projectiles
    
    def super_ability(self, projectile_manager, target_x=None, target_y=None):
        """
        Bullet Storm: Fire 12 piercing bullets that destroy walls.
        """
        projectiles = []
        
        # Update facing if target provided
        if target_x is not None and target_y is not None:
            self.aim_at(target_x, target_y)
        
        for i in range(self.super_bullet_count):
            # Tighter spread for super
            angle_offset = (i - (self.super_bullet_count - 1) / 2) * (self.bullet_spread * 0.7)
            angle = self.facing_angle + angle_offset
            
            spawn_dist = self.radius + 10
            bullet_x = self.x + math.cos(self.facing_angle) * spawn_dist
            bullet_y = self.y + math.sin(self.facing_angle) * spawn_dist
            
            bullet = Bullet(
                bullet_x, bullet_y, angle,
                self.bullet_speed * 1.2, self.super_damage,
                self, self.colors['projectile'],
                self.attack_range * 1.5,
                piercing=True,
                destroys_walls=True
            )
            
            projectile_manager.add(bullet)
            projectiles.append(bullet)
        
        return projectiles
