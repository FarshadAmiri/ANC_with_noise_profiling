"""Command-line interface for ANC noise profiling."""

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

from ..core.processor import NoiseReductionProcessor
from ..utils.config import Config
from ..utils.logging_config import setup_logging
from ..io.audio_handler import AudioHandler


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Active Noise Cancellation with Noise Profiling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a file with default settings
  anc-noise-profiling process-file input.wav output.wav
  
  # Use adaptive noise profiling
  anc-noise-profiling process-file input.wav output.wav --profile-method adaptive
  
  # Record from microphone for 30 seconds
  anc-noise-profiling record output.wav --duration 30
  
  # Real-time processing with playback
  anc-noise-profiling record --output-mode stream+file output.wav
  
  # List available audio devices
  anc-noise-profiling list-devices
        """
    )
    
    # Global options
    parser.add_argument("--config", "-c", type=Path, help="Configuration file path")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                       default="INFO", help="Logging level")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode (minimal output)")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # File processing command
    file_parser = subparsers.add_parser("process-file", help="Process an audio file")
    file_parser.add_argument("input_file", type=Path, help="Input audio file")
    file_parser.add_argument("output_file", type=Path, help="Output audio file")
    file_parser.add_argument("--profile-method", default="first_0.5",
                           help="Noise profile extraction method")
    file_parser.add_argument("--silence-threshold", type=float, default=0.01,
                           help="RMS threshold for silence detection (adaptive mode)")
    file_parser.add_argument("--min-silence-duration", type=float, default=0.3,
                           help="Minimum silence duration (adaptive mode)")
    file_parser.add_argument("--chunk-duration", type=float, default=0.5,
                           help="Processing chunk duration in seconds")
    file_parser.add_argument("--duration", type=float,
                           help="Maximum duration to process (seconds)")
    file_parser.add_argument("--save-raw", action="store_true",
                           help="Save raw audio alongside processed audio")
    
    # Microphone recording command
    record_parser = subparsers.add_parser("record", help="Record and process from microphone")
    record_parser.add_argument("output_file", nargs="?", type=Path,
                             help="Output audio file (required for file mode)")
    record_parser.add_argument("--output-mode", choices=["file", "stream", "stream+file"],
                             default="file", help="Output mode")
    record_parser.add_argument("--profile-method", default="first_0.5",
                             help="Noise profile extraction method")
    record_parser.add_argument("--device", type=int, help="Audio device index")
    record_parser.add_argument("--duration", type=float,
                             help="Recording duration in seconds")
    record_parser.add_argument("--chunk-duration", type=float, default=0.5,
                             help="Processing chunk duration in seconds")
    record_parser.add_argument("--save-raw", action="store_true",
                             help="Save raw audio alongside processed audio")
    
    # Device listing command
    subparsers.add_parser("list-devices", help="List available audio devices")
    
    # Configuration commands
    config_parser = subparsers.add_parser("config", help="Configuration management")
    config_subparsers = config_parser.add_subparsers(dest="config_action")
    
    show_config_parser = config_subparsers.add_parser("show", help="Show current configuration")
    
    save_config_parser = config_subparsers.add_parser("save", help="Save configuration to file")
    save_config_parser.add_argument("config_file", type=Path, help="Configuration file to create")
    save_config_parser.add_argument("--format", choices=["yaml", "json"], default="yaml",
                                   help="Configuration file format")
    
    return parser


def process_file_command(args, config: Config) -> None:
    """Handle file processing command."""
    processor = NoiseReductionProcessor(
        sample_rate=config.get("audio.sample_rate", 16000),
        chunk_duration=args.chunk_duration
    )
    
    try:
        result = processor.process_file(
            input_file=args.input_file,
            output_file=args.output_file,
            noise_profile_method=args.profile_method,
            silence_threshold=args.silence_threshold,
            min_silence_duration=args.min_silence_duration,
            save_raw_audio=args.save_raw,
            duration=args.duration
        )
        
        if not args.quiet:
            print(f"✓ Processing completed successfully")
            print(f"  Input: {result['input_file']}")
            print(f"  Output: {result['output_file']}")
            print(f"  Duration: {result['input_duration']:.2f}s -> {result['output_duration']:.2f}s")
            print(f"  Chunks: {result['chunks_processed']}")
            print(f"  Profile: {result['noise_profile']['method']}")
        
    except Exception as e:
        print(f"✗ Error processing file: {e}", file=sys.stderr)
        sys.exit(1)


def record_command(args, config: Config) -> None:
    """Handle microphone recording command."""
    if "file" in args.output_mode and not args.output_file:
        print("✗ Error: output_file is required when output_mode includes 'file'", file=sys.stderr)
        sys.exit(1)
    
    processor = NoiseReductionProcessor(
        sample_rate=config.get("audio.sample_rate", 16000),
        chunk_duration=args.chunk_duration
    )
    
    try:
        duration_msg = f" for {args.duration}s" if args.duration else ""
        mode_msg = f" (mode: {args.output_mode})"
        
        if not args.quiet:
            print(f"🎤 Starting microphone recording{duration_msg}{mode_msg}")
            print("   Press Ctrl+C to stop recording")
        
        processor.process_microphone(
            output_file=args.output_file,
            noise_profile_method=args.profile_method,
            output_mode=args.output_mode,
            save_raw_audio=args.save_raw,
            device=args.device,
            duration=args.duration
        )
        
        if not args.quiet:
            print("✓ Recording completed successfully")
            if args.output_file:
                print(f"  Saved to: {args.output_file}")
        
    except KeyboardInterrupt:
        if not args.quiet:
            print("\n✓ Recording stopped by user")
    except Exception as e:
        print(f"✗ Error during recording: {e}", file=sys.stderr)
        sys.exit(1)


def list_devices_command() -> None:
    """Handle device listing command."""
    print("Available audio devices:")
    AudioHandler.list_audio_devices()


def config_command(args, config: Config) -> None:
    """Handle configuration commands."""
    if args.config_action == "show":
        print("Current configuration:")
        print(config)
    elif args.config_action == "save":
        try:
            config.save_config_file(args.config_file, args.format)
            print(f"✓ Configuration saved to: {args.config_file}")
        except Exception as e:
            print(f"✗ Error saving configuration: {e}", file=sys.stderr)
            sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Load configuration
    config = Config(args.config if hasattr(args, 'config') else None)
    
    # Setup logging
    log_level = "WARNING" if args.quiet else args.log_level
    setup_logging(level=log_level, include_timestamp=not args.quiet)
    
    # Handle commands
    if args.command == "process-file":
        process_file_command(args, config)
    elif args.command == "record":
        record_command(args, config)
    elif args.command == "list-devices":
        list_devices_command()
    elif args.command == "config":
        config_command(args, config)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()