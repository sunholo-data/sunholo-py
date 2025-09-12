# Installing Sunholo with uv

## Local Development Installation

### 1. Install in Editable/Development Mode

From the sunholo-py directory:

```bash
# Install with all dependencies
uv pip install -e ".[all]"

# Or install with specific features
uv pip install -e ".[fastapi]"
uv pip install -e ".[gcp,langchain]"
uv pip install -e ".[test]"
```

The `-e` flag installs in "editable" mode, meaning changes to the source code are immediately reflected without reinstalling.

### 2. Install from Local Path

From any directory:

```bash
# Install from local path
uv pip install /path/to/sunholo-py

# With extras
uv pip install "/path/to/sunholo-py[fastapi]"
```

### 3. Install for Testing

```bash
# Install with test dependencies
uv pip install -e ".[test]"

# Run tests
uv run pytest tests/
```

## Available Extras

The package has several optional dependency groups:

- `[all]` - Install everything
- `[fastapi]` - FastAPI support
- `[gcp]` - Google Cloud Platform tools
- `[langchain]` - LangChain integration
- `[openai]` - OpenAI support
- `[anthropic]` - Anthropic/Claude support
- `[test]` - Testing dependencies
- `[azure]` - Azure support
- `[database]` - Database tools

## Verify Installation

```bash
# Check if sunholo is installed
uv pip list | grep sunholo

# Test import
uv run python -c "import sunholo; print(sunholo.__version__)"

# Run CLI
uv run sunholo --help
```

## Using with Scripts

Once installed, you can:

1. **Import in Python scripts:**
```python
from sunholo.agents.fastapi import VACRoutesFastAPI
from sunholo.utils import ConfigManager
```

2. **Use the CLI:**
```bash
uv run sunholo list-configs
uv run sunholo vac chat my_agent
```

3. **Run examples:**
```bash
# These will now work since sunholo is installed
uv run examples/fastapi_vac_demo.py
```

## Uninstall

```bash
uv pip uninstall sunholo
```

## Development Workflow

For active development:

```bash
# 1. Clone the repo
git clone https://github.com/sunholo-data/sunholo-py.git
cd sunholo-py

# 2. Install in editable mode with test dependencies
uv pip install -e ".[test,fastapi]"

# 3. Make changes to the code

# 4. Run tests to verify
uv run pytest tests/test_vac_routes_fastapi.py -v

# 5. Changes are immediately available - no reinstall needed!
```

## Troubleshooting

### If imports fail after installation:

```bash
# Check Python path
uv run python -c "import sys; print(sys.path)"

# Verify installation location
uv pip show sunholo
```

### For clean reinstall:

```bash
# Uninstall first
uv pip uninstall sunholo

# Clear cache (if needed)
uv cache clean

# Reinstall
uv pip install -e ".[all]"
```