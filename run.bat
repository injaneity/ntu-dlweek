@echo off
echo Setting up backend environment...

cd middleware

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    echo Activating virtual environment...
    call venv\Scripts\activate
)

:: Start ingestion.py in a new process
echo Starting ingestion.py...
start "Ingestion" cmd /c "call venv\Scripts\activate && python ingestion.py"

:: Start middleware.py in a new process
echo Starting middleware.py...
start "Middleware" cmd /c "call venv\Scripts\activate && python middleware.py"

cd ../frontend
echo Setting up frontend...

if not exist node_modules (
    echo Installing frontend dependencies...
    npm i --force
)

:: Start frontend in a new process
echo Starting frontend...
start "Frontend" cmd /c "npm run dev"

:: Wait for user to manually close everything
echo All services started. Press Ctrl+C in each window to stop.
pause
