# Changelog

All notable changes to the ANC Noise Profiling project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-22

### Added
- Complete package restructure into professional Python package
- Modular architecture with separate modules for core processing, I/O, profiling, and utilities
- Professional command-line interface with comprehensive options
- Configuration file support (YAML/JSON) with environment variable integration
- Comprehensive logging system with configurable levels
- Type hints throughout the codebase for better IDE support
- Unit test suite using pytest with coverage reporting
- Multiple noise profiling methods:
  - Temporal extraction (first_X, last_X seconds)
  - Adaptive silence detection
  - External noise profile file support
- Real-time microphone processing with streaming output
- File-based batch processing capabilities
- Professional documentation with usage examples
- GitHub Actions CI/CD pipeline
- Development tools configuration (black, isort, flake8, mypy)

### Changed
- Transformed from standalone scripts to installable Python package
- Improved error handling with informative error messages
- Enhanced API design for better usability
- Moved original files to `legacy/` directory with migration guide

### Fixed
- Robust audio format handling for various input types
- Memory-efficient chunk-based processing for large files
- Proper cleanup of audio streams and resources

### Technical Details
- **Package Structure**: `src/anc_noise_profiling/` with proper module organization
- **Dependencies**: Pinned versions for stability, support for Python 3.8+
- **CLI Entry Point**: `anc-noise-profiling` command available after installation
- **Testing**: Comprehensive unit tests with pytest and coverage reporting
- **Documentation**: Professional README with examples and API documentation

## [0.1.0] - Legacy

### Initial Implementation
- Basic noise reduction script (`anc_with_noise_profile_realtime.py`)
- Jupyter notebook demonstrations
- Simple file and microphone processing
- First implementation of noise profile extraction