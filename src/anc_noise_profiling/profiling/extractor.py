"""Noise profile extraction from audio data."""

import os
import logging
from typing import Union, Tuple, Optional
import numpy as np
import soundfile as sf


class NoiseProfileExtractor:
    """Extracts noise profiles from audio data using various methods."""
    
    def __init__(self, sample_rate: int = 16000):
        """Initialize the noise profile extractor.
        
        Args:
            sample_rate: Sample rate for audio processing
        """
        self.sample_rate = sample_rate
        self.logger = logging.getLogger(__name__)
    
    def extract_profile(
        self,
        audio_data: np.ndarray,
        method: str = "first_0.5",
        silence_threshold: float = 0.01,
        min_silence_duration: float = 0.3,
    ) -> Tuple[np.ndarray, dict]:
        """Extract noise profile from audio data.
        
        Args:
            audio_data: Input audio data
            method: Extraction method ('first_X', 'last_X', 'adaptive', or file path)
            silence_threshold: RMS threshold for silence detection (adaptive mode)
            min_silence_duration: Minimum duration for silence segments (adaptive mode)
            
        Returns:
            Tuple of (noise_profile, metadata) where metadata contains extraction info
        """
        self.logger.info(f"Extracting noise profile using method: {method}")
        
        # Handle file path case
        if os.path.exists(method):
            return self._extract_from_file(method)
        
        # Handle keyword-based extraction
        if method.startswith("first_") or method.startswith("last_"):
            return self._extract_temporal(audio_data, method)
        elif method == "adaptive":
            return self._extract_adaptive(
                audio_data, silence_threshold, min_silence_duration
            )
        else:
            raise ValueError(f"Unknown extraction method: {method}")
    
    def _extract_from_file(self, file_path: str) -> Tuple[np.ndarray, dict]:
        """Extract noise profile from an external file."""
        try:
            noise_profile, rate = sf.read(file_path)
            if len(noise_profile.shape) > 1:
                noise_profile = np.mean(noise_profile, axis=1)
            
            metadata = {
                "method": "file",
                "file_path": file_path,
                "duration": len(noise_profile) / rate,
                "sample_rate": rate
            }
            
            self.logger.info(f"Loaded noise profile from file: {file_path}")
            return noise_profile, metadata
            
        except Exception as e:
            raise ValueError(f"Failed to load noise profile from {file_path}: {e}")
    
    def _extract_temporal(self, audio_data: np.ndarray, method: str) -> Tuple[np.ndarray, dict]:
        """Extract noise profile from first or last portion of audio."""
        try:
            part, seconds_str = method.split("_")
            seconds = float(seconds_str)
            sample_count = int(seconds * self.sample_rate)
            
            if part == "first":
                start_sample = 0
                end_sample = min(sample_count, len(audio_data))
                noise_profile = audio_data[:end_sample]
            elif part == "last":
                start_sample = max(0, len(audio_data) - sample_count)
                end_sample = len(audio_data)
                noise_profile = audio_data[start_sample:]
            else:
                raise ValueError(f"Invalid temporal method: {part}")
            
            metadata = {
                "method": method,
                "start_sample": start_sample,
                "end_sample": end_sample,
                "duration": len(noise_profile) / self.sample_rate,
                "sample_rate": self.sample_rate
            }
            
            self.logger.info(f"Extracted {part} {seconds}s as noise profile")
            return noise_profile, metadata
            
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid temporal extraction method: {method}") from e
    
    def _extract_adaptive(
        self,
        audio_data: np.ndarray,
        silence_threshold: float,
        min_silence_duration: float
    ) -> Tuple[np.ndarray, dict]:
        """Extract noise profile using adaptive silence detection."""
        window_size = int(0.05 * self.sample_rate)  # 50ms windows
        stride = window_size // 2
        min_samples = int(min_silence_duration * self.sample_rate)
        
        best_start = None
        best_length = 0
        
        self.logger.debug("Starting adaptive noise profile extraction")
        
        i = 0
        while i < len(audio_data) - window_size:
            window = audio_data[i:i + window_size]
            rms = np.sqrt(np.mean(window**2))
            
            if rms < silence_threshold:
                # Found start of potential silence
                start = i
                while i < len(audio_data) - window_size:
                    window = audio_data[i:i + window_size]
                    rms = np.sqrt(np.mean(window**2))
                    if rms >= silence_threshold:
                        break
                    i += stride
                
                end = i
                length = end - start
                
                if length > best_length and length >= min_samples:
                    best_start = start
                    best_length = length
                    self.logger.debug(f"Found better silence segment: {start}-{end} ({length} samples)")
            else:
                i += stride
        
        if best_start is not None:
            noise_profile = audio_data[best_start:best_start + best_length]
            metadata = {
                "method": "adaptive",
                "start_sample": best_start,
                "end_sample": best_start + best_length,
                "duration": best_length / self.sample_rate,
                "silence_threshold": silence_threshold,
                "min_silence_duration": min_silence_duration,
                "sample_rate": self.sample_rate
            }
            
            self.logger.info(f"Extracted adaptive noise profile: {best_length} samples")
            return noise_profile, metadata
        else:
            raise ValueError(
                "Could not find a suitable low-energy segment for adaptive noise profiling. "
                "Try adjusting silence_threshold or min_silence_duration parameters."
            )