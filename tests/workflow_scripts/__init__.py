"""Tests for workflow helper scripts."""

from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parents[2] / ".github/workflows/scripts"
SCRIPT_PATH = str(SCRIPT_DIR)
if SCRIPT_PATH not in sys.path:
    sys.path.insert(0, SCRIPT_PATH)
