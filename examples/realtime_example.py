"""
Real-time processing examples for ANC with Noise Profiling

This script demonstrates various ways to use the real-time noise reduction functionality.
"""

import time
from anc_noise_profiling import reduce_noise_realtime, NoiseReductionConfig

def microphone_to_file():
    """Record from microphone and save to file."""
    print("=== Microphone to File ===")
    
    output_file = "mic_recording.wav"
    
    print("Starting 10-second recording from microphone...")
    print("Speak into your microphone!")
    
    try:
        result = reduce_noise_realtime(
            input_source="mic",
            output_file=output_file,
            duration=10.0,  # Record for 10 seconds
            noise_profile="first_0.5"  # Use first 0.5s as noise profile
        )
        print(f"✓ Recording saved: {output_file}")
    except Exception as e:
        print(f"✗ Recording failed: {e}")


def microphone_live_streaming():
    """Real-time microphone processing with live audio output."""
    print("\n=== Live Microphone Streaming ===")
    
    print("Starting live noise reduction...")
    print("Speak into your microphone - you'll hear the processed audio!")
    print("Press Ctrl+C to stop...")
    
    try:
        result = reduce_noise_realtime(
            input_source="mic",
            output_mode="stream",  # Live streaming only
            chunk_duration=0.1,    # Low latency
            duration=None          # Unlimited duration
        )
        print("✓ Live streaming completed")
    except KeyboardInterrupt:
        print("\n✓ Streaming stopped by user")
    except Exception as e:
        print(f"✗ Streaming failed: {e}")


def microphone_stream_and_save():
    """Real-time processing with both live streaming and file saving."""
    print("\n=== Microphone: Stream + Save ===")
    
    output_file = "live_stream_and_save.wav"
    
    print("Starting live streaming with file saving...")
    print("Duration: 15 seconds")
    print("You'll hear processed audio AND it will be saved to file")
    
    try:
        result = reduce_noise_realtime(
            input_source="mic",
            output_file=output_file,
            output_mode="stream+file",  # Both streaming and saving
            duration=15.0,
            save_raw_audio=True  # Also save original recording
        )
        print(f"✓ Live streaming completed, file saved: {output_file}")
        print(f"✓ Raw audio saved: {output_file.replace('.wav', '_raw.wav')}")
    except Exception as e:
        print(f"✗ Processing failed: {e}")


def file_to_stream():
    """Process audio file with real-time streaming output."""
    print("\n=== File to Stream ===")
    
    input_file = "example_input.wav"  # Replace with your audio file
    
    print(f"Streaming processed audio from file: {input_file}")
    print("You'll hear the cleaned audio in real-time")
    
    try:
        result = reduce_noise_realtime(
            input_source="file",
            input_file=input_file,
            output_mode="stream",
            noise_profile="adaptive",
            chunk_duration=0.5
        )
        print("✓ File streaming completed")
    except FileNotFoundError:
        print(f"⚠ Input file not found: {input_file}")
        print("  Please provide a valid audio file path")
    except Exception as e:
        print(f"✗ Streaming failed: {e}")


def custom_realtime_config():
    """Real-time processing with custom configuration."""
    print("\n=== Custom Real-time Configuration ===")
    
    # Create custom configuration
    config = NoiseReductionConfig(
        noise_profile="adaptive",
        silence_threshold=0.02,
        min_silence_duration=0.5,
        output_mode="stream+file",
        chunk_duration=0.2,  # Higher responsiveness 
        save_raw_audio=True,
        device=None,  # Use default microphone
        duration=8.0,  # 8 seconds
        sample_rate=22050  # Higher quality
    )
    
    output_file = "custom_realtime.wav"
    
    print("Recording with custom configuration...")
    print("- Adaptive noise detection")
    print("- Higher sample rate (22kHz)")
    print("- Low latency (200ms chunks)")
    print("- 8 second duration")
    
    try:
        result = reduce_noise_realtime(
            input_source="mic",
            output_file=output_file,
            config=config
        )
        print(f"✓ Custom recording completed: {output_file}")
    except Exception as e:
        print(f"✗ Custom recording failed: {e}")


def device_selection_example():
    """Example showing how to select specific audio devices."""
    print("\n=== Audio Device Selection ===")
    
    try:
        import sounddevice as sd
        
        print("Available audio devices:")
        print(sd.query_devices())
        
        # You can specify a device by ID
        device_id = None  # Replace with specific device ID if needed
        
        print(f"\nUsing device ID: {device_id} (None = default)")
        
        result = reduce_noise_realtime(
            input_source="mic",
            output_file="device_test.wav",
            output_mode="file",
            device=device_id,
            duration=5.0
        )
        print("✓ Device selection test completed")
        
    except ImportError:
        print("⚠ sounddevice not available for device listing")
    except Exception as e:
        print(f"✗ Device test failed: {e}")


if __name__ == "__main__":
    print("ANC with Noise Profiling - Real-time Processing Examples")
    print("=" * 60)
    
    # Note about audio requirements
    print("\nNOTE: These examples require:")
    print("- A working microphone for mic input examples")
    print("- Speakers/headphones for streaming output examples")
    print("- Audio files for file input examples")
    print("\nPress Enter to continue or Ctrl+C to exit...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\nExiting...")
        exit()
    
    # Run examples (comment out any you don't want to run)
    microphone_to_file()
    
    # Uncomment to run live streaming examples:
    # microphone_live_streaming()
    # microphone_stream_and_save()
    # file_to_stream()
    # custom_realtime_config()
    # device_selection_example()
    
    print("\n" + "=" * 60)
    print("Real-time examples completed!")
    print("\nNote: Uncomment other examples in the script to try them.")
    print("Some examples require manual intervention (Ctrl+C to stop).")