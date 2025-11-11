#!/bin/bash
# Voice2Note Production Startup Script
# For use with Tailscale network deployment

set -e  # Exit on error

echo "=========================================="
echo "  Voice2Note Production Startup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running in virtual environment
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}⚠ Warning: Not running in virtual environment${NC}"
    echo "Activating venv..."
    source venv/bin/activate || {
        echo "Error: Could not activate virtual environment"
        echo "Run: python3 -m venv venv && source venv/bin/activate"
        exit 1
    }
fi

# Check for SECRET_KEY
if [[ -z "$SECRET_KEY" ]]; then
    echo -e "${YELLOW}⚠ Warning: SECRET_KEY not set${NC}"
    echo "Generating a secure secret key..."
    export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    echo ""
    echo "Add this to your ~/.bashrc or environment:"
    echo "export SECRET_KEY=\"$SECRET_KEY\""
    echo ""
fi

# Get configuration
WORKERS=${WORKERS:-4}
PORT=${PORT:-5000}
TIMEOUT=${TIMEOUT:-600}

# Detect RAM and suggest worker count
TOTAL_RAM=$(free -g | awk '/^Mem:/{print $2}')
if [ "$TOTAL_RAM" -ge 20 ]; then
    SUGGESTED_WORKERS=8
    echo -e "${GREEN}✓ Detected ${TOTAL_RAM}GB RAM - suggesting 8 workers${NC}"
elif [ "$TOTAL_RAM" -ge 8 ]; then
    SUGGESTED_WORKERS=4
    echo -e "${GREEN}✓ Detected ${TOTAL_RAM}GB RAM - suggesting 4 workers${NC}"
else
    SUGGESTED_WORKERS=2
    echo -e "${YELLOW}⚠ Detected ${TOTAL_RAM}GB RAM - suggesting 2 workers${NC}"
fi

if [ -z "$WORKERS" ] || [ "$WORKERS" -eq 4 ]; then
    WORKERS=$SUGGESTED_WORKERS
fi

# Get Tailscale IP
TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "Not available")

echo ""
echo "Configuration:"
echo "  Workers: $WORKERS"
echo "  Port: $PORT"
echo "  Timeout: ${TIMEOUT}s"
echo "  Secret Key: $([ -n "$SECRET_KEY" ] && echo "Set ✓" || echo "Not set ✗")"
echo ""

if [ "$TAILSCALE_IP" != "Not available" ]; then
    echo -e "${GREEN}Tailscale Network:${NC}"
    echo "  IP: $TAILSCALE_IP"
    echo "  Access at: http://$TAILSCALE_IP:$PORT"
    echo ""
    echo "Enable HTTPS with: tailscale serve --bg https / http://localhost:$PORT"
    echo ""
fi

# Check if port is in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠ Warning: Port $PORT is already in use${NC}"
    echo "Kill the process with: sudo kill \$(sudo lsof -t -i:$PORT)"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Starting Voice2Note with Gunicorn..."
echo ""

# Start gunicorn
exec gunicorn \
    -w "$WORKERS" \
    -b "0.0.0.0:$PORT" \
    --timeout "$TIMEOUT" \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    app:app
