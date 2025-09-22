"""
Custom noise profile example using ANC Noise Profiling package.

This example demonstrates how to create and use custom noise profiles.
"""

import numpy as np
from pathlib import Path
from anc_noise_profiling.profiling import NoiseProfileExtractor
from anc_noise_profiling.io import AudioHandler
from anc_noise_profiling.utils import setup_logging


def create_synthetic_audio():
    """Create synthetic audio for demonstration."""
    setup_logging(level="INFO")
    
    sample_rate = 16000
    duration = 5.0  # 5 seconds
    t = np.linspace(0, duration, int(duration * sample_rate))
    
    # Create audio with different sections:
    # 0-1s: pure noise (good for profile)
    # 1-3s: speech simulation
    # 3-4s: mixed noise + weak signal
    # 4-5s: pure noise again
    
    audio = np.zeros_like(t)
    
    # Section 1: Pure noise (0-1s)
    noise_section = slice(0, sample_rate)
    audio[noise_section] = 0.02 * np.random.randn(sample_rate)
    
    # Section 2: Speech simulation (1-3s)
    speech_section = slice(sample_rate, 3 * sample_rate)
    speech_duration = len(audio[speech_section])
    speech_t = t[speech_section] - 1.0
    
    # Simulate speech with multiple frequency components
    speech = (0.3 * np.sin(2 * np.pi * 200 * speech_t) +
              0.2 * np.sin(2 * np.pi * 400 * speech_t) +
              0.15 * np.sin(2 * np.pi * 800 * speech_t))
    
    # Add envelope to simulate speech patterns
    envelope = np.abs(np.sin(2 * np.pi * 2 * speech_t)) ** 0.5
    speech *= envelope
    
    # Add noise to speech
    audio[speech_section] = speech + 0.02 * np.random.randn(speech_duration)
    
    # Section 3: Mixed weak signal + noise (3-4s)
    mixed_section = slice(3 * sample_rate, 4 * sample_rate)
    mixed_duration = len(audio[mixed_section])
    mixed_t = t[mixed_section] - 3.0
    
    weak_signal = 0.1 * np.sin(2 * np.pi * 300 * mixed_t)
    audio[mixed_section] = weak_signal + 0.03 * np.random.randn(mixed_duration)
    
    # Section 4: Pure noise again (4-5s)
    final_noise_section = slice(4 * sample_rate, 5 * sample_rate)
    audio[final_noise_section] = 0.025 * np.random.randn(sample_rate)
    
    return audio, sample_rate


def main():
    """Custom noise profile extraction example."""
    setup_logging(level="INFO")
    
    # Create synthetic audio
    print("Creating synthetic audio for demonstration...")
    audio_data, sample_rate = create_synthetic_audio()
    
    # Save synthetic audio
    handler = AudioHandler(sample_rate)
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    synthetic_file = output_dir / "synthetic_noisy_audio.wav"
    handler.save_audio_file(audio_data, synthetic_file, sample_rate)
    print(f"✓ Synthetic audio saved to: {synthetic_file}")
    
    # Initialize noise profile extractor
    extractor = NoiseProfileExtractor(sample_rate)
    
    # Test different extraction methods
    methods_to_test = [
        ("first_1.0", "Uses first 1 second (pure noise)"),
        ("last_1.0", "Uses last 1 second (pure noise)"),
        ("first_0.5", "Uses first 0.5 seconds (pure noise)"),
        ("adaptive", "Finds quietest segments automatically")
    ]
    
    print(f"\n{'='*60}")
    print("Testing different noise profile extraction methods:")
    print(f"{'='*60}")
    
    extracted_profiles = {}
    
    for method, description in methods_to_test:
        print(f"\nMethod: {method}")
        print(f"Description: {description}")
        print("-" * 40)
        
        try:
            # Extract noise profile
            noise_profile, metadata = extractor.extract_profile(
                audio_data,
                method=method,
                silence_threshold=0.01,
                min_silence_duration=0.2
            )
            
            extracted_profiles[method] = noise_profile
            
            # Print metadata
            print(f"✓ Extracted {len(noise_profile)} samples")
            print(f"  Duration: {metadata['duration']:.3f}s")
            print(f"  RMS Energy: {np.sqrt(np.mean(noise_profile**2)):.6f}")
            
            if 'start_sample' in metadata:
                start_time = metadata['start_sample'] / sample_rate
                end_time = metadata['end_sample'] / sample_rate
                print(f"  Time Range: {start_time:.3f}s - {end_time:.3f}s")
            
            # Save noise profile
            profile_file = output_dir / f"noise_profile_{method.replace('.', '_')}.wav"
            handler.save_audio_file(noise_profile, profile_file, sample_rate)
            print(f"  Saved to: {profile_file}")
            
        except Exception as e:
            print(f"✗ Error: {e}")
    
    # Compare profile qualities
    print(f"\n{'='*60}")
    print("Noise Profile Quality Comparison:")
    print(f"{'='*60}")
    
    for method, profile in extracted_profiles.items():
        rms_energy = np.sqrt(np.mean(profile**2))
        std_dev = np.std(profile)
        
        # Simple quality metric (lower energy = better for noise profile)
        quality_score = 1.0 / (rms_energy + 1e-6)
        
        print(f"{method:15s}: RMS={rms_energy:.6f}, STD={std_dev:.6f}, "
              f"Quality={quality_score:.2f}")
    
    # Demonstrate using external noise profile file
    print(f"\n{'='*60}")
    print("Using external noise profile file:")
    print(f"{'='*60}")
    
    # Use the best profile as external file
    best_profile_file = output_dir / "noise_profile_first_1_0.wav"
    
    if best_profile_file.exists():
        try:
            external_profile, metadata = extractor.extract_profile(
                audio_data,  # Not used when loading from file
                method=str(best_profile_file)
            )
            
            print(f"✓ Loaded external profile from: {best_profile_file}")
            print(f"  Duration: {metadata['duration']:.3f}s")
            print(f"  Sample Rate: {metadata['sample_rate']} Hz")
            
        except Exception as e:
            print(f"✗ Error loading external profile: {e}")
    
    print(f"\n✓ Custom noise profile demonstration completed!")
    print(f"  Check the output directory for saved files: {output_dir}")


if __name__ == "__main__":
    main()