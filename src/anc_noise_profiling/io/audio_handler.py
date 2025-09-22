"""Audio input/output handling for various sources."""

import logging
import queue
import threading
import time
from pathlib import Path
from typing import Optional, Union, Tuple, Generator
import numpy as np
import sounddevice as sd
import soundfile as sf


class AudioHandler:
    """Handles audio input/output from files and microphones."""
    
    def __init__(self, sample_rate: int = 16000):
        """Initialize the audio handler.
        
        Args:
            sample_rate: Default sample rate for audio processing
        """
        self.sample_rate = sample_rate
        self.logger = logging.getLogger(__name__)
    
    def load_audio_file(self, file_path: Union[str, Path]) -> Tuple[np.ndarray, int]:
        """Load audio from file and convert to mono if needed.
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Tuple of (audio_data, sample_rate)
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file can't be loaded
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        try:
            data, rate = sf.read(str(file_path))
            
            # Convert stereo to mono
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)
                self.logger.info("Converted stereo audio to mono")
            
            self.logger.info(f"Loaded audio file: {file_path} ({len(data)} samples, {rate} Hz)")
            return data, rate
            
        except Exception as e:
            raise ValueError(f"Failed to load audio file {file_path}: {e}")
    
    def save_audio_file(
        self,
        audio_data: np.ndarray,
        file_path: Union[str, Path],
        sample_rate: Optional[int] = None
    ) -> None:
        """Save audio data to file.
        
        Args:
            audio_data: Audio data to save
            file_path: Output file path
            sample_rate: Sample rate for output file
        """
        file_path = Path(file_path)
        rate = sample_rate or self.sample_rate
        
        try:
            # Ensure output directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            sf.write(str(file_path), audio_data, rate)
            self.logger.info(f"Saved audio to: {file_path}")
            
        except Exception as e:
            raise ValueError(f"Failed to save audio to {file_path}: {e}")
    
    def create_audio_chunks(
        self,
        audio_data: np.ndarray,
        chunk_duration: float,
        sample_rate: Optional[int] = None
    ) -> Generator[np.ndarray, None, None]:
        """Create chunks of audio data for processing.
        
        Args:
            audio_data: Input audio data
            chunk_duration: Duration of each chunk in seconds
            sample_rate: Sample rate for chunk calculation
            
        Yields:
            Audio chunks as numpy arrays
        """
        rate = sample_rate or self.sample_rate
        chunk_samples = int(chunk_duration * rate)
        
        for start in range(0, len(audio_data), chunk_samples):
            chunk = audio_data[start:start + chunk_samples]
            yield chunk
    
    def setup_microphone_stream(
        self,
        callback,
        chunk_duration: float = 0.5,
        device: Optional[int] = None
    ) -> sd.InputStream:
        """Set up microphone input stream.
        
        Args:
            callback: Callback function for processing audio chunks
            chunk_duration: Duration of each audio chunk in seconds
            device: Audio device index (None for default)
            
        Returns:
            Configured input stream
        """
        chunk_samples = int(chunk_duration * self.sample_rate)
        
        stream = sd.InputStream(
            callback=callback,
            channels=1,
            samplerate=self.sample_rate,
            blocksize=chunk_samples,
            dtype="float32",
            device=device
        )
        
        self.logger.info(f"Set up microphone stream: {self.sample_rate} Hz, {chunk_duration}s chunks")
        return stream
    
    def setup_audio_playback(self, audio_queue: queue.Queue) -> threading.Thread:
        """Set up audio playback thread for streaming output.
        
        Args:
            audio_queue: Queue containing audio chunks for playback
            
        Returns:
            Playback thread (not started)
        """
        def playback_worker():
            """Worker function for audio playback thread."""
            try:
                with sd.OutputStream(
                    channels=1,
                    samplerate=self.sample_rate,
                    dtype="float32"
                ) as out_stream:
                    self.logger.info("Started audio playback thread")
                    
                    while True:
                        try:
                            chunk = audio_queue.get(timeout=0.1)
                            if chunk is None:  # Sentinel value to stop
                                break
                            out_stream.write(chunk.astype(np.float32))
                        except queue.Empty:
                            continue
                        except Exception as e:
                            self.logger.error(f"Playback error: {e}")
                            break
                            
            except Exception as e:
                self.logger.error(f"Failed to start playback stream: {e}")
        
        thread = threading.Thread(target=playback_worker, daemon=True)
        return thread
    
    @staticmethod
    def list_audio_devices() -> None:
        """List available audio devices for debugging."""
        print("Available audio devices:")
        print(sd.query_devices())
    
    def validate_audio_device(self, device: Optional[int] = None) -> bool:
        """Validate that an audio device is available.
        
        Args:
            device: Device index to validate (None for default)
            
        Returns:
            True if device is valid, False otherwise
        """
        try:
            device_info = sd.query_devices(device)
            self.logger.info(f"Using audio device: {device_info['name']}")
            return True
        except Exception as e:
            self.logger.error(f"Invalid audio device {device}: {e}")
            return False