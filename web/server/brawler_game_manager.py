"""
Brawler game manager for multiplayer web version
"""

import asyncio
import random
import time
import math
from typing import Dict, Optional, List, Callable, Tuple

from .brawler_models import (
    BrawlerGameState, GamePhase, Fighter, Projectile, Ball, Wall, Goal,
    Position, Velocity, BrawlerType, Team, ProjectileType,
    BRAWLER_STATS, SPAWN_POSITIONS, ARENA_WIDTH, ARENA_HEIGHT, TILE_SIZE,
    GOAL_WIDTH, GOAL_DEPTH, BALL_RADIUS, BALL_PICKUP_RANGE, BALL_SHOOT_SPEED,
    BALL_FRICTION, BRAWLER_RADIUS, FRICTION, KNOCKBACK_FORCE,
    MATCH_DURATION, GOALS_TO_WIN, RESPAWN_TIME, COUNTDOWN_TIME,
    GOAL_CELEBRATION_TIME, AI_REACTION_TIME, AI_AIM_ERROR,
    normalize, lerp, clamp
)
from .room_manager import Room


class BrawlerGameManager:
    """Manages game state and logic for a Brawler game instance"""
    
    def __init__(self, room: Room, broadcast_callback: Callable):
        self.room = room
        self.broadcast = broadcast_callback
        self.state = BrawlerGameState()
        self.game_task: Optional[asyncio.Task] = None
        self.last_update = time.time()
        
        # Input state for each fighter
        self.fighter_inputs: Dict[str, Dict] = {}
    
    def setup_game(self):
        """Initialize the game with players and AI"""
        self.state = BrawlerGameState()
        self.state.phase = GamePhase.COUNTDOWN
        self.state.countdown_timer = COUNTDOWN_TIME
        
        # Setup arena
        self._setup_arena()
        
        # Get player assignments
        team_assignments = getattr(self.room, 'team_assignments', {})
        char_selections = getattr(self.room, 'character_selections', {})
        
        # Create fighters for human players
        blue_count = 0
        red_count = 0
        used_characters = {Team.BLUE: set(), Team.RED: set()}
        
        for player_id, player in self.room.players.items():
            team = team_assignments.get(player_id, Team.BLUE if blue_count <= red_count else Team.RED)
            if isinstance(team, int):
                team = Team(team)
            
            char_type = char_selections.get(player_id, BrawlerType.COLT)
            if isinstance(char_type, str):
                char_type = BrawlerType(char_type)
            
            # Track character usage
            used_characters[team].add(char_type)
            
            # Get spawn position
            if team == Team.BLUE:
                spawn_idx = blue_count % 2
                blue_count += 1
            else:
                spawn_idx = red_count % 2
                red_count += 1
            
            spawn_pos = SPAWN_POSITIONS[team][spawn_idx]
            
            # Create fighter
            fighter_id = f"fighter_{player_id}"
            fighter = Fighter(
                id=fighter_id,
                player_id=player_id,
                brawler_type=char_type,
                team=team,
                position=Position(spawn_pos[0], spawn_pos[1]),
                facing_angle=0 if team == Team.BLUE else math.pi,
                is_ai=False
            )
            self.state.fighters[fighter_id] = fighter
            self.fighter_inputs[fighter_id] = {}
        
        # Fill remaining slots with AI
        ai_id_counter = 0
        available_chars = list(BrawlerType)
        
        while blue_count < 2:
            # Pick character not used by blue team
            char_type = None
            for c in available_chars:
                if c not in used_characters[Team.BLUE]:
                    char_type = c
                    break
            if char_type is None:
                char_type = random.choice(available_chars)
            
            used_characters[Team.BLUE].add(char_type)
            spawn_pos = SPAWN_POSITIONS[Team.BLUE][blue_count]
            
            fighter_id = f"ai_{ai_id_counter}"
            ai_id_counter += 1
            
            fighter = Fighter(
                id=fighter_id,
                player_id=None,
                brawler_type=char_type,
                team=Team.BLUE,
                position=Position(spawn_pos[0], spawn_pos[1]),
                facing_angle=0,
                is_ai=True
            )
            self.state.fighters[fighter_id] = fighter
            blue_count += 1
        
        while red_count < 2:
            char_type = None
            for c in available_chars:
                if c not in used_characters[Team.RED]:
                    char_type = c
                    break
            if char_type is None:
                char_type = random.choice(available_chars)
            
            used_characters[Team.RED].add(char_type)
            spawn_pos = SPAWN_POSITIONS[Team.RED][red_count]
            
            fighter_id = f"ai_{ai_id_counter}"
            ai_id_counter += 1
            
            fighter = Fighter(
                id=fighter_id,
                player_id=None,
                brawler_type=char_type,
                team=Team.RED,
                position=Position(spawn_pos[0], spawn_pos[1]),
                facing_angle=math.pi,
                is_ai=True
            )
            self.state.fighters[fighter_id] = fighter
            red_count += 1
        
        # Place ball at center
        self.state.ball = Ball(
            position=Position(ARENA_WIDTH / 2, ARENA_HEIGHT / 2)
        )
    
    def _setup_arena(self):
        """Setup arena walls and goals"""
        # Border walls
        wall_thickness = TILE_SIZE
        
        # Top wall
        self.state.walls.append(Wall(0, 0, ARENA_WIDTH, wall_thickness))
        # Bottom wall
        self.state.walls.append(Wall(0, ARENA_HEIGHT - wall_thickness, ARENA_WIDTH, wall_thickness))
        
        # Left wall (with goal gap)
        goal_start = (ARENA_HEIGHT - GOAL_WIDTH) / 2
        self.state.walls.append(Wall(0, wall_thickness, wall_thickness, goal_start - wall_thickness))
        self.state.walls.append(Wall(0, goal_start + GOAL_WIDTH, wall_thickness, goal_start - wall_thickness))
        
        # Right wall (with goal gap)
        self.state.walls.append(Wall(ARENA_WIDTH - wall_thickness, wall_thickness, wall_thickness, goal_start - wall_thickness))
        self.state.walls.append(Wall(ARENA_WIDTH - wall_thickness, goal_start + GOAL_WIDTH, wall_thickness, goal_start - wall_thickness))
        
        # Goals
        goal_y = (ARENA_HEIGHT - GOAL_WIDTH) / 2
        
        # Blue goal (left side, Red scores here)
        self.state.goals[Team.RED.value] = Goal(
            team=Team.RED,
            x=-GOAL_DEPTH,
            y=goal_y,
            width=GOAL_DEPTH,
            height=GOAL_WIDTH
        )
        
        # Red goal (right side, Blue scores here)
        self.state.goals[Team.BLUE.value] = Goal(
            team=Team.BLUE,
            x=ARENA_WIDTH,
            y=goal_y,
            width=GOAL_DEPTH,
            height=GOAL_WIDTH
        )
    
    def handle_input(self, player_id: int, action: str, data: dict):
        """Handle player input"""
        # Find fighter for this player
        fighter_id = f"fighter_{player_id}"
        fighter = self.state.fighters.get(fighter_id)
        
        if not fighter or not fighter.is_alive:
            return
        
        if action == "move":
            # data: {x: -1 to 1, y: -1 to 1}
            self.fighter_inputs[fighter_id]["move_x"] = clamp(data.get("x", 0), -1, 1)
            self.fighter_inputs[fighter_id]["move_y"] = clamp(data.get("y", 0), -1, 1)
        
        elif action == "aim":
            # data: {x: world x, y: world y}
            aim_x = data.get("x", fighter.position.x)
            aim_y = data.get("y", fighter.position.y)
            fighter.facing_angle = math.atan2(
                aim_y - fighter.position.y,
                aim_x - fighter.position.x
            )
        
        elif action == "attack":
            self.fighter_inputs[fighter_id]["attack"] = True
            # Also update aim from attack data
            if "aim_x" in data and "aim_y" in data:
                fighter.facing_angle = math.atan2(
                    data["aim_y"] - fighter.position.y,
                    data["aim_x"] - fighter.position.x
                )
        
        elif action == "ability":
            self.fighter_inputs[fighter_id]["ability"] = True
            if "aim_x" in data and "aim_y" in data:
                fighter.facing_angle = math.atan2(
                    data["aim_y"] - fighter.position.y,
                    data["aim_x"] - fighter.position.x
                )
    
    def update(self, dt: float):
        """Update game state"""
        if self.state.phase == GamePhase.COUNTDOWN:
            self._update_countdown(dt)
        elif self.state.phase == GamePhase.PLAYING:
            self._update_playing(dt)
        elif self.state.phase == GamePhase.GOAL_SCORED:
            self._update_goal_celebration(dt)
    
    def _update_countdown(self, dt: float):
        """Update countdown phase"""
        self.state.countdown_timer -= dt
        if self.state.countdown_timer <= 0:
            self.state.phase = GamePhase.PLAYING
    
    def _update_playing(self, dt: float):
        """Update main gameplay"""
        # Update timers
        self.state.time_remaining -= dt
        
        # Check time limit
        if self.state.time_remaining <= 0:
            if self.state.scores[0] == self.state.scores[1]:
                # Overtime
                self.state.overtime = True
                self.state.time_remaining = 60  # 1 minute overtime
            else:
                self._end_game()
                return
        
        # Update fighters
        for fighter_id, fighter in self.state.fighters.items():
            if fighter.is_ai:
                self._update_ai(fighter, dt)
            self._update_fighter(fighter, dt)
        
        # Update projectiles
        self._update_projectiles(dt)
        
        # Update ball
        self._update_ball(dt)
        
        # Check for goals
        self._check_goals()
        
        # Clear one-shot inputs
        for inp in self.fighter_inputs.values():
            inp.pop("attack", None)
            inp.pop("ability", None)
    
    def _update_goal_celebration(self, dt: float):
        """Update goal celebration phase"""
        self.state.goal_celebration_timer -= dt
        if self.state.goal_celebration_timer <= 0:
            # Check if game is over
            if (self.state.scores[0] >= GOALS_TO_WIN or 
                self.state.scores[1] >= GOALS_TO_WIN or
                self.state.overtime):
                self._end_game()
            else:
                # Reset for next round
                self._reset_round()
    
    def _update_fighter(self, fighter: Fighter, dt: float):
        """Update a single fighter"""
        if not fighter.is_alive:
            fighter.respawn_timer -= dt
            if fighter.respawn_timer <= 0:
                self._respawn_fighter(fighter)
            return
        
        # Update invulnerability
        if fighter.invulnerable_timer > 0:
            fighter.invulnerable_timer -= dt
        
        # Update cooldowns
        if fighter.attack_cooldown > 0:
            fighter.attack_cooldown -= dt
        
        # Reload ammo
        stats = BRAWLER_STATS.get(fighter.brawler_type.value, {})
        reload_time = stats.get('reload_time', 1.5)
        if fighter.ammo < fighter.max_ammo:
            fighter.reload_timer += dt
            if fighter.reload_timer >= reload_time:
                fighter.ammo = min(fighter.ammo + 1, fighter.max_ammo)
                fighter.reload_timer = 0
        
        # Handle jumping
        if fighter.is_jumping and fighter.jump_target:
            self._update_jump(fighter, dt)
            return
        
        # Get input
        inp = self.fighter_inputs.get(fighter.id, {})
        move_x = inp.get("move_x", 0)
        move_y = inp.get("move_y", 0)
        
        # Apply movement
        speed = stats.get('speed', 220)
        if move_x != 0 or move_y != 0:
            # Normalize movement
            length = math.sqrt(move_x * move_x + move_y * move_y)
            if length > 0:
                move_x /= length
                move_y /= length
            
            fighter.velocity.x = move_x * speed
            fighter.velocity.y = move_y * speed
            fighter.move_direction = (move_x, move_y)
        else:
            # Apply friction
            fighter.velocity.x *= FRICTION
            fighter.velocity.y *= FRICTION
        
        # Update position
        new_x = fighter.position.x + fighter.velocity.x * dt
        new_y = fighter.position.y + fighter.velocity.y * dt
        
        # Wall collision
        new_x, new_y = self._resolve_wall_collision(new_x, new_y, BRAWLER_RADIUS)
        
        fighter.position.x = new_x
        fighter.position.y = new_y
        
        # Handle attack
        if inp.get("attack") and fighter.attack_cooldown <= 0 and fighter.ammo > 0:
            self._fighter_attack(fighter)
        
        # Handle ability (super)
        if inp.get("ability") and fighter.super_charge >= 100:
            self._fighter_ability(fighter)
        
        # Auto-charge super for Edgar
        if fighter.brawler_type == BrawlerType.EDGAR:
            auto_charge = stats.get('super_auto_charge', 2.5)
            fighter.super_charge = min(100, fighter.super_charge + auto_charge * dt)
        
        # Ball pickup
        if not fighter.is_carrying_ball and self.state.ball and not self.state.ball.carrier_id:
            dist = fighter.position.distance_to(self.state.ball.position)
            if dist < BALL_PICKUP_RANGE + BRAWLER_RADIUS:
                self.state.ball.carrier_id = fighter.id
                fighter.is_carrying_ball = True
    
    def _update_jump(self, fighter: Fighter, dt: float):
        """Update fighter jump movement"""
        if not fighter.jump_target:
            fighter.is_jumping = False
            return
        
        jump_speed = 500
        dx = fighter.jump_target.x - fighter.position.x
        dy = fighter.jump_target.y - fighter.position.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist < jump_speed * dt:
            fighter.position.x = fighter.jump_target.x
            fighter.position.y = fighter.jump_target.y
            fighter.is_jumping = False
            fighter.jump_target = None
            fighter.invulnerable_timer = 0.3
        else:
            fighter.position.x += (dx / dist) * jump_speed * dt
            fighter.position.y += (dy / dist) * jump_speed * dt
    
    def _fighter_attack(self, fighter: Fighter):
        """Execute fighter attack"""
        stats = BRAWLER_STATS.get(fighter.brawler_type.value, {})
        
        if fighter.is_carrying_ball:
            # Kick ball instead
            self._kick_ball(fighter)
            return
        
        fighter.ammo -= 1
        fighter.reload_timer = 0
        fighter.attack_cooldown = 0.3
        
        # Create projectiles based on brawler type
        num_projectiles = stats.get('attack_projectiles', 1)
        spread = stats.get('attack_spread', 0)
        proj_speed = stats.get('projectile_speed', 500)
        damage = stats.get('attack_damage', 300)
        attack_range = stats.get('attack_range', 300)
        
        # Determine projectile type
        if fighter.brawler_type == BrawlerType.COLT:
            proj_type = ProjectileType.BULLET
        elif fighter.brawler_type == BrawlerType.SHELLY:
            proj_type = ProjectileType.PELLET
        elif fighter.brawler_type == BrawlerType.PIPER:
            proj_type = ProjectileType.SNIPER
        elif fighter.brawler_type == BrawlerType.EDGAR:
            proj_type = ProjectileType.MELEE
            attack_range = 60
        else:
            proj_type = ProjectileType.BULLET
        
        for i in range(num_projectiles):
            # Calculate angle with spread
            angle_offset = 0
            if num_projectiles > 1:
                angle_offset = (i - (num_projectiles - 1) / 2) * spread
            
            angle = fighter.facing_angle + angle_offset
            
            vx = math.cos(angle) * proj_speed
            vy = math.sin(angle) * proj_speed
            
            proj = Projectile(
                id=self.state.get_projectile_id(),
                owner_id=fighter.id,
                team=fighter.team,
                projectile_type=proj_type,
                position=Position(
                    fighter.position.x + math.cos(angle) * 25,
                    fighter.position.y + math.sin(angle) * 25
                ),
                velocity=Velocity(vx, vy),
                damage=damage,
                range_remaining=attack_range
            )
            self.state.projectiles[proj.id] = proj
    
    def _fighter_ability(self, fighter: Fighter):
        """Execute fighter super ability"""
        stats = BRAWLER_STATS.get(fighter.brawler_type.value, {})
        fighter.super_charge = 0
        
        if fighter.brawler_type == BrawlerType.COLT:
            # Enhanced shot - more projectiles, piercing
            num_projectiles = stats.get('super_projectiles', 12)
            proj_speed = stats.get('projectile_speed', 600)
            damage = stats.get('super_damage', 420)
            
            for i in range(num_projectiles):
                angle_offset = (i - (num_projectiles - 1) / 2) * 0.03
                angle = fighter.facing_angle + angle_offset
                
                proj = Projectile(
                    id=self.state.get_projectile_id(),
                    owner_id=fighter.id,
                    team=fighter.team,
                    projectile_type=ProjectileType.BULLET,
                    position=Position(
                        fighter.position.x + math.cos(angle) * 25,
                        fighter.position.y + math.sin(angle) * 25
                    ),
                    velocity=Velocity(math.cos(angle) * proj_speed, math.sin(angle) * proj_speed),
                    damage=damage,
                    range_remaining=ARENA_WIDTH,
                    piercing=True
                )
                self.state.projectiles[proj.id] = proj
        
        elif fighter.brawler_type == BrawlerType.SHELLY:
            # Knockback super
            num_projectiles = stats.get('super_projectiles', 9)
            proj_speed = stats.get('projectile_speed', 500)
            damage = stats.get('super_damage', 480)
            knockback = stats.get('super_knockback', 300)
            
            for i in range(num_projectiles):
                angle_offset = (i - (num_projectiles - 1) / 2) * 0.5 / num_projectiles
                angle = fighter.facing_angle + angle_offset
                
                proj = Projectile(
                    id=self.state.get_projectile_id(),
                    owner_id=fighter.id,
                    team=fighter.team,
                    projectile_type=ProjectileType.PELLET,
                    position=Position(
                        fighter.position.x + math.cos(angle) * 25,
                        fighter.position.y + math.sin(angle) * 25
                    ),
                    velocity=Velocity(math.cos(angle) * proj_speed, math.sin(angle) * proj_speed),
                    damage=damage,
                    range_remaining=300,
                    knockback=knockback
                )
                self.state.projectiles[proj.id] = proj
        
        elif fighter.brawler_type == BrawlerType.PIPER:
            # Jump away and drop grenades
            jump_range = stats.get('super_jump_range', 300)
            # Jump in facing direction
            fighter.jump_target = Position(
                fighter.position.x + math.cos(fighter.facing_angle) * jump_range,
                fighter.position.y + math.sin(fighter.facing_angle) * jump_range
            )
            fighter.is_jumping = True
            fighter.invulnerable_timer = 1.0
            
            # Drop grenades at current position
            for i in range(4):
                angle = (i / 4) * math.pi * 2
                proj = Projectile(
                    id=self.state.get_projectile_id(),
                    owner_id=fighter.id,
                    team=fighter.team,
                    projectile_type=ProjectileType.GRENADE,
                    position=Position(fighter.position.x, fighter.position.y),
                    velocity=Velocity(math.cos(angle) * 100, math.sin(angle) * 100),
                    damage=stats.get('super_grenade_damage', 900),
                    range_remaining=100
                )
                self.state.projectiles[proj.id] = proj
        
        elif fighter.brawler_type == BrawlerType.EDGAR:
            # Vault jump
            jump_range = stats.get('super_jump_range', 350)
            fighter.jump_target = Position(
                fighter.position.x + math.cos(fighter.facing_angle) * jump_range,
                fighter.position.y + math.sin(fighter.facing_angle) * jump_range
            )
            fighter.is_jumping = True
            fighter.invulnerable_timer = 0.5
    
    def _kick_ball(self, fighter: Fighter):
        """Kick the ball"""
        if not fighter.is_carrying_ball or not self.state.ball:
            return
        
        fighter.is_carrying_ball = False
        self.state.ball.carrier_id = None
        
        # Kick in facing direction
        self.state.ball.velocity.x = math.cos(fighter.facing_angle) * BALL_SHOOT_SPEED
        self.state.ball.velocity.y = math.sin(fighter.facing_angle) * BALL_SHOOT_SPEED
    
    def _update_projectiles(self, dt: float):
        """Update all projectiles"""
        to_remove = []
        
        for proj_id, proj in self.state.projectiles.items():
            # Move projectile
            proj.position.x += proj.velocity.x * dt
            proj.position.y += proj.velocity.y * dt
            
            # Reduce range
            speed = math.sqrt(proj.velocity.x ** 2 + proj.velocity.y ** 2)
            proj.range_remaining -= speed * dt
            
            # Check if out of range or bounds
            if (proj.range_remaining <= 0 or
                proj.position.x < -50 or proj.position.x > ARENA_WIDTH + 50 or
                proj.position.y < -50 or proj.position.y > ARENA_HEIGHT + 50):
                to_remove.append(proj_id)
                continue
            
            # Wall collision for non-piercing
            if not proj.piercing:
                for wall in self.state.walls:
                    if self._point_in_rect(proj.position.x, proj.position.y, wall):
                        to_remove.append(proj_id)
                        break
            
            # Hit detection
            for fighter_id, fighter in self.state.fighters.items():
                if fighter_id == proj.owner_id:
                    continue
                if not fighter.is_alive:
                    continue
                if fighter.team == proj.team:
                    continue
                if fighter.invulnerable_timer > 0:
                    continue
                if fighter_id in proj.hit_targets:
                    continue
                
                dist = proj.position.distance_to(fighter.position)
                if dist < BRAWLER_RADIUS + 10:
                    # Hit!
                    self._apply_damage(fighter, proj)
                    proj.hit_targets.append(fighter_id)
                    
                    if not proj.piercing:
                        to_remove.append(proj_id)
                        break
        
        # Remove projectiles
        for proj_id in to_remove:
            self.state.projectiles.pop(proj_id, None)
    
    def _apply_damage(self, fighter: Fighter, proj: Projectile):
        """Apply damage from projectile to fighter"""
        damage = proj.damage
        
        # Piper damage scaling
        if proj.projectile_type == ProjectileType.SNIPER:
            owner = self.state.fighters.get(proj.owner_id)
            if owner:
                stats = BRAWLER_STATS.get(owner.brawler_type.value, {})
                dist = fighter.position.distance_to(owner.position)
                max_range = stats.get('attack_range', 450)
                damage_min = stats.get('attack_damage_min', 1400)
                damage_max = stats.get('attack_damage_max', 2800)
                ratio = min(1, dist / max_range)
                damage = int(damage_min + (damage_max - damage_min) * ratio)
        
        fighter.health -= damage
        
        # Knockback
        if proj.knockback > 0:
            angle = math.atan2(proj.velocity.y, proj.velocity.x)
            fighter.velocity.x += math.cos(angle) * proj.knockback
            fighter.velocity.y += math.sin(angle) * proj.knockback
            
            # Drop ball if carrying
            if fighter.is_carrying_ball:
                fighter.is_carrying_ball = False
                if self.state.ball:
                    self.state.ball.carrier_id = None
        
        # Give super charge to attacker
        attacker = self.state.fighters.get(proj.owner_id)
        if attacker:
            stats = BRAWLER_STATS.get(attacker.brawler_type.value, {})
            charge = stats.get('super_charge_per_hit', 8)
            attacker.super_charge = min(100, attacker.super_charge + charge)
            
            # Edgar heal
            if attacker.brawler_type == BrawlerType.EDGAR:
                heal_percent = stats.get('heal_percent', 0.35)
                attacker.health = min(attacker.max_health, 
                                     attacker.health + int(damage * heal_percent))
        
        # Give super charge to victim
        stats = BRAWLER_STATS.get(fighter.brawler_type.value, {})
        charge = stats.get('super_charge_per_damage', 10) * (damage / 1000)
        fighter.super_charge = min(100, fighter.super_charge + charge)
        
        # Check death
        if fighter.health <= 0:
            self._kill_fighter(fighter)
    
    def _kill_fighter(self, fighter: Fighter):
        """Handle fighter death"""
        fighter.is_alive = False
        fighter.health = 0
        fighter.respawn_timer = RESPAWN_TIME
        
        # Drop ball
        if fighter.is_carrying_ball and self.state.ball:
            fighter.is_carrying_ball = False
            self.state.ball.carrier_id = None
    
    def _respawn_fighter(self, fighter: Fighter):
        """Respawn a fighter"""
        # Find spawn position
        team_idx = 0
        for fid, f in self.state.fighters.items():
            if f.team == fighter.team and fid != fighter.id:
                team_idx = 1
                break
        
        spawn_pos = SPAWN_POSITIONS[fighter.team][team_idx]
        
        fighter.position.x = spawn_pos[0]
        fighter.position.y = spawn_pos[1]
        fighter.velocity.x = 0
        fighter.velocity.y = 0
        fighter.health = fighter.max_health
        fighter.ammo = fighter.max_ammo
        fighter.is_alive = True
        fighter.invulnerable_timer = 2.0
        fighter.facing_angle = 0 if fighter.team == Team.BLUE else math.pi
    
    def _update_ball(self, dt: float):
        """Update ball physics"""
        if not self.state.ball:
            return
        
        ball = self.state.ball
        
        # If carried, follow carrier
        if ball.carrier_id:
            carrier = self.state.fighters.get(ball.carrier_id)
            if carrier and carrier.is_alive:
                ball.position.x = carrier.position.x + math.cos(carrier.facing_angle) * 30
                ball.position.y = carrier.position.y + math.sin(carrier.facing_angle) * 30
                ball.velocity.x = 0
                ball.velocity.y = 0
                return
            else:
                ball.carrier_id = None
        
        # Apply velocity
        ball.position.x += ball.velocity.x * dt
        ball.position.y += ball.velocity.y * dt
        
        # Apply friction
        ball.velocity.x *= BALL_FRICTION
        ball.velocity.y *= BALL_FRICTION
        
        # Wall bounce
        if ball.position.x < BALL_RADIUS + TILE_SIZE:
            # Check if in goal area
            goal = self.state.goals.get(Team.RED.value)
            if not (goal and goal.y < ball.position.y < goal.y + goal.height):
                ball.position.x = BALL_RADIUS + TILE_SIZE
                ball.velocity.x = -ball.velocity.x * 0.8
        
        if ball.position.x > ARENA_WIDTH - BALL_RADIUS - TILE_SIZE:
            goal = self.state.goals.get(Team.BLUE.value)
            if not (goal and goal.y < ball.position.y < goal.y + goal.height):
                ball.position.x = ARENA_WIDTH - BALL_RADIUS - TILE_SIZE
                ball.velocity.x = -ball.velocity.x * 0.8
        
        if ball.position.y < BALL_RADIUS + TILE_SIZE:
            ball.position.y = BALL_RADIUS + TILE_SIZE
            ball.velocity.y = -ball.velocity.y * 0.8
        
        if ball.position.y > ARENA_HEIGHT - BALL_RADIUS - TILE_SIZE:
            ball.position.y = ARENA_HEIGHT - BALL_RADIUS - TILE_SIZE
            ball.velocity.y = -ball.velocity.y * 0.8
    
    def _check_goals(self):
        """Check if ball is in a goal"""
        if not self.state.ball or self.state.ball.carrier_id:
            return
        
        ball = self.state.ball
        
        for team_value, goal in self.state.goals.items():
            if goal.contains(ball.position):
                # Goal scored!
                scoring_team = Team(team_value)
                self.state.scores[scoring_team.value] += 1
                self.state.last_scorer_team = scoring_team
                self.state.phase = GamePhase.GOAL_SCORED
                self.state.goal_celebration_timer = GOAL_CELEBRATION_TIME
                return
    
    def _reset_round(self):
        """Reset positions for next round"""
        # Reset ball
        self.state.ball = Ball(position=Position(ARENA_WIDTH / 2, ARENA_HEIGHT / 2))
        
        # Reset fighters to spawn positions
        blue_idx = 0
        red_idx = 0
        
        for fighter in self.state.fighters.values():
            if fighter.team == Team.BLUE:
                spawn_pos = SPAWN_POSITIONS[Team.BLUE][blue_idx % 2]
                blue_idx += 1
            else:
                spawn_pos = SPAWN_POSITIONS[Team.RED][red_idx % 2]
                red_idx += 1
            
            fighter.position.x = spawn_pos[0]
            fighter.position.y = spawn_pos[1]
            fighter.velocity.x = 0
            fighter.velocity.y = 0
            fighter.health = fighter.max_health
            fighter.ammo = fighter.max_ammo
            fighter.is_alive = True
            fighter.is_carrying_ball = False
            fighter.facing_angle = 0 if fighter.team == Team.BLUE else math.pi
        
        # Clear projectiles
        self.state.projectiles.clear()
        
        # Start countdown
        self.state.phase = GamePhase.COUNTDOWN
        self.state.countdown_timer = COUNTDOWN_TIME
    
    def _end_game(self):
        """End the game"""
        self.state.phase = GamePhase.GAME_OVER
        
        if self.state.scores[0] > self.state.scores[1]:
            self.state.winner_team = Team.BLUE
        elif self.state.scores[1] > self.state.scores[0]:
            self.state.winner_team = Team.RED
        else:
            self.state.winner_team = None  # Draw
    
    def _resolve_wall_collision(self, x: float, y: float, radius: float) -> Tuple[float, float]:
        """Resolve collision with walls"""
        for wall in self.state.walls:
            # Check collision with wall rectangle
            closest_x = clamp(x, wall.x, wall.x + wall.width)
            closest_y = clamp(y, wall.y, wall.y + wall.height)
            
            dx = x - closest_x
            dy = y - closest_y
            dist = math.sqrt(dx * dx + dy * dy)
            
            if dist < radius and dist > 0:
                # Push out of wall
                overlap = radius - dist
                x += (dx / dist) * overlap
                y += (dy / dist) * overlap
        
        # Keep in bounds
        x = clamp(x, radius + TILE_SIZE, ARENA_WIDTH - radius - TILE_SIZE)
        y = clamp(y, radius + TILE_SIZE, ARENA_HEIGHT - radius - TILE_SIZE)
        
        return x, y
    
    def _point_in_rect(self, x: float, y: float, wall: Wall) -> bool:
        """Check if point is in rectangle"""
        return (wall.x <= x <= wall.x + wall.width and
                wall.y <= y <= wall.y + wall.height)
    
    # AI Methods
    
    def _update_ai(self, fighter: Fighter, dt: float):
        """Update AI for a fighter"""
        if not fighter.is_alive:
            return
        
        fighter.ai_decision_timer -= dt
        
        if fighter.ai_decision_timer <= 0:
            self._ai_make_decision(fighter)
            fighter.ai_decision_timer = AI_REACTION_TIME + random.random() * 0.1
        
        self._ai_execute_state(fighter)
    
    def _ai_make_decision(self, fighter: Fighter):
        """AI decision making"""
        stats = BRAWLER_STATS.get(fighter.brawler_type.value, {})
        aggression = stats.get('ai_aggression', 0.5)
        
        # Check health - retreat if low
        health_percent = fighter.health / fighter.max_health
        if health_percent < 0.25:
            fighter.ai_state = "retreat"
            return
        
        # If we have the ball, try to score
        if fighter.is_carrying_ball:
            fighter.ai_state = "score"
            return
        
        # If teammate has ball, support
        for fid, f in self.state.fighters.items():
            if f.team == fighter.team and f.id != fighter.id and f.is_carrying_ball:
                fighter.ai_state = "support"
                return
        
        # If enemy has ball
        for fid, f in self.state.fighters.items():
            if f.team != fighter.team and f.is_carrying_ball:
                if random.random() < aggression:
                    fighter.ai_state = "attack"
                    fighter.ai_target_id = fid
                else:
                    fighter.ai_state = "defend"
                return
        
        # Ball is free
        fighter.ai_state = "chase_ball"
    
    def _ai_execute_state(self, fighter: Fighter):
        """Execute AI actions based on state"""
        inp = self.fighter_inputs.setdefault(fighter.id, {})
        
        if fighter.ai_state == "chase_ball":
            self._ai_chase_ball(fighter, inp)
        elif fighter.ai_state == "attack":
            self._ai_attack(fighter, inp)
        elif fighter.ai_state == "defend":
            self._ai_defend(fighter, inp)
        elif fighter.ai_state == "score":
            self._ai_score(fighter, inp)
        elif fighter.ai_state == "retreat":
            self._ai_retreat(fighter, inp)
        elif fighter.ai_state == "support":
            self._ai_support(fighter, inp)
        else:
            inp["move_x"] = 0
            inp["move_y"] = 0
    
    def _ai_chase_ball(self, fighter: Fighter, inp: Dict):
        """AI: Chase the ball"""
        if not self.state.ball:
            return
        
        target_x = self.state.ball.position.x
        target_y = self.state.ball.position.y
        
        # Predict ball movement
        target_x += self.state.ball.velocity.x * 0.5
        target_y += self.state.ball.velocity.y * 0.5
        
        self._ai_move_towards(fighter, inp, target_x, target_y)
    
    def _ai_attack(self, fighter: Fighter, inp: Dict):
        """AI: Attack enemies"""
        target = self.state.fighters.get(fighter.ai_target_id)
        if not target or not target.is_alive:
            # Find new target
            for fid, f in self.state.fighters.items():
                if f.team != fighter.team and f.is_alive:
                    fighter.ai_target_id = fid
                    target = f
                    break
        
        if not target:
            fighter.ai_state = "idle"
            return
        
        stats = BRAWLER_STATS.get(fighter.brawler_type.value, {})
        attack_range = stats.get('attack_range', 300)
        
        dist = fighter.position.distance_to(target.position)
        
        if dist > attack_range * 0.8:
            self._ai_move_towards(fighter, inp, target.position.x, target.position.y)
        elif dist < attack_range * 0.3 and fighter.brawler_type != BrawlerType.EDGAR:
            self._ai_move_away(fighter, inp, target.position.x, target.position.y)
        else:
            inp["move_x"] = 0
            inp["move_y"] = 0
        
        # Aim at target
        self._ai_aim_at(fighter, target.position.x, target.position.y)
        
        if dist <= attack_range:
            inp["attack"] = True
            
            # Use super if ready
            if fighter.super_charge >= 100:
                inp["ability"] = True
    
    def _ai_defend(self, fighter: Fighter, inp: Dict):
        """AI: Defend goal"""
        if not self.state.ball:
            return
        
        # Position between ball and our goal
        if fighter.team == Team.BLUE:
            goal_x = ARENA_WIDTH * 0.15
        else:
            goal_x = ARENA_WIDTH * 0.85
        goal_y = ARENA_HEIGHT / 2
        
        ball = self.state.ball
        dx = goal_x - ball.position.x
        dy = goal_y - ball.position.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist > 0:
            target_x = ball.position.x + dx * 0.5
            target_y = ball.position.y + dy * 0.5
        else:
            target_x = goal_x
            target_y = goal_y
        
        self._ai_move_towards(fighter, inp, target_x, target_y)
        self._ai_aim_at(fighter, ball.position.x, ball.position.y)
    
    def _ai_score(self, fighter: Fighter, inp: Dict):
        """AI: Try to score"""
        # Move towards enemy goal
        if fighter.team == Team.BLUE:
            goal_x = ARENA_WIDTH + 30
        else:
            goal_x = -30
        goal_y = ARENA_HEIGHT / 2
        
        self._ai_move_towards(fighter, inp, goal_x, goal_y)
        self._ai_aim_at(fighter, goal_x, goal_y)
        
        # Kick when close
        dist_to_goal = abs(fighter.position.x - goal_x)
        if dist_to_goal < 150:
            inp["attack"] = True
    
    def _ai_retreat(self, fighter: Fighter, inp: Dict):
        """AI: Retreat to spawn"""
        spawn_idx = 0
        spawn_pos = SPAWN_POSITIONS[fighter.team][spawn_idx]
        self._ai_move_towards(fighter, inp, spawn_pos[0], spawn_pos[1])
    
    def _ai_support(self, fighter: Fighter, inp: Dict):
        """AI: Support teammate with ball"""
        ball_carrier = None
        for fid, f in self.state.fighters.items():
            if f.is_carrying_ball:
                ball_carrier = f
                break
        
        if ball_carrier:
            # Move ahead of carrier towards enemy goal
            if fighter.team == Team.BLUE:
                target_x = ball_carrier.position.x + 100
            else:
                target_x = ball_carrier.position.x - 100
            target_y = ball_carrier.position.y
            
            self._ai_move_towards(fighter, inp, target_x, target_y)
        
        # Attack nearby enemies
        for fid, f in self.state.fighters.items():
            if f.team != fighter.team and f.is_alive:
                dist = fighter.position.distance_to(f.position)
                stats = BRAWLER_STATS.get(fighter.brawler_type.value, {})
                if dist < stats.get('attack_range', 300):
                    self._ai_aim_at(fighter, f.position.x, f.position.y)
                    inp["attack"] = True
                    break
    
    def _ai_move_towards(self, fighter: Fighter, inp: Dict, target_x: float, target_y: float):
        """Move AI towards target"""
        dx = target_x - fighter.position.x
        dy = target_y - fighter.position.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist > 10:
            inp["move_x"] = dx / dist
            inp["move_y"] = dy / dist
        else:
            inp["move_x"] = 0
            inp["move_y"] = 0
    
    def _ai_move_away(self, fighter: Fighter, inp: Dict, target_x: float, target_y: float):
        """Move AI away from target"""
        dx = fighter.position.x - target_x
        dy = fighter.position.y - target_y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist > 0:
            inp["move_x"] = dx / dist
            inp["move_y"] = dy / dist
    
    def _ai_aim_at(self, fighter: Fighter, target_x: float, target_y: float):
        """Aim AI at target with some error"""
        error = random.uniform(-AI_AIM_ERROR, AI_AIM_ERROR)
        fighter.facing_angle = math.atan2(
            target_y - fighter.position.y,
            target_x - fighter.position.x
        ) + error
    
    # Game loop
    
    async def run(self):
        """Run the game loop"""
        self.setup_game()
        
        tick_rate = 1 / 60
        
        while self.state.phase != GamePhase.GAME_OVER:
            loop_start = time.time()
            
            self.update(tick_rate)
            
            # Broadcast state
            await self.broadcast({
                "type": "brawler_game_state",
                "state": self.state.to_dict()
            })
            
            # Sleep to maintain tick rate
            elapsed = time.time() - loop_start
            if elapsed < tick_rate:
                await asyncio.sleep(tick_rate - elapsed)
        
        # Send final game over message
        await self.broadcast({
            "type": "brawler_game_over",
            "winner_team": self.state.winner_team.value if self.state.winner_team else None,
            "scores": self.state.scores,
            "state": self.state.to_dict()
        })
    
    def start(self):
        """Start the game task"""
        self.game_task = asyncio.create_task(self.run())
    
    def stop(self):
        """Stop the game"""
        self.state.phase = GamePhase.GAME_OVER
        if self.game_task:
            self.game_task.cancel()
