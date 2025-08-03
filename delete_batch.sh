#!/bin/bash

# Test batch of workflow run IDs to delete
run_ids=(
16699889144
16699872311
16696221649
16696221257
16696214461
)

echo "Deleting ${#run_ids[@]} workflow runs for reusable-goreleaser.yml (test batch)..."

count=0
failed=0

for run_id in "${run_ids[@]}"; do
    count=$((count + 1))
    echo "[$count/${#run_ids[@]}] Deleting run ID: $run_id"

    if gh run delete "$run_id" 2>/dev/null; then
        echo "  ✓ Successfully deleted run $run_id"
    else
        echo "  ✗ Failed to delete run $run_id (might already be deleted or permission issue)"
        failed=$((failed + 1))
    fi

    # Add a small delay to avoid rate limiting
    sleep 1
done

echo ""
echo "Summary:"
echo "  Total runs: ${#run_ids[@]}"
echo "  Successfully deleted: $((count - failed))"
echo "  Failed: $failed"
