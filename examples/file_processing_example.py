"""
File processing examples for ANC with Noise Profiling

This script demonstrates various ways to use the file-based noise reduction functionality.
"""

import os
from anc_noise_profiling import reduce_noise_file, NoiseReductionConfig

def basic_file_processing():
    """Basic file processing example."""
    print("=== Basic File Processing ===")
    
    # Example with first 0.5 seconds as noise profile
    input_file = "example_input.wav"  # Replace with your audio file
    output_file = "output_basic.wav"
    
    if os.path.exists(input_file):
        result = reduce_noise_file(
            input_file=input_file,
            output_file=output_file,
            noise_profile="first_0.5"
        )
        print(f"✓ Processed: {result}")
    else:
        print(f"⚠ Input file not found: {input_file}")
        print("  Please provide a valid audio file path")


def adaptive_noise_detection():
    """Example using adaptive noise profile detection."""
    print("\n=== Adaptive Noise Detection ===")
    
    input_file = "example_input.wav"  # Replace with your audio file
    output_file = "output_adaptive.wav"
    
    if os.path.exists(input_file):
        result = reduce_noise_file(
            input_file=input_file,
            output_file=output_file,
            noise_profile="adaptive",
            silence_threshold=0.02,  # Adjust based on your audio
            min_silence_duration=0.5,
            visualization=True  # Show waveform plot
        )
        print(f"✓ Processed with adaptive detection: {result}")
    else:
        print(f"⚠ Input file not found: {input_file}")


def custom_configuration():
    """Example using custom configuration object."""
    print("\n=== Custom Configuration ===")
    
    input_file = "example_input.wav"  # Replace with your audio file
    output_file = "output_custom.wav"
    
    # Create custom configuration
    config = NoiseReductionConfig(
        noise_profile="last_1.0",  # Use last 1 second
        silence_threshold=0.015,
        min_silence_duration=0.3,
        visualization=True,
        save_raw_audio=True  # Save original audio too
    )
    
    if os.path.exists(input_file):
        result = reduce_noise_file(
            input_file=input_file,
            output_file=output_file,
            config=config
        )
        print(f"✓ Processed with custom config: {result}")
        print(f"✓ Raw audio saved as: {output_file.replace('.wav', '_raw.wav')}")
    else:
        print(f"⚠ Input file not found: {input_file}")


def external_noise_file():
    """Example using external noise file."""
    print("\n=== External Noise File ===")
    
    input_file = "example_input.wav"  # Replace with your audio file
    noise_file = "noise_sample.wav"   # Replace with your noise file
    output_file = "output_external_noise.wav"
    
    if os.path.exists(input_file) and os.path.exists(noise_file):
        result = reduce_noise_file(
            input_file=input_file,
            output_file=output_file,
            noise_profile=noise_file
        )
        print(f"✓ Processed with external noise file: {result}")
    else:
        if not os.path.exists(input_file):
            print(f"⚠ Input file not found: {input_file}")
        if not os.path.exists(noise_file):
            print(f"⚠ Noise file not found: {noise_file}")


def batch_processing():
    """Example of batch processing multiple files."""
    print("\n=== Batch Processing ===")
    
    # List of input files (replace with your files)
    input_files = [
        "audio1.wav",
        "audio2.wav", 
        "audio3.wav"
    ]
    
    config = NoiseReductionConfig(
        noise_profile="adaptive",
        visualization=False,  # Disable for batch processing
        save_raw_audio=False
    )
    
    for i, input_file in enumerate(input_files):
        if os.path.exists(input_file):
            output_file = f"output_batch_{i+1}.wav"
            try:
                result = reduce_noise_file(
                    input_file=input_file,
                    output_file=output_file,
                    config=config
                )
                print(f"✓ Processed {i+1}/{len(input_files)}: {result}")
            except Exception as e:
                print(f"✗ Failed to process {input_file}: {e}")
        else:
            print(f"⚠ File not found: {input_file}")


if __name__ == "__main__":
    print("ANC with Noise Profiling - File Processing Examples")
    print("=" * 50)
    
    # Run examples
    basic_file_processing()
    adaptive_noise_detection()
    custom_configuration()
    external_noise_file()
    batch_processing()
    
    print("\n" + "=" * 50)
    print("Examples completed!")
    print("\nNote: Replace 'example_input.wav' with actual audio file paths")
    print("to see the noise reduction in action.")