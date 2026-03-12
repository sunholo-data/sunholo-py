---
name: Release
description: Manage releases for Python projects. Use when user asks to release, bump version, tag, publish to PyPI, or monitor release workflows. Also use for /release.
---

# Release

Manages the full release lifecycle for sunholo-py and similar Python projects: version bumping, local testing, git tagging, pushing to trigger CI/CD, and monitoring GitHub Actions workflows through to PyPI publication.

## Quick Start

**Most common usage:**
```
User: "release a new patch version"
# This skill will:
# 1. Read current version from pyproject.toml
# 2. Bump patch version (e.g., 0.146.1 → 0.146.2)
# 3. Run local tests (uv run pytest tests)
# 4. Commit version bump via PR (protected branch)
# 5. After merge, create annotated git tag v0.146.2
# 6. Push tag to trigger GitHub Actions
# 7. Monitor workflow status until PyPI publish completes
```

## When to Use This Skill

Invoke this skill when:
- User asks to "release", "publish", "deploy to PyPI", or "tag a release"
- User says "bump version" (patch/minor/major)
- User asks to "monitor the release" or "check workflow status"
- User says "/release"
- User asks "what version are we on?"

## Available Scripts

### `scripts/bump_version.sh <patch|minor|major>`
Reads the current version from pyproject.toml and bumps it.

### `scripts/monitor_workflows.sh <tag>`
Monitors GitHub Actions workflows triggered by a tag push.

### `scripts/check_version.sh`
Displays the current version from pyproject.toml.

## Workflow

### 1. Pre-Release Checks

Before any release:
- Ensure you're on the `main` branch (or the branch to release from)
- Run `scripts/check_version.sh` to see current version
- Run `uv run pytest tests` to verify all tests pass locally
- Check `git status` for uncommitted changes

### 2. Version Bump

Run `scripts/bump_version.sh <patch|minor|major>` to update pyproject.toml.

**Version types:**
- `patch`: 0.146.1 → 0.146.2 (bug fixes, CI fixes)
- `minor`: 0.146.1 → 0.147.0 (new features, module additions)
- `major`: 0.146.1 → 1.0.0 (breaking changes)

**Protected branch workflow:**
Since main is typically protected, the version bump needs a PR:
1. Create branch: `git checkout -b release/v{new_version}`
2. Commit the pyproject.toml change
3. Push and create PR via `gh pr create`
4. Wait for user to merge (or merge if allowed)

### 3. Tag and Push

After the version bump is merged to main:
```bash
git checkout main && git pull origin main
git tag -a v{version} -m "Release v{version}

- Summary of changes
- Key features or fixes"
git push origin v{version}
```

Tag format: Always `v{version}` (e.g., `v0.146.1`).

### 4. Monitor Workflows

Run `scripts/monitor_workflows.sh v{version}` to watch the three triggered workflows:

| Workflow | File | Purpose |
|----------|------|---------|
| Test Python Package | test.yml | Run full test suite |
| Create GitHub Release | github-release.yml | Create GitHub Release page |
| Upload Python Package | python-publish.yml | Build, test, publish to PyPI |

The publish workflow steps:
1. Checkout code
2. Setup Python
3. Install build + pytest
4. `python -m build` (sdist + wheel)
5. Test minimal install (`pip install dist/*.whl && python -c "import sunholo"`)
6. Run unit tests (`pip install .[test] && pytest tests`)
7. Publish via `pypa/gh-action-pypi-publish`

### 5. Handle Failures

If a workflow fails:
1. Check failure details: `gh run view <run-id> --log-failed`
2. Common issues:
   - **Test failures**: Optional deps missing in CI (use `pytest.importorskip`)
   - **Build failures**: Check pyproject.toml syntax
   - **Publish failures**: Check PyPI token secret
3. Fix the issue, bump version again (patch), and re-release
4. **Never reuse a tag** that was pushed to PyPI (even if it failed partway)

### 6. Verify Publication

After successful workflow:
```bash
pip install sunholo=={version}  # Test install from PyPI
```

## Resources

### Workflow Reference
See [resources/reference.md](resources/reference.md) for GitHub Actions workflow details, troubleshooting guide, and common failure patterns.

## Notes

- **Always use `uv`** for local package management, never pip directly
- **Never force-push tags** — create a new patch version instead
- **Main branch is protected** — version bumps require PRs with approving reviews
- **CI tests with `.[test]` only** — channel/adk tests must skip when optional deps are missing
- Repository: `sunholo-data/sunholo-py`
- PyPI package name: `sunholo`
