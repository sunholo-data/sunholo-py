#!/usr/bin/env bash
# Monitor GitHub Actions workflows triggered by a tag push
# Usage: monitor_workflows.sh <tag> [--wait]
#
# Examples:
#   monitor_workflows.sh v0.146.1          # Check status once
#   monitor_workflows.sh v0.146.1 --wait   # Poll until all complete

set -euo pipefail

TAG="${1:-}"
WAIT="${2:-}"

if [ -z "$TAG" ]; then
    echo "Usage: monitor_workflows.sh <tag> [--wait]" >&2
    echo "Example: monitor_workflows.sh v0.146.1" >&2
    exit 1
fi

# Verify gh CLI is available
if ! command -v gh &> /dev/null; then
    echo "ERROR: gh CLI not found. Install from https://cli.github.com/" >&2
    exit 1
fi

echo "Monitoring workflows for tag: $TAG"
echo "================================================"

check_workflows() {
    local all_complete=true
    local any_failed=false

    # List workflow runs triggered by this tag
    RUNS=$(gh run list --limit 10 --json "workflowName,status,conclusion,databaseId,event,headBranch" 2>/dev/null)

    if [ -z "$RUNS" ] || [ "$RUNS" = "[]" ]; then
        echo "No workflow runs found yet. They may take a moment to start."
        all_complete=false
        return 1
    fi

    # Filter runs related to this tag (headBranch matches tag name without 'v' prefix sometimes)
    echo ""
    echo "Workflow Status ($(date '+%H:%M:%S')):"
    echo "----------------------------------------"

    # Use jq to process
    echo "$RUNS" | jq -r '.[] | "\(.workflowName)|\(.status)|\(.conclusion // "pending")|\(.databaseId)"' | while IFS='|' read -r name status conclusion run_id; do
        # Status emoji
        case "$status" in
            completed)
                case "$conclusion" in
                    success) icon="PASS" ;;
                    failure) icon="FAIL" ;;
                    cancelled) icon="SKIP" ;;
                    *) icon="?   " ;;
                esac
                ;;
            in_progress) icon="... " ;;
            queued) icon="WAIT" ;;
            *) icon="?   " ;;
        esac
        printf "  [%s] %-30s (run %s)\n" "$icon" "$name" "$run_id"
    done

    # Check if all are complete
    INCOMPLETE=$(echo "$RUNS" | jq '[.[] | select(.status != "completed")] | length')
    FAILED=$(echo "$RUNS" | jq '[.[] | select(.conclusion == "failure")] | length')

    echo ""
    if [ "$INCOMPLETE" -gt 0 ]; then
        echo "Status: $INCOMPLETE workflow(s) still running..."
        return 1
    elif [ "$FAILED" -gt 0 ]; then
        echo "Status: $FAILED workflow(s) FAILED"
        echo ""
        echo "To view failure details:"
        echo "$RUNS" | jq -r '.[] | select(.conclusion == "failure") | "  gh run view \(.databaseId) --log-failed"'
        return 2
    else
        echo "Status: All workflows completed successfully!"
        return 0
    fi
}

if [ "$WAIT" = "--wait" ]; then
    echo "Polling every 30s until all workflows complete..."
    while true; do
        check_workflows
        result=$?
        if [ $result -eq 0 ]; then
            echo ""
            echo "All done! Verify on PyPI:"
            VERSION="${TAG#v}"
            echo "  pip install sunholo==$VERSION"
            break
        elif [ $result -eq 2 ]; then
            echo ""
            echo "Fix failures and re-release with a new patch version."
            exit 1
        fi
        echo ""
        echo "Waiting 30s before next check..."
        sleep 30
    done
else
    check_workflows
    exit $?
fi
