"""
Shelly brawler for Brawler game.

Close-range brawler with devastating spread shot.
- Attack: Fires 5 pellets in a wide spread
- Super: Knockback blast that can push enemies and the ball
"""

import math
from .base import Brawler
from ..projectiles import Pellet
from ..assets import BRAWLER_STATS


class Shelly(Brawler):
    """
    Shelly - Close-range spread shot specialist.
    
    Devastating at close range, but damage falls off quickly.
    Super can knock enemies back and push the ball.
    """
    
    BRAWLER_ID = 'shelly'
    
    def __init__(self, team, spawn_x, spawn_y, player_controlled=True, player_id=None):
        super().__init__(team, spawn_x, spawn_y, player_controlled, player_id)
        
        # Shelly-specific properties
        self.pellet_count = self.stats['attack_projectiles']
        self.pellet_damage = self.stats['attack_damage']
        self.pellet_speed = self.stats['projectile_speed']
        self.pellet_spread = self.stats['attack_spread']
        self.attack_range = self.stats['attack_range']
        
        # Super properties
        self.super_pellet_count = self.stats['super_projectiles']
        self.super_damage = self.stats['super_damage']
        self.super_knockback = self.stats['super_knockback']
    
    def attack(self, projectile_manager):
        """
        Fire 5 pellets in a wide spread.
        """
        projectiles = []
        
        for i in range(self.pellet_count):
            # Spread pellets across wide arc
            t = i / (self.pellet_count - 1) if self.pellet_count > 1 else 0.5
            angle_offset = (t - 0.5) * self.pellet_spread
            angle = self.facing_angle + angle_offset
            
            spawn_dist = self.radius + 8
            pellet_x = self.x + math.cos(angle) * spawn_dist
            pellet_y = self.y + math.sin(angle) * spawn_dist
            
            pellet = Pellet(
                pellet_x, pellet_y, angle,
                self.pellet_speed, self.pellet_damage,
                self, self.colors['projectile'],
                self.attack_range
            )
            
            projectile_manager.add(pellet)
            projectiles.append(pellet)
        
        # Set attack cooldown
        self.attack_cooldown = 0.3
        
        return projectiles
    
    def super_ability(self, projectile_manager, target_x=None, target_y=None):
        """
        Super Shell: Wide knockback blast.
        Fires 9 pellets and knocks back enemies hit.
        """
        projectiles = []
        
        if target_x is not None and target_y is not None:
            self.aim_at(target_x, target_y)
        
        for i in range(self.super_pellet_count):
            # Even wider spread for super
            t = i / (self.super_pellet_count - 1) if self.super_pellet_count > 1 else 0.5
            angle_offset = (t - 0.5) * (self.pellet_spread * 1.2)
            angle = self.facing_angle + angle_offset
            
            spawn_dist = self.radius + 8
            pellet_x = self.x + math.cos(angle) * spawn_dist
            pellet_y = self.y + math.sin(angle) * spawn_dist
            
            pellet = Pellet(
                pellet_x, pellet_y, angle,
                self.pellet_speed, self.super_damage,
                self, self.colors['projectile'],
                self.attack_range * 1.2,
                knockback=self.super_knockback,
                is_super=True
            )
            
            projectile_manager.add(pellet)
            projectiles.append(pellet)
        
        return projectiles
