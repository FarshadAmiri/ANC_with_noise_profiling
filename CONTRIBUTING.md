## Contributing to ANC Noise Profiling

We welcome contributions to make this project better! Here's how you can help:

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YourUsername/ANC_with_noise_profiling.git
   cd ANC_with_noise_profiling
   ```

2. **Set up development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

### Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following the existing patterns
   - Add type hints for all new functions
   - Include docstrings for all public functions
   - Add tests for new functionality

3. **Run tests and linting**
   ```bash
   # Run tests
   pytest tests/ -v
   
   # Check code formatting
   black src/ tests/
   isort src/ tests/
   
   # Lint code
   flake8 src/ tests/
   
   # Type checking
   mypy src/
   ```

4. **Commit and push**
   ```bash
   git add .
   git commit -m "Add your descriptive commit message"
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**

### Code Standards

- **Python Version**: Support Python 3.8+
- **Code Style**: Use Black for formatting (88 character line length)
- **Import Sorting**: Use isort with Black profile
- **Type Hints**: Add type hints for all function parameters and return values
- **Docstrings**: Use Google-style docstrings
- **Testing**: Write tests for all new functionality using pytest

### Project Structure

```
src/anc_noise_profiling/
├── __init__.py          # Main package exports
├── core/                # Core processing functionality
├── io/                  # Audio input/output handling
├── profiling/           # Noise profile extraction
├── utils/               # Utilities (config, logging)
└── cli/                 # Command-line interface

tests/                   # Test files
examples/                # Usage examples
legacy/                  # Original code (preserved)
```

### Types of Contributions

**🐛 Bug Reports**
- Use the GitHub issue template
- Include minimal reproduction steps
- Specify your environment (OS, Python version, dependencies)

**✨ Feature Requests**
- Describe the use case clearly
- Explain how it fits with existing functionality
- Consider if it could be implemented as a plugin

**📝 Documentation**
- Improve README or docstrings
- Add usage examples
- Fix typos or unclear explanations

**🔧 Code Contributions**
- Bug fixes
- Performance improvements
- New noise profiling methods
- Audio format support
- CLI enhancements

### Testing Guidelines

- Write unit tests for all new functions
- Include integration tests for end-to-end workflows
- Test edge cases and error conditions
- Ensure tests run quickly (mock external dependencies)
- Aim for >90% code coverage

Example test structure:
```python
def test_noise_profile_extraction():
    """Test noise profile extraction with known audio."""
    # Create test audio
    audio_data = create_test_audio()
    
    # Test extraction
    extractor = NoiseProfileExtractor(sample_rate=16000)
    profile, metadata = extractor.extract_profile(audio_data, "first_0.5")
    
    # Assertions
    assert len(profile) == 8000  # 0.5s * 16000 Hz
    assert metadata["method"] == "first_0.5"
    assert metadata["duration"] == 0.5
```

### Performance Considerations

- Keep memory usage reasonable for large audio files
- Consider chunk-based processing for streaming
- Profile performance-critical sections
- Document time complexity for algorithms

### Documentation Standards

- **README**: Keep examples up-to-date and working
- **Docstrings**: Include parameter types, descriptions, and examples
- **Comments**: Explain "why" not "what" for complex logic
- **Type Hints**: Use for all public APIs

### Release Process

1. Update version in `pyproject.toml` and `__init__.py`
2. Update CHANGELOG.md with new features and fixes
3. Create release tag: `git tag v1.x.x`
4. GitHub Actions will automatically build and test
5. Manual PyPI release (for maintainers)

### Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Chat**: Join our community discussions

Thank you for contributing to ANC Noise Profiling! 🎵