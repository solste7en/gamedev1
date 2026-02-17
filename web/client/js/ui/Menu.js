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
        this.btnCreateRoom = document.getElementById('btn-create-room');
        this.btnJoinRoom = document.getElementById('btn-join-room');
        this.btnBrowseRooms = document.getElementById('btn-browse-rooms');
        this.btnJoinConfirm = document.getElementById('btn-join-confirm');
        this.btnJoinCancel = document.getElementById('btn-join-cancel');
        this.btnRefreshRooms = document.getElementById('btn-refresh-rooms');
        this.btnBackMenu = document.getElementById('btn-back-menu');
        
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
        this.btnSinglePlayer.addEventListener('click', () => this.startSinglePlayer());
        this.btnCreateRoom.addEventListener('click', () => this.createRoom());
        this.btnJoinRoom.addEventListener('click', () => this.showJoinModal());
        this.btnBrowseRooms.addEventListener('click', () => this.showBrowseScreen());
        
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
     * Start single player mode
     */
    startSinglePlayer() {
        const name = this.getPlayerName();
        this.network.createRoom(name, 'snake_classic', 'single_player');
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
        this.network.createRoom(name, 'snake_classic', 'survival');
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
    }
}

export default Menu;
