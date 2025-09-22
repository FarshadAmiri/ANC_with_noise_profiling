"""
Legacy Script Compatibility Layer

This module provides compatibility functions that match the original script interfaces
while using the new professional package structure underneath.
"""

import warnings
from anc_noise_profiling import reduce_noise_file, reduce_noise_realtime

def legacy_reduce_noise_with_profile(
    input_file, 
    output_file, 
    noise_profile_file="last_0.5",
    silence_threshold=0.01, 
    min_silence_duration=0.3, 
    visualization=False
):
    """
    Legacy compatibility function for the original notebook function.
    
    This function provides exactly the same interface as the original
    reduce_noise_with_profile function from the Jupyter notebook.
    
    Args:
        input_file (str): Path to the noisy input audio file
        output_file (str): Path to save the denoised output
        noise_profile_file (str): Noise profile specification
        silence_threshold (float): RMS threshold for silence detection
        min_silence_duration (float): Minimum silence duration
        visualization (bool): Whether to show waveform plot
        
    Returns:
        str: Path to the output file
    """
    warnings.warn(
        "This legacy function is deprecated. Use anc_noise_profiling.reduce_noise_file() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    return reduce_noise_file(
        input_file=input_file,
        output_file=output_file,
        noise_profile=noise_profile_file,
        silence_threshold=silence_threshold,
        min_silence_duration=min_silence_duration,
        visualization=visualization
    )


def legacy_reduce_noise_streaming(
    input_source="file",
    input_file=None,
    output_file=None,
    noise_profile_file="first_0.5",
    silence_threshold=0.01,
    min_silence_duration=0.3,
    output_mode="file",
    chunk_duration=0.5,
    save_raw_audio=False,
    visualization=False,
    device=None,
    duration=None
):
    """
    Legacy compatibility function for the original realtime script function.
    
    This function provides exactly the same interface as the original
    reduce_noise_streaming function from the Python script.
    
    Args:
        input_source (str): "file" or "mic"
        input_file (str): Input file path
        output_file (str): Output file path  
        noise_profile_file (str): Noise profile specification
        silence_threshold (float): RMS threshold for silence detection
        min_silence_duration (float): Minimum silence duration
        output_mode (str): "file", "stream", or "stream+file"
        chunk_duration (float): Processing chunk duration
        save_raw_audio (bool): Whether to save raw audio
        visualization (bool): Whether to show visualization
        device (int): Audio device ID
        duration (float): Recording duration
        
    Returns:
        queue.Queue or None: Stream queue for real-time output
    """
    warnings.warn(
        "This legacy function is deprecated. Use anc_noise_profiling.reduce_noise_realtime() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    return reduce_noise_realtime(
        input_source=input_source,
        input_file=input_file,
        output_file=output_file,
        noise_profile=noise_profile_file,
        silence_threshold=silence_threshold,
        min_silence_duration=min_silence_duration,
        output_mode=output_mode,
        chunk_duration=chunk_duration,
        save_raw_audio=save_raw_audio,
        visualization=visualization,
        device=device,
        duration=duration
    )


# Make legacy functions available at module level for easy import
__all__ = ["legacy_reduce_noise_with_profile", "legacy_reduce_noise_streaming"]