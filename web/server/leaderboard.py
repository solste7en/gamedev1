"""
Leaderboard manager for storing and retrieving high scores
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import threading


@dataclass
class LeaderboardEntry:
    player_name: str
    score: int
    date: str  # YYYY-MM-DD format
    game_type: str  # snake_classic or snake_3d
    game_mode: str = "single_player"  # single_player, survival, high_score
    
    def to_dict(self) -> Dict:
        return asdict(self)


class LeaderboardManager:
    """Manages the leaderboard with file-based persistence"""
    
    MAX_ENTRIES = 20
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Default to a data directory in the project
            data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
        
        self.data_dir = data_dir
        self.leaderboard_file = os.path.join(data_dir, 'leaderboard.json')
        self._lock = threading.Lock()
        self._ensure_data_dir()
        self._load()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _load(self):
        """Load leaderboard from file"""
        self.entries: List[LeaderboardEntry] = []
        
        if os.path.exists(self.leaderboard_file):
            try:
                with open(self.leaderboard_file, 'r') as f:
                    data = json.load(f)
                    self.entries = [
                        LeaderboardEntry(**entry) for entry in data.get('entries', [])
                    ]
            except (json.JSONDecodeError, KeyError, TypeError):
                self.entries = []
    
    def _save(self):
        """Save leaderboard to file"""
        with open(self.leaderboard_file, 'w') as f:
            json.dump({
                'entries': [e.to_dict() for e in self.entries]
            }, f, indent=2)
    
    def _sort_entries(self):
        """Sort entries by score (desc), then by date (asc for tiebreaker - earlier is higher)"""
        self.entries.sort(key=lambda e: (-e.score, e.date))
    
    def add_score(self, player_name: str, score: int, game_type: str = "snake_classic", 
                   game_mode: str = "single_player") -> Optional[int]:
        """
        Add a score to the leaderboard.
        Returns the rank (1-indexed) if it made the leaderboard, None otherwise.
        """
        with self._lock:
            date = datetime.now().strftime('%Y-%m-%d')
            entry = LeaderboardEntry(
                player_name=player_name,
                score=score,
                date=date,
                game_type=game_type,
                game_mode=game_mode
            )
            
            # Add entry
            self.entries.append(entry)
            self._sort_entries()
            
            # Trim to max entries
            if len(self.entries) > self.MAX_ENTRIES:
                self.entries = self.entries[:self.MAX_ENTRIES]
            
            # Check if entry is still in the list
            try:
                rank = self.entries.index(entry) + 1
                self._save()
                return rank
            except ValueError:
                return None
    
    def get_leaderboard(self) -> List[Dict]:
        """Get the leaderboard as a list of dicts"""
        with self._lock:
            return [e.to_dict() for e in self.entries]
    
    def get_rank_for_score(self, score: int) -> int:
        """Get what rank a score would achieve (for preview)"""
        with self._lock:
            rank = 1
            for entry in self.entries:
                if entry.score > score:
                    rank += 1
                else:
                    break
            return rank


# Singleton instance
_leaderboard_manager: Optional[LeaderboardManager] = None


def get_leaderboard_manager() -> LeaderboardManager:
    """Get the singleton leaderboard manager"""
    global _leaderboard_manager
    if _leaderboard_manager is None:
        _leaderboard_manager = LeaderboardManager()
    return _leaderboard_manager
