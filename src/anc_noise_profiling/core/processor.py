"""Core noise reduction processing functionality."""

import logging
import queue
import threading
import time
from typing import Optional, Union, List, Dict, Any
from pathlib import Path
import numpy as np
import sounddevice as sd
import noisereduce as nr

from ..io.audio_handler import AudioHandler
from ..profiling.extractor import NoiseProfileExtractor


class NoiseReductionProcessor:
    """Main processor for active noise cancellation with noise profiling."""
    
    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_duration: float = 0.5,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the noise reduction processor.
        
        Args:
            sample_rate: Sample rate for audio processing
            chunk_duration: Duration of processing chunks in seconds
            logger: Optional logger instance
        """
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize components
        self.audio_handler = AudioHandler(sample_rate)
        self.profile_extractor = NoiseProfileExtractor(sample_rate)
        
        # Processing state
        self.output_audio = []
        self.raw_audio = []
        self.stream_queue = queue.Queue()
        self.noise_profile = None
        self.processing_metadata = {}
    
    def process_file(
        self,
        input_file: Union[str, Path],
        output_file: Union[str, Path],
        noise_profile_method: str = "first_0.5",
        silence_threshold: float = 0.01,
        min_silence_duration: float = 0.3,
        save_raw_audio: bool = False,
        duration: Optional[float] = None
    ) -> Dict[str, Any]:
        """Process an audio file for noise reduction.
        
        Args:
            input_file: Path to input audio file
            output_file: Path to save processed audio
            noise_profile_method: Method for extracting noise profile
            silence_threshold: RMS threshold for adaptive profiling
            min_silence_duration: Minimum silence duration for adaptive profiling
            save_raw_audio: Whether to save the original audio
            duration: Maximum duration to process (None for full file)
            
        Returns:
            Dictionary with processing results and metadata
        """
        self.logger.info(f"Starting file processing: {input_file} -> {output_file}")
        
        # Load input audio
        data, rate = self.audio_handler.load_audio_file(input_file)
        self.sample_rate = rate  # Use file's sample rate
        
        # Limit duration if specified
        if duration is not None:
            max_samples = int(duration * rate)
            data = data[:max_samples]
            self.logger.info(f"Limited processing to {duration}s ({max_samples} samples)")
        
        # Extract noise profile
        self.noise_profile, profile_metadata = self.profile_extractor.extract_profile(
            data, noise_profile_method, silence_threshold, min_silence_duration
        )
        
        # Process audio in chunks
        self.output_audio = []
        self.raw_audio = []
        
        chunk_count = 0
        for chunk in self.audio_handler.create_audio_chunks(data, self.chunk_duration, rate):
            reduced_chunk = nr.reduce_noise(y=chunk, y_noise=self.noise_profile, sr=rate)
            self.output_audio.extend(reduced_chunk)
            self.raw_audio.extend(chunk)
            chunk_count += 1
        
        # Save results
        final_audio = np.array(self.output_audio)
        self.audio_handler.save_audio_file(final_audio, output_file, rate)
        
        if save_raw_audio:
            raw_output_path = Path(output_file).with_suffix(".raw.wav")
            self.audio_handler.save_audio_file(np.array(self.raw_audio), raw_output_path, rate)
        
        # Compile metadata
        self.processing_metadata = {
            "input_file": str(input_file),
            "output_file": str(output_file),
            "input_duration": len(data) / rate,
            "output_duration": len(final_audio) / rate,
            "chunks_processed": chunk_count,
            "sample_rate": rate,
            "noise_profile": profile_metadata,
            "parameters": {
                "noise_profile_method": noise_profile_method,
                "silence_threshold": silence_threshold,
                "min_silence_duration": min_silence_duration,
                "chunk_duration": self.chunk_duration
            }
        }
        
        self.logger.info(f"File processing completed: {chunk_count} chunks")
        return self.processing_metadata
    
    def process_microphone(
        self,
        output_file: Optional[Union[str, Path]] = None,
        noise_profile_method: str = "first_0.5",
        output_mode: str = "file",
        save_raw_audio: bool = False,
        device: Optional[int] = None,
        duration: Optional[float] = None
    ) -> Optional[queue.Queue]:
        """Process audio from microphone in real-time.
        
        Args:
            output_file: Path to save processed audio (if output_mode includes 'file')
            noise_profile_method: Method for noise profiling (typically "first_X")
            output_mode: Output mode ("file", "stream", or "stream+file")
            save_raw_audio: Whether to save raw audio
            device: Audio device index (None for default)
            duration: Recording duration in seconds (None for indefinite)
            
        Returns:
            Stream queue if output_mode includes 'stream', None otherwise
        """
        self.logger.info(f"Starting microphone processing (mode: {output_mode})")
        
        # Validate audio device
        if not self.audio_handler.validate_audio_device(device):
            raise ValueError(f"Invalid audio device: {device}")
        
        # Initialize processing state
        self.output_audio = []
        self.raw_audio = []
        self.stream_queue = queue.Queue()
        self.noise_profile = None
        recorded_samples = 0
        stop_flag = False
        
        # Setup playback thread if streaming
        playback_thread = None
        if "stream" in output_mode:
            playback_thread = self.audio_handler.setup_audio_playback(self.stream_queue)
            playback_thread.start()
            self.logger.info("Started audio playback for streaming")
        
        def audio_callback(indata, frames, t, status):
            """Callback for processing incoming audio data."""
            nonlocal recorded_samples, stop_flag
            
            if status:
                self.logger.warning(f"Audio callback status: {status}")
            
            chunk = indata[:frames, 0]  # Get mono channel
            self.raw_audio.extend(chunk)
            
            # Extract noise profile from initial audio if not yet available
            if self.noise_profile is None:
                profile_duration = self._parse_profile_duration(noise_profile_method)
                profile_samples = int(profile_duration * self.sample_rate)
                
                if len(self.raw_audio) >= profile_samples:
                    self.noise_profile = np.array(self.raw_audio[:profile_samples])
                    self.logger.info(f"Extracted noise profile from first {profile_duration}s")
            
            # Apply noise reduction if profile is available
            if self.noise_profile is not None:
                reduced_chunk = nr.reduce_noise(y=chunk, y_noise=self.noise_profile, sr=self.sample_rate)
            else:
                reduced_chunk = chunk  # Pass through until profile is ready
            
            # Handle output based on mode
            if "stream" in output_mode:
                self.stream_queue.put(reduced_chunk)
            if "file" in output_mode:
                self.output_audio.extend(reduced_chunk)
            
            # Check for duration limit
            recorded_samples += frames
            if duration is not None and recorded_samples >= int(duration * self.sample_rate):
                stop_flag = True
                raise sd.CallbackStop()
        
        # Start recording
        chunk_samples = int(self.chunk_duration * self.sample_rate)
        with self.audio_handler.setup_microphone_stream(audio_callback, self.chunk_duration, device):
            try:
                duration_msg = f" for {duration}s" if duration else " indefinitely"
                self.logger.info(f"Recording{duration_msg} (Ctrl+C to stop)")
                
                if duration is not None:
                    sd.sleep(int(duration * 1000))
                else:
                    while not stop_flag:
                        time.sleep(0.1)
                        
            except KeyboardInterrupt:
                self.logger.info("Recording stopped by user")
                stop_flag = True
        
        # Stop playback thread
        if playback_thread:
            self.stream_queue.put(None)  # Sentinel to stop playback
            playback_thread.join(timeout=1.0)
        
        # Save file output if requested
        if "file" in output_mode and output_file:
            final_audio = np.array(self.output_audio)
            self.audio_handler.save_audio_file(final_audio, output_file, self.sample_rate)
            
            if save_raw_audio:
                raw_output_path = Path(output_file).with_suffix(".raw.wav")
                self.audio_handler.save_audio_file(np.array(self.raw_audio), raw_output_path, self.sample_rate)
        
        self.logger.info("Microphone processing completed")
        return self.stream_queue if "stream" in output_mode else None
    
    def _parse_profile_duration(self, method: str) -> float:
        """Parse duration from profile method string."""
        if method.startswith("first_") or method.startswith("last_"):
            try:
                return float(method.split("_")[1])
            except (IndexError, ValueError):
                return 0.5  # Default fallback
        return 0.5  # Default for other methods
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get statistics about the last processing operation."""
        if not self.processing_metadata:
            return {"status": "No processing completed yet"}
        
        return {
            "input_duration": self.processing_metadata.get("input_duration", 0),
            "output_duration": self.processing_metadata.get("output_duration", 0),
            "chunks_processed": self.processing_metadata.get("chunks_processed", 0),
            "sample_rate": self.processing_metadata.get("sample_rate", self.sample_rate),
            "noise_profile_info": self.processing_metadata.get("noise_profile", {}),
            "parameters": self.processing_metadata.get("parameters", {})
        }