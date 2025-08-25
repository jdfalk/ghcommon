#!/bin/bash
# file: scripts/setup-protovalidate.sh
# version: 1.0.0
# guid: f1e2d3c4-b5a6-7c8d-9e0f-1a2b3c4d5e6f

# Setup protovalidate for protobuf repositories
# This script downloads and configures protovalidate for any repository

set -euo pipefail

REPO_ROOT="${1:-$(pwd)}"
GHCOMMON_REPO="https://raw.githubusercontent.com/jdfalk/ghcommon/main"

echo "🚀 Setting up protovalidate for repository: $REPO_ROOT"
cd "$REPO_ROOT"

# Create tools directory if it doesn't exist
mkdir -p tools

echo "📥 Downloading protovalidate configuration and tools..."

# Download buf configuration files
echo "  → Downloading buf.yaml..."
if [ ! -f "buf.yaml" ]; then
    curl -sSL "$GHCOMMON_REPO/buf.yaml" -o buf.yaml
    echo "    ✓ Created buf.yaml"
else
    echo "    - buf.yaml already exists (skipping)"
fi

echo "  → Downloading buf.gen.yaml..."
if [ ! -f "buf.gen.yaml" ]; then
    curl -sSL "$GHCOMMON_REPO/buf.gen.yaml" -o buf.gen.yaml
    echo "    ✓ Created buf.gen.yaml"
    echo "    ⚠️  Update the module path in buf.gen.yaml for your repository"
else
    echo "    - buf.gen.yaml already exists (skipping)"
fi

# Download the protovalidate injection tool
echo "  → Downloading protovalidate injection tool..."
curl -sSL "$GHCOMMON_REPO/tools/mass-protovalidate-injector.py" -o tools/mass-protovalidate-injector.py
chmod +x tools/mass-protovalidate-injector.py
echo "    ✓ Created tools/mass-protovalidate-injector.py"

# Download documentation
echo "  → Downloading implementation guide..."
curl -sSL "$GHCOMMON_REPO/PROTOVALIDATE_IMPLEMENTATION_GUIDE.md" -o PROTOVALIDATE_IMPLEMENTATION_GUIDE.md
echo "    ✓ Created PROTOVALIDATE_IMPLEMENTATION_GUIDE.md"

# Count existing proto files
PROTO_COUNT=$(find . -name "*.proto" | wc -l)

echo ""
echo "📊 Repository Analysis:"
echo "  → Protobuf files found: $PROTO_COUNT"

if [ "$PROTO_COUNT" -eq 0 ]; then
    echo ""
    echo "❓ No protobuf files found. Choose an option:"
    echo "  1. Run 'python3 tools/mass-protovalidate-injector.py' to create example files"
    echo "  2. Create your own proto files and then run the tool"
    echo "  3. This repository might not need protobuf support"
else
    echo ""
    echo "🔧 Ready to apply protovalidate to $PROTO_COUNT proto files!"
    echo ""
    echo "Next steps:"
    echo "  1. Review buf.gen.yaml and update the module path"
    echo "  2. Run: python3 tools/mass-protovalidate-injector.py"
    echo "  3. Review and commit the changes"
    
    read -p "Apply protovalidate now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "🚀 Applying protovalidate to all proto files..."
        python3 tools/mass-protovalidate-injector.py
        
        echo ""
        echo "✅ Protovalidate setup complete!"
        echo ""
        echo "📋 Summary of changes:"
        echo "  → $PROTO_COUNT proto files processed"
        echo "  → Protovalidate imports added"
        echo "  → Validation rules applied based on field names and types"
        echo ""
        echo "🔍 Next steps:"
        echo "  1. Review the generated validation rules"
        echo "  2. Test with: buf lint && buf generate"
        echo "  3. Customize rules as needed"
        echo "  4. Commit your changes"
    else
        echo ""
        echo "✋ Skipped automatic application."
        echo "   Run 'python3 tools/mass-protovalidate-injector.py' when ready."
    fi
fi

echo ""
echo "📚 Documentation:"
echo "  → Implementation guide: PROTOVALIDATE_IMPLEMENTATION_GUIDE.md"
echo "  → Protovalidate docs: https://protovalidate.com/quickstart/"
echo ""
echo "🎉 Setup complete!"