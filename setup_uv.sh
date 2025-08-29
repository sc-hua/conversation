#!/bin/bash

# setup_uv.sh
# Helper script that sets up the project's virtual environment and dependencies.
# Prefers/optionally uses 'uv' (https://github.com/jonashaag/uv) if available.
#
# Usage:
#   ./setup_uv.sh            # Create/activate venv and install deps (no auto-enter uv)
#   ./setup_uv.sh --enter    # If 'uv' is installed, exec into 'uv' after setup
#   ./setup_uv.sh -e         # shorthand
#
# This script preserves the original venv + pip install flow and only uses
# 'uv' to enter an interactive environment when requested.

set -euo pipefail

ENTER_UV=0
if [ "${1-}" = "--enter" ] || [ "${1-}" = "-e" ]; then
  ENTER_UV=1
fi

# Detect uv availability
if command -v uv >/dev/null 2>&1; then
  UV_AVAILABLE=1
else
  UV_AVAILABLE=0
fi

echo "🚀 Running setup_uv.sh (uv available: ${UV_AVAILABLE})"

# Create virtual environment if missing
if [ ! -d "venv" ]; then
  echo "Creating virtual environment 'venv'..."
  python3 -m venv venv
else
  echo "Found existing 'venv' directory. Skipping creation."
fi

# Activate venv for this script
if [ -f "venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source venv/bin/activate
else
  echo "Warning: venv activation script not found. Continuing without activation."
fi

# Upgrade pip and install requirements
echo "Installing dependencies from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Dependencies installed."

if [ "$UV_AVAILABLE" -eq 1 ]; then
  echo ""
  echo "Detected 'uv'. Recommended: install via pipx if you haven't: pipx install uv"
  echo "You can enter the uv-managed environment with the 'uv' command."
  if [ "$ENTER_UV" -eq 1 ]; then
    echo "Launching 'uv' now (this will replace the current process)..."
    exec uv
  else
    echo "Run './setup_uv.sh --enter' to drop into an interactive 'uv' shell after setup."
  fi
else
  echo ""
  echo "Note: 'uv' not found. To use uv install it (recommended): pipx install uv"
fi

echo ""
echo "Next steps:"
echo " 1. Configure your .env file with API keys"
echo " 2. Start Redis server: redis-server"
echo " 3. Run demo: python demo.py"
echo " 4. Or start API server: python main.py"
