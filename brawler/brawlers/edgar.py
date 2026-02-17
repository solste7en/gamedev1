"""
Edgar brawler for Brawler game.

Melee assassin that heals when dealing damage.
- Attack: Rapid double punch with short range
- Super: Vault jump to target location (auto-charges over time)
"""

import math
from .base import Brawler
from ..projectiles import MeleeAttack
from ..assets import BRAWLER_STATS, MELEE_ARC_ANGLE, SUPER_CHARGE_MAX


class Edgar(Brawler):
    """
    Edgar - Melee assassin.
    
    Very fast with rapid attacks that heal.
    Super auto-charges and allows jumping into fights.
    """
    
    BRAWLER_ID = 'edgar'
    
    def __init__(self, team, spawn_x, spawn_y, player_controlled=True, player_id=None):
        super().__init__(team, spawn_x, spawn_y, player_controlled, player_id)
        
        # Edgar-specific properties
        self.punch_damage = self.stats['attack_damage']
        self.punch_count = self.stats['attack_projectiles']
        self.attack_range = self.stats['attack_range']
        self.attack_spread = self.stats['attack_spread']
        self.heal_percent = self.stats['heal_percent']
        
        # Super properties
        self.super_jump_range = self.stats['super_jump_range']
        self.auto_charge_rate = self.stats['super_auto_charge']
    
    def _update_auto_charge(self, dt):
        """
        Edgar's super auto-charges over time.
        """
        if self.super_charge < SUPER_CHARGE_MAX:
            self.super_charge += self.auto_charge_rate * dt
            self.super_charge = min(SUPER_CHARGE_MAX, self.super_charge)
    
    def attack(self, projectile_manager):
        """
        Execute rapid double punch.
        """
        projectiles = []
        
        for i in range(self.punch_count):
            # Alternate punch direction slightly
            angle_offset = (i - 0.5) * 0.3
            punch_angle = self.facing_angle + angle_offset
            
            melee_hit = MeleeAttack(
                owner=self,
                angle=punch_angle,
                damage=self.punch_damage,
                range=self.attack_range,
                arc_angle=math.radians(MELEE_ARC_ANGLE),
                duration=0.15,
                delay=i * 0.1,
                heal_percent=self.heal_percent
            )
            
            projectile_manager.add(melee_hit)
            projectiles.append(melee_hit)
        
        # Very fast attack cooldown
        self.attack_cooldown = 0.15
        self.attack_timer = 0.2
        
        return projectiles
    
    def super_ability(self, projectile_manager, target_x=None, target_y=None):
        """
        Vault: Jump to target location.
        """
        # Determine jump target
        if target_x is None or target_y is None:
            target_x = self.x + math.cos(self.facing_angle) * self.super_jump_range
            target_y = self.y + math.sin(self.facing_angle) * self.super_jump_range
        
        # Start the jump
        self.start_jump(target_x, target_y, self.super_jump_range)
        
        return []
    
    def on_damage_dealt(self, damage):
        """
        Called when Edgar deals damage. Heals based on damage dealt.
        """
        heal_amount = int(damage * self.heal_percent)
        self.heal(heal_amount)
