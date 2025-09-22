# Legacy Code

This directory contains the original code files before the package restructure:

- `anc_with_noise_profile_realtime.py` - Original real-time processing script
- `anc_with_noise_profile.ipynb` - Original Jupyter notebook for file processing  
- `anc_with_noise_profile_realtime.ipynb` - Original Jupyter notebook for real-time processing

These files are preserved for reference but should not be used in production. 
Please use the new package API instead.

## Migration Guide

### Old Script Usage
```python
# Old way (legacy)
from anc_with_noise_profile_realtime import reduce_noise_streaming

result = reduce_noise_streaming(
    input_source="file",
    input_file="input.wav", 
    output_file="output.wav",
    noise_profile_file="first_0.5"
)
```

### New Package Usage
```python
# New way (recommended)
from anc_noise_profiling import NoiseReductionProcessor

processor = NoiseReductionProcessor()
result = processor.process_file(
    input_file="input.wav",
    output_file="output.wav", 
    noise_profile_method="first_0.5"
)
```

The new package provides the same functionality with better error handling, logging, type hints, and a cleaner API.