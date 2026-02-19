"""
FastAPI WebSocket server for multiplayer snake games
"""

import os
import socket
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import uvicorn

try:
    # websockets ≥ 10 exposes ConnectionClosedError at the top level
    from websockets.exceptions import ConnectionClosedError as _WSConnectionClosedError
except ImportError:
    _WSConnectionClosedError = None

from .websocket import connection_manager


VERSION = "0.4.0"

app = FastAPI(title="Snake Multiplayer Server", version=VERSION)

# Get the client directory path
CLIENT_DIR = Path(__file__).parent.parent / "client"


# Serve static files
if CLIENT_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(CLIENT_DIR)), name="static")


@app.get("/")
async def root():
    """Serve the main game page"""
    index_path = CLIENT_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse("""
    <html>
        <head><title>Snake Multiplayer</title></head>
        <body>
            <h1>Snake Multiplayer Server</h1>
            <p>Server is running. Client files not found.</p>
            <p>WebSocket endpoint: /ws</p>
        </body>
    </html>
    """)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": VERSION}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for game communication"""
    await connection_manager.connect(websocket)
    player_id = -1
    
    try:
        while True:
            data = await websocket.receive_json()
            player_id = await connection_manager.handle_message(websocket, player_id, data)
    
    except WebSocketDisconnect:
        # Normal disconnect (client sent close frame)
        if player_id != -1:
            await connection_manager.disconnect(player_id)
    except Exception as e:
        # Silently swallow keepalive ping timeouts and other abrupt disconnects —
        # these are normal when a browser tab is closed or the network drops.
        # Re-raise anything that is genuinely unexpected.
        is_abrupt_disconnect = (
            "keepalive ping timeout" in str(e)
            or "no close frame received" in str(e)
            or "ConnectionClosed" in type(e).__name__
            or (_WSConnectionClosedError is not None and isinstance(e, _WSConnectionClosedError))
        )
        if not is_abrupt_disconnect:
            print(f"WebSocket error (player {player_id}): {e}")
        if player_id != -1:
            await connection_manager.disconnect(player_id)


def get_local_ip():
    """Get the local IP address for LAN play"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main():
    """Run the server"""
    host = "0.0.0.0"  # Listen on all interfaces
    port = 8000
    
    local_ip = get_local_ip()
    
    print("\n" + "=" * 60)
    print(f"  🐍 Snake Multiplayer Server v{VERSION}")
    print("=" * 60)
    print(f"\n  Local URL:    http://localhost:{port}")
    print(f"  Network URL:  http://{local_ip}:{port}")
    print("\n  Share the Network URL with friends on the same network!")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
