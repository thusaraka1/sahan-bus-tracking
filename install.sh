#!/bin/bash
set -e

echo "============================================================"
echo "  BusTrack AI - Automated Installation Script (Linux/macOS)"
echo "============================================================"
echo ""

# 1. Check Python
echo "[1/4] Checking Python 3..."
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed. Please install Python 3.10+."
    exit 1
fi
echo "  Found: $(python3 --version)"

# 2. Check Node.js
echo ""
echo "[2/4] Checking Node.js and npm..."
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js is not installed. Please install Node.js 18+."
    exit 1
fi
echo "  Found Node: $(node --version)"
echo "  Found npm:  $(npm --version)"

# 3. Setup Backend
echo ""
echo "[3/4] Setting up Python Backend..."
cd "$(dirname "$0")/backend"

if [ ! -d "venv" ]; then
    echo "  Creating Python virtual environment in backend/venv..."
    python3 -m venv venv
fi

echo "  Activating virtual environment..."
source venv/bin/activate

echo "  Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "  Copying .env.example to .env..."
        cp .env.example .env
    fi
fi

mkdir -p data

# 4. Setup Frontend
echo ""
echo "[4/4] Setting up Frontend..."
cd "$(dirname "$0")/frontend"
echo "  Installing Node packages..."
npm install

cd "$(dirname "$0")"

echo ""
echo "============================================================"
echo "  INSTALLATION COMPLETED SUCCESSFULLY!"
echo "============================================================"
echo ""
echo "To run the application:"
echo "  chmod +x run.sh && ./run.sh"
echo ""
