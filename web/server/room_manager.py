"""
Room manager for multiplayer game sessions
"""

import random
import string
from typing import Dict, Optional, List
from dataclasses import dataclass, field
import asyncio
from datetime import datetime
from .models import Player, PlayerState, GameType, GameMode


def generate_room_code() -> str:
    """Generate a random room code like SNAKE-XXXX"""
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(random.choices(chars, k=4))
    return f"SNAKE-{suffix}"


@dataclass
class Room:
    code: str
    host_id: int
    game_type: GameType = GameType.SNAKE_CLASSIC
    game_mode: GameMode = GameMode.SURVIVAL
    barrier_density: str = "none"  # none, sparse, moderate, dense
    map_size: str = "medium"  # small, medium, large, extra_large
    time_limit: str = "1m"  # 30s, 1m, 2m, 3m (for high score mode)
    players: Dict[int, Player] = field(default_factory=dict)
    max_players: int = 4
    min_players: int = 1  # Changed to 1 to support single player
    created_at: datetime = field(default_factory=datetime.now)
    game_started: bool = False
    
    # AI settings for Snake games
    ai_count: int = 0  # Number of AI players to add
    ai_difficulties: List[str] = field(default_factory=list)  # Per-AI difficulty levels
    ai_names: List[str] = field(default_factory=list)  # Custom names for AI bots
    
    # Brawler-specific fields
    team_assignments: Dict[int, int] = field(default_factory=dict)  # player_id -> team (0=blue, 1=red)
    character_selections: Dict[int, str] = field(default_factory=dict)  # player_id -> brawler_type
    
    def add_player(self, player: Player) -> bool:
        """Add a player to the room"""
        if len(self.players) >= self.max_players:
            return False
        if player.id in self.players:
            return False
        
        # Assign quadrant
        used_quadrants = {p.quadrant for p in self.players.values()}
        for q in range(4):
            if q not in used_quadrants:
                player.quadrant = q
                break
        
        self.players[player.id] = player
        return True
    
    def remove_player(self, player_id: int) -> Optional[Player]:
        """Remove a player from the room"""
        if player_id in self.players:
            return self.players.pop(player_id)
        return None
    
    def get_player(self, player_id: int) -> Optional[Player]:
        """Get a player by ID"""
        return self.players.get(player_id)
    
    def get_ready_count(self) -> int:
        """Count ready players"""
        return sum(1 for p in self.players.values() if p.state == PlayerState.READY)
    
    def can_start(self) -> bool:
        """Check if game can start.
        AI bots are always considered ready; only human players must explicitly ready up.
        """
        human_count = len(self.players)
        human_ready = self.get_ready_count()
        total_players = human_count + self.ai_count
        
        # Need at least 1 human player
        if human_count < 1:
            return False
        
        if self.game_started:
            return False
        
        # All human players must be ready
        if human_ready != human_count:
            return False
        
        # Total players (human + AI) must meet minimum requirement
        return total_players >= self.min_players
    
    def reset_for_rematch(self):
        """Reset room state for a new game (after game over)"""
        self.game_started = False
        # Reset all players to WAITING state
        for player in self.players.values():
            player.state = PlayerState.WAITING
            player.snake = None
            player.rank = None
            player.death_time = None
    
    def to_dict(self):
        result = {
            "code": self.code,
            "host_id": self.host_id,
            "game_type": self.game_type.value,
            "game_mode": self.game_mode.value,
            "barrier_density": self.barrier_density,
            "map_size": self.map_size,
            "time_limit": self.time_limit,
            "players": [p.to_dict() for p in self.players.values()],
            "max_players": self.max_players,
            "min_players": self.min_players,
            "player_count": len(self.players),
            "ready_count": self.get_ready_count(),
            "can_start": self.can_start(),
            "game_started": self.game_started,
            "ai_count": self.ai_count,
            "ai_difficulties": self.ai_difficulties,
            "ai_names": self.ai_names
        }
        
        # Add brawler-specific fields if it's a brawler game
        if self.game_type == GameType.BRAWLER:
            result["team_assignments"] = self.team_assignments
            result["character_selections"] = self.character_selections
        
        return result


class RoomManager:
    """Manages all game rooms"""
    
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.player_rooms: Dict[int, str] = {}  # Map player_id to room_code
        self._next_player_id = 1
        self._lock = asyncio.Lock()
    
    async def create_room(self, host_websocket, host_name: str, 
                          game_type: GameType = GameType.SNAKE_CLASSIC,
                          game_mode: GameMode = GameMode.SURVIVAL) -> tuple[Room, Player]:
        """Create a new room and return it with the host player"""
        async with self._lock:
            # Generate unique room code
            code = generate_room_code()
            while code in self.rooms:
                code = generate_room_code()
            
            # Create host player
            player = Player(
                id=self._next_player_id,
                name=host_name,
                websocket=host_websocket,
                state=PlayerState.WAITING
            )
            self._next_player_id += 1
            
            # Create room
            room = Room(
                code=code,
                host_id=player.id,
                game_type=game_type,
                game_mode=game_mode
            )
            room.add_player(player)
            
            self.rooms[code] = room
            self.player_rooms[player.id] = code
            
            return room, player
    
    async def join_room(self, code: str, websocket, player_name: str) -> tuple[Optional[Room], Optional[Player], str]:
        """Join an existing room. Returns (room, player, error_message)"""
        async with self._lock:
            code = code.upper()
            
            if code not in self.rooms:
                return None, None, "Room not found"
            
            room = self.rooms[code]
            
            if room.game_started:
                return None, None, "Game already started"
            
            if len(room.players) >= room.max_players:
                return None, None, "Room is full"
            
            # Create player
            player = Player(
                id=self._next_player_id,
                name=player_name,
                websocket=websocket,
                state=PlayerState.WAITING
            )
            self._next_player_id += 1
            
            room.add_player(player)
            self.player_rooms[player.id] = code
            
            return room, player, ""
    
    async def leave_room(self, player_id: int) -> Optional[Room]:
        """Remove a player from their room"""
        async with self._lock:
            if player_id not in self.player_rooms:
                return None
            
            code = self.player_rooms.pop(player_id)
            if code not in self.rooms:
                return None
            
            room = self.rooms[code]
            room.remove_player(player_id)
            
            # Delete empty rooms or transfer host
            if len(room.players) == 0:
                del self.rooms[code]
                return None
            elif room.host_id == player_id:
                # Transfer host to next player
                room.host_id = next(iter(room.players.keys()))
            
            return room
    
    def get_room(self, code: str) -> Optional[Room]:
        """Get a room by code"""
        return self.rooms.get(code.upper())
    
    def get_player_room(self, player_id: int) -> Optional[Room]:
        """Get the room a player is in"""
        if player_id not in self.player_rooms:
            return None
        return self.rooms.get(self.player_rooms[player_id])
    
    def get_all_rooms(self) -> List[Room]:
        """Get all active rooms"""
        return list(self.rooms.values())
    
    async def set_player_ready(self, player_id: int, ready: bool) -> Optional[Room]:
        """Set a player's ready state"""
        room = self.get_player_room(player_id)
        if room and player_id in room.players:
            room.players[player_id].state = PlayerState.READY if ready else PlayerState.WAITING
            return room
        return None
    
    async def set_game_settings(self, player_id: int, game_type: Optional[GameType] = None,
                                 game_mode: Optional[GameMode] = None,
                                 barrier_density: Optional[str] = None,
                                 map_size: Optional[str] = None,
                                 time_limit: Optional[str] = None,
                                 ai_count: Optional[int] = None,
                                 ai_difficulties: Optional[List[str]] = None,
                                 ai_names: Optional[List[str]] = None) -> Optional[Room]:
        """Host can change game settings"""
        room = self.get_player_room(player_id)
        if room and room.host_id == player_id and not room.game_started:
            if game_type:
                room.game_type = game_type
            if game_mode:
                room.game_mode = game_mode
            if barrier_density and barrier_density in ["none", "sparse", "moderate", "dense"]:
                room.barrier_density = barrier_density
            if map_size and map_size in ["small", "medium", "large", "extra_large"]:
                room.map_size = map_size
            if time_limit and time_limit in ["30s", "1m", "2m", "3m"]:
                room.time_limit = time_limit
            if ai_count is not None and 0 <= ai_count <= 3:
                room.ai_count = ai_count
            if ai_difficulties is not None and isinstance(ai_difficulties, list):
                valid = ["amateur", "semi_pro", "pro", "world_class"]
                room.ai_difficulties = [d if d in valid else "amateur" for d in ai_difficulties]
            if ai_names is not None and isinstance(ai_names, list):
                room.ai_names = [str(n)[:16] for n in ai_names]
            return room
        return None
