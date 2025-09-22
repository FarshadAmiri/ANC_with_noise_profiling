"""
Real-time streaming noise reduction for ANC with Noise Profiling
"""

import os
import numpy as np
import queue
import threading
import sys
import time
from typing import Optional, Union, Any
import logging

from ..core.audio_utils import load_audio, save_audio, convert_to_mono, extract_noise_profile
from ..config import NoiseReductionConfig, DEFAULT_CONFIG

logger = logging.getLogger(__name__)


def reduce_noise_realtime(
    input_source: str = "file",
    input_file: Optional[str] = None,
    output_file: Optional[str] = None,
    config: Optional[NoiseReductionConfig] = None,
    noise_profile: Optional[str] = None,
    silence_threshold: Optional[float] = None,
    min_silence_duration: Optional[float] = None,
    output_mode: Optional[str] = None,
    chunk_duration: Optional[float] = None,
    save_raw_audio: Optional[bool] = None,
    visualization: Optional[bool] = None,
    device: Optional[int] = None,
    duration: Optional[float] = None
) -> Optional[queue.Queue]:
    """
    Real-time noise reduction with noise profile, supporting mic or file input.
    
    Allows streaming, file saving, or both, with acceptable delay.
    Can run indefinitely (Ctrl+C to stop) if duration=None.
    Streaming playback included for 'stream' or 'stream+file' modes.
    
    Args:
        input_source: "file" or "mic" for input source
        input_file: Path to input file (required if input_source="file")
        output_file: Path to save output file (optional)
        config: Configuration object (optional, uses defaults if None)
        noise_profile: Noise profile specification (overrides config)
        silence_threshold: RMS threshold for silence detection (overrides config)
        min_silence_duration: Minimum silence duration (overrides config)
        output_mode: "file", "stream", or "stream+file" (overrides config)
        chunk_duration: Processing chunk duration in seconds (overrides config)
        save_raw_audio: Whether to save raw audio (overrides config)
        visualization: Whether to show visualization (overrides config)
        device: Audio device ID for microphone input (overrides config)
        duration: Recording duration in seconds, None for unlimited (overrides config)
        
    Returns:
        Queue object for streaming output (if output_mode includes "stream"), None otherwise
        
    Raises:
        ValueError: If parameters are invalid
        ImportError: If required dependencies are missing
    """
    # Import required libraries
    try:
        import sounddevice as sd
        import noisereduce as nr
    except ImportError as e:
        raise ImportError(f"Required audio libraries missing: {str(e)}. "
                         "Install with: pip install sounddevice noisereduce")
    
    # Use provided config or default
    if config is None:
        config = DEFAULT_CONFIG
    
    # Override config with explicit parameters
    actual_noise_profile = noise_profile if noise_profile is not None else config.noise_profile
    actual_silence_threshold = silence_threshold if silence_threshold is not None else config.silence_threshold
    actual_min_silence_duration = min_silence_duration if min_silence_duration is not None else config.min_silence_duration
    actual_output_mode = output_mode if output_mode is not None else config.output_mode
    actual_chunk_duration = chunk_duration if chunk_duration is not None else config.chunk_duration
    actual_save_raw = save_raw_audio if save_raw_audio is not None else config.save_raw_audio
    actual_visualization = visualization if visualization is not None else config.visualization
    actual_device = device if device is not None else config.device
    actual_duration = duration if duration is not None else config.duration
    
    logger.info(f"Starting real-time noise reduction: input={input_source}, output_mode={actual_output_mode}")
    
    # Initialize variables
    rate = config.sample_rate
    output_audio = []
    raw_audio = []
    stream_queue = queue.Queue()
    
    if input_source == "file":
        return _process_file_streaming(
            input_file, output_file, actual_noise_profile, actual_silence_threshold,
            actual_min_silence_duration, actual_output_mode, actual_chunk_duration,
            actual_save_raw, actual_visualization, actual_duration, rate,
            output_audio, raw_audio, stream_queue
        )
    
    elif input_source == "mic":
        return _process_microphone_streaming(
            output_file, actual_noise_profile, actual_silence_threshold,
            actual_min_silence_duration, actual_output_mode, actual_chunk_duration,
            actual_save_raw, actual_visualization, actual_device, actual_duration,
            rate, output_audio, raw_audio, stream_queue
        )
    
    else:
        raise ValueError(f"Invalid input_source: {input_source}. Must be 'file' or 'mic'")


def _process_file_streaming(
    input_file: Optional[str],
    output_file: Optional[str], 
    noise_profile: str,
    silence_threshold: float,
    min_silence_duration: float,
    output_mode: str,
    chunk_duration: float,
    save_raw_audio: bool,
    visualization: bool,
    duration: Optional[float],
    rate: int,
    output_audio: list,
    raw_audio: list,
    stream_queue: queue.Queue
) -> Optional[queue.Queue]:
    """Process file input with streaming output."""
    try:
        import noisereduce as nr
    except ImportError:
        raise ImportError("noisereduce is required. Install with: pip install noisereduce")
    
    if not input_file:
        raise ValueError("input_file must be specified when input_source='file'")
    
    logger.info(f"Processing file: {input_file}")
    
    # Load and prepare audio
    data, rate = load_audio(input_file)
    data = convert_to_mono(data)
    total_samples = len(data)
    
    if duration is not None:
        max_samples = int(duration * rate)
        data = data[:max_samples]
        total_samples = len(data)
    
    # Extract noise profile
    noise_profile_data, noise_start, noise_end = extract_noise_profile(
        data, rate, noise_profile, silence_threshold, min_silence_duration
    )
    
    # Process in chunks
    chunk_samples = int(chunk_duration * rate)
    logger.info(f"Processing {total_samples} samples in chunks of {chunk_samples}")
    
    for start in range(0, total_samples, chunk_samples):
        chunk = data[start:start + chunk_samples]
        
        # Apply noise reduction
        reduced = nr.reduce_noise(y=chunk, y_noise=noise_profile_data, sr=rate)
        
        # Output processing
        if output_mode in ("stream", "stream+file"):
            stream_queue.put(reduced)
        if output_mode in ("file", "stream+file"):
            output_audio.extend(reduced)
        
        raw_audio.extend(chunk)
    
    # Save final output
    _save_final_output(output_file, output_audio, raw_audio, rate, save_raw_audio, output_mode)
    
    return stream_queue if output_mode in ("stream", "stream+file") else None


def _process_microphone_streaming(
    output_file: Optional[str],
    noise_profile: str,
    silence_threshold: float,
    min_silence_duration: float,
    output_mode: str,
    chunk_duration: float,
    save_raw_audio: bool,
    visualization: bool,
    device: Optional[int],
    duration: Optional[float],
    rate: int,
    output_audio: list,
    raw_audio: list,
    stream_queue: queue.Queue
) -> Optional[queue.Queue]:
    """Process microphone input with streaming output."""
    try:
        import sounddevice as sd
        import noisereduce as nr
    except ImportError:
        raise ImportError("sounddevice and noisereduce are required")
    
    chunk_samples = int(chunk_duration * rate)
    logger.info(f"Recording from microphone{' indefinitely' if duration is None else f' for {duration}s'}")
    
    recorded_samples = 0
    noise_profile_data = None
    stop_flag = False
    
    # Playback thread for real-time streaming
    def playback_thread():
        try:
            with sd.OutputStream(channels=1, samplerate=rate, dtype="float32") as out_stream:
                while not stop_flag or not stream_queue.empty():
                    try:
                        chunk = stream_queue.get(timeout=0.1)
                        out_stream.write(chunk.astype(np.float32))
                    except queue.Empty:
                        time.sleep(0.01)
        except Exception as e:
            logger.error(f"Playback thread error: {e}")
    
    # Start playback thread if streaming
    t_playback = None
    if output_mode in ("stream", "stream+file"):
        t_playback = threading.Thread(target=playback_thread, daemon=True)
        t_playback.start()
        logger.info("Started playback thread")
    
    def callback(indata: np.ndarray, frames: int, time_info: Any, status: Any) -> None:
        nonlocal recorded_samples, noise_profile_data, stop_flag
        
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        chunk = indata[:frames, 0]
        raw_audio.extend(chunk)
        
        # Extract noise profile from first 0.5s
        if noise_profile_data is None:
            profile_samples = int(0.5 * rate)
            if len(raw_audio) >= profile_samples:
                noise_profile_data = np.array(raw_audio[:profile_samples])
                logger.info("Extracted noise profile from first 0.5s of recording")
        
        # Apply noise reduction if profile is available
        if noise_profile_data is not None:
            try:
                reduced = nr.reduce_noise(y=chunk, y_noise=noise_profile_data, sr=rate)
            except Exception as e:
                logger.warning(f"Noise reduction failed: {e}, using original audio")
                reduced = chunk
        else:
            reduced = chunk
        
        # Output processing
        if output_mode in ("stream", "stream+file"):
            stream_queue.put(reduced)
        if output_mode in ("file", "stream+file"):
            output_audio.extend(reduced)
        
        recorded_samples += frames
        if duration is not None and recorded_samples >= int(duration * rate):
            stop_flag = True
            raise sd.CallbackStop()
    
    # Start recording
    try:
        with sd.InputStream(
            callback=callback, 
            channels=1, 
            samplerate=rate,
            blocksize=chunk_samples, 
            dtype="float32", 
            device=device
        ):
            try:
                if duration is not None:
                    sd.sleep(int(duration * 1000))
                else:
                    while not stop_flag:
                        time.sleep(0.1)
            except KeyboardInterrupt:
                logger.info("Recording stopped by user")
                stop_flag = True
    
    except Exception as e:
        logger.error(f"Recording error: {e}")
        stop_flag = True
    
    # Wait for playback to finish
    if t_playback and t_playback.is_alive():
        logger.info("Waiting for playback to finish...")
        t_playback.join(timeout=5)
    
    # Save final output
    _save_final_output(output_file, output_audio, raw_audio, rate, save_raw_audio, output_mode)
    
    return stream_queue if output_mode in ("stream", "stream+file") else None


def _save_final_output(
    output_file: Optional[str],
    output_audio: list,
    raw_audio: list,
    rate: int,
    save_raw_audio: bool,
    output_mode: str
) -> None:
    """Save final audio output to files."""
    if output_mode in ("file", "stream+file") and output_file and output_audio:
        try:
            save_audio(output_file, np.array(output_audio), rate)
            logger.info(f"Denoised audio saved to {output_file}")
            
            if save_raw_audio and raw_audio:
                raw_out_file = output_file.replace(".wav", "_raw.wav")
                save_audio(raw_out_file, np.array(raw_audio), rate)
                logger.info(f"Raw audio saved to {raw_out_file}")
        except Exception as e:
            logger.error(f"Failed to save output: {e}")


# Legacy function for backward compatibility
def reduce_noise_streaming(**kwargs) -> Optional[queue.Queue]:
    """
    Legacy function for backward compatibility.
    
    This function provides the same interface as the original script function.
    It's recommended to use reduce_noise_realtime() for new code.
    """
    logger.warning("reduce_noise_streaming() is deprecated. Use reduce_noise_realtime() instead.")
    return reduce_noise_realtime(**kwargs)