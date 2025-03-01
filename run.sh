#!/bin/bash

echo "Setting up backend environment..."

# Navigate to middleware
cd middleware || exit

# Check if virtual environment exists, create it if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Trap function to handle script termination
trap "echo 'Stopping all processes...'; kill 0; exit" SIGINT SIGTERM

# Start ingestion.py in the background
echo "Starting ingestion.py..."
python ingestion.py &

# Start middleware.py in the background
echo "Starting middleware.py..."
python middleware.py &

# Navigate to frontend
cd ../frontend || exit

# Check if node_modules exists, install if needed
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm i --force
fi

# Start frontend in the background
echo "Starting frontend..."
npm run dev &

# Wait for all background processes and terminate them properly on Ctrl+C
wait
