# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-02-10

### Added

#### Web Multiplayer
- Browser-based multiplayer Snake games accessible via local network
- Support for 2-4 players in local network multiplayer
- Modern PixiJS-powered graphics with smooth animations
- Three game modes:
  - **Single Player**: Practice mode with no time limit, score-based speed increase
  - **Survival Mode**: Last snake standing wins, arena shrinks every 30 seconds
  - **High Score Mode**: 3-minute matches, highest score wins, combo system
- Quadrant-based gameplay - each player has their own arena section
- Room-based lobby system with room codes (e.g., SNAKE-XXXX)
- Real-time game state synchronization via WebSockets
- In-lobby chat system
- Host controls for game type, mode, and barrier settings
- Ready-up system before game starts

#### Barriers/Walls System
- Four barrier density options:
  - **None**: Classic mode - no obstacles
  - **Sparse**: Few scattered walls
  - **Moderate**: Strategic wall placement
  - **Dense**: Maze-like challenge
- Score multipliers based on barrier difficulty (1x to 2x)
- Brick-textured wall rendering with mortar details

#### Enhanced Animal System (Web)
- 20+ animal types with unique appearances
- Four size categories:
  - **Small** (1 cell): Mouse, Frog, Bug, Cricket, Worm, Butterfly, Spider, Bee, Ladybug
  - **Medium** (2-3 cells): Rabbit, Fish, Lizard, Turtle, Duck
  - **Large** (4-5 cells): Bird, Fox, Wolf, Deer, Pig
  - **Huge** (6-8 cells): Tiger, Lion, Bear, Crocodile, Hippo, Elephant
- Multi-cell animals with proper collision detection
- Health bars for multi-hit animals
- Detailed sprite rendering with eyes, ears, patterns, and animations

#### Improved Snake Graphics
- Realistic snake head with eyes, pupils, and highlights
- Flickering forked tongue animation
- Gradient body coloring (brighter at head)
- Scale pattern on body segments
- Tapered tail rendering
- Direction-aware eye placement

#### Web Client Features
- Responsive modern UI with glassmorphism effects
- Single Player quick-start button
- Barrier density selector in lobby
- Synthesized sound effects (eat, death, countdown, victory)
- Particle effects for eating food and deaths
- Countdown animation before game start
- Live scoreboard with player colors
- Timer display (count-up for survival/single, countdown for high score)
- Game over screen with rankings and final scores

#### Snake 3D (Web)
- Stardew Valley-style oblique 2.5D rendering
- Checkerboard grass pattern
- 3D depth effects on snakes and food
- Shadow rendering
- Highlight effects on food

### Technical
- FastAPI WebSocket server with room management
- JSON-based message protocol for client-server communication
- PixiJS 7.x for WebGL-accelerated rendering
- Modular JavaScript architecture with ES6 modules
- Web Audio API for synthesized sound effects
- CSS animations and transitions for UI polish
- Multi-cell food spawning with collision avoidance
- Wall generation algorithms for different density patterns

### How to Run
1. Install dependencies: `pip install fastapi uvicorn websockets`
2. Start server: `python -m web.server.main`
3. Open browser to displayed URL (localhost:8000 or network IP)
4. Share network URL with friends on same WiFi

---

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

[0.2.0]: https://github.com/username/project/releases/tag/v0.2.0
[0.1.0]: https://github.com/username/project/releases/tag/v0.1.0
