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
from .profiles import get_profile_manager


VERSION = "0.5.0"

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


@app.get("/profile/{player_name}")
async def get_profile(player_name: str):
    """Return profile data for a player name (used for New/Existing check)"""
    mgr = get_profile_manager()
    profile = mgr.get_profile(player_name)
    return {"exists": profile is not None, "profile": profile.to_dict() if profile else None}


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


def _find_ssl_certs():
    """
    Look for mkcert-generated cert files next to this script and in CWD.
    Returns (certfile, keyfile) paths or (None, None) if not found.

    Run these commands once to generate the files:
        sudo mkcert -install           # installs local CA into browser trust store
        mkcert localhost 127.0.0.1 <your-LAN-IP>
    The generated files are named  localhost+2.pem / localhost+2-key.pem
    (the +2 suffix indicates two extra SANs were added).
    """
    search_dirs = [
        Path(__file__).parent.parent.parent,  # project root
        Path.cwd(),
    ]
    patterns = [
        ("localhost+2.pem", "localhost+2-key.pem"),
        ("localhost+1.pem", "localhost+1-key.pem"),
        ("localhost.pem",   "localhost-key.pem"),
        ("cert.pem",        "key.pem"),
    ]
    for d in search_dirs:
        for cert_name, key_name in patterns:
            cert = d / cert_name
            key  = d / key_name
            if cert.exists() and key.exists():
                return str(cert), str(key)
    return None, None


def main():
    """Run the server"""
    host = "0.0.0.0"  # Listen on all interfaces
    port = 8000

    local_ip = get_local_ip()
    ssl_certfile, ssl_keyfile = _find_ssl_certs()
    scheme = "https" if ssl_certfile else "http"
    ws_scheme = "wss" if ssl_certfile else "ws"

    print("\n" + "=" * 60)
    print(f"  🐍 Snake Multiplayer Server v{VERSION}")
    print("=" * 60)
    print(f"\n  Local URL:    {scheme}://localhost:{port}")
    print(f"  Network URL:  {scheme}://{local_ip}:{port}")
    if ssl_certfile:
        print(f"\n  🔒 HTTPS enabled  ({Path(ssl_certfile).name})")
    else:
        print("\n  ⚠  Running over HTTP (no SSL certs found).")
        print("     To enable HTTPS, run once in the project root:")
        print("       sudo mkcert -install")
        print(f"       mkcert localhost 127.0.0.1 {local_ip}")
        print("     Then restart the server.")
    print("\n  Share the Network URL with friends on the same network!")
    print("=" * 60 + "\n")

    kwargs = dict(host=host, port=port, log_level="info")
    if ssl_certfile:
        kwargs["ssl_certfile"] = ssl_certfile
        kwargs["ssl_keyfile"]  = ssl_keyfile

    uvicorn.run(app, **kwargs)


if __name__ == "__main__":
    main()
