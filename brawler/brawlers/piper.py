"""
Piper brawler for Brawler game.

Long-range sniper with damage that scales with distance.
- Attack: Single powerful shot that deals more damage at longer range
- Super: Jump escape that drops grenades below
"""

import math
from .base import Brawler
from ..projectiles import SniperBullet, Grenade
from ..assets import BRAWLER_STATS


class Piper(Brawler):
    """
    Piper - Long-range sniper.
    
    Deals massive damage at long range, but weak up close.
    Super allows escape while dropping grenades.
    """
    
    BRAWLER_ID = 'piper'
    
    def __init__(self, team, spawn_x, spawn_y, player_controlled=True, player_id=None):
        super().__init__(team, spawn_x, spawn_y, player_controlled, player_id)
        
        # Piper-specific properties
        self.min_damage = self.stats['attack_damage_min']
        self.max_damage = self.stats['attack_damage_max']
        self.bullet_speed = self.stats['projectile_speed']
        self.attack_range = self.stats['attack_range']
        
        # Super properties
        self.super_jump_range = self.stats['super_jump_range']
        self.grenade_count = self.stats['super_grenades']
        self.grenade_damage = self.stats['super_grenade_damage']
    
    def attack(self, projectile_manager):
        """
        Fire a single powerful sniper shot.
        Damage increases with distance traveled.
        """
        projectiles = []
        
        spawn_dist = self.radius + 12
        bullet_x = self.x + math.cos(self.facing_angle) * spawn_dist
        bullet_y = self.y + math.sin(self.facing_angle) * spawn_dist
        
        sniper_shot = SniperBullet(
            bullet_x, bullet_y, self.facing_angle,
            self.bullet_speed,
            self.min_damage, self.max_damage,
            self, self.colors['projectile'],
            self.attack_range
        )
        
        projectile_manager.add(sniper_shot)
        projectiles.append(sniper_shot)
        
        # Slow attack cooldown for sniper
        self.attack_cooldown = 0.4
        
        return projectiles
    
    def super_ability(self, projectile_manager, target_x=None, target_y=None):
        """
        Poppin': Jump to target location while dropping grenades.
        """
        projectiles = []
        
        # Determine jump target
        if target_x is None or target_y is None:
            target_x = self.x + math.cos(self.facing_angle) * self.super_jump_range
            target_y = self.y + math.sin(self.facing_angle) * self.super_jump_range
        
        # Store start position for grenades
        start_x = self.x
        start_y = self.y
        
        # Drop grenades at start position
        grenade_angles = [0, math.pi/2, math.pi, 3*math.pi/2]
        for i, angle in enumerate(grenade_angles[:self.grenade_count]):
            grenade_x = start_x + math.cos(angle) * 20
            grenade_y = start_y + math.sin(angle) * 20
            
            grenade = Grenade(
                grenade_x, grenade_y,
                self.grenade_damage,
                self,
                delay=0.5
            )
            
            projectile_manager.add(grenade)
            projectiles.append(grenade)
        
        # Start the jump
        self.start_jump(target_x, target_y, self.super_jump_range)
        
        return projectiles
