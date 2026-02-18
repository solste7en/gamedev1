# Python Gaming Platform

A multi-game Python gaming platform featuring classic and modern games with both local (Pygame) and web-based (multiplayer) versions.

## Games Included

- **Snake Classic** - Traditional snake game with enhanced features
- **Snake 3D** - 2.5D oblique-view version (Stardew Valley style)
- **Brawler** - 2v2 Brawl Ball-style arena game

## Quick Start

### Local Games (Pygame)
```bash
pip install -r requirements.txt
python main.py
```

### Web Multiplayer
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies and run
pip install -r requirements.txt
python -m web.server.main
```

Then open `http://localhost:8000` in your browser. Share the Network URL with friends on the same WiFi to play together.

## Requirements

- Python 3.8+
- Pygame (for local games)
- FastAPI, uvicorn, websockets (for web version)
