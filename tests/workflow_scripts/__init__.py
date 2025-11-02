"""Tests for workflow helper scripts."""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[2] / ".github/workflows/scripts"
SCRIPT_PATH = str(SCRIPT_DIR)
if SCRIPT_PATH not in sys.path:
    sys.path.insert(0, SCRIPT_PATH)
