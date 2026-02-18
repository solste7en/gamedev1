"""
Brawler game state models for multiplayer web version
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import math
import random


class BrawlerType(Enum):
    COLT = "colt"
    SHELLY = "shelly"
    PIPER = "piper"
    EDGAR = "edgar"


class Team(Enum):
    BLUE = 0
    RED = 1


class GamePhase(Enum):
    WAITING = "waiting"
    COUNTDOWN = "countdown"
    PLAYING = "playing"
    GOAL_SCORED = "goal_scored"
    GAME_OVER = "game_over"
    PAUSED = "paused"


class ProjectileType(Enum):
    BULLET = "bullet"
    PELLET = "pellet"
    SNIPER = "sniper"
    MELEE = "melee"
    GRENADE = "grenade"


# ============== Game Constants ==============

ARENA_WIDTH = 672   # 21 tiles * 32
ARENA_HEIGHT = 480  # 15 tiles * 32
TILE_SIZE = 32

GOAL_WIDTH = 96     # 3 tiles
GOAL_DEPTH = 64     # 2 tiles

MATCH_DURATION = 120  # 2 minutes
GOALS_TO_WIN = 2
RESPAWN_TIME = 3.0
COUNTDOWN_TIME = 3.0
GOAL_CELEBRATION_TIME = 2.0

BALL_RADIUS = 18
BALL_PICKUP_RANGE = 30
BALL_SHOOT_SPEED = 400
BALL_FRICTION = 0.98

BRAWLER_RADIUS = 20
FRICTION = 0.92
KNOCKBACK_FORCE = 8

# Speed values (pixels per second)
SPEED_SLOW = 180
SPEED_NORMAL = 220
SPEED_FAST = 260
SPEED_VERY_FAST = 300

# Range values (in pixels)
RANGE_MELEE = 60
RANGE_SHORT = 150
RANGE_MEDIUM = 250
RANGE_LONG = 350
RANGE_VERY_LONG = 450

# AI Settings
AI_REACTION_TIME = 0.15
AI_AIM_ERROR = 0.15

BRAWLER_STATS = {
    'colt': {
        'name': 'Colt',
        'max_health': 3600,
        'speed': SPEED_FAST,
        'attack_range': RANGE_LONG,
        'attack_damage': 420,
        'attack_projectiles': 6,
        'attack_spread': 0.05,
        'reload_time': 1.3,
        'max_ammo': 3,
        'projectile_speed': 600,
        'super_damage': 420,
        'super_projectiles': 12,
        'super_charge_per_hit': 8,
        'super_charge_per_damage': 10,
        'ai_aggression': 0.6,
        'color': '#4682E6'
    },
    'shelly': {
        'name': 'Shelly',
        'max_health': 5100,
        'speed': SPEED_NORMAL,
        'attack_range': RANGE_MEDIUM,
        'attack_damage': 420,
        'attack_projectiles': 5,
        'attack_spread': 0.4,
        'reload_time': 1.5,
        'max_ammo': 3,
        'projectile_speed': 500,
        'super_damage': 480,
        'super_projectiles': 9,
        'super_knockback': 300,
        'super_charge_per_hit': 7,
        'super_charge_per_damage': 12,
        'ai_aggression': 0.8,
        'color': '#A050B4'
    },
    'piper': {
        'name': 'Piper',
        'max_health': 2800,
        'speed': SPEED_SLOW,
        'attack_range': RANGE_VERY_LONG,
        'attack_damage_min': 1400,
        'attack_damage_max': 2800,
        'attack_projectiles': 1,
        'attack_spread': 0,
        'reload_time': 2.3,
        'max_ammo': 3,
        'projectile_speed': 700,
        'super_grenades': 4,
        'super_grenade_damage': 900,
        'super_jump_range': 300,
        'super_charge_per_hit': 15,
        'super_charge_per_damage': 15,
        'ai_aggression': 0.3,
        'color': '#FF96B4'
    },
    'edgar': {
        'name': 'Edgar',
        'max_health': 4200,
        'speed': SPEED_VERY_FAST,
        'attack_range': RANGE_MELEE,
        'attack_damage': 756,
        'attack_projectiles': 2,
        'attack_spread': 0.6,
        'reload_time': 0.7,
        'max_ammo': 2,
        'heal_percent': 0.35,
        'super_jump_range': 350,
        'super_auto_charge': 2.5,
        'super_charge_per_hit': 5,
        'super_charge_per_damage': 8,
        'ai_aggression': 0.9,
        'color': '#C83232'
    }
}

# Spawn positions for each team (2 per team)
SPAWN_POSITIONS = {
    Team.BLUE: [
        (ARENA_WIDTH * 0.15, ARENA_HEIGHT * 0.35),
        (ARENA_WIDTH * 0.15, ARENA_HEIGHT * 0.65),
    ],
    Team.RED: [
        (ARENA_WIDTH * 0.85, ARENA_HEIGHT * 0.35),
        (ARENA_WIDTH * 0.85, ARENA_HEIGHT * 0.65),
    ]
}


@dataclass
class Position:
    x: float
    y: float
    
    def to_dict(self) -> Dict:
        return {"x": self.x, "y": self.y}
    
    def distance_to(self, other: 'Position') -> float:
        dx = other.x - self.x
        dy = other.y - self.y
        return math.sqrt(dx * dx + dy * dy)
    
    def angle_to(self, other: 'Position') -> float:
        dx = other.x - self.x
        dy = other.y - self.y
        return math.atan2(dy, dx)


@dataclass
class Velocity:
    x: float = 0
    y: float = 0
    
    def to_dict(self) -> Dict:
        return {"x": self.x, "y": self.y}


@dataclass 
class Fighter:
    id: str
    player_id: Optional[int]  # None for AI
    brawler_type: BrawlerType
    team: Team
    position: Position
    velocity: Velocity = field(default_factory=Velocity)
    
    health: int = 0
    max_health: int = 0
    ammo: int = 3
    max_ammo: int = 3
    super_charge: float = 0  # 0-100
    
    facing_angle: float = 0  # Radians
    move_direction: Tuple[float, float] = (0, 0)
    
    is_alive: bool = True
    respawn_timer: float = 0
    reload_timer: float = 0
    attack_cooldown: float = 0
    
    is_carrying_ball: bool = False
    is_jumping: bool = False
    jump_target: Optional[Position] = None
    invulnerable_timer: float = 0
    
    # AI-specific
    is_ai: bool = False
    ai_state: str = "idle"
    ai_target_id: Optional[str] = None
    ai_decision_timer: float = 0
    
    def __post_init__(self):
        stats = BRAWLER_STATS.get(self.brawler_type.value, {})
        self.max_health = stats.get('max_health', 3000)
        self.health = self.max_health
        self.max_ammo = stats.get('max_ammo', 3)
        self.ammo = self.max_ammo
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "player_id": self.player_id,
            "brawler_type": self.brawler_type.value,
            "team": self.team.value,
            "position": self.position.to_dict(),
            "velocity": self.velocity.to_dict(),
            "health": self.health,
            "max_health": self.max_health,
            "ammo": self.ammo,
            "max_ammo": self.max_ammo,
            "super_charge": self.super_charge,
            "facing_angle": self.facing_angle,
            "is_alive": self.is_alive,
            "is_carrying_ball": self.is_carrying_ball,
            "is_jumping": self.is_jumping,
            "invulnerable": self.invulnerable_timer > 0,
            "is_ai": self.is_ai
        }


@dataclass
class Projectile:
    id: str
    owner_id: str
    team: Team
    projectile_type: ProjectileType
    position: Position
    velocity: Velocity
    damage: int
    range_remaining: float
    
    piercing: bool = False
    knockback: float = 0
    hit_targets: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "team": self.team.value,
            "type": self.projectile_type.value,
            "position": self.position.to_dict(),
            "velocity": self.velocity.to_dict(),
            "damage": self.damage
        }


@dataclass
class Ball:
    position: Position
    velocity: Velocity = field(default_factory=Velocity)
    carrier_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "position": self.position.to_dict(),
            "velocity": self.velocity.to_dict(),
            "carrier_id": self.carrier_id
        }


@dataclass
class Goal:
    team: Team
    x: float
    y: float
    width: float
    height: float
    
    def contains(self, pos: Position) -> bool:
        return (self.x <= pos.x <= self.x + self.width and
                self.y <= pos.y <= self.y + self.height)
    
    def to_dict(self) -> Dict:
        return {
            "team": self.team.value,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height
        }


@dataclass
class Wall:
    x: float
    y: float
    width: float
    height: float
    destructible: bool = False
    health: int = 100
    
    def to_dict(self) -> Dict:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "destructible": self.destructible
        }


@dataclass
class BrawlerGameState:
    phase: GamePhase = GamePhase.WAITING
    
    fighters: Dict[str, Fighter] = field(default_factory=dict)
    projectiles: Dict[str, Projectile] = field(default_factory=dict)
    ball: Optional[Ball] = None
    walls: List[Wall] = field(default_factory=list)
    goals: Dict[int, Goal] = field(default_factory=dict)  # team -> goal
    
    scores: Dict[int, int] = field(default_factory=lambda: {0: 0, 1: 0})  # team -> score
    time_remaining: float = MATCH_DURATION
    countdown_timer: float = COUNTDOWN_TIME
    goal_celebration_timer: float = 0
    last_scorer_team: Optional[Team] = None
    
    overtime: bool = False
    winner_team: Optional[Team] = None
    
    arena_width: float = ARENA_WIDTH
    arena_height: float = ARENA_HEIGHT
    
    next_projectile_id: int = 0
    
    def get_projectile_id(self) -> str:
        self.next_projectile_id += 1
        return f"proj_{self.next_projectile_id}"
    
    def to_dict(self) -> Dict:
        return {
            "phase": self.phase.value,
            "fighters": {fid: f.to_dict() for fid, f in self.fighters.items()},
            "projectiles": {pid: p.to_dict() for pid, p in self.projectiles.items()},
            "ball": self.ball.to_dict() if self.ball else None,
            "walls": [w.to_dict() for w in self.walls],
            "goals": {t: g.to_dict() for t, g in self.goals.items()},
            "scores": self.scores,
            "time_remaining": self.time_remaining,
            "countdown_timer": self.countdown_timer,
            "overtime": self.overtime,
            "winner_team": self.winner_team.value if self.winner_team else None,
            "arena_width": self.arena_width,
            "arena_height": self.arena_height
        }


# Helper functions

def normalize(x: float, y: float) -> Tuple[float, float]:
    length = math.sqrt(x * x + y * y)
    if length == 0:
        return (0, 0)
    return (x / length, y / length)


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def clamp(value: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, value))
