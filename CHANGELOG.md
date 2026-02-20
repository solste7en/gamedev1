# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-02-10

### Added
- **Duel mode**: new 1v1 competitive game mode with these features:
  - Accelerated survival mechanics — reaches top speed in ~2 minutes, game ends at 2:30
  - Best of 3, 5, or 7 series format with automatic round progression
  - Hybrid tail decay + speed ramp (compressed intervals: 5s → 4s → 3s → 2.5s)
  - Series score displayed at the top of the screen throughout the match
  - Round-over intermission with 5-second countdown to next round
  - "XXX wins!" announcement when series is decided
  - Extra Large map option disabled for Duel mode
- **Player profiles — Duel stats section**: tracks win/loss record against human players and each AI difficulty level, with winning percentage displayed (e.g., "3W / 5G (60%)")
- **Smooth screen transitions**: all screen changes (menu ↔ lobby ↔ game) now use consistent fade animations for polished UX
- **Automated game simulation script** (`test_duel_simulation.py`): runs 100+ games programmatically to identify bugs and validate game logic

### Changed
- Duel mode is now selectable even with default AI bots — selecting Duel automatically adjusts AI count to ensure exactly 2 total players
- Series length selector (Best of 3/5/7) properly persists across room updates
- Game mode change handler reordered to apply UI constraints before sending settings to server

### Fixed
- **Critical bug**: human players in non-Battle Royale modes now spawn in separate quadrants instead of all spawning at the same position
- Duel mode enable/disable logic now only considers human player count (AI bots no longer incorrectly disable the mode)
- Series length dropdown no longer reverts to "Best of 3" after selection

### Technical
- Server-side delta state broadcasting: `game_state` messages now exclude static fields (walls, quadrant_bounds) after initial sync, reducing network payload per tick
- Client-side food graphics caching: skip expensive redraws when food visual state is unchanged between frames
- Player quadrant assignment logic moved to `setup_game()` for consistency across all game modes

---

## [0.4.0] - 2026-02-10

### Added
- **Battle Royale mode**: up to 6 players on a shared map; 3–4 food items simultaneously; only killing hits score; half-length respawn penalty (min 3); same Fibonacci respawn delay as High Score mode; timed match, highest score wins
- **Spawn freeze (all modes)**: 1-second invulnerability window after respawn and at game start — snake glows white and cannot move or be hit
- **Per-player hunger bars**: individual decay/hunger bars rendered inside each player's quadrant in Survival mode; global speed multiplier shown separately in the HUD
- **Map size expansion**: four new sizes — Small (25×18), Medium (35×22, default), Large (45×28), Extra Large (60×36)
- **Leaderboard top-500** with pagination (50 per page) and extended color tiers for top 3, 10, 30, 50, and 100
- **Leaderboard unique-player filter**: toggle checkbox to show only each player's personal best
- **Fibonacci respawn penalty** in High Score mode — each death adds a progressively longer respawn delay (2s, 3s, 5s, 8s, 13s, 21s…)
- **Hybrid scoring system**: small animals now yield 60–100 pts; per-category hit-recovery cooldowns (0.8s / 1.5s / 2.5s) prevent instant multi-hit farming; combo bonus on killing hit
- **AI bot names**: randomly selected from a pool of 100 top soccer players (post-2000) — different each session, re-rollable with the dice button
- **Reroll button** (🎲) on AI cards simultaneously randomises both the bot's name and skill level
- **Remove bot button** (✕) on AI cards allows removing a bot and updates the count dropdown automatically
- **Click-to-reroll**: clicking an AI bot's name in the lobby re-rolls it to a new random name
- **Random initial AI skill levels**: bots no longer default to Amateur; each starts at a randomly assigned level

### Changed
- Survival mode speed multiplier now correctly resets to 1× on every new game
- AI bots significantly improved at all levels — higher levels use BFS flood-fill dead-end avoidance, `value_power` scoring, and mode-aware tactics (Survival vs High Score vs Battle Royale)
- Pro and World-Class AI levels dialled back slightly: Pro ≈ previous Semi-Pro+, World-Class ≈ previous Pro
- Countdown overlay is fully transparent — game map and player positions are clearly visible before the match begins (all modes)
- All modes default to 2 AI bots on new room creation
- Battle Royale defaults to Large map; "None" and "1 Bot" AI count options are grayed out in this mode
- Brawler game marked as "In Dev" on the home page and in the Brawler lobby title
- Removed "Create Multiplayer" button — single-player and multiplayer both use the same "Start Game" / "Join Room" flow
- In-game animal legend updated to reflect the new hybrid scoring scheme with point values per animal

### Fixed
- WebSocket `ConnectionClosedError` (keepalive ping timeout) no longer printed as a noisy server error — abrupt client disconnects (closed tab, network drop) are now handled silently
- Ready button no longer stops working after a game ends; server syncs ready state on every room update
- AI bot name input no longer resets cursor position on each keystroke
- Speed multiplier no longer carries over from a previous Survival game session
- Gray screen on solo Survival game entry resolved
- 404 not found errors for `/favicon.ico` resolved via inline SVG favicon
- AI bot cards: reroll (🎲) and remove (✕) buttons no longer overlap

### Technical
- Version constant centralised in `main.py` (`VERSION = "0.4.0"`) — used by both the health endpoint and startup banner
- `websockets.exceptions.ConnectionClosedError` now caught and suppressed at the WebSocket endpoint level

---

## [0.3.2] - 2026-02-10

### Added
- **Battle Royale mode**: new PvP game mode with these features:
  - All players share a single map (only Medium, Large, or Extra Large available)
  - 3–4 food items spawn simultaneously for competitive feeding
  - Only killing hits score (no per-hit points like other modes)
  - Death by wall, barrier, or colliding into another snake's body — the snake being hit survives
  - Fibonacci respawn delays (same as High Score mode)
  - Respawn at half length (rounded up, minimum 3)
  - Timed match with configurable duration (30s, 1min, 2min, 3min)
  - Highest score at the end wins
- **Spawn freeze**: 1-second invulnerability period after respawn and at game start (applies to all modes) — snake glows white and cannot move or be hit during this time
- **Spawn freeze visual**: pulsing white glow effect on snakes during their invulnerability window

### Changed
- Small map option is disabled (grayed out) in Battle Royale mode
- Timer displays purple tint for Battle Royale mode

---

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

[0.5.0]: https://github.com/solste7en/gamedev1/releases/tag/v0.5.0
[0.4.0]: https://github.com/solste7en/gamedev1/releases/tag/v0.4.0
[0.3.2]: https://github.com/solste7en/gamedev1/releases/tag/v0.3.2
[0.3.1]: https://github.com/solste7en/gamedev1/releases/tag/v0.3.1
[0.3.0]: https://github.com/solste7en/gamedev1/releases/tag/v0.3.0
[0.2.0]: https://github.com/solste7en/gamedev1/releases/tag/v0.2.0
[0.1.0]: https://github.com/solste7en/gamedev1/releases/tag/v0.1.0
