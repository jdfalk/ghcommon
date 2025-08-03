#!/bin/bash

# Workflow run IDs to delete (removed already deleted ones)
run_ids=(
16696204468
16696194691
16696165738
16696156352
16696135617
16696129223
16696080889
16694648383
16694628216
16694611500
16694597464
16694597062
16693530065
16693463136
16693462269
16693461442
16693461161
16693440739
16693432552
16693428846
16693419931
16693419320
16693304129
16693297757
16693278805
16693209800
16693202891
16693202648
16693202425
16680835599
16680755273
16680030413
16680029604
16680029045
16649103516
16649096885
16649095834
16649075495
16649045182
16649043596
16624167847
16581876113
16581835286
16581804099
16576494625
16559262029
16555644854
16555106610
16554940305
16554939496
16554773387
16554742984
16554741680
16554062715
)

echo "Deleting ${#run_ids[@]} workflow runs for reusable-goreleaser.yml..."

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
    sleep 0.5
done

echo ""
echo "Summary:"
echo "  Total runs: ${#run_ids[@]}"
echo "  Successfully deleted: $((count - failed))"
echo "  Failed: $failed"
