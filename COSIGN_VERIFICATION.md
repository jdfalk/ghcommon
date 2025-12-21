<!-- file: COSIGN_VERIFICATION.md -->
<!-- version: 1.0.0 -->
<!-- guid: c0519n-v3r1f1c4t10n-1a2b3c4d5e6f -->

# Cosign Signature Verification

This repository uses [Cosign](https://docs.sigstore.dev/cosign/overview/) to
sign release artifacts, providing cryptographic verification of their
authenticity and integrity.

## What is Signed

All release artifacts are signed using Cosign:

- `go-build-all.tar.gz` and `go-build-all.zip` (combined builds)
- Individual platform builds in `per-os/` directory
- Corresponding `.sig` signature files are generated for each artifact

## Verifying Signatures

### Prerequisites

Install Cosign:

```bash
# Using Homebrew (macOS)
brew install cosign

# Using Go
go install github.com/sigstore/cosign/v2/cmd/cosign@latest

# Or download from releases
# https://github.com/sigstore/cosign/releases
```

### Verification Steps

1. **Download the artifacts and signature files** from the GitHub release or
   workflow artifacts

2. **Download the public key** (`cosign.pub`) from the GitHub release artifacts
   or from this repository

3. **Verify a signature**:

   ```bash
   # Verify a specific artifact
   cosign verify-blob --key cosign.pub --signature go-build-all.tar.gz.sig go-build-all.tar.gz

   # Verify all artifacts in current directory
   for f in *.tar.gz *.zip; do
     if [ -f "$f.sig" ]; then
       echo "Verifying $f..."
       cosign verify-blob --key cosign.pub --signature "$f.sig" "$f"
     fi
   done
   ```

### Successful Verification Output

A successful verification will output:

```text
Verified OK
```

If verification fails, cosign will exit with a non-zero status and provide an
error message.

## Public Key Information

- **File**: `cosign.pub` (available in release artifacts)
- **Algorithm**: ECDSA P-256
- **Purpose**: Verifying release artifact signatures
- **Source**: Generated from the repository's `COSIGN_PRIVATE_KEY` secret

## Security Notes

- Always verify signatures before using release artifacts in production
- The public key is included with each release to ensure you have the correct
  key
- You can also find a copy of the current public key in this repository
- If verification fails, do not use the artifact as it may have been tampered
  with
- Report any signature verification failures as potential security issues

## Automation

You can integrate signature verification into your deployment scripts:

```bash
#!/bin/bash
set -euo pipefail

ARTIFACT="go-build-all.tar.gz"
SIGNATURE="go-build-all.tar.gz.sig"
PUBLIC_KEY="cosign.pub"

# Download files (adjust URLs as needed)
curl -L -o "$ARTIFACT" "https://github.com/jdfalk/ghcommon/releases/download/v1.0.0/$ARTIFACT"
curl -L -o "$SIGNATURE" "https://github.com/jdfalk/ghcommon/releases/download/v1.0.0/$SIGNATURE"
curl -L -o "$PUBLIC_KEY" "https://github.com/jdfalk/ghcommon/releases/download/v1.0.0/$PUBLIC_KEY"

# Verify signature
if cosign verify-blob --key "$PUBLIC_KEY" --signature "$SIGNATURE" "$ARTIFACT"; then
    echo "✅ Signature verified successfully"
    # Proceed with deployment
else
    echo "❌ Signature verification failed"
    exit 1
fi
```

For more information about Cosign, visit the
[official documentation](https://docs.sigstore.dev/cosign/overview/).
