"""
Audio processing utilities for ANC with Noise Profiling
"""

import os
import numpy as np
from typing import Tuple, Optional, Union
import logging

logger = logging.getLogger(__name__)


def load_audio(file_path: str) -> Tuple[np.ndarray, int]:
    """
    Load audio file and return audio data and sample rate.
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        Tuple of (audio_data, sample_rate)
        
    Raises:
        FileNotFoundError: If the audio file doesn't exist
        ValueError: If the audio file cannot be loaded
    """
    try:
        import soundfile as sf
    except ImportError:
        raise ImportError("soundfile is required. Install with: pip install soundfile")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")
    
    try:
        data, rate = sf.read(file_path)
        logger.info(f"Loaded audio file: {file_path}, shape: {data.shape}, rate: {rate}")
        return data, rate
    except Exception as e:
        raise ValueError(f"Failed to load audio file {file_path}: {str(e)}")


def save_audio(file_path: str, audio_data: np.ndarray, sample_rate: int) -> None:
    """
    Save audio data to file.
    
    Args:
        file_path: Path to save the audio file
        audio_data: Audio data to save
        sample_rate: Sample rate of the audio
        
    Raises:
        ValueError: If the audio data is invalid
    """
    try:
        import soundfile as sf
    except ImportError:
        raise ImportError("soundfile is required. Install with: pip install soundfile")
    
    if audio_data is None or len(audio_data) == 0:
        raise ValueError("Audio data is empty")
    
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        sf.write(file_path, audio_data, sample_rate)
        logger.info(f"Saved audio file: {file_path}")
    except Exception as e:
        raise ValueError(f"Failed to save audio file {file_path}: {str(e)}")


def convert_to_mono(audio_data: np.ndarray) -> np.ndarray:
    """
    Convert stereo audio to mono by averaging channels.
    
    Args:
        audio_data: Audio data array
        
    Returns:
        Mono audio data
    """
    if len(audio_data.shape) > 1:
        logger.info("Converting stereo audio to mono")
        return np.mean(audio_data, axis=1)
    return audio_data


def extract_noise_profile(
    audio_data: np.ndarray, 
    sample_rate: int,
    noise_profile_spec: str,
    silence_threshold: float = 0.01,
    min_silence_duration: float = 0.3
) -> Tuple[np.ndarray, Optional[int], Optional[int]]:
    """
    Extract noise profile from audio data.
    
    Args:
        audio_data: Input audio data
        sample_rate: Sample rate of the audio
        noise_profile_spec: Noise profile specification:
            - Path to noise file
            - "first_X" for first X seconds
            - "last_X" for last X seconds  
            - "adaptive" for automatic detection
        silence_threshold: RMS threshold for silence detection (for adaptive)
        min_silence_duration: Minimum silence duration for adaptive detection
        
    Returns:
        Tuple of (noise_profile, start_sample, end_sample)
        
    Raises:
        ValueError: If noise profile specification is invalid
    """
    # If it's a file path, load the noise profile
    if os.path.exists(noise_profile_spec):
        noise_profile, _ = load_audio(noise_profile_spec)
        return convert_to_mono(noise_profile), 0, len(noise_profile)
    
    # Handle time-based specifications
    if noise_profile_spec.startswith("first_") or noise_profile_spec.startswith("last_"):
        try:
            part, seconds_str = noise_profile_spec.split("_")
            seconds = float(seconds_str)
            sample_count = int(seconds * sample_rate)
            
            if sample_count > len(audio_data):
                logger.warning(f"Requested {seconds}s but audio is only {len(audio_data)/sample_rate:.2f}s long")
                sample_count = len(audio_data)
            
            if part == "first":
                noise_start = 0
                noise_end = sample_count
                noise_profile = audio_data[:sample_count]
            elif part == "last":
                noise_start = len(audio_data) - sample_count
                noise_end = len(audio_data)
                noise_profile = audio_data[-sample_count:]
            else:
                raise ValueError(f"Invalid keyword '{part}', expected 'first' or 'last'")
                
            logger.info(f"Extracted {part} {seconds}s as noise profile")
            return noise_profile, noise_start, noise_end
            
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid noise_profile_spec format: {noise_profile_spec}") from e
    
    # Handle adaptive detection
    elif noise_profile_spec == "adaptive":
        return _detect_adaptive_noise_profile(
            audio_data, sample_rate, silence_threshold, min_silence_duration
        )
    
    else:
        raise ValueError(f"Invalid noise_profile_spec: {noise_profile_spec}")


def _detect_adaptive_noise_profile(
    audio_data: np.ndarray,
    sample_rate: int, 
    silence_threshold: float,
    min_silence_duration: float
) -> Tuple[np.ndarray, int, int]:
    """
    Detect noise profile using adaptive silence detection.
    
    Args:
        audio_data: Input audio data
        sample_rate: Sample rate
        silence_threshold: RMS threshold for silence
        min_silence_duration: Minimum silence duration
        
    Returns:
        Tuple of (noise_profile, start_sample, end_sample)
    """
    window_size = int(0.05 * sample_rate)  # 50ms window
    stride = window_size // 2
    min_samples = int(min_silence_duration * sample_rate)
    
    best_start = None
    best_length = 0
    i = 0
    
    logger.info("Starting adaptive noise profile detection")
    
    while i < len(audio_data) - window_size:
        window = audio_data[i:i + window_size]
        rms = np.sqrt(np.mean(window**2))
        
        if rms < silence_threshold:
            start = i
            # Find end of silent region
            while i < len(audio_data) - window_size:
                window = audio_data[i:i + window_size]
                rms = np.sqrt(np.mean(window**2))
                if rms >= silence_threshold:
                    break
                i += stride
            
            end = i
            length = end - start
            
            if length > best_length and length >= min_samples:
                best_start, best_length = start, length
                logger.debug(f"Found silence region: {start}-{end} ({length/sample_rate:.2f}s)")
        else:
            i += stride
    
    if best_start is not None:
        noise_profile = audio_data[best_start:best_start + best_length]
        logger.info(f"Selected adaptive noise profile: {best_length/sample_rate:.2f}s")
        return noise_profile, best_start, best_start + best_length
    else:
        # Fallback to first 0.5 seconds
        logger.warning("No suitable silence region found, using first 0.5s as fallback")
        fallback_samples = int(0.5 * sample_rate)
        fallback_samples = min(fallback_samples, len(audio_data))
        return audio_data[:fallback_samples], 0, fallback_samples


def visualize_noise_profile(
    audio_data: np.ndarray,
    sample_rate: int,
    noise_start: Optional[int] = None,
    noise_end: Optional[int] = None,
    title: str = "Audio Waveform with Noise Profile"
) -> None:
    """
    Visualize audio waveform with highlighted noise profile region.
    
    Args:
        audio_data: Audio data to visualize
        sample_rate: Sample rate
        noise_start: Start sample of noise profile region
        noise_end: End sample of noise profile region
        title: Plot title
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        logger.warning("matplotlib not available, skipping visualization")
        return
    
    time_axis = np.arange(len(audio_data)) / sample_rate
    
    plt.figure(figsize=(16, 4))
    plt.plot(time_axis, audio_data, alpha=0.7, label="Audio Signal")
    
    if noise_start is not None and noise_end is not None:
        noise_time_start = noise_start / sample_rate
        noise_time_end = noise_end / sample_rate
        plt.axvspan(noise_time_start, noise_time_end, 
                   alpha=0.3, color='red', label='Noise Profile Region')
    
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.title(title)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    logger.info("Displayed audio visualization")