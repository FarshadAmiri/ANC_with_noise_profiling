# ANC with Noise Profiling

A Python script for Active Noise Cancellation (ANC) that works both in real-time and with audio files. The key feature is automatic noise profile extraction from the input audio itself, eliminating the need for separate noise samples. This is a single file (`anc_stable_version.py`) containing the `reduce_noise_streaming()` function for both real-time microphone processing and file-based noise reduction.

## Features

- **File-based processing**: Clean audio files using various noise profile extraction methods
- **Real-time processing**: Live noise reduction with microphone input and audio streaming  
- **Automatic noise profiling**: Extract noise profiles from the audio itself using:
  - First/last N seconds of audio
  - Adaptive silence detection 
  - External noise files
- **Flexible output modes**: File saving, real-time streaming, or both
- **Single function interface**: Simple `reduce_noise_streaming()` function handles all use cases
- **Configurable parameters**: Extensive customization options
- **Visualization support**: Optional waveform plotting with noise profile highlights

## Installation

### Clone and setup
```bash
git clone https://github.com/FarshadAmiri/ANC_with_noise_profiling.git
cd ANC_with_noise_profiling
pip install -r requirements.txt
```

### Dependencies
- Python 3.8+
- numpy>=1.20.0
- soundfile>=0.10.0  
- sounddevice>=0.4.0
- noisereduce>=2.0.0
- matplotlib>=3.3.0

## Quick Start

### Python Usage

#### File-based noise reduction
```python
from anc_stable_version import reduce_noise_streaming

# Process a file using first 0.5 seconds as noise profile
result = reduce_noise_streaming(
    input_source="file",
    input_path="noisy_audio.wav", 
    output_path="clean_audio.wav",
    output_mode="file",
    noise_profile_mode="first_0.5"
)

# Use adaptive noise detection
result = reduce_noise_streaming(
    input_source="file",
    input_path="noisy_audio.wav",
    output_path="clean_audio.wav", 
    output_mode="file",
    noise_profile_mode="adaptive"
)

# Use external noise file
result = reduce_noise_streaming(
    input_source="file",
    input_path="noisy_audio.wav",
    output_path="clean_audio.wav",
    output_mode="file", 
    noise_profile_mode="noise_sample.wav"
)
```

#### Real-time processing
```python
from anc_stable_version import reduce_noise_streaming

# Real-time microphone processing with file output
result = reduce_noise_streaming(
    input_source="mic",
    output_path="live_recording.wav",
    output_mode="stream+file",
    noise_profile_mode="adaptive",
    duration=30  # Record for 30 seconds
)

# Process file with real-time streaming playback
result = reduce_noise_streaming(
    input_source="file",
    input_path="input.wav",
    output_mode="stream"
)
```

#### Advanced configuration
```python
from anc_stable_version import reduce_noise_streaming

# Advanced settings with visualization
result = reduce_noise_streaming(
    input_source="file",
    input_path="input.wav",
    output_path="output.wav",
    output_mode="stream+file",
    noise_profile_mode="adaptive",
    noise_amp_threshold=0.02,
    min_noise_duration=0.5,
    chunk_duration=2.0,
    save_raw_audio=True,
    visualization=True,
    plot_path="analysis.png"
)
```


## Noise Profile Methods

### Time-based extraction
- `"first_X"`: Use first X seconds (e.g., `"first_0.5"`, `"first_2.0"`)
- `"last_X"`: Use last X seconds (e.g., `"last_1.0"`)

### Adaptive detection  
- `"adaptive"`: Automatically find silent regions using RMS energy analysis
- Configurable silence threshold and minimum duration
- Continuously updates noise profile in real-time mode every few chunks
- Falls back to previous profile if no suitable region found

### External noise file
- Provide path to separate noise sample file
- Supports all audio formats compatible with soundfile

## Configuration Options

### Function Parameters
- `input_source`: "file" or "mic" - Input source selection
- `input_path`: Path to input audio file (required when input_source="file")
- `output_path`: Path for output audio file (optional)
- `output_mode`: "file", "stream", or "stream+file" - Output mode
- `noise_profile_mode`: Noise profile method (default: "adaptive")
- `noise_amp_threshold`: RMS threshold for silence detection (default: 0.025)
- `min_noise_duration`: Minimum silence duration in seconds (default: 0.2)
- `chunk_duration`: Processing chunk size in seconds (default: 2.5)
- `save_raw_audio`: Save original audio alongside processed (default: False)  
- `visualization`: Show waveform plots (default: False)
- `plot_path`: Path to save plot image (optional)
- `device`: Audio device ID for microphone input (default: None)
- `duration`: Recording duration in seconds, None for unlimited (default: None)
- `adaptive_refresh_chunks`: Chunks between adaptive profile updates (default: 4)

## Usage Examples

### Simple file processing
```python
# Import the function
from anc_stable_version import reduce_noise_streaming

# Basic file denoising
reduce_noise_streaming(
    input_source="file",
    input_path="noisy_file.wav",
    output_path="clean_file.wav"
)
```

### Real-time microphone processing
```python
# Record from microphone with real-time playback and file saving
reduce_noise_streaming(
    input_source="mic",
    output_path="recording.wav", 
    output_mode="stream+file",
    duration=60  # Record for 1 minute
)
```

### Legacy notebooks
The original Jupyter notebooks are preserved for reference:
- `anc_with_noise_profile.ipynb`: Original file-based implementation
- `anc_with_noise_profile_realtime.ipynb`: Original real-time implementation

## API Reference

### Main Function

#### `reduce_noise_streaming(input_source="mic", input_path=None, output_mode="stream+file", output_path=None, ...)`
Noise reduction function supporting both streaming and file processing modes.

**Key Parameters:**
- `input_source` (str): "file" or "mic" - Input source
- `input_path` (str, optional): Input file path (required if input_source="file")
- `output_path` (str, optional): Output file path
- `output_mode` (str): "file", "stream", or "stream+file" - Output mode
- `noise_profile_mode` (str): Noise profile method - "adaptive", "first_X", "last_X", or file path
- `noise_amp_threshold` (float): RMS threshold for silence detection (default: 0.025)
- `min_noise_duration` (float): Minimum silence duration in seconds (default: 0.2)
- `chunk_duration` (float): Processing chunk size in seconds (default: 2.5)
- `save_raw_audio` (bool): Save raw audio alongside processed (default: False)
- `visualization` (bool): Show waveform plots (default: False)
- `plot_path` (str, optional): Path to save visualization plot
- `device` (int, optional): Audio device ID for microphone
- `duration` (float, optional): Recording duration in seconds, None for unlimited
- `adaptive_refresh_chunks` (int): Chunks between adaptive profile updates (default: 4)

**Returns:** `queue.Queue` or `None` - Stream queue for real-time output (if output_mode includes "stream")

## Development

### Setting up development environment
```bash
git clone https://github.com/FarshadAmiri/ANC_with_noise_profiling.git
cd ANC_with_noise_profiling
pip install -r requirements.txt
```

### Testing the function
```python
# Test with a simple example
from anc_stable_version import reduce_noise_streaming

# Test microphone input (requires audio hardware)
reduce_noise_streaming(
    input_source="mic",
    output_path="test_output.wav",
    duration=5,  # 5 second test
    visualization=True
)
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## Changelog

### Current Version
- Simplified to single file structure (`anc_stable_version.py`)
- Single function `reduce_noise_streaming()` handles both file and real-time processing
- Adaptive noise profiling with continuous updates in real-time mode
- Comprehensive parameter configuration
- Optional visualization with noise profile highlighting  
- Support for various output modes (file, stream, both)

## Acknowledgments

- Built on top of the excellent `noisereduce` library
- Uses `soundfile` and `sounddevice` for audio I/O