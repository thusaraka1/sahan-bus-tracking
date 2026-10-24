#!/bin/bash

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "============================================================"
echo "  BusTrack AI - Launching Application"
echo "============================================================"
echo ""

# Check installation
if [ ! -d "$ROOT_DIR/backend/venv" ]; then
    echo "[WARNING] Backend virtual environment not found!"
    echo "Please run ./install.sh first."
    exit 1
fi

if [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
    echo "[WARNING] Frontend node_modules not found!"
    echo "Please run ./install.sh first."
    exit 1
fi

cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "[1/2] Starting Flask Backend Server (Port 5000)..."
cd "$ROOT_DIR/backend"
source venv/bin/activate
python3 app.py &
BACKEND_PID=$!

echo "[2/2] Starting Vite Frontend Server (Port 5173)..."
cd "$ROOT_DIR/frontend"
npm run dev &
FRONTEND_PID=$!

sleep 3

echo ""
echo "============================================================"
echo "  APPLICATION RUNNING!"
echo "  - Backend:  http://localhost:5000"
echo "  - Frontend: http://localhost:5173"
echo "============================================================"
echo "Press Ctrl+C to stop all servers."
echo ""

wait
