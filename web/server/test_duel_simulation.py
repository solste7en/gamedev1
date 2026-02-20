#!/usr/bin/env python3
"""
Duel Mode Simulation Script
Runs multiple automated duel games to identify potential bugs.
"""

import asyncio
import sys
import os
import time
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.models import GameState, GameMode, GameType, Player, PlayerState, Direction
from server.game_manager import GameManager
from server.room_manager import Room, RoomManager


@dataclass
class SimulationResult:
    """Results from a single game simulation."""
    round_number: int
    elapsed_time: float
    winner_id: Optional[int]
    player1_alive: bool
    player2_alive: bool
    player1_score: int
    player2_score: int
    player1_length: int
    player2_length: int
    end_reason: str
    
    
class DuelSimulator:
    """Simulates duel games to identify bugs."""
    
    def __init__(self):
        self.results: List[SimulationResult] = []
        self.anomalies: List[str] = []
        
    def create_mock_room(self, series_length: int = 3, human_vs_ai: bool = True) -> Room:
        """Create a mock room for testing.
        
        Args:
            series_length: Best of N games (3, 5, or 7)
            human_vs_ai: If True, creates 1 human + 1 AI. If False, creates 2 AI players.
        """
        room = Room(
            code="TEST",
            host_id=1,
            game_type=GameType.SNAKE_CLASSIC,
            game_mode=GameMode.DUEL
        )
        room.series_length = series_length
        room.map_size = "medium"
        room.barrier_density = "none"
        
        if human_vs_ai:
            # Simulate human vs AI (1 human player + 1 AI from ai_count)
            player1 = Player(id=1, name="HumanPlayer")
            player1.is_ai = True  # Simulate AI behavior for testing
            player1.ai_difficulty = "world_class"
            room.players[1] = player1
            room.ai_count = 1  # One additional AI opponent
            room.ai_difficulties = ["world_class"]
            room.ai_names = ["TestAI"]
        else:
            # Two AI players in the room (no additional AI from ai_count)
            player1 = Player(id=1, name="TestAI1")
            player1.is_ai = True
            player1.ai_difficulty = "world_class"
            player2 = Player(id=2, name="TestAI2")
            player2.is_ai = True
            player2.ai_difficulty = "world_class"
            room.players[1] = player1
            room.players[2] = player2
            room.ai_count = 0  # No additional AI
            room.ai_difficulties = []
            room.ai_names = []
        
        return room
        
    def run_single_round(self, game_manager: GameManager, max_ticks: int = 10000, debug: bool = False) -> SimulationResult:
        """Run a single round and return results.
        
        Uses the same timing logic as the actual game loop to accurately simulate games.
        """
        tick_rate = 1/30  # 30 FPS
        move_accumulator = 0.0
        ticks = 0
        
        if debug:
            # Print initial state including quadrant bounds
            print(f"\n--- Initial State ---")
            print(f"  Grid size: {game_manager.state.grid_width}x{game_manager.state.grid_height}")
            print(f"  Mode: {game_manager.state.mode.value}, Time limit: {game_manager.state.time_limit}s")
            print(f"  Current speed: {game_manager.state.current_speed}ms per move")
            for q, bounds in game_manager.state.quadrant_bounds.items():
                print(f"  Quadrant {q} bounds: x=[{bounds.x_min}, {bounds.x_max}), y=[{bounds.y_min}, {bounds.y_max})")
                foods = game_manager.state.foods.get(q, [])
                print(f"    Food in quadrant {q}: {len(foods)}")
                for f in foods:
                    print(f"      - {f.food_type} at ({f.position.x}, {f.position.y}), value={f.value}")
            for pid, p in game_manager.state.players.items():
                if p.snake:
                    print(f"  Player {pid}: head={p.snake.body[0] if p.snake.body else 'N/A'}, "
                          f"dir={p.snake.direction.value if p.snake.direction else 'N/A'}, "
                          f"quadrant={p.quadrant}, body_len={len(p.snake.body) if p.snake.body else 0}")
        
        while game_manager.state.running and not game_manager.state.game_over and ticks < max_ticks:
            # Accumulate time in milliseconds (like actual game loop)
            move_accumulator += tick_rate * 1000
            
            # Only move snakes when enough time has accumulated
            while move_accumulator >= game_manager.state.current_speed:
                game_manager.update(game_manager.state.current_speed / 1000)
                move_accumulator -= game_manager.state.current_speed
                
                if debug and game_manager.state.elapsed_time <= 5.0:
                    for pid, p in game_manager.state.players.items():
                        if p.snake and not p.snake.alive:
                            print(f"  Elapsed {game_manager.state.elapsed_time:.2f}s: Player {pid} DIED")
                            if p.snake.body:
                                print(f"    Last head position: {p.snake.body[0]}")
            
            ticks += 1
            
        # Determine end reason
        if ticks >= max_ticks:
            end_reason = "max_ticks_reached"
        elif game_manager.state.elapsed_time >= game_manager.state.time_limit:
            end_reason = "time_limit"
        elif game_manager.state.alive_count <= 1:
            end_reason = "player_death"
        else:
            end_reason = "unknown"
            
        # Get player states
        players = list(game_manager.state.players.values())
        p1 = players[0] if len(players) > 0 else None
        p2 = players[1] if len(players) > 1 else None
        
        return SimulationResult(
            round_number=game_manager.state.current_round,
            elapsed_time=game_manager.state.elapsed_time,
            winner_id=game_manager.state.winner_id,
            player1_alive=p1.snake.alive if p1 and p1.snake else False,
            player2_alive=p2.snake.alive if p2 and p2.snake else False,
            player1_score=p1.snake.score if p1 and p1.snake else 0,
            player2_score=p2.snake.score if p2 and p2.snake else 0,
            player1_length=len(p1.snake.body) if p1 and p1.snake and p1.snake.body else 0,
            player2_length=len(p2.snake.body) if p2 and p2.snake and p2.snake.body else 0,
            end_reason=end_reason
        )
        
    def check_anomalies(self, result: SimulationResult, game_manager: GameManager = None) -> List[str]:
        """Check for anomalies in game result."""
        anomalies = []
        
        # Check 1: Game ended but both players alive and time not reached
        if result.player1_alive and result.player2_alive:
            if result.elapsed_time < 150 and result.end_reason != "time_limit":
                anomalies.append(f"Round {result.round_number}: Game ended at {result.elapsed_time:.1f}s with both players alive (reason: {result.end_reason})")
                
        # Check 2: Both players dead (draw scenario - should be handled)
        if not result.player1_alive and not result.player2_alive:
            anomalies.append(f"Round {result.round_number}: Both players dead at {result.elapsed_time:.1f}s")
            
        # Check 3: Game ended instantly (before spawn freeze ended - definite bug)
        if result.elapsed_time < 1.0:
            anomalies.append(f"Round {result.round_number}: BUG - Game ended before spawn freeze ({result.elapsed_time:.1f}s)")
            
        return anomalies
        
    async def noop_broadcast(self, data):
        """No-op broadcast callback for testing."""
        pass
        
    def run_simulation(self, num_games: int = 100, series_length: int = 3) -> Dict:
        """Run multiple game simulations."""
        print(f"Running {num_games} duel simulations (Best of {series_length})...")
        print("=" * 60)
        
        stats = defaultdict(int)
        
        for game_num in range(num_games):
            # Create fresh room and game manager (human_vs_ai=True simulates typical duel)
            room = self.create_mock_room(series_length, human_vs_ai=True)
            game_manager = GameManager(room, self.noop_broadcast)
            game_manager.setup_game()
            
            # Run the round (debug first game only)
            result = self.run_single_round(game_manager, debug=(game_num == 0))
            self.results.append(result)
            
            # Check for anomalies
            anomalies = self.check_anomalies(result, game_manager)
            self.anomalies.extend(anomalies)
            
            # Track stats
            stats["total_rounds"] += 1
            stats[f"end_reason_{result.end_reason}"] += 1
            
            if result.player1_alive and result.player2_alive:
                stats["both_alive_at_end"] += 1
            elif not result.player1_alive and not result.player2_alive:
                stats["both_dead_at_end"] += 1
                
            # Progress indicator
            if (game_num + 1) % 10 == 0:
                print(f"  Completed {game_num + 1}/{num_games} games...")
                
        return dict(stats)
        
    def print_report(self):
        """Print simulation report."""
        print("\n" + "=" * 60)
        print("SIMULATION REPORT")
        print("=" * 60)
        
        # Anomalies
        print(f"\nAnomalies Found: {len(self.anomalies)}")
        if self.anomalies:
            print("-" * 40)
            for anomaly in self.anomalies[:20]:  # Show first 20
                print(f"  • {anomaly}")
            if len(self.anomalies) > 20:
                print(f"  ... and {len(self.anomalies) - 20} more")
                
        # Statistics
        if self.results:
            times = [r.elapsed_time for r in self.results]
            print(f"\nGame Duration Statistics:")
            print(f"  Min: {min(times):.1f}s")
            print(f"  Max: {max(times):.1f}s")
            print(f"  Avg: {sum(times)/len(times):.1f}s")
            
            # End reasons
            reasons = defaultdict(int)
            for r in self.results:
                reasons[r.end_reason] += 1
            print(f"\nEnd Reasons:")
            for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
                print(f"  {reason}: {count} ({100*count/len(self.results):.1f}%)")


def main():
    """Main entry point."""
    print("Snake Duel Mode Simulation")
    print("=" * 60)
    
    simulator = DuelSimulator()
    
    # Run simulations
    stats = simulator.run_simulation(num_games=100, series_length=3)
    
    # Print report
    simulator.print_report()
    
    print("\n" + "=" * 60)
    print("Raw Stats:", stats)
    
    # Return exit code based on anomalies
    return 0 if len(simulator.anomalies) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
