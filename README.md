# ANC with Noise Profiling

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Active Noise Cancellation with Noise Profiling** - A professional Python package for real-time and file-based audio noise reduction that extracts noise profiles directly from the input audio itself.

## Features

- 🎯 **Smart Noise Profiling**: Automatically extract noise profiles from input audio using multiple methods
- 🎤 **Real-time Processing**: Live noise cancellation from microphone input with streaming output
- 📁 **File-based Processing**: Batch process audio files with high-quality noise reduction
- 🔧 **Flexible Configuration**: YAML/JSON configuration files and comprehensive CLI interface
- 📊 **Multiple Profile Methods**: First/last segment extraction, adaptive silence detection
- 🎵 **Format Support**: Support for WAV, MP3, FLAC, and other audio formats via soundfile
- 📝 **Professional Logging**: Structured logging with configurable levels
- 🧪 **Well Tested**: Comprehensive test suite and type hints throughout

## Installation

### From PyPI (when published)
```bash
pip install anc-noise-profiling
```

### From Source
```bash
git clone https://github.com/FarshadAmiri/ANC_with_noise_profiling.git
cd ANC_with_noise_profiling
pip install -e .
```

### Development Installation
```bash
git clone https://github.com/FarshadAmiri/ANC_with_noise_profiling.git
cd ANC_with_noise_profiling
pip install -e ".[dev]"
```

## Quick Start

### Command Line Interface

```bash
# Process an audio file (uses first 0.5 seconds as noise profile)
anc-noise-profiling process-file input.wav output.wav

# Use adaptive noise profiling (finds quietest segments)
anc-noise-profiling process-file input.wav output.wav --profile-method adaptive

# Record from microphone for 30 seconds
anc-noise-profiling record output.wav --duration 30

# Real-time processing with live playback
anc-noise-profiling record --output-mode stream+file output.wav

# List available audio devices
anc-noise-profiling list-devices
```

### Python API

```python
from anc_noise_profiling import NoiseReductionProcessor

# Initialize processor
processor = NoiseReductionProcessor(sample_rate=16000)

# Process a file
result = processor.process_file(
    input_file="noisy_audio.wav",
    output_file="clean_audio.wav",
    noise_profile_method="first_0.5"  # Use first 0.5 seconds as noise profile
)

# Real-time microphone processing
processor.process_microphone(
    output_file="live_recording.wav",
    output_mode="stream+file",  # Both live playback and file saving
    duration=60  # Record for 60 seconds
)
```

## Noise Profile Methods

The package supports several methods for extracting noise profiles:

### Temporal Methods
- **`first_X`**: Use the first X seconds of audio (e.g., `first_0.5`, `first_2.0`)
- **`last_X`**: Use the last X seconds of audio (e.g., `last_1.0`)

### Adaptive Method
- **`adaptive`**: Automatically find the quietest segment in the audio
  - Analyzes the entire audio file using sliding window RMS energy
  - Selects the longest segment below the silence threshold
  - Ideal when you don't know where the noise-only sections are

### External File
- **File path**: Use a separate noise profile file (e.g., `noise_sample.wav`)

## Configuration

### Configuration File
Create a `config.yaml` file for persistent settings:

```yaml
audio:
  sample_rate: 16000
  chunk_duration: 0.5
  device: null  # Use default device

noise_profiling:
  method: "first_0.5"
  silence_threshold: 0.01
  min_silence_duration: 0.3

processing:
  output_mode: "file"
  save_raw_audio: false
  visualization: false

logging:
  level: "INFO"
  include_timestamp: true

output:
  directory: "output"
  filename_template: "denoised_{timestamp}.wav"
```

Use the configuration file:
```bash
anc-noise-profiling --config config.yaml process-file input.wav output.wav
```

### Environment Variables
```bash
export ANC_LOG_LEVEL=DEBUG
export ANC_SAMPLE_RATE=22050
```

## Advanced Usage

### Batch Processing
```python
from pathlib import Path
from anc_noise_profiling import NoiseReductionProcessor

processor = NoiseReductionProcessor()

# Process multiple files
input_dir = Path("input_audio/")
output_dir = Path("output_audio/")

for audio_file in input_dir.glob("*.wav"):
    output_file = output_dir / f"clean_{audio_file.name}"
    processor.process_file(audio_file, output_file, noise_profile_method="adaptive")
```

### Custom Noise Profile
```python
import numpy as np
from anc_noise_profiling.profiling import NoiseProfileExtractor

# Extract custom noise profile
extractor = NoiseProfileExtractor(sample_rate=16000)
audio_data, _ = sf.read("input.wav")

# Use adaptive method with custom parameters
noise_profile, metadata = extractor.extract_profile(
    audio_data,
    method="adaptive",
    silence_threshold=0.005,  # More sensitive
    min_silence_duration=1.0   # Longer segments
)
```

## API Reference

### NoiseReductionProcessor

Main class for audio processing operations.

#### Methods

- **`process_file(input_file, output_file, **kwargs)`**: Process audio file
- **`process_microphone(output_file=None, **kwargs)`**: Real-time microphone processing
- **`get_processing_stats()`**: Get statistics from last operation

### NoiseProfileExtractor

Handles extraction of noise profiles from audio data.

#### Methods

- **`extract_profile(audio_data, method, **kwargs)`**: Extract noise profile

### AudioHandler

Manages audio input/output operations.

#### Methods

- **`load_audio_file(file_path)`**: Load audio from file
- **`save_audio_file(audio_data, file_path, sample_rate)`**: Save audio to file
- **`list_audio_devices()`**: List available audio devices

## Development

### Setup Development Environment
```bash
git clone https://github.com/FarshadAmiri/ANC_with_noise_profiling.git
cd ANC_with_noise_profiling
pip install -e ".[dev]"
pre-commit install
```

### Run Tests
```bash
pytest
pytest --cov=anc_noise_profiling  # With coverage
```

### Code Formatting
```bash
black src/ tests/
isort src/ tests/
flake8 src/ tests/
mypy src/
```

## Examples

See the `examples/` directory for:
- Basic file processing
- Real-time microphone processing
- Batch processing scripts
- Configuration examples
- Custom noise profile extraction

## Performance Tips

1. **Choose appropriate chunk duration**: Smaller chunks = lower latency, larger chunks = better quality
2. **Use appropriate sample rate**: 16kHz is sufficient for speech, 44.1kHz for music
3. **Adaptive profiling**: Best quality but slower, use temporal methods for speed
4. **Real-time processing**: Use `chunk_duration=0.1` for lower latency

## Troubleshooting

### Common Issues

**Audio device not found**:
```bash
anc-noise-profiling list-devices  # List available devices
```

**Poor noise reduction quality**:
- Try adaptive profiling method
- Adjust silence threshold
- Ensure noise profile represents actual noise

**Real-time latency too high**:
- Reduce chunk_duration
- Use lower sample rate
- Check audio device buffer settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built on top of the excellent [noisereduce](https://github.com/timsainb/noisereduce) library
- Uses [soundfile](https://github.com/bastibe/python-soundfile) for audio I/O
- Real-time audio processing powered by [sounddevice](https://github.com/spatialaudio/python-sounddevice)

## Changelog

### v1.0.0
- Initial release with complete package restructure
- Professional CLI interface
- Comprehensive API
- Configuration file support
- Real-time and file-based processing
- Multiple noise profiling methods