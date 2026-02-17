/**
 * Snake Multiplayer - Main Entry Point
 */

import { NetworkManager } from './engine/NetworkManager.js';
import { InputManager } from './engine/InputManager.js';
import { Renderer } from './engine/Renderer.js';
import { SoundManager } from './engine/SoundManager.js';
import { Menu } from './ui/Menu.js';
import { Lobby } from './ui/Lobby.js';
import { HUD } from './ui/HUD.js';
import { SnakeGame } from './game/SnakeGame.js';
import { Snake3DGame } from './game/Snake3DGame.js';

class App {
    constructor() {
        this.network = new NetworkManager();
        this.input = new InputManager();
        this.sound = new SoundManager();
        this.renderer = null;
        this.menu = null;
        this.lobby = null;
        this.hud = null;
        this.game = null;
        
        this.currentScreen = 'menu';
        this.playerId = null;
        this.currentRoom = null;
        
        // Initialize audio on first user interaction
        document.addEventListener('click', () => this.sound.init(), { once: true });
        document.addEventListener('keydown', () => this.sound.init(), { once: true });
    }
    
    /**
     * Initialize the application
     */
    async init() {
        console.log('Snake Multiplayer v0.2.0');
        
        // Initialize UI components
        this.menu = new Menu(this.network);
        this.lobby = new Lobby(this.network);
        this.hud = new HUD();
        
        // Setup network handlers
        this.setupNetworkHandlers();
        
        // Connect to server
        this.network.connect();
        
        // Setup back to lobby handler
        this.hud.onBackLobby(() => this.backToLobby());
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
            this.lobby.playerJoined(data.player, data.room);
            this.sound.play('join');
        });
        
        this.network.on('player_left', (data) => {
            this.lobby.playerLeft(data.player_id, data.room);
        });
        
        this.network.on('player_ready', (data) => {
            this.lobby.updateRoom(data.room);
            this.sound.play('ready');
        });
        
        this.network.on('settings_changed', (data) => {
            this.lobby.updateRoom(data.room);
        });
        
        this.network.on('room_reset', (data) => {
            this.currentRoom = data.room;
            this.lobby.updateRoom(data.room);
        });
        
        this.network.on('room_list', (data) => {
            this.menu.updateRoomList(data.rooms);
        });
        
        this.network.on('chat', (data) => {
            this.lobby.addChatMessage(data.player_name, data.message);
        });
        
        // Game events
        this.network.on('game_starting', async (data) => {
            await this.startGame();
            
            // Show countdown with sound
            this.hud.animateCountdown(
                () => {
                    if (this.game) {
                        this.game.start();
                    }
                    this.sound.play('go');
                },
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
        this.lobby.show(this.currentRoom, this.playerId, isNewRoom);
        this.currentScreen = 'lobby';
    }
    
    /**
     * Show menu screen
     */
    showMenu() {
        this.lobby.hide();
        this.hideGame();
        this.menu.show();
        this.currentScreen = 'menu';
    }
    
    /**
     * Start the game
     */
    async startGame() {
        this.lobby.hide();
        this.menu.hide();
        
        // Show game screen
        const gameScreen = document.getElementById('game-screen');
        gameScreen.classList.remove('hidden');
        gameScreen.classList.add('active');
        
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
        
        this.currentScreen = 'game';
    }
    
    /**
     * Hide game screen
     */
    hideGame() {
        const gameScreen = document.getElementById('game-screen');
        gameScreen.classList.remove('active');
        gameScreen.classList.add('hidden');
        
        if (this.game) {
            this.game.stop();
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
            
            // For single player mode, automatically set ready so player can click Start
            if (this.currentRoom.game_mode === 'single_player') {
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
        } else {
            this.showMenu();
        }
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
