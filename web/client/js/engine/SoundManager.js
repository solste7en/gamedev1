/**
 * SoundManager - Handles game audio using Web Audio API
 * Generates synthesized sound effects
 */

export class SoundManager {
    constructor() {
        this.audioContext = null;
        this.enabled = true;
        this.volume = 0.3;
        this.initialized = false;
    }
    
    /**
     * Initialize audio context (must be called after user interaction)
     */
    init() {
        if (this.initialized) return;
        
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.initialized = true;
            console.log('Audio initialized');
        } catch (e) {
            console.warn('Web Audio API not supported:', e);
            this.enabled = false;
        }
    }
    
    /**
     * Enable/disable sound
     */
    setEnabled(enabled) {
        this.enabled = enabled;
    }
    
    /**
     * Set master volume (0-1)
     */
    setVolume(volume) {
        this.volume = Math.max(0, Math.min(1, volume));
    }
    
    /**
     * Play a sound effect
     */
    play(soundName) {
        if (!this.enabled || !this.audioContext) return;
        
        // Resume context if suspended (browser autoplay policy)
        if (this.audioContext.state === 'suspended') {
            this.audioContext.resume();
        }
        
        switch (soundName) {
            case 'eat':
                this.playEatSound();
                break;
            case 'eat_large':
                this.playEatLargeSound();
                break;
            case 'death':
                this.playDeathSound();
                break;
            case 'countdown':
                this.playCountdownSound();
                break;
            case 'go':
                this.playGoSound();
                break;
            case 'win':
                this.playWinSound();
                break;
            case 'click':
                this.playClickSound();
                break;
            case 'join':
                this.playJoinSound();
                break;
            case 'ready':
                this.playReadySound();
                break;
            case 'combo':
                this.playComboSound();
                break;
            default:
                console.warn('Unknown sound:', soundName);
        }
    }
    
    /**
     * Create oscillator with envelope
     */
    createOscillator(type, frequency, duration, attack = 0.01, decay = 0.1) {
        const osc = this.audioContext.createOscillator();
        const gain = this.audioContext.createGain();
        
        osc.type = type;
        osc.frequency.setValueAtTime(frequency, this.audioContext.currentTime);
        
        gain.gain.setValueAtTime(0, this.audioContext.currentTime);
        gain.gain.linearRampToValueAtTime(this.volume, this.audioContext.currentTime + attack);
        gain.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + duration);
        
        osc.connect(gain);
        gain.connect(this.audioContext.destination);
        
        osc.start();
        osc.stop(this.audioContext.currentTime + duration);
        
        return { osc, gain };
    }
    
    /**
     * Play eat food sound - short blip
     */
    playEatSound() {
        this.createOscillator('sine', 880, 0.1);
    }
    
    /**
     * Play eat large food sound - deeper blip
     */
    playEatLargeSound() {
        this.createOscillator('sine', 440, 0.15);
        setTimeout(() => {
            this.createOscillator('sine', 660, 0.1);
        }, 50);
    }
    
    /**
     * Play death sound - descending tone
     */
    playDeathSound() {
        const osc = this.audioContext.createOscillator();
        const gain = this.audioContext.createGain();
        
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(400, this.audioContext.currentTime);
        osc.frequency.exponentialRampToValueAtTime(100, this.audioContext.currentTime + 0.5);
        
        gain.gain.setValueAtTime(this.volume * 0.5, this.audioContext.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.5);
        
        osc.connect(gain);
        gain.connect(this.audioContext.destination);
        
        osc.start();
        osc.stop(this.audioContext.currentTime + 0.5);
    }
    
    /**
     * Play countdown beep
     */
    playCountdownSound() {
        this.createOscillator('sine', 660, 0.15);
    }
    
    /**
     * Play "GO!" sound
     */
    playGoSound() {
        this.createOscillator('sine', 880, 0.1);
        setTimeout(() => {
            this.createOscillator('sine', 1100, 0.2);
        }, 100);
    }
    
    /**
     * Play win fanfare
     */
    playWinSound() {
        const notes = [523, 659, 784, 1047]; // C5, E5, G5, C6
        notes.forEach((freq, i) => {
            setTimeout(() => {
                this.createOscillator('sine', freq, 0.3);
            }, i * 150);
        });
    }
    
    /**
     * Play UI click sound
     */
    playClickSound() {
        this.createOscillator('sine', 1000, 0.05);
    }
    
    /**
     * Play player join sound
     */
    playJoinSound() {
        this.createOscillator('sine', 440, 0.1);
        setTimeout(() => {
            this.createOscillator('sine', 550, 0.1);
        }, 100);
    }
    
    /**
     * Play ready sound
     */
    playReadySound() {
        this.createOscillator('sine', 660, 0.1);
        setTimeout(() => {
            this.createOscillator('sine', 880, 0.15);
        }, 80);
    }
    
    /**
     * Play combo sound (pitch based on combo level)
     */
    playComboSound(comboLevel = 1) {
        const baseFreq = 440 + (comboLevel * 100);
        this.createOscillator('sine', baseFreq, 0.1);
    }
    
    /**
     * Play background music (simple loop)
     */
    playBackgroundMusic() {
        // Background music would require longer samples
        // For now, we just have sound effects
    }
    
    /**
     * Stop all sounds
     */
    stopAll() {
        if (this.audioContext) {
            this.audioContext.close();
            this.audioContext = null;
            this.initialized = false;
        }
    }
}

export default SoundManager;
