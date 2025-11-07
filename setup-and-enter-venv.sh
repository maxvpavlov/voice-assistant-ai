#!/bin/bash
# setup-and-enter-venv.sh - Setup virtual environment and install dependencies
# Usage: source setup-and-enter-venv.sh

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

echo "=========================================="
echo "Voice Assistant Setup"
echo "=========================================="
echo ""

# Check if script is being sourced (needed for venv activation)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "⚠️  Note: For the virtual environment to persist, run:"
    echo "   source setup-and-enter-venv.sh"
    echo ""
    echo "Continuing with setup anyway..."
    echo ""
    SOURCED=false
else
    SOURCED=true
fi

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Check system dependencies
echo ""
echo "Checking system dependencies..."

# Check for PortAudio (needed for PyAudio)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if ! command -v brew &> /dev/null; then
        echo "⚠️  Homebrew not found. You may need to install PortAudio manually."
    elif ! brew list portaudio &> /dev/null 2>&1; then
        echo ""
        echo "📦 PortAudio not found. Installing via Homebrew..."
        brew install portaudio
    else
        echo "✓ PortAudio is installed"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if ! dpkg -l | grep -q portaudio19-dev; then
        echo ""
        echo "⚠️  PortAudio not detected. You may need to install it:"
        echo "   sudo apt-get install -y python3-pyaudio portaudio19-dev"
        echo ""
        echo -n "Would you like to install it now? (requires sudo) [y/N] "
        read REPLY
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo apt-get update
            sudo apt-get install -y python3-pyaudio portaudio19-dev
        fi
    else
        echo "✓ PortAudio is installed"
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment exists"
fi

# Activate virtual environment
echo ""
echo "🔄 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo ""
echo "📦 Upgrading pip..."
pip install --upgrade pip --quiet

# Install/upgrade requirements
echo ""
echo "📦 Installing dependencies from requirements.txt..."
pip install -r "$SCRIPT_DIR/requirements.txt"

# Check for training requirements
if [ -f "$SCRIPT_DIR/requirements-training.txt" ]; then
    echo ""
    echo "📦 Found requirements-training.txt (for full model training)"
    echo "   This includes PyTorch and other ML training dependencies (~500MB)"
    echo ""
    echo -n "Would you like to install training dependencies? [y/N] "
    read REPLY
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📦 Installing training dependencies..."
        pip install -r "$SCRIPT_DIR/requirements-training.txt"
        echo "✓ Training dependencies installed"
    else
        echo "⏭️  Skipping training dependencies"
        echo "   (You can install them later with: pip install -r requirements-training.txt)"
    fi
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""

# Check if venv is activated
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "🎉 Virtual environment is active!"
    echo ""
    echo "You can now run:"
    echo "  ./edge-wake-word test              # Test with pre-trained models"
    echo "  ./edge-wake-word train --help      # See training options"
    echo ""
    echo "To deactivate the virtual environment later, run:"
    echo "  deactivate"
else
    if [ "$SOURCED" = false ]; then
        echo "⚠️  Virtual environment was set up but not activated."
        echo ""
        echo "To activate it, run:"
        echo "  source venv/bin/activate"
        echo ""
        echo "Or run this script with 'source':"
        echo "  source setup-and-enter-venv.sh"
    fi
fi

echo ""
