/**
 * InputManager - Handles keyboard input for the game
 */

export class InputManager {
    constructor() {
        this.keyStates = new Map();
        this.keyCallbacks = new Map();
        this.enabled = true;
        
        // Bind event handlers
        this.handleKeyDown = this.handleKeyDown.bind(this);
        this.handleKeyUp = this.handleKeyUp.bind(this);
    }
    
    /**
     * Start listening for input
     */
    start() {
        window.addEventListener('keydown', this.handleKeyDown);
        window.addEventListener('keyup', this.handleKeyUp);
    }
    
    /**
     * Stop listening for input
     */
    stop() {
        window.removeEventListener('keydown', this.handleKeyDown);
        window.removeEventListener('keyup', this.handleKeyUp);
    }
    
    /**
     * Enable/disable input handling
     */
    setEnabled(enabled) {
        this.enabled = enabled;
    }
    
    /**
     * Handle keydown event
     */
    handleKeyDown(event) {
        if (!this.enabled) return;
        
        // Ignore if typing in input field
        if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
            return;
        }
        
        const key = event.key.toLowerCase();
        
        // Check if already pressed (prevent key repeat)
        if (this.keyStates.get(key)) return;
        
        this.keyStates.set(key, true);
        
        // Call registered callback
        const callback = this.keyCallbacks.get(key);
        if (callback) {
            callback('down', event);
            event.preventDefault();
        }
        
        // Also check for 'any' callbacks
        const anyCallback = this.keyCallbacks.get('*');
        if (anyCallback) {
            anyCallback('down', key, event);
        }
    }
    
    /**
     * Handle keyup event
     */
    handleKeyUp(event) {
        const key = event.key.toLowerCase();
        this.keyStates.set(key, false);
        
        const callback = this.keyCallbacks.get(key);
        if (callback && this.enabled) {
            callback('up', event);
        }
    }
    
    /**
     * Register a key callback
     */
    on(key, callback) {
        this.keyCallbacks.set(key.toLowerCase(), callback);
    }
    
    /**
     * Remove a key callback
     */
    off(key) {
        this.keyCallbacks.delete(key.toLowerCase());
    }
    
    /**
     * Check if a key is currently pressed
     */
    isPressed(key) {
        return this.keyStates.get(key.toLowerCase()) || false;
    }
    
    /**
     * Set up game controls for snake
     */
    setupSnakeControls(onDirection) {
        // Arrow keys
        this.on('arrowup', () => onDirection('up'));
        this.on('arrowdown', () => onDirection('down'));
        this.on('arrowleft', () => onDirection('left'));
        this.on('arrowright', () => onDirection('right'));
        
        // WASD keys
        this.on('w', () => onDirection('up'));
        this.on('s', () => onDirection('down'));
        this.on('a', () => onDirection('left'));
        this.on('d', () => onDirection('right'));
    }
    
    /**
     * Clear all controls
     */
    clearControls() {
        this.keyCallbacks.clear();
    }
}

export default InputManager;
