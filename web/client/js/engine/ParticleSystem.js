/**
 * ParticleSystem - Enhanced particle effects for the game
 */

export class ParticleSystem {
    constructor(container) {
        this.container = container;
        this.particles = [];
        this.emitters = [];
    }
    
    /**
     * Create a burst of particles
     */
    burst(x, y, options = {}) {
        const {
            count = 10,
            color = 0xFFFFFF,
            colors = null,  // Array of colors for variety
            minSpeed = 2,
            maxSpeed = 6,
            minSize = 2,
            maxSize = 6,
            minLife = 0.5,
            maxLife = 1.0,
            gravity = 0,
            spread = Math.PI * 2,  // Full circle
            direction = 0,  // Center direction
            fadeOut = true,
            shrink = true
        } = options;
        
        for (let i = 0; i < count; i++) {
            const particle = new PIXI.Graphics();
            
            // Random size
            const size = minSize + Math.random() * (maxSize - minSize);
            
            // Random color from array or single color
            let particleColor = color;
            if (colors && colors.length > 0) {
                particleColor = colors[Math.floor(Math.random() * colors.length)];
            }
            
            particle.beginFill(particleColor);
            particle.drawCircle(0, 0, size);
            particle.endFill();
            
            particle.x = x;
            particle.y = y;
            
            // Random velocity within spread angle
            const angle = direction + (Math.random() - 0.5) * spread;
            const speed = minSpeed + Math.random() * (maxSpeed - minSpeed);
            particle.vx = Math.cos(angle) * speed;
            particle.vy = Math.sin(angle) * speed;
            
            // Particle properties
            particle.life = minLife + Math.random() * (maxLife - minLife);
            particle.maxLife = particle.life;
            particle.gravity = gravity;
            particle.fadeOut = fadeOut;
            particle.shrink = shrink;
            particle.initialScale = 1;
            
            this.container.addChild(particle);
            this.particles.push(particle);
        }
    }
    
    /**
     * Create eat effect (food collected)
     */
    eatEffect(x, y, foodColor = 0x22C55E, size = 1) {
        const count = 8 + size * 4;
        this.burst(x, y, {
            count: count,
            color: foodColor,
            minSpeed: 1,
            maxSpeed: 4,
            minSize: 2,
            maxSize: 4 + size,
            minLife: 0.3,
            maxLife: 0.6,
            gravity: 0.1
        });
        
        // Add sparkle effect
        this.burst(x, y, {
            count: 5,
            color: 0xFFFFFF,
            minSpeed: 2,
            maxSpeed: 5,
            minSize: 1,
            maxSize: 2,
            minLife: 0.2,
            maxLife: 0.4
        });
    }
    
    /**
     * Create death effect
     */
    deathEffect(x, y, snakeColor = 0x22C55E) {
        // Big explosion
        this.burst(x, y, {
            count: 30,
            colors: [snakeColor, 0xFF0000, 0xFF6B6B],
            minSpeed: 3,
            maxSpeed: 8,
            minSize: 3,
            maxSize: 8,
            minLife: 0.5,
            maxLife: 1.0,
            gravity: 0.2
        });
        
        // Smoke
        this.burst(x, y, {
            count: 15,
            color: 0x666666,
            minSpeed: 1,
            maxSpeed: 3,
            minSize: 5,
            maxSize: 12,
            minLife: 0.8,
            maxLife: 1.5,
            gravity: -0.1
        });
    }
    
    /**
     * Create combo effect
     */
    comboEffect(x, y, comboLevel) {
        const colors = [0xF1C40F, 0xE67E22, 0xE74C3C, 0x9B59B6, 0x3498DB];
        const colorIndex = Math.min(comboLevel - 1, colors.length - 1);
        
        this.burst(x, y, {
            count: 5 + comboLevel * 2,
            color: colors[colorIndex],
            minSpeed: 2,
            maxSpeed: 4,
            minSize: 2,
            maxSize: 4,
            minLife: 0.3,
            maxLife: 0.5,
            spread: Math.PI,
            direction: -Math.PI / 2  // Upward
        });
    }
    
    /**
     * Create win celebration effect
     */
    winEffect(x, y) {
        const colors = [0xF1C40F, 0xE74C3C, 0x3498DB, 0x2ECC71, 0x9B59B6];
        
        // Multiple bursts
        for (let i = 0; i < 3; i++) {
            setTimeout(() => {
                this.burst(x + (Math.random() - 0.5) * 100, y + (Math.random() - 0.5) * 50, {
                    count: 20,
                    colors: colors,
                    minSpeed: 4,
                    maxSpeed: 10,
                    minSize: 3,
                    maxSize: 7,
                    minLife: 0.8,
                    maxLife: 1.5,
                    gravity: 0.3
                });
            }, i * 200);
        }
    }
    
    /**
     * Create shrink warning effect (survival mode)
     */
    shrinkWarningEffect(bounds, cellSize, offsetX, offsetY) {
        const x1 = offsetX + bounds.x_min * cellSize;
        const y1 = offsetY + bounds.y_min * cellSize;
        const x2 = offsetX + bounds.x_max * cellSize;
        const y2 = offsetY + bounds.y_max * cellSize;
        
        // Particles along the edges
        for (let i = 0; i < 20; i++) {
            let px, py;
            const edge = Math.floor(Math.random() * 4);
            
            switch (edge) {
                case 0: // Top
                    px = x1 + Math.random() * (x2 - x1);
                    py = y1;
                    break;
                case 1: // Bottom
                    px = x1 + Math.random() * (x2 - x1);
                    py = y2;
                    break;
                case 2: // Left
                    px = x1;
                    py = y1 + Math.random() * (y2 - y1);
                    break;
                case 3: // Right
                    px = x2;
                    py = y1 + Math.random() * (y2 - y1);
                    break;
            }
            
            this.burst(px, py, {
                count: 2,
                color: 0xEF4444,
                minSpeed: 1,
                maxSpeed: 3,
                minSize: 2,
                maxSize: 4,
                minLife: 0.5,
                maxLife: 0.8
            });
        }
    }
    
    /**
     * Update all particles
     */
    update(deltaTime = 1/60) {
        for (let i = this.particles.length - 1; i >= 0; i--) {
            const p = this.particles[i];
            
            // Update position
            p.x += p.vx;
            p.y += p.vy;
            
            // Apply gravity
            p.vy += p.gravity;
            
            // Update life
            p.life -= deltaTime;
            
            // Apply effects based on life
            const lifeRatio = p.life / p.maxLife;
            
            if (p.fadeOut) {
                p.alpha = lifeRatio;
            }
            
            if (p.shrink) {
                p.scale.set(lifeRatio * p.initialScale);
            }
            
            // Remove dead particles
            if (p.life <= 0) {
                this.container.removeChild(p);
                this.particles.splice(i, 1);
            }
        }
    }
    
    /**
     * Clear all particles
     */
    clear() {
        for (const p of this.particles) {
            this.container.removeChild(p);
        }
        this.particles = [];
    }
}

export default ParticleSystem;
