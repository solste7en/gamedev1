/**
 * NetworkManager - Handles WebSocket communication with the game server
 */

export class NetworkManager {
    constructor() {
        this.ws = null;
        this.connected = false;
        this.playerId = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000;
        
        // Event callbacks
        this.onConnect = null;
        this.onDisconnect = null;
        this.onError = null;
        this.messageHandlers = new Map();
    }
    
    /**
     * Connect to the WebSocket server
     */
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.updateStatus('connecting');
        
        try {
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                this.connected = true;
                this.reconnectAttempts = 0;
                this.updateStatus('connected');
                if (this.onConnect) this.onConnect();
            };
            
            this.ws.onclose = () => {
                this.connected = false;
                this.updateStatus('disconnected');
                if (this.onDisconnect) this.onDisconnect();
                this.attemptReconnect();
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                if (this.onError) this.onError(error);
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(data);
                } catch (e) {
                    console.error('Failed to parse message:', e);
                }
            };
        } catch (e) {
            console.error('Failed to connect:', e);
            this.updateStatus('disconnected');
        }
    }
    
    /**
     * Attempt to reconnect after disconnection
     */
    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('Max reconnect attempts reached');
            return;
        }
        
        this.reconnectAttempts++;
        console.log(`Reconnect attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
        
        setTimeout(() => {
            this.connect();
        }, this.reconnectDelay * this.reconnectAttempts);
    }
    
    /**
     * Update connection status display
     */
    updateStatus(status) {
        const indicator = document.getElementById('connection-status');
        if (!indicator) return;
        
        indicator.className = `connection-indicator ${status}`;
        const statusText = indicator.querySelector('.status-text');
        
        const statusTexts = {
            'connected': 'Connected',
            'disconnected': 'Disconnected',
            'connecting': 'Connecting...'
        };
        
        if (statusText) {
            statusText.textContent = statusTexts[status] || status;
        }
    }
    
    /**
     * Send a message to the server
     */
    send(data) {
        if (!this.connected || !this.ws) {
            console.error('Cannot send: not connected');
            return false;
        }
        
        try {
            this.ws.send(JSON.stringify(data));
            return true;
        } catch (e) {
            console.error('Failed to send message:', e);
            return false;
        }
    }
    
    /**
     * Handle incoming messages
     */
    handleMessage(data) {
        const type = data.type;
        
        // Handle player ID updates
        if (data.player_id) {
            this.playerId = data.player_id;
        }
        
        // Call registered handler
        const handler = this.messageHandlers.get(type);
        if (handler) {
            handler(data);
        } else {
            console.log('Unhandled message type:', type, data);
        }
    }
    
    /**
     * Register a message handler
     */
    on(messageType, handler) {
        this.messageHandlers.set(messageType, handler);
    }
    
    /**
     * Remove a message handler
     */
    off(messageType) {
        this.messageHandlers.delete(messageType);
    }
    
    // Room operations
    
    createRoom(playerName, gameType = 'snake_classic', gameMode = 'survival') {
        return this.send({
            type: 'create_room',
            player_name: playerName,
            game_type: gameType,
            game_mode: gameMode
        });
    }
    
    joinRoom(roomCode, playerName) {
        return this.send({
            type: 'join_room',
            room_code: roomCode,
            player_name: playerName
        });
    }
    
    leaveRoom() {
        return this.send({ type: 'leave_room' });
    }
    
    setReady(ready) {
        return this.send({ type: 'ready', ready: ready });
    }
    
    setSettings(gameType, gameMode, barrierDensity = null, mapSize = null, timeLimit = null) {
        const data = {
            type: 'set_settings',
            game_type: gameType,
            game_mode: gameMode
        };
        if (barrierDensity) {
            data.barrier_density = barrierDensity;
        }
        if (mapSize) {
            data.map_size = mapSize;
        }
        if (timeLimit) {
            data.time_limit = timeLimit;
        }
        return this.send(data);
    }
    
    startGame() {
        return this.send({ type: 'start_game' });
    }
    
    listRooms() {
        return this.send({ type: 'list_rooms' });
    }
    
    sendChat(message) {
        return this.send({ type: 'chat', message: message });
    }
    
    returnToLobby() {
        return this.send({ type: 'return_to_lobby' });
    }
    
    getLeaderboard() {
        return this.send({ type: 'get_leaderboard' });
    }
    
    submitScore(playerName, score, gameType) {
        return this.send({
            type: 'submit_score',
            player_name: playerName,
            score: score,
            game_type: gameType
        });
    }
    
    // Game operations
    
    sendInput(direction) {
        return this.send({ type: 'input', direction: direction });
    }
    
    /**
     * Disconnect from the server
     */
    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.connected = false;
    }
}

export default NetworkManager;
