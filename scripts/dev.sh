#!/bin/bash

# Cognito Development Script
# Starts both backend and frontend

# Exit on error
set -e

# Function to kill all background processes on exit
cleanup() {
    echo -e "\n\033[0;33mShutting down services...\033[0m"
    # Kill the background processes
    [ -n "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null
    [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

echo -e "\033[0;32mStarting Cognito Development Environment...\033[0m"

# Start Backend
echo -e "\033[0;34m[Backend]\033[0m Starting on http://0.0.0.0:8000"
(cd backend && uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload) &
BACKEND_PID=$!

# Start Frontend
echo -e "\033[0;36m[Frontend]\033[0m Starting..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

# Wait for all background processes
wait
