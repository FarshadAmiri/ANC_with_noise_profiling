"""
Command-line interface for ANC with Noise Profiling
"""

import argparse
import sys
import os
from typing import Optional

try:
    from ..core.noise_reduction import reduce_noise_file, setup_logging
    from ..streaming.realtime import reduce_noise_realtime
    from ..config import NoiseReductionConfig
    _dependencies_available = True
except ImportError:
    _dependencies_available = False
    # Create dummy functions for CLI help when dependencies aren't available
    def reduce_noise_file(*args, **kwargs):
        raise ImportError("Audio dependencies required. Install with: pip install -r requirements.txt")
    def reduce_noise_realtime(*args, **kwargs):
        raise ImportError("Audio dependencies required. Install with: pip install -r requirements.txt")
    def setup_logging(*args, **kwargs):
        import logging
        logging.basicConfig(level=logging.INFO)
    from ..config import NoiseReductionConfig


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="ANC with Noise Profiling - Active Noise Cancellation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # File-based noise reduction
  anc-noise-profiling file input.wav output.wav --noise-profile first_0.5
  
  # Real-time microphone processing
  anc-noise-profiling realtime --input-source mic --output-file output.wav
  
  # Adaptive noise profile detection
  anc-noise-profiling file input.wav output.wav --noise-profile adaptive --visualization
  
  # Stream processing with file input
  anc-noise-profiling realtime --input-source file --input-file input.wav --output-mode stream+file

Noise Profile Options:
  - first_X: Use first X seconds (e.g., first_0.5, first_1.0)
  - last_X: Use last X seconds (e.g., last_0.5, last_2.0)
  - adaptive: Automatically detect silent regions
  - /path/to/noise.wav: Use external noise file
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Processing mode')
    
    # File processing command
    file_parser = subparsers.add_parser('file', help='Process audio file')
    file_parser.add_argument('input_file', help='Input audio file path')
    file_parser.add_argument('output_file', help='Output audio file path')
    file_parser.add_argument('--noise-profile', default='first_0.5',
                           help='Noise profile specification (default: first_0.5)')
    file_parser.add_argument('--silence-threshold', type=float, default=0.01,
                           help='RMS threshold for silence detection (default: 0.01)')
    file_parser.add_argument('--min-silence-duration', type=float, default=0.3,
                           help='Minimum silence duration in seconds (default: 0.3)')
    file_parser.add_argument('--visualization', action='store_true',
                           help='Show waveform visualization')
    file_parser.add_argument('--save-raw-audio', action='store_true',
                           help='Save original audio alongside processed')
    
    # Real-time processing command  
    realtime_parser = subparsers.add_parser('realtime', help='Real-time processing')
    realtime_parser.add_argument('--input-source', choices=['file', 'mic'], default='mic',
                               help='Input source (default: mic)')
    realtime_parser.add_argument('--input-file', 
                               help='Input file path (required if input-source=file)')
    realtime_parser.add_argument('--output-file',
                               help='Output file path (optional)')
    realtime_parser.add_argument('--noise-profile', default='first_0.5',
                               help='Noise profile specification (default: first_0.5)')
    realtime_parser.add_argument('--output-mode', choices=['file', 'stream', 'stream+file'],
                               default='file', help='Output mode (default: file)')
    realtime_parser.add_argument('--chunk-duration', type=float, default=0.5,
                               help='Processing chunk duration in seconds (default: 0.5)')
    realtime_parser.add_argument('--duration', type=float,
                               help='Recording duration in seconds (unlimited if not specified)')
    realtime_parser.add_argument('--device', type=int,
                               help='Audio device ID for microphone input')
    realtime_parser.add_argument('--silence-threshold', type=float, default=0.01,
                               help='RMS threshold for silence detection (default: 0.01)')
    realtime_parser.add_argument('--min-silence-duration', type=float, default=0.3,
                               help='Minimum silence duration in seconds (default: 0.3)')
    realtime_parser.add_argument('--save-raw-audio', action='store_true',
                               help='Save original audio alongside processed')
    realtime_parser.add_argument('--visualization', action='store_true',
                               help='Show waveform visualization')
    
    # Global options
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Logging level (default: INFO)')
    parser.add_argument('--sample-rate', type=int, default=16000,
                       help='Sample rate for audio processing (default: 16000)')
    
    return parser


def validate_args(args: argparse.Namespace) -> None:
    """Validate command-line arguments."""
    if args.command == 'file':
        if not os.path.exists(args.input_file):
            raise FileNotFoundError(f"Input file not found: {args.input_file}")
        
        # Ensure output directory exists
        output_dir = os.path.dirname(args.output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
    
    elif args.command == 'realtime':
        if args.input_source == 'file' and not args.input_file:
            raise ValueError("--input-file is required when --input-source=file")
        
        if args.input_source == 'file' and not os.path.exists(args.input_file):
            raise FileNotFoundError(f"Input file not found: {args.input_file}")
        
        if args.output_mode in ('file', 'stream+file') and not args.output_file:
            raise ValueError("--output-file is required when output-mode includes 'file'")


def run_file_processing(args: argparse.Namespace) -> None:
    """Run file-based noise reduction."""
    print(f"Processing file: {args.input_file}")
    print(f"Output file: {args.output_file}")
    print(f"Noise profile: {args.noise_profile}")
    
    # Create configuration
    config = NoiseReductionConfig(
        noise_profile=args.noise_profile,
        silence_threshold=args.silence_threshold,
        min_silence_duration=args.min_silence_duration,
        visualization=args.visualization,
        save_raw_audio=args.save_raw_audio,
        sample_rate=args.sample_rate
    )
    
    # Process file
    output_path = reduce_noise_file(
        input_file=args.input_file,
        output_file=args.output_file,
        config=config
    )
    
    print(f"✓ Processing completed successfully: {output_path}")


def run_realtime_processing(args: argparse.Namespace) -> None:
    """Run real-time noise reduction."""
    print(f"Real-time processing:")
    print(f"  Input source: {args.input_source}")
    if args.input_file:
        print(f"  Input file: {args.input_file}")
    if args.output_file:
        print(f"  Output file: {args.output_file}")
    print(f"  Output mode: {args.output_mode}")
    print(f"  Noise profile: {args.noise_profile}")
    
    # Create configuration
    config = NoiseReductionConfig(
        noise_profile=args.noise_profile,
        silence_threshold=args.silence_threshold,
        min_silence_duration=args.min_silence_duration,
        output_mode=args.output_mode,
        chunk_duration=args.chunk_duration,
        save_raw_audio=args.save_raw_audio,
        visualization=args.visualization,
        device=args.device,
        duration=args.duration,
        sample_rate=args.sample_rate
    )
    
    # Process in real-time
    try:
        stream_queue = reduce_noise_realtime(
            input_source=args.input_source,
            input_file=args.input_file,
            output_file=args.output_file,
            config=config
        )
        
        if stream_queue:
            print("✓ Real-time processing completed with streaming output")
        else:
            print("✓ Real-time processing completed")
            
    except KeyboardInterrupt:
        print("\n✓ Processing stopped by user")


def main() -> None:
    """Main entry point for the CLI."""
    parser = create_parser()
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    args = parser.parse_args()
    
    # Check if dependencies are available
    if not _dependencies_available:
        print("Error: Audio processing dependencies are not installed.", file=sys.stderr)
        print("Please install them with: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)
    
    # Setup logging
    setup_logging(args.log_level)
    
    try:
        # Validate arguments
        validate_args(args)
        
        # Run appropriate command
        if args.command == 'file':
            run_file_processing(args)
        elif args.command == 'realtime':
            run_realtime_processing(args)
        else:
            parser.print_help()
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()