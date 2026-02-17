# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-17

### Added

#### Game Launcher
- Main game launcher with menu to select between different games
- Support for Snake Classic, Snake 3D, and Brawler games

#### Snake Classic
- Classic 2D snake gameplay with sandbox and story modes
- Player profile system with persistent leaderboards
- Multiple map sizes (Small, Medium, Large)
- Barrier/obstacle options (None, Low, Medium, High)
- Expanded animal food system with 15+ animal types
- Multi-cell animals (up to 8 cells) requiring multiple hits to eat
- Health bar display for large animals
- Kids Mode with 30% slower speed and 50% score adjustment
- Pause functionality (P key) - games start paused
- Profile management with delete confirmation

#### Snake 3D
- Stardew Valley-style oblique 3D perspective
- Same gameplay features as Snake Classic
- Enhanced visual depth with front-face rendering
- Warm, organic color palette

#### Brawler (New Game)
- 2v2 Brawl Ball arena game mode
- 4 unique brawlers with distinct abilities:
  - **Colt**: Long-range 6-bullet burst, piercing super
  - **Shelly**: Wide spread pellets, knockback super
  - **Piper**: Sniper with distance-scaling damage, escape jump super
  - **Edgar**: Melee assassin with lifesteal, vault jump super
- Two game modes: 2-Player Local and Player vs AI
- AI bot system with state-based behavior (chase, attack, defend, score)
- Ball physics with kicking, carrying, and goal detection
- Projectile system with bullets, pellets, and melee attacks
- Health bars, ammo system, and super ability meters
- 2-minute matches, first to 2 goals wins
- Character selection screen with game controls display
- Respawn system with invincibility frames

### Technical
- Modular codebase with separate packages for each game
- Pygame-based rendering with isometric/oblique projection support
- JSON-based player profile storage
- Centralized asset management per game

---

[0.1.0]: https://github.com/username/project/releases/tag/v0.1.0
