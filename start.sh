#!/bin/bash

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

echo ""
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}${BLUE}     NSE/BSE Stock Analysis Tool - Starting Up    ${NC}"
echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}✗ Python3 not found. Please install Python 3.9+ first.${NC}"
    exit 1
fi

# Check Node.js
if ! command -v node &>/dev/null; then
    echo -e "${RED}✗ Node.js not found. Please install Node.js 18+ first.${NC}"
    exit 1
fi

# Setup backend
echo -e "${YELLOW}→ Setting up Python backend...${NC}"
cd "$(dirname "$0")/backend"

if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "  Installing Python dependencies..."
pip install -r requirements.txt -q --disable-pip-version-check

echo -e "${GREEN}✓ Backend dependencies ready${NC}"

# Start backend
echo -e "${YELLOW}→ Starting FastAPI backend on port 8000...${NC}"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to start
sleep 2

# Check backend started
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${GREEN}✓ Backend running at http://localhost:8000${NC}"
else
    echo -e "${RED}✗ Backend failed to start${NC}"
    exit 1
fi

cd "$(dirname "$0")/frontend"

# Setup frontend
echo -e "${YELLOW}→ Setting up React frontend...${NC}"

if [ ! -d "node_modules" ]; then
    echo "  Installing Node.js dependencies (this may take a minute)..."
    npm install --silent
fi

echo -e "${GREEN}✓ Frontend dependencies ready${NC}"
echo -e "${YELLOW}→ Starting Vite dev server on port 5173...${NC}"

npm run dev &
FRONTEND_PID=$!

sleep 2

echo ""
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}${GREEN}  App is running!${NC}"
echo -e "${GREEN}  Frontend: ${BOLD}http://localhost:5173${NC}"
echo -e "${GREEN}  Backend:  ${BOLD}http://localhost:8000${NC}"
echo -e "${BOLD}${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  Press ${BOLD}Ctrl+C${NC} to stop all servers"
echo ""

# Open browser
sleep 1
if command -v open &>/dev/null; then
    open http://localhost:5173
fi

cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down servers...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}Done. Goodbye!${NC}"
}

trap cleanup INT TERM EXIT
wait
