# RFP System - Quick Reference Guide

## One-Line Deployment Commands

### Full Automated Deployment
```bash
sudo bash -c 'cd /tmp && git clone https://github.com/yourorg/agentic-rfp-demo.git && cd agentic-rfp-demo && chmod +x deploy-production.sh && ./deploy-production.sh'
```

### Start Service
```bash
sudo systemctl start rfp-system && sudo systemctl status rfp-system
```

### View Real-Time Logs
```bash
sudo journalctl -u rfp-system -f
```

### Monitor System Health
```bash
./monitor-rfp-system.sh
```

### Test API
```bash
curl http://localhost:8000/health && curl -X POST http://localhost:8000/api/rfp/process -H "Content-Type: application/json" -d @test_rfp.json
```

---

## Common Management Commands

```bash
# Service Control
sudo systemctl start rfp-system          # Start
sudo systemctl stop rfp-system           # Stop
sudo systemctl restart rfp-system        # Restart
sudo systemctl enable rfp-system         # Auto-start on reboot
sudo systemctl disable rfp-system        # Disable auto-start
sudo systemctl status rfp-system         # Check status

# Logs
sudo journalctl -u rfp-system -f                          # Follow live logs
sudo journalctl -u rfp-system -n 100                      # Last 100 lines
sudo journalctl -u rfp-system --since today               # Today's logs
sudo journalctl -u rfp-system -p err -n 50                # Last 50 errors
sudo journalctl -u rfp-system --since "2 hours ago"       # Last 2 hours

# Monitoring
ps aux | grep rfp-system                 # Check process running
netstat -tlnp | grep 8000               # Check port listening
du -sh /opt/rfp-system/data/             # Database size
df -h /opt/rfp-system/                  # Disk space
top -u rfp-system                       # CPU/Memory usage

# Configuration
sudo nano /opt/rfp-system/.env          # Edit config
sudo systemctl restart rfp-system        # Apply config changes

# Updates
cd /opt/rfp-system && sudo -u rfp-system git pull origin main
sudo systemctl restart rfp-system
```

---

## Troubleshooting Matrix

| Problem | Symptom | Check | Fix |
|---------|---------|-------|-----|
| **Service won't start** | `systemctl start` fails | `journalctl -u rfp-system` | Check logs for Python errors |
| **API not responding** | 502 Bad Gateway | `systemctl status rfp-system` | `systemctl restart rfp-system` |
| **Port in use** | Bind error on 8000 | `lsof -i :8000` | Kill the process or change port |
| **Out of memory** | Slow responses | `top -u rfp-system` | Restart service, check FAISS size |
| **API key error** | 403 Unauthorized | Check `.env` | Set GOOGLE_API_KEY correctly |
| **Database errors** | Vector DB failures | `ls -la /opt/rfp-system/data/` | Verify FAISS_DB_PATH |
| **High CPU usage** | Slow processing | `top -u rfp-system` | Increase workers or optimize |
| **Disk full** | Write errors | `df -h` | Delete old logs, backup FAISS DB |

---

## API Endpoints Quick Reference

```bash
# Health Check
GET /health

# Process RFP
POST /api/rfp/process
Content-Type: application/json
Body: { "rfp_data": [...] }

# Interactive Docs
GET /docs (Swagger UI)
GET /openapi.json (OpenAPI schema)
```

---

## Environment Variables Cheat Sheet

```bash
# Critical (must set)
GOOGLE_API_KEY=sk-...

# Important (review before deployment)
API_DEBUG=false              # Never true in production
API_WORKERS=4               # Adjust based on CPU cores
FAISS_DB_PATH=/opt/rfp-system/data/faiss_db
SECRET_KEY=your_secret_here

# Optional (defaults work)
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
GEMINI_MODEL=gemini-2.0-flash
```

---

## Useful File Locations

```bash
# Application
/opt/rfp-system                  # App root
/opt/rfp-system/backend          # Code
/opt/rfp-system/.env             # Config
/opt/rfp-system/venv             # Python

# Service
/etc/systemd/system/rfp-system.service

# Web Server
/etc/nginx/sites-available/rfp-system
/etc/nginx/sites-enabled/rfp-system

# Logs
/var/log/rfp-system/app.log
/var/log/rfp-system/access.log

# Data
/opt/rfp-system/data/faiss_db/   # Vector DB
/backups/                         # Backup location
```

---

## Performance Optimization

```bash
# Increase workers for better throughput
API_WORKERS=8  # Change based on CPU count (usually: cpu_count - 1 or -2)

# Increase timeout for complex RFPs
# In systemd service: --timeout 600

# Enable caching
# Add Redis: REDIS_URL=redis://localhost:6379

# Monitor performance
watch -n 1 'top -u rfp-system -b -n 1'
```

---

## Backup & Restore

```bash
# Backup FAISS database
sudo tar -czf /backup/faiss_db_$(date +%Y%m%d_%H%M%S).tar.gz /opt/rfp-system/data/faiss_db/

# Backup configuration
sudo cp /opt/rfp-system/.env /backup/.env.$(date +%Y%m%d_%H%M%S)

# Restore FAISS database
sudo tar -xzf /backup/faiss_db_YYYYMMDD_HHMMSS.tar.gz -C /

# Verify backup
sudo ls -lh /backup/
```

---

## Security Quick Checks

```bash
# Verify non-root user
ps aux | grep rfp-system    # Should run as rfp-system user

# Check .env permissions
ls -l /opt/rfp-system/.env  # Should be 600 (owner read/write only)

# Verify SSL/HTTPS
curl -I https://rfp-api.yourcompany.com/health

# Check firewall rules
sudo ufw status
```

---

## Nginx Troubleshooting

```bash
# Test config
sudo nginx -t

# Reload
sudo systemctl reload nginx

# View access logs
sudo tail -f /var/log/nginx/rfp-system-access.log

# View error logs
sudo tail -f /var/log/nginx/rfp-system-error.log

# Check if proxy is working
curl -v http://localhost:8000/health
curl -v http://localhost/health  # Through nginx
```

---

## Database Management

```bash
# Check database size
du -sh /opt/rfp-system/data/faiss_db/

# List database files
ls -lah /opt/rfp-system/data/faiss_db/

# Monitor during RFP processing
watch -n 1 'du -sh /opt/rfp-system/data/faiss_db/'
```

---

## Monitoring & Alerting Setup (Optional)

```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Monitor real-time
htop -u rfp-system

# Check I/O
iotop -u rfp-system

# Check network
nethogs

# CPU/Memory by process
ps aux | grep rfp-system | grep -v grep
```

---

## Emergency Procedures

### Service Crash Recovery
```bash
sudo systemctl restart rfp-system
sudo journalctl -u rfp-system -n 100  # Check what went wrong
```

### Clean Logs (when disk full)
```bash
sudo journalctl --vacuum=30d           # Keep only 30 days
sudo journalctl -u rfp-system --vacuum=500M  # Limit size
```

### Force Stop Stuck Process
```bash
sudo pkill -9 -f rfp-system
sleep 2
sudo systemctl start rfp-system
```

### Reset to Clean State
```bash
sudo systemctl stop rfp-system
sudo rm -rf /opt/rfp-system/data/faiss_db/*
sudo systemctl start rfp-system
```

---

## Verification Checklist

After deployment/changes:

```
☐ Service running: systemctl status rfp-system
☐ Port listening: netstat -tlnp | grep 8000
☐ Health OK: curl http://localhost:8000/health
☐ No errors: journalctl -u rfp-system | grep -i error
☐ API docs available: curl http://localhost:8000/docs
☐ Test RFP processes: curl -X POST ... -d @test_rfp.json
☐ Disk space OK: df -h /opt/rfp-system
☐ Memory OK: free -h
```

---

## Support Resources

- **Full Guide**: `DEPLOYMENT_GUIDE.md`
- **Checklist**: `DEPLOYMENT_CHECKLIST.md`
- **Status**: `DEPLOYMENT_READY.md`
- **API Docs**: `http://localhost:8000/docs`
- **Logs**: `sudo journalctl -u rfp-system -f`

---

**Version**: 1.0.0
**Last Updated**: 2026-02-21
