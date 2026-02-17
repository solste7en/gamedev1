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
        
        // Visual settings
        this.cellSize = 16;
        this.padding = 10;
        
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
        
        const quadrantWidth = this.gameState.quadrant_bounds[0] 
            ? (this.gameState.quadrant_bounds[0].x_max - this.gameState.quadrant_bounds[0].x_min)
            : 20;
        const quadrantHeight = this.gameState.quadrant_bounds[0]
            ? (this.gameState.quadrant_bounds[0].y_max - this.gameState.quadrant_bounds[0].y_min)
            : 20;
        
        const width = cols * quadrantWidth * this.cellSize + this.padding * 2;
        const height = rows * quadrantHeight * this.cellSize + this.padding * 2 + 50; // Extra for labels
        
        this.renderer.resize(width, height);
        this.renderer.setGrid(quadrantWidth * cols, quadrantHeight * rows, this.cellSize);
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
     * Render the game
     */
    render() {
        if (!this.gameState) return;
        
        this.renderer.clear();
        
        // Render each player's quadrant
        for (const [playerId, player] of Object.entries(this.gameState.players)) {
            const bounds = this.gameState.quadrant_bounds[player.quadrant];
            if (!bounds) continue;
            
            const color = player.snake ? player.snake.color : '#FFFFFF';
            const isAlive = player.snake ? player.snake.alive : false;
            
            // Draw quadrant background
            this.renderer.drawQuadrantBackground(
                bounds, 
                color, 
                isAlive,
                this.padding,
                this.padding + 30  // Offset for player name
            );
            
            // Draw walls in this quadrant
            const walls = this.gameState.walls[player.quadrant] || [];
            walls.forEach(wall => {
                this.drawWall(wall, this.padding, this.padding + 30);
            });
            
            // Draw player name above quadrant
            const quadrantX = this.padding + bounds.x_min * this.cellSize;
            const quadrantWidth = (bounds.x_max - bounds.x_min) * this.cellSize;
            
            this.renderer.drawText(
                `${player.name}${!isAlive ? ' (DEAD)' : ''}`,
                quadrantX + quadrantWidth / 2,
                this.padding + 15,
                {
                    fontSize: 12,
                    fill: parseInt(color.replace('#', ''), 16),
                    fontWeight: 'bold'
                }
            );
            
            // Draw food in this quadrant
            const foods = this.gameState.foods[player.quadrant] || [];
            foods.forEach(food => {
                this.drawAnimal(food, this.padding, this.padding + 30);
            });
            
            // Draw snake
            if (player.snake) {
                this.drawDetailedSnake(player.snake, this.padding, this.padding + 30);
                
                // Add eat particles
                if (player.snake.combo > 0) {
                    const head = player.snake.body[0];
                    if (head) {
                        const x = this.padding + head.x * this.cellSize + this.cellSize / 2;
                        const y = this.padding + 30 + head.y * this.cellSize + this.cellSize / 2;
                        
                        // Combo indicator
                        this.renderer.drawText(
                            `x${player.snake.combo}`,
                            x,
                            y - 20,
                            {
                                fontSize: 10,
                                fill: 0xF1C40F,
                                fontWeight: 'bold'
                            }
                        );
                    }
                }
            }
        }
    }
    
    /**
     * Draw a wall/barrier
     */
    drawWall(wall, offsetX, offsetY) {
        const x = offsetX + wall.position.x * this.cellSize;
        const y = offsetY + wall.position.y * this.cellSize;
        const width = wall.width * this.cellSize;
        const height = wall.height * this.cellSize;
        
        const graphics = new PIXI.Graphics();
        
        // Brick colors
        const brickColor = 0x654321;
        const brickLight = 0x8B5A2B;
        const mortarColor = 0x505050;
        
        // Draw mortar background
        graphics.beginFill(mortarColor);
        graphics.drawRect(x, y, width, height);
        graphics.endFill();
        
        // Draw bricks
        const brickW = this.cellSize / 2 - 1;
        const brickH = this.cellSize / 3 - 1;
        
        for (let by = 0; by < height; by += brickH + 1) {
            const rowOffset = (Math.floor(by / (brickH + 1)) % 2) * (brickW / 2);
            for (let bx = -brickW; bx < width + brickW; bx += brickW + 1) {
                const brick_x = x + bx + rowOffset;
                const brick_y = y + by;
                
                // Check if brick is within wall bounds
                if (brick_x >= x - 1 && brick_x + brickW <= x + width + 1 &&
                    brick_y >= y && brick_y + brickH <= y + height) {
                    
                    // Random brick color variation
                    const color = Math.random() > 0.3 ? brickColor : brickLight;
                    
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
        
        this.renderer.gameContainer.addChild(graphics);
    }
    
    /**
     * Draw detailed animal based on type
     */
    drawAnimal(food, offsetX, offsetY) {
        const baseX = offsetX + food.position.x * this.cellSize;
        const baseY = offsetY + food.position.y * this.cellSize;
        const colors = food.colors || {};
        const type = food.type;
        const cells = food.cells || [[0, 0]];
        
        const graphics = new PIXI.Graphics();
        
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
        
        // Health bar for multi-hit animals
        if (food.max_health > 1) {
            const totalWidth = cells.length > 1 ? 
                (Math.max(...cells.map(c => c[0])) + 1) * this.cellSize : this.cellSize;
            const healthPercent = food.health / food.max_health;
            
            // Background
            graphics.beginFill(0x333333);
            graphics.drawRect(baseX, baseY - 5, totalWidth - 2, 4);
            graphics.endFill();
            
            // Health fill
            const healthColor = healthPercent > 0.5 ? 0x22C55E : 
                               healthPercent > 0.25 ? 0xF59E0B : 0xEF4444;
            graphics.beginFill(healthColor);
            graphics.drawRect(baseX, baseY - 5, (totalWidth - 2) * healthPercent, 4);
            graphics.endFill();
        }
        
        this.renderer.gameContainer.addChild(graphics);
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
     * Draw detailed snake
     */
    drawDetailedSnake(snake, offsetX, offsetY) {
        if (!snake || !snake.body || snake.body.length === 0) return;
        
        const baseColor = this.parseColor(snake.color);
        const alpha = snake.alive ? 1 : 0.3;
        
        // Draw body segments from tail to head
        for (let i = snake.body.length - 1; i >= 0; i--) {
            const segment = snake.body[i];
            const x = offsetX + segment.x * this.cellSize;
            const y = offsetY + segment.y * this.cellSize;
            
            const isHead = i === 0;
            const isTail = i === snake.body.length - 1;
            
            // Calculate color gradient (brighter at head)
            const brightness = 0.6 + (1 - i / snake.body.length) * 0.4;
            const segColor = this.adjustBrightness(baseColor, brightness);
            
            const graphics = new PIXI.Graphics();
            
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
            
            this.renderer.gameContainer.addChild(graphics);
        }
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
        
        // Tongue (flickering effect based on time)
        if (Math.random() > 0.7) {
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
    onGameOver(winnerId, finalState) {
        this.running = false;
        this.gameState = finalState;
        this.render();
        
        this.hud.showGameOver(winnerId, finalState.players, finalState.mode);
    }
}

export default SnakeGame;
