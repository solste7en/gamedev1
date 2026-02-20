"""
Player profile manager — tracks per-player game statistics.
Profiles are persisted in data/profiles.json and updated server-side
after every game so they cannot be spoofed by clients.
"""

import json
import os
import threading
from datetime import datetime
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict, field


MODES = ["survival", "high_score", "battle_royale", "single_player", "duel"]

AI_LEVELS = ["amateur", "semi_pro", "pro", "world_class"]


@dataclass
class PlayerProfile:
    player_name: str
    registered_at: str
    # Lifetime totals
    total_games: int = 0
    total_wins: int = 0
    # Per-mode breakdowns
    games_by_mode: Dict[str, int] = field(default_factory=lambda: {m: 0 for m in MODES})
    wins_by_mode: Dict[str, int]  = field(default_factory=lambda: {m: 0 for m in MODES})
    highest_score_by_mode: Dict[str, int] = field(default_factory=lambda: {m: 0 for m in MODES})
    # AI-only subset
    games_vs_ai_only: int = 0
    wins_vs_ai_only: int = 0
    # Duel-specific stats
    duel_vs_human: Dict[str, int] = field(default_factory=lambda: {"games": 0, "wins": 0})
    duel_vs_ai: Dict[str, Dict[str, int]] = field(
        default_factory=lambda: {lvl: {"games": 0, "wins": 0} for lvl in AI_LEVELS}
    )

    # ---- derived helpers (computed on the fly, not stored) ----
    def win_pct(self) -> float:
        return round(self.total_wins / self.total_games * 100, 1) if self.total_games else 0.0

    def win_pct_vs_humans(self) -> float:
        human_games = self.total_games - self.games_vs_ai_only
        human_wins  = self.total_wins  - self.wins_vs_ai_only
        return round(human_wins / human_games * 100, 1) if human_games > 0 else 0.0

    def to_dict(self) -> dict:
        d = asdict(self)
        d["win_pct"] = self.win_pct()
        d["win_pct_vs_humans"] = self.win_pct_vs_humans()
        d["games_vs_humans"] = self.total_games - self.games_vs_ai_only
        d["wins_vs_humans"]  = self.total_wins  - self.wins_vs_ai_only
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "PlayerProfile":
        for key in ("games_by_mode", "wins_by_mode", "highest_score_by_mode"):
            for m in MODES:
                data.setdefault(key, {})[m] = data.get(key, {}).get(m, 0)
        # Ensure duel sub-dicts exist
        data.setdefault("duel_vs_human", {"games": 0, "wins": 0})
        duel_ai = data.setdefault("duel_vs_ai", {})
        for lvl in AI_LEVELS:
            duel_ai.setdefault(lvl, {"games": 0, "wins": 0})
        for computed in ("win_pct", "win_pct_vs_humans", "games_vs_humans", "wins_vs_humans"):
            data.pop(computed, None)
        import dataclasses
        valid_fields = {f.name for f in dataclasses.fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})


class ProfileManager:
    """Thread-safe file-backed player profile store."""

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
        self.data_dir = data_dir
        self.profiles_file = os.path.join(data_dir, 'profiles.json')
        self._lock = threading.Lock()
        os.makedirs(data_dir, exist_ok=True)
        self._profiles: Dict[str, PlayerProfile] = {}
        self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self):
        if os.path.exists(self.profiles_file):
            try:
                with open(self.profiles_file, 'r') as f:
                    raw = json.load(f)
                for name, data in raw.items():
                    try:
                        self._profiles[name] = PlayerProfile.from_dict(data)
                    except Exception:
                        pass
            except (json.JSONDecodeError, TypeError):
                self._profiles = {}

    def _save(self):
        with open(self.profiles_file, 'w') as f:
            json.dump(
                {name: p.to_dict() for name, p in self._profiles.items()},
                f, indent=2
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_profile(self, player_name: str) -> Optional[PlayerProfile]:
        with self._lock:
            return self._profiles.get(player_name)

    def ensure_profile(self, player_name: str) -> PlayerProfile:
        """Create a profile if it does not exist yet (registration)."""
        with self._lock:
            if player_name not in self._profiles:
                self._profiles[player_name] = PlayerProfile(
                    player_name=player_name,
                    registered_at=datetime.now().strftime('%Y-%m-%d'),
                )
                self._save()
            return self._profiles[player_name]

    def record_game(
        self,
        player_name: str,
        is_winner: bool,
        score: int,
        game_mode: str,
        vs_ai_only: bool,
    ):
        """Record a single game result for a human player."""
        if not player_name:
            return
        # Normalize mode key
        mode = game_mode if game_mode in MODES else "single_player"

        with self._lock:
            if player_name not in self._profiles:
                self._profiles[player_name] = PlayerProfile(
                    player_name=player_name,
                    registered_at=datetime.now().strftime('%Y-%m-%d'),
                )

            p = self._profiles[player_name]
            p.total_games += 1
            p.games_by_mode[mode] = p.games_by_mode.get(mode, 0) + 1

            if is_winner:
                p.total_wins += 1
                p.wins_by_mode[mode] = p.wins_by_mode.get(mode, 0) + 1

            if score > p.highest_score_by_mode.get(mode, 0):
                p.highest_score_by_mode[mode] = score

            if vs_ai_only:
                p.games_vs_ai_only += 1
                if is_winner:
                    p.wins_vs_ai_only += 1

            self._save()

    def record_duel(
        self,
        player_name: str,
        is_winner: bool,
        opponent_is_ai: bool,
        opponent_ai_level: Optional[str] = None,
    ):
        """Record a duel series result (called once per series, not per round)."""
        if not player_name:
            return
        with self._lock:
            if player_name not in self._profiles:
                self._profiles[player_name] = PlayerProfile(
                    player_name=player_name,
                    registered_at=datetime.now().strftime('%Y-%m-%d'),
                )
            p = self._profiles[player_name]
            if opponent_is_ai and opponent_ai_level:
                lvl = opponent_ai_level if opponent_ai_level in AI_LEVELS else "amateur"
                p.duel_vs_ai.setdefault(lvl, {"games": 0, "wins": 0})
                p.duel_vs_ai[lvl]["games"] += 1
                if is_winner:
                    p.duel_vs_ai[lvl]["wins"] += 1
            else:
                p.duel_vs_human["games"] += 1
                if is_winner:
                    p.duel_vs_human["wins"] += 1
            self._save()

    def reset_profile(self, player_name: str) -> bool:
        """Reset all stats for a player (preserves registration date, not leaderboard)."""
        with self._lock:
            if player_name not in self._profiles:
                return False
            reg_date = self._profiles[player_name].registered_at
            self._profiles[player_name] = PlayerProfile(
                player_name=player_name,
                registered_at=reg_date,
            )
            self._save()
            return True

    def get_all(self) -> List[dict]:
        with self._lock:
            return [p.to_dict() for p in self._profiles.values()]


# Singleton
_profile_manager: Optional[ProfileManager] = None


def get_profile_manager() -> ProfileManager:
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = ProfileManager()
    return _profile_manager
