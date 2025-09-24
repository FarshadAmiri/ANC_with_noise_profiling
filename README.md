# ANC with Noise Profiling

A Python script for Active Noise Cancellation (ANC) that works both in real-time and with audio files. The key feature is automatic noise profile extraction from the input audio itself, eliminating the need for separate noise samples. This is a single file (`anc.py`) containing the `anc()` function for both real-time microphone processing and file-based noise reduction.

## Features

- **File-based processing**: Clean audio files using various noise profile extraction methods
- **Real-time processing**: Live noise reduction with microphone input and audio streaming  
- **Automatic noise profiling**: Extract noise profiles from the audio itself using:
  - First/last N seconds of audio
  - Adaptive silence detection 
  - External noise files
- **Flexible output modes**: File saving, real-time streaming, or both
- **Single function interface**: Simple `anc()` function handles all use cases
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
from anc import anc

# Process a file using first 0.5 seconds as noise profile
result = anc(
    input_source="file",
    input_path="noisy_audio.wav", 
    output_path="clean_audio.wav",
    output_mode="file",
    noise_profile_mode="adaptive"  # Recommended
)

# Noise profile modes:
noise_profile_mode = "adaptive"
noise_profile_mode = "noise_sample.wav"
noise_profile_mode = "first_{x}s" # x is a float number. first x seconds of the audio
noise_profile_mode =  "last_{x}s"  # x is a float number.  last x seconds of the audio
```

#### Real-time processing
```python
from anc import anc

# Real-time microphone processing with file output
result = anc(
    input_source="mic",
    output_path="live_recording.wav",
    output_mode="stream+file",
    noise_profile_mode="adaptive",
    duration=30  # Record for 30 seconds
)
```

#### Advanced configuration
```python
from anc import anc

# Advanced settings with visualization
result = anc(
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
from anc import anc

# Test microphone input (requires audio hardware)
anc(
    input_source="mic",
    output_path="test_output.wav",
    duration=5,  # 5 second test
    visualization=True
)
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## Acknowledgments

- Built on top of the excellent `noisereduce` library
- Uses `soundfile` and `sounddevice` for audio I/O