# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2026-02-10

### Added
- **Map size overhaul**: all four sizes scaled up — Small (25×18), Medium (35×22, new default), Large (45×28), Extra Large (60×36)
- **Focused layout for large maps**: in multiplayer with Large or Extra Large maps, the viewport centers on each player's own quadrant; other players' areas remain partially visible at the edges
- **Leaderboard top-500** with pagination (50 entries per page) and expanded color tiers for top 3, 10, 30, 50, and 100
- **Leaderboard unique-player filter**: checkbox to show only each player's personal best
- **Fibonacci respawn penalty** in High Score mode — each death adds progressively longer respawn delay (2s, 3s, 5s, 8s, 13s, 21s…)
- **Hybrid scoring system**: small animals now yield significantly more points; medium/large/huge animals distribute score across multiple hits with non-consecutive hit enforcement (hit-recovery windows of 0.8s / 1.5s / 2.5s); combo bonus applies on the killing hit

### Changed
- Survival mode speed multiplier now correctly resets to 1× on every new game
- AI bots improved: stronger at all levels, Pro and World-Class use flood-fill dead-end avoidance, `value_power`, and combo-aware food targeting for more consistent play
- Countdown overlay is semi-transparent so the game map and player positions are visible before the game begins
- AI difficulty badge restyled as a labeled interactive button (↻ Level: …) to make it more obvious it can be toggled

### Fixed
- Ready button no longer stops working after a game ends; state is now synced from the server on every room update
- AI bot name input no longer resets cursor position on each keystroke (focus and selection range preserved across re-renders)
- Speed multiplier no longer carries over from a previous Survival game session
- Game display no longer shows a gray screen when entering a solo Survival game

---

## [0.3.0] - 2026-02-05

### Added

#### Web Brawler Multiplayer
- Browser-based Brawler game accessible via local network
- Support for 1–4 players with AI filling empty slots
- 2v2 Team-based gameplay (Blue vs Red)
- Team selection UI with player counts
- Character selection with unique brawler abilities:
  - **Colt**: Long-range 6-bullet burst, piercing super
  - **Shelly**: Wide spread pellets, knockback super
  - **Piper**: Sniper with distance-scaling damage, escape jump super
  - **Edgar**: Melee assassin with lifesteal, vault jump super
- Each player must select a unique character on their team
- AI companions automatically fill remaining team slots
- Full game mechanics: ball pickup and kick, goal scoring with celebration screen, 2-minute match timer with overtime, first to 2 goals wins, projectile system and damage, health bars and respawning
- WASD movement + mouse aiming controls; left-click attack, E / right-click for ability

#### Game Selection Hub
- New unified home page for Snake and Brawler games
- Game selection buttons to toggle between game types
- Clear labeling that the leaderboard is Snake-only

### Changed
- Removed Snake 3D from web game list (temporary)
- Updated UI to show "Game Hub" branding

### Technical
- BrawlerGameManager with 60 FPS game loop
- AI state machine: chase, attack, defend, score, retreat, support
- Team and character selection via WebSocket messages
- Brawler-specific lobby with team/character UI
- BrawlerGame.js with PixiJS rendering

---

## [0.2.0] - 2026-01-15

### Added

#### Browser-Based Snake
- Snake game playable in any browser, accessible across a local network
- Support for 2–4 human players plus AI bots with individually configurable skill levels (Amateur, Semi-Pro, Pro, World-Class)
- Modern PixiJS-powered graphics with smooth animations
- Three game modes:
  - **Survival Mode**: last snake standing; arena shrinks, speed ramps up over time, tail decay if not eating
  - **High Score Mode**: timed match, highest score wins, combo system
- Quadrant-based gameplay — each player has their own arena section
- Room-based lobby with room codes (e.g., SNAKE-XXXX)
- Real-time game state synchronisation via WebSockets
- In-lobby chat
- Host controls for game mode, map size, and barrier density
- Ready-up system

#### Barriers / Walls System
- Four barrier density options: None, Sparse, Moderate, Dense
- Randomised layout each game
- Score multipliers based on barrier difficulty (1× to 2×)
- Brick-textured wall rendering

#### Animal System
- 20+ animal types across four size categories
- Small (1 cell): Mouse, Frog, Bug, Cricket, Worm, Butterfly, Spider, Bee, Ladybug
- Medium (2–3 cells): Rabbit, Fish, Lizard, Turtle, Duck
- Large (4–5 cells): Bird, Fox, Wolf, Deer, Pig
- Huge (6–8 cells): Tiger, Lion, Bear, Crocodile, Hippo, Elephant
- Multi-cell animals with collision detection and health bars
- Per-animal colour palette with distinct rendering so each is identifiable
- On-screen legend mapping animal name to colour/shape

#### Snake Graphics
- Realistic snake head with eyes, pupils, and highlights
- Flickering forked tongue animation
- Gradient body with scale pattern
- Tapered tail rendering

#### Survival Mode Mechanics
- Tail decay pressure: snake loses one segment every few seconds; interval shortens as the game progresses; eating food resets the decay timer; death if length drops below 3
- Speed ramp: global move speed increases every 15 seconds, capped at 2× base speed
- Hunger bar and speed-multiplier indicator in the HUD

#### Other Client Features
- Responsive UI with glassmorphism effects
- Single-player quick-start button (no room code needed)
- Synthesised sound effects (eat, death, countdown, victory)
- Particle effects for eating and death events
- Live scoreboard with player colours
- Timer (count-up for Survival, countdown for High Score)
- Game-over screen with final rankings

### Technical
- FastAPI WebSocket server with room management
- JSON message protocol for client–server communication
- PixiJS 7.x for WebGL-accelerated rendering
- Modular ES6 JavaScript architecture
- Web Audio API for synthesised sound
- CSS animations and transitions

---

## [0.1.0] - 2025-12-15

### Added

#### Game Launcher
- Main launcher with menu to select between games
- Support for Snake Classic, Snake 3D, and Brawler

#### Snake Classic (Pygame)
- Classic 2D snake gameplay with sandbox and story modes
- Player profile system with persistent leaderboards
- Multiple map sizes and barrier options
- Expanded animal food system with 15+ types, multi-cell animals, health bars
- Kids Mode with 30% slower speed and 50% score adjustment
- Pause functionality

#### Snake 3D (Pygame)
- Stardew Valley-style oblique 3D perspective
- Same gameplay as Snake Classic with enhanced visual depth

#### Brawler (Pygame)
- 2v2 Brawl Ball arena game
- Four unique brawlers: Colt, Shelly, Piper, Edgar
- Two modes: 2-Player Local and Player vs AI
- AI state-based behaviour, ball physics, projectile system
- Health bars, ammo, super meters; 2-minute matches, first to 2 goals

### Technical
- Modular codebase with per-game packages
- Pygame-based rendering with oblique-projection support
- JSON-based player profile storage

---

[0.3.1]: https://github.com/username/project/releases/tag/v0.3.1
[0.3.0]: https://github.com/username/project/releases/tag/v0.3.0
[0.2.0]: https://github.com/username/project/releases/tag/v0.2.0
[0.1.0]: https://github.com/username/project/releases/tag/v0.1.0
