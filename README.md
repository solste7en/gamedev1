# Python Gaming Platform

A browser-based gaming platform featuring Snake and Brawler games, playable solo or with others on the same local network — no installation required for players.

**Current Version: 0.4.0**

## Games

- **Snake** — Multi-player snake with AI bots, Survival / High Score / Battle Royale modes, animal-hunting mechanics, and a persistent leaderboard
- **Brawler** — 2v2 Brawl Ball-style arena game *(in development)*

---

## Setup & Running

### Requirements

- Python 3.8+
- Dependencies: `fastapi`, `uvicorn`, `websockets`

### Start the Server

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the game server
python -m web.server.main
```

The server will print:

```
============================================================
  🐍 Snake Multiplayer Server v0.4.0
============================================================

  Local URL:    http://localhost:8000
  Network URL:  http://192.168.x.x:8000

  Share the Network URL with friends on the same network!
============================================================
```

### Open the Game

Open your browser and go to:

```
http://localhost:8000
```

---

## Multiplayer on the Same Wi-Fi

Any device on the same Wi-Fi network can join a game without installing anything — just a browser.

1. **Find your local IP address** (on the host machine):
   - macOS / Linux: run `ifconfig | grep "inet "` or `ipconfig getifaddr en0`
   - Windows: run `ipconfig` and look for your IPv4 address
   - The server also prints it on startup as **Network URL**

2. **Share the address** with other players. They open:
   ```
   http://192.168.x.x:8000
   ```

3. **Create or join a room** from the home page. Share the room code so others can join.

> The server must remain running on the host machine for the duration of play.

---

## Snake — Game Modes

| Mode | Description |
|------|-------------|
| **Survival** | Last snake alive wins. Hunger decay + speed ramp creates escalating pressure |
| **High Score** | Score the most points before time runs out. Fibonacci respawn penalty on death |
| **Battle Royale** | All players share one map (up to 6). Only kill shots score. Half-length respawn |

## Snake — Scoring System

| Category | Animals | Points | Hits | Hit Cooldown |
|----------|---------|--------|------|-------------|
| Small | Worm, Bug, Cricket, Spider, Ladybug, Mouse, Bee, Frog, Butterfly | 60–100 | 1 | — |
| Medium | Fish, Rabbit, Turtle, Duck, Lizard | 80–120 | 2–3 | 0.8s |
| Large | Bird, Deer, Pig, Fox, Wolf | 160–200 | 4–5 | 1.5s |
| Huge | Bear, Croc, Tiger, Hippo, Lion, Elephant | 260–400 | 5 | 2.5s |

---

## Controls

### Snake
| Key | Action |
|-----|--------|
| Arrow keys or WASD | Move snake |

### Brawler
| Key | Action |
|-----|--------|
| WASD | Move |
| Mouse | Aim |
| Left-click | Attack |
| E / Right-click | Ability |
