"""
ANC Noise Profiling - Active Noise Cancellation with Noise Profiling

A Python package for active noise cancellation that extracts noise profiles
from the input audio itself, supporting both real-time and file-based processing.
"""

__version__ = "1.0.0"
__author__ = "Farshad Amiri"

# Import main classes for easy access
try:
    from .core.processor import NoiseReductionProcessor
    from .profiling.extractor import NoiseProfileExtractor
    from .io.audio_handler import AudioHandler
    from .utils.config import Config
    from .utils.logging_config import setup_logging
    
    __all__ = [
        "NoiseReductionProcessor",
        "NoiseProfileExtractor", 
        "AudioHandler",
        "Config",
        "setup_logging",
    ]
except ImportError:
    # Handle case where dependencies aren't installed yet
    __all__ = []