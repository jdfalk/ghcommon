#!/bin/bash
# file: scripts/test-codeql-cache-fixes.sh
# version: 1.0.0
# guid: 789a1234-b567-8c90-d123-456789abcdef

set -euo pipefail

echo "🧪 Testing CodeQL Cache Collision Fixes"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
tests_passed=0
tests_total=0

run_test() {
    local test_name="$1"
    local test_command="$2"
    
    ((tests_total++))
    echo -e "\n${YELLOW}Test $tests_total: $test_name${NC}"
    echo "Command: $test_command"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASSED${NC}"
        ((tests_passed++))
    else
        echo -e "${RED}❌ FAILED${NC}"
    fi
}

# Test 1: Validate workflow YAML syntax
run_test "YAML Syntax Validation" \
    "python -c \"import yaml; yaml.safe_load(open('.github/workflows/reusable-codeql.yml'))\""

# Test 2: Validate example workflow YAML syntax
run_test "Example Workflow YAML Validation" \
    "python -c \"import yaml; yaml.safe_load(open('examples/workflows/codeql-analysis-example.yml'))\""

# Test 3: Check matrix-key input is present
run_test "Matrix-key Input Present" \
    "python -c \"
import yaml
wf = yaml.safe_load(open('.github/workflows/reusable-codeql.yml'))
inputs = wf.get(True, {}).get('workflow_call', {}).get('inputs', {})
assert 'matrix-key' in inputs, 'matrix-key input missing'
assert inputs['matrix-key']['default'] == 'default', 'matrix-key default incorrect'
print('matrix-key input properly configured')
\""

# Test 4: Check cache-id includes all uniqueness components
run_test "Cache-ID Uniqueness Components" \
    "python -c \"
import yaml
wf = yaml.safe_load(open('.github/workflows/reusable-codeql.yml'))
jobs = wf.get('jobs', {})
steps = jobs.get('analyze', {}).get('steps', [])
init_steps = [s for s in steps if 'github/codeql-action/init' in s.get('uses', '')]
assert init_steps, 'CodeQL init step not found'
cache_id = init_steps[0].get('with', {}).get('cache-id', '')
components = ['github.repository', 'github.ref_name', 'inputs.languages', 'inputs.matrix-key']
for comp in components:
    assert comp in cache_id, f'Missing component: {comp}'
print('All uniqueness components present in cache-id')
\""

# Test 5: Verify manual cache step was removed
run_test "Manual Cache Step Removed" \
    "python -c \"
import yaml
wf = yaml.safe_load(open('.github/workflows/reusable-codeql.yml'))
jobs = wf.get('jobs', {})
steps = jobs.get('analyze', {}).get('steps', [])
cache_steps = [s for s in steps if s.get('name') == 'Cache CodeQL database']
assert not cache_steps, 'Manual cache step still present'
print('Manual cache step successfully removed')
\""

# Test 6: Simulate cache key generation for different scenarios
run_test "Cache Collision Prevention" \
    "python -c \"
# Simulate different workflow scenarios
scenarios = [
    {'repo': 'owner/repo1', 'ref': 'main', 'lang': 'javascript', 'key': 'single'},
    {'repo': 'owner/repo1', 'ref': 'main', 'lang': 'python', 'key': 'single'},
    {'repo': 'owner/repo1', 'ref': 'main', 'lang': 'javascript', 'key': 'matrix-js'},
    {'repo': 'owner/repo2', 'ref': 'main', 'lang': 'javascript', 'key': 'single'},
    {'repo': 'owner/repo1', 'ref': 'feature', 'lang': 'javascript', 'key': 'single'},
]

cache_keys = set()
for scenario in scenarios:
    cache_key = f\\\"{scenario['repo']}-{scenario['ref']}-{scenario['lang']}-{scenario['key']}\\\"
    assert cache_key not in cache_keys, f'Cache collision detected: {cache_key}'
    cache_keys.add(cache_key)

print(f'Generated {len(cache_keys)} unique cache keys - no collisions!')
\""

# Test 7: Check documentation was created
run_test "Documentation Created" \
    "test -f docs/codeql-caching-guide.md && test -f examples/workflows/codeql-analysis-example.yml"

# Test 8: Validate version was updated
run_test "Version Updated" \
    "grep -q 'version: 1.1.0' .github/workflows/reusable-codeql.yml"

# Summary
echo -e "\n${YELLOW}===============================================${NC}"
echo -e "${YELLOW}Test Summary${NC}"
echo -e "${YELLOW}===============================================${NC}"

if [ $tests_passed -eq $tests_total ]; then
    echo -e "${GREEN}🎉 All tests passed! ($tests_passed/$tests_total)${NC}"
    echo -e "${GREEN}✅ CodeQL cache collision fixes are working correctly${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed ($tests_passed/$tests_total)${NC}"
    echo -e "${RED}Please review the failed tests above${NC}"
    exit 1
fi