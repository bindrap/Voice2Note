#!/bin/bash
# restart.sh - Restart Voice2Note web application

echo "🔄 Restarting Voice2Note application..."

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Kill existing gunicorn processes for this app (only port 5000)
echo "📋 Stopping existing processes..."

# Get PIDs of gunicorn processes using port 5000
PIDS=$(ps aux | grep "[g]unicorn.*5000" | awk '{print $2}')

if [ -n "$PIDS" ]; then
    echo "Found processes: $PIDS"
    for pid in $PIDS; do
        kill $pid 2>/dev/null || true
    done

    # Wait for graceful shutdown
    sleep 3

    # Force kill any remaining processes
    REMAINING=$(ps aux | grep "[g]unicorn.*5000" | awk '{print $2}')
    if [ -n "$REMAINING" ]; then
        echo "⚠️  Forcefully killing remaining processes: $REMAINING"
        for pid in $REMAINING; do
            kill -9 $pid 2>/dev/null || true
        done
        sleep 1
    fi
else
    echo "No existing processes found."
fi

# Activate virtual environment
echo "🚀 Starting application..."
source venv/bin/activate

# Check if app.py exists
if [ ! -f "app.py" ]; then
    echo "❌ app.py not found in $SCRIPT_DIR"
    exit 1
fi

# Start gunicorn in daemon mode with error log
nohup gunicorn -w 8 -b 0.0.0.0:5000 --timeout 1800 app:app --error-logfile logs/error.log --access-logfile logs/access.log > logs/gunicorn.log 2>&1 &

# Wait a moment for startup
sleep 3

# Check if it started successfully
if ps aux | grep "[g]unicorn.*5000" > /dev/null; then
    WORKER_COUNT=$(ps aux | grep "[g]unicorn.*5000" | wc -l)
    echo "✅ Application restarted successfully!"
    echo "📍 Running on http://0.0.0.0:5000"
    echo "👷 Workers: $WORKER_COUNT"
else
    echo "❌ Failed to start application. Check logs/gunicorn.log for errors."
    if [ -f "logs/gunicorn.log" ]; then
        echo "Last 20 lines of error log:"
        tail -20 logs/gunicorn.log
    fi
    exit 1
fi
