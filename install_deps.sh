#!/bin/bash
# Shears dependency installation script

echo "=== Shears Dependency Installer ==="
echo

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Option 1: Try pipx (recommended)
if command_exists pipx; then
    echo "✓ pipx found, installing textual and rich..."
    pipx install textual
    pipx install rich
    echo "✓ Dependencies installed via pipx"
    echo "✓ You can now run: shears"
    exit 0
fi

# Option 2: Check if we can install pipx
echo "pipx not found. Attempting to install pipx..."
if command_exists apt; then
    sudo apt update
    sudo apt install -y pipx
    if [ $? -eq 0 ]; then
        echo "✓ pipx installed successfully"
        pipx install textual
        pipx install rich
        echo "✓ Dependencies installed via pipx"
        echo "✓ You can now run: shears"
        exit 0
    fi
fi

# Option 3: Fall back to user install
echo "Installing with pip --user (requires --break-system-packages)..."
pip install --user textual rich --break-system-packages
if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed via pip --user"
    echo "✓ You can now run: shears"
    exit 0
fi

# Option 4: Virtual environment
echo "Creating virtual environment..."
python3 -m venv ~/.shears-venv
if [ $? -eq 0 ]; then
    source ~/.shears-venv/bin/activate
    pip install textual rich
    echo "✓ Dependencies installed in virtual environment"
    echo "✓ To use shears with this venv:"
    echo "  source ~/.shears-venv/bin/activate"
    echo "  shears"
    exit 0
fi

echo "❌ All installation methods failed"
echo "Please try manually:"
echo "1. sudo apt install pipx && pipx install textual rich"
echo "2. pip install --user textual rich --break-system-packages"
exit 1