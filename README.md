# Python Gaming Platform

A browser-based gaming platform featuring Snake and Brawler games, playable solo or with others on the same local network — no installation required for players.

## Games

- **Snake** — Multi-player snake with AI bots, survival and high-score modes, animal-hunting mechanics, and a persistent leaderboard
- **Brawler** — 2v2 Brawl Ball-style arena game with four unique characters and AI opponents

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

The server will print something like:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
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
   - Example: `192.168.1.42`

2. **Share the address** with other players. They open:
   ```
   http://192.168.1.42:8000
   ```

3. **Create a room** from the home page. Share the room code with others so they can join.

> The server must remain running on the host machine for the duration of play.

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
