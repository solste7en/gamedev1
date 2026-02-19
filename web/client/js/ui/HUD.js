/**
 * HUD - In-game heads-up display
 */

export class HUD {
    constructor() {
        this.bindElements();
    }
    
    /**
     * Bind DOM elements
     */
    bindElements() {
        this.timer = document.getElementById('timer');
        this.scoreboard = document.getElementById('scoreboard');
        this.countdownOverlay = document.getElementById('countdown-overlay');
        this.countdownNumber = document.getElementById('countdown-number');
        this.gameOverOverlay = document.getElementById('game-over-overlay');
        this.gameOverTitle = document.getElementById('game-over-title');
        this.finalScores = document.getElementById('final-scores');
        this.btnBackLobby = document.getElementById('btn-back-lobby');
        
        // Survival pressure indicators
        this.survivalPressure = document.getElementById('survival-pressure');
        this.decayBarFill = document.getElementById('decay-bar-fill');
        this.decayLabel = document.getElementById('decay-label');
        this.speedIndicator = document.getElementById('speed-indicator');
    }
    
    /**
     * Update timer display
     */
    updateTimer(elapsedTime, timeLimit = null, mode = 'survival') {
        let displayTime;
        
        if (mode === 'high_score' && timeLimit) {
            // Count down for high score mode
            const remaining = Math.max(0, timeLimit - elapsedTime);
            displayTime = remaining;
        } else {
            // Count up for survival mode and single player
            displayTime = elapsedTime;
        }
        
        const minutes = Math.floor(displayTime / 60);
        const seconds = Math.floor(displayTime % 60);
        this.timer.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        // Warning color when low time in high score mode
        if (mode === 'high_score' && displayTime < 30) {
            this.timer.style.color = '#EF4444';
        } else if (mode === 'single_player') {
            // Green tint for single player practice
            this.timer.style.color = '#22C55E';
        } else {
            this.timer.style.color = '';
        }
    }
    
    /**
     * Update scoreboard display
     */
    updateScoreboard(players) {
        this.scoreboard.innerHTML = '';
        
        // Sort by score descending
        const sorted = Object.values(players).sort((a, b) => {
            const scoreA = a.snake ? a.snake.score : 0;
            const scoreB = b.snake ? b.snake.score : 0;
            return scoreB - scoreA;
        });
        
        sorted.forEach(player => {
            const item = document.createElement('div');
            item.className = 'score-item';
            
            const color = player.snake ? player.snake.color : '#FFFFFF';
            const score = player.snake ? player.snake.score : 0;
            const alive = player.snake ? player.snake.alive : false;
            
            item.innerHTML = `
                <div class="score-color" style="background-color: ${color}; opacity: ${alive ? 1 : 0.4}"></div>
                <span class="score-name" style="opacity: ${alive ? 1 : 0.4}">${player.name}</span>
                <span class="score-value">${score}</span>
            `;
            
            this.scoreboard.appendChild(item);
        });
    }
    
    /**
     * Show countdown
     */
    showCountdown(number) {
        this.countdownNumber.textContent = number;
        this.countdownOverlay.classList.remove('hidden');
    }
    
    /**
     * Hide countdown
     */
    hideCountdown() {
        this.countdownOverlay.classList.add('hidden');
    }
    
    /**
     * Animate countdown
     */
    async animateCountdown(onComplete, onTick = null) {
        for (let i = 3; i > 0; i--) {
            this.showCountdown(i);
            if (onTick) onTick(i);
            await this.sleep(1000);
        }
        this.showCountdown('GO!');
        await this.sleep(500);
        this.hideCountdown();
        if (onComplete) onComplete();
    }
    
    /**
     * Show game over screen
     */
    showGameOver(winnerId, players, mode) {
        // Sort by rank or score
        const sorted = Object.values(players).sort((a, b) => {
            if (mode === 'survival') {
                return a.rank - b.rank;
            } else {
                const scoreA = a.snake ? a.snake.score : 0;
                const scoreB = b.snake ? b.snake.score : 0;
                return scoreB - scoreA;
            }
        });
        
        // Find winner name
        const winner = sorted.find(p => p.id === winnerId);
        const winnerName = winner ? winner.name : 'Unknown';
        
        this.gameOverTitle.textContent = `${winnerName} Wins!`;
        
        // Build scores
        this.finalScores.innerHTML = '';
        
        sorted.forEach((player, index) => {
            const row = document.createElement('div');
            row.className = 'final-score-row';
            if (player.id === winnerId) {
                row.classList.add('winner');
            }
            
            const rank = mode === 'survival' ? player.rank : index + 1;
            const score = player.snake ? player.snake.score : 0;
            
            row.innerHTML = `
                <span class="rank">#${rank}</span>
                <span class="final-name">${player.name}</span>
                <span class="final-score">${score}</span>
            `;
            
            this.finalScores.appendChild(row);
        });
        
        this.gameOverOverlay.classList.remove('hidden');
    }
    
    /**
     * Hide game over screen
     */
    hideGameOver() {
        this.gameOverOverlay.classList.add('hidden');
    }
    
    /**
     * Set back to lobby callback
     */
    onBackLobby(callback) {
        this.btnBackLobby.onclick = callback;
    }
    
    /**
     * Update survival mode pressure indicators.
     * @param {number} decayTimer   - Seconds remaining until next tail loss (for this player's snake)
     * @param {number} decayInterval - Full interval length at the current game stage
     * @param {number} speedMult    - Current speed multiplier (1.0 = normal, 2.0 = max)
     */
    updateSurvivalPressure(decayTimer, decayInterval, speedMult) {
        if (!this.survivalPressure) return;
        this.survivalPressure.classList.remove('hidden');

        // Bar fill: full when timer is maxed, empty when at 0
        const ratio = Math.max(0, Math.min(1, decayTimer / decayInterval));
        const pct = (ratio * 100).toFixed(0);
        this.decayBarFill.style.width = `${pct}%`;

        // Color: green → yellow → red
        if (ratio > 0.5) {
            this.decayBarFill.style.background = 'var(--success)';
        } else if (ratio > 0.25) {
            this.decayBarFill.style.background = 'var(--warning)';
        } else {
            this.decayBarFill.style.background = 'var(--danger)';
            // Pulse the panel when critical
            this.survivalPressure.classList.add('sp-critical');
        }
        if (ratio > 0.25) {
            this.survivalPressure.classList.remove('sp-critical');
        }

        this.decayLabel.textContent = `${Math.max(0, decayTimer).toFixed(1)}s`;
        this.speedIndicator.textContent = `${speedMult.toFixed(2)}×`;

        // Tint the speed indicator when noticeably fast
        this.speedIndicator.style.color = speedMult >= 1.5 ? 'var(--danger)' :
                                           speedMult >= 1.25 ? 'var(--warning)' : '';
    }

    /**
     * Hide survival pressure indicators (non-survival modes)
     */
    hideSurvivalPressure() {
        if (this.survivalPressure) {
            this.survivalPressure.classList.add('hidden');
        }
    }

    /**
     * Reset HUD
     */
    reset() {
        this.timer.textContent = '0:00';
        this.timer.style.color = '';
        this.scoreboard.innerHTML = '';
        this.hideCountdown();
        this.hideGameOver();
        this.hideSurvivalPressure();
    }
    
    /**
     * Sleep helper
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

export default HUD;
