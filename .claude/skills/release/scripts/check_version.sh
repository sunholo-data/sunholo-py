#!/usr/bin/env bash
# Check current version from pyproject.toml
# Usage: check_version.sh [path/to/pyproject.toml]

set -euo pipefail

PYPROJECT="${1:-pyproject.toml}"

if [ ! -f "$PYPROJECT" ]; then
    echo "ERROR: $PYPROJECT not found" >&2
    echo "Run from the project root directory." >&2
    exit 1
fi

VERSION=$(grep '^version = ' "$PYPROJECT" | head -1 | sed 's/version = "\(.*\)"/\1/')

if [ -z "$VERSION" ]; then
    echo "ERROR: Could not parse version from $PYPROJECT" >&2
    exit 1
fi

echo "Current version: $VERSION"
echo "Tag would be: v$VERSION"

# Check if tag already exists
if git tag -l "v$VERSION" | grep -q "v$VERSION"; then
    echo "WARNING: Tag v$VERSION already exists!"
    echo "Latest tags:"
    git tag --sort=-v:refname | head -5
else
    echo "Tag v$VERSION does not exist yet (ready to tag)"
fi

# Show latest tags for context
echo ""
echo "Recent tags:"
git tag --sort=-v:refname | head -5 2>/dev/null || echo "(no tags found)"
