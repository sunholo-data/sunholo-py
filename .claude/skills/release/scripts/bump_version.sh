#!/usr/bin/env bash
# Bump version in pyproject.toml
# Usage: bump_version.sh <patch|minor|major> [path/to/pyproject.toml]
#
# Examples:
#   bump_version.sh patch   # 0.146.1 → 0.146.2
#   bump_version.sh minor   # 0.146.1 → 0.147.0
#   bump_version.sh major   # 0.146.1 → 1.0.0

set -euo pipefail

BUMP_TYPE="${1:-}"
PYPROJECT="${2:-pyproject.toml}"

if [ -z "$BUMP_TYPE" ]; then
    echo "Usage: bump_version.sh <patch|minor|major> [pyproject.toml]" >&2
    exit 1
fi

if [ ! -f "$PYPROJECT" ]; then
    echo "ERROR: $PYPROJECT not found" >&2
    exit 1
fi

# Parse current version
CURRENT=$(grep '^version = ' "$PYPROJECT" | head -1 | sed 's/version = "\(.*\)"/\1/')
if [ -z "$CURRENT" ]; then
    echo "ERROR: Could not parse version from $PYPROJECT" >&2
    exit 1
fi

# Split into components
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT"

# Bump
case "$BUMP_TYPE" in
    patch)
        PATCH=$((PATCH + 1))
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    *)
        echo "ERROR: Invalid bump type '$BUMP_TYPE'. Use: patch, minor, or major" >&2
        exit 1
        ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"

# Update pyproject.toml
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' "s/^version = \"${CURRENT}\"/version = \"${NEW_VERSION}\"/" "$PYPROJECT"
else
    sed -i "s/^version = \"${CURRENT}\"/version = \"${NEW_VERSION}\"/" "$PYPROJECT"
fi

# Verify
VERIFY=$(grep '^version = ' "$PYPROJECT" | head -1 | sed 's/version = "\(.*\)"/\1/')
if [ "$VERIFY" != "$NEW_VERSION" ]; then
    echo "ERROR: Version update failed. Expected $NEW_VERSION, got $VERIFY" >&2
    exit 1
fi

echo "Version bumped: $CURRENT → $NEW_VERSION"
echo "Tag will be: v$NEW_VERSION"
echo ""
echo "Next steps:"
echo "  1. Run tests: uv run pytest tests"
echo "  2. Commit: git add pyproject.toml && git commit -m 'Bump version to $NEW_VERSION'"
echo "  3. If main is protected, create a PR"
echo "  4. After merge, tag: git tag -a v$NEW_VERSION -m 'Release v$NEW_VERSION'"
echo "  5. Push tag: git push origin v$NEW_VERSION"
