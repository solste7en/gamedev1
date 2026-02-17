"""
Sound effects module for the Snake Game.
Generates and manages all game sound effects programmatically.
"""

import pygame
import numpy as np
import io


class SoundManager:
    """
    Manages all sound effects for the game.
    Generates sounds programmatically using numpy waveforms.
    """
    
    def __init__(self, enabled=True):
        """
        Initialize the sound manager.
        
        Args:
            enabled: Whether sound is enabled
        """
        self.enabled = enabled
        self.sounds = {}
        
        if self.enabled:
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                self._generate_sounds()
            except pygame.error:
                print("Warning: Could not initialize sound mixer")
                self.enabled = False
    
    def _generate_sounds(self):
        """Generate all game sound effects."""
        self.sounds['eat'] = self._create_eat_sound()
        self.sounds['game_over'] = self._create_game_over_sound()
        self.sounds['move'] = self._create_move_sound()
        self.sounds['start'] = self._create_start_sound()
        self.sounds['bonus'] = self._create_bonus_sound()
    
    def _create_sound_from_array(self, samples, sample_rate=44100):
        """
        Convert a numpy array to a pygame Sound object.
        
        Args:
            samples: Numpy array of audio samples
            sample_rate: Sample rate in Hz
            
        Returns:
            pygame.mixer.Sound object
        """
        # Ensure samples are in the correct format
        samples = np.clip(samples, -1, 1)
        samples = (samples * 32767).astype(np.int16)
        
        # Make stereo
        stereo_samples = np.column_stack((samples, samples))
        
        # Create sound from array
        sound = pygame.sndarray.make_sound(stereo_samples)
        return sound
    
    def _create_eat_sound(self):
        """Create a satisfying 'chomp' sound for eating food."""
        sample_rate = 44100
        duration = 0.15  # seconds
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Start frequency and end frequency for a descending chirp
        freq_start = 800
        freq_end = 400
        
        # Create frequency sweep
        freq = np.linspace(freq_start, freq_end, len(t))
        
        # Generate the sweep
        phase = 2 * np.pi * np.cumsum(freq) / sample_rate
        wave = np.sin(phase)
        
        # Add harmonics for richness
        wave += 0.3 * np.sin(phase * 2)
        wave += 0.1 * np.sin(phase * 3)
        
        # Apply envelope (quick attack, medium decay)
        envelope = np.exp(-t * 20)
        wave = wave * envelope
        
        # Normalize
        wave = wave / np.max(np.abs(wave)) * 0.7
        
        return self._create_sound_from_array(wave, sample_rate)
    
    def _create_game_over_sound(self):
        """Create a dramatic game over sound."""
        sample_rate = 44100
        duration = 0.8  # seconds
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Descending tone
        freq_start = 400
        freq_end = 100
        freq = np.linspace(freq_start, freq_end, len(t))
        
        phase = 2 * np.pi * np.cumsum(freq) / sample_rate
        wave = np.sin(phase)
        
        # Add dissonant harmonics
        wave += 0.5 * np.sin(phase * 1.5)  # Tritone interval
        wave += 0.3 * np.sin(phase * 0.5)  # Sub-bass
        
        # Add some noise for harshness
        noise = np.random.random(len(t)) * 0.1
        wave = wave + noise
        
        # Envelope with slower decay
        envelope = np.exp(-t * 3)
        wave = wave * envelope
        
        # Normalize
        wave = wave / np.max(np.abs(wave)) * 0.8
        
        return self._create_sound_from_array(wave, sample_rate)
    
    def _create_move_sound(self):
        """Create a subtle slithering/movement sound."""
        sample_rate = 44100
        duration = 0.05  # Very short
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Soft click/tick
        freq = 150
        wave = np.sin(2 * np.pi * freq * t)
        
        # Add some noise for texture
        noise = np.random.random(len(t)) * 0.3
        wave = wave * 0.7 + noise * 0.3
        
        # Very quick envelope
        envelope = np.exp(-t * 100)
        wave = wave * envelope
        
        # Keep it quiet
        wave = wave / np.max(np.abs(wave)) * 0.15
        
        return self._create_sound_from_array(wave, sample_rate)
    
    def _create_start_sound(self):
        """Create an ascending 'ready' sound for game start."""
        sample_rate = 44100
        duration = 0.3
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Three-note ascending arpeggio
        segments = len(t) // 3
        
        wave = np.zeros(len(t))
        
        # Note 1 (C)
        freq1 = 262
        wave[:segments] = np.sin(2 * np.pi * freq1 * t[:segments])
        
        # Note 2 (E)
        freq2 = 330
        wave[segments:2*segments] = np.sin(2 * np.pi * freq2 * t[:segments])
        
        # Note 3 (G)
        freq3 = 392
        wave[2*segments:] = np.sin(2 * np.pi * freq3 * t[:len(t) - 2*segments])
        
        # Add harmonics
        wave2 = np.zeros(len(t))
        wave2[:segments] = np.sin(2 * np.pi * freq1 * 2 * t[:segments]) * 0.3
        wave2[segments:2*segments] = np.sin(2 * np.pi * freq2 * 2 * t[:segments]) * 0.3
        wave2[2*segments:] = np.sin(2 * np.pi * freq3 * 2 * t[:len(t) - 2*segments]) * 0.3
        
        wave = wave + wave2
        
        # Envelope
        envelope = np.ones(len(t))
        for i in range(3):
            start = i * segments
            end = min((i + 1) * segments, len(t))
            seg_t = np.linspace(0, 0.1, end - start)
            envelope[start:end] = np.exp(-seg_t * 15)
        
        wave = wave * envelope
        wave = wave / np.max(np.abs(wave)) * 0.6
        
        return self._create_sound_from_array(wave, sample_rate)
    
    def _create_bonus_sound(self):
        """Create a special sound for high-value prey."""
        sample_rate = 44100
        duration = 0.25
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        
        # Shimmering effect with multiple frequencies
        freq1 = 600
        freq2 = 900
        freq3 = 1200
        
        wave = np.sin(2 * np.pi * freq1 * t)
        wave += 0.6 * np.sin(2 * np.pi * freq2 * t)
        wave += 0.4 * np.sin(2 * np.pi * freq3 * t)
        
        # Vibrato effect
        vibrato = np.sin(2 * np.pi * 20 * t) * 0.1
        wave = wave * (1 + vibrato)
        
        # Envelope
        envelope = np.exp(-t * 8)
        wave = wave * envelope
        
        wave = wave / np.max(np.abs(wave)) * 0.6
        
        return self._create_sound_from_array(wave, sample_rate)
    
    def play(self, sound_name):
        """
        Play a sound effect by name.
        
        Args:
            sound_name: Name of the sound to play ('eat', 'game_over', 'move', 'start', 'bonus')
        """
        if not self.enabled:
            return
            
        if sound_name in self.sounds:
            self.sounds[sound_name].play()
    
    def play_eat_sound(self, animal_type):
        """
        Play the appropriate eating sound based on animal type.
        High-value prey (butterfly, frog) get the bonus sound.
        """
        high_value = ['butterfly', 'frog', 'mouse']
        
        if animal_type in high_value:
            self.play('bonus')
        else:
            self.play('eat')
    
    def set_enabled(self, enabled):
        """Enable or disable sound effects."""
        self.enabled = enabled
    
    def toggle(self):
        """Toggle sound on/off."""
        self.enabled = not self.enabled
        return self.enabled
    
    def cleanup(self):
        """Clean up sound resources."""
        if pygame.mixer.get_init():
            pygame.mixer.quit()
