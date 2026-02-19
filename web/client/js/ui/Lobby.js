/**
 * Lobby - Game lobby UI controller
 */

const AI_ICONS = ['🤖', '🐍', '👾', '🎮', '🦾', '🧠', '👻', '🔥', '⚡', '🌟', '🦊', '💀'];
const AI_DIFF_LEVELS = ['amateur', 'semi_pro', 'pro', 'world_class'];
const AI_DIFF_LABELS = { amateur: 'Amateur', semi_pro: 'Semi-Pro', pro: 'Pro', world_class: 'World-Class' };

export class Lobby {
    constructor(networkManager) {
        this.network = networkManager;
        this.room = null;
        this.playerId = null;
        this.isHost = false;
        this.isReady = false;
        
        this.onGameStart = null;  // Callback when game starts
        this.onShowLeaderboard = null;  // Callback to show leaderboard
        
        // Per-bot config state: [{name, icon, difficulty}, ...]
        this.aiConfigs = [];
        
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
        
        this.selectGameMode = document.getElementById('select-game-mode');
        this.selectBarrierDensity = document.getElementById('select-barrier-density');
        this.selectMapSize = document.getElementById('select-map-size');
        this.selectTimeLimit = document.getElementById('select-time-limit');
        this.timeLimitRow = document.getElementById('time-limit-row');
        this.selectAICount = document.getElementById('select-ai-count');
        
        this.btnReady = document.getElementById('btn-ready');
        this.btnStartGame = document.getElementById('btn-start-game');
        this.btnLobbyLeaderboard = document.getElementById('btn-lobby-leaderboard');
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
        this.btnLobbyLeaderboard.addEventListener('click', () => this.showLeaderboard());
        this.btnLeaveRoom.addEventListener('click', () => this.leaveRoom());
        this.btnCopyCode.addEventListener('click', () => this.copyRoomCode());
        this.btnSendChat.addEventListener('click', () => this.sendChat());
        
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendChat();
        });
        
        this.selectGameMode.addEventListener('change', () => {
            this.updateSettings();
            this.updateTimeLimitVisibility();
        });
        this.selectBarrierDensity.addEventListener('change', () => this.updateSettings());
        this.selectMapSize.addEventListener('change', () => this.updateSettings());
        this.selectTimeLimit.addEventListener('change', () => this.updateSettings());
        
        this.selectAICount?.addEventListener('change', () => {
            this.syncAIConfigs();
            this.updateSettings();
            this.updatePlayerList();
        });
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
        
        // Reset aiConfigs and sync from room
        this.aiConfigs = [];
        if (this.selectAICount) {
            this.selectAICount.value = (room.ai_count || 0).toString();
        }
        this.syncAIConfigs(room.ai_difficulties || [], room.ai_names || []);
        
        this.lobbyScreen.classList.remove('hidden');
        this.lobbyScreen.classList.add('active');
        
        this.updateRoomDisplay();
        this.updatePlayerList();
        this.updateHostControls();
        this.updateSinglePlayerMode(isNewRoom);
        
        // Clear chat
        this.chatMessages.innerHTML = '';
        this.addSystemMessage('Welcome to the lobby!');
        
        // Auto-ready for single player mode OR when AI opponents are set
        // (AI bots are always ready, so no need for the human to click ready)
        if (this.shouldAutoReady()) {
            const msg = this.isSinglePlayer()
                ? 'Single player mode - click Start Game when ready!'
                : 'AI opponents set - you are auto-readied. Click Start Game!';
            this.addSystemMessage(msg);
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
        const mode = this.room.game_mode;
        // Map legacy 'single_player' to 'survival' since we no longer show that option
        this.selectGameMode.value = (mode === 'single_player') ? 'survival' : (mode || 'survival');
        this.selectBarrierDensity.value = this.room.barrier_density || 'none';
        this.selectMapSize.value = this.room.map_size || 'medium';
        this.selectTimeLimit.value = this.room.time_limit || '1m';
        this.updateTimeLimitVisibility();
    }
    
    /**
     * Sync aiConfigs array to match current ai count, preserving existing entries.
     * Should be called when ai count changes.
     */
    syncAIConfigs(serverDifficulties = null, serverNames = null) {
        const aiCount = parseInt(this.selectAICount?.value || '0');
        const defaultIcons = ['🤖', '👾', '🦾', '🧠'];
        
        // Grow or shrink the array
        while (this.aiConfigs.length < aiCount) {
            const i = this.aiConfigs.length;
            this.aiConfigs.push({
                name: `Bot ${i + 1}`,
                icon: defaultIcons[i % defaultIcons.length],
                difficulty: (serverDifficulties && serverDifficulties[i]) || 'amateur'
            });
        }
        this.aiConfigs.length = aiCount;
        
        // Apply server values if given (sync from room state)
        if (serverDifficulties) {
            serverDifficulties.forEach((d, i) => {
                if (this.aiConfigs[i]) this.aiConfigs[i].difficulty = d;
            });
        }
        if (serverNames) {
            serverNames.forEach((n, i) => {
                if (this.aiConfigs[i]) this.aiConfigs[i].name = n;
            });
        }
    }
    
    /**
     * Cycle the icon for an AI bot - updates in-place to avoid input cursor loss
     */
    cycleAIIcon(index, btn) {
        const current = this.aiConfigs[index].icon;
        const idx = AI_ICONS.indexOf(current);
        this.aiConfigs[index].icon = AI_ICONS[(idx + 1) % AI_ICONS.length];
        if (btn) btn.textContent = this.aiConfigs[index].icon;
    }
    
    /**
     * Cycle the difficulty for an AI bot - updates in-place to avoid input cursor loss
     */
    cycleAIDifficulty(index, btn) {
        const current = this.aiConfigs[index].difficulty;
        const idx = AI_DIFF_LEVELS.indexOf(current);
        const next = AI_DIFF_LEVELS[(idx + 1) % AI_DIFF_LEVELS.length];
        this.aiConfigs[index].difficulty = next;
        if (btn) {
            const nextLabel = AI_DIFF_LABELS[next];
            const nextClass = 'diff-' + next.replace('_', '-');
            btn.textContent = `↻ ${nextLabel}`;
            btn.className = `ai-diff-badge ${nextClass}`;
        }
        this.updateSettings();
    }
    
    /**
     * Update player list.
     * Preserves focus/cursor of any active AI name input to avoid cursor-jump bugs.
     */
    updatePlayerList() {
        // Save focus state before wiping DOM
        const activeEl = document.activeElement;
        let savedAiIdx = null;
        let savedSelStart = null;
        let savedSelEnd = null;
        if (activeEl && activeEl.classList && activeEl.classList.contains('ai-name-input')) {
            savedAiIdx = activeEl.dataset.aiIdx;
            savedSelStart = activeEl.selectionStart;
            savedSelEnd = activeEl.selectionEnd;
        }
        
        this.playerList.innerHTML = '';
        
        const colors = ['#3498DB', '#E74C3C', '#2ECC71', '#F1C40F'];
        
        this.room.players.forEach((player) => {
            const card = document.createElement('div');
            card.className = 'player-card';
            
            if (player.state === 'ready') card.classList.add('ready');
            if (player.id === this.room.host_id) card.classList.add('host');
            
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
        
        // AI bot slots
        const aiCount = this.room.ai_count || 0;
        for (let i = 0; i < aiCount; i++) {
            // Ensure config exists
            if (!this.aiConfigs[i]) {
                this.aiConfigs[i] = {
                    name: `Bot ${i + 1}`,
                    icon: AI_ICONS[i % AI_ICONS.length],
                    difficulty: (this.room.ai_difficulties && this.room.ai_difficulties[i]) || 'amateur'
                };
            }
            const cfg = this.aiConfigs[i];
            const diffLabel = AI_DIFF_LABELS[cfg.difficulty] || 'Amateur';
            const diffClass = 'diff-' + cfg.difficulty.replace('_', '-');
            
            const card = document.createElement('div');
            card.className = 'player-card ready ai-slot' + (this.isHost ? ' ai-configurable' : '');
            
            if (this.isHost) {
                card.innerHTML = `
                    <button class="ai-icon-btn" title="Click to change icon">${cfg.icon}</button>
                    <div class="player-details">
                        <input class="ai-name-input" data-ai-idx="${i}" value="${this.escapeHtml(cfg.name)}" maxlength="12" placeholder="Bot name…" />
                        <div class="ai-skill-row">
                            <span class="ai-skill-label">Level:</span>
                            <button class="ai-diff-badge ${diffClass}" title="Click to cycle difficulty">↻ ${diffLabel}</button>
                        </div>
                    </div>
                `;
                
                const iconBtn = card.querySelector('.ai-icon-btn');
                const nameInput = card.querySelector('.ai-name-input');
                const diffBtn = card.querySelector('.ai-diff-badge');
                
                // Capture index for closures
                const idx = i;
                iconBtn.addEventListener('click', (e) => this.cycleAIIcon(idx, e.currentTarget));
                nameInput.addEventListener('input', (e) => {
                    this.aiConfigs[idx].name = e.target.value;
                    // Debounce server sync to avoid round-trip on every keystroke
                    clearTimeout(this._nameDebounceTimer);
                    this._nameDebounceTimer = setTimeout(() => this.updateSettings(), 600);
                });
                diffBtn.addEventListener('click', (e) => this.cycleAIDifficulty(idx, e.currentTarget));
            } else {
                card.innerHTML = `
                    <div class="player-avatar" style="background-color:#555">${cfg.icon}</div>
                    <div class="player-details">
                        <div class="player-name">${this.escapeHtml(cfg.name)}</div>
                        <div class="player-status ai-status-badge diff-${cfg.difficulty.replace('_','-')}">${diffLabel} · Ready</div>
                    </div>
                `;
            }
            
            this.playerList.appendChild(card);
        }
        
        // Restore focus to name input if it was active before the re-render
        if (savedAiIdx !== null) {
            const newInput = this.playerList.querySelector(`.ai-name-input[data-ai-idx="${savedAiIdx}"]`);
            if (newInput) {
                newInput.focus();
                try { newInput.setSelectionRange(savedSelStart, savedSelEnd); } catch (_) {}
            }
        }
        
        this.updateStartButton();
    }
    
    /**
     * Update host-only controls
     */
    updateHostControls() {
        // Only host can change settings
        this.selectGameMode.disabled = !this.isHost;
        this.selectBarrierDensity.disabled = !this.isHost;
        this.selectMapSize.disabled = !this.isHost;
        this.selectTimeLimit.disabled = !this.isHost;
        
        if (this.selectAICount) {
            this.selectAICount.disabled = !this.isHost;
        }
        
        // Settings visibility
        this.lobbySettings.style.display = this.isHost ? 'block' : 'none';
        
        // Sync room settings to UI
        if (this.room) {
            const mode = this.room.game_mode;
            this.selectGameMode.value = (mode === 'single_player') ? 'survival' : (mode || 'survival');
            this.selectBarrierDensity.value = this.room.barrier_density || 'none';
            this.selectMapSize.value = this.room.map_size || 'medium';
            this.selectTimeLimit.value = this.room.time_limit || '1m';
            
            if (this.selectAICount) {
                this.selectAICount.value = (this.room.ai_count || 0).toString();
            }
            
            // Sync aiConfigs from room state
            this.syncAIConfigs(this.room.ai_difficulties || [], this.room.ai_names || []);
            
            this.updateTimeLimitVisibility();
        }
    }
    
    /**
     * Show/hide time limit based on game mode
     */
    updateTimeLimitVisibility() {
        // Only show time limit for high_score mode
        if (this.timeLimitRow) {
            this.timeLimitRow.style.display = 
                this.selectGameMode.value === 'high_score' ? 'flex' : 'none';
        }
    }
    
    /**
     * Check if this is single player mode (no other human players, AI or alone)
     */
    isSinglePlayer() {
        return this.room && (
            this.room.game_mode === 'single_player' ||
            (this.room.players.length <= 1 && (this.room.ai_count || 0) > 0)
        );
    }
    
    /**
     * Check if player should be auto-readied.
     * True when there are AI opponents (AI bots are always ready) or playing alone.
     */
    shouldAutoReady() {
        if (!this.room) return false;
        if (this.room.game_mode === 'single_player') return true;
        if ((this.room.ai_count || 0) > 0) return true;
        // Alone in room
        if (this.room.players.length === 1) return true;
        return false;
    }
    
    /**
     * Update UI for single player mode or AI-opponent mode
     * @param {boolean} isNewRoom - True if this is a newly created room
     */
    updateSinglePlayerMode(isNewRoom = true) {
        if (this.shouldAutoReady()) {
            // Gray out ready button - player is automatically ready
            this.btnReady.disabled = true;
            this.btnReady.classList.add('btn-secondary');
            this.btnReady.classList.remove('btn-primary');
            this.btnReady.textContent = this.isSinglePlayer() ? 'Ready (Solo)' : 'Ready (AI Mode)';
        } else {
            // Normal multiplayer mode - enable ready button and always reflect current state
            this.btnReady.disabled = false;
            this.btnReady.textContent = this.isReady ? 'Not Ready' : 'Ready';
            this.btnReady.classList.toggle('btn-secondary', this.isReady);
            this.btnReady.classList.toggle('btn-primary', !this.isReady);
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
     * Get per-AI difficulty values from aiConfigs
     */
    getAIDifficulties() {
        const count = parseInt(this.selectAICount?.value || '0');
        return this.aiConfigs.slice(0, count).map(c => c.difficulty);
    }
    
    /**
     * Get per-AI names from aiConfigs
     */
    getAINames() {
        const count = parseInt(this.selectAICount?.value || '0');
        return this.aiConfigs.slice(0, count).map((c, i) => c.name || `Bot ${i + 1}`);
    }
    
    /**
     * Update settings (host only)
     */
    updateSettings() {
        if (!this.isHost) return;
        
        const aiCount = this.selectAICount ? parseInt(this.selectAICount.value) : 0;
        const aiDifficulties = this.getAIDifficulties();
        const aiNames = this.getAINames();
        
        this.network.setSettings(
            'snake_classic',
            this.selectGameMode.value,
            this.selectBarrierDensity.value,
            this.selectMapSize.value,
            this.selectTimeLimit.value,
            aiCount,
            aiDifficulties,
            aiNames
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
     * Show leaderboard from lobby
     */
    showLeaderboard() {
        if (this.onShowLeaderboard) {
            this.onShowLeaderboard();
        }
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
        const prevAiCount = this.room ? (this.room.ai_count || 0) : 0;
        this.room = room;
        this.isHost = room.host_id === this.playerId;
        
        // Sync local ready state from server data.
        // This prevents stale state after room_reset (where server sets all players to WAITING)
        // and avoids the ready button becoming unresponsive.
        const myServerPlayer = Array.isArray(room.players)
            ? room.players.find(p => p.id === this.playerId)
            : (room.players && room.players[this.playerId]);
        if (myServerPlayer) {
            this.isReady = myServerPlayer.state === 'ready';
        }
        
        // Sync ai count selector and aiConfigs from incoming room data
        if (this.selectAICount) {
            this.selectAICount.value = (room.ai_count || 0).toString();
        }
        this.syncAIConfigs(room.ai_difficulties || [], room.ai_names || []);
        
        this.updateRoomDisplay();
        this.updatePlayerList();
        this.updateHostControls();
        // Pass false since this is an update to an existing room, not a new one
        this.updateSinglePlayerMode(false);
        
        // If AI count just changed to > 0, auto-ready the player
        const newAiCount = room.ai_count || 0;
        if (newAiCount > 0 && prevAiCount === 0 && !this.isReady) {
            setTimeout(() => {
                if (!this.isReady && this.shouldAutoReady()) {
                    this.network.setReady(true);
                    this.isReady = true;
                }
            }, 200);
        }
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
