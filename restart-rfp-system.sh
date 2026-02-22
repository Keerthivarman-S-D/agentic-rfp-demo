#!/bin/bash
# RFP System - Restart Service
sudo systemctl restart rfp-system
sleep 2
echo "Service status:"
sudo systemctl status rfp-system
echo ""
echo "Recent logs:"
sudo journalctl -u rfp-system -n 20 --no-pager
