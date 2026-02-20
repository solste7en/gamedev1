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

        // Left sidebar
        this.playerStandings   = document.getElementById('player-standings');
        this.globalMultipliers = document.getElementById('global-multipliers');
        this.multSpeedRow = document.getElementById('mult-speed');
        this.multSpeedVal = document.getElementById('mult-speed-val');
        this.multBarrierRow = document.getElementById('mult-barrier');
        this.multBarrierVal = document.getElementById('mult-barrier-val');
    }
    
    /**
     * Update timer display
     */
    updateTimer(elapsedTime, timeLimit = null, mode = 'survival') {
        let displayTime;
        const isTimedMode = (mode === 'high_score' || mode === 'battle_royale') && timeLimit;
        
        if (isTimedMode) {
            // Count down for high score and battle royale modes
            const remaining = Math.max(0, timeLimit - elapsedTime);
            displayTime = remaining;
        } else {
            // Count up for survival mode and single player
            displayTime = elapsedTime;
        }
        
        const minutes = Math.floor(displayTime / 60);
        const seconds = Math.floor(displayTime % 60);
        this.timer.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        // Warning color when low time in timed modes
        if (isTimedMode && displayTime < 30) {
            this.timer.style.color = '#EF4444';
        } else if (mode === 'single_player') {
            // Green tint for single player practice
            this.timer.style.color = '#22C55E';
        } else if (mode === 'battle_royale') {
            // Purple tint for battle royale
            this.timer.style.color = '#A855F7';
        } else {
            this.timer.style.color = '';
        }
    }
    
    /**
     * Update scoreboard display (legacy, no-op — replaced by sidebar)
     */
    updateScoreboard(players) {
        // Delegated to updateSidebar()
    }

    /**
     * Update the left player-sidebar standings list.
     * @param {Object} players  - gameState.players dict
     * @param {string} mode     - game mode string
     * @param {number} barrierMult - points multiplier from barriers (0 = hide)
     */
    updateSidebar(players, mode, barrierMult = 0) {
        if (!this.playerStandings) return;

        // Sort by score descending
        const sorted = Object.values(players).sort((a, b) => {
            const scoreA = a.snake ? a.snake.score : 0;
            const scoreB = b.snake ? b.snake.score : 0;
            return scoreB - scoreA;
        });

        this.playerStandings.innerHTML = '';

        sorted.forEach((player, idx) => {
            const color  = player.snake ? player.snake.color : '#FFFFFF';
            const score  = player.snake ? player.snake.score : 0;
            const alive  = player.snake ? player.snake.alive : false;
            const respawn = player.respawn_remaining || 0;
            const decayTimer   = player.snake ? (player.snake.decay_timer ?? null) : null;
            const spawnFreeze  = player.snake ? (player.snake.spawn_freeze ?? 0) : 0;
            const isAI = player.is_ai || false;

            let subHtml = '';
            if (!alive && respawn > 0) {
                subHtml = `<span class="respawn-cd">↺ ${respawn.toFixed(1)}s</span>`;
            } else if (spawnFreeze > 0) {
                subHtml = `<span class="respawn-cd">● ${spawnFreeze.toFixed(1)}s</span>`;
            } else if (mode === 'survival' && alive && decayTimer !== null) {
                const ratio = Math.min(1, Math.max(0, decayTimer / 6));
                const barColor = ratio > 0.5 ? '#22C55E' : ratio > 0.25 ? '#F59E0B' : '#EF4444';
                const barWidth = Math.round(ratio * 40);
                subHtml = `<span class="decay-bar" style="width:${barWidth}px;background:${barColor}"></span>🍽 ${decayTimer.toFixed(1)}s`;
            }

            const aiTag = isAI ? ` <span style="font-size:8px;opacity:.5">AI</span>` : '';

            const item = document.createElement('div');
            item.className = 'standing-item';
            item.innerHTML = `
                <span class="standing-rank">#${idx + 1}</span>
                <span class="standing-color" style="background:${color};opacity:${alive ? 1 : 0.4}"></span>
                <span class="standing-info">
                    <span class="standing-name${alive ? '' : ' dead'}">${player.name}${aiTag}</span>
                    ${subHtml ? `<span class="standing-sub">${subHtml}</span>` : ''}
                </span>
                <span class="standing-score" style="opacity:${alive ? 1 : 0.6}">${score}</span>
            `;
            this.playerStandings.appendChild(item);
        });

        // Barrier multiplier row (show only when > 1)
        if (this.multBarrierRow && this.multBarrierVal) {
            if (barrierMult > 1.0) {
                this.multBarrierRow.classList.remove('hidden');
                this.multBarrierVal.textContent = `${barrierMult.toFixed(1)}×`;
                if (this.globalMultipliers) this.globalMultipliers.classList.remove('hidden');
            } else {
                this.multBarrierRow.classList.add('hidden');
            }
        }
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
     * @deprecated Use updateSurvivalSpeed() instead; per-player decay bars are now drawn in-canvas.
     */
    updateSurvivalPressure(decayTimer, decayInterval, speedMult) {
        this.updateSurvivalSpeed(speedMult);
    }

    /**
     * Show global speed multiplier in the sidebar and HUD.
     * Per-player decay/hunger bars are rendered directly on the game canvas.
     * @param {number} speedMult - Current speed multiplier (1.0 = normal)
     */
    updateSurvivalSpeed(speedMult) {
        // Legacy HUD element (keep hidden as sidebar takes over)
        if (this.survivalPressure) {
            this.survivalPressure.classList.add('hidden');
        }

        // Sidebar speed row
        if (this.multSpeedRow && this.multSpeedVal) {
            this.multSpeedRow.classList.remove('hidden');
            this.multSpeedVal.textContent = `${speedMult.toFixed(2)}×`;
            this.multSpeedVal.className = 'mult-val' +
                (speedMult >= 1.5 ? ' fast' : speedMult >= 1.25 ? ' medium-fast' : '');
            if (this.globalMultipliers) this.globalMultipliers.classList.remove('hidden');
        }
    }

    /**
     * Hide survival pressure indicators (non-survival modes)
     */
    hideSurvivalPressure() {
        if (this.survivalPressure) {
            this.survivalPressure.classList.add('hidden');
        }
        if (this.multSpeedRow) this.multSpeedRow.classList.add('hidden');
    }

    /**
     * Reset HUD
     */
    reset() {
        this.timer.textContent = '0:00';
        this.timer.style.color = '';
        if (this.scoreboard) this.scoreboard.innerHTML = '';
        if (this.playerStandings) this.playerStandings.innerHTML = '';
        if (this.globalMultipliers) this.globalMultipliers.classList.add('hidden');
        if (this.multBarrierRow) this.multBarrierRow.classList.add('hidden');
        if (this.multSpeedRow) this.multSpeedRow.classList.add('hidden');
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
