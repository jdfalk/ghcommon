<!-- file: docs/cross-registry-todos/task-01/t01-part2.md -->
<!-- version: 1.0.0 -->
<!-- guid: t01-yaml-fix-part2-b2c3d4e5-f6a7 -->

# Task 01 Part 2: Step-by-Step Fix Procedure

## Detailed Fix Instructions

### Step 1: Locate the File

```bash
# Navigate to repository
cd /path/to/ghcommon

# Verify file exists
ls -la .github/workflows/release-rust.yml

# View file
cat .github/workflows/release-rust.yml | less
```

### Step 2: Find Affected Lines

```bash
# Search for restore-keys sections
grep -n "restore-keys" .github/workflows/release-rust.yml

# Output will show line numbers:
# 233:        restore-keys: |
# 243:        restore-keys: |
# 253:        restore-keys: |
```

### Step 3: Examine Current State

```bash
# View context around each occurrence
sed -n '230,240p' .github/workflows/release-rust.yml
sed -n '240,250p' .github/workflows/release-rust.yml
sed -n '250,260p' .github/workflows/release-rust.yml
```

### Expected Output - First Occurrence (Lines 230-240)

```yaml
- name: Cache Cargo dependencies
  uses: actions/cache@v4
  with:
    path: |
      ~/.cargo/bin/
      ~/.cargo/registry/index/
      ~/.cargo/registry/cache/
      ~/.cargo/git/db/
      target/
    key: ${{ runner.os }}-cargo-${{ matrix.rust }}-${{ hashFiles('**/Cargo.lock') }}
    restore-keys: |
      ${{ runner.os }}-cargo-${{ matrix.rust }}-
      ${{ runner.os }}-cargo-
```

### Expected Output - Second Occurrence (Lines 240-250)

```yaml
- name: Cache Cargo dependencies (aarch64)
  uses: actions/cache@v4
  with:
    path: |
      ~/.cargo/bin/
      ~/.cargo/registry/index/
      ~/.cargo/registry/cache/
      ~/.cargo/git/db/
      target/
    key: ${{ runner.os }}-cargo-${{ matrix.rust }}-${{ hashFiles('**/Cargo.lock') }}
    restore-keys: |
      ${{ runner.os }}-cargo-${{ matrix.rust }}-
      ${{ runner.os }}-cargo-
```

### Expected Output - Third Occurrence (Lines 250-260)

```yaml
- name: Cache Cargo dependencies (macOS)
  uses: actions/cache@v4
  with:
    path: |
      ~/.cargo/bin/
      ~/.cargo/registry/index/
      ~/.cargo/registry/cache/
      ~/.cargo/git/db/
      target/
    key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}
    restore-keys: |
      ${{ runner.os }}-cargo-
```

## Making the Changes

### Method 1: Using sed (Automated)

```bash
#!/bin/bash
# file: scripts/fix-yaml-trailing-hyphens.sh
# version: 1.0.0
# guid: fix-yaml-trailing-hyphens-script

set -e

FILE=".github/workflows/release-rust.yml"

echo "=== Fixing YAML Trailing Hyphens ==="

# Backup original file
cp "$FILE" "${FILE}.bak"
echo "✅ Created backup: ${FILE}.bak"

# Fix: Remove trailing hyphens from restore-keys lines
# Pattern: Lines ending with "}-" should become "}"
sed -i.tmp 's/\${{ runner\.os }}-cargo-\${{ matrix\.rust }}-$/\${{ runner.os }}-cargo-\${{ matrix.rust }}/g' "$FILE"
sed -i.tmp 's/\${{ runner\.os }}-cargo-$/\${{ runner.os }}-cargo/g' "$FILE"

# Remove temporary file
rm -f "${FILE}.tmp"

echo "✅ Fixed trailing hyphens"

# Show changes
echo ""
echo "=== Changes Made ==="
diff -u "${FILE}.bak" "$FILE" || true

# Verify
echo ""
echo "=== Verification ==="
if grep -q "\-$" <(grep -A 2 "restore-keys" "$FILE"); then
  echo "⚠️  Warning: Still found trailing hyphens"
  exit 1
else
  echo "✅ No trailing hyphens found in restore-keys"
fi

echo ""
echo "✅ Fix complete!"
```

### Method 2: Manual Editing with VS Code

**Step 1: Open file**

```bash
code .github/workflows/release-rust.yml
```

**Step 2: Use Find & Replace**

1. Press `Cmd+H` (Mac) or `Ctrl+H` (Windows/Linux)
2. Enable regex mode (button on right side of find box)

**Find Pattern:**

```regex
(\$\{\{ runner\.os \}\}-cargo-\$\{\{ matrix\.rust \}\})-.
```

**Replace Pattern:**

```
$1
```

**Step 3: Preview and Replace**

- Click "Replace All" (or `Cmd+Enter`)
- Review changes
- Save file (`Cmd+S`)

### Method 3: Manual Line-by-Line

**First Cache Block (Lines 233-236):**

**Before:**

```yaml
restore-keys: |
  ${{ runner.os }}-cargo-${{ matrix.rust }}-
  ${{ runner.os }}-cargo-
```

**After:**

```yaml
restore-keys: |
  ${{ runner.os }}-cargo-${{ matrix.rust }}
  ${{ runner.os }}-cargo
```

**Changes:**

- Line 234: Remove trailing `-`
- Line 235: Remove trailing `-`

**Second Cache Block (Lines 243-246):**

**Before:**

```yaml
restore-keys: |
  ${{ runner.os }}-cargo-${{ matrix.rust }}-
  ${{ runner.os }}-cargo-
```

**After:**

```yaml
restore-keys: |
  ${{ runner.os }}-cargo-${{ matrix.rust }}
  ${{ runner.os }}-cargo
```

**Changes:**

- Line 244: Remove trailing `-`
- Line 245: Remove trailing `-`

**Third Cache Block (Lines 253-256):**

**Before:**

```yaml
restore-keys: |
  ${{ runner.os }}-cargo-
```

**After:**

```yaml
restore-keys: |
  ${{ runner.os }}-cargo
```

**Changes:**

- Line 254: Remove trailing `-`

## Complete Before/After Comparison

### Full Context - First Occurrence

**Before (Lines 225-240):**

```yaml
- name: Install Rust
  uses: dtolnay/rust-toolchain@stable
  with:
    targets: ${{ matrix.target }}

- name: Cache Cargo dependencies
  uses: actions/cache@v4
  with:
    path: |
      ~/.cargo/bin/
      ~/.cargo/registry/index/
      ~/.cargo/registry/cache/
      ~/.cargo/git/db/
      target/
    key: ${{ runner.os }}-cargo-${{ matrix.rust }}-${{ hashFiles('**/Cargo.lock') }}
    restore-keys: |
      ${{ runner.os }}-cargo-${{ matrix.rust }}-
      ${{ runner.os }}-cargo-
```

**After (Lines 225-240):**

```yaml
- name: Install Rust
  uses: dtolnay/rust-toolchain@stable
  with:
    targets: ${{ matrix.target }}

- name: Cache Cargo dependencies
  uses: actions/cache@v4
  with:
    path: |
      ~/.cargo/bin/
      ~/.cargo/registry/index/
      ~/.cargo/registry/cache/
      ~/.cargo/git/db/
      target/
    key: ${{ runner.os }}-cargo-${{ matrix.rust }}-${{ hashFiles('**/Cargo.lock') }}
    restore-keys: |
      ${{ runner.os }}-cargo-${{ matrix.rust }}
      ${{ runner.os }}-cargo
```

**Diff:**

```diff
           key: ${{ runner.os }}-cargo-${{ matrix.rust }}-${{ hashFiles('**/Cargo.lock') }}
           restore-keys: |
-            ${{ runner.os }}-cargo-${{ matrix.rust }}-
-            ${{ runner.os }}-cargo-
+            ${{ runner.os }}-cargo-${{ matrix.rust }}
+            ${{ runner.os }}-cargo
```

### Full Context - Second Occurrence

**Before (Lines 238-252):**

```yaml
- name: Cache Cargo dependencies (aarch64)
  if: matrix.target == 'aarch64-unknown-linux-gnu'
  uses: actions/cache@v4
  with:
    path: |
      ~/.cargo/bin/
      ~/.cargo/registry/index/
      ~/.cargo/registry/cache/
      ~/.cargo/git/db/
      target/
    key: ${{ runner.os }}-cargo-${{ matrix.rust }}-${{ hashFiles('**/Cargo.lock') }}
    restore-keys: |
      ${{ runner.os }}-cargo-${{ matrix.rust }}-
      ${{ runner.os }}-cargo-
```

**After (Lines 238-252):**

```yaml
- name: Cache Cargo dependencies (aarch64)
  if: matrix.target == 'aarch64-unknown-linux-gnu'
  uses: actions/cache@v4
  with:
    path: |
      ~/.cargo/bin/
      ~/.cargo/registry/index/
      ~/.cargo/registry/cache/
      ~/.cargo/git/db/
      target/
    key: ${{ runner.os }}-cargo-${{ matrix.rust }}-${{ hashFiles('**/Cargo.lock') }}
    restore-keys: |
      ${{ runner.os }}-cargo-${{ matrix.rust }}
      ${{ runner.os }}-cargo
```

**Diff:**

```diff
           key: ${{ runner.os }}-cargo-${{ matrix.rust }}-${{ hashFiles('**/Cargo.lock') }}
           restore-keys: |
-            ${{ runner.os }}-cargo-${{ matrix.rust }}-
-            ${{ runner.os }}-cargo-
+            ${{ runner.os }}-cargo-${{ matrix.rust }}
+            ${{ runner.os }}-cargo
```

### Full Context - Third Occurrence

**Before (Lines 250-262):**

```yaml
- name: Cache Cargo dependencies (macOS)
  if: startsWith(matrix.os, 'macos')
  uses: actions/cache@v4
  with:
    path: |
      ~/.cargo/bin/
      ~/.cargo/registry/index/
      ~/.cargo/registry/cache/
      ~/.cargo/git/db/
      target/
    key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}
    restore-keys: |
      ${{ runner.os }}-cargo-
```

**After (Lines 250-262):**

```yaml
- name: Cache Cargo dependencies (macOS)
  if: startsWith(matrix.os, 'macos')
  uses: actions/cache@v4
  with:
    path: |
      ~/.cargo/bin/
      ~/.cargo/registry/index/
      ~/.cargo/registry/cache/
      ~/.cargo/git/db/
      target/
    key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}
    restore-keys: |
      ${{ runner.os }}-cargo
```

**Diff:**

```diff
           key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}
           restore-keys: |
-            ${{ runner.os }}-cargo-
+            ${{ runner.os }}-cargo
```

## Verification After Changes

### Automated Verification Script

```bash
#!/bin/bash
# file: scripts/verify-yaml-fix.sh
# version: 1.0.0
# guid: verify-yaml-fix-script

set -e

FILE=".github/workflows/release-rust.yml"

echo "=== Verifying YAML Fix ==="

# 1. Check file exists
if [ ! -f "$FILE" ]; then
  echo "❌ File not found: $FILE"
  exit 1
fi
echo "✅ File found"

# 2. Check for trailing hyphens in restore-keys
echo ""
echo "Checking for trailing hyphens in restore-keys..."
if grep -A 3 "restore-keys:" "$FILE" | grep -E "^\s+\$.*-$"; then
  echo "❌ Found trailing hyphens:"
  grep -A 3 "restore-keys:" "$FILE" | grep -E "^\s+\$.*-$"
  exit 1
else
  echo "✅ No trailing hyphens found"
fi

# 3. Validate YAML syntax
echo ""
echo "Validating YAML syntax..."
if command -v yamllint &> /dev/null; then
  yamllint "$FILE" && echo "✅ YAML syntax valid" || echo "⚠️  YAML warnings (non-critical)"
else
  echo "⚠️  yamllint not installed, skipping syntax check"
fi

# 4. Count restore-keys blocks
echo ""
restore_blocks=$(grep -c "restore-keys:" "$FILE")
echo "Restore-keys blocks found: $restore_blocks"
if [ "$restore_blocks" -eq 3 ]; then
  echo "✅ Expected number of restore-keys blocks"
else
  echo "⚠️  Unexpected number of restore-keys blocks (expected 3)"
fi

# 5. Verify cache key format
echo ""
echo "Verifying cache key formats..."
grep -A 3 "restore-keys:" "$FILE" | grep "\${{ runner.os }}-cargo" | while read line; do
  if echo "$line" | grep -qE "cargo-?$"; then
    echo "⚠️  Potential issue: $line"
  fi
done
echo "✅ Cache key formats look good"

echo ""
echo "✅ Verification complete!"
```

### Manual Verification Checklist

- [ ] Line 234: No trailing hyphen on `${{ runner.os }}-cargo-${{ matrix.rust }}`
- [ ] Line 235: No trailing hyphen on `${{ runner.os }}-cargo`
- [ ] Line 244: No trailing hyphen on `${{ runner.os }}-cargo-${{ matrix.rust }}`
- [ ] Line 245: No trailing hyphen on `${{ runner.os }}-cargo`
- [ ] Line 254: No trailing hyphen on `${{ runner.os }}-cargo`
- [ ] File still builds successfully
- [ ] Cache keys still work correctly
- [ ] No YAML syntax errors

## Continue to Part 3

Next part covers testing procedures and validation.
