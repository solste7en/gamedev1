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
        this.leaderboardPagination = document.getElementById('leaderboard-pagination');
        this.btnLbPrev = document.getElementById('btn-lb-prev');
        this.btnLbNext = document.getElementById('btn-lb-next');
        this.lbPageInfo = document.getElementById('lb-page-info');
        
        // Leaderboard pagination state
        this._lbEntries = [];
        this._lbPage = 0;
        this._lbPageSize = 50;
        this._lbShowUnique = false;
        this.lbUniqueToggle = document.getElementById('lb-unique-toggle');
        
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
        this.btnLbPrev.addEventListener('click', () => {
            if (this._lbPage > 0) { this._lbPage--; this._renderLeaderboardPage(); }
        });
        this.btnLbNext.addEventListener('click', () => {
            const maxPage = Math.ceil(this._getFilteredEntries().length / this._lbPageSize) - 1;
            if (this._lbPage < maxPage) { this._lbPage++; this._renderLeaderboardPage(); }
        });
        if (this.lbUniqueToggle) {
            this.lbUniqueToggle.addEventListener('change', (e) => {
                this._lbShowUnique = e.target.checked;
                this._lbPage = 0;  // Reset to first page on filter change
                this._renderLeaderboardPage();
            });
        }
        
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
            const gameModeText = room.game_mode === 'survival' ? 'Survival' : 
                                 room.game_mode === 'battle_royale' ? 'Battle Royale' : 'High Score';
            
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
            if (this.leaderboardPagination) this.leaderboardPagination.classList.add('hidden');
        } else {
            this.leaderboardList.innerHTML = '<div class="loading">Loading...</div>';
            if (this.leaderboardPagination) this.leaderboardPagination.classList.add('hidden');
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
            'high_score': 'High Score',
            'battle_royale': 'Battle Royale'
        };
        return modeNames[mode] || mode || 'Solo';
    }
    
    /**
     * Update leaderboard display — stores all entries and renders page 1
     */
    updateLeaderboard(entries) {
        if (!entries || entries.length === 0) {
            this.leaderboardList.innerHTML = '<div class="leaderboard-empty">No scores yet. Be the first!</div>';
            if (this.leaderboardPagination) this.leaderboardPagination.classList.add('hidden');
            return;
        }
        
        this._lbEntries = entries;
        this._lbPage = 0;
        if (this.leaderboardPagination) this.leaderboardPagination.classList.remove('hidden');
        this._renderLeaderboardPage();
    }
    
    /**
     * Return entries filtered by the current toggle state
     */
    _getFilteredEntries() {
        if (!this._lbShowUnique) return this._lbEntries;
        // Keep only the highest score per unique player name (already sorted desc)
        const seen = new Set();
        return this._lbEntries.filter(e => {
            const key = e.player_name.toLowerCase().trim();
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
        });
    }
    
    /**
     * Render the current leaderboard page
     */
    _renderLeaderboardPage() {
        const entries = this._getFilteredEntries();
        const pageSize = this._lbPageSize;
        const totalPages = Math.max(1, Math.ceil(entries.length / pageSize));
        const page = this._lbPage;
        const start = page * pageSize;
        const pageEntries = entries.slice(start, start + pageSize);
        
        this.leaderboardList.innerHTML = '';
        
        pageEntries.forEach((entry, localIdx) => {
            const rank = start + localIdx + 1;
            const item = document.createElement('div');
            item.className = 'leaderboard-entry';
            
            // Expanded color tiers
            if (rank <= 3) {
                item.classList.add('rank-top3');
            } else if (rank <= 10) {
                item.classList.add('rank-top10');
            } else if (rank <= 30) {
                item.classList.add('rank-top30');
            } else if (rank <= 50) {
                item.classList.add('rank-top50');
            } else if (rank <= 100) {
                item.classList.add('rank-top100');
            }
            
            const gameMode = this.formatGameMode(entry.game_mode);
            const medal = rank === 1 ? '🥇' : rank === 2 ? '🥈' : rank === 3 ? '🥉' : '';
            
            item.innerHTML = `
                <span class="entry-rank">${medal || '#' + rank}</span>
                <span class="entry-name">${this.escapeHtml(entry.player_name)}</span>
                <span class="entry-mode">${gameMode}</span>
                <span class="entry-score">${entry.score.toLocaleString()}</span>
                <span class="entry-date">${entry.date}</span>
            `;
            
            this.leaderboardList.appendChild(item);
        });
        
        // Update pagination controls
        this.lbPageInfo.textContent = `Page ${page + 1} / ${totalPages}`;
        this.btnLbPrev.disabled = page === 0;
        this.btnLbNext.disabled = page >= totalPages - 1;
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
