"""
DEPRECATED: This file has been replaced by the professional anc_noise_profiling package.

The original functionality is now available through:

1. Import the new package:
   from anc_noise_profiling import reduce_noise_realtime

2. Use the CLI tool:
   anc-noise-profiling realtime --input-source mic --output-file output.wav

3. For exact compatibility, use the legacy wrapper:
   from anc_noise_profiling.legacy import legacy_reduce_noise_streaming

This file remains for backward compatibility but will show deprecation warnings.
"""

import warnings
warnings.warn(
    "anc_with_noise_profile_realtime.py is deprecated. "
    "Use the anc_noise_profiling package instead. "
    "See README.md for migration instructions.",
    DeprecationWarning,
    stacklevel=2
)

# Import the legacy compatibility function
from anc_noise_profiling.legacy import legacy_reduce_noise_streaming as reduce_noise_streaming

# Example usage with new package (commented out to avoid execution)
if __name__ == "__main__":
    print("=" * 60)
    print("MIGRATION NOTICE")
    print("=" * 60)
    print("This script has been replaced by the anc_noise_profiling package.")
    print("")
    print("New usage options:")
    print("")
    print("1. Python API:")
    print("   from anc_noise_profiling import reduce_noise_realtime")
    print("   reduce_noise_realtime(input_source='mic', output_file='output.wav')")
    print("")
    print("2. Command Line:")
    print("   anc-noise-profiling realtime --input-source mic --output-file output.wav")
    print("")
    print("3. For examples, see:")
    print("   - examples/realtime_example.py")
    print("   - examples/cli_examples.sh")
    print("")
    print("4. Install the package:")
    print("   pip install -e .")
    print("")
    print("=" * 60)

# Original example (updated to use relative paths and be safer)
# Uncomment and modify these lines to test with your own files:

# import os
# 
# # Example with file input (safer than hardcoded Windows paths)
# input_path = "example_input.wav"  # Replace with your audio file
# output_path = "output_realtime.wav"
# 
# if os.path.exists(input_path):
#     print(f"Processing {input_path} -> {output_path}")
#     result = reduce_noise_streaming(
#         input_source="file",
#         input_file=input_path,
#         output_file=output_path,
#         noise_profile_file="first_0.5",
#         silence_threshold=0.01,
#         min_silence_duration=0.3,
#         output_mode="file",
#         chunk_duration=0.5,
#         save_raw_audio=False,
#         visualization=False,
#         device=None,
#         duration=None
#     )
#     print(f"✓ Processing completed: {output_path}")
# else:
#     print(f"⚠ Input file not found: {input_path}")
#     print("Please provide a valid audio file to test the functionality.")