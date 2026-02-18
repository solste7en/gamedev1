/**
 * BrawlerGame - Brawl Ball multiplayer game renderer
 */

import { ParticleSystem } from '../engine/ParticleSystem.js';

// Brawler colors
const BRAWLER_COLORS = {
    colt: { primary: 0x4682E6, secondary: 0x325AAA },
    shelly: { primary: 0xA050B4, secondary: 0x783288 },
    piper: { primary: 0xFF96B4, secondary: 0xDC6488 },
    edgar: { primary: 0xC83232, secondary: 0x961E1E }
};

const TEAM_COLORS = {
    0: { main: 0x4682E6, light: 0x64A0FF, name: 'Blue' },
    1: { main: 0xE64646, light: 0xFF6464, name: 'Red' }
};

export class BrawlerGame {
    constructor(renderer, inputManager, networkManager, hud, soundManager = null) {
        this.renderer = renderer;
        this.input = inputManager;
        this.network = networkManager;
        this.hud = hud;
        this.sound = soundManager;
        
        this.gameState = null;
        this.prevState = null;
        this.playerId = null;
        this.running = false;
        
        // Visual settings
        this.scale = 1;
        this.offsetX = 0;
        this.offsetY = 0;
        
        // Particle system
        this.particles = null;
        
        // Mouse position for aiming
        this.mouseX = 0;
        this.mouseY = 0;
        
        // Movement input
        this.moveX = 0;
        this.moveY = 0;
        
        // Input send interval
        this.lastInputTime = 0;
        this.inputInterval = 50; // ms
    }
    
    /**
     * Initialize the game
     */
    async init(playerId) {
        this.playerId = playerId;
        
        // Setup brawler controls
        this.setupControls();
        
        // Calculate canvas size
        await this.calculateSize();
        
        // Start input loop
        this.startInputLoop();
        
        return this;
    }
    
    /**
     * Setup keyboard and mouse controls
     */
    setupControls() {
        // WASD movement
        document.addEventListener('keydown', (e) => {
            if (!this.running) return;
            
            switch (e.key.toLowerCase()) {
                case 'w': this.moveY = -1; break;
                case 's': this.moveY = 1; break;
                case 'a': this.moveX = -1; break;
                case 'd': this.moveX = 1; break;
                case 'e':
                    this.network.send({
                        type: 'brawler_input',
                        action: 'ability',
                        aim_x: this.screenToWorldX(this.mouseX),
                        aim_y: this.screenToWorldY(this.mouseY)
                    });
                    break;
            }
        });
        
        document.addEventListener('keyup', (e) => {
            switch (e.key.toLowerCase()) {
                case 'w': if (this.moveY < 0) this.moveY = 0; break;
                case 's': if (this.moveY > 0) this.moveY = 0; break;
                case 'a': if (this.moveX < 0) this.moveX = 0; break;
                case 'd': if (this.moveX > 0) this.moveX = 0; break;
            }
        });
        
        // Mouse tracking
        const canvas = document.getElementById('game-canvas');
        
        canvas.addEventListener('mousemove', (e) => {
            const rect = canvas.getBoundingClientRect();
            this.mouseX = e.clientX - rect.left;
            this.mouseY = e.clientY - rect.top;
        });
        
        // Attack on click
        canvas.addEventListener('mousedown', (e) => {
            if (!this.running) return;
            
            if (e.button === 0) { // Left click
                this.network.send({
                    type: 'brawler_input',
                    action: 'attack',
                    aim_x: this.screenToWorldX(this.mouseX),
                    aim_y: this.screenToWorldY(this.mouseY)
                });
            } else if (e.button === 2) { // Right click
                this.network.send({
                    type: 'brawler_input',
                    action: 'ability',
                    aim_x: this.screenToWorldX(this.mouseX),
                    aim_y: this.screenToWorldY(this.mouseY)
                });
            }
        });
        
        // Prevent context menu
        canvas.addEventListener('contextmenu', (e) => e.preventDefault());
    }
    
    /**
     * Start the input sending loop
     */
    startInputLoop() {
        setInterval(() => {
            if (!this.running) return;
            
            const now = Date.now();
            if (now - this.lastInputTime < this.inputInterval) return;
            this.lastInputTime = now;
            
            // Send movement
            if (this.moveX !== 0 || this.moveY !== 0) {
                this.network.send({
                    type: 'brawler_input',
                    action: 'move',
                    x: this.moveX,
                    y: this.moveY
                });
            }
            
            // Send aim direction
            this.network.send({
                type: 'brawler_input',
                action: 'aim',
                x: this.screenToWorldX(this.mouseX),
                y: this.screenToWorldY(this.mouseY)
            });
            
        }, 16); // ~60fps
    }
    
    /**
     * Convert screen X to world X
     */
    screenToWorldX(screenX) {
        return (screenX - this.offsetX) / this.scale;
    }
    
    /**
     * Convert screen Y to world Y
     */
    screenToWorldY(screenY) {
        return (screenY - this.offsetY) / this.scale;
    }
    
    /**
     * Convert world X to screen X
     */
    worldToScreenX(worldX) {
        return worldX * this.scale + this.offsetX;
    }
    
    /**
     * Convert world Y to screen Y
     */
    worldToScreenY(worldY) {
        return worldY * this.scale + this.offsetY;
    }
    
    /**
     * Calculate and set renderer size
     */
    async calculateSize() {
        const width = 900;
        const height = 650;
        
        const canvas = document.getElementById('game-canvas');
        canvas.width = width;
        canvas.height = height;
        
        if (!this.renderer.app) {
            await this.renderer.init(width, height);
        } else {
            this.renderer.resize(width, height);
        }
        
        // Initialize particle system
        this.particles = new ParticleSystem(this.renderer.effectsContainer);
        
        // Calculate scale to fit arena
        this.updateScale(672, 480); // Default arena size
    }
    
    /**
     * Update scale based on arena size
     */
    updateScale(arenaWidth, arenaHeight) {
        const canvas = document.getElementById('game-canvas');
        const padding = 50;
        
        const scaleX = (canvas.width - padding * 2) / arenaWidth;
        const scaleY = (canvas.height - padding * 2) / arenaHeight;
        this.scale = Math.min(scaleX, scaleY);
        
        // Center the arena
        this.offsetX = (canvas.width - arenaWidth * this.scale) / 2;
        this.offsetY = (canvas.height - arenaHeight * this.scale) / 2;
    }
    
    /**
     * Start the game
     */
    start() {
        this.running = true;
    }
    
    /**
     * Update game state from server
     */
    updateState(state) {
        const firstUpdate = !this.gameState;
        this.prevState = this.gameState;
        this.gameState = state;
        
        if (firstUpdate) {
            this.updateScale(state.arena_width, state.arena_height);
        }
        
        // Detect changes for effects
        this.detectChanges();
        
        // Update particles
        if (this.particles) {
            this.particles.update();
        }
        
        this.render();
        this.updateHUD();
    }
    
    /**
     * Detect state changes for effects
     */
    detectChanges() {
        if (!this.prevState || !this.gameState) return;
        
        // Check for goals
        if (this.gameState.phase === 'goal_scored' && this.prevState.phase === 'playing') {
            if (this.sound) this.sound.play('goal');
        }
        
        // Check for damage
        for (const [fighterId, fighter] of Object.entries(this.gameState.fighters)) {
            const prevFighter = this.prevState.fighters[fighterId];
            if (prevFighter && fighter.health < prevFighter.health) {
                // Damage effect
                const screenX = this.worldToScreenX(fighter.position.x);
                const screenY = this.worldToScreenY(fighter.position.y);
                if (this.particles) {
                    this.particles.emit(screenX, screenY, 0xFF0000, 5);
                }
                if (this.sound) this.sound.play('hit');
            }
        }
    }
    
    /**
     * Render the game
     */
    render() {
        if (!this.gameState) return;
        
        this.renderer.clear();
        
        // Draw arena
        this.drawArena();
        
        // Draw walls
        this.drawWalls();
        
        // Draw goals
        this.drawGoals();
        
        // Draw ball
        this.drawBall();
        
        // Draw fighters
        this.drawFighters();
        
        // Draw projectiles
        this.drawProjectiles();
        
        // Draw phase overlays
        this.drawPhaseOverlay();
    }
    
    /**
     * Draw the arena floor
     */
    drawArena() {
        const state = this.gameState;
        
        // Floor
        this.renderer.drawRect(
            this.offsetX, this.offsetY,
            state.arena_width * this.scale,
            state.arena_height * this.scale,
            0xDCB478 // Sand color
        );
        
        // Center line
        const centerX = this.worldToScreenX(state.arena_width / 2);
        this.renderer.drawRect(
            centerX - 2, this.offsetY,
            4, state.arena_height * this.scale,
            0xFFFFFF, 0.5
        );
        
        // Center circle
        this.renderer.drawCircle(
            centerX,
            this.worldToScreenY(state.arena_height / 2),
            50 * this.scale,
            0xFFFFFF, 0.3
        );
    }
    
    /**
     * Draw walls
     */
    drawWalls() {
        for (const wall of this.gameState.walls) {
            this.renderer.drawRect(
                this.worldToScreenX(wall.x),
                this.worldToScreenY(wall.y),
                wall.width * this.scale,
                wall.height * this.scale,
                0x8C6440
            );
        }
    }
    
    /**
     * Draw goals
     */
    drawGoals() {
        for (const [team, goal] of Object.entries(this.gameState.goals)) {
            const color = team === '0' ? 0x3264C8 : 0xC83232;
            
            // Goal area
            this.renderer.drawRect(
                this.worldToScreenX(goal.x),
                this.worldToScreenY(goal.y),
                goal.width * this.scale,
                goal.height * this.scale,
                color, 0.5
            );
            
            // Goal net lines
            const netColor = team === '0' ? 0x1E4696 : 0x961E1E;
            const x = this.worldToScreenX(goal.x);
            const y = this.worldToScreenY(goal.y);
            const w = goal.width * this.scale;
            const h = goal.height * this.scale;
            
            for (let i = 0; i < 4; i++) {
                this.renderer.drawRect(
                    x + (w / 4) * i, y,
                    2, h,
                    netColor, 0.8
                );
            }
        }
    }
    
    /**
     * Draw the ball
     */
    drawBall() {
        const ball = this.gameState.ball;
        if (!ball) return;
        
        const x = this.worldToScreenX(ball.position.x);
        const y = this.worldToScreenY(ball.position.y);
        const radius = 18 * this.scale;
        
        // Ball shadow
        this.renderer.drawCircle(x + 3, y + 3, radius, 0x000000, 0.3);
        
        // Ball
        this.renderer.drawCircle(x, y, radius, 0xFFFFFF);
        
        // Ball pattern
        this.renderer.drawCircle(x - 5 * this.scale, y - 3 * this.scale, 
                                  5 * this.scale, 0x323232, 0.5);
        this.renderer.drawCircle(x + 4 * this.scale, y + 4 * this.scale, 
                                  4 * this.scale, 0x323232, 0.5);
    }
    
    /**
     * Draw all fighters
     */
    drawFighters() {
        // Sort by Y position for proper layering
        const fighters = Object.values(this.gameState.fighters)
            .sort((a, b) => a.position.y - b.position.y);
        
        for (const fighter of fighters) {
            this.drawFighter(fighter);
        }
    }
    
    /**
     * Draw a single fighter
     */
    drawFighter(fighter) {
        if (!fighter.is_alive) return;
        
        const x = this.worldToScreenX(fighter.position.x);
        const y = this.worldToScreenY(fighter.position.y);
        const radius = 20 * this.scale;
        
        const brawlerColors = BRAWLER_COLORS[fighter.brawler_type] || BRAWLER_COLORS.colt;
        const teamColor = TEAM_COLORS[fighter.team] || TEAM_COLORS[0];
        
        // Shadow
        this.renderer.drawCircle(x + 2, y + 4, radius, 0x000000, 0.3);
        
        // Team ring
        this.renderer.drawCircle(x, y, radius + 4 * this.scale, teamColor.main, 0.7);
        
        // Body
        this.renderer.drawCircle(x, y, radius, brawlerColors.primary);
        
        // Invulnerability effect
        if (fighter.invulnerable) {
            this.renderer.drawCircle(x, y, radius + 2, 0xFFFFFF, 0.5);
        }
        
        // Facing indicator (small arrow)
        const facingX = x + Math.cos(fighter.facing_angle) * radius * 1.3;
        const facingY = y + Math.sin(fighter.facing_angle) * radius * 1.3;
        this.renderer.drawCircle(facingX, facingY, 5 * this.scale, brawlerColors.secondary);
        
        // Health bar
        const healthBarWidth = 40 * this.scale;
        const healthBarHeight = 6 * this.scale;
        const healthPercent = fighter.health / fighter.max_health;
        
        // Background
        this.renderer.drawRect(
            x - healthBarWidth / 2, y - radius - 15 * this.scale,
            healthBarWidth, healthBarHeight,
            0x282828
        );
        
        // Health
        const healthColor = healthPercent > 0.6 ? 0x50C850 : 
                           healthPercent > 0.3 ? 0xDCC832 : 0xDC3C3C;
        this.renderer.drawRect(
            x - healthBarWidth / 2, y - radius - 15 * this.scale,
            healthBarWidth * healthPercent, healthBarHeight,
            healthColor
        );
        
        // Super charge indicator
        if (fighter.super_charge >= 100) {
            this.renderer.drawCircle(x, y, radius + 8 * this.scale, 0xFFDC00, 0.4);
        }
        
        // Name tag
        const displayName = fighter.is_ai ? `AI-${fighter.brawler_type}` : 
                           (fighter.player_id === this.playerId ? 'YOU' : 
                            fighter.brawler_type.toUpperCase());
        this.renderer.drawText(
            displayName, x, y - radius - 25 * this.scale,
            { fill: 0xFFFFFF, fontSize: 10 * this.scale, align: 'center' }
        );
        
        // Ball indicator
        if (fighter.is_carrying_ball) {
            this.renderer.drawCircle(
                x + Math.cos(fighter.facing_angle) * 30 * this.scale,
                y + Math.sin(fighter.facing_angle) * 30 * this.scale,
                10 * this.scale, 0xFFFFFF, 0.8
            );
        }
    }
    
    /**
     * Draw projectiles
     */
    drawProjectiles() {
        for (const proj of Object.values(this.gameState.projectiles)) {
            const x = this.worldToScreenX(proj.position.x);
            const y = this.worldToScreenY(proj.position.y);
            
            let color, radius;
            
            switch (proj.type) {
                case 'bullet':
                    color = 0xFFDC64;
                    radius = 6 * this.scale;
                    break;
                case 'pellet':
                    color = 0xFFC896;
                    radius = 5 * this.scale;
                    break;
                case 'sniper':
                    color = 0xFF64A0;
                    radius = 8 * this.scale;
                    break;
                case 'melee':
                    color = 0xFF6464;
                    radius = 15 * this.scale;
                    break;
                case 'grenade':
                    color = 0x6464FF;
                    radius = 10 * this.scale;
                    break;
                default:
                    color = 0xFFFFFF;
                    radius = 6 * this.scale;
            }
            
            // Trail
            const speed = Math.sqrt(proj.velocity.x ** 2 + proj.velocity.y ** 2);
            if (speed > 0) {
                const trailX = x - (proj.velocity.x / speed) * radius * 2;
                const trailY = y - (proj.velocity.y / speed) * radius * 2;
                this.renderer.drawCircle(trailX, trailY, radius * 0.6, color, 0.3);
            }
            
            // Projectile
            this.renderer.drawCircle(x, y, radius, color);
        }
    }
    
    /**
     * Draw phase overlays
     */
    drawPhaseOverlay() {
        const state = this.gameState;
        const canvas = document.getElementById('game-canvas');
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        
        if (state.phase === 'countdown') {
            const count = Math.ceil(state.countdown_timer);
            this.renderer.drawText(
                count.toString(), centerX, centerY,
                { fill: 0xFFFFFF, fontSize: 80, align: 'center' }
            );
        }
        
        if (state.phase === 'goal_scored') {
            const scorerTeam = state.scores[0] > (this.prevState?.scores[0] || 0) ? 'Blue' : 'Red';
            const color = scorerTeam === 'Blue' ? 0x4682E6 : 0xE64646;
            
            this.renderer.drawText(
                'GOAL!', centerX, centerY - 30,
                { fill: color, fontSize: 60, align: 'center' }
            );
            this.renderer.drawText(
                `${scorerTeam} Team Scores!`, centerX, centerY + 30,
                { fill: 0xFFFFFF, fontSize: 24, align: 'center' }
            );
        }
        
        if (state.phase === 'game_over') {
            let winnerText = 'Draw!';
            let color = 0xFFFFFF;
            
            if (state.winner_team === 0) {
                winnerText = 'Blue Team Wins!';
                color = 0x4682E6;
            } else if (state.winner_team === 1) {
                winnerText = 'Red Team Wins!';
                color = 0xE64646;
            }
            
            this.renderer.drawText(
                'GAME OVER', centerX, centerY - 40,
                { fill: 0xFFFFFF, fontSize: 50, align: 'center' }
            );
            this.renderer.drawText(
                winnerText, centerX, centerY + 20,
                { fill: color, fontSize: 36, align: 'center' }
            );
            this.renderer.drawText(
                `${state.scores[0]} - ${state.scores[1]}`, centerX, centerY + 70,
                { fill: 0xFFFFFF, fontSize: 30, align: 'center' }
            );
        }
        
        // Overtime indicator
        if (state.overtime && state.phase === 'playing') {
            this.renderer.drawText(
                'OVERTIME', centerX, 30,
                { fill: 0xFFDC00, fontSize: 24, align: 'center' }
            );
        }
    }
    
    /**
     * Update HUD
     */
    updateHUD() {
        if (!this.gameState) return;
        
        // Update timer
        const minutes = Math.floor(this.gameState.time_remaining / 60);
        const seconds = Math.floor(this.gameState.time_remaining % 60);
        const timerText = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        const timerEl = document.getElementById('timer');
        if (timerEl) {
            timerEl.textContent = timerText;
            if (this.gameState.overtime) {
                timerEl.style.color = '#FFD700';
            }
        }
        
        // Update scoreboard
        const scoreboardEl = document.getElementById('scoreboard');
        if (scoreboardEl) {
            scoreboardEl.innerHTML = `
                <div style="display: flex; gap: 20px; justify-content: center; align-items: center;">
                    <span style="color: #4682E6; font-size: 24px; font-weight: bold;">
                        Blue ${this.gameState.scores[0]}
                    </span>
                    <span style="color: white; font-size: 20px;">-</span>
                    <span style="color: #E64646; font-size: 24px; font-weight: bold;">
                        ${this.gameState.scores[1]} Red
                    </span>
                </div>
            `;
        }
    }
    
    /**
     * Handle game over
     */
    onGameOver(winnerTeam, finalState) {
        this.running = false;
        this.gameState = finalState;
        this.render();
    }
    
    /**
     * Destroy the game
     */
    destroy() {
        this.running = false;
        this.moveX = 0;
        this.moveY = 0;
    }
}

export default BrawlerGame;
