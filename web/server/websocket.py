"""
WebSocket handlers for multiplayer game communication
"""

import json
import asyncio
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect

from .models import GameType, GameMode
from .room_manager import RoomManager, Room
from .game_manager import GameManager
from .brawler_game_manager import BrawlerGameManager
from .leaderboard import get_leaderboard_manager


class ConnectionManager:
    """Manages WebSocket connections and message routing"""
    
    def __init__(self):
        self.room_manager = RoomManager()
        self.active_connections: Dict[int, WebSocket] = {}  # player_id -> websocket
        self.game_managers: Dict[str, GameManager] = {}  # room_code -> snake game_manager
        self.brawler_game_managers: Dict[str, BrawlerGameManager] = {}  # room_code -> brawler game_manager
    
    async def connect(self, websocket: WebSocket) -> int:
        """Accept a new WebSocket connection"""
        await websocket.accept()
        return -1  # Temporary ID until they create/join a room
    
    async def disconnect(self, player_id: int):
        """Handle disconnection"""
        if player_id in self.active_connections:
            del self.active_connections[player_id]
        
        room = await self.room_manager.leave_room(player_id)
        if room:
            await self.broadcast_to_room(room.code, {
                "type": "player_left",
                "player_id": player_id,
                "room": room.to_dict()
            })
    
    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send message to a specific connection"""
        try:
            await websocket.send_json(message)
        except Exception:
            pass
    
    async def broadcast_to_room(self, room_code: str, message: dict):
        """Broadcast message to all players in a room"""
        room = self.room_manager.get_room(room_code)
        if not room:
            return
        
        for player in room.players.values():
            if player.websocket:
                try:
                    await player.websocket.send_json(message)
                except Exception:
                    pass
    
    async def handle_message(self, websocket: WebSocket, player_id: int, data: dict) -> int:
        """Handle incoming WebSocket message. Returns updated player_id."""
        msg_type = data.get("type")
        
        if msg_type == "create_room":
            return await self._handle_create_room(websocket, data)
        
        elif msg_type == "join_room":
            return await self._handle_join_room(websocket, data)
        
        elif msg_type == "leave_room":
            await self._handle_leave_room(player_id)
            return -1
        
        elif msg_type == "ready":
            await self._handle_ready(player_id, data)
        
        elif msg_type == "set_settings":
            await self._handle_set_settings(player_id, data)
        
        elif msg_type == "start_game":
            await self._handle_start_game(player_id)
        
        elif msg_type == "input":
            await self._handle_input(player_id, data)
        
        elif msg_type == "list_rooms":
            await self._handle_list_rooms(websocket)
        
        elif msg_type == "chat":
            await self._handle_chat(player_id, data)
        
        elif msg_type == "return_to_lobby":
            await self._handle_return_to_lobby(player_id)
        
        elif msg_type == "get_leaderboard":
            await self._handle_get_leaderboard(websocket)
        
        elif msg_type == "submit_score":
            await self._handle_submit_score(websocket, data)
        
        # Brawler-specific messages
        elif msg_type == "select_team":
            await self._handle_select_team(player_id, data)
        
        elif msg_type == "select_character":
            await self._handle_select_character(player_id, data)
        
        elif msg_type == "brawler_input":
            await self._handle_brawler_input(player_id, data)
        
        return player_id
    
    async def _handle_create_room(self, websocket: WebSocket, data: dict) -> int:
        """Create a new room"""
        player_name = data.get("player_name", "Player")
        game_type_str = data.get("game_type", "snake_classic")
        game_mode_str = data.get("game_mode", "survival")
        
        try:
            game_type = GameType(game_type_str)
        except ValueError:
            game_type = GameType.SNAKE_CLASSIC
        
        try:
            game_mode = GameMode(game_mode_str)
        except ValueError:
            game_mode = GameMode.SURVIVAL
        
        room, player = await self.room_manager.create_room(
            websocket, player_name, game_type, game_mode
        )
        
        self.active_connections[player.id] = websocket
        
        await self.send_personal(websocket, {
            "type": "room_created",
            "room": room.to_dict(),
            "player_id": player.id
        })
        
        return player.id
    
    async def _handle_join_room(self, websocket: WebSocket, data: dict) -> int:
        """Join an existing room"""
        room_code = data.get("room_code", "")
        player_name = data.get("player_name", "Player")
        
        room, player, error = await self.room_manager.join_room(
            room_code, websocket, player_name
        )
        
        if error:
            await self.send_personal(websocket, {
                "type": "error",
                "message": error
            })
            return -1
        
        self.active_connections[player.id] = websocket
        
        # Notify joining player
        await self.send_personal(websocket, {
            "type": "room_joined",
            "room": room.to_dict(),
            "player_id": player.id
        })
        
        # Notify other players
        await self.broadcast_to_room(room.code, {
            "type": "player_joined",
            "player": player.to_dict(),
            "room": room.to_dict()
        })
        
        return player.id
    
    async def _handle_leave_room(self, player_id: int):
        """Leave current room"""
        # Grab websocket before removing from room
        ws = self.active_connections.get(player_id)
        
        room = await self.room_manager.leave_room(player_id)
        if room:
            await self.broadcast_to_room(room.code, {
                "type": "player_left",
                "player_id": player_id,
                "room": room.to_dict()
            })
        
        # Notify the leaving player to go back to the main menu
        if ws:
            await self.send_personal(ws, {"type": "room_left"})
    
    async def _handle_ready(self, player_id: int, data: dict):
        """Toggle ready state"""
        ready = data.get("ready", True)
        room = await self.room_manager.set_player_ready(player_id, ready)
        
        if room:
            await self.broadcast_to_room(room.code, {
                "type": "player_ready",
                "player_id": player_id,
                "ready": ready,
                "room": room.to_dict()
            })
    
    async def _handle_set_settings(self, player_id: int, data: dict):
        """Host changes game settings"""
        game_type = None
        game_mode = None
        barrier_density = None
        map_size = None
        time_limit = None
        ai_count = None
        ai_difficulties = None
        ai_names = None
        
        if "game_type" in data:
            try:
                game_type = GameType(data["game_type"])
            except ValueError:
                pass
        
        if "game_mode" in data:
            try:
                game_mode = GameMode(data["game_mode"])
            except ValueError:
                pass
        
        if "barrier_density" in data:
            barrier_density = data["barrier_density"]
        
        if "map_size" in data:
            map_size = data["map_size"]
        
        if "time_limit" in data:
            time_limit = data["time_limit"]
        
        if "ai_count" in data:
            ai_count = data["ai_count"]
        
        if "ai_difficulties" in data:
            ai_difficulties = data["ai_difficulties"]
        
        ai_names = data.get("ai_names", None)
        
        room = await self.room_manager.set_game_settings(
            player_id, game_type, game_mode, barrier_density, map_size, time_limit,
            ai_count, ai_difficulties, ai_names
        )
        
        if room:
            await self.broadcast_to_room(room.code, {
                "type": "settings_changed",
                "room": room.to_dict()
            })
    
    async def _handle_start_game(self, player_id: int):
        """Start the game"""
        room = self.room_manager.get_player_room(player_id)
        
        if not room:
            return
        
        if room.host_id != player_id:
            ws = self.active_connections.get(player_id)
            if ws:
                await self.send_personal(ws, {
                    "type": "error",
                    "message": "Only host can start the game"
                })
            return
        
        if not room.can_start():
            ws = self.active_connections.get(player_id)
            if ws:
                await self.send_personal(ws, {
                    "type": "error",
                    "message": "Not all players are ready"
                })
            return
        
        room.game_started = True
        
        # Create game manager based on game type
        async def broadcast_callback(message):
            await self.broadcast_to_room(room.code, message)
        
        if room.game_type == GameType.BRAWLER:
            # Brawler game
            game_manager = BrawlerGameManager(room, broadcast_callback)
            self.brawler_game_managers[room.code] = game_manager
            
            # Notify players game is starting
            await self.broadcast_to_room(room.code, {
                "type": "brawler_game_starting",
                "countdown": 3
            })
            
            # Countdown
            await asyncio.sleep(3)
            
            # Start brawler game
            game_manager.start()
        else:
            # Snake game
            game_manager = GameManager(room, broadcast_callback)
            self.game_managers[room.code] = game_manager
            
            # Notify players game is starting
            await self.broadcast_to_room(room.code, {
                "type": "game_starting",
                "countdown": 3
            })
            
            # Countdown
            await asyncio.sleep(3)
            
            # Start game
            game_manager.start()
    
    async def _handle_input(self, player_id: int, data: dict):
        """Handle player input"""
        room = self.room_manager.get_player_room(player_id)
        if not room:
            return
        
        game_manager = self.game_managers.get(room.code)
        if not game_manager:
            return
        
        direction = data.get("direction")
        if direction:
            game_manager.handle_input(player_id, direction)
    
    async def _handle_list_rooms(self, websocket: WebSocket):
        """List available rooms"""
        rooms = self.room_manager.get_all_rooms()
        available = [r.to_dict() for r in rooms if not r.game_started]
        
        await self.send_personal(websocket, {
            "type": "room_list",
            "rooms": available
        })
    
    async def _handle_chat(self, player_id: int, data: dict):
        """Handle chat message"""
        room = self.room_manager.get_player_room(player_id)
        if not room:
            return
        
        message = data.get("message", "")[:200]  # Limit length
        player = room.get_player(player_id)
        
        if player and message:
            await self.broadcast_to_room(room.code, {
                "type": "chat",
                "player_id": player_id,
                "player_name": player.name,
                "message": message
            })
    
    async def _handle_return_to_lobby(self, player_id: int):
        """Handle player returning to lobby after game over"""
        room = self.room_manager.get_player_room(player_id)
        if not room:
            return
        
        # Clean up snake game manager if exists
        if room.code in self.game_managers:
            game_manager = self.game_managers[room.code]
            game_manager.stop()
            del self.game_managers[room.code]
        
        # Clean up brawler game manager if exists
        if room.code in self.brawler_game_managers:
            game_manager = self.brawler_game_managers[room.code]
            game_manager.stop()
            del self.brawler_game_managers[room.code]
        
        # Reset room state for rematch
        room.reset_for_rematch()
        
        # Notify all players in room
        await self.broadcast_to_room(room.code, {
            "type": "room_reset",
            "room": room.to_dict()
        })
    
    async def _handle_get_leaderboard(self, websocket: WebSocket):
        """Get the leaderboard"""
        leaderboard = get_leaderboard_manager()
        await self.send_personal(websocket, {
            "type": "leaderboard",
            "entries": leaderboard.get_leaderboard()
        })
    
    async def _handle_submit_score(self, websocket: WebSocket, data: dict):
        """Submit a score to the leaderboard"""
        player_name = data.get("player_name", "Unknown")
        score = data.get("score", 0)
        game_type = data.get("game_type", "snake_classic")
        game_mode = data.get("game_mode", "single_player")
        
        if score <= 0:
            return
        
        leaderboard = get_leaderboard_manager()
        rank = leaderboard.add_score(player_name, score, game_type, game_mode)
        
        await self.send_personal(websocket, {
            "type": "score_submitted",
            "rank": rank,  # None if didn't make leaderboard
            "leaderboard": leaderboard.get_leaderboard()
        })
    
    # Brawler-specific handlers
    
    async def _handle_select_team(self, player_id: int, data: dict):
        """Handle player team selection for Brawler"""
        room = self.room_manager.get_player_room(player_id)
        if not room or room.game_type != GameType.BRAWLER:
            return
        
        team = data.get("team", 0)  # 0 = blue, 1 = red
        if team not in [0, 1]:
            return
        
        # Count players on each team
        blue_count = sum(1 for t in room.team_assignments.values() if t == 0)
        red_count = sum(1 for t in room.team_assignments.values() if t == 1)
        
        # Check if team is full (max 2 per team)
        if team == 0 and blue_count >= 2:
            ws = self.active_connections.get(player_id)
            if ws:
                await self.send_personal(ws, {
                    "type": "error",
                    "message": "Blue team is full"
                })
            return
        
        if team == 1 and red_count >= 2:
            ws = self.active_connections.get(player_id)
            if ws:
                await self.send_personal(ws, {
                    "type": "error",
                    "message": "Red team is full"
                })
            return
        
        room.team_assignments[player_id] = team
        
        await self.broadcast_to_room(room.code, {
            "type": "team_selected",
            "player_id": player_id,
            "team": team,
            "room": room.to_dict()
        })
    
    async def _handle_select_character(self, player_id: int, data: dict):
        """Handle player character selection for Brawler"""
        room = self.room_manager.get_player_room(player_id)
        if not room or room.game_type != GameType.BRAWLER:
            return
        
        character = data.get("character", "colt")
        valid_chars = ["colt", "shelly", "piper", "edgar"]
        
        if character not in valid_chars:
            return
        
        # Check if character is already taken on this team
        player_team = room.team_assignments.get(player_id, 0)
        for pid, char in room.character_selections.items():
            if pid != player_id and char == character:
                other_team = room.team_assignments.get(pid, 0)
                if other_team == player_team:
                    ws = self.active_connections.get(player_id)
                    if ws:
                        await self.send_personal(ws, {
                            "type": "error",
                            "message": f"{character.capitalize()} is already taken on your team"
                        })
                    return
        
        room.character_selections[player_id] = character
        
        await self.broadcast_to_room(room.code, {
            "type": "character_selected",
            "player_id": player_id,
            "character": character,
            "room": room.to_dict()
        })
    
    async def _handle_brawler_input(self, player_id: int, data: dict):
        """Handle player input for Brawler game"""
        room = self.room_manager.get_player_room(player_id)
        if not room:
            return
        
        game_manager = self.brawler_game_managers.get(room.code)
        if not game_manager:
            return
        
        action = data.get("action")  # move, aim, attack, ability
        if action:
            game_manager.handle_input(player_id, action, data)


# Singleton connection manager
connection_manager = ConnectionManager()
