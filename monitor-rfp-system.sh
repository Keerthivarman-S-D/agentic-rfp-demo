#!/bin/bash
# RFP System - Health Check and Monitoring
# Usage: ./monitor-rfp-system.sh

API_URL="http://localhost:8000"
SERVICE_NAME="rfp-system"

echo "====================================="
echo "RFP System - Health Check"
echo "====================================="

# Check systemd service status
echo ""
echo "[SERVICE STATUS]"
sudo systemctl status $SERVICE_NAME --no-pager | head -10

# Check if API is responding
echo ""
echo "[API HEALTH]"
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $API_URL/health 2>/dev/null)
if [ "$HEALTH_RESPONSE" == "200" ]; then
    echo "✓ API is responding (HTTP $HEALTH_RESPONSE)"
    curl -s $API_URL/health | python -m json.tool
else
    echo "✗ API not responding (HTTP $HEALTH_RESPONSE)"
fi

# Check port is listening
echo ""
echo "[PORT STATUS]"
if netstat -tlnp 2>/dev/null | grep -q ":8000"; then
    echo "✓ Port 8000 is listening"
else
    echo "✗ Port 8000 is not listening"
fi

# Check filesystem
echo ""
echo "[DISK USAGE]"
df -h /opt/rfp-system 2>/dev/null | awk '{if (NR==1 || NR==2) print}'

# Check logs for recent errors
echo ""
echo "[RECENT ERRORS]"
sudo journalctl -u $SERVICE_NAME -p err -n 5 --no-pager 2>/dev/null || echo "No recent errors"

# Check system resources
echo ""
echo "[SYSTEM RESOURCES]"
free -h | head -2
echo ""
top -bn1 -u $SERVICE_NAME 2>/dev/null | head -5 || echo "Process not running"

echo ""
echo "====================================="
