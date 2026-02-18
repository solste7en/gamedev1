/**
 * BrawlerLobby - Team and character selection UI for Brawler game
 */

const BRAWLERS = {
    colt: {
        name: 'Colt',
        description: 'Long-range sharpshooter with rapid-fire bullets',
        color: '#4682E6',
        icon: '🔫'
    },
    shelly: {
        name: 'Shelly',
        description: 'Close-range with devastating spread shot',
        color: '#A050B4',
        icon: '💥'
    },
    piper: {
        name: 'Piper',
        description: 'Sniper - damage increases with distance',
        color: '#FF96B4',
        icon: '🎯'
    },
    edgar: {
        name: 'Edgar',
        description: 'Assassin that heals when dealing damage',
        color: '#C83232',
        icon: '⚔️'
    }
};

export class BrawlerLobby {
    constructor(networkManager) {
        this.network = networkManager;
        this.room = null;
        this.playerId = null;
        this.isHost = false;
        this.isReady = false;
        
        this.selectedTeam = null;
        this.selectedCharacter = null;
        
        this.onGameStart = null;
        
        this.bindElements();
        this.setupEventListeners();
    }
    
    /**
     * Bind DOM elements
     */
    bindElements() {
        this.lobbyScreen = document.getElementById('brawler-lobby-screen');
        this.roomCodeDisplay = document.getElementById('brawler-room-code');
        this.playerList = document.getElementById('brawler-player-list');
        
        this.teamBlueBtn = document.getElementById('team-blue-btn');
        this.teamRedBtn = document.getElementById('team-red-btn');
        this.teamBlueCount = document.getElementById('team-blue-count');
        this.teamRedCount = document.getElementById('team-red-count');
        
        this.characterGrid = document.getElementById('character-grid');
        
        this.btnReady = document.getElementById('brawler-btn-ready');
        this.btnStartGame = document.getElementById('brawler-btn-start');
        this.btnLeaveRoom = document.getElementById('brawler-btn-leave');
        this.btnCopyCode = document.getElementById('brawler-btn-copy-code');
    }
    
    /**
     * Setup event listeners
     */
    setupEventListeners() {
        this.teamBlueBtn?.addEventListener('click', () => this.selectTeam(0));
        this.teamRedBtn?.addEventListener('click', () => this.selectTeam(1));
        
        this.btnReady?.addEventListener('click', () => this.toggleReady());
        this.btnStartGame?.addEventListener('click', () => this.startGame());
        this.btnLeaveRoom?.addEventListener('click', () => this.leaveRoom());
        this.btnCopyCode?.addEventListener('click', () => this.copyRoomCode());
    }
    
    /**
     * Show the lobby
     */
    show(room, playerId) {
        this.room = room;
        this.playerId = playerId;
        this.isHost = room.host_id === playerId;
        this.isReady = false;
        this.selectedTeam = room.team_assignments?.[playerId] ?? null;
        this.selectedCharacter = room.character_selections?.[playerId] ?? null;
        
        this.lobbyScreen.classList.remove('hidden');
        this.lobbyScreen.classList.add('active');
        
        this.updateRoomDisplay();
        this.updateTeamButtons();
        this.renderCharacterGrid();
        this.updatePlayerList();
        this.updateButtons();
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
        if (this.roomCodeDisplay) {
            this.roomCodeDisplay.textContent = this.room.code;
        }
    }
    
    /**
     * Update team buttons
     */
    updateTeamButtons() {
        // Count players on each team
        const teamAssignments = this.room.team_assignments || {};
        let blueCount = 0;
        let redCount = 0;
        
        for (const team of Object.values(teamAssignments)) {
            if (team === 0) blueCount++;
            else if (team === 1) redCount++;
        }
        
        if (this.teamBlueCount) {
            this.teamBlueCount.textContent = `${blueCount}/2`;
        }
        if (this.teamRedCount) {
            this.teamRedCount.textContent = `${redCount}/2`;
        }
        
        // Highlight selected team
        if (this.teamBlueBtn) {
            this.teamBlueBtn.classList.toggle('selected', this.selectedTeam === 0);
            this.teamBlueBtn.disabled = blueCount >= 2 && this.selectedTeam !== 0;
        }
        if (this.teamRedBtn) {
            this.teamRedBtn.classList.toggle('selected', this.selectedTeam === 1);
            this.teamRedBtn.disabled = redCount >= 2 && this.selectedTeam !== 1;
        }
    }
    
    /**
     * Render character selection grid
     */
    renderCharacterGrid() {
        if (!this.characterGrid) return;
        
        this.characterGrid.innerHTML = '';
        
        const charSelections = this.room.character_selections || {};
        const teamAssignments = this.room.team_assignments || {};
        
        // Get taken characters on player's team
        const takenOnTeam = new Set();
        for (const [pid, char] of Object.entries(charSelections)) {
            const playerTeam = teamAssignments[pid];
            if (playerTeam === this.selectedTeam && parseInt(pid) !== this.playerId) {
                takenOnTeam.add(char);
            }
        }
        
        for (const [id, brawler] of Object.entries(BRAWLERS)) {
            const card = document.createElement('div');
            card.className = 'character-card';
            
            const isTaken = takenOnTeam.has(id);
            const isSelected = this.selectedCharacter === id;
            
            if (isSelected) card.classList.add('selected');
            if (isTaken) card.classList.add('taken');
            
            card.innerHTML = `
                <div class="character-icon" style="background-color: ${brawler.color}">${brawler.icon}</div>
                <div class="character-name">${brawler.name}</div>
                <div class="character-desc">${brawler.description}</div>
                ${isTaken ? '<div class="taken-label">TAKEN</div>' : ''}
            `;
            
            if (!isTaken) {
                card.addEventListener('click', () => this.selectCharacter(id));
            }
            
            this.characterGrid.appendChild(card);
        }
    }
    
    /**
     * Update player list
     */
    updatePlayerList() {
        if (!this.playerList) return;
        
        this.playerList.innerHTML = '';
        
        const teamAssignments = this.room.team_assignments || {};
        const charSelections = this.room.character_selections || {};
        
        // Group players by team
        const blueTeam = [];
        const redTeam = [];
        const unassigned = [];
        
        for (const player of this.room.players) {
            const team = teamAssignments[player.id];
            const entry = {
                ...player,
                character: charSelections[player.id],
                team: team
            };
            
            if (team === 0) blueTeam.push(entry);
            else if (team === 1) redTeam.push(entry);
            else unassigned.push(entry);
        }
        
        // Render team sections
        this.renderTeamSection('Blue Team', blueTeam, 0);
        this.renderTeamSection('Red Team', redTeam, 1);
        
        if (unassigned.length > 0) {
            this.renderTeamSection('Unassigned', unassigned, -1);
        }
    }
    
    /**
     * Render a team section in the player list
     */
    renderTeamSection(title, players, team) {
        const section = document.createElement('div');
        section.className = 'team-section';
        
        const teamColor = team === 0 ? '#4682E6' : team === 1 ? '#E64646' : '#888888';
        
        section.innerHTML = `
            <div class="team-header" style="color: ${teamColor}">${title}</div>
        `;
        
        for (const player of players) {
            const playerEl = document.createElement('div');
            playerEl.className = 'brawler-player-item';
            
            const charInfo = player.character ? BRAWLERS[player.character] : null;
            const isReady = player.state === 'ready';
            
            playerEl.innerHTML = `
                <span class="player-name">${player.name}${player.id === this.playerId ? ' (You)' : ''}</span>
                <span class="player-character">${charInfo ? charInfo.icon + ' ' + charInfo.name : '?'}</span>
                <span class="player-status ${isReady ? 'ready' : ''}">${isReady ? '✓' : '...'}</span>
            `;
            
            section.appendChild(playerEl);
        }
        
        // Show AI slots if team is not full
        const aiSlots = 2 - players.length;
        for (let i = 0; i < aiSlots; i++) {
            const aiEl = document.createElement('div');
            aiEl.className = 'brawler-player-item ai-slot';
            aiEl.innerHTML = `
                <span class="player-name" style="color: #888;">AI Bot</span>
                <span class="player-character">?</span>
                <span class="player-status">Auto</span>
            `;
            section.appendChild(aiEl);
        }
        
        this.playerList.appendChild(section);
    }
    
    /**
     * Update buttons state
     */
    updateButtons() {
        // Ready button - can only ready if team and character selected
        const canReady = this.selectedTeam !== null && this.selectedCharacter !== null;
        
        if (this.btnReady) {
            this.btnReady.disabled = !canReady;
            this.btnReady.textContent = this.isReady ? 'Not Ready' : 'Ready';
            this.btnReady.classList.toggle('btn-secondary', this.isReady);
            this.btnReady.classList.toggle('btn-primary', !this.isReady);
        }
        
        // Start button - only visible to host when all ready
        if (this.btnStartGame) {
            this.btnStartGame.classList.toggle('hidden', !this.isHost || !this.room.can_start);
        }
    }
    
    /**
     * Select a team
     */
    selectTeam(team) {
        this.selectedTeam = team;
        this.network.send({
            type: 'select_team',
            team: team
        });
        this.updateTeamButtons();
        this.renderCharacterGrid();
        this.updateButtons();
    }
    
    /**
     * Select a character
     */
    selectCharacter(character) {
        if (this.selectedTeam === null) {
            alert('Please select a team first!');
            return;
        }
        
        this.selectedCharacter = character;
        this.network.send({
            type: 'select_character',
            character: character
        });
        this.renderCharacterGrid();
        this.updateButtons();
    }
    
    /**
     * Toggle ready state
     */
    toggleReady() {
        this.isReady = !this.isReady;
        this.network.setReady(this.isReady);
        this.updateButtons();
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
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    }
    
    /**
     * Update room data
     */
    updateRoom(room) {
        this.room = room;
        this.selectedTeam = room.team_assignments?.[this.playerId] ?? this.selectedTeam;
        this.selectedCharacter = room.character_selections?.[this.playerId] ?? this.selectedCharacter;
        
        this.updateTeamButtons();
        this.renderCharacterGrid();
        this.updatePlayerList();
        this.updateButtons();
    }
    
    /**
     * Add system message
     */
    addSystemMessage(message) {
        console.log('[Brawler Lobby]', message);
    }
}

export default BrawlerLobby;
