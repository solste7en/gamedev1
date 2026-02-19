/**
 * Lobby - Game lobby UI controller
 */

const AI_ICONS = ['🤖', '🐍', '👾', '🎮', '🦾', '🧠', '👻', '🔥', '⚡', '🌟', '🦊', '💀'];
const AI_DIFF_LEVELS = ['amateur', 'semi_pro', 'pro', 'world_class'];
const AI_DIFF_LABELS = { amateur: 'Amateur', semi_pro: 'Semi-Pro', pro: 'Pro', world_class: 'World-Class' };

// Full pool of bot names — top soccer players post-2000
const AI_DEFAULT_NAMES = [
    'Messi', 'Ronaldo', 'Neymar', 'Mbappé', 'Lewandowski',
    'Modric', 'Salah', 'De Bruyne', 'Benzema', 'Kane',
    'Suárez', 'Rooney', 'Ribéry', 'Robben', 'Iniesta',
    'Xavi', 'Ramos', 'Pirlo', 'Buffon', 'Drogba',
    'Hazard', 'Agüero', 'Özil', 'Müller', 'Haaland',
    'Vinicius', 'Pedri', 'Bellingham', 'Rodri', 'Kroos',
    'Firmino', 'Mané', 'Son', 'Griezmann', 'Ibrahimović',
    'Cavani', 'Falcao', 'Henry', 'Kaka', 'Ronaldinho',
    'Tevez', 'Thiago', 'Verratti', 'Dybala', 'Lukaku',
    'Shevchenko', 'Del Piero', 'Totti', 'Nedvěd', 'Lahm',
    'Götze', 'Klose', 'Kompany', 'Vidic', 'Ferdinand',
    'Silva', 'Buffon', 'Casillas', 'Fabregas', 'Rakitić',
    'Busquets', 'Villa', 'Torres', 'Forlan', 'Balotelli',
    'Oscar', 'Willian', 'Coutinho', 'Hulk', 'Bernard',
];

/** Pick a random name from the pool, optionally excluding names already used */
function randomAIName(usedNames = []) {
    const available = AI_DEFAULT_NAMES.filter(n => !usedNames.includes(n));
    const pool = available.length > 0 ? available : AI_DEFAULT_NAMES;
    return pool[Math.floor(Math.random() * pool.length)];
}

/** Pick a random difficulty level */
function randomAIDifficulty() {
    return AI_DIFF_LEVELS[Math.floor(Math.random() * AI_DIFF_LEVELS.length)];
}

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
            this.updateTimeLimitVisibility(true);  // modeJustChanged = true
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
        
        // Default new rooms to 2 AI bots (host only, no existing bots set)
        let effectiveAiCount = room.ai_count || 0;
        if (isNewRoom && this.isHost && effectiveAiCount === 0) {
            effectiveAiCount = 2;
            // Push the default to the server immediately
            setTimeout(() => {
                if (this.selectAICount) {
                    this.selectAICount.value = '2';
                    this.syncAIConfigs();
                    this.updateSettings();
                    this.updatePlayerList();
                }
            }, 0);
        }
        
        if (this.selectAICount) {
            this.selectAICount.value = effectiveAiCount.toString();
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
        
        // Grow or shrink the array
        while (this.aiConfigs.length < aiCount) {
            const i = this.aiConfigs.length;
            const usedNames = this.aiConfigs.map(c => c.name);
            this.aiConfigs.push({
                name: randomAIName(usedNames),
                icon: AI_ICONS[Math.floor(Math.random() * AI_ICONS.length)],
                difficulty: randomAIDifficulty()
            });
        }
        this.aiConfigs.length = aiCount;
        
        // Apply server values if given (sync from room state) — only override if non-empty
        if (serverDifficulties) {
            serverDifficulties.forEach((d, i) => {
                if (this.aiConfigs[i] && d) this.aiConfigs[i].difficulty = d;
            });
        }
        if (serverNames) {
            serverNames.forEach((n, i) => {
                if (this.aiConfigs[i] && n) this.aiConfigs[i].name = n;
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
     * Remove an AI bot by index, update dropdown and re-render
     */
    removeAIBot(index) {
        this.aiConfigs.splice(index, 1);
        const newCount = this.aiConfigs.length;
        if (this.selectAICount) {
            this.selectAICount.value = String(newCount);
        }
        this.updateSettings();
        this.updatePlayerList();
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
        
        const colors = ['#3498DB', '#E74C3C', '#2ECC71', '#F1C40F', '#A855F7', '#F97316'];
        
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
                const usedNames = this.aiConfigs.filter(Boolean).map(c => c.name);
                this.aiConfigs[i] = {
                    name: randomAIName(usedNames),
                    icon: AI_ICONS[Math.floor(Math.random() * AI_ICONS.length)],
                    difficulty: (this.room.ai_difficulties && this.room.ai_difficulties[i]) || randomAIDifficulty()
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
                        <div class="ai-name-row">
                            <input class="ai-name-input" data-ai-idx="${i}" value="${this.escapeHtml(cfg.name)}" maxlength="16" placeholder="Bot name…" />
                            <button class="ai-reroll-btn" title="Random new name">🎲</button>
                        </div>
                        <div class="ai-skill-row">
                            <span class="ai-skill-label">Level:</span>
                            <button class="ai-diff-badge ${diffClass}" title="Click to cycle difficulty">↻ ${diffLabel}</button>
                        </div>
                    </div>
                    <button class="ai-remove-btn" title="Remove this bot">✕</button>
                `;
                
                const iconBtn   = card.querySelector('.ai-icon-btn');
                const nameInput = card.querySelector('.ai-name-input');
                const rerollBtn = card.querySelector('.ai-reroll-btn');
                const diffBtn   = card.querySelector('.ai-diff-badge');
                const removeBtn = card.querySelector('.ai-remove-btn');
                
                // Capture index for closures
                const idx = i;
                iconBtn.addEventListener('click', (e) => this.cycleAIIcon(idx, e.currentTarget));
                nameInput.addEventListener('input', (e) => {
                    this.aiConfigs[idx].name = e.target.value;
                    clearTimeout(this._nameDebounceTimer);
                    this._nameDebounceTimer = setTimeout(() => this.updateSettings(), 600);
                });
                rerollBtn.addEventListener('click', () => {
                    // Randomize name
                    const usedNames = this.aiConfigs.map((c, j) => j !== idx ? c.name : null).filter(Boolean);
                    const newName = randomAIName(usedNames);
                    this.aiConfigs[idx].name = newName;
                    nameInput.value = newName;
                    
                    // Randomize difficulty (in-place update of the badge to avoid re-render)
                    const newDiff = randomAIDifficulty();
                    this.aiConfigs[idx].difficulty = newDiff;
                    const newLabel = AI_DIFF_LABELS[newDiff];
                    const newClass = 'diff-' + newDiff.replace('_', '-');
                    diffBtn.textContent = `↻ ${newLabel}`;
                    diffBtn.className = `ai-diff-badge ${newClass}`;
                    
                    clearTimeout(this._nameDebounceTimer);
                    this._nameDebounceTimer = setTimeout(() => this.updateSettings(), 300);
                });
                diffBtn.addEventListener('click', (e) => this.cycleAIDifficulty(idx, e.currentTarget));
                removeBtn.addEventListener('click', () => this.removeAIBot(idx));
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
     * Show/hide time limit based on game mode.
     * @param {boolean} modeJustChanged - pass true when the user actually changed the mode dropdown
     */
    updateTimeLimitVisibility(modeJustChanged = false) {
        // Show time limit for high_score and battle_royale modes
        if (this.timeLimitRow) {
            const mode = this.selectGameMode.value;
            this.timeLimitRow.style.display = 
                (mode === 'high_score' || mode === 'battle_royale') ? 'flex' : 'none';
        }
        this.updateMapSizeOptions(modeJustChanged);
    }
    
    /**
     * Update map size and AI count options based on game mode.
     * @param {boolean} modeJustChanged - true when called because the user just switched modes
     */
    updateMapSizeOptions(modeJustChanged = false) {
        if (!this.selectMapSize) return;
        const mode = this.selectGameMode.value;
        const isBattleRoyale = mode === 'battle_royale';
        
        // Battle Royale: disable small map, default to large
        const smallOption = this.selectMapSize.querySelector('option[value="small"]');
        if (smallOption) {
            smallOption.disabled = isBattleRoyale;
            if (isBattleRoyale && this.selectMapSize.value === 'small') {
                this.selectMapSize.value = 'large';
            }
        }
        
        // AI count limits: Battle Royale = 2–5 bots (min 3 players); others = 0–3 bots
        if (this.selectAICount) {
            const allOptions = this.selectAICount.querySelectorAll('option');
            allOptions.forEach(opt => {
                const val = parseInt(opt.value);
                if (isBattleRoyale) {
                    // Gray out 0 and 1 bot (need at least 2 for min-3-player requirement)
                    opt.disabled = val < 2;
                    // Also disable 4/5 if already controlled by br-only class below
                } else {
                    // Other modes: disable 4 and 5 bot options (BR-only)
                    opt.disabled = val > 3;
                }
            });
            
            const currentVal = parseInt(this.selectAICount.value);
            if (!isBattleRoyale && currentVal > 3) {
                this.selectAICount.value = '3';
                this.syncAIConfigs();
            }
            // When switching TO Battle Royale, enforce minimum 2 bots
            if (isBattleRoyale && modeJustChanged && currentVal < 2) {
                this.selectAICount.value = '2';
                this.syncAIConfigs();
                this.updatePlayerList();
            }
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
