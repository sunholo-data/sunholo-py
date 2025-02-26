# Sunholo-py Development Guide

## Build & Test Commands
```bash
# Install package in dev mode
pip install -e ".[all]"  # or specific features: ".[test,gcp,langchain]"

# Run all tests
pytest tests

# Run a specific test file
pytest tests/test_config.py

# Run a specific test function
pytest tests/test_config.py::test_load_config

# Run tests with coverage
pytest --cov=src/sunholo tests/
```

## Code Style
- **Imports**: Standard lib → Third-party → Local modules; group by category with blank lines
- **Typing**: Use type hints for function parameters and return values
- **Docstrings**: Google style docstrings with Args, Returns, Examples
- **Error handling**: Use try/except blocks with specific exceptions; log errors
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Structure**: Keep functions focused; follow single responsibility principle
- **Logging**: Use the custom logging module (from sunholo.custom_logging import log)

## License Header
All files should include the Apache 2.0 license header