import wave
import struct
import math
import os

def generate_sine_wave(frequency, duration, sample_rate=44100, amplitude=0.5):
    """Generate a sine wave at the specified frequency and duration."""
    n_samples = int(sample_rate * duration)
    samples = []
    
    for i in range(n_samples):
        sample = amplitude * math.sin(2 * math.pi * frequency * i / sample_rate)
        samples.append(int(sample * 32767))  # Convert to 16-bit PCM
    
    return samples

def save_wave_file(filename, samples, sample_rate=44100):
    """Save samples to a WAV file."""
    with wave.open(filename, 'w') as wav_file:
        # Set parameters
        n_channels = 1  # Mono
        sample_width = 2  # 2 bytes (16 bits) per sample
        
        wav_file.setparams((n_channels, sample_width, sample_rate, len(samples), 'NONE', 'not compressed'))
        
        # Convert samples to binary data
        sample_data = struct.pack('<' + ('h' * len(samples)), *samples)
        wav_file.writeframes(sample_data)

def generate_start_sound():
    """Generate a sound for when translation starts."""
    # Create a simple ascending tone
    samples = generate_sine_wave(440, 0.1)  # A4 note
    samples += generate_sine_wave(523.25, 0.1)  # C5 note
    samples += generate_sine_wave(659.25, 0.1)  # E5 note
    
    # Ensure the sounds directory exists
    os.makedirs("sounds", exist_ok=True)
    
    # Save the sound
    save_wave_file("sounds/start.wav", samples)
    print("Generated start sound: sounds/start.wav")

def generate_complete_sound():
    """Generate a sound for when translation is complete."""
    # Create a simple descending tone
    samples = generate_sine_wave(659.25, 0.1)  # E5 note
    samples += generate_sine_wave(523.25, 0.1)  # C5 note
    samples += generate_sine_wave(440, 0.1)  # A4 note
    
    # Add a final "ding"
    samples += generate_sine_wave(880, 0.3)  # A5 note
    
    # Ensure the sounds directory exists
    os.makedirs("sounds", exist_ok=True)
    
    # Save the sound
    save_wave_file("sounds/complete.wav", samples)
    print("Generated complete sound: sounds/complete.wav")

if __name__ == "__main__":
    print("Generating notification sounds...")
    generate_start_sound()
    generate_complete_sound()
    print("Done!") 