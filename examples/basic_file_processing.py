"""
Basic file processing example using ANC Noise Profiling package.

This example demonstrates how to process an audio file with different noise profiling methods.
"""

from pathlib import Path
from anc_noise_profiling import NoiseReductionProcessor
from anc_noise_profiling.utils import setup_logging


def main():
    """Basic file processing example."""
    # Setup logging
    setup_logging(level="INFO")
    
    # Initialize processor
    processor = NoiseReductionProcessor(sample_rate=16000)
    
    # Example file paths (replace with your own)
    input_file = Path("example_audio/noisy_input.wav")
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Check if input file exists
    if not input_file.exists():
        print(f"Input file not found: {input_file}")
        print("Please provide a valid input audio file.")
        return
    
    # Process with different methods
    methods = [
        ("first_0.5", "Uses first 0.5 seconds as noise profile"),
        ("last_1.0", "Uses last 1.0 seconds as noise profile"),
        ("adaptive", "Automatically finds quietest segment")
    ]
    
    for method, description in methods:
        print(f"\n{'='*60}")
        print(f"Processing with method: {method}")
        print(f"Description: {description}")
        print(f"{'='*60}")
        
        output_file = output_dir / f"clean_{method}_{input_file.name}"
        
        try:
            result = processor.process_file(
                input_file=input_file,
                output_file=output_file,
                noise_profile_method=method,
                save_raw_audio=True  # Save original for comparison
            )
            
            print(f"✓ Success! Output saved to: {output_file}")
            print(f"  Processing time: {result['input_duration']:.2f}s")
            print(f"  Chunks processed: {result['chunks_processed']}")
            print(f"  Noise profile: {result['noise_profile']['duration']:.3f}s")
            
        except Exception as e:
            print(f"✗ Error: {e}")


if __name__ == "__main__":
    main()