"""
Game state models for multiplayer snake games
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import random
import time
import math


class GameMode(Enum):
    SURVIVAL = "survival"
    HIGH_SCORE = "high_score"
    SINGLE_PLAYER = "single_player"
    BATTLE_ROYALE = "battle_royale"
    DUEL = "duel"


class GameType(Enum):
    SNAKE_CLASSIC = "snake_classic"
    SNAKE_3D = "snake_3d"
    BRAWLER = "brawler"


class BarrierDensity(Enum):
    NONE = "none"
    SPARSE = "sparse"
    MODERATE = "moderate"
    DENSE = "dense"


# Time limit options for high score mode (in seconds)
TIME_LIMIT_OPTIONS = {
    "30s": {"name": "30 Seconds", "seconds": 30},
    "1m": {"name": "1 Minute", "seconds": 60},
    "2m": {"name": "2 Minutes", "seconds": 120},
    "3m": {"name": "3 Minutes", "seconds": 180}
}
TIME_LIMIT_ORDER = ["30s", "1m", "2m", "3m"]
DEFAULT_TIME_LIMIT = "1m"


class Direction(Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"


class PlayerState(Enum):
    WAITING = "waiting"
    READY = "ready"
    PLAYING = "playing"
    DEAD = "dead"
    SPECTATING = "spectating"


class AIDifficulty(Enum):
    AMATEUR = "amateur"
    SEMI_PRO = "semi_pro"
    PRO = "pro"
    WORLD_CLASS = "world_class"


AI_DIFFICULTY_SETTINGS = {
    "amateur": {
        "name": "Amateur",
        "reaction_time": 260,
        "food_seeking": 0.70,
        "deterministic": False,
        "dead_end_check": False,
        "flood_fill_depth": 8,
        "dead_end_threshold": 0.2,
        "randomness": 35,
        "use_pathfinding": False,
        "pathfinding_depth": 20,
        "value_power": 1.0,
        "combo_aware": False,
        "survival_awareness": False,
    },
    "semi_pro": {
        "name": "Semi-Pro",
        "reaction_time": 140,
        "food_seeking": 0.88,
        "deterministic": False,
        "dead_end_check": True,
        "flood_fill_depth": 20,
        "dead_end_threshold": 0.25,
        "randomness": 15,
        "use_pathfinding": True,
        "pathfinding_depth": 35,
        "value_power": 1.0,
        "combo_aware": False,
        "survival_awareness": True,
    },
    "pro": {
        "name": "Pro",
        "reaction_time": 90,
        "food_seeking": 0.95,
        "deterministic": True,
        "dead_end_check": True,
        "flood_fill_depth": 28,
        "dead_end_threshold": 0.28,
        "randomness": 5,
        "use_pathfinding": True,
        "pathfinding_depth": 42,
        "value_power": 1.2,
        "combo_aware": True,
        "survival_awareness": True,
    },
    "world_class": {
        "name": "World-Class",
        "reaction_time": 45,
        "food_seeking": 1.0,
        "deterministic": True,
        "dead_end_check": True,
        "flood_fill_depth": 50,
        "dead_end_threshold": 0.35,
        "randomness": 0,
        "use_pathfinding": True,
        "pathfinding_depth": 65,
        "value_power": 1.4,
        "combo_aware": True,
        "survival_awareness": True,
    }
}


@dataclass
class Position:
    x: int
    y: int
    
    def to_dict(self):
        return {"x": self.x, "y": self.y}
    
    def __eq__(self, other):
        if isinstance(other, Position):
            return self.x == other.x and self.y == other.y
        return False
    
    def __hash__(self):
        return hash((self.x, self.y))


@dataclass
class Food:
    position: Position
    value: int = 1  # Score value (TOTAL kill value; score per hit = value // max_health)
    health: int = 1  # Hits remaining
    max_health: int = 1  # Original health for health bar display
    color: str = "#FF0000"
    colors: Dict = field(default_factory=dict)  # Detailed color map
    food_type: str = "mouse"  # mouse, rabbit, etc.
    size: int = 1  # Visual size
    cells: List[Tuple[int, int]] = field(default_factory=list)  # Cell offsets
    category: str = "small"  # small, medium, large, huge
    hit_recovery: float = 0.0  # Seconds until this animal can be hit again (non-consecutive rule)
    
    def to_dict(self):
        return {
            "position": self.position.to_dict(),
            "value": self.value,
            "health": self.health,
            "max_health": self.max_health,
            "color": self.color,
            "colors": self.colors,
            "type": self.food_type,
            "size": self.size,
            "cells": self.cells,
            "category": self.category,
            "hit_recovery": round(self.hit_recovery, 2),
            "recovering": self.hit_recovery > 0,
        }
    
    def get_all_positions(self) -> List[Position]:
        """Get all positions occupied by this food"""
        positions = []
        for dx, dy in self.cells:
            positions.append(Position(self.position.x + dx, self.position.y + dy))
        return positions


@dataclass
class Wall:
    """A barrier/wall segment"""
    position: Position
    width: int = 1  # In cells
    height: int = 1  # In cells
    
    def to_dict(self):
        return {
            "position": self.position.to_dict(),
            "width": self.width,
            "height": self.height
        }
    
    def get_all_positions(self) -> List[Position]:
        """Get all positions occupied by this wall"""
        positions = []
        for dx in range(self.width):
            for dy in range(self.height):
                positions.append(Position(self.position.x + dx, self.position.y + dy))
        return positions


@dataclass
class Snake:
    player_id: int
    body: List[Position] = field(default_factory=list)
    direction: Direction = Direction.RIGHT
    next_direction: Direction = Direction.RIGHT
    color: str = "#00FF00"
    alive: bool = True
    score: int = 0
    combo: int = 0
    combo_timer: float = 0
    # Survival mode: time until next tail segment is lost (counts down each tick)
    decay_timer: float = 6.0
    # Spawn freeze: snake is visible but invulnerable and cannot move (seconds remaining)
    spawn_freeze: float = 0.0
    
    def to_dict(self):
        return {
            "player_id": self.player_id,
            "body": [p.to_dict() for p in self.body],
            "direction": self.direction.value,
            "color": self.color,
            "alive": self.alive,
            "score": self.score,
            "combo": self.combo,
            "decay_timer": self.decay_timer,
            "spawn_freeze": round(self.spawn_freeze, 2)
        }


@dataclass
class Player:
    id: int
    name: str
    websocket: any = None
    state: PlayerState = PlayerState.WAITING
    snake: Optional[Snake] = None
    quadrant: int = 0  # 0-3 for which quadrant they're in
    death_time: Optional[float] = None
    rank: int = 0
    is_ai: bool = False
    ai_difficulty: str = "amateur"  # amateur, semi_pro, pro, world_class
    ai_last_decision: float = 0  # Timestamp of last AI decision
    death_count: int = 0          # Number of deaths this game (drives respawn penalty)
    respawn_delay: float = 2.0    # Current respawn delay in seconds (fibonacci-based)
    
    def to_dict(self):
        d = {
            "id": self.id,
            "name": self.name,
            "state": self.state.value,
            "quadrant": self.quadrant,
            "rank": self.rank,
            "snake": self.snake.to_dict() if self.snake else None,
            "is_ai": self.is_ai,
            "ai_difficulty": self.ai_difficulty,
            "death_count": self.death_count,
            "respawn_delay": self.respawn_delay,
        }
        # Include remaining respawn time so client can display a countdown
        if self.death_time and self.state == PlayerState.DEAD:
            d["respawn_remaining"] = max(0.0, round(self.respawn_delay - (time.time() - self.death_time), 1))
        else:
            d["respawn_remaining"] = 0.0
        return d


@dataclass
class QuadrantBounds:
    x_min: int
    x_max: int
    y_min: int
    y_max: int
    
    def contains(self, pos: Position) -> bool:
        return (self.x_min <= pos.x < self.x_max and 
                self.y_min <= pos.y < self.y_max)
    
    def to_dict(self):
        return {
            "x_min": self.x_min,
            "x_max": self.x_max,
            "y_min": self.y_min,
            "y_max": self.y_max
        }


@dataclass
class GameState:
    game_type: GameType = GameType.SNAKE_CLASSIC
    mode: GameMode = GameMode.SURVIVAL
    barrier_density: str = "none"  # none, sparse, moderate, dense
    map_size: str = "medium"  # small, medium, large, extra_large
    
    # Grid settings
    grid_width: int = 40
    grid_height: int = 40
    quadrant_width: int = 20
    quadrant_height: int = 20
    
    # Game state
    running: bool = False
    paused: bool = False
    game_over: bool = False
    winner_id: Optional[int] = None
    
    # Timing
    start_time: float = 0
    elapsed_time: float = 0
    time_limit: float = 180  # 3 minutes for high score mode
    
    # Survival mode specifics
    shrink_interval: float = 30  # Seconds between shrinks
    shrink_amount: int = 1  # Cells to shrink per interval
    next_shrink_time: float = 30
    # Tail decay pressure
    survival_decay_min_length: int = 3   # Min body length before death
    survival_decay_current_interval: float = 6.0  # Active decay interval (sent to client for HUD)
    # Speed ramp pressure
    survival_speed_increase_interval: float = 15.0  # Seconds between ramps
    survival_speed_factor: float = 0.95             # Multiply speed by this each ramp (5% faster)
    survival_speed_next_increase: float = 15.0      # When next ramp fires
    
    # High score mode specifics
    speed_increase_interval: float = 60  # Seconds between speed increases
    base_speed: float = 100  # ms between moves
    current_speed: float = 100
    speed_increase_factor: float = 0.85  # Multiply speed by this
    
    # Single player mode specifics
    single_player_high_score: int = 0
    
    # Players and food
    players: Dict[int, Player] = field(default_factory=dict)
    foods: Dict[int, List[Food]] = field(default_factory=dict)  # Per quadrant
    quadrant_bounds: Dict[int, QuadrantBounds] = field(default_factory=dict)
    walls: Dict[int, List[Wall]] = field(default_factory=dict)  # Per quadrant
    
    # Stats
    alive_count: int = 0

    # Duel series tracking
    series_length: int = 0          # 0 = no series; 3/5/7
    series_scores: Dict[int, int] = field(default_factory=dict)  # player_id -> rounds won
    current_round: int = 1
    series_winner_id: Optional[int] = None
    
    def to_dict(self):
        return {
            "game_type": self.game_type.value,
            "mode": self.mode.value,
            "barrier_density": self.barrier_density,
            "map_size": self.map_size,
            "grid_width": self.grid_width,
            "grid_height": self.grid_height,
            "running": self.running,
            "paused": self.paused,
            "game_over": self.game_over,
            "winner_id": self.winner_id,
            "elapsed_time": self.elapsed_time,
            "time_limit": self.time_limit,
            "current_speed": self.current_speed,
            "players": {pid: p.to_dict() for pid, p in self.players.items()},
            "foods": {q: [f.to_dict() for f in foods] for q, foods in self.foods.items()},
            "quadrant_bounds": {q: b.to_dict() for q, b in self.quadrant_bounds.items()},
            "walls": {q: [w.to_dict() for w in walls] for q, walls in self.walls.items()},
            "alive_count": self.alive_count,
            "single_player_high_score": self.single_player_high_score,
            "survival_decay_current_interval": self.survival_decay_current_interval,
            "survival_speed_next_increase": self.survival_speed_next_increase,
            "series_length": self.series_length,
            "series_scores": self.series_scores,
            "current_round": self.current_round,
            "series_winner_id": self.series_winner_id,
        }

    def to_dict_delta(self):
        """Lightweight state dict excluding static fields (walls, quadrant_bounds).
        Clients merge this with the initial full state received at game_start."""
        return {
            "running": self.running,
            "paused": self.paused,
            "game_over": self.game_over,
            "winner_id": self.winner_id,
            "elapsed_time": self.elapsed_time,
            "time_limit": self.time_limit,
            "current_speed": self.current_speed,
            "players": {pid: p.to_dict() for pid, p in self.players.items()},
            "foods": {q: [f.to_dict() for f in foods] for q, foods in self.foods.items()},
            "alive_count": self.alive_count,
            "survival_decay_current_interval": self.survival_decay_current_interval,
            "survival_speed_next_increase": self.survival_speed_next_increase,
            "series_length": self.series_length,
            "series_scores": self.series_scores,
            "current_round": self.current_round,
            "series_winner_id": self.series_winner_id,
        }


# Map size configurations (matching pygame version)
MAP_SIZES = {
    "small": {
        "name": "Small",
        "width": 25,
        "height": 18,
        "description": "Compact arenas - fast games"
    },
    "medium": {
        "name": "Medium",
        "width": 35,
        "height": 22,
        "description": "Balanced gameplay"
    },
    "large": {
        "name": "Large",
        "width": 45,
        "height": 28,
        "description": "Plenty of room to roam"
    },
    "extra_large": {
        "name": "Extra Large",
        "width": 60,
        "height": 36,
        "description": "Vast open arena"
    }
}

MAP_SIZE_ORDER = ["small", "medium", "large", "extra_large"]


# Barrier configurations
BARRIER_CONFIGS = {
    "none": {
        "name": "None",
        "description": "Classic mode - No obstacles",
        "multiplier": 1.0,
        "wall_count": 0,
    },
    "sparse": {
        "name": "Sparse",
        "description": "A few scattered walls",
        "multiplier": 1.25,
        "wall_count": 4,
    },
    "moderate": {
        "name": "Moderate",
        "description": "Strategic wall placement",
        "multiplier": 1.5,
        "wall_count": 8,
    },
    "dense": {
        "name": "Dense",
        "description": "Maze-like challenge",
        "multiplier": 2.0,
        "wall_count": 12,
    }
}

# Hit-recovery window per category (seconds between consecutive hits on same animal)
# Small animals = no recovery (one-shot), larger animals require re-approach
FOOD_HIT_RECOVERY = {
    "small":  0.0,   # One-shot, no cooldown
    "medium": 0.8,   # Must leave and return after 0.8s
    "large":  1.5,   # Meaningful re-approach required
    "huge":   2.5,   # Significant tactical gap needed
}

# Comprehensive animal types with shapes and detailed properties.
# Scoring philosophy (Hybrid A+B):
#   - Small animals: high base value (rewarding precision) — one-shot kill, full points immediately
#   - Multi-health animals: score awarded PER HIT (value // max_health per hit), not on full kill
#   - Non-consecutive hits enforced via hit_recovery window — must leave and re-approach
#   - Huge animals health capped at 5 (was 6-8)
ANIMAL_TYPES = {
    # Small animals (1 cell, 1 health) — high value, one-shot, full points instantly
    "mouse": {
        "value": 75, "health": 1, "size": 1, "weight": 25,
        "colors": {"body": "#A9A9A9", "ear": "#FFB6C1", "tail": "#FFA0A0", "eye": "#000000"},
        "cells": [(0, 0)], "category": "small"
    },
    "frog": {
        "value": 85, "health": 1, "size": 1, "weight": 20,
        "colors": {"body": "#32CD32", "belly": "#90EE90", "eye": "#FFD700"},
        "cells": [(0, 0)], "category": "small"
    },
    "bug": {
        "value": 65, "health": 1, "size": 1, "weight": 30,
        "colors": {"body": "#8B4513", "shell": "#A0522D", "legs": "#654321"},
        "cells": [(0, 0)], "category": "small"
    },
    "cricket": {
        "value": 65, "health": 1, "size": 1, "weight": 25,
        "colors": {"body": "#553723", "legs": "#3C2819"},
        "cells": [(0, 0)], "category": "small"
    },
    "worm": {
        "value": 60, "health": 1, "size": 1, "weight": 35,
        "colors": {"body": "#FF9696", "segment": "#FF7878"},
        "cells": [(0, 0)], "category": "small"
    },
    "butterfly": {
        "value": 100, "health": 1, "size": 1, "weight": 15,
        "colors": {"wing1": "#FF69B4", "wing2": "#FFB6C1", "body": "#463228"},
        "cells": [(0, 0)], "category": "small"
    },
    "spider": {
        "value": 70, "health": 1, "size": 1, "weight": 20,
        "colors": {"body": "#282828", "legs": "#1E1E1E", "eye": "#FF0000"},
        "cells": [(0, 0)], "category": "small"
    },
    "bee": {
        "value": 80, "health": 1, "size": 1, "weight": 18,
        "colors": {"body": "#FFC832", "stripes": "#281E14", "wings": "#C8DCFF"},
        "cells": [(0, 0)], "category": "small"
    },
    "ladybug": {
        "value": 70, "health": 1, "size": 1, "weight": 22,
        "colors": {"shell": "#DC2828", "spots": "#141414", "head": "#1E1E1E"},
        "cells": [(0, 0)], "category": "small"
    },
    
    # Medium animals (2-3 cells, 2-3 health) — score per hit (value // max_health), 0.8s recovery
    # Total per kill: stated value spread across hits
    "rabbit": {
        "value": 90, "health": 2, "size": 2, "weight": 12,   # 45 pts/hit × 2
        "colors": {"body": "#DCC8B4", "ear": "#FFB6C1", "nose": "#FF9696", "eye": "#323232"},
        "cells": [(0, 0), (1, 0)], "category": "medium"
    },
    "fish": {
        "value": 80, "health": 2, "size": 2, "weight": 14,   # 40 pts/hit × 2
        "colors": {"body": "#64B4DC", "scales": "#50A0C8", "fin": "#3C8CB4", "eye": "#1E1E1E"},
        "cells": [(0, 0), (1, 0)], "category": "medium"
    },
    "lizard": {
        "value": 120, "health": 3, "size": 3, "weight": 10,  # 40 pts/hit × 3
        "colors": {"body": "#3C783C", "belly": "#8CB464", "spots": "#285028", "eye": "#FFC800"},
        "cells": [(0, 0), (1, 0), (2, 0)], "category": "medium"
    },
    "turtle": {
        "value": 105, "health": 3, "size": 3, "weight": 11,  # 35 pts/hit × 3
        "colors": {"shell": "#50783C", "pattern": "#3C6428", "skin": "#648C50", "eye": "#1E1E1E"},
        "cells": [(0, 0), (1, 0), (0, 1)], "category": "medium"
    },
    "duck": {
        "value": 120, "health": 3, "size": 3, "weight": 9,   # 40 pts/hit × 3
        "colors": {"body": "#B48C50", "head": "#327832", "beak": "#FFA500", "eye": "#1E1E1E"},
        "cells": [(0, 0), (1, 0), (2, 0)], "category": "medium"
    },
    
    # Large animals (4-5 cells, 4-5 health) — 40pts/hit, 1.5s recovery
    "bird": {
        "value": 160, "health": 4, "size": 4, "weight": 7,   # 40 pts/hit × 4
        "colors": {"body": "#6495ED", "belly": "#ADD8E6", "wing": "#4169E1", "beak": "#FFA500", "eye": "#1E1E1E"},
        "cells": [(0, 0), (1, 0), (0, 1), (1, 1)], "category": "large"
    },
    "fox": {
        "value": 180, "health": 4, "size": 4, "weight": 6,   # 45 pts/hit × 4
        "colors": {"body": "#D2691E", "belly": "#FFDCB4", "tail_tip": "#FFFFFF", "eye": "#281E14"},
        "cells": [(0, 0), (1, 0), (2, 0), (0, 1)], "category": "large"
    },
    "wolf": {
        "value": 200, "health": 5, "size": 5, "weight": 5,   # 40 pts/hit × 5
        "colors": {"body": "#787882", "belly": "#B4B4BE", "muzzle": "#64646E", "eye": "#C8B432"},
        "cells": [(1, 0), (0, 1), (1, 1), (2, 1), (1, 2)], "category": "large"
    },
    "deer": {
        "value": 160, "health": 4, "size": 4, "weight": 6,   # 40 pts/hit × 4
        "colors": {"body": "#B48C64", "belly": "#DCC8AA", "spots": "#C8A078", "antlers": "#64503C"},
        "cells": [(0, 0), (0, 1), (0, 2), (0, 3)], "category": "large"
    },
    "pig": {
        "value": 160, "health": 4, "size": 4, "weight": 8,   # 40 pts/hit × 4
        "colors": {"body": "#FFB4B4", "snout": "#FF9696", "eye": "#1E1E1E"},
        "cells": [(0, 0), (1, 0), (0, 1), (1, 1)], "category": "large"
    },
    
    # Huge animals (health capped at 5, 2.5s recovery) — 60-80pts/hit
    "tiger": {
        "value": 300, "health": 5, "size": 6, "weight": 3,   # 60 pts/hit × 5
        "colors": {"body": "#FFA532", "stripes": "#281E14", "belly": "#FFDCB4", "eye": "#C8B432"},
        "cells": [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)], "category": "huge"
    },
    "lion": {
        "value": 350, "health": 5, "size": 6, "weight": 3,   # 70 pts/hit × 5
        "colors": {"body": "#DCB464", "mane": "#B47832", "belly": "#F0DCB4", "eye": "#967832"},
        "cells": [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)], "category": "huge"
    },
    "bear": {
        "value": 280, "health": 5, "size": 6, "weight": 4,   # 56 pts/hit × 5
        "colors": {"body": "#644632", "snout": "#8C6446", "belly": "#785A46", "eye": "#1E1914"},
        "cells": [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2)], "category": "huge"
    },
    "crocodile": {
        "value": 260, "health": 5, "size": 6, "weight": 4,   # 52 pts/hit × 5
        "colors": {"body": "#46643C", "belly": "#8CA078", "scales": "#325028", "eye": "#C8C832"},
        "cells": [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0)], "category": "huge"
    },
    "hippo": {
        "value": 375, "health": 5, "size": 8, "weight": 2,   # 75 pts/hit × 5 (was 8 health)
        "colors": {"body": "#826E78", "belly": "#B4A0AA", "mouth": "#C896A0", "eye": "#28232A"},
        "cells": [(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1), (3, 1)], "category": "huge"
    },
    "elephant": {
        "value": 400, "health": 5, "size": 8, "weight": 1,   # 80 pts/hit × 5 (was 8 health)
        "colors": {"body": "#8C8C96", "ear": "#A08C96", "tusk": "#FFFFF0", "eye": "#322D32"},
        "cells": [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2), (0, 3), (1, 3)], "category": "huge"
    },
}

# Weight by category for spawn probability
CATEGORY_WEIGHTS = {
    "small": 50,
    "medium": 30,
    "large": 15,
    "huge": 5
}


def get_random_food() -> dict:
    """Get a random food type based on weighted probability"""
    # First select category
    category_total = sum(CATEGORY_WEIGHTS.values())
    r = random.randint(1, category_total)
    cumulative = 0
    selected_category = "small"
    
    for cat, weight in CATEGORY_WEIGHTS.items():
        cumulative += weight
        if r <= cumulative:
            selected_category = cat
            break
    
    # Then select animal from category
    category_animals = [
        (name, data) for name, data in ANIMAL_TYPES.items() 
        if data["category"] == selected_category
    ]
    
    if not category_animals:
        # Fallback to any
        category_animals = list(ANIMAL_TYPES.items())
    
    total_weight = sum(a[1]["weight"] for a in category_animals)
    r = random.randint(1, total_weight)
    cumulative = 0
    
    for name, data in category_animals:
        cumulative += data["weight"]
        if r <= cumulative:
            return {
                "type": name,
                "value": data["value"],
                "health": data["health"],
                "max_health": data["health"],
                "color": data["colors"]["body"],
                "colors": data["colors"],
                "size": data["size"],
                "cells": data["cells"].copy(),
                "category": data["category"]
            }
    
    # Fallback
    name = "mouse"
    data = ANIMAL_TYPES[name]
    return {
        "type": name,
        "value": data["value"],
        "health": data["health"],
        "max_health": data["health"],
        "color": data["colors"]["body"],
        "colors": data["colors"],
        "size": data["size"],
        "cells": data["cells"].copy(),
        "category": data["category"]
    }


# Player colors
PLAYER_COLORS = [
    "#3498DB",  # Blue
    "#E74C3C",  # Red
    "#2ECC71",  # Green
    "#F1C40F",  # Yellow
]
