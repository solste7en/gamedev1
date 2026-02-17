/**
 * Snake3DGame - Snake 3D (oblique view) multiplayer game renderer
 * Stardew Valley-style 2.5D view with proper oblique projection
 */

import { ParticleSystem } from '../engine/ParticleSystem.js';

export class Snake3DGame {
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
        
        // Oblique projection settings
        this.cellWidth = 24;
        this.cellHeight = 16;
        this.cellDepth = 10;
        this.obliqueShift = 0.4;  // How much Y affects X (0.5 = 45 degree angle)
        this.padding = 30;
        
        // Particle system
        this.particles = null;
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
        
        // Calculate canvas size
        await this.calculateSize();
        
        return this;
    }
    
    /**
     * Calculate and set renderer size
     */
    async calculateSize() {
        // Will be recalculated when game state arrives
        const width = 1000;
        const height = 700;
        
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
        
        const numPlayers = Object.keys(this.gameState.players).length;
        const isSinglePlayer = this.gameState.mode === 'single_player' || numPlayers === 1;
        
        // Calculate grid dimensions
        let cols, rows;
        if (isSinglePlayer) {
            cols = 1;
            rows = 1;
        } else if (numPlayers <= 2) {
            cols = 2;
            rows = 1;
        } else {
            cols = 2;
            rows = 2;
        }
        
        const bounds = this.gameState.quadrant_bounds[0];
        const gridW = bounds ? (bounds.x_max - bounds.x_min) : 20;
        const gridH = bounds ? (bounds.y_max - bounds.y_min) : 20;
        
        // Calculate quadrant pixel dimensions with oblique shift
        const quadrantPixelWidth = gridW * this.cellWidth + gridH * (this.cellWidth * this.obliqueShift);
        const quadrantPixelHeight = gridH * this.cellHeight + this.cellDepth;
        
        const width = cols * quadrantPixelWidth + this.padding * (cols + 1);
        const height = rows * quadrantPixelHeight + this.padding * (rows + 1) + 60;
        
        this.renderer.resize(width, height);
    }
    
    /**
     * Convert grid position to screen position (oblique projection)
     */
    gridToScreen(gridX, gridY, offsetX = 0, offsetY = 0) {
        // Oblique projection: Y position shifts X to the right
        const screenX = offsetX + gridX * this.cellWidth + gridY * (this.cellWidth * this.obliqueShift);
        const screenY = offsetY + gridY * this.cellHeight;
        return { x: screenX, y: screenY };
    }
    
    /**
     * Start the game
     */
    start() {
        this.running = true;
        this.hud.reset();
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
     * Update game state from server
     */
    updateState(state) {
        const firstUpdate = !this.gameState;
        this.prevState = this.gameState;
        this.gameState = state;
        
        if (firstUpdate) {
            this.updateCanvasSize();
        }
        
        // Detect score changes
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
                    const bounds = this.gameState.quadrant_bounds[player.quadrant];
                    if (bounds) {
                        const pos = this.gridToScreen(
                            head.x - bounds.x_min,
                            head.y - bounds.y_min,
                            this.padding,
                            this.padding + 50
                        );
                        const color = parseInt(player.snake.color.replace('#', ''), 16);
                        
                        // Add eat particles
                        if (this.particles) {
                            this.particles.eatEffect(pos.x + this.cellWidth / 2, pos.y + this.cellHeight / 2, color);
                        }
                    }
                }
                
                // Play sound for local player
                if (this.sound && parseInt(playerId) === this.playerId) {
                    const scoreDiff = player.snake.score - prevPlayer.snake.score;
                    if (scoreDiff > 50) {
                        this.sound.play('eat_large');
                    } else {
                        this.sound.play('eat');
                    }
                }
            }
            
            // Death detection
            if (prevPlayer.snake.alive && !player.snake.alive) {
                const head = player.snake.body[0];
                if (head && this.particles) {
                    const bounds = this.gameState.quadrant_bounds[player.quadrant];
                    if (bounds) {
                        const pos = this.gridToScreen(
                            head.x - bounds.x_min,
                            head.y - bounds.y_min,
                            this.padding,
                            this.padding + 50
                        );
                        const color = parseInt(player.snake.color.replace('#', ''), 16);
                        this.particles.deathEffect(pos.x + this.cellWidth / 2, pos.y + this.cellHeight / 2, color);
                    }
                }
            }
        }
    }
    
    /**
     * Render the game
     */
    render() {
        if (!this.gameState) return;
        
        this.renderer.clear();
        
        const numPlayers = Object.keys(this.gameState.players).length;
        const isSinglePlayer = this.gameState.mode === 'single_player' || numPlayers === 1;
        
        // Calculate layout
        let cols = isSinglePlayer ? 1 : (numPlayers <= 2 ? 2 : 2);
        let rows = isSinglePlayer ? 1 : (numPlayers <= 2 ? 1 : 2);
        
        const bounds0 = this.gameState.quadrant_bounds[0];
        const gridW = bounds0 ? (bounds0.x_max - bounds0.x_min) : 20;
        const gridH = bounds0 ? (bounds0.y_max - bounds0.y_min) : 20;
        
        const quadrantPixelWidth = gridW * this.cellWidth + gridH * (this.cellWidth * this.obliqueShift);
        const quadrantPixelHeight = gridH * this.cellHeight + this.cellDepth;
        
        // Render each player's quadrant
        let quadrantIndex = 0;
        for (const [playerId, player] of Object.entries(this.gameState.players)) {
            const bounds = this.gameState.quadrant_bounds[player.quadrant];
            if (!bounds) continue;
            
            // Calculate quadrant screen position
            const col = quadrantIndex % cols;
            const row = Math.floor(quadrantIndex / cols);
            const offsetX = this.padding + col * (quadrantPixelWidth + this.padding);
            const offsetY = this.padding + 50 + row * (quadrantPixelHeight + 60);
            
            const color = player.snake ? player.snake.color : '#FFFFFF';
            const isAlive = player.snake ? player.snake.alive : false;
            
            // Draw quadrant (parallelogram)
            this.drawQuadrant3D(bounds, offsetX, offsetY, color, isAlive);
            
            // Draw player name
            this.renderer.drawText(
                `${player.name}${!isAlive ? ' (DEAD)' : ''}`,
                offsetX + quadrantPixelWidth / 2,
                offsetY - 35,
                {
                    fontSize: 14,
                    fill: parseInt(color.replace('#', ''), 16),
                    fontWeight: 'bold'
                }
            );
            
            // Draw score
            const score = player.snake ? player.snake.score : 0;
            this.renderer.drawText(
                `Score: ${score}`,
                offsetX + quadrantPixelWidth / 2,
                offsetY - 18,
                {
                    fontSize: 11,
                    fill: 0x94A3B8
                }
            );
            
            // Draw walls
            const walls = this.gameState.walls[player.quadrant] || [];
            walls.forEach(wall => {
                this.drawWall3D(wall, bounds, offsetX, offsetY);
            });
            
            // Draw food
            const foods = this.gameState.foods[player.quadrant] || [];
            foods.forEach(food => {
                this.drawFood3D(food, bounds, offsetX, offsetY);
            });
            
            // Draw snake
            if (player.snake) {
                this.drawSnake3D(player.snake, bounds, offsetX, offsetY);
                
                // Combo indicator
                if (player.snake.combo > 0) {
                    const head = player.snake.body[0];
                    if (head) {
                        const headPos = this.gridToScreen(
                            head.x - bounds.x_min,
                            head.y - bounds.y_min,
                            offsetX, offsetY
                        );
                        this.renderer.drawText(
                            `x${player.snake.combo}`,
                            headPos.x + this.cellWidth / 2,
                            headPos.y - 15,
                            {
                                fontSize: 12,
                                fill: 0xF1C40F,
                                fontWeight: 'bold'
                            }
                        );
                    }
                }
            }
            
            quadrantIndex++;
        }
    }
    
    /**
     * Draw 3D quadrant background (parallelogram)
     */
    drawQuadrant3D(bounds, offsetX, offsetY, playerColor, isAlive) {
        const gridW = bounds.x_max - bounds.x_min;
        const gridH = bounds.y_max - bounds.y_min;
        const color = parseInt(playerColor.replace('#', ''), 16);
        
        // Calculate corners of parallelogram
        const topLeft = this.gridToScreen(0, 0, offsetX, offsetY);
        const topRight = this.gridToScreen(gridW, 0, offsetX, offsetY);
        const bottomLeft = this.gridToScreen(0, gridH, offsetX, offsetY);
        const bottomRight = this.gridToScreen(gridW, gridH, offsetX, offsetY);
        
        // Draw grass/ground tiles (parallelogram shaped)
        for (let y = 0; y < gridH; y++) {
            for (let x = 0; x < gridW; x++) {
                const tl = this.gridToScreen(x, y, offsetX, offsetY);
                const tr = this.gridToScreen(x + 1, y, offsetX, offsetY);
                const bl = this.gridToScreen(x, y + 1, offsetX, offsetY);
                const br = this.gridToScreen(x + 1, y + 1, offsetX, offsetY);
                
                // Checkerboard grass pattern
                const isLight = (x + y) % 2 === 0;
                const grassColor = isAlive 
                    ? (isLight ? 0x4ADE80 : 0x22C55E)
                    : (isLight ? 0x475569 : 0x334155);
                
                // Draw tile as parallelogram
                const tile = new PIXI.Graphics();
                tile.beginFill(grassColor);
                tile.moveTo(tl.x, tl.y);
                tile.lineTo(tr.x, tr.y);
                tile.lineTo(br.x, br.y);
                tile.lineTo(bl.x, bl.y);
                tile.closePath();
                tile.endFill();
                this.renderer.gameContainer.addChild(tile);
            }
        }
        
        // Draw border with depth effect
        const border = new PIXI.Graphics();
        
        // Bottom edge (3D depth) - parallelogram bottom
        border.beginFill(isAlive ? 0x166534 : 0x1E293B);
        border.moveTo(bottomLeft.x, bottomLeft.y);
        border.lineTo(bottomRight.x, bottomRight.y);
        border.lineTo(bottomRight.x, bottomRight.y + this.cellDepth);
        border.lineTo(bottomLeft.x, bottomLeft.y + this.cellDepth);
        border.closePath();
        border.endFill();
        
        // Right edge (3D depth)
        border.beginFill(isAlive ? 0x15803D : 0x334155);
        border.moveTo(topRight.x, topRight.y);
        border.lineTo(bottomRight.x, bottomRight.y);
        border.lineTo(bottomRight.x, bottomRight.y + this.cellDepth);
        border.lineTo(topRight.x, topRight.y + this.cellDepth);
        border.closePath();
        border.endFill();
        
        // Border outline (parallelogram)
        border.lineStyle(2, color, isAlive ? 1 : 0.3);
        border.moveTo(topLeft.x, topLeft.y);
        border.lineTo(topRight.x, topRight.y);
        border.lineTo(bottomRight.x, bottomRight.y);
        border.lineTo(bottomLeft.x, bottomLeft.y);
        border.closePath();
        
        this.renderer.gameContainer.addChild(border);
    }
    
    /**
     * Draw 3D wall
     */
    drawWall3D(wall, bounds, offsetX, offsetY) {
        const brickColor = 0x8B4513;
        const brickLight = 0xA0522D;
        const mortarColor = 0x505050;
        
        // Draw each cell of the wall
        for (let dy = 0; dy < wall.height; dy++) {
            for (let dx = 0; dx < wall.width; dx++) {
                const x = wall.position.x + dx - bounds.x_min;
                const y = wall.position.y + dy - bounds.y_min;
                
                const tl = this.gridToScreen(x, y, offsetX, offsetY);
                const tr = this.gridToScreen(x + 1, y, offsetX, offsetY);
                const bl = this.gridToScreen(x, y + 1, offsetX, offsetY);
                const br = this.gridToScreen(x + 1, y + 1, offsetX, offsetY);
                
                const graphics = new PIXI.Graphics();
                
                // Top face
                const topColor = Math.random() > 0.3 ? brickColor : brickLight;
                graphics.beginFill(topColor);
                graphics.moveTo(tl.x + 1, tl.y + 1);
                graphics.lineTo(tr.x - 1, tr.y + 1);
                graphics.lineTo(br.x - 1, br.y - 1);
                graphics.lineTo(bl.x + 1, bl.y - 1);
                graphics.closePath();
                graphics.endFill();
                
                // Front face (3D depth)
                graphics.beginFill(this.adjustBrightness(topColor, 0.6));
                graphics.moveTo(bl.x + 1, bl.y - 1);
                graphics.lineTo(br.x - 1, br.y - 1);
                graphics.lineTo(br.x - 1, br.y + this.cellDepth - 2);
                graphics.lineTo(bl.x + 1, bl.y + this.cellDepth - 2);
                graphics.closePath();
                graphics.endFill();
                
                // Right face (3D depth)
                graphics.beginFill(this.adjustBrightness(topColor, 0.5));
                graphics.moveTo(tr.x - 1, tr.y + 1);
                graphics.lineTo(br.x - 1, br.y - 1);
                graphics.lineTo(br.x - 1, br.y + this.cellDepth - 2);
                graphics.lineTo(tr.x - 1, tr.y + this.cellDepth);
                graphics.closePath();
                graphics.endFill();
                
                // Mortar lines
                graphics.lineStyle(1, mortarColor, 0.5);
                graphics.moveTo(tl.x + 1, tl.y + 1);
                graphics.lineTo(tr.x - 1, tr.y + 1);
                graphics.lineTo(br.x - 1, br.y - 1);
                graphics.lineTo(bl.x + 1, bl.y - 1);
                graphics.closePath();
                
                this.renderer.gameContainer.addChild(graphics);
            }
        }
    }
    
    /**
     * Draw 3D snake
     */
    drawSnake3D(snake, bounds, offsetX, offsetY) {
        if (!snake || !snake.body || snake.body.length === 0) return;
        
        const color = parseInt(snake.color.replace('#', ''), 16);
        const alpha = snake.alive ? 1 : 0.3;
        
        // Draw from tail to head so head is on top
        for (let i = snake.body.length - 1; i >= 0; i--) {
            const segment = snake.body[i];
            const localX = segment.x - bounds.x_min;
            const localY = segment.y - bounds.y_min;
            
            const tl = this.gridToScreen(localX, localY, offsetX, offsetY);
            const tr = this.gridToScreen(localX + 1, localY, offsetX, offsetY);
            const bl = this.gridToScreen(localX, localY + 1, offsetX, offsetY);
            const br = this.gridToScreen(localX + 1, localY + 1, offsetX, offsetY);
            
            const isHead = i === 0;
            const isTail = i === snake.body.length - 1;
            
            // Brightness gradient
            const brightness = 1 - (i / snake.body.length) * 0.4;
            const segColor = this.adjustBrightness(color, brightness);
            
            const graphics = new PIXI.Graphics();
            
            // Shadow
            graphics.beginFill(0x000000, 0.2 * alpha);
            const shadowCenter = {
                x: (tl.x + tr.x + bl.x + br.x) / 4,
                y: (bl.y + br.y) / 2 + this.cellDepth
            };
            graphics.drawEllipse(shadowCenter.x, shadowCenter.y, this.cellWidth / 2 - 2, 4);
            graphics.endFill();
            
            // 3D body (front face)
            const sideColor = this.adjustBrightness(segColor, 0.7);
            graphics.beginFill(sideColor, alpha);
            graphics.moveTo(bl.x + 3, bl.y - 2);
            graphics.lineTo(br.x - 3, br.y - 2);
            graphics.lineTo(br.x - 3, br.y + this.cellDepth - 4);
            graphics.lineTo(bl.x + 3, bl.y + this.cellDepth - 4);
            graphics.closePath();
            graphics.endFill();
            
            // Top of segment (parallelogram)
            graphics.beginFill(segColor, alpha);
            if (isHead) {
                // Rounded head
                const centerX = (tl.x + tr.x + bl.x + br.x) / 4;
                const centerY = (tl.y + tr.y + bl.y + br.y) / 4;
                graphics.drawEllipse(centerX, centerY, this.cellWidth / 2 - 2, this.cellHeight / 2 - 1);
            } else if (isTail) {
                // Tapered tail
                const centerX = (tl.x + tr.x + bl.x + br.x) / 4;
                const centerY = (tl.y + tr.y + bl.y + br.y) / 4;
                graphics.drawEllipse(centerX, centerY, this.cellWidth / 2 - 4, this.cellHeight / 2 - 2);
            } else {
                // Body segment
                graphics.moveTo(tl.x + 3, tl.y + 2);
                graphics.lineTo(tr.x - 3, tr.y + 2);
                graphics.lineTo(br.x - 3, br.y - 2);
                graphics.lineTo(bl.x + 3, bl.y - 2);
                graphics.closePath();
            }
            graphics.endFill();
            
            // Scale pattern for body
            if (!isHead && !isTail) {
                const centerX = (tl.x + tr.x + bl.x + br.x) / 4;
                const centerY = (tl.y + tr.y + bl.y + br.y) / 4;
                graphics.beginFill(this.adjustBrightness(segColor, 0.85), alpha * 0.5);
                graphics.drawEllipse(centerX, centerY, 4, 2);
                graphics.endFill();
            }
            
            // Eyes for head
            if (isHead) {
                const centerX = (tl.x + tr.x + bl.x + br.x) / 4;
                const centerY = (tl.y + tr.y + bl.y + br.y) / 4;
                
                // Eye whites
                graphics.beginFill(0xFFFFFF, alpha);
                const eyeSize = 3;
                let eye1X, eye1Y, eye2X, eye2Y;
                
                if (snake.direction === 'right') {
                    eye1X = centerX + 5; eye1Y = centerY - 3;
                    eye2X = centerX + 5; eye2Y = centerY + 3;
                } else if (snake.direction === 'left') {
                    eye1X = centerX - 5; eye1Y = centerY - 3;
                    eye2X = centerX - 5; eye2Y = centerY + 3;
                } else if (snake.direction === 'up') {
                    eye1X = centerX - 4; eye1Y = centerY - 2;
                    eye2X = centerX + 4; eye2Y = centerY - 2;
                } else { // down
                    eye1X = centerX - 4; eye1Y = centerY + 2;
                    eye2X = centerX + 4; eye2Y = centerY + 2;
                }
                
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
                
                // Tongue (flickering)
                if (Math.random() > 0.6) {
                    graphics.lineStyle(1, 0xFF3333, alpha);
                    let tongueEndX, tongueEndY;
                    
                    if (snake.direction === 'right') {
                        tongueEndX = centerX + this.cellWidth / 2 + 5;
                        tongueEndY = centerY;
                    } else if (snake.direction === 'left') {
                        tongueEndX = centerX - this.cellWidth / 2 - 5;
                        tongueEndY = centerY;
                    } else if (snake.direction === 'up') {
                        tongueEndX = centerX;
                        tongueEndY = centerY - this.cellHeight / 2 - 5;
                    } else {
                        tongueEndX = centerX;
                        tongueEndY = centerY + this.cellHeight / 2 + 5;
                    }
                    
                    graphics.moveTo(centerX, centerY);
                    graphics.lineTo(tongueEndX, tongueEndY);
                    // Forked tongue
                    if (snake.direction === 'left' || snake.direction === 'right') {
                        graphics.moveTo(tongueEndX, tongueEndY);
                        graphics.lineTo(tongueEndX + (snake.direction === 'right' ? 3 : -3), tongueEndY - 2);
                        graphics.moveTo(tongueEndX, tongueEndY);
                        graphics.lineTo(tongueEndX + (snake.direction === 'right' ? 3 : -3), tongueEndY + 2);
                    } else {
                        graphics.moveTo(tongueEndX, tongueEndY);
                        graphics.lineTo(tongueEndX - 2, tongueEndY + (snake.direction === 'down' ? 3 : -3));
                        graphics.moveTo(tongueEndX, tongueEndY);
                        graphics.lineTo(tongueEndX + 2, tongueEndY + (snake.direction === 'down' ? 3 : -3));
                    }
                }
            }
            
            this.renderer.gameContainer.addChild(graphics);
        }
    }
    
    /**
     * Draw 3D food/animal
     */
    drawFood3D(food, bounds, offsetX, offsetY) {
        const localX = food.position.x - bounds.x_min;
        const localY = food.position.y - bounds.y_min;
        
        const tl = this.gridToScreen(localX, localY, offsetX, offsetY);
        const tr = this.gridToScreen(localX + 1, localY, offsetX, offsetY);
        const bl = this.gridToScreen(localX, localY + 1, offsetX, offsetY);
        const br = this.gridToScreen(localX + 1, localY + 1, offsetX, offsetY);
        
        const centerX = (tl.x + tr.x + bl.x + br.x) / 4;
        const centerY = (tl.y + tr.y + bl.y + br.y) / 4;
        
        const color = parseInt(food.color.replace('#', ''), 16);
        const size = Math.min(food.size || 1, 3) * 3 + 5;
        
        const graphics = new PIXI.Graphics();
        
        // Shadow
        graphics.beginFill(0x000000, 0.2);
        graphics.drawEllipse(centerX, centerY + this.cellDepth, size + 2, 4);
        graphics.endFill();
        
        // 3D effect (bottom ellipsoid)
        graphics.beginFill(this.adjustBrightness(color, 0.6));
        graphics.drawEllipse(centerX, centerY + 4, size, size * 0.5);
        graphics.endFill();
        
        // Main body
        graphics.beginFill(color);
        graphics.drawCircle(centerX, centerY, size);
        graphics.endFill();
        
        // Highlight
        graphics.beginFill(0xFFFFFF, 0.3);
        graphics.drawCircle(centerX - size / 3, centerY - size / 3, size / 3);
        graphics.endFill();
        
        // Draw animal details based on type
        if (food.type) {
            this.drawAnimalDetails(graphics, centerX, centerY, size, food.type, food.colors || {});
        }
        
        this.renderer.gameContainer.addChild(graphics);
        
        // Health bar for multi-hit animals
        if (food.max_health > 1) {
            const healthGraphics = new PIXI.Graphics();
            const barWidth = size * 2;
            const barHeight = 4;
            const healthPercent = food.health / food.max_health;
            
            // Background
            healthGraphics.beginFill(0x333333);
            healthGraphics.drawRect(centerX - barWidth / 2, centerY - size - 8, barWidth, barHeight);
            healthGraphics.endFill();
            
            // Health fill
            const healthColor = healthPercent > 0.5 ? 0x22C55E : 
                               healthPercent > 0.25 ? 0xF59E0B : 0xEF4444;
            healthGraphics.beginFill(healthColor);
            healthGraphics.drawRect(centerX - barWidth / 2, centerY - size - 8, barWidth * healthPercent, barHeight);
            healthGraphics.endFill();
            
            this.renderer.gameContainer.addChild(healthGraphics);
        }
    }
    
    /**
     * Draw animal-specific details
     */
    drawAnimalDetails(graphics, x, y, size, type, colors) {
        switch (type) {
            case 'mouse':
                // Ears
                graphics.beginFill(0xFFB6C1);
                graphics.drawCircle(x - size * 0.5, y - size * 0.7, size * 0.3);
                graphics.drawCircle(x + size * 0.5, y - size * 0.7, size * 0.3);
                graphics.endFill();
                // Eyes
                graphics.beginFill(0x000000);
                graphics.drawCircle(x - 2, y - 1, 1.5);
                graphics.drawCircle(x + 2, y - 1, 1.5);
                graphics.endFill();
                break;
                
            case 'frog':
                // Eyes (bulging)
                graphics.beginFill(0xFFD700);
                graphics.drawCircle(x - size * 0.4, y - size * 0.4, size * 0.35);
                graphics.drawCircle(x + size * 0.4, y - size * 0.4, size * 0.35);
                graphics.endFill();
                graphics.beginFill(0x000000);
                graphics.drawCircle(x - size * 0.4, y - size * 0.4, size * 0.15);
                graphics.drawCircle(x + size * 0.4, y - size * 0.4, size * 0.15);
                graphics.endFill();
                break;
                
            case 'butterfly':
                // Wings
                graphics.beginFill(0xFF69B4, 0.7);
                graphics.drawEllipse(x - size * 0.7, y, size * 0.8, size * 0.5);
                graphics.drawEllipse(x + size * 0.7, y, size * 0.8, size * 0.5);
                graphics.endFill();
                break;
                
            case 'rabbit':
                // Ears
                graphics.beginFill(0xFFFFFF);
                graphics.drawEllipse(x - 3, y - size - 3, 2, 5);
                graphics.drawEllipse(x + 3, y - size - 3, 2, 5);
                graphics.endFill();
                graphics.beginFill(0xFFB6C1);
                graphics.drawEllipse(x - 3, y - size - 3, 1, 3);
                graphics.drawEllipse(x + 3, y - size - 3, 1, 3);
                graphics.endFill();
                break;
                
            default:
                // Generic eyes
                graphics.beginFill(0x000000);
                graphics.drawCircle(x - 2, y - 1, 1.5);
                graphics.drawCircle(x + 2, y - 1, 1.5);
                graphics.endFill();
        }
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
     * Update HUD elements
     */
    updateHUD() {
        if (!this.gameState) return;
        
        this.hud.updateTimer(
            this.gameState.elapsed_time,
            this.gameState.time_limit,
            this.gameState.mode
        );
        
        this.hud.updateScoreboard(this.gameState.players);
    }
    
    /**
     * Handle game over
     */
    onGameOver(winnerId, finalState) {
        this.running = false;
        this.gameState = finalState;
        this.render();
        
        this.hud.showGameOver(winnerId, finalState.players, finalState.mode);
    }
}

export default Snake3DGame;
