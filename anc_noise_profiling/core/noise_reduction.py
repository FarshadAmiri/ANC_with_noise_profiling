"""
Core noise reduction functionality for ANC with Noise Profiling
"""

import os
import numpy as np
from typing import Optional, Union
import logging

from .audio_utils import (
    load_audio, save_audio, convert_to_mono, 
    extract_noise_profile, visualize_noise_profile
)
from ..config import NoiseReductionConfig, DEFAULT_CONFIG

logger = logging.getLogger(__name__)


def reduce_noise_file(
    input_file: str,
    output_file: str,
    noise_profile: str = "first_0.5",
    config: Optional[NoiseReductionConfig] = None,
    silence_threshold: Optional[float] = None,
    min_silence_duration: Optional[float] = None,
    visualization: Optional[bool] = None,
    save_raw_audio: Optional[bool] = None
) -> str:
    """
    Reduce noise in an audio file using a noise profile.
    
    This function loads an audio file, extracts or loads a noise profile,
    and applies noise reduction to produce a cleaner output file.
    
    Args:
        input_file: Path to the noisy input audio file
        output_file: Path to save the denoised output
        noise_profile: Noise profile specification:
            - Path to a noise file
            - "first_X" for first X seconds (e.g., "first_0.5")
            - "last_X" for last X seconds (e.g., "last_1.0") 
            - "adaptive" for automatic silence detection
        config: Configuration object (optional, uses defaults if None)
        silence_threshold: RMS threshold for silence detection (overrides config)
        min_silence_duration: Minimum silence duration for adaptive detection (overrides config)
        visualization: Whether to show waveform plot (overrides config)
        save_raw_audio: Whether to save original audio alongside processed (overrides config)
        
    Returns:
        Path to the output file
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If parameters are invalid
        ImportError: If required dependencies are missing
    """
    # Use provided config or default
    if config is None:
        config = DEFAULT_CONFIG
    
    # Override config with explicit parameters
    actual_silence_threshold = silence_threshold if silence_threshold is not None else config.silence_threshold
    actual_min_silence_duration = min_silence_duration if min_silence_duration is not None else config.min_silence_duration
    actual_visualization = visualization if visualization is not None else config.visualization
    actual_save_raw = save_raw_audio if save_raw_audio is not None else config.save_raw_audio
    
    logger.info(f"Starting noise reduction: {input_file} -> {output_file}")
    logger.info(f"Noise profile: {noise_profile}")
    
    # Validate inputs
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Import noise reduction library
    try:
        import noisereduce as nr
    except ImportError:
        raise ImportError("noisereduce is required. Install with: pip install noisereduce")
    
    # Load and prepare audio
    logger.info("Loading input audio...")
    audio_data, sample_rate = load_audio(input_file)
    audio_data = convert_to_mono(audio_data)
    
    # Extract noise profile
    logger.info("Extracting noise profile...")
    noise_profile_data, noise_start, noise_end = extract_noise_profile(
        audio_data, 
        sample_rate,
        noise_profile,
        actual_silence_threshold,
        actual_min_silence_duration
    )
    
    # Apply noise reduction
    logger.info("Applying noise reduction...")
    try:
        reduced_audio = nr.reduce_noise(
            y=audio_data, 
            y_noise=noise_profile_data, 
            sr=sample_rate
        )
        logger.info("Noise reduction completed successfully")
    except Exception as e:
        raise ValueError(f"Noise reduction failed: {str(e)}")
    
    # Save output
    logger.info("Saving output file...")
    save_audio(output_file, reduced_audio, sample_rate)
    
    # Save raw audio if requested
    if actual_save_raw:
        raw_output_file = _get_raw_filename(output_file)
        save_audio(raw_output_file, audio_data, sample_rate)
        logger.info(f"Saved raw audio: {raw_output_file}")
    
    # Show visualization if requested
    if actual_visualization:
        logger.info("Displaying visualization...")
        visualize_noise_profile(
            audio_data, sample_rate, noise_start, noise_end,
            title=f"Noise Reduction: {os.path.basename(input_file)}"
        )
    
    logger.info(f"Noise reduction completed: {output_file}")
    return output_file


def reduce_noise_with_profile(
    input_file: str,
    output_file: str, 
    noise_profile_file: str = "last_0.5",
    silence_threshold: float = 0.01,
    min_silence_duration: float = 0.3,
    visualization: bool = False
) -> str:
    """
    Legacy function for backward compatibility.
    
    This function provides the same interface as the original notebook function.
    It's recommended to use reduce_noise_file() for new code.
    
    Args:
        input_file: Path to the noisy input audio file
        output_file: Path to save the denoised output  
        noise_profile_file: Noise profile specification
        silence_threshold: RMS threshold for silence detection
        min_silence_duration: Minimum silence duration for adaptive detection
        visualization: Whether to show waveform plot
        
    Returns:
        Path to the output file
    """
    logger.warning("reduce_noise_with_profile() is deprecated. Use reduce_noise_file() instead.")
    
    return reduce_noise_file(
        input_file=input_file,
        output_file=output_file,
        noise_profile=noise_profile_file,
        silence_threshold=silence_threshold,
        min_silence_duration=min_silence_duration,
        visualization=visualization
    )


def _get_raw_filename(output_file: str) -> str:
    """Generate filename for raw audio output."""
    base, ext = os.path.splitext(output_file)
    return f"{base}_raw{ext}"


# Setup logging
def setup_logging(level: str = "INFO") -> None:
    """Setup logging for the noise reduction module."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )