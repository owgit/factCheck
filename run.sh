#!/bin/bash

# Display colored messages
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================${NC}"
echo -e "${GREEN}Fact Check Application Launcher${NC}"
echo -e "${BLUE}=================================${NC}"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required dependencies
if ! command_exists node; then
    echo -e "${RED}Error: Node.js is required but not installed.${NC}"
    echo "Please install Node.js: https://nodejs.org/"
    exit 1
fi

if ! command_exists python3; then
    echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
    echo "Please install Python 3"
    exit 1
fi

# Check for Python environment
if [ -d "venv" ]; then
    echo -e "${GREEN}Found Python virtual environment (venv)${NC}"
    source venv/bin/activate
elif command_exists conda; then
    echo -e "${GREEN}Found Conda, activating environment from environment.yml${NC}"
    conda activate factCheck
else
    echo -e "${BLUE}No Python environment found, will run with system Python${NC}"
fi

# Check if .env file exists, if not copy from example
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${BLUE}Creating .env file from .env.example${NC}"
        cp .env.example .env
        echo -e "${RED}Please edit .env file to add your API keys${NC}"
    else
        echo -e "${RED}No .env or .env.example file found!${NC}"
        echo "Please create a .env file with appropriate configuration"
    fi
fi

# Make sure the uploads directory exists
mkdir -p uploads
mkdir -p video-upload-app/uploads

# Start backend server in the background
echo -e "${GREEN}Starting backend server...${NC}"
cd video-upload-app
if command_exists uvicorn; then
    uvicorn app:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    echo -e "${GREEN}Backend running on http://localhost:8000${NC}"
else
    echo -e "${RED}Uvicorn not found. Installing requirements...${NC}"
    pip install -r requirements.txt
    uvicorn app:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    echo -e "${GREEN}Backend running on http://localhost:8000${NC}"
fi
cd ..

# Start frontend in the background
echo -e "${GREEN}Starting frontend application...${NC}"
cd video-transcription-frontend
npm install
npm start &
FRONTEND_PID=$!
echo -e "${GREEN}Frontend running on http://localhost:3000${NC}"
cd ..

echo -e "${BLUE}=================================${NC}"
echo -e "${GREEN}All services started!${NC}"
echo -e "${GREEN}* Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}* Backend API: http://localhost:8000${NC}"
echo -e "${BLUE}=================================${NC}"
echo -e "${BLUE}Press Ctrl+C to stop all services${NC}"

# Trap SIGINT to kill both processes when Ctrl+C is pressed
trap "echo -e '${RED}Stopping services...${NC}'; kill $BACKEND_PID $FRONTEND_PID; exit" INT

# Wait for processes to finish
wait 