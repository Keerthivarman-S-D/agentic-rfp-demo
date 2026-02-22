#!/bin/bash
# RFP System - View Logs (Real-time)
# Usage: ./logs-rfp-system.sh [OPTIONS]
# OPTIONS:
#   (none)          - Follow live logs
#   --tail N        - Show last N lines
#   --errors        - Show only errors
#   --today         - Show logs from today only

if [ "$1" == "--errors" ]; then
    sudo journalctl -u rfp-system -p err --no-pager | tail -50
elif [ "$1" == "--today" ]; then
    sudo journalctl -u rfp-system --since today --no-pager
elif [ "$1" == "--tail" ] && [ -n "$2" ]; then
    sudo journalctl -u rfp-system -n "$2" --no-pager
else
    echo "Following RFP System logs... (Ctrl+C to exit)"
    sudo journalctl -u rfp-system -f
fi
