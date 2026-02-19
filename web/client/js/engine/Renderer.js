/**
 * Renderer - PixiJS wrapper for game rendering
 */

export class Renderer {
    constructor(canvas) {
        this.canvas = canvas;
        this.app = null;
        this.gameContainer = null;
        this.effectsContainer = null;
        this.particles = [];
        
        // Grid settings
        this.cellSize = 20;
        this.gridWidth = 40;
        this.gridHeight = 40;
    }
    
    /**
     * Initialize PixiJS
     */
    async init(width = 800, height = 600) {
        this.app = new PIXI.Application({
            view: this.canvas,
            width: width,
            height: height,
            backgroundColor: 0x0F172A,
            antialias: true,
            resolution: window.devicePixelRatio || 1,
            autoDensity: true
        });
        
        // Create main containers
        this.gameContainer = new PIXI.Container();
        this.effectsContainer = new PIXI.Container();
        
        this.app.stage.addChild(this.gameContainer);
        this.app.stage.addChild(this.effectsContainer);
        
        // Start update loop for particles
        this.app.ticker.add(() => this.updateParticles());
        
        return this;
    }
    
    /**
     * Resize the renderer
     */
    resize(width, height) {
        if (this.app) {
            this.app.renderer.resize(width, height);
            // Keep the canvas CSS size in sync so it isn't clipped by the DOM
            this.canvas.style.width = width + 'px';
            this.canvas.style.height = height + 'px';
        }
    }
    
    /**
     * Set grid dimensions
     */
    setGrid(gridWidth, gridHeight, cellSize) {
        this.gridWidth = gridWidth;
        this.gridHeight = gridHeight;
        this.cellSize = cellSize;
    }
    
    /**
     * Clear the game container
     */
    clear() {
        if (this.gameContainer) {
            this.gameContainer.removeChildren();
        }
    }
    
    /**
     * Draw a rectangle
     */
    drawRect(x, y, width, height, color, alpha = 1) {
        const graphics = new PIXI.Graphics();
        graphics.beginFill(color, alpha);
        graphics.drawRect(x, y, width, height);
        graphics.endFill();
        this.gameContainer.addChild(graphics);
        return graphics;
    }
    
    /**
     * Draw a rounded rectangle
     */
    drawRoundedRect(x, y, width, height, radius, color, alpha = 1) {
        const graphics = new PIXI.Graphics();
        graphics.beginFill(color, alpha);
        graphics.drawRoundedRect(x, y, width, height, radius);
        graphics.endFill();
        this.gameContainer.addChild(graphics);
        return graphics;
    }
    
    /**
     * Draw a circle
     */
    drawCircle(x, y, radius, color, alpha = 1) {
        const graphics = new PIXI.Graphics();
        graphics.beginFill(color, alpha);
        graphics.drawCircle(x, y, radius);
        graphics.endFill();
        this.gameContainer.addChild(graphics);
        return graphics;
    }
    
    /**
     * Draw a line
     */
    drawLine(x1, y1, x2, y2, color, width = 1, alpha = 1) {
        const graphics = new PIXI.Graphics();
        graphics.lineStyle(width, color, alpha);
        graphics.moveTo(x1, y1);
        graphics.lineTo(x2, y2);
        this.gameContainer.addChild(graphics);
        return graphics;
    }
    
    /**
     * Draw text
     */
    drawText(text, x, y, style = {}) {
        const defaultStyle = {
            fontFamily: 'Inter',
            fontSize: 14,
            fill: 0xFFFFFF,
            align: 'center'
        };
        
        const textStyle = new PIXI.TextStyle({ ...defaultStyle, ...style });
        const textObj = new PIXI.Text(text, textStyle);
        textObj.x = x;
        textObj.y = y;
        textObj.anchor.set(0.5);
        this.gameContainer.addChild(textObj);
        return textObj;
    }
    
    /**
     * Draw a grid cell (for snake games)
     */
    drawCell(gridX, gridY, color, offsetX = 0, offsetY = 0) {
        const x = offsetX + gridX * this.cellSize;
        const y = offsetY + gridY * this.cellSize;
        const padding = 1;
        
        return this.drawRoundedRect(
            x + padding,
            y + padding,
            this.cellSize - padding * 2,
            this.cellSize - padding * 2,
            4,
            color
        );
    }
    
    /**
     * Draw quadrant background
     */
    drawQuadrantBackground(bounds, playerColor, isAlive = true, offsetX = 0, offsetY = 0) {
        const x = offsetX + bounds.x_min * this.cellSize;
        const y = offsetY + bounds.y_min * this.cellSize;
        const width = (bounds.x_max - bounds.x_min) * this.cellSize;
        const height = (bounds.y_max - bounds.y_min) * this.cellSize;
        
        // Background
        const bgColor = isAlive ? 0x1E293B : 0x0F172A;
        this.drawRect(x, y, width, height, bgColor);
        
        // Border with player color
        const borderColor = parseInt(playerColor.replace('#', ''), 16);
        const graphics = new PIXI.Graphics();
        graphics.lineStyle(3, borderColor, isAlive ? 1 : 0.3);
        graphics.drawRect(x, y, width, height);
        this.gameContainer.addChild(graphics);
        
        // Grid lines
        const gridGraphics = new PIXI.Graphics();
        gridGraphics.lineStyle(1, 0x334155, 0.3);
        
        for (let gx = bounds.x_min; gx <= bounds.x_max; gx++) {
            gridGraphics.moveTo(offsetX + gx * this.cellSize, y);
            gridGraphics.lineTo(offsetX + gx * this.cellSize, y + height);
        }
        
        for (let gy = bounds.y_min; gy <= bounds.y_max; gy++) {
            gridGraphics.moveTo(x, offsetY + gy * this.cellSize);
            gridGraphics.lineTo(x + width, offsetY + gy * this.cellSize);
        }
        
        this.gameContainer.addChild(gridGraphics);
    }
    
    /**
     * Draw snake
     */
    drawSnake(snake, offsetX = 0, offsetY = 0) {
        if (!snake || !snake.body || snake.body.length === 0) return;
        
        const color = parseInt(snake.color.replace('#', ''), 16);
        const alpha = snake.alive ? 1 : 0.3;
        
        // Draw body segments
        snake.body.forEach((segment, index) => {
            const x = offsetX + segment.x * this.cellSize;
            const y = offsetY + segment.y * this.cellSize;
            const padding = 2;
            
            // Head is slightly different
            if (index === 0) {
                const headGraphics = new PIXI.Graphics();
                headGraphics.beginFill(color, alpha);
                headGraphics.drawRoundedRect(
                    x + padding,
                    y + padding,
                    this.cellSize - padding * 2,
                    this.cellSize - padding * 2,
                    6
                );
                headGraphics.endFill();
                
                // Eyes
                const eyeColor = 0xFFFFFF;
                const eyeSize = 3;
                const eyeOffset = 5;
                
                headGraphics.beginFill(eyeColor, alpha);
                if (snake.direction === 'right') {
                    headGraphics.drawCircle(x + this.cellSize - eyeOffset, y + eyeOffset, eyeSize);
                    headGraphics.drawCircle(x + this.cellSize - eyeOffset, y + this.cellSize - eyeOffset, eyeSize);
                } else if (snake.direction === 'left') {
                    headGraphics.drawCircle(x + eyeOffset, y + eyeOffset, eyeSize);
                    headGraphics.drawCircle(x + eyeOffset, y + this.cellSize - eyeOffset, eyeSize);
                } else if (snake.direction === 'up') {
                    headGraphics.drawCircle(x + eyeOffset, y + eyeOffset, eyeSize);
                    headGraphics.drawCircle(x + this.cellSize - eyeOffset, y + eyeOffset, eyeSize);
                } else {
                    headGraphics.drawCircle(x + eyeOffset, y + this.cellSize - eyeOffset, eyeSize);
                    headGraphics.drawCircle(x + this.cellSize - eyeOffset, y + this.cellSize - eyeOffset, eyeSize);
                }
                headGraphics.endFill();
                
                this.gameContainer.addChild(headGraphics);
            } else {
                // Body segment with gradient effect
                const brightness = 1 - (index / snake.body.length) * 0.3;
                const segmentColor = this.adjustBrightness(color, brightness);
                
                const segGraphics = new PIXI.Graphics();
                segGraphics.beginFill(segmentColor, alpha);
                segGraphics.drawRoundedRect(
                    x + padding,
                    y + padding,
                    this.cellSize - padding * 2,
                    this.cellSize - padding * 2,
                    4
                );
                segGraphics.endFill();
                this.gameContainer.addChild(segGraphics);
            }
        });
    }
    
    /**
     * Draw food
     */
    drawFood(food, offsetX = 0, offsetY = 0) {
        const x = offsetX + food.position.x * this.cellSize + this.cellSize / 2;
        const y = offsetY + food.position.y * this.cellSize + this.cellSize / 2;
        const color = parseInt(food.color.replace('#', ''), 16);
        
        const size = Math.min(food.size, 3) * 4 + 6;
        
        // Glow effect
        const glow = new PIXI.Graphics();
        glow.beginFill(color, 0.2);
        glow.drawCircle(x, y, size + 4);
        glow.endFill();
        this.gameContainer.addChild(glow);
        
        // Main food
        const foodGraphics = new PIXI.Graphics();
        foodGraphics.beginFill(color);
        foodGraphics.drawCircle(x, y, size);
        foodGraphics.endFill();
        this.gameContainer.addChild(foodGraphics);
        
        // Health indicator for multi-hit food
        if (food.health > 1) {
            const healthText = new PIXI.Text(food.health.toString(), {
                fontFamily: 'Inter',
                fontSize: 10,
                fill: 0xFFFFFF,
                fontWeight: 'bold'
            });
            healthText.anchor.set(0.5);
            healthText.x = x;
            healthText.y = y;
            this.gameContainer.addChild(healthText);
        }
    }
    
    /**
     * Add particle effect
     */
    addParticle(x, y, color, count = 10) {
        for (let i = 0; i < count; i++) {
            const particle = new PIXI.Graphics();
            const size = 2 + Math.random() * 4;
            particle.beginFill(color);
            particle.drawCircle(0, 0, size);
            particle.endFill();
            
            particle.x = x;
            particle.y = y;
            particle.vx = (Math.random() - 0.5) * 8;
            particle.vy = (Math.random() - 0.5) * 8;
            particle.life = 1;
            particle.decay = 0.02 + Math.random() * 0.02;
            
            this.effectsContainer.addChild(particle);
            this.particles.push(particle);
        }
    }
    
    /**
     * Update particles
     */
    updateParticles() {
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const p = this.particles[i];
            p.x += p.vx;
            p.y += p.vy;
            p.life -= p.decay;
            p.alpha = p.life;
            p.scale.set(p.life);
            
            if (p.life <= 0) {
                this.effectsContainer.removeChild(p);
                this.particles.splice(i, 1);
            }
        }
    }
    
    /**
     * Adjust color brightness
     */
    adjustBrightness(color, factor) {
        const r = Math.min(255, ((color >> 16) & 0xFF) * factor);
        const g = Math.min(255, ((color >> 8) & 0xFF) * factor);
        const b = Math.min(255, (color & 0xFF) * factor);
        return (r << 16) | (g << 8) | b;
    }
    
    /**
     * Get renderer dimensions
     */
    getDimensions() {
        return {
            width: this.app ? this.app.renderer.width : 0,
            height: this.app ? this.app.renderer.height : 0
        };
    }
    
    /**
     * Destroy the renderer
     */
    destroy() {
        if (this.app) {
            // Use destroy(false, {children: true}) to clean up WebGL context
            // but keep the canvas element in the DOM for reuse
            this.app.destroy(false, {children: true});
            this.app = null;
        }
        this.gameContainer = null;
        this.effectsContainer = null;
        this.particles = [];
    }
}

export default Renderer;
