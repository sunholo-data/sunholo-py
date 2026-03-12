# Release Skill Reference

## GitHub Actions Workflows

### python-publish.yml (Upload Python Package)
- **Triggers**: `release: [published]` and `push: tags: ['v*']`
- **Permissions**: `contents: write`
- **Steps**:
  1. `actions/checkout@v3`
  2. `actions/setup-python@v3` (Python 3.x, currently resolves to 3.14.x)
  3. Install: `pip install build pytest`
  4. Build: `python -m build`
  5. Test minimal install: venv + `pip install dist/*.whl` + `python -c "import sunholo"`
  6. Run unit tests: `pip install .[test]` then `pytest tests`
  7. Publish: `pypa/gh-action-pypi-publish` with `PYPI_API_TOKEN` secret

### github-release.yml (Create GitHub Release)
- **Triggers**: `push: tags: ['v*']`
- Creates a GitHub Release page from the tag

### test.yml (Test Python Package)
- Runs the full test suite on push/PR

## Common Failure Patterns

### 1. Missing Optional Dependencies in CI
**Symptom**: `ImportError: <package> is required for <module>`
**Cause**: CI installs `pip install .[test]` which doesn't include optional groups like `[channels]`, `[adk]`
**Fix**: Add `pytest.importorskip("<package>")` at the start of tests that need optional deps
**Example**:
```python
@pytest.mark.asyncio
async def test_something(self):
    pytest.importorskip("httpx")
    from sunholo.channels.telegram import TelegramChannel
    ...
```

### 2. Version Already Exists on PyPI
**Symptom**: `HTTPError: 400 Bad Request - File already exists`
**Cause**: Attempted to re-upload a version that already exists
**Fix**: Never reuse versions. Bump to a new patch version.

### 3. Build Failures
**Symptom**: `python -m build` fails
**Cause**: Usually pyproject.toml syntax issues
**Fix**: Test build locally first: `python -m build`

### 4. PyPI Token Issues
**Symptom**: `403 Forbidden` during publish
**Cause**: `PYPI_API_TOKEN` secret expired or misconfigured
**Fix**: Regenerate token on PyPI and update GitHub repository secret

## Version Scheme

Follows semantic versioning: `MAJOR.MINOR.PATCH`

| Change Type | Bump | Example |
|------------|------|---------|
| Bug fix, CI fix, typo | patch | 0.146.1 → 0.146.2 |
| New module, feature | minor | 0.146.1 → 0.147.0 |
| Breaking API change | major | 0.146.1 → 1.0.0 |

## Tag Format

Always prefix with `v`: `v0.146.1`

Annotated tags with release notes:
```bash
git tag -a v0.146.1 -m "Release v0.146.1

- Fix CI: skip channel tests when httpx unavailable
- Bump setuptools requirement"
```

## Protected Branch Workflow

Since `main` is protected (requires PR with approving review):

1. Create release branch: `git checkout -b release/v0.146.1`
2. Make changes (version bump, fixes)
3. Commit and push
4. Create PR: `gh pr create --title "Release v0.146.1" --body "..."`
5. Wait for approval and merge
6. Switch to main: `git checkout main && git pull`
7. Tag: `git tag -a v0.146.1 -m "Release v0.146.1"`
8. Push tag: `git push origin v0.146.1`

## Dependency Groups

The `pyproject.toml` defines these optional dependency groups:

| Group | Key Packages | CI Installed |
|-------|-------------|-------------|
| `test` | pytest, pytest-asyncio | Yes |
| `channels` | httpx, twilio, markdown | No |
| `adk` | google-adk, litellm | No |
| `gcp` | google-cloud-* | No |
| `all` | Everything | No |

Tests for optional-dep modules MUST use `pytest.importorskip()` to gracefully skip in CI.

## Checklist

Before releasing:
- [ ] All local tests pass (`uv run pytest tests`)
- [ ] Version bumped in pyproject.toml
- [ ] No uncommitted changes
- [ ] On main branch (for tagging)
- [ ] Previous release workflow succeeded (check PyPI)
- [ ] Tag doesn't already exist
