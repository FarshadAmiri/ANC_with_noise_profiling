"""
Configuration settings for ANC with Noise Profiling
"""

from typing import Optional, Union
from dataclasses import dataclass


@dataclass
class NoiseReductionConfig:
    """Configuration class for noise reduction parameters."""
    
    # Noise profile settings
    noise_profile: str = "first_0.5"
    silence_threshold: float = 0.01
    min_silence_duration: float = 0.3
    
    # Processing settings
    chunk_duration: float = 0.5
    sample_rate: int = 16000
    
    # Output settings
    save_raw_audio: bool = False
    visualization: bool = False
    
    # Real-time settings
    output_mode: str = "file"  # "file", "stream", "stream+file"
    device: Optional[int] = None
    duration: Optional[float] = None
    
    def __post_init__(self):
        """Validate configuration parameters."""
        if self.output_mode not in ["file", "stream", "stream+file"]:
            raise ValueError("output_mode must be 'file', 'stream', or 'stream+file'")
        
        if self.silence_threshold < 0 or self.silence_threshold > 1:
            raise ValueError("silence_threshold must be between 0 and 1")
        
        if self.min_silence_duration <= 0:
            raise ValueError("min_silence_duration must be positive")
        
        if self.chunk_duration <= 0:
            raise ValueError("chunk_duration must be positive")
        
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive")


# Default configuration instance
DEFAULT_CONFIG = NoiseReductionConfig()