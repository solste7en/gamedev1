/**
 * SnakeGame - Snake Classic multiplayer game renderer
 */

import { ParticleSystem } from '../engine/ParticleSystem.js';

export class SnakeGame {
    constructor(renderer, inputManager, networkManager, hud, soundManager = null) {
        this.renderer = renderer;
        this.input = inputManager;
        this.network = networkManager;
        this.hud = hud;
        this.sound = soundManager;
        
        this.gameState = null;
        this.prevState = null;  // For detecting changes
        this.playerId = null;
        this.running = false;

        // Callback set by main.js to handle mid-game quit
        this.onLeaveGame = null;
        // Prevents showing the dead overlay more than once per game
        this._deadOverlayShown = false;
        
        // Visual settings
        this.cellSize = 16;
        this.padding = 10;
        this.focusedLayout = false;
        this.focusPeek = 0;
        
        // Particle system
        this.particles = null;
        
        // Graphics caching for performance optimization
        // Static elements are rendered once and reused
        this.graphicsCache = {
            staticLayer: null,       // Quadrant backgrounds, grid, walls (rendered once)
            staticRendered: false,   // Flag to track if static layer is ready
            wallBrickColors: new Map(), // Pre-computed brick colors per wall
            // Dynamic element pools
            snakeGraphics: [],       // Pool of graphics for snake segments
            foodGraphics: [],        // Pool of graphics for food items
            textObjects: new Map(),  // Cached text objects by key
            decayBarGraphics: new Map(), // Per-player decay bar graphics (key = playerId)
        };
        
        // Track what was rendered last frame for change detection
        this.lastRenderState = {
            quadrantBoundsHash: null,
            playerAliveStates: {},
            foodHash: null,
            snakePositions: {},
        };
        
        // Frame counter for tongue animation (deterministic)
        this.frameCount = 0;
    }
    
    /**
     * Initialize the game
     */
    async init(playerId) {
        this.playerId = playerId;
        
        // Setup input controls
        this.input.setupSnakeControls((direction) => {
            if (this.running) {
                this.network.sendInput(direction);
            }
        });
        
        this.input.start();
        
        // Calculate canvas size based on expected grid
        await this.calculateSize();
        
        return this;
    }
    
    /**
     * Calculate and set renderer size
     */
    async calculateSize() {
        // Default size until we get game state
        const width = 800;
        const height = 600;
        
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
    }
    
    /**
     * Update canvas size based on game state
     */
    updateCanvasSize() {
        if (!this.gameState) return;
        
        // Derive layout from actual quadrant bounds, not from mode or player count.
        const numQuadrants = Object.keys(this.gameState.quadrant_bounds).length;
        
        let cols, rows;
        if (numQuadrants <= 1) {
            cols = 1;
            rows = 1;
        } else if (numQuadrants <= 2) {
            cols = 2;
            rows = 1;
        } else {
            cols = 2;
            rows = 2;
        }
        
        const quadrantWidth = this.gameState.quadrant_bounds[0] 
            ? (this.gameState.quadrant_bounds[0].x_max - this.gameState.quadrant_bounds[0].x_min)
            : 20;
        const quadrantHeight = this.gameState.quadrant_bounds[0]
            ? (this.gameState.quadrant_bounds[0].y_max - this.gameState.quadrant_bounds[0].y_min)
            : 20;

        this.focusedLayout = false;
        this.focusPeek = 0;

        const width  = cols * quadrantWidth  * this.cellSize + this.padding * 2;
        const height = rows * quadrantHeight * this.cellSize + this.padding * 2 + 30;
        
        this.renderer.resize(width, height);
        this.renderer.setGrid(quadrantWidth * cols, quadrantHeight * rows, this.cellSize);

        // Position the side panels immediately adjacent to the canvas so they stay
        // in view even on small/narrow browser windows.
        requestAnimationFrame(() => this._repositionSidePanels(width));
    }

    /**
     * Position side panels flush against the canvas edges.
     * Both panels are position:absolute relative to #game-wrapper (full viewport).
     */
    _repositionSidePanels(canvasWidth) {
        const wrapper = document.getElementById('game-wrapper');
        const sidebar = document.getElementById('player-sidebar');
        const legend  = document.getElementById('animal-legend');
        if (!wrapper || !sidebar || !legend) return;

        const wrapperW = wrapper.clientWidth;
        const canvasLeft  = Math.max(0, (wrapperW - canvasWidth) / 2);
        const canvasRight = canvasLeft + canvasWidth;
        const GAP = 10;
        const PANEL_W = 180;

        // Left panel: right-align to just left of canvas, min 4px from viewport edge
        const sidebarLeft = Math.max(4, canvasLeft - PANEL_W - GAP);
        sidebar.style.left  = sidebarLeft + 'px';
        sidebar.style.right = 'auto';

        // Right panel: left-align to just right of canvas
        const legendLeft = Math.min(wrapperW - PANEL_W - 4, canvasRight + GAP);
        legend.style.left  = legendLeft + 'px';
        legend.style.right = 'auto';
    }
    
    /**
     * Start the game
     */
    start() {
        this.running = true;
        this._deadOverlayShown = false;
        this.hud.reset();
        // Note: graphics cache is intentionally NOT reset here.
        // The canvas is already pre-rendered during the countdown (via game_start/game_state events),
        // so clearing it would cause a needless flash. New SnakeGame instances start with an empty cache.
    }
    
    /**
     * Stop the game
     */
    stop() {
        this.running = false;
        this.input.clearControls();
        this.input.stop();
    }
    
    /**
     * Reset graphics cache (call when starting new game)
     */
    resetGraphicsCache() {
        // Clear static layer
        if (this.graphicsCache.staticLayer) {
            this.graphicsCache.staticLayer.destroy({ children: true });
            this.graphicsCache.staticLayer = null;
        }
        this.graphicsCache.staticRendered = false;
        this.graphicsCache.wallBrickColors.clear();
        
        // Clear pools
        this.graphicsCache.snakeGraphics.forEach(g => g.destroy());
        this.graphicsCache.snakeGraphics = [];
        this.graphicsCache.foodGraphics.forEach(g => g.destroy());
        this.graphicsCache.foodGraphics = [];
        this.graphicsCache.textObjects.forEach(t => {
            if (t && typeof t.destroy === 'function') t.destroy();
        });
        this.graphicsCache.textObjects.clear();
        this.graphicsCache.decayBarGraphics.forEach(g => g.destroy());
        this.graphicsCache.decayBarGraphics.clear();
        
        // Reset render state
        this.lastRenderState = {
            quadrantBoundsHash: null,
            playerAliveStates: {},
            foodHash: null,
            snakePositions: {},
        };
        this.frameCount = 0;
    }
    
    /**
     * Update game state from server
     */
    updateState(state) {
        const firstUpdate = !this.gameState;
        this.prevState = this.gameState;

        if (!firstUpdate && this.gameState) {
            // Delta states omit static fields; carry them forward
            if (!state.walls && this.gameState.walls) state.walls = this.gameState.walls;
            if (!state.quadrant_bounds && this.gameState.quadrant_bounds) state.quadrant_bounds = this.gameState.quadrant_bounds;
            if (!state.game_type && this.gameState.game_type) state.game_type = this.gameState.game_type;
            if (!state.mode && this.gameState.mode) state.mode = this.gameState.mode;
            if (!state.barrier_density && this.gameState.barrier_density) state.barrier_density = this.gameState.barrier_density;
            if (!state.map_size && this.gameState.map_size) state.map_size = this.gameState.map_size;
            if (state.grid_width == null) state.grid_width = this.gameState.grid_width;
            if (state.grid_height == null) state.grid_height = this.gameState.grid_height;
        }

        this.gameState = state;
        
        if (firstUpdate) {
            this.updateCanvasSize();
        }
        
        // Detect score changes (food eaten)
        this.detectScoreChanges();
        
        // Update particles
        if (this.particles) {
            this.particles.update();
        }
        
        this.render();
        this.updateHUD();
    }
    
    /**
     * Detect when players eat food
     */
    detectScoreChanges() {
        if (!this.prevState || !this.gameState) return;
        
        for (const [playerId, player] of Object.entries(this.gameState.players)) {
            const prevPlayer = this.prevState.players[playerId];
            if (!prevPlayer || !player.snake || !prevPlayer.snake) continue;
            
            // Score increased = food eaten
            if (player.snake.score > prevPlayer.snake.score) {
                const head = player.snake.body[0];
                if (head) {
                    const x = this.padding + head.x * this.cellSize + this.cellSize / 2;
                    const y = this.padding + 30 + head.y * this.cellSize + this.cellSize / 2;
                    const color = parseInt(player.snake.color.replace('#', ''), 16);
                    
                    // Add eat particles
                    if (this.particles) {
                        this.particles.eatEffect(x, y, color);
                    }
                    
                    // Play sound
                    if (this.sound && parseInt(playerId) === this.playerId) {
                        const scoreDiff = player.snake.score - prevPlayer.snake.score;
                        if (scoreDiff > 50) {
                            this.sound.play('eat_large');
                        } else {
                            this.sound.play('eat');
                        }
                        
                        // Combo sound
                        if (player.snake.combo > prevPlayer.snake.combo && player.snake.combo > 1) {
                            this.sound.playComboSound(player.snake.combo);
                        }
                    }
                }
            }
            
            // Death detection
            if (prevPlayer.snake.alive && !player.snake.alive) {
                const head = player.snake.body[0];
                if (head && this.particles) {
                    const x = this.padding + head.x * this.cellSize + this.cellSize / 2;
                    const y = this.padding + 30 + head.y * this.cellSize + this.cellSize / 2;
                    const color = parseInt(player.snake.color.replace('#', ''), 16);
                    this.particles.deathEffect(x, y, color);
                }
            }
        }
    }
    
    /**
     * Render the game (optimized with caching)
     */
    render() {
        if (!this.gameState) return;
        
        this.frameCount++;

        const contentOffsetX = this.padding;
        const contentOffsetY = this.padding + 30;
        
        // Step 1: Render static layer (backgrounds, grid, walls) - only once
        if (!this.graphicsCache.staticRendered) {
            this.renderStaticLayer(contentOffsetX, contentOffsetY);
        }
        
        // Step 2: Clear and re-render dynamic elements (snake, food, text)
        this.renderDynamicLayer(contentOffsetX, contentOffsetY);
    }
    
    /**
     * Render static layer (backgrounds, grid, walls) - called once per game
     */
    renderStaticLayer(contentOffsetX, contentOffsetY) {
        // Create static layer container
        this.graphicsCache.staticLayer = new PIXI.Container();
        this.renderer.gameContainer.addChild(this.graphicsCache.staticLayer);
        
        // Pre-compute brick colors for all walls (deterministic)
        this.precomputeWallBrickColors();
        
        // Render each quadrant's static elements
        for (const [playerId, player] of Object.entries(this.gameState.players)) {
            const bounds = this.gameState.quadrant_bounds[player.quadrant];
            if (!bounds) continue;
            
            const color = player.snake ? player.snake.color : '#FFFFFF';
            
            // Draw quadrant background and grid (static)
            this.drawQuadrantBackgroundCached(bounds, color, contentOffsetX, contentOffsetY);
            
            // Draw walls (static)
            const walls = this.gameState.walls[player.quadrant] || [];
            walls.forEach((wall, index) => {
                const wallKey = `${player.quadrant}_${index}`;
                this.drawWallCached(wall, wallKey, contentOffsetX, contentOffsetY);
            });
        }
        
        this.graphicsCache.staticRendered = true;
    }
    
    /**
     * Render dynamic layer (snake, food, text) - called every frame
     */
    renderDynamicLayer(contentOffsetX, contentOffsetY) {
        // Track used graphics from pools
        let snakeGraphicsIndex = 0;
        let foodGraphicsIndex = 0;
        
        // Render each player's dynamic elements
        for (const [playerId, player] of Object.entries(this.gameState.players)) {
            const bounds = this.gameState.quadrant_bounds[player.quadrant];
            if (!bounds) continue;
            
            const color = player.snake ? player.snake.color : '#FFFFFF';
            const isAlive = player.snake ? player.snake.alive : false;
            
            // Update player name label inside each quadrant (fixed-width background pill)
            const quadrantX = contentOffsetX + bounds.x_min * this.cellSize;
            const quadrantY = contentOffsetY + bounds.y_min * this.cellSize;
            const quadrantWidth = (bounds.x_max - bounds.x_min) * this.cellSize;

            // Fixed-width background pill for the name header
            const pillKey = `pill_${playerId}`;
            let pillG = this.graphicsCache.textObjects.get(pillKey + '_bg');
            if (!pillG) {
                pillG = new PIXI.Graphics();
                this.renderer.gameContainer.addChild(pillG);
                this.graphicsCache.textObjects.set(pillKey + '_bg', pillG);
            }
            const pillW = 100;
            const pillH = 16;
            const pillX = quadrantX + quadrantWidth / 2 - pillW / 2;
            const pillY = quadrantY + 2;
            pillG.clear();
            pillG.beginFill(0x0F172A, 0.75);
            pillG.drawRoundedRect(pillX, pillY, pillW, pillH, 4);
            pillG.endFill();
            pillG.visible = true;

            this.updateCachedText(
                `name_${playerId}`,
                `${player.name}${!isAlive ? ' ✝' : ''}`,
                quadrantX + quadrantWidth / 2,
                quadrantY + 10,
                {
                    fontSize: 11,
                    fill: this.parseColor(color),
                    fontWeight: 'bold'
                }
            );

            // Name tag above snake head during spawn freeze (countdown + respawn)
            const spawnFreeze = player.snake ? (player.snake.spawn_freeze || 0) : 0;
            if (player.snake && spawnFreeze > 0) {
                const head = player.snake.body[0];
                if (head) {
                    const tagX = contentOffsetX + head.x * this.cellSize + this.cellSize / 2;
                    const tagY = contentOffsetY + head.y * this.cellSize - 14;
                    this.updateCachedText(
                        `spawntag_${playerId}`,
                        player.name,
                        tagX,
                        tagY,
                        { fontSize: 10, fill: this.parseColor(color), fontWeight: 'bold' }
                    );
                } else {
                    this.hideCachedText(`spawntag_${playerId}`);
                }
            } else {
                this.hideCachedText(`spawntag_${playerId}`);
            }
            
            // Per-player hunger (decay) bar in Survival mode
            if (this.gameState.mode === 'survival') {
                this._drawPlayerDecayBar(playerId, player, quadrantX, quadrantY, quadrantWidth, contentOffsetX, contentOffsetY);
            } else {
                // Hide if not survival mode
                const dbg = this.graphicsCache.decayBarGraphics.get(String(playerId));
                if (dbg) dbg.visible = false;
            }
            
            // Draw food (pooled)
            const foods = this.gameState.foods[player.quadrant] || [];
            foods.forEach(food => {
                foodGraphicsIndex = this.drawAnimalPooled(food, contentOffsetX, contentOffsetY, foodGraphicsIndex);
            });
            
            // Draw snake (pooled)
            if (player.snake) {
                snakeGraphicsIndex = this.drawDetailedSnakePooled(player.snake, contentOffsetX, contentOffsetY, snakeGraphicsIndex);
                
                // Combo indicator (cached text)
                if (player.snake.combo > 0) {
                    const head = player.snake.body[0];
                    if (head) {
                        const x = contentOffsetX + head.x * this.cellSize + this.cellSize / 2;
                        const y = contentOffsetY + head.y * this.cellSize + this.cellSize / 2;
                        
                        this.updateCachedText(
                            `combo_${playerId}`,
                            `x${player.snake.combo}`,
                            x,
                            y - 20,
                            { fontSize: 10, fill: 0xF1C40F, fontWeight: 'bold' }
                        );
                    }
                } else {
                    // Hide combo text if no combo
                    this.hideCachedText(`combo_${playerId}`);
                }
            }
        }
        
        // Hide unused pooled graphics
        this.hideUnusedPooledGraphics(snakeGraphicsIndex, foodGraphicsIndex);
    }
    
    /**
     * Draw quadrant background (cached in static layer)
     */
    drawQuadrantBackgroundCached(bounds, playerColor, offsetX, offsetY) {
        const x = offsetX + bounds.x_min * this.cellSize;
        const y = offsetY + bounds.y_min * this.cellSize;
        const width = (bounds.x_max - bounds.x_min) * this.cellSize;
        const height = (bounds.y_max - bounds.y_min) * this.cellSize;
        
        const graphics = new PIXI.Graphics();
        
        // Background
        graphics.beginFill(0x1E293B);
        graphics.drawRect(x, y, width, height);
        graphics.endFill();
        
        // Border with player color
        const borderColor = this.parseColor(playerColor);
        graphics.lineStyle(3, borderColor, 1);
        graphics.drawRect(x, y, width, height);
        
        // Grid lines
        graphics.lineStyle(1, 0x334155, 0.3);
        for (let gx = bounds.x_min; gx <= bounds.x_max; gx++) {
            graphics.moveTo(offsetX + gx * this.cellSize, y);
            graphics.lineTo(offsetX + gx * this.cellSize, y + height);
        }
        for (let gy = bounds.y_min; gy <= bounds.y_max; gy++) {
            graphics.moveTo(x, offsetY + gy * this.cellSize);
            graphics.lineTo(x + width, offsetY + gy * this.cellSize);
        }
        
        this.graphicsCache.staticLayer.addChild(graphics);
    }
    
    /**
     * Pre-compute brick colors for walls (deterministic, no Math.random in render)
     */
    precomputeWallBrickColors() {
        const brickColor = 0x654321;
        const brickLight = 0x8B5A2B;
        
        for (const [quadrant, walls] of Object.entries(this.gameState.walls)) {
            walls.forEach((wall, wallIndex) => {
                const wallKey = `${quadrant}_${wallIndex}`;
                const colors = [];
                
                const width = wall.width * this.cellSize;
                const height = wall.height * this.cellSize;
                const brickW = this.cellSize / 2 - 1;
                const brickH = this.cellSize / 3 - 1;
                
                // Use deterministic pattern based on position
                let brickIndex = 0;
                for (let by = 0; by < height; by += brickH + 1) {
                    for (let bx = -brickW; bx < width + brickW; bx += brickW + 1) {
                        // Deterministic: use a simple hash of position
                        const useLight = ((brickIndex * 7 + wallIndex * 13) % 10) < 3;
                        colors.push(useLight ? brickLight : brickColor);
                        brickIndex++;
                    }
                }
                
                this.graphicsCache.wallBrickColors.set(wallKey, colors);
            });
        }
    }
    
    /**
     * Draw a wall/barrier (cached in static layer with pre-computed colors)
     */
    drawWallCached(wall, wallKey, offsetX, offsetY) {
        const x = offsetX + wall.position.x * this.cellSize;
        const y = offsetY + wall.position.y * this.cellSize;
        const width = wall.width * this.cellSize;
        const height = wall.height * this.cellSize;
        
        const graphics = new PIXI.Graphics();
        const mortarColor = 0x505050;
        
        // Draw mortar background
        graphics.beginFill(mortarColor);
        graphics.drawRect(x, y, width, height);
        graphics.endFill();
        
        // Draw bricks with pre-computed colors (no randomness)
        const brickW = this.cellSize / 2 - 1;
        const brickH = this.cellSize / 3 - 1;
        const brickColors = this.graphicsCache.wallBrickColors.get(wallKey) || [];
        let colorIndex = 0;
        
        for (let by = 0; by < height; by += brickH + 1) {
            const rowOffset = (Math.floor(by / (brickH + 1)) % 2) * (brickW / 2);
            for (let bx = -brickW; bx < width + brickW; bx += brickW + 1) {
                const brick_x = x + bx + rowOffset;
                const brick_y = y + by;
                
                // Check if brick is within wall bounds
                if (brick_x >= x - 1 && brick_x + brickW <= x + width + 1 &&
                    brick_y >= y && brick_y + brickH <= y + height) {
                    
                    const color = brickColors[colorIndex] || 0x654321;
                    colorIndex++;
                    
                    graphics.beginFill(color);
                    graphics.drawRect(brick_x, brick_y, brickW, brickH);
                    graphics.endFill();
                    
                    // Brick highlight
                    graphics.beginFill(0xFFFFFF, 0.1);
                    graphics.drawRect(brick_x, brick_y, brickW, 1);
                    graphics.endFill();
                }
            }
        }
        
        // Border
        graphics.lineStyle(1, 0x3D2914);
        graphics.drawRect(x, y, width, height);
        
        this.graphicsCache.staticLayer.addChild(graphics);
    }
    
    /**
     * Get or create a pooled graphics object for food
     */
    getPooledFoodGraphics(index) {
        while (this.graphicsCache.foodGraphics.length <= index) {
            const g = new PIXI.Graphics();
            g.visible = false;
            this.renderer.gameContainer.addChild(g);
            this.graphicsCache.foodGraphics.push(g);
        }
        return this.graphicsCache.foodGraphics[index];
    }
    
    /**
     * Get or create a pooled graphics object for snake
     */
    getPooledSnakeGraphics(index) {
        while (this.graphicsCache.snakeGraphics.length <= index) {
            const g = new PIXI.Graphics();
            g.visible = false;
            this.renderer.gameContainer.addChild(g);
            this.graphicsCache.snakeGraphics.push(g);
        }
        return this.graphicsCache.snakeGraphics[index];
    }
    
    /**
     * Hide unused pooled graphics at end of frame
     */
    hideUnusedPooledGraphics(snakeIndex, foodIndex) {
        for (let i = snakeIndex; i < this.graphicsCache.snakeGraphics.length; i++) {
            this.graphicsCache.snakeGraphics[i].visible = false;
        }
        for (let i = foodIndex; i < this.graphicsCache.foodGraphics.length; i++) {
            const g = this.graphicsCache.foodGraphics[i];
            g.visible = false;
            g._lastStateKey = null;
        }
    }
    
    /**
     * Update or create cached text object
     */
    updateCachedText(key, text, x, y, style) {
        let textObj = this.graphicsCache.textObjects.get(key);
        
        if (!textObj) {
            const defaultStyle = {
                fontFamily: 'Inter',
                fontSize: 14,
                fill: 0xFFFFFF,
                align: 'center'
            };
            const textStyle = new PIXI.TextStyle({ ...defaultStyle, ...style });
            textObj = new PIXI.Text(text, textStyle);
            textObj.anchor.set(0.5);
            this.renderer.gameContainer.addChild(textObj);
            this.graphicsCache.textObjects.set(key, textObj);
        } else {
            // Update text content if changed
            if (textObj.text !== text) {
                textObj.text = text;
            }
        }
        
        textObj.x = x;
        textObj.y = y;
        textObj.visible = true;
        
        return textObj;
    }
    
    /**
     * Hide a cached text object
     */
    hideCachedText(key) {
        const textObj = this.graphicsCache.textObjects.get(key);
        if (textObj) {
            textObj.visible = false;
        }
    }
    
    /**
     * Draw a per-player decay (hunger) bar in Survival mode.
     * Bar sits just below the player name label, inside their quadrant.
     */
    _drawPlayerDecayBar(playerId, player, quadrantX, quadrantY, quadrantWidth, offsetX, offsetY) {
        const key = String(playerId);
        let g = this.graphicsCache.decayBarGraphics.get(key);
        if (!g) {
            g = new PIXI.Graphics();
            this.renderer.gameContainer.addChild(g);
            this.graphicsCache.decayBarGraphics.set(key, g);
        }
        g.clear();
        g.visible = true;

        const snake = player.snake;
        const isAlive = snake && snake.alive;
        const interval = this.gameState.survival_decay_current_interval || 6;
        const timer = (snake && snake.decay_timer != null) ? snake.decay_timer : interval;
        const ratio = Math.max(0, Math.min(1, timer / interval));

        // Bar dimensions — sits right below the name label
        const barW = Math.min(80, quadrantWidth * 0.4);
        const barH = 5;
        const barX = quadrantX + 4;
        const barY = quadrantY + 20;

        if (!isAlive) {
            // Ghost bar when dead
            g.beginFill(0x334155, 0.5);
            g.drawRoundedRect(barX, barY, barW, barH, 2);
            g.endFill();
            return;
        }

        // Background track
        g.beginFill(0x1E293B, 0.8);
        g.drawRoundedRect(barX - 1, barY - 1, barW + 2, barH + 2, 3);
        g.endFill();

        // Filled portion
        let fillColor;
        if (ratio > 0.5)       fillColor = 0x22C55E;   // green
        else if (ratio > 0.25) fillColor = 0xF59E0B;   // amber
        else                   fillColor = 0xEF4444;   // red

        // Pulse when critical
        let fillAlpha = 1.0;
        if (ratio <= 0.25) {
            fillAlpha = 0.5 + 0.5 * Math.abs(Math.sin(this.frameCount * 0.15));
        }

        const filledW = Math.max(2, barW * ratio);
        g.beginFill(fillColor, fillAlpha);
        g.drawRoundedRect(barX, barY, filledW, barH, 2);
        g.endFill();

        // Fork icon + timer label via cached text
        const labelText = `🍽 ${Math.max(0, timer).toFixed(1)}s`;
        this.updateCachedText(
            `decay_label_${playerId}`,
            labelText,
            barX + barW + 4,
            barY - 1,
            { fontSize: 9, fill: ratio > 0.25 ? 0xCBD5E1 : 0xEF4444 }
        );
    }

    /**
     * Draw animal using pooled graphics (returns next available index)
     */
    drawAnimalPooled(food, offsetX, offsetY, poolIndex) {
        const graphics = this.getPooledFoodGraphics(poolIndex);

        const baseX = offsetX + food.position.x * this.cellSize;
        const baseY = offsetY + food.position.y * this.cellSize;
        const colors = food.colors || {};
        const type = food.type;
        const cells = food.cells || [[0, 0]];

        // Recovery flash: pulsing transparency when animal is in cooldown after being hit
        if (food.recovering && food.hit_recovery > 0) {
            const flashPhase = Math.sin(Date.now() / 80) * 0.5 + 0.5;
            graphics.alpha = 0.25 + flashPhase * 0.45;
        } else {
            graphics.alpha = 1.0;
        }

        // Skip expensive redraw if food visual state is unchanged since last frame
        const stateKey = `${type}_${food.position.x}_${food.position.y}_${food.health}_${food.recovering ? 1 : 0}_${food.max_health}`;
        if (graphics._lastStateKey === stateKey) {
            graphics.visible = true;
            return poolIndex + 1;
        }
        graphics._lastStateKey = stateKey;
        graphics.clear();
        graphics.visible = true;
        
        // Draw based on animal category and type
        if (food.category === 'small') {
            this.drawSmallAnimal(graphics, baseX, baseY, type, colors);
        } else if (food.category === 'medium') {
            this.drawMediumAnimal(graphics, baseX, baseY, type, colors, cells);
        } else if (food.category === 'large') {
            this.drawLargeAnimal(graphics, baseX, baseY, type, colors, cells);
        } else {
            this.drawHugeAnimal(graphics, baseX, baseY, type, colors, cells);
        }
        
        // Health bar for multi-hit animals (shown even during recovery to indicate damage)
        if (food.max_health > 1) {
            // Span the widest row of cells
            const maxCol = cells.length > 1 ? Math.max(...cells.map(c => c[0])) : 0;
            const totalWidth = (maxCol + 1) * this.cellSize;
            const healthPercent = food.health / food.max_health;
            const barH = 5;
            const barY = baseY - barH - 1;
            
            // Background (dark track)
            graphics.beginFill(0x1a1a2e, 0.85);
            graphics.drawRoundedRect(baseX, barY, totalWidth - 2, barH, 2);
            graphics.endFill();
            
            // Health fill with colour coding
            const healthColor = healthPercent > 0.6 ? 0x22C55E :
                                healthPercent > 0.35 ? 0xF59E0B : 0xEF4444;
            graphics.beginFill(healthColor);
            graphics.drawRoundedRect(baseX, barY, Math.max(2, (totalWidth - 2) * healthPercent), barH, 2);
            graphics.endFill();
            
            // Recovery indicator: show a small ⏱ shimmer overlay across full bar
            if (food.recovering) {
                graphics.beginFill(0xffffff, 0.18);
                graphics.drawRoundedRect(baseX, barY, totalWidth - 2, barH, 2);
                graphics.endFill();
            }
        }
        
        return poolIndex + 1;
    }
    
    /**
     * Draw small animal (1 cell)
     */
    drawSmallAnimal(graphics, x, y, type, colors) {
        const cx = x + this.cellSize / 2;
        const cy = y + this.cellSize / 2;
        const size = this.cellSize / 2 - 2;
        
        const bodyColor = this.parseColor(colors.body || '#808080');
        
        switch (type) {
            case 'mouse':
                // Body
                graphics.beginFill(bodyColor);
                graphics.drawEllipse(cx, cy, size, size * 0.7);
                graphics.endFill();
                // Ears
                const earColor = this.parseColor(colors.ear || '#FFB6C1');
                graphics.beginFill(earColor);
                graphics.drawCircle(cx - 4, cy - 4, 3);
                graphics.drawCircle(cx + 4, cy - 4, 3);
                graphics.endFill();
                // Eyes
                graphics.beginFill(0x000000);
                graphics.drawCircle(cx - 2, cy - 1, 1);
                graphics.drawCircle(cx + 2, cy - 1, 1);
                graphics.endFill();
                // Tail
                graphics.lineStyle(1, this.parseColor(colors.tail || '#FFA0A0'));
                graphics.moveTo(cx + size, cy);
                graphics.bezierCurveTo(cx + size + 4, cy + 2, cx + size + 6, cy - 2, cx + size + 8, cy + 4);
                break;
                
            case 'frog':
                // Body
                graphics.beginFill(bodyColor);
                graphics.drawCircle(cx, cy, size);
                graphics.endFill();
                // Belly
                graphics.beginFill(this.parseColor(colors.belly || '#90EE90'));
                graphics.drawEllipse(cx, cy + 2, size * 0.6, size * 0.5);
                graphics.endFill();
                // Eyes
                const eyeColor = this.parseColor(colors.eye || '#FFD700');
                graphics.beginFill(eyeColor);
                graphics.drawCircle(cx - 3, cy - 3, 3);
                graphics.drawCircle(cx + 3, cy - 3, 3);
                graphics.endFill();
                graphics.beginFill(0x000000);
                graphics.drawCircle(cx - 3, cy - 3, 1);
                graphics.drawCircle(cx + 3, cy - 3, 1);
                graphics.endFill();
                break;
                
            case 'butterfly':
                // Wings
                const wing1 = this.parseColor(colors.wing1 || '#FF69B4');
                const wing2 = this.parseColor(colors.wing2 || '#FFB6C1');
                graphics.beginFill(wing1);
                graphics.drawEllipse(cx - 4, cy - 2, 5, 4);
                graphics.drawEllipse(cx + 4, cy - 2, 5, 4);
                graphics.endFill();
                graphics.beginFill(wing2);
                graphics.drawEllipse(cx - 3, cy + 3, 3, 3);
                graphics.drawEllipse(cx + 3, cy + 3, 3, 3);
                graphics.endFill();
                // Body
                graphics.beginFill(this.parseColor(colors.body || '#463228'));
                graphics.drawEllipse(cx, cy, 2, 5);
                graphics.endFill();
                break;
                
            case 'bee':
                // Body
                graphics.beginFill(this.parseColor(colors.body || '#FFC832'));
                graphics.drawEllipse(cx, cy, size, size * 0.7);
                graphics.endFill();
                // Stripes
                graphics.beginFill(this.parseColor(colors.stripes || '#281E14'));
                graphics.drawRect(cx - size + 2, cy - 2, 3, 4);
                graphics.drawRect(cx - 2, cy - 2, 3, 4);
                graphics.drawRect(cx + size - 5, cy - 2, 3, 4);
                graphics.endFill();
                // Wings
                graphics.beginFill(this.parseColor(colors.wings || '#C8DCFF'), 0.6);
                graphics.drawEllipse(cx, cy - 5, 4, 3);
                graphics.endFill();
                break;
                
            case 'spider':
                // Body
                graphics.beginFill(bodyColor);
                graphics.drawCircle(cx, cy, size * 0.6);
                graphics.drawCircle(cx, cy + 3, size * 0.4);
                graphics.endFill();
                // Legs
                graphics.lineStyle(1, this.parseColor(colors.legs || '#1E1E1E'));
                for (let i = 0; i < 4; i++) {
                    const angle = (i - 1.5) * 0.4;
                    graphics.moveTo(cx, cy);
                    graphics.lineTo(cx - 6 - i, cy + 4 + Math.abs(i - 1.5) * 2);
                    graphics.moveTo(cx, cy);
                    graphics.lineTo(cx + 6 + i, cy + 4 + Math.abs(i - 1.5) * 2);
                }
                // Eyes
                graphics.beginFill(this.parseColor(colors.eye || '#FF0000'));
                graphics.drawCircle(cx - 1, cy - 2, 1);
                graphics.drawCircle(cx + 1, cy - 2, 1);
                graphics.endFill();
                break;
                
            default:
                // Generic small animal
                graphics.beginFill(bodyColor);
                graphics.drawCircle(cx, cy, size);
                graphics.endFill();
                // Eyes
                graphics.beginFill(0x000000);
                graphics.drawCircle(cx - 2, cy - 1, 1);
                graphics.drawCircle(cx + 2, cy - 1, 1);
                graphics.endFill();
        }
    }
    
    /**
     * Draw medium animal (2-3 cells)
     */
    drawMediumAnimal(graphics, x, y, type, colors, cells) {
        const bodyColor = this.parseColor(colors.body || '#A9A9A9');
        
        // Draw body across cells
        cells.forEach(([dx, dy]) => {
            const cx = x + dx * this.cellSize + this.cellSize / 2;
            const cy = y + dy * this.cellSize + this.cellSize / 2;
            
            graphics.beginFill(bodyColor);
            graphics.drawRoundedRect(
                x + dx * this.cellSize + 1,
                y + dy * this.cellSize + 1,
                this.cellSize - 2,
                this.cellSize - 2,
                3
            );
            graphics.endFill();
        });
        
        // Draw details based on type
        const headX = x + this.cellSize / 2;
        const headY = y + this.cellSize / 2;
        
        switch (type) {
            case 'rabbit':
                // Ears
                graphics.beginFill(this.parseColor(colors.ear || '#FFB6C1'));
                graphics.drawEllipse(headX - 3, headY - 8, 2, 5);
                graphics.drawEllipse(headX + 3, headY - 8, 2, 5);
                graphics.endFill();
                // Nose
                graphics.beginFill(this.parseColor(colors.nose || '#FF9696'));
                graphics.drawCircle(headX, headY + 2, 2);
                graphics.endFill();
                break;
                
            case 'fish':
                // Tail fin
                graphics.beginFill(this.parseColor(colors.fin || '#3C8CB4'));
                const tailX = x + cells.length * this.cellSize - 2;
                graphics.moveTo(tailX, headY);
                graphics.lineTo(tailX + 6, headY - 4);
                graphics.lineTo(tailX + 6, headY + 4);
                graphics.closePath();
                graphics.endFill();
                // Eye
                graphics.beginFill(0xFFFFFF);
                graphics.drawCircle(headX + 2, headY - 2, 3);
                graphics.endFill();
                graphics.beginFill(0x000000);
                graphics.drawCircle(headX + 3, headY - 2, 1.5);
                graphics.endFill();
                break;
                
            case 'lizard':
                // Spots
                graphics.beginFill(this.parseColor(colors.spots || '#285028'));
                for (let i = 0; i < 3; i++) {
                    graphics.drawCircle(x + 8 + i * 12, y + 6, 2);
                }
                graphics.endFill();
                // Eye
                graphics.beginFill(this.parseColor(colors.eye || '#FFC800'));
                graphics.drawCircle(headX + 2, headY - 2, 2);
                graphics.endFill();
                break;
        }
        
        // Eyes (generic)
        graphics.beginFill(0x000000);
        graphics.drawCircle(headX - 2, headY - 2, 1.5);
        graphics.drawCircle(headX + 2, headY - 2, 1.5);
        graphics.endFill();
    }
    
    /**
     * Draw large animal (4-5 cells)
     */
    drawLargeAnimal(graphics, x, y, type, colors, cells) {
        const bodyColor = this.parseColor(colors.body || '#A9A9A9');
        const bellyColor = this.parseColor(colors.belly || '#D0D0D0');
        
        // Draw body
        cells.forEach(([dx, dy], i) => {
            const color = i === 0 ? bodyColor : (i % 2 === 0 ? bodyColor : bellyColor);
            graphics.beginFill(color);
            graphics.drawRoundedRect(
                x + dx * this.cellSize + 1,
                y + dy * this.cellSize + 1,
                this.cellSize - 2,
                this.cellSize - 2,
                4
            );
            graphics.endFill();
        });
        
        // Type-specific details
        const headX = x + this.cellSize / 2;
        const headY = y + this.cellSize / 2;
        
        if (type === 'fox') {
            // Ears
            graphics.beginFill(bodyColor);
            graphics.moveTo(headX - 4, headY - 6);
            graphics.lineTo(headX - 7, headY - 12);
            graphics.lineTo(headX - 1, headY - 6);
            graphics.closePath();
            graphics.moveTo(headX + 4, headY - 6);
            graphics.lineTo(headX + 7, headY - 12);
            graphics.lineTo(headX + 1, headY - 6);
            graphics.closePath();
            graphics.endFill();
            // White snout
            graphics.beginFill(0xFFFFFF);
            graphics.drawEllipse(headX, headY + 3, 4, 3);
            graphics.endFill();
        } else if (type === 'wolf') {
            // Muzzle
            graphics.beginFill(this.parseColor(colors.muzzle || '#64646E'));
            graphics.drawEllipse(headX, headY + 3, 5, 3);
            graphics.endFill();
        }
        
        // Eyes
        graphics.beginFill(0x000000);
        graphics.drawCircle(headX - 3, headY - 2, 2);
        graphics.drawCircle(headX + 3, headY - 2, 2);
        graphics.endFill();
    }
    
    /**
     * Draw huge animal (6-8 cells)
     */
    drawHugeAnimal(graphics, x, y, type, colors, cells) {
        const bodyColor = this.parseColor(colors.body || '#A9A9A9');
        const bellyColor = this.parseColor(colors.belly || '#D0D0D0');
        
        // Draw body with gradient
        cells.forEach(([dx, dy], i) => {
            // Shade based on position
            const shade = 1 - (dy * 0.1);
            const color = this.adjustBrightness(bodyColor, shade);
            
            graphics.beginFill(color);
            graphics.drawRoundedRect(
                x + dx * this.cellSize + 1,
                y + dy * this.cellSize + 1,
                this.cellSize - 2,
                this.cellSize - 2,
                4
            );
            graphics.endFill();
        });
        
        const headX = x + this.cellSize / 2;
        const headY = y + this.cellSize / 2;
        
        // Type-specific patterns
        if (type === 'tiger') {
            // Stripes
            graphics.lineStyle(2, this.parseColor(colors.stripes || '#281E14'));
            for (let i = 0; i < 3; i++) {
                graphics.moveTo(x + 5 + i * 15, y + 2);
                graphics.lineTo(x + 8 + i * 15, y + this.cellSize - 2);
            }
        } else if (type === 'elephant') {
            // Trunk hint
            graphics.lineStyle(3, bodyColor);
            graphics.moveTo(headX, headY + 5);
            graphics.lineTo(headX, headY + 12);
            // Tusks
            graphics.beginFill(this.parseColor(colors.tusk || '#FFFFF0'));
            graphics.drawEllipse(headX - 4, headY + 3, 2, 4);
            graphics.drawEllipse(headX + 4, headY + 3, 2, 4);
            graphics.endFill();
        }
        
        // Eyes
        graphics.beginFill(0x000000);
        graphics.drawCircle(headX - 4, headY - 2, 2);
        graphics.drawCircle(headX + 4, headY - 2, 2);
        graphics.endFill();
        
        // Highlight
        graphics.beginFill(0xFFFFFF, 0.2);
        graphics.drawCircle(headX - 3, headY - 3, 1);
        graphics.drawCircle(headX + 5, headY - 3, 1);
        graphics.endFill();
    }
    
    /**
     * Draw detailed snake using pooled graphics (returns next available index)
     */
    drawDetailedSnakePooled(snake, offsetX, offsetY, poolIndex) {
        if (!snake || !snake.body || snake.body.length === 0) return poolIndex;
        
        const baseColor = this.parseColor(snake.color);
        const baseAlpha = snake.alive ? 1 : 0.3;
        
        // Spawn freeze: snake is invulnerable and glowing
        const isSpawnFrozen = snake.spawn_freeze > 0;
        
        // Survival decay warning: compute how urgent the decay is (0 = safe, 1 = critical)
        let decayUrgency = 0;
        if (this.gameState?.mode === 'survival' && snake.alive && !isSpawnFrozen) {
            const interval = this.gameState.survival_decay_current_interval || 6;
            const timer = snake.decay_timer ?? interval;
            decayUrgency = 1 - Math.max(0, Math.min(1, timer / interval));
        }
        
        // Draw body segments from tail to head
        for (let i = snake.body.length - 1; i >= 0; i--) {
            const segment = snake.body[i];
            const x = offsetX + segment.x * this.cellSize;
            const y = offsetY + segment.y * this.cellSize;
            
            const isHead = i === 0;
            const isTail = i === snake.body.length - 1;
            
            // Calculate color gradient (brighter at head)
            const brightness = 0.6 + (1 - i / snake.body.length) * 0.4;
            let segColor = this.adjustBrightness(baseColor, brightness);
            
            // Spawn freeze effect: pulsing white tint
            if (isSpawnFrozen) {
                const pulse = 0.5 + 0.5 * Math.sin(this.frameCount * 0.2);
                segColor = this.blendColors(segColor, 0xFFFFFF, 0.3 + pulse * 0.3);
            }
            
            // Decay warning: fade last few tail segments when timer is low.
            // The more urgent, the more segments are affected and the more they pulse.
            let alpha = baseAlpha;
            if (decayUrgency > 0.4 && snake.alive) {
                // Tail segments to warn: scales from 1 (mild) up to 4 (critical)
                const warnCount = Math.floor(decayUrgency * 5);
                const segFromTail = snake.body.length - 1 - i; // 0 = tail end
                if (segFromTail < warnCount) {
                    const pulse = 0.35 + 0.65 * Math.abs(Math.sin(this.frameCount * 0.18 + segFromTail * 0.5));
                    alpha = baseAlpha * pulse;
                }
            }
            
            const graphics = this.getPooledSnakeGraphics(poolIndex);
            graphics.clear();
            graphics.visible = true;
            poolIndex++;
            
            if (isHead) {
                // Draw detailed head
                this.drawSnakeHead(graphics, x, y, snake.direction, segColor, alpha);
            } else if (isTail) {
                // Tapered tail
                graphics.beginFill(segColor, alpha);
                graphics.drawEllipse(
                    x + this.cellSize / 2,
                    y + this.cellSize / 2,
                    this.cellSize / 2 - 3,
                    this.cellSize / 2 - 4
                );
                graphics.endFill();
            } else {
                // Body segment with scale pattern
                graphics.beginFill(segColor, alpha);
                graphics.drawRoundedRect(x + 2, y + 2, this.cellSize - 4, this.cellSize - 4, 4);
                graphics.endFill();
                
                // Scale pattern
                const scaleColor = this.adjustBrightness(segColor, 0.8);
                graphics.beginFill(scaleColor, alpha * 0.5);
                graphics.drawEllipse(x + this.cellSize / 2, y + this.cellSize / 2, 3, 2);
                graphics.endFill();
                
                // Highlight
                graphics.beginFill(0xFFFFFF, 0.15 * alpha);
                graphics.drawRect(x + 3, y + 3, this.cellSize - 8, 2);
                graphics.endFill();
            }
        }
        
        return poolIndex;
    }
    
    /**
     * Draw snake head
     */
    drawSnakeHead(graphics, x, y, direction, color, alpha) {
        const cx = x + this.cellSize / 2;
        const cy = y + this.cellSize / 2;
        const size = this.cellSize / 2 - 1;
        
        // Head shape
        graphics.beginFill(color, alpha);
        graphics.drawRoundedRect(x + 1, y + 1, this.cellSize - 2, this.cellSize - 2, 5);
        graphics.endFill();
        
        // Darker top
        graphics.beginFill(this.adjustBrightness(color, 0.7), alpha * 0.3);
        graphics.drawRoundedRect(x + 2, y + 2, this.cellSize - 4, this.cellSize / 2 - 2, 3);
        graphics.endFill();
        
        // Eyes position based on direction
        let eye1X, eye1Y, eye2X, eye2Y;
        const eyeSize = 3;
        const eyeOffset = 4;
        
        switch (direction) {
            case 'up':
                eye1X = cx - eyeOffset; eye1Y = cy - 2;
                eye2X = cx + eyeOffset; eye2Y = cy - 2;
                break;
            case 'down':
                eye1X = cx - eyeOffset; eye1Y = cy + 2;
                eye2X = cx + eyeOffset; eye2Y = cy + 2;
                break;
            case 'left':
                eye1X = cx - 2; eye1Y = cy - eyeOffset;
                eye2X = cx - 2; eye2Y = cy + eyeOffset;
                break;
            default: // right
                eye1X = cx + 2; eye1Y = cy - eyeOffset;
                eye2X = cx + 2; eye2Y = cy + eyeOffset;
        }
        
        // Eye whites
        graphics.beginFill(0xFFFFFF, alpha);
        graphics.drawCircle(eye1X, eye1Y, eyeSize);
        graphics.drawCircle(eye2X, eye2Y, eyeSize);
        graphics.endFill();
        
        // Pupils
        graphics.beginFill(0x000000, alpha);
        graphics.drawCircle(eye1X, eye1Y, eyeSize - 1.5);
        graphics.drawCircle(eye2X, eye2Y, eyeSize - 1.5);
        graphics.endFill();
        
        // Eye shine
        graphics.beginFill(0xFFFFFF, alpha * 0.8);
        graphics.drawCircle(eye1X - 0.5, eye1Y - 0.5, 1);
        graphics.drawCircle(eye2X - 0.5, eye2Y - 0.5, 1);
        graphics.endFill();
        
        // Tongue (deterministic flickering based on frame count, not random)
        // Show tongue every 20 frames for 6 frames
        const tonguePhase = this.frameCount % 20;
        if (tonguePhase < 6) {
            graphics.lineStyle(1, 0xFF3333, alpha);
            let tongueX, tongueY, tongueEndX, tongueEndY;
            
            switch (direction) {
                case 'up':
                    tongueX = cx; tongueY = y;
                    tongueEndX = cx; tongueEndY = y - 4;
                    break;
                case 'down':
                    tongueX = cx; tongueY = y + this.cellSize;
                    tongueEndX = cx; tongueEndY = y + this.cellSize + 4;
                    break;
                case 'left':
                    tongueX = x; tongueY = cy;
                    tongueEndX = x - 4; tongueEndY = cy;
                    break;
                default:
                    tongueX = x + this.cellSize; tongueY = cy;
                    tongueEndX = x + this.cellSize + 4; tongueEndY = cy;
            }
            
            graphics.moveTo(tongueX, tongueY);
            graphics.lineTo(tongueEndX, tongueEndY);
            // Forked tongue
            if (direction === 'up' || direction === 'down') {
                graphics.moveTo(tongueEndX, tongueEndY);
                graphics.lineTo(tongueEndX - 2, tongueEndY + (direction === 'up' ? -2 : 2));
                graphics.moveTo(tongueEndX, tongueEndY);
                graphics.lineTo(tongueEndX + 2, tongueEndY + (direction === 'up' ? -2 : 2));
            } else {
                graphics.moveTo(tongueEndX, tongueEndY);
                graphics.lineTo(tongueEndX + (direction === 'left' ? -2 : 2), tongueEndY - 2);
                graphics.moveTo(tongueEndX, tongueEndY);
                graphics.lineTo(tongueEndX + (direction === 'left' ? -2 : 2), tongueEndY + 2);
            }
        }
    }
    
    /**
     * Parse color string to number
     */
    parseColor(colorStr) {
        if (typeof colorStr === 'number') return colorStr;
        if (typeof colorStr === 'string' && colorStr.startsWith('#')) {
            return parseInt(colorStr.replace('#', ''), 16);
        }
        return 0x808080; // Default gray
    }
    
    /**
     * Adjust color brightness
     */
    adjustBrightness(color, factor) {
        const r = Math.min(255, Math.floor(((color >> 16) & 0xFF) * factor));
        const g = Math.min(255, Math.floor(((color >> 8) & 0xFF) * factor));
        const b = Math.min(255, Math.floor((color & 0xFF) * factor));
        return (r << 16) | (g << 8) | b;
    }
    
    /**
     * Blend two colors together
     */
    blendColors(color1, color2, amount) {
        const r1 = (color1 >> 16) & 0xFF;
        const g1 = (color1 >> 8) & 0xFF;
        const b1 = color1 & 0xFF;
        const r2 = (color2 >> 16) & 0xFF;
        const g2 = (color2 >> 8) & 0xFF;
        const b2 = color2 & 0xFF;
        const r = Math.round(r1 + (r2 - r1) * amount);
        const g = Math.round(g1 + (g2 - g1) * amount);
        const b = Math.round(b1 + (b2 - b1) * amount);
        return (r << 16) | (g << 8) | b;
    }
    
    /**
     * Update HUD elements
     */
    updateHUD() {
        if (!this.gameState) return;

        this.hud.updateTimer(
            this.gameState.elapsed_time,
            this.gameState.time_limit,
            this.gameState.mode
        );

        // Barrier points multiplier
        const barrierMults = { none: 1.0, sparse: 1.25, moderate: 1.5, dense: 2.0 };
        const barrierMult = barrierMults[this.gameState.barrier_density] || 1.0;

        // Update left sidebar standings
        this.hud.updateSidebar(this.gameState.players, this.gameState.mode, barrierMult);

        // Survival/Duel mode: show global speed multiplier in sidebar
        if (this.gameState.mode === 'survival' || this.gameState.mode === 'duel') {
            const baseSpeed = 100;
            const currentSpeed = this.gameState.current_speed || baseSpeed;
            const speedMult = baseSpeed / currentSpeed;
            this.hud.updateSurvivalSpeed(speedMult);
        } else {
            this.hud.hideSurvivalPressure();
        }

        // Duel series bar
        if (this.gameState.mode === 'duel' && this.gameState.series_length > 0) {
            this.hud.updateDuelSeriesBar(
                this.gameState.players,
                this.gameState.series_scores || {},
                this.gameState.current_round || 1,
                this.gameState.series_length
            );
        }

        // Show "Leave Game" overlay when current player dies in Survival mode
        if (this.gameState.mode === 'survival' && this.gameState.running) {
            const myPlayer = this.gameState.players[this.playerId];
            const iAmDead = myPlayer && myPlayer.snake && !myPlayer.snake.alive;
            if (iAmDead && !this._deadOverlayShown) {
                this._deadOverlayShown = true;
                this.hud.showDeadOverlay(() => {
                    if (this.onLeaveGame) this.onLeaveGame();
                });
            }
        }
    }
    
    /**
     * Handle food eaten event (for particles)
     */
    onFoodEaten(playerId, position) {
        const x = this.padding + position.x * this.cellSize + this.cellSize / 2;
        const y = this.padding + 30 + position.y * this.cellSize + this.cellSize / 2;
        
        const player = this.gameState?.players[playerId];
        const color = player?.snake ? parseInt(player.snake.color.replace('#', ''), 16) : 0x22C55E;
        
        this.renderer.addParticle(x, y, color, 15);
    }
    
    /**
     * Handle player death event
     */
    onPlayerDeath(playerId) {
        const player = this.gameState?.players[playerId];
        if (!player?.snake) return;
        
        const head = player.snake.body[0];
        if (!head) return;
        
        const x = this.padding + head.x * this.cellSize + this.cellSize / 2;
        const y = this.padding + 30 + head.y * this.cellSize + this.cellSize / 2;
        
        this.renderer.addParticle(x, y, 0xEF4444, 30);
    }
    
    /**
     * Handle game over
     */
    onGameOver(winnerId, finalState, seriesScores = null) {
        this.running = false;
        this.gameState = finalState;
        this.render();
        
        this.hud.showGameOver(winnerId, finalState.players, finalState.mode, seriesScores);
    }
}

export default SnakeGame;
