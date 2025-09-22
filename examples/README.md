# Examples

This directory contains comprehensive examples demonstrating how to use the ANC Noise Profiling package.

## Available Examples

### 🎵 Basic File Processing (`basic_file_processing.py`)
Demonstrates basic file processing with different noise profiling methods.
```bash
python examples/basic_file_processing.py
```

### ⚙️ Advanced Configuration (`advanced_config.py`)
Shows how to use configuration files and customize settings.
```bash
python examples/advanced_config.py
```

### 🎛️ Custom Noise Profiles (`custom_noise_profiles.py`)
Demonstrates custom noise profile creation and comparison.
```bash
python examples/custom_noise_profiles.py
```

### 📄 Configuration File (`config_example.yaml`)
Example configuration file showing all available options.

## Running Examples

1. **Install the package first:**
   ```bash
   pip install -e .
   ```

2. **Create test audio (optional):**
   The `custom_noise_profiles.py` example creates synthetic audio for demonstration.

3. **Run any example:**
   ```bash
   cd ANC_with_noise_profiling
   python examples/basic_file_processing.py
   ```

## Example Output Structure

Examples will create an `output/` directory with processed files:
```
output/
├── clean_first_0.5_input.wav
├── clean_adaptive_input.wav
├── noise_profiles/
├── config_modified.yaml
└── synthetic_noisy_audio.wav
```

## CLI Examples

You can also use the command-line interface directly:

```bash
# Process a file with different methods
anc-noise-profiling process-file input.wav output_temporal.wav --profile-method first_1.0
anc-noise-profiling process-file input.wav output_adaptive.wav --profile-method adaptive

# Record from microphone
anc-noise-profiling record microphone_recording.wav --duration 30

# Real-time processing with playback
anc-noise-profiling record --output-mode stream+file live_output.wav

# Use configuration file
anc-noise-profiling --config examples/config_example.yaml process-file input.wav output.wav
```

## Need Help?

- Check the main README.md for complete API documentation
- Look at the docstrings in the source code
- Run `anc-noise-profiling --help` for CLI usage
- Open an issue on GitHub for questions