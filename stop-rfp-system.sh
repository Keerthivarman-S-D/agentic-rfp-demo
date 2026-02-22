#!/bin/bash
# RFP System - Stop Service
sudo systemctl stop rfp-system
sleep 2
sudo systemctl status rfp-system
