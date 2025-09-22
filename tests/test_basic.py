"""Basic tests for the ANC noise profiling package."""

import tempfile
import numpy as np
import pytest
from pathlib import Path

from anc_noise_profiling.profiling.extractor import NoiseProfileExtractor
from anc_noise_profiling.io.audio_handler import AudioHandler
from anc_noise_profiling.utils.config import Config


class TestNoiseProfileExtractor:
    """Test noise profile extraction functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = NoiseProfileExtractor(sample_rate=16000)
        # Create a simple test audio signal
        self.sample_rate = 16000
        duration = 2.0  # 2 seconds
        t = np.linspace(0, duration, int(duration * self.sample_rate))
        # First 0.5s: low noise, then signal + noise
        self.test_audio = np.concatenate([
            0.01 * np.random.randn(int(0.5 * self.sample_rate)),  # Low noise
            0.5 * np.sin(2 * np.pi * 440 * t[int(0.5 * self.sample_rate):]) + 
            0.1 * np.random.randn(len(t) - int(0.5 * self.sample_rate))  # Signal + noise
        ])
    
    def test_temporal_extraction_first(self):
        """Test first_X temporal extraction."""
        profile, metadata = self.extractor.extract_profile(
            self.test_audio, method="first_0.5"
        )
        
        assert len(profile) == int(0.5 * self.sample_rate)
        assert metadata["method"] == "first_0.5"
        assert metadata["start_sample"] == 0
        assert abs(metadata["duration"] - 0.5) < 0.01
    
    def test_temporal_extraction_last(self):
        """Test last_X temporal extraction."""
        profile, metadata = self.extractor.extract_profile(
            self.test_audio, method="last_0.3"
        )
        
        expected_samples = int(0.3 * self.sample_rate)
        assert len(profile) == expected_samples
        assert metadata["method"] == "last_0.3"
        assert metadata["start_sample"] == len(self.test_audio) - expected_samples
    
    def test_adaptive_extraction(self):
        """Test adaptive noise profile extraction."""
        profile, metadata = self.extractor.extract_profile(
            self.test_audio, 
            method="adaptive",
            silence_threshold=0.05,
            min_silence_duration=0.1
        )
        
        assert len(profile) > 0
        assert metadata["method"] == "adaptive"
        assert "start_sample" in metadata
        assert "silence_threshold" in metadata
    
    def test_invalid_method(self):
        """Test error handling for invalid methods."""
        with pytest.raises(ValueError):
            self.extractor.extract_profile(self.test_audio, method="invalid_method")


class TestAudioHandler:
    """Test audio I/O functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.handler = AudioHandler(sample_rate=16000)
        self.test_audio = np.random.randn(16000)  # 1 second of noise
    
    def test_save_and_load_audio(self):
        """Test saving and loading audio files."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            # Save audio
            self.handler.save_audio_file(self.test_audio, temp_path, 16000)
            assert temp_path.exists()
            
            # Load audio
            loaded_audio, sample_rate = self.handler.load_audio_file(temp_path)
            
            assert sample_rate == 16000
            assert len(loaded_audio) == len(self.test_audio)
            np.testing.assert_allclose(loaded_audio, self.test_audio, rtol=1e-3)
            
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    def test_audio_chunks(self):
        """Test audio chunk creation."""
        chunks = list(self.handler.create_audio_chunks(
            self.test_audio, chunk_duration=0.5, sample_rate=16000
        ))
        
        expected_chunk_size = int(0.5 * 16000)
        assert len(chunks) == 2  # 1 second / 0.5 second chunks
        assert len(chunks[0]) == expected_chunk_size
        assert len(chunks[1]) == expected_chunk_size


class TestConfig:
    """Test configuration management."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        
        assert config.get("audio.sample_rate") == 16000
        assert config.get("noise_profiling.method") == "first_0.5"
        assert config.get("logging.level") == "INFO"
    
    def test_config_get_set(self):
        """Test getting and setting configuration values."""
        config = Config()
        
        # Test nested key setting
        config.set("audio.sample_rate", 22050)
        assert config.get("audio.sample_rate") == 22050
        
        # Test new key creation
        config.set("new.nested.key", "value")
        assert config.get("new.nested.key") == "value"
    
    def test_config_sections(self):
        """Test configuration section getters."""
        config = Config()
        
        audio_config = config.get_audio_config()
        assert "sample_rate" in audio_config
        assert "chunk_duration" in audio_config
        
        noise_config = config.get_noise_profiling_config()
        assert "method" in noise_config
        assert "silence_threshold" in noise_config