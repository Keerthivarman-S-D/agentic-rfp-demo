# RFP System - Production Deployment Guide

## Overview

This guide covers deploying the RFP Processing System in a production environment on a Linux server.

**System Requirements:**
- Ubuntu 20.04 LTS or newer (or equivalent Linux distribution)
- 8+ CPU cores
- 16+ GB RAM
- 100 GB free disk space (for FAISS vector DB)
- Network access to Google Gemini API
- Internet connectivity for LME commodity data

## Pre-Deployment Checklist

Before starting deployment:

- [ ] Linux server is provisioned and accessible via SSH
- [ ] You have `sudo` access to the server
- [ ] Python 3.10+ is installed
- [ ] Git is installed
- [ ] Nginx is installed (optional, for reverse proxy)
- [ ] Google Gemini API key obtained (https://ai.google.dev)
- [ ] Domain name configured and DNS points to server
- [ ] SSL certificate ready or plan to use Let's Encrypt

## Quick Start (5 minutes)

### 1. SSH into your server
```bash
ssh ubuntu@your-server-ip
sudo -i  # Switch to root
```

### 2. Download and run automated deployment
```bash
cd /tmp
git clone https://github.com/yourorg/agentic-rfp-demo.git
cd agentic-rfp-demo
chmod +x deploy-production.sh
./deploy-production.sh
```

### 3. Configure environment
```bash
nano /opt/rfp-system/.env
# Add your GOOGLE_API_KEY and other settings
```

### 4. Start the service
```bash
systemctl start rfp-system
systemctl enable rfp-system  # Auto-start on reboot
```

### 5. Verify it's running
```bash
curl http://localhost:8000/health
```

## Detailed Deployment Steps

### Step 1: Server Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3.10 python3.10-venv python3-pip git nginx curl

# Install optional: monitoring tools
sudo apt install -y htop iotop nethogs

# Create RFP system user
sudo useradd -r -s /bin/bash -d /opt/rfp-system rfp-system

# Create directories
sudo mkdir -p /opt/rfp-system/{data,logs}
sudo chown -R rfp-system:rfp-system /opt/rfp-system
sudo mkdir -p /var/log/rfp-system
sudo chown -R rfp-system:rfp-system /var/log/rfp-system
```

### Step 2: Clone Repository

```bash
# Clone the code
cd /tmp
git clone https://github.com/yourorg/agentic-rfp-demo.git rfp-deploy-tmp
cd rfp-deploy-tmp

# Copy to production location
sudo cp -r . /opt/rfp-system/
sudo chown -R rfp-system:rfp-system /opt/rfp-system
```

### Step 3: Setup Python Virtual Environment

```bash
cd /opt/rfp-system

# Create and activate virtual environment
sudo -u rfp-system python3.10 -m venv venv
sudo -u rfp-system ./venv/bin/pip install --upgrade pip setuptools wheel

# Install dependencies
sudo -u rfp-system ./venv/bin/pip install -r requirements.txt

# Install production WSGI server
sudo -u rfp-system ./venv/bin/pip install gunicorn uvicorn
```

### Step 4: Configure Environment

```bash
# Copy production environment template
sudo cp /opt/rfp-system/.env.production /opt/rfp-system/.env
sudo chown rfp-system:rfp-system /opt/rfp-system/.env
sudo chmod 600 /opt/rfp-system/.env

# Edit configuration
sudo nano /opt/rfp-system/.env
```

**Critical Configuration Variables:**

```bash
GOOGLE_API_KEY=sk-...           # Get from https://ai.google.dev
GEMINI_MODEL=gemini-2.0-flash

API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false
API_WORKERS=4

# Create directories and paths
FAISS_DB_PATH=/opt/rfp-system/data/faiss_db
LOG_FILE=/var/log/rfp-system/app.log

# Security
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')
ALLOWED_ORIGINS=https://yourcompany.com
```

### Step 5: Setup Systemd Service

```bash
# Copy service file
sudo cp /opt/rfp-system/rfp-system.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable auto-start
sudo systemctl enable rfp-system

# Start the service
sudo systemctl start rfp-system

# Verify it's running
sudo systemctl status rfp-system
```

### Step 6: Setup Nginx Reverse Proxy

```bash
# Copy nginx configuration
sudo cp /opt/rfp-system/nginx-rfp-system.conf /etc/nginx/sites-available/rfp-system

# Enable site
sudo ln -s /etc/nginx/sites-available/rfp-system /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

**For HTTPS setup with Let's Encrypt:**

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d rfp-api.yourcompany.com

# Update nginx config path in /etc/nginx/sites-available/rfp-system
# Uncomment the ssl_certificate lines and update domain
```

## Operations and Management

### Check Service Status

```bash
sudo systemctl status rfp-system
```

### View Real-Time Logs

```bash
sudo journalctl -u rfp-system -f
```

### View Specific Error Logs

```bash
# Last 50 errors
sudo journalctl -u rfp-system -p err -n 50

# Logs from today
sudo journalctl -u rfp-system --since today

# Last 100 lines
sudo journalctl -u rfp-system -n 100
```

### Restart Service

```bash
sudo systemctl restart rfp-system
```

### Stop Service

```bash
sudo systemctl stop rfp-system
```

### Update Code

```bash
cd /opt/rfp-system
sudo -u rfp-system git pull origin main
sudo systemctl restart rfp-system
```

## Health Monitoring

### API Health Check

```bash
# Local check
curl http://localhost:8000/health

# Remote check
curl https://rfp-api.yourcompany.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "RFP Processing API",
  "version": "1.0.0",
  "vector_db_ready": true
}
```

### System Monitoring

```bash
# Use the monitoring script
chmod +x /opt/rfp-system/monitor-rfp-system.sh
./monitor-rfp-system.sh
```

Check:
- Service running status
- Port 8000 listening
- Disk space usage
- Recent errors
- System resources (CPU, memory)

### Performance Metrics

Monitor these key metrics:

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Response Time (P50) | <2s | >5s | >10s |
| Response Time (P99) | <5s | >10s | >20s |
| Error Rate | <0.1% | >1% | >5% |
| CPU Usage | <50% | >80% | >95% |
| Memory Usage | <60% | >80% | >95% |
| Disk Space | >20% free | <10% free | <5% free |

## Database & Data Management

### FAISS Vector Database

The FAISS database stores SKU embeddings for semantic matching:

```bash
# Check database location
ls -lh /opt/rfp-system/data/faiss_db/

# Backup FAISS database
sudo cp -r /opt/rfp-system/data/faiss_db /backup/faiss_db_$(date +%Y%m%d)

# Monitor database size
du -sh /opt/rfp-system/data/faiss_db/
```

### Log Rotation

Create `/etc/logrotate.d/rfp-system`:

```
/var/log/rfp-system/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 rfp-system rfp-system
    sharedscripts
    postrotate
        systemctl reload rfp-system > /dev/null 2>&1 || true
    endscript
}
```

Apply with: `sudo logrotate -f /etc/logrotate.d/rfp-system`

## Backup Strategy

### Create Backup Script

Create `/opt/rfp-system/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/rfp-system"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup FAISS database
tar -czf $BACKUP_DIR/faiss_db_$DATE.tar.gz /opt/rfp-system/data/faiss_db/

# Backup configuration
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /opt/rfp-system/.env /opt/rfp-system/requirements.txt

# Keep only last 7 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

### Schedule Automated Backups

Add to crontab: `sudo crontab -e`

```cron
# Daily backup at 2 AM
0 2 * * * /opt/rfp-system/backup.sh
```

## Troubleshooting

### Service won't start

```bash
# Check logs
sudo journalctl -u rfp-system -n 50 --no-pager

# Test manually
cd /opt/rfp-system
. venv/bin/activate
python -m backend.api.main

# Check Python environment
/opt/rfp-system/venv/bin/python -c "import backend.api.main; print('OK')"
```

### API responds with 502 Bad Gateway

```bash
# Check if backend is running
sudo systemctl status rfp-system

# Check port
netstat -tlnp | grep 8000

# Restart service
sudo systemctl restart rfp-system

# Check error logs
sudo journalctl -u rfp-system -p err -n 20
```

### High Memory Usage

```bash
# Check which process is using memory
sudo top -u rfp-system

# Check FAISS database size
du -sh /opt/rfp-system/data/faiss_db/

# Restart service (memory may be leaking)
sudo systemctl restart rfp-system
```

### Slow RFP Processing

```bash
# Check API logs for bottleneck
sudo journalctl -u rfp-system --since "5 minutes ago" | grep -i "duration\|timeout"

# Monitor during request
watch -n 1 'top -u rfp-system -b -n 1'

# Increase workers (in systemd service)
# API_WORKERS=8
```

## Security Hardening

### Firewall Setup

```bash
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp  # If internal only
```

### SSH Key Authentication

```bash
# Disable password auth
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl reload sshd
```

### API Authentication (Optional)

Add API key validation to `backend/api/main.py`:

```python
@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        api_key = request.headers.get("X-API-Key")
        if api_key != os.getenv("API_KEY_SECRET"):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
    return await call_next(request)
```

### Rate Limiting (Optional)

Install slowapi: `pip install slowapi`

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/rfp/process")
@limiter.limit("10/minute")
async def process_rfp(request: Request, rfp_data: dict):
    ...
```

## Scaling & Performance

### Multiple Workers

For high load, use Gunicorn with more workers:

```bash
# In systemd service, increase:
API_WORKERS=8  # or more based on CPU cores

# Or in deploy command:
gunicorn --workers 8 --worker-class uvicorn.workers.UvicornWorker ...
```

### Load Balancing

For multi-server setup, use Nginx load balancer:

```nginx
upstream rfp_backend {
    server backend1.internal:8000;
    server backend2.internal:8000;
    server backend3.internal:8000;
    keepalive 32;
}

server {
    location /api/ {
        proxy_pass http://rfp_backend;
    }
}
```

### Caching

Add Redis caching layer (optional):

```bash
# Install Redis
sudo apt install -y redis-server

# Add to your code:
REDIS_URL=redis://localhost:6379/0
```

## Monitoring & Alerting (Optional)

### Setup Prometheus Metrics

Add to your FastAPI app for monitoring dashboards.

### Setup Sentry Error Tracking

```bash
# Install
pip install sentry-sdk

# Configure
SENTRY_DSN=https://key@sentry.io/project_id
```

## Support & Documentation

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Health Check**: http://localhost:8000/health
- **Logs**: `sudo journalctl -u rfp-system -f`
- **Status**: `sudo systemctl status rfp-system`

## Next Steps

1. **Test the deployment**: Use the test RFP script
2. **Monitor performance**: Track API response times
3. **Setup backups**: Automate FAISS DB backups
4. **Configure alerts**: Monitor critical metrics
5. **Plan scaling**: Add load balancing if needed

---

**Last Updated**: 2026-02-21
**Version**: 1.0.0
