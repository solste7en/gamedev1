/**
 * Lobby - Game lobby UI controller
 */

export class Lobby {
    constructor(networkManager) {
        this.network = networkManager;
        this.room = null;
        this.playerId = null;
        this.isHost = false;
        this.isReady = false;
        
        this.onGameStart = null;  // Callback when game starts
        
        this.bindElements();
        this.setupEventListeners();
    }
    
    /**
     * Bind DOM elements
     */
    bindElements() {
        this.lobbyScreen = document.getElementById('lobby-screen');
        this.roomCodeDisplay = document.getElementById('lobby-room-code');
        this.lobbySettings = document.getElementById('lobby-settings');
        this.playerList = document.getElementById('player-list');
        this.chatMessages = document.getElementById('chat-messages');
        this.chatInput = document.getElementById('chat-input');
        
        this.selectGameType = document.getElementById('select-game-type');
        this.selectGameMode = document.getElementById('select-game-mode');
        this.selectBarrierDensity = document.getElementById('select-barrier-density');
        this.selectMapSize = document.getElementById('select-map-size');
        
        this.btnReady = document.getElementById('btn-ready');
        this.btnStartGame = document.getElementById('btn-start-game');
        this.btnLeaveRoom = document.getElementById('btn-leave-room');
        this.btnCopyCode = document.getElementById('btn-copy-code');
        this.btnSendChat = document.getElementById('btn-send-chat');
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        this.btnReady.addEventListener('click', () => this.toggleReady());
        this.btnStartGame.addEventListener('click', () => this.startGame());
        this.btnLeaveRoom.addEventListener('click', () => this.leaveRoom());
        this.btnCopyCode.addEventListener('click', () => this.copyRoomCode());
        this.btnSendChat.addEventListener('click', () => this.sendChat());
        
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendChat();
        });
        
        this.selectGameType.addEventListener('change', () => this.updateSettings());
        this.selectGameMode.addEventListener('change', () => this.updateSettings());
        this.selectBarrierDensity.addEventListener('change', () => this.updateSettings());
        this.selectMapSize.addEventListener('change', () => this.updateSettings());
    }
    
    /**
     * Show the lobby
     * @param {Object} room - Room data
     * @param {number} playerId - Current player's ID
     * @param {boolean} isNewRoom - True if this is a newly created room, false if returning from game
     */
    show(room, playerId, isNewRoom = true) {
        this.room = room;
        this.playerId = playerId;
        this.isHost = room.host_id === playerId;
        this.isReady = false;
        
        this.lobbyScreen.classList.remove('hidden');
        this.lobbyScreen.classList.add('active');
        
        this.updateRoomDisplay();
        this.updatePlayerList();
        this.updateHostControls();
        this.updateSinglePlayerMode(isNewRoom);
        
        // Clear chat
        this.chatMessages.innerHTML = '';
        this.addSystemMessage('Welcome to the lobby!');
        
        // Auto-ready (but NOT auto-start) for single player mode
        // Player can adjust settings then click "Start Game" manually
        if (this.isSinglePlayer()) {
            this.addSystemMessage('Single player mode - click Start Game when ready!');
            // Auto-ready after a brief delay
            setTimeout(() => {
                if (!this.isReady) {
                    this.network.setReady(true);
                    this.isReady = true;
                }
            }, 300);
        }
    }
    
    /**
     * Hide the lobby
     */
    hide() {
        this.lobbyScreen.classList.remove('active');
        this.lobbyScreen.classList.add('hidden');
    }
    
    /**
     * Update room display
     */
    updateRoomDisplay() {
        this.roomCodeDisplay.textContent = this.room.code;
        this.selectGameType.value = this.room.game_type;
        this.selectGameMode.value = this.room.game_mode;
        this.selectBarrierDensity.value = this.room.barrier_density || 'none';
        this.selectMapSize.value = this.room.map_size || 'medium';
    }
    
    /**
     * Update player list
     */
    updatePlayerList() {
        this.playerList.innerHTML = '';
        
        const colors = ['#3498DB', '#E74C3C', '#2ECC71', '#F1C40F'];
        
        this.room.players.forEach((player, index) => {
            const card = document.createElement('div');
            card.className = 'player-card';
            
            if (player.state === 'ready') {
                card.classList.add('ready');
            }
            if (player.id === this.room.host_id) {
                card.classList.add('host');
            }
            
            const color = colors[player.quadrant % colors.length];
            const isMe = player.id === this.playerId;
            const hostBadge = player.id === this.room.host_id ? ' 👑' : '';
            const statusText = player.state === 'ready' ? 'Ready' : 'Not Ready';
            
            card.innerHTML = `
                <div class="player-avatar" style="background-color: ${color}">
                    ${player.name.charAt(0).toUpperCase()}
                </div>
                <div class="player-details">
                    <div class="player-name">${player.name}${hostBadge}${isMe ? ' (You)' : ''}</div>
                    <div class="player-status">${statusText}</div>
                </div>
            `;
            
            this.playerList.appendChild(card);
        });
        
        // Update start button visibility
        this.updateStartButton();
    }
    
    /**
     * Update host-only controls
     */
    updateHostControls() {
        // Only host can change settings
        this.selectGameType.disabled = !this.isHost;
        this.selectGameMode.disabled = !this.isHost;
        this.selectBarrierDensity.disabled = !this.isHost;
        this.selectMapSize.disabled = !this.isHost;
        
        // Settings visibility
        this.lobbySettings.style.display = this.isHost ? 'block' : 'none';
    }
    
    /**
     * Check if this is single player mode
     */
    isSinglePlayer() {
        return this.room && this.room.game_mode === 'single_player';
    }
    
    /**
     * Update UI for single player mode
     * @param {boolean} isNewRoom - True if this is a newly created room
     */
    updateSinglePlayerMode(isNewRoom = true) {
        if (this.isSinglePlayer()) {
            // Gray out ready button for single player (auto-ready)
            this.btnReady.disabled = true;
            this.btnReady.classList.add('btn-secondary');
            this.btnReady.classList.remove('btn-primary');
            this.btnReady.textContent = 'Ready (Solo)';
        } else {
            // Normal mode - enable ready button
            this.btnReady.disabled = false;
            if (!this.isReady) {
                this.btnReady.textContent = 'Ready';
                this.btnReady.classList.remove('btn-secondary');
                this.btnReady.classList.add('btn-primary');
            }
        }
    }
    
    /**
     * Update start button visibility
     */
    updateStartButton() {
        if (this.isHost && this.room.can_start) {
            this.btnStartGame.classList.remove('hidden');
        } else {
            this.btnStartGame.classList.add('hidden');
        }
    }
    
    /**
     * Toggle ready state
     */
    toggleReady() {
        this.isReady = !this.isReady;
        this.network.setReady(this.isReady);
        
        this.btnReady.textContent = this.isReady ? 'Not Ready' : 'Ready';
        this.btnReady.classList.toggle('btn-secondary', this.isReady);
        this.btnReady.classList.toggle('btn-primary', !this.isReady);
    }
    
    /**
     * Update settings (host only)
     */
    updateSettings() {
        if (!this.isHost) return;
        
        this.network.setSettings(
            this.selectGameType.value,
            this.selectGameMode.value,
            this.selectBarrierDensity.value,
            this.selectMapSize.value
        );
    }
    
    /**
     * Start the game (host only)
     */
    startGame() {
        if (!this.isHost) return;
        this.network.startGame();
    }
    
    /**
     * Leave the room
     */
    leaveRoom() {
        this.network.leaveRoom();
        this.hide();
    }
    
    /**
     * Copy room code to clipboard
     */
    async copyRoomCode() {
        try {
            await navigator.clipboard.writeText(this.room.code);
            this.btnCopyCode.textContent = '✓';
            setTimeout(() => {
                this.btnCopyCode.textContent = '📋';
            }, 2000);
        } catch (e) {
            console.error('Failed to copy:', e);
        }
    }
    
    /**
     * Send chat message
     */
    sendChat() {
        const message = this.chatInput.value.trim();
        if (!message) return;
        
        this.network.sendChat(message);
        this.chatInput.value = '';
    }
    
    /**
     * Add chat message to display
     */
    addChatMessage(playerName, message) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'chat-message';
        msgDiv.innerHTML = `<span class="name">${playerName}:</span> ${this.escapeHtml(message)}`;
        this.chatMessages.appendChild(msgDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    /**
     * Add system message
     */
    addSystemMessage(message) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'chat-message';
        msgDiv.style.color = '#94A3B8';
        msgDiv.style.fontStyle = 'italic';
        msgDiv.textContent = message;
        this.chatMessages.appendChild(msgDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    /**
     * Update room state
     */
    updateRoom(room) {
        this.room = room;
        this.isHost = room.host_id === this.playerId;
        this.updateRoomDisplay();
        this.updatePlayerList();
        this.updateHostControls();
        // Pass false since this is an update to an existing room, not a new one
        this.updateSinglePlayerMode(false);
    }
    
    /**
     * Handle player joined
     */
    playerJoined(player, room) {
        this.updateRoom(room);
        this.addSystemMessage(`${player.name} joined the room`);
    }
    
    /**
     * Handle player left
     */
    playerLeft(playerId, room) {
        this.updateRoom(room);
        this.addSystemMessage('A player left the room');
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

export default Lobby;
