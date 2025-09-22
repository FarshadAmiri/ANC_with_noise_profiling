"""
File-based noise reduction example using the new anc_noise_profiling package

This script replaces the original Jupyter notebook with a clean Python script
that demonstrates the same functionality using the professional package structure.
"""

import os
from anc_noise_profiling import reduce_noise_file, NoiseReductionConfig

def main():
    """Demonstrate file-based noise reduction."""
    
    print("ANC with Noise Profiling - File Processing Demo")
    print("=" * 50)
    
    # Example file paths (replace with your actual files)
    input_file = "example_input.wav"  # Replace with your noisy audio file
    
    print(f"Looking for input file: {input_file}")
    
    if not os.path.exists(input_file):
        print("⚠ Input file not found. Creating a demo with any available .wav files...")
        
        # Look for any .wav files in current directory
        wav_files = [f for f in os.listdir('.') if f.endswith('.wav')]
        
        if wav_files:
            input_file = wav_files[0]
            print(f"✓ Using found file: {input_file}")
        else:
            print("✗ No .wav files found in current directory.")
            print("\nTo test the functionality:")
            print("1. Add an audio file (e.g., 'example_input.wav') to this directory")
            print("2. Or modify the input_file variable in this script")
            print("3. Then run this script again")
            return
    
    # Example 1: Basic noise reduction using first 0.5 seconds
    print("\n1. Basic noise reduction (first 0.5s as noise profile):")
    output_file1 = "output_basic.wav"
    
    try:
        result = reduce_noise_file(
            input_file=input_file,
            output_file=output_file1,
            noise_profile="first_0.5"
        )
        print(f"✓ Success: {result}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Example 2: Adaptive noise detection with visualization
    print("\n2. Adaptive noise detection with visualization:")
    output_file2 = "output_adaptive.wav"
    
    try:
        result = reduce_noise_file(
            input_file=input_file,
            output_file=output_file2,
            noise_profile="adaptive",
            silence_threshold=0.01,
            min_silence_duration=0.3,
            visualization=True  # This will show a plot if matplotlib is available
        )
        print(f"✓ Success: {result}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Example 3: Custom configuration
    print("\n3. Custom configuration with last 1.0 seconds:")
    output_file3 = "output_custom.wav"
    
    config = NoiseReductionConfig(
        noise_profile="last_1.0",
        silence_threshold=0.02,
        min_silence_duration=0.5,
        visualization=False,
        save_raw_audio=True  # Save original audio too
    )
    
    try:
        result = reduce_noise_file(
            input_file=input_file,
            output_file=output_file3,
            config=config
        )
        print(f"✓ Success: {result}")
        print(f"✓ Raw audio saved: {output_file3.replace('.wav', '_raw.wav')}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "=" * 50)
    print("Demo completed!")
    print("\nNext steps:")
    print("- Check the output files generated")
    print("- Try the CLI: anc-noise-profiling file input.wav output.wav")
    print("- See examples/ directory for more usage examples")
    print("- Read README.md for complete documentation")


if __name__ == "__main__":
    main()