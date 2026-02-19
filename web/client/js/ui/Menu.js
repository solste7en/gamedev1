/**
 * Menu - Main menu UI controller
 */

export class Menu {
    constructor(networkManager) {
        this.network = networkManager;
        this.playerName = '';
        
        this.bindElements();
        this.setupEventListeners();
        this.loadSavedName();
    }
    
    /**
     * Bind DOM elements
     */
    bindElements() {
        // Screens
        this.menuScreen = document.getElementById('menu-screen');
        this.browseScreen = document.getElementById('browse-screen');
        this.joinModal = document.getElementById('join-modal');
        
        // Inputs
        this.playerNameInput = document.getElementById('player-name');
        this.roomCodeInput = document.getElementById('room-code-input');
        
        // Buttons
        this.btnSinglePlayer = document.getElementById('btn-single-player');
        this.btnJoinRoom = document.getElementById('btn-join-room');
        this.btnBrowseRooms = document.getElementById('btn-browse-rooms');
        this.btnLeaderboard = document.getElementById('btn-leaderboard');
        this.btnJoinConfirm = document.getElementById('btn-join-confirm');
        this.btnJoinCancel = document.getElementById('btn-join-cancel');
        this.btnRefreshRooms = document.getElementById('btn-refresh-rooms');
        this.btnBackMenu = document.getElementById('btn-back-menu');
        
        // Leaderboard modal
        this.leaderboardModal = document.getElementById('leaderboard-modal');
        this.leaderboardList = document.getElementById('leaderboard-list');
        this.btnLeaderboardClose = document.getElementById('btn-leaderboard-close');
        
        // Lists
        this.roomList = document.getElementById('room-list');
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Name input
        this.playerNameInput.addEventListener('input', (e) => {
            this.playerName = e.target.value.trim();
            localStorage.setItem('playerName', this.playerName);
        });
        
        // Menu buttons
        this.btnSinglePlayer.addEventListener('click', () => this.createRoom());
        this.btnJoinRoom.addEventListener('click', () => this.showJoinModal());
        this.btnBrowseRooms.addEventListener('click', () => this.showBrowseScreen());
        this.btnLeaderboard.addEventListener('click', () => this.showLeaderboard());
        
        // Leaderboard modal
        this.btnLeaderboardClose.addEventListener('click', () => this.hideLeaderboard());
        
        // Join modal
        this.btnJoinConfirm.addEventListener('click', () => this.joinRoom());
        this.btnJoinCancel.addEventListener('click', () => this.hideJoinModal());
        this.roomCodeInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.joinRoom();
        });
        
        // Browse screen
        this.btnRefreshRooms.addEventListener('click', () => this.refreshRooms());
        this.btnBackMenu.addEventListener('click', () => this.showMenuScreen());
    }
    
    /**
     * Get currently selected game type
     */
    getSelectedGame() {
        const brawlerBtn = document.getElementById('btn-brawler-game');
        if (brawlerBtn && brawlerBtn.classList.contains('selected')) {
            return 'brawler';
        }
        return 'snake';
    }
    
    /**
     * Start single player mode
     */
    startSinglePlayer() {
        const name = this.getPlayerName();
        const selectedGame = this.getSelectedGame();
        
        if (selectedGame === 'brawler') {
            this.network.createRoom(name, 'brawler', 'single_player');
        } else {
            this.network.createRoom(name, 'snake_classic', 'single_player');
        }
    }
    
    /**
     * Load saved player name
     */
    loadSavedName() {
        const savedName = localStorage.getItem('playerName');
        if (savedName) {
            this.playerName = savedName;
            this.playerNameInput.value = savedName;
        } else {
            // Generate random name
            this.playerName = `Player${Math.floor(Math.random() * 1000)}`;
            this.playerNameInput.value = this.playerName;
        }
    }
    
    /**
     * Get validated player name
     */
    getPlayerName() {
        const name = this.playerNameInput.value.trim();
        if (!name) {
            return `Player${Math.floor(Math.random() * 1000)}`;
        }
        return name.substring(0, 12);
    }
    
    /**
     * Create a new room
     */
    createRoom() {
        const name = this.getPlayerName();
        const selectedGame = this.getSelectedGame();
        
        if (selectedGame === 'brawler') {
            this.network.createRoom(name, 'brawler', 'survival');
        } else {
            this.network.createRoom(name, 'snake_classic', 'survival');
        }
    }
    
    /**
     * Show join modal
     */
    showJoinModal() {
        this.joinModal.classList.remove('hidden');
        this.roomCodeInput.value = '';
        this.roomCodeInput.focus();
    }
    
    /**
     * Hide join modal
     */
    hideJoinModal() {
        this.joinModal.classList.add('hidden');
    }
    
    /**
     * Join a room by code
     */
    joinRoom() {
        const code = this.roomCodeInput.value.trim().toUpperCase();
        if (!code) {
            this.showError('Please enter a room code');
            return;
        }
        
        const name = this.getPlayerName();
        this.network.joinRoom(code, name);
        this.hideJoinModal();
    }
    
    /**
     * Join room from browse list
     */
    joinRoomFromList(roomCode) {
        const name = this.getPlayerName();
        this.network.joinRoom(roomCode, name);
    }
    
    /**
     * Show browse screen
     */
    showBrowseScreen() {
        this.menuScreen.classList.remove('active');
        this.menuScreen.classList.add('hidden');
        this.browseScreen.classList.remove('hidden');
        this.browseScreen.classList.add('active');
        this.refreshRooms();
    }
    
    /**
     * Show menu screen
     */
    showMenuScreen() {
        this.browseScreen.classList.remove('active');
        this.browseScreen.classList.add('hidden');
        this.menuScreen.classList.remove('hidden');
        this.menuScreen.classList.add('active');
    }
    
    /**
     * Refresh room list
     */
    refreshRooms() {
        this.roomList.innerHTML = '<div class="loading">Searching for rooms...</div>';
        this.network.listRooms();
    }
    
    /**
     * Update room list display
     */
    updateRoomList(rooms) {
        if (!rooms || rooms.length === 0) {
            this.roomList.innerHTML = '<div class="loading">No rooms available. Create one!</div>';
            return;
        }
        
        this.roomList.innerHTML = '';
        
        rooms.forEach(room => {
            const item = document.createElement('div');
            item.className = 'room-item';
            
            const gameTypeText = room.game_type === 'snake_classic' ? 'Snake Classic' : 'Snake 3D';
            const gameModeText = room.game_mode === 'survival' ? 'Survival' : 'High Score';
            
            item.innerHTML = `
                <div class="room-info">
                    <h3>${room.code}</h3>
                    <span>${gameTypeText} - ${gameModeText} | ${room.player_count}/${room.max_players} players</span>
                </div>
                <button class="btn btn-primary btn-small">Join</button>
            `;
            
            const joinBtn = item.querySelector('button');
            joinBtn.addEventListener('click', () => this.joinRoomFromList(room.code));
            
            this.roomList.appendChild(item);
        });
    }
    
    /**
     * Show error toast
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
    
    /**
     * Show the menu
     */
    show() {
        this.showMenuScreen();
    }
    
    /**
     * Hide the menu
     */
    hide() {
        this.menuScreen.classList.remove('active');
        this.menuScreen.classList.add('hidden');
        this.browseScreen.classList.remove('active');
        this.browseScreen.classList.add('hidden');
        this.hideJoinModal();
        this.hideLeaderboard();
    }
    
    /**
     * Show leaderboard modal
     */
    showLeaderboard() {
        this.leaderboardModal.classList.remove('hidden');
        
        const selectedGame = this.getSelectedGame();
        if (selectedGame === 'brawler') {
            // Show "In Development" banner for Brawler
            this.leaderboardList.innerHTML = `
                <div class="leaderboard-banner">
                    <div class="banner-icon">🚧</div>
                    <div class="banner-title">In Development</div>
                    <div class="banner-text">Brawler leaderboard coming soon!</div>
                </div>
            `;
        } else {
            this.leaderboardList.innerHTML = '<div class="loading">Loading...</div>';
            this.network.getLeaderboard();
        }
    }
    
    /**
     * Hide leaderboard modal
     */
    hideLeaderboard() {
        this.leaderboardModal.classList.add('hidden');
    }
    
    /**
     * Format game mode for display
     */
    formatGameMode(mode) {
        const modeNames = {
            'single_player': 'Solo',
            'survival': 'Survival',
            'high_score': 'High Score'
        };
        return modeNames[mode] || mode || 'Solo';
    }
    
    /**
     * Update leaderboard display
     */
    updateLeaderboard(entries) {
        if (!entries || entries.length === 0) {
            this.leaderboardList.innerHTML = '<div class="leaderboard-empty">No scores yet. Be the first!</div>';
            return;
        }
        
        this.leaderboardList.innerHTML = '';
        
        entries.forEach((entry, index) => {
            const rank = index + 1;
            const item = document.createElement('div');
            item.className = 'leaderboard-entry';
            
            // Color coding: 1-3 green (gold), 4-10 blue (silver)
            if (rank <= 3) {
                item.classList.add('rank-gold');
            } else if (rank <= 10) {
                item.classList.add('rank-silver');
            }
            
            const gameMode = this.formatGameMode(entry.game_mode);
            
            item.innerHTML = `
                <span class="entry-rank">#${rank}</span>
                <span class="entry-name">${this.escapeHtml(entry.player_name)}</span>
                <span class="entry-mode">${gameMode}</span>
                <span class="entry-score">${entry.score.toLocaleString()}</span>
                <span class="entry-date">${entry.date}</span>
            `;
            
            this.leaderboardList.appendChild(item);
        });
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

export default Menu;
