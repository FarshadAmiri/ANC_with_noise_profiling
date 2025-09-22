"""
Advanced configuration example using ANC Noise Profiling package.

This example demonstrates advanced configuration options and custom processing.
"""

import logging
from pathlib import Path
from anc_noise_profiling import NoiseReductionProcessor
from anc_noise_profiling.utils import Config, setup_logging


def main():
    """Advanced configuration example."""
    
    # 1. Load configuration from file
    config_file = Path("examples/config_example.yaml")
    
    if config_file.exists():
        config = Config(config_file)
        print("✓ Loaded configuration from file")
    else:
        print("Creating default configuration...")
        config = Config()
        config.save_config_file(config_file, format="yaml")
        print(f"✓ Default configuration saved to: {config_file}")
    
    # 2. Setup logging based on config
    log_config = config.get_logging_config()
    setup_logging(
        level=log_config.get("level", "INFO"),
        include_timestamp=log_config.get("include_timestamp", True)
    )
    
    # 3. Initialize processor with configuration
    audio_config = config.get_audio_config()
    processor = NoiseReductionProcessor(
        sample_rate=audio_config.get("sample_rate", 16000),
        chunk_duration=audio_config.get("chunk_duration", 0.5)
    )
    
    # 4. Get processing parameters from config
    noise_config = config.get_noise_profiling_config()
    processing_config = config.get_processing_config()
    
    print(f"\nConfiguration Summary:")
    print(f"  Sample Rate: {audio_config.get('sample_rate')} Hz")
    print(f"  Chunk Duration: {audio_config.get('chunk_duration')}s")
    print(f"  Noise Method: {noise_config.get('method')}")
    print(f"  Output Mode: {processing_config.get('output_mode')}")
    
    # 5. Custom configuration modifications
    print(f"\nCustomizing configuration...")
    
    # Modify settings for high-quality processing
    config.set("audio.sample_rate", 44100)
    config.set("audio.chunk_duration", 0.25)  # Lower latency
    config.set("noise_profiling.method", "adaptive")
    config.set("noise_profiling.silence_threshold", 0.005)  # More sensitive
    
    # Save modified configuration
    modified_config_file = Path("output/config_modified.yaml")
    modified_config_file.parent.mkdir(exist_ok=True)
    config.save_config_file(modified_config_file)
    
    print(f"✓ Modified configuration saved to: {modified_config_file}")
    
    # 6. Demonstrate different output directories
    output_config = config.get_output_config()
    output_dir = Path(output_config.get("directory", "output"))
    
    # Create organized output structure
    subdirs = ["file_processing", "real_time", "batch_results"]
    for subdir in subdirs:
        (output_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    print(f"✓ Created output directory structure in: {output_dir}")
    
    # 7. Show configuration sections
    print(f"\nComplete Configuration:")
    print(config)


if __name__ == "__main__":
    main()