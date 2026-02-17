"""
AI module for Brawler game.

Implements bot behavior using a simple state machine.
"""

import math
import random
from .assets import (
    AI_REACTION_TIME, AI_AIM_ERROR, AI_AGGRESSION,
    distance, angle_to, SUPER_CHARGE_MAX, BRAWLER_RADIUS
)


class AIState:
    """AI behavior states."""
    IDLE = 'idle'
    CHASE_BALL = 'chase_ball'
    ATTACK = 'attack'
    DEFEND = 'defend'
    SCORE = 'score'
    RETREAT = 'retreat'
    SUPPORT = 'support'


class BrawlerAI:
    """
    AI controller for a brawler bot.
    
    Uses a simple state machine to make decisions:
    - CHASE_BALL: Go for the ball when nobody has it
    - ATTACK: Engage enemy brawlers
    - DEFEND: Protect our goal
    - SCORE: Try to score when we have the ball
    - RETREAT: Fall back when low health
    - SUPPORT: Help teammates
    """
    
    def __init__(self, brawler, arena):
        self.brawler = brawler
        self.arena = arena
        
        # AI settings based on brawler type
        self.aggression = AI_AGGRESSION.get(brawler.BRAWLER_ID, 0.5)
        self.aim_error = AI_AIM_ERROR
        self.reaction_time = AI_REACTION_TIME
        
        # State
        self.state = AIState.IDLE
        self.state_timer = 0
        self.target = None
        self.target_position = None
        
        # Reaction delay
        self.decision_cooldown = 0
        self.last_decision_time = 0
        
        # Random seed for consistent behavior
        self.random_offset = random.random() * 100
    
    def update(self, dt, ball, teammates, enemies, projectile_manager):
        """
        Update AI decision making and execute actions.
        """
        if not self.brawler.alive:
            return
        
        # Update decision cooldown
        self.decision_cooldown -= dt
        
        # Make new decision periodically
        if self.decision_cooldown <= 0:
            self._make_decision(ball, teammates, enemies)
            self.decision_cooldown = self.reaction_time + random.random() * 0.1
        
        # Execute current state
        self._execute_state(dt, ball, teammates, enemies, projectile_manager)
    
    def _make_decision(self, ball, teammates, enemies):
        """
        Decide what state to be in based on game situation.
        """
        brawler = self.brawler
        
        # Check if we should retreat (low health)
        health_percent = brawler.health / brawler.max_health
        if health_percent < 0.25 and not ball.carrier == brawler:
            self.state = AIState.RETREAT
            return
        
        # If we have the ball, try to score
        if ball.carrier == brawler:
            self.state = AIState.SCORE
            return
        
        # If teammate has ball, support
        for teammate in teammates:
            if ball.carrier == teammate:
                self.state = AIState.SUPPORT
                return
        
        # If enemy has ball, defend or attack carrier
        for enemy in enemies:
            if ball.carrier == enemy:
                if self._should_attack():
                    self.state = AIState.ATTACK
                    self.target = enemy
                else:
                    self.state = AIState.DEFEND
                return
        
        # Ball is free
        if self._should_chase_ball(ball, teammates, enemies):
            self.state = AIState.CHASE_BALL
            return
        
        # Check for nearby enemies to attack
        nearest_enemy = self._find_nearest_enemy(enemies)
        if nearest_enemy and self._should_attack():
            enemy_dist = distance((brawler.x, brawler.y), (nearest_enemy.x, nearest_enemy.y))
            if enemy_dist < brawler.stats.get('attack_range', 300) * 1.5:
                self.state = AIState.ATTACK
                self.target = nearest_enemy
                return
        
        # Default: chase ball
        self.state = AIState.CHASE_BALL
    
    def _execute_state(self, dt, ball, teammates, enemies, projectile_manager):
        """
        Execute actions based on current state.
        """
        if self.state == AIState.CHASE_BALL:
            self._do_chase_ball(ball)
        elif self.state == AIState.ATTACK:
            self._do_attack(enemies, projectile_manager)
        elif self.state == AIState.DEFEND:
            self._do_defend(ball)
        elif self.state == AIState.SCORE:
            self._do_score(ball, enemies, projectile_manager)
        elif self.state == AIState.RETREAT:
            self._do_retreat()
        elif self.state == AIState.SUPPORT:
            self._do_support(ball, teammates)
        else:
            self._do_idle()
    
    def _do_chase_ball(self, ball):
        """
        Move towards the ball.
        """
        target_x = ball.x
        target_y = ball.y
        
        # Predict ball movement if it's moving
        if ball.is_moving():
            speed = ball.get_speed()
            predict_time = 0.5
            target_x += ball.vx * predict_time
            target_y += ball.vy * predict_time
        
        self._move_towards(target_x, target_y)
        
        # Try to pick up ball if close
        if distance((self.brawler.x, self.brawler.y), (ball.x, ball.y)) < 50:
            ball.try_pickup(self.brawler)
    
    def _do_attack(self, enemies, projectile_manager):
        """
        Attack enemy brawlers.
        """
        if self.target is None or not self.target.alive:
            self.target = self._find_nearest_enemy(enemies)
        
        if self.target is None:
            self.state = AIState.IDLE
            return
        
        target_dist = distance((self.brawler.x, self.brawler.y), 
                               (self.target.x, self.target.y))
        attack_range = self.brawler.stats.get('attack_range', 300)
        
        # Move towards target if too far
        if target_dist > attack_range * 0.8:
            self._move_towards(self.target.x, self.target.y)
        elif target_dist < attack_range * 0.3:
            # Too close for ranged brawlers, back up (except Edgar)
            if self.brawler.BRAWLER_ID != 'edgar':
                self._move_away_from(self.target.x, self.target.y)
        else:
            # In range, stop and shoot
            self.brawler.set_movement(0, 0)
        
        # Aim and attack
        self._aim_at_target(self.target.x, self.target.y)
        
        if target_dist <= attack_range:
            # Try to attack
            self.brawler.try_attack(projectile_manager)
            
            # Use super if ready and good opportunity
            if self.brawler.is_super_ready():
                if self._should_use_super():
                    self.brawler.try_super(projectile_manager, self.target.x, self.target.y)
    
    def _do_defend(self, ball):
        """
        Move to defensive position near our goal.
        """
        # Get our goal position
        if self.brawler.team == 0:
            goal_x = self.arena.world_width * 0.15
        else:
            goal_x = self.arena.world_width * 0.85
        goal_y = self.arena.world_height / 2
        
        # Position between ball and goal
        ball_to_goal_x = goal_x - ball.x
        ball_to_goal_y = goal_y - ball.y
        dist_to_goal = math.sqrt(ball_to_goal_x ** 2 + ball_to_goal_y ** 2)
        
        if dist_to_goal > 0:
            # Stand halfway between ball and goal
            target_x = ball.x + ball_to_goal_x * 0.5
            target_y = ball.y + ball_to_goal_y * 0.5
        else:
            target_x = goal_x
            target_y = goal_y
        
        self._move_towards(target_x, target_y)
        
        # Face the ball
        self._aim_at_target(ball.x, ball.y)
    
    def _do_score(self, ball, enemies, projectile_manager):
        """
        Move towards enemy goal and try to score.
        """
        # Get enemy goal position
        if self.brawler.team == 0:
            goal_x = self.arena.world_width + 30
            goal_y = self.arena.world_height / 2
        else:
            goal_x = -30
            goal_y = self.arena.world_height / 2
        
        # Check for nearby enemies
        nearest_enemy = self._find_nearest_enemy(enemies)
        if nearest_enemy:
            enemy_dist = distance((self.brawler.x, self.brawler.y),
                                  (nearest_enemy.x, nearest_enemy.y))
            
            # Attack enemy if close
            if enemy_dist < self.brawler.stats.get('attack_range', 300):
                self._aim_at_target(nearest_enemy.x, nearest_enemy.y)
                self.brawler.try_attack(projectile_manager)
        
        # Move towards goal
        self._move_towards(goal_x, goal_y)
        
        # Kick ball towards goal when close enough
        goal_dist = distance((self.brawler.x, self.brawler.y), (goal_x, goal_y))
        if goal_dist < 200:
            self.brawler.aim_at(goal_x, goal_y)
            ball.kick()
    
    def _do_retreat(self):
        """
        Move back towards our spawn/goal area.
        """
        self._move_towards(self.brawler.spawn_x, self.brawler.spawn_y)
    
    def _do_support(self, ball, teammates):
        """
        Support teammate who has the ball.
        """
        # Find teammate with ball
        ball_carrier = None
        for teammate in teammates:
            if ball.carrier == teammate:
                ball_carrier = teammate
                break
        
        if ball_carrier is None:
            self.state = AIState.CHASE_BALL
            return
        
        # Position ahead of ball carrier towards goal
        if self.brawler.team == 0:
            ahead_x = ball_carrier.x + 100
        else:
            ahead_x = ball_carrier.x - 100
        ahead_y = ball_carrier.y + (random.random() - 0.5) * 100
        
        self._move_towards(ahead_x, ahead_y)
    
    def _do_idle(self):
        """
        Default idle behavior - slight movement towards center.
        """
        center_x = self.arena.world_width / 2
        center_y = self.arena.world_height / 2
        
        # Slight drift towards center
        self._move_towards(center_x, center_y, speed_mult=0.3)
    
    def _move_towards(self, target_x, target_y, speed_mult=1.0):
        """
        Set movement towards a target position.
        """
        dx = target_x - self.brawler.x
        dy = target_y - self.brawler.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist > 5:
            self.brawler.set_movement(dx / dist * speed_mult, dy / dist * speed_mult)
        else:
            self.brawler.set_movement(0, 0)
    
    def _move_away_from(self, target_x, target_y, speed_mult=1.0):
        """
        Set movement away from a position.
        """
        dx = self.brawler.x - target_x
        dy = self.brawler.y - target_y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist > 0:
            self.brawler.set_movement(dx / dist * speed_mult, dy / dist * speed_mult)
    
    def _aim_at_target(self, target_x, target_y):
        """
        Aim at target with some error.
        """
        # Add aim error
        error = self.aim_error * (random.random() * 2 - 1)
        angle = angle_to((self.brawler.x, self.brawler.y), (target_x, target_y))
        
        target_with_error_x = target_x + math.cos(angle + math.pi/2) * error * 50
        target_with_error_y = target_y + math.sin(angle + math.pi/2) * error * 50
        
        self.brawler.aim_at(target_with_error_x, target_with_error_y)
    
    def _find_nearest_enemy(self, enemies):
        """
        Find the nearest alive enemy.
        """
        nearest = None
        nearest_dist = float('inf')
        
        for enemy in enemies:
            if not enemy.alive:
                continue
            
            dist = distance((self.brawler.x, self.brawler.y), (enemy.x, enemy.y))
            if dist < nearest_dist:
                nearest_dist = dist
                nearest = enemy
        
        return nearest
    
    def _should_attack(self):
        """
        Decide if we should attack based on aggression.
        """
        return random.random() < self.aggression
    
    def _should_chase_ball(self, ball, teammates, enemies):
        """
        Decide if we should chase the ball.
        """
        my_dist = distance((self.brawler.x, self.brawler.y), (ball.x, ball.y))
        
        # Check if teammate is closer
        for teammate in teammates:
            if not teammate.alive:
                continue
            teammate_dist = distance((teammate.x, teammate.y), (ball.x, ball.y))
            if teammate_dist < my_dist * 0.7:
                return False  # Let teammate get it
        
        return True
    
    def _should_use_super(self):
        """
        Decide if we should use super ability.
        """
        brawler = self.brawler
        
        # Edgar: use to engage
        if brawler.BRAWLER_ID == 'edgar':
            if self.target:
                target_dist = distance((brawler.x, brawler.y), 
                                       (self.target.x, self.target.y))
                return target_dist > brawler.stats.get('attack_range', 60) * 2
        
        # Piper: use to escape when low health
        elif brawler.BRAWLER_ID == 'piper':
            health_percent = brawler.health / brawler.max_health
            return health_percent < 0.4
        
        # Shelly: use when enemy is close
        elif brawler.BRAWLER_ID == 'shelly':
            if self.target:
                target_dist = distance((brawler.x, brawler.y),
                                       (self.target.x, self.target.y))
                return target_dist < 150
        
        # Colt: use similar to attack
        elif brawler.BRAWLER_ID == 'colt':
            return True  # Always use when ready
        
        return random.random() < 0.5
