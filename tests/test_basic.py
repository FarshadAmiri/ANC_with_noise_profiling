"""
Basic tests for ANC with Noise Profiling package

These tests verify the package structure and basic functionality.
Note: Full testing requires audio files and may need audio hardware.
"""

import pytest
import numpy as np
import tempfile
import os
from unittest.mock import patch, MagicMock

def test_package_imports():
    """Test that main package imports work correctly."""
    try:
        import anc_noise_profiling
        assert hasattr(anc_noise_profiling, 'reduce_noise_file')
        assert hasattr(anc_noise_profiling, 'reduce_noise_realtime') 
        assert hasattr(anc_noise_profiling, 'NoiseReductionConfig')
        assert hasattr(anc_noise_profiling, '__version__')
    except ImportError as e:
        pytest.fail(f"Package import failed: {e}")


def test_config_creation():
    """Test NoiseReductionConfig creation and validation."""
    from anc_noise_profiling import NoiseReductionConfig
    
    # Test default config
    config = NoiseReductionConfig()
    assert config.noise_profile == "first_0.5"
    assert config.silence_threshold == 0.01
    assert config.output_mode == "file"
    
    # Test custom config
    config = NoiseReductionConfig(
        noise_profile="adaptive",
        silence_threshold=0.02,
        output_mode="stream"
    )
    assert config.noise_profile == "adaptive"
    assert config.silence_threshold == 0.02
    assert config.output_mode == "stream"


def test_config_validation():
    """Test NoiseReductionConfig parameter validation."""
    from anc_noise_profiling import NoiseReductionConfig
    
    # Test invalid output_mode
    with pytest.raises(ValueError, match="output_mode must be"):
        NoiseReductionConfig(output_mode="invalid")
    
    # Test invalid silence_threshold
    with pytest.raises(ValueError, match="silence_threshold must be"):
        NoiseReductionConfig(silence_threshold=-0.1)
    
    with pytest.raises(ValueError, match="silence_threshold must be"):
        NoiseReductionConfig(silence_threshold=1.5)
    
    # Test invalid durations
    with pytest.raises(ValueError, match="min_silence_duration must be"):
        NoiseReductionConfig(min_silence_duration=-0.1)
    
    with pytest.raises(ValueError, match="chunk_duration must be"):
        NoiseReductionConfig(chunk_duration=0)


def test_audio_utils_imports():
    """Test that audio utility functions can be imported."""
    try:
        from anc_noise_profiling.core.audio_utils import (
            convert_to_mono, extract_noise_profile
        )
    except ImportError as e:
        pytest.fail(f"Audio utils import failed: {e}")


def test_convert_to_mono():
    """Test mono conversion function."""
    from anc_noise_profiling.core.audio_utils import convert_to_mono
    
    # Test stereo to mono conversion
    stereo_data = np.random.rand(1000, 2)
    mono_data = convert_to_mono(stereo_data)
    assert mono_data.shape == (1000,)
    assert np.allclose(mono_data, np.mean(stereo_data, axis=1))
    
    # Test already mono data
    mono_input = np.random.rand(1000)
    mono_output = convert_to_mono(mono_input)
    assert np.array_equal(mono_input, mono_output)


def test_noise_profile_extraction():
    """Test noise profile extraction with synthetic data."""
    from anc_noise_profiling.core.audio_utils import extract_noise_profile
    
    # Create synthetic audio data
    sample_rate = 16000
    duration = 2.0  # 2 seconds
    audio_data = np.random.rand(int(sample_rate * duration)) * 0.1
    
    # Test first_X extraction
    noise_profile, start, end = extract_noise_profile(
        audio_data, sample_rate, "first_0.5"
    )
    expected_samples = int(0.5 * sample_rate)
    assert len(noise_profile) == expected_samples
    assert start == 0
    assert end == expected_samples
    
    # Test last_X extraction  
    noise_profile, start, end = extract_noise_profile(
        audio_data, sample_rate, "last_0.5"
    )
    assert len(noise_profile) == expected_samples
    assert start == len(audio_data) - expected_samples
    assert end == len(audio_data)


def test_cli_parser():
    """Test command-line interface parser."""
    try:
        from anc_noise_profiling.cli.main import create_parser
        parser = create_parser()
        
        # Test file command parsing
        args = parser.parse_args(['file', 'input.wav', 'output.wav'])
        assert args.command == 'file'
        assert args.input_file == 'input.wav'
        assert args.output_file == 'output.wav'
        
        # Test realtime command parsing
        args = parser.parse_args(['realtime', '--input-source', 'mic'])
        assert args.command == 'realtime'
        assert args.input_source == 'mic'
        
    except ImportError as e:
        pytest.fail(f"CLI import failed: {e}")


@patch('anc_noise_profiling.core.audio_utils.load_audio')
@patch('anc_noise_profiling.core.audio_utils.save_audio')
@patch('noisereduce.reduce_noise')
def test_reduce_noise_file_mock(mock_nr, mock_save, mock_load):
    """Test reduce_noise_file with mocked dependencies."""
    from anc_noise_profiling import reduce_noise_file
    
    # Setup mocks
    sample_rate = 16000
    audio_data = np.random.rand(sample_rate)  # 1 second of audio
    
    mock_load.return_value = (audio_data, sample_rate)
    mock_nr.return_value = audio_data * 0.5  # Simulated noise reduction
    
    # Test function
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_in, \
         tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_out:
        
        try:
            result = reduce_noise_file(
                input_file=tmp_in.name,
                output_file=tmp_out.name,
                noise_profile="first_0.5"
            )
            
            assert result == tmp_out.name
            mock_load.assert_called_once()
            mock_save.assert_called_once()
            mock_nr.assert_called_once()
            
        finally:
            os.unlink(tmp_in.name)
            os.unlink(tmp_out.name)


def test_legacy_compatibility():
    """Test that legacy function names still work."""
    try:
        from anc_noise_profiling.core.noise_reduction import reduce_noise_with_profile
        from anc_noise_profiling.streaming.realtime import reduce_noise_streaming
        
        # These should be importable (actual testing would need audio files)
        assert callable(reduce_noise_with_profile)
        assert callable(reduce_noise_streaming)
        
    except ImportError as e:
        pytest.fail(f"Legacy function import failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__])