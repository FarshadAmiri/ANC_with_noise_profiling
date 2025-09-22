"""
Real-time streaming functionality for ANC with Noise Profiling
"""

from .realtime import reduce_noise_realtime, reduce_noise_streaming

__all__ = [
    "reduce_noise_realtime",
    "reduce_noise_streaming"  # Legacy compatibility
]