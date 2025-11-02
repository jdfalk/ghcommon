#!/bin/bash
# file: .devcontainer/post-create.sh
# version: 1.0.0
# guid: b2c3d4e5-f6g7-8901-2345-678901bcdefg

set -e

echo "🚀 Setting up GitHub Common Tools development environment..."

# Ensure we're in the workspace directory
cd /workspace

# Upgrade pip
echo "📦 Upgrading pip..."
python -m pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt
fi

# Install development dependencies
echo "🔧 Installing development dependencies..."
pip install black pylint flake8 isort pytest mypy

# Install additional dependencies for scripts
echo "📦 Installing additional script dependencies..."
if [ -f "scripts/copilot-firewall/requirements.txt" ]; then
  pip install -r scripts/copilot-firewall/requirements.txt
fi

# Make scripts executable
echo "🔧 Making scripts executable..."
find scripts/ -name "*.sh" -exec chmod +x {} \;
find scripts/ -name "*.py" -exec chmod +x {} \;

# Set up git safe directory
echo "🔒 Configuring git safe directory..."
git config --global --add safe.directory /workspace

# Create cache directories
echo "📁 Creating cache directories..."
mkdir -p /workspace/.cache
mkdir -p /workspace/tmp

echo "✅ GitHub Common Tools development environment setup complete!"
echo ""
echo "🎯 Available commands:"
echo "  python scripts/issue_manager.py --help    # Issue management"
echo "  python scripts/label_manager.py --help    # Label management"
echo "  python scripts/workflow_summary.py --help # Workflow summaries"
echo "  ./scripts/setup-label-sync.sh             # Setup label sync"
echo ""
echo "🔧 Development tools:"
echo "  black .                                    # Format code"
echo "  pylint scripts/                           # Lint Python code"
echo "  pytest                                     # Run tests (if any)"
