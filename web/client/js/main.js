/**
 * Game Hub - Multiplayer Game Platform
 */

import { NetworkManager } from './engine/NetworkManager.js';
import { InputManager } from './engine/InputManager.js';
import { Renderer } from './engine/Renderer.js';
import { SoundManager } from './engine/SoundManager.js';
import { Menu } from './ui/Menu.js';
import { Lobby } from './ui/Lobby.js';
import { BrawlerLobby } from './ui/BrawlerLobby.js';
import { HUD } from './ui/HUD.js';
import { SnakeGame } from './game/SnakeGame.js';
import { Snake3DGame } from './game/Snake3DGame.js';
import { BrawlerGame } from './game/BrawlerGame.js';

class App {
    constructor() {
        this.network = new NetworkManager();
        this.input = new InputManager();
        this.sound = new SoundManager();
        this.renderer = null;
        this.menu = null;
        this.lobby = null;
        this.brawlerLobby = null;
        this.hud = null;
        this.game = null;
        
        this.currentScreen = 'menu';
        this.playerId = null;
        this.currentRoom = null;
        this.selectedGame = 'snake'; // 'snake' or 'brawler'
        
        // Initialize audio on first user interaction
        document.addEventListener('click', () => this.sound.init(), { once: true });
        document.addEventListener('keydown', () => this.sound.init(), { once: true });
    }
    
    /**
     * Initialize the application
     */
    async init() {
        console.log('Game Hub v0.4.0');

        // Initialize UI components
        this.menu = new Menu(this.network);
        this.lobby = new Lobby(this.network);
        this.brawlerLobby = new BrawlerLobby(this.network);
        this.hud = new HUD();

        // Connect lobby leaderboard callback to menu
        this.lobby.onShowLeaderboard = () => this.menu.showLeaderboard();

        // Setup game selection UI
        this.setupGameSelection();

        // Setup network handlers
        this.setupNetworkHandlers();

        // Setup profile modal
        this.setupProfileModal();

        // Setup player name new/existing indicator
        this.setupPlayerNameCheck();

        // Connect to server
        this.network.connect();

        // Setup back to lobby handler
        this.hud.onBackLobby(() => this.backToLobby());
    }
    
    /**
     * Setup game selection UI handlers
     */
    setupGameSelection() {
        const snakeBtn = document.getElementById('btn-snake-game');
        const brawlerBtn = document.getElementById('btn-brawler-game');
        
        if (snakeBtn) {
            snakeBtn.addEventListener('click', () => {
                this.selectedGame = 'snake';
                snakeBtn.classList.add('selected');
                brawlerBtn?.classList.remove('selected');
            });
        }
        
        if (brawlerBtn) {
            brawlerBtn.addEventListener('click', () => {
                this.selectedGame = 'brawler';
                brawlerBtn.classList.add('selected');
                snakeBtn?.classList.remove('selected');
            });
        }
    }
    
    /**
     * Setup network message handlers
     */
    setupNetworkHandlers() {
        // Connection events
        this.network.onConnect = () => {
            console.log('Connected to server');
        };
        
        this.network.onDisconnect = () => {
            console.log('Disconnected from server');
            if (this.currentScreen === 'game') {
                this.showError('Lost connection to server');
            }
        };
        
        // Room events
        this.network.on('room_created', (data) => {
            this.playerId = data.player_id;
            this.currentRoom = data.room;
            this.sound.play('click');
            this.showLobby();
        });
        
        this.network.on('room_joined', (data) => {
            this.playerId = data.player_id;
            this.currentRoom = data.room;
            this.sound.play('join');
            this.showLobby();
        });
        
        this.network.on('player_joined', (data) => {
            if (this.currentRoom?.game_type === 'brawler') {
                this.brawlerLobby.updateRoom(data.room);
            } else {
                this.lobby.playerJoined(data.player, data.room);
            }
            this.sound.play('join');
        });
        
        this.network.on('player_left', (data) => {
            if (this.currentRoom?.game_type === 'brawler') {
                this.brawlerLobby.updateRoom(data.room);
            } else {
                this.lobby.playerLeft(data.player_id, data.room);
            }
        });
        
        this.network.on('player_ready', (data) => {
            if (this.currentRoom?.game_type === 'brawler') {
                this.brawlerLobby.updateRoom(data.room);
            } else {
                this.lobby.updateRoom(data.room);
            }
            this.sound.play('ready');
        });
        
        this.network.on('settings_changed', (data) => {
            this.currentRoom = data.room;
            if (this.currentRoom?.game_type === 'brawler') {
                this.brawlerLobby.updateRoom(data.room);
            } else {
                this.lobby.updateRoom(data.room);
            }
        });
        
        this.network.on('room_reset', (data) => {
            this.currentRoom = data.room;
            if (this.currentRoom?.game_type === 'brawler') {
                this.brawlerLobby.updateRoom(data.room);
            } else {
                this.lobby.updateRoom(data.room);
            }
        });
        
        this.network.on('room_list', (data) => {
            this.menu.updateRoomList(data.rooms);
        });
        
        // Player left their own room → navigate back to home
        this.network.on('room_left', () => {
            this.currentRoom = null;
            this.showMenu();
        });
        
        this.network.on('chat', (data) => {
            this.lobby.addChatMessage(data.player_name, data.message);
        });
        
        // Brawler-specific events
        this.network.on('team_selected', (data) => {
            this.currentRoom = data.room;
            this.brawlerLobby.updateRoom(data.room);
        });
        
        this.network.on('character_selected', (data) => {
            this.currentRoom = data.room;
            this.brawlerLobby.updateRoom(data.room);
        });
        
        // Leaderboard events
        this.network.on('leaderboard', (data) => {
            this.menu.updateLeaderboard(data.entries);
        });
        
        this.network.on('score_submitted', (data) => {
            this.menu.updateLeaderboard(data.leaderboard);
            if (data.rank) {
                console.log(`Score submitted! Rank: #${data.rank}`);
            }
        });
        
        // Snake Game events
        this.network.on('game_starting', async (data) => {
            await this.startGame();
            
            // Apply initial state immediately so map renders before countdown starts
            if (this.game && data.initial_state) {
                this.game.updateState(data.initial_state);
            }
            
            // Start the engine so it keeps re-rendering during the countdown
            if (this.game) {
                this.game.start();
            }
            
            // Show countdown — fully transparent overlay so map is 100% visible
            this.hud.animateCountdown(
                () => { this.sound.play('go'); },
                () => this.sound.play('countdown')
            );
        });
        
        this.network.on('game_start', (data) => {
            if (this.game) {
                this.game.updateState(data.state);
            }
        });
        
        this.network.on('game_state', (data) => {
            if (this.game) {
                this.game.updateState(data.state);
            }
        });
        
        this.network.on('player_died', (data) => {
            if (this.game && this.game.onPlayerDeath) {
                this.game.onPlayerDeath(data.player_id);
            }
            this.sound.play('death');
        });
        
        this.network.on('game_over', (data) => {
            if (this.game) {
                this.game.onGameOver(data.winner_id, data.final_state);
            }
            // Play win sound if we won
            if (data.winner_id === this.playerId) {
                this.sound.play('win');
            }
            
            // Submit score to leaderboard for all Snake game modes
            if (this.currentRoom && this.currentRoom.game_type !== 'brawler') {
                const playerState = data.final_state?.players?.[this.playerId];
                if (playerState && playerState.snake && playerState.snake.score > 0) {
                    const playerName = this.menu.getPlayerName();
                    const gameType = this.currentRoom.game_type || 'snake_classic';
                    const gameMode = this.currentRoom.game_mode || 'single_player';
                    this.network.submitScore(playerName, playerState.snake.score, gameType, gameMode);
                }
            }
        });
        
        // Brawler Game events
        this.network.on('brawler_game_starting', async (data) => {
            await this.startBrawlerGame();
            
            // Brawler game handles its own countdown internally
            if (this.game) {
                this.game.start();
            }
        });
        
        this.network.on('brawler_game_state', (data) => {
            if (this.game) {
                this.game.updateState(data.state);
            }
        });
        
        this.network.on('brawler_game_over', (data) => {
            if (this.game) {
                this.game.onGameOver(data.winner_team, data.state);
            }
        });
        
        // Profile events
        this.network.on('profile_data', (data) => {
            this._onProfileData(data);
        });
        this.network.on('profile_reset', (data) => {
            this._onProfileData(data);
        });

        // Error handling
        this.network.on('error', (data) => {
            this.showError(data.message);
        });
    }
    
    /**
     * Show lobby screen
     * @param {boolean} isNewRoom - True if this is a newly created/joined room
     */
    showLobby(isNewRoom = true) {
        this.menu.hide();
        this.hideGame();

        // Show appropriate lobby based on game type
        if (this.currentRoom?.game_type === 'brawler') {
            this.lobby.hide();
            this.brawlerLobby.show(this.currentRoom, this.playerId);
            this.currentScreen = 'brawler-lobby';
        } else {
            this.brawlerLobby.hide();
            this.lobby.show(this.currentRoom, this.playerId, isNewRoom);
            this.currentScreen = 'lobby';
        }
    }
    
    /**
     * Show menu screen
     */
    showMenu() {
        this.lobby.hide();
        this.brawlerLobby.hide();
        this.hideGame();
        this.menu.show();
        this.currentScreen = 'menu';
    }
    
    /**
     * Start the game
     */
    async startGame() {
        // Reset HUD state (clears survival pressure, speed indicator, etc. from previous game)
        this.hud.reset();
        
        this.lobby.hide();
        this.menu.hide();
        
        // Show game screen
        const gameScreen = document.getElementById('game-screen');
        gameScreen.classList.remove('hidden');
        gameScreen.classList.add('active');
        
        // Show animal legend for snake games
        const animalLegend = document.getElementById('animal-legend');
        if (animalLegend) {
            animalLegend.classList.remove('hidden');
        }
        
        // Get or recreate canvas to ensure clean WebGL context
        let canvas = document.getElementById('game-canvas');
        
        // Recreate canvas to ensure fresh WebGL context
        if (canvas) {
            const parent = canvas.parentNode;
            const newCanvas = document.createElement('canvas');
            newCanvas.id = 'game-canvas';
            parent.replaceChild(newCanvas, canvas);
            canvas = newCanvas;
        }
        
        this.renderer = new Renderer(canvas);
        
        // Create appropriate game based on type
        const gameType = this.currentRoom.game_type;
        
        if (gameType === 'snake_3d') {
            this.game = new Snake3DGame(this.renderer, this.input, this.network, this.hud, this.sound);
        } else {
            this.game = new SnakeGame(this.renderer, this.input, this.network, this.hud, this.sound);
        }
        
        await this.game.init(this.playerId);
    }
    
    /**
     * Start the brawler game
     */
    async startBrawlerGame() {
        this.brawlerLobby.hide();
        this.menu.hide();
        
        // Show game screen
        const gameScreen = document.getElementById('game-screen');
        gameScreen.classList.remove('hidden');
        gameScreen.classList.add('active');
        
        // Hide animal legend for brawler games
        const animalLegend = document.getElementById('animal-legend');
        if (animalLegend) {
            animalLegend.classList.add('hidden');
        }
        
        // Get or recreate canvas to ensure clean WebGL context
        let canvas = document.getElementById('game-canvas');
        
        // Recreate canvas to ensure fresh WebGL context
        if (canvas) {
            const parent = canvas.parentNode;
            const newCanvas = document.createElement('canvas');
            newCanvas.id = 'game-canvas';
            parent.replaceChild(newCanvas, canvas);
            canvas = newCanvas;
        }
        
        this.renderer = new Renderer(canvas);
        
        // Create brawler game
        this.game = new BrawlerGame(this.renderer, this.input, this.network, this.hud, this.sound);
        
        await this.game.init(this.playerId);
        
        this.currentScreen = 'game';
    }
    
    /**
     * Hide game screen
     */
    hideGame() {
        const gameScreen = document.getElementById('game-screen');
        gameScreen.classList.remove('active');
        gameScreen.classList.add('hidden');
        
        // Hide animal legend
        const animalLegend = document.getElementById('animal-legend');
        if (animalLegend) {
            animalLegend.classList.add('hidden');
        }
        
        if (this.game) {
            if (this.game.stop) {
                this.game.stop();
            } else if (this.game.destroy) {
                this.game.destroy();
            }
            this.game = null;
        }
        
        if (this.renderer) {
            this.renderer.destroy();
            this.renderer = null;
        }
        
        this.hud.reset();
    }
    
    /**
     * Go back to lobby from game
     */
    backToLobby() {
        this.hideGame();
        
        // If room still exists, go to lobby
        if (this.currentRoom) {
            // Notify server to reset room state
            this.network.returnToLobby();
            
            // Show lobby (room state will be updated via room_reset event)
            // Pass false to prevent auto-start in single player mode
            this.showLobby(false);
            
            // Handle ready state for snake games
            if (this.currentRoom.game_type !== 'brawler') {
                // Auto-ready when returning to lobby if it's a solo/AI game
                const isAutoReady = this.lobby.shouldAutoReady();
                if (isAutoReady) {
                    // Small delay to let server process room reset first
                    setTimeout(() => {
                        this.network.setReady(true);
                        this.lobby.isReady = true;
                    }, 200);
                } else {
                    // Reset ready state locally for multiplayer
                    this.lobby.isReady = false;
                    this.lobby.btnReady.textContent = 'Ready';
                    this.lobby.btnReady.classList.remove('btn-secondary');
                    this.lobby.btnReady.classList.add('btn-primary');
                }
            }
        } else {
            this.showMenu();
        }
    }
    
    /**
     * Setup the profile modal and lobby profile button
     */
    setupProfileModal() {
        this._profileAIToggle = false;

        // Lobby profile button
        const btnLobbyProfile = document.getElementById('btn-lobby-profile');
        if (btnLobbyProfile) {
            btnLobbyProfile.addEventListener('click', () => {
                const name = this.menu.getPlayerName();
                if (!name || name.length < 2) { this.showError('Enter a name first.'); return; }
                this.network.send({ type: 'get_profile', player_name: name });
            });
        }

        // AI-only toggle inside modal
        const aiToggle = document.getElementById('profile-ai-toggle');
        if (aiToggle) {
            aiToggle.addEventListener('change', () => {
                this._profileAIToggle = aiToggle.checked;
                if (this._lastProfileData) this._renderProfileModal(this._lastProfileData);
            });
        }

        // Reset button (double-click to confirm)
        const btnReset = document.getElementById('btn-profile-reset');
        if (btnReset) {
            btnReset.addEventListener('click', () => {
                if (!btnReset.classList.contains('confirm')) {
                    btnReset.classList.add('confirm');
                    btnReset.textContent = 'Confirm Reset?';
                    setTimeout(() => {
                        btnReset.classList.remove('confirm');
                        btnReset.textContent = 'Reset Stats';
                    }, 3000);
                } else {
                    const name = this.menu.getPlayerName();
                    this.network.send({ type: 'reset_profile', player_name: name });
                    btnReset.classList.remove('confirm');
                    btnReset.textContent = 'Reset Stats';
                }
            });
        }

        // Close button
        const btnClose = document.getElementById('btn-profile-close');
        if (btnClose) {
            btnClose.addEventListener('click', () => {
                document.getElementById('profile-modal').classList.add('hidden');
            });
        }
    }

    /**
     * Setup new/existing player indicator on the home page name input
     */
    setupPlayerNameCheck() {
        const input = document.getElementById('player-name');
        const label = document.getElementById('player-status-label');
        if (!input || !label) return;

        let debounceTimer = null;
        input.addEventListener('input', () => {
            const name = input.value.trim();
            if (name.length < 2) {
                label.className = 'player-status-label hidden';
                return;
            }
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(async () => {
                try {
                    const res = await fetch(`/profile/${encodeURIComponent(name)}`);
                    const data = await res.json();
                    if (data.exists) {
                        label.textContent = '✓ Existing Player';
                        label.className = 'player-status-label existing-player';
                    } else {
                        label.textContent = '★ New Player';
                        label.className = 'player-status-label new-player';
                    }
                } catch {
                    label.className = 'player-status-label hidden';
                }
            }, 400);
        });
    }

    /**
     * Handle incoming profile data from server
     */
    _onProfileData(data) {
        this._lastProfileData = data;
        const modal = document.getElementById('profile-modal');
        if (modal) {
            modal.classList.remove('hidden');
            this._renderProfileModal(data);
        }
    }

    /**
     * Render the profile modal contents
     */
    _renderProfileModal(data) {
        const aiOnly = this._profileAIToggle;
        const profile = data.profile;

        document.getElementById('profile-name-header').textContent = data.player_name;

        const noData = document.getElementById('profile-no-data');
        const statsEl = document.getElementById('profile-stats');

        if (!profile || profile.total_games === 0) {
            noData.classList.remove('hidden');
            statsEl.style.display = 'none';
            document.getElementById('profile-registered-date').textContent = profile
                ? `Registered: ${profile.registered_at}` : '';
            return;
        }

        noData.classList.add('hidden');
        statsEl.style.display = '';

        const games = aiOnly ? profile.total_games : profile.games_vs_humans || (profile.total_games - profile.games_vs_ai_only);
        const wins  = aiOnly ? profile.total_wins  : profile.wins_vs_humans  || (profile.total_wins  - profile.wins_vs_ai_only);
        const winPct = games > 0 ? (wins / games * 100).toFixed(1) : '0.0';

        document.getElementById('stat-total-games').textContent = games;
        document.getElementById('stat-total-wins').textContent  = wins;
        document.getElementById('stat-win-pct').textContent     = `${winPct}%`;

        // Per-mode breakdown
        const modeLabels = {
            survival: 'Survival',
            high_score: 'High Score',
            battle_royale: 'Battle Royale',
            single_player: 'Solo Practice',
        };
        const modeStats = document.getElementById('profile-mode-stats');
        modeStats.innerHTML = '';
        for (const [mode, label] of Object.entries(modeLabels)) {
            const mg = profile.games_by_mode?.[mode] || 0;
            const mw = profile.wins_by_mode?.[mode]  || 0;
            if (mg === 0) continue;
            const row = document.createElement('div');
            row.className = 'profile-mode-row';
            row.innerHTML = `
                <span class="profile-mode-label">${label}</span>
                <span class="profile-mode-val">${mw}W / ${mg}G (${mg > 0 ? (mw/mg*100).toFixed(0) : 0}%)</span>
            `;
            modeStats.appendChild(row);
        }

        // Best scores
        const bestScores = document.getElementById('profile-best-scores');
        bestScores.innerHTML = '';
        for (const [mode, label] of Object.entries(modeLabels)) {
            const best = profile.highest_score_by_mode?.[mode] || 0;
            if (best === 0) continue;
            const row = document.createElement('div');
            row.className = 'profile-mode-row';
            row.innerHTML = `
                <span class="profile-mode-label">${label}</span>
                <span class="profile-mode-val" style="color:#F59E0B;font-weight:600">${best.toLocaleString()}</span>
            `;
            bestScores.appendChild(row);
        }

        document.getElementById('profile-registered-date').textContent =
            `Member since ${profile.registered_at}`;
    }

    /**
     * Show error message
     */
    showError(message) {
        const toast = document.getElementById('error-toast');
        const toastMessage = toast.querySelector('.toast-message');
        toastMessage.textContent = message;
        toast.classList.remove('hidden');
        
        setTimeout(() => {
            toast.classList.add('hidden');
        }, 3000);
    }
}

// Start the application
const app = new App();
app.init().catch(console.error);
