#!/bin/bash

# Clean up stale .egg-info directories that can cause version conflicts
# This script should be run when encountering version mismatch issues

echo "Cleaning up stale .egg-info directories..."

# Get the script's directory to find the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Counter for found directories
COUNT=0

# Find and remove .egg-info directories
echo "Searching for .egg-info directories in $PROJECT_ROOT..."

# Use find to locate all .egg-info directories
while IFS= read -r egg_info_dir; do
    if [ -d "$egg_info_dir" ]; then
        # Skip the one in .venv as it's managed by uv/pip
        if [[ "$egg_info_dir" == *".venv"* ]]; then
            echo "  Skipping (managed by uv): $egg_info_dir"
        else
            echo "  Removing: $egg_info_dir"
            rm -rf "$egg_info_dir"
            COUNT=$((COUNT + 1))
        fi
    fi
done < <(find "$PROJECT_ROOT" -name "*.egg-info" -type d 2>/dev/null)

# Summary
if [ $COUNT -eq 0 ]; then
    echo "No stale .egg-info directories found."
else
    echo "Removed $COUNT stale .egg-info directories."
fi

echo ""
echo "Next steps:"
echo "1. Reinstall sunholo with: uv pip install -e ."
echo "2. Verify version with: sunholo -v"