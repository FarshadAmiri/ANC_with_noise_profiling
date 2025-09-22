"""
ANC with Noise Profiling

A professional active noise cancellation library that works both real-time and file-based,
with the ability to extract noise profiles from the input audio file itself.

This package provides:
- File-based noise reduction with various noise profile extraction methods
- Real-time noise reduction with microphone input and live audio processing
- Adaptive noise profile detection
- Configurable processing parameters
- Command-line interface for easy usage

Basic usage:
    # File-based processing
    from anc_noise_profiling import reduce_noise_file
    reduce_noise_file("input.wav", "output.wav", noise_profile="first_0.5")
    
    # Real-time processing
    from anc_noise_profiling import reduce_noise_realtime
    reduce_noise_realtime(input_source="mic", output_file="output.wav")
"""

__version__ = "1.0.0"
__author__ = "Farshad Amiri"

# Import configuration (this doesn't require external dependencies)
from .config.settings import NoiseReductionConfig

# Conditional imports for main functions (to handle missing dependencies gracefully)
try:
    from .core.noise_reduction import reduce_noise_file
    _reduce_noise_file_available = True
except ImportError:
    _reduce_noise_file_available = False
    def reduce_noise_file(*args, **kwargs):
        raise ImportError("reduce_noise_file requires audio dependencies. Install with: pip install -r requirements.txt")

try:
    from .streaming.realtime import reduce_noise_realtime
    _reduce_noise_realtime_available = True
except ImportError:
    _reduce_noise_realtime_available = False
    def reduce_noise_realtime(*args, **kwargs):
        raise ImportError("reduce_noise_realtime requires audio dependencies. Install with: pip install -r requirements.txt")

__all__ = [
    "reduce_noise_file",
    "reduce_noise_realtime", 
    "NoiseReductionConfig",
    "__version__",
    "__author__"
]