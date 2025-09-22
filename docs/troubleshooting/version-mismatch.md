# Troubleshooting: Version Mismatch Issues

## Problem
When running `sunholo -v` or checking the package version, you might see an old version (e.g., 0.118.0) even after updating pyproject.toml to a newer version (e.g., 0.145.0).

## Root Causes

### 1. Hardcoded Download URL in pyproject.toml
**Issue**: The `Download` URL in `[project.urls]` section was hardcoded to a specific version tag.

**Solution**: Remove the Download URL entirely from pyproject.toml. PyPI will handle version management automatically.

```toml
# Before (problematic)
[project.urls]
Homepage = "https://github.com/sunholo-data/sunholo-py"
Download = "https://github.com/sunholo-data/sunholo-py/archive/refs/tags/v0.118.0.tar.gz"

# After (fixed)
[project.urls]
Homepage = "https://github.com/sunholo-data/sunholo-py"
```

### 2. Stale .egg-info Directories
**Issue**: Old `.egg-info` directories from previous installations can take precedence over the current version.

**Common locations**:
- `/Users/[username]/dev/sunholo/sunholo-py/sunholo.egg-info`
- `/Users/[username]/dev/sunholo/sunholo-py/src/sunholo.egg-info`
- `/Users/[username]/dev/sunholo/sunholo-py/src/sunholo/sunholo.egg-info`

**Solution**: Remove all stale .egg-info directories before reinstalling.

### 3. Multiple Python/pip Installations
**Issue**: System-level pip installations can conflict with virtual environment installations.

**Solution**: Always use `uv` for package management within the project.

## Resolution Steps

1. **Clean up stale egg-info directories**:
   ```bash
   # Run the cleanup script
   ./scripts/clean-egg-info.sh
   ```

2. **Uninstall existing installation**:
   ```bash
   uv pip uninstall sunholo
   ```

3. **Reinstall with uv**:
   ```bash
   uv pip install -e .
   ```

4. **Verify the version**:
   ```bash
   sunholo -v
   # Should show: sunholo-[current-version-from-pyproject.toml]
   ```

## Prevention

### Use the cleanup script before installing
Always run the cleanup script when you encounter version issues or after updating the version in pyproject.toml:

```bash
./scripts/clean-egg-info.sh
uv pip install -e .
```

### Check for multiple installations
To find all sunholo installations:

```bash
# Check with Python
python -c "from importlib.metadata import distributions; [print(f'{d.name}: {d.version} at {d._path}') for d in distributions() if 'sunholo' in d.name.lower()]"

# Check with pip (system)
pip list | grep sunholo

# Check with uv (virtual environment)
uv pip list | grep sunholo
```

## Best Practices

1. **Always use uv** for package management in this project
2. **Never use system pip** to install sunholo
3. **Run cleanup script** if you encounter version mismatches
4. **Keep pyproject.toml URLs dynamic** - don't hardcode version-specific URLs
5. **Use virtual environments** to isolate the development environment

## Related Files
- `/scripts/clean-egg-info.sh` - Cleanup script for stale egg-info directories
- `/src/sunholo/utils/version.py` - Version detection function
- `/pyproject.toml` - Package configuration