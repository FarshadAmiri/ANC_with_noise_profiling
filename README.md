# ANC with Noise Profiling

A professional Python package for Active Noise Cancellation (ANC) that works both in real-time and with audio files. The key feature is automatic noise profile extraction from the input audio itself, eliminating the need for separate noise samples.

## Features

- **File-based processing**: Clean audio files using various noise profile extraction methods
- **Real-time processing**: Live noise reduction with microphone input and audio streaming
- **Automatic noise profiling**: Extract noise profiles from the audio itself using:
  - First/last N seconds of audio
  - Adaptive silence detection 
  - External noise files
- **Flexible output modes**: File saving, real-time streaming, or both
- **Professional API**: Clean, documented interface with type hints
- **Command-line interface**: Easy-to-use CLI for common tasks
- **Configurable parameters**: Extensive customization options

## Installation

### From PyPI (recommended)
```bash
pip install anc-noise-profiling
```

### From source
```bash
git clone https://github.com/FarshadAmiri/ANC_with_noise_profiling.git
cd ANC_with_noise_profiling
pip install -r requirements.txt
pip install -e .
```

### Dependencies
- Python 3.8+
- numpy
- soundfile  
- sounddevice
- noisereduce
- matplotlib

## Quick Start

### Python API

#### File-based noise reduction
```python
from anc_noise_profiling import reduce_noise_file

# Use first 0.5 seconds as noise profile
reduce_noise_file("noisy_audio.wav", "clean_audio.wav", noise_profile="first_0.5")

# Use adaptive noise detection
reduce_noise_file("noisy_audio.wav", "clean_audio.wav", noise_profile="adaptive")

# Use external noise file
reduce_noise_file("noisy_audio.wav", "clean_audio.wav", noise_profile="noise_sample.wav")
```

#### Real-time processing
```python
from anc_noise_profiling import reduce_noise_realtime

# Real-time microphone processing with file output
reduce_noise_realtime(
    input_source="mic",
    output_file="live_recording.wav",
    output_mode="stream+file"
)

# Process file with real-time streaming
reduce_noise_realtime(
    input_source="file",
    input_file="input.wav", 
    output_mode="stream"
)
```

#### Advanced configuration
```python
from anc_noise_profiling import NoiseReductionConfig, reduce_noise_file

config = NoiseReductionConfig(
    noise_profile="adaptive",
    silence_threshold=0.02,
    min_silence_duration=0.5,
    visualization=True,
    save_raw_audio=True
)

reduce_noise_file("input.wav", "output.wav", config=config)
```


## Noise Profile Methods

### Time-based extraction
- `"first_X"`: Use first X seconds (e.g., `"first_0.5"`, `"first_2.0"`)
- `"last_X"`: Use last X seconds (e.g., `"last_1.0"`)

### Adaptive detection
- `"adaptive"`: Automatically find silent regions using RMS energy analysis
- Configurable silence threshold and minimum duration
- Falls back to first 0.5 seconds if no suitable region found

### External noise file
- Provide path to separate noise sample file
- Supports all audio formats compatible with soundfile

## Configuration Options

### NoiseReductionConfig parameters
- `noise_profile`: Noise profile specification (default: "first_0.5")
- `silence_threshold`: RMS threshold for silence detection (default: 0.01)
- `min_silence_duration`: Minimum silence duration in seconds (default: 0.3)
- `chunk_duration`: Processing chunk size in seconds (default: 0.5)
- `sample_rate`: Audio sample rate (default: 16000)
- `output_mode`: Output mode - "file", "stream", or "stream+file" (default: "file")
- `save_raw_audio`: Save original audio alongside processed (default: False)
- `visualization`: Show waveform plots (default: False)
- `device`: Audio device ID for microphone input (default: None)
- `duration`: Recording duration in seconds, None for unlimited (default: None)

## Examples

### Example scripts
See the `examples/` directory for comprehensive usage examples:

- `examples/file_processing_example.py`: File-based noise reduction examples
- `examples/realtime_example.py`: Real-time processing examples  
- `examples/advanced_config_example.py`: Advanced configuration examples
- `examples/cli_examples.sh`: Command-line usage examples

### Jupyter notebooks (legacy)
The original Jupyter notebooks are preserved for reference:
- `anc_with_noise_profile.ipynb`: Original file-based implementation
- `anc_with_noise_profile_realtime.ipynb`: Original real-time implementation

## API Reference

### Core Functions

#### `reduce_noise_file(input_file, output_file, noise_profile="first_0.5", config=None, **kwargs)`
Process audio file with noise reduction.

**Parameters:**
- `input_file` (str): Path to input audio file
- `output_file` (str): Path for output audio file  
- `noise_profile` (str): Noise profile specification
- `config` (NoiseReductionConfig, optional): Configuration object
- Additional keyword arguments override config parameters

**Returns:** str - Path to output file

#### `reduce_noise_realtime(input_source="file", input_file=None, output_file=None, config=None, **kwargs)`
Real-time noise reduction processing.

**Parameters:**
- `input_source` (str): "file" or "mic" 
- `input_file` (str, optional): Input file path (required if input_source="file")
- `output_file` (str, optional): Output file path
- `config` (NoiseReductionConfig, optional): Configuration object
- Additional keyword arguments override config parameters

**Returns:** queue.Queue or None - Stream queue for real-time output

## Development

### Setting up development environment
```bash
git clone https://github.com/FarshadAmiri/ANC_with_noise_profiling.git
cd ANC_with_noise_profiling
pip install -r requirements.txt
pip install -e ".[dev]"
```

### Running tests
```bash
pytest tests/
```

### Code formatting
```bash
black anc_noise_profiling/
flake8 anc_noise_profiling/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## Changelog

### Version 1.0.0
- Initial professional package release
- Refactored code into modular structure
- Added comprehensive API and CLI
- Added configuration management
- Added proper documentation and examples
- Maintained backward compatibility with original scripts

## Acknowledgments

- Built on top of the excellent `noisereduce` library
- Uses `soundfile` and `sounddevice` for audio I/O