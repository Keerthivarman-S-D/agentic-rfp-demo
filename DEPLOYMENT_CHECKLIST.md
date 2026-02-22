# RFP System - Deployment Checklist

## Pre-Deployment Verification

- [ ] All code committed to Git
- [ ] `requirements.txt` is up to date
- [ ] `.env.production` template reviewed
- [ ] Google Gemini API key obtained
- [ ] Domain name and DNS configured
- [ ] Server provisioned and accessible

## Automated Deployment (Recommended)

```bash
# 1. SSH into your server
ssh ubuntu@your-server-ip

# 2. Download and run deployment script
sudo bash -c 'cd /tmp && git clone https://github.com/yourorg/agentic-rfp-demo.git && cd agentic-rfp-demo && chmod +x deploy-production.sh && ./deploy-production.sh'

# 3. Configure environment
sudo nano /opt/rfp-system/.env
# Add: GOOGLE_API_KEY=your_api_key_here

# 4. Start service
sudo systemctl start rfp-system
sudo systemctl enable rfp-system
```

## Deployment Steps

### Quick Verification

- [ ] Service running: `sudo systemctl status rfp-system`
- [ ] Health check passes: `curl http://localhost:8000/health`
- [ ] API responds: `curl http://localhost:8000/docs`
- [ ] No errors in logs: `sudo journalctl -u rfp-system | grep -i error`

### Post-Deployment

- [ ] Test RFP processing: `curl -X POST http://localhost:8000/api/rfp/process -d @test_rfp.json`
- [ ] Monitor service: Run `./monitor-rfp-system.sh`
- [ ] Setup log rotation: Configure logrotate
- [ ] Schedule backups: Add cron job for FAISS DB
- [ ] Configure monitoring: Sentry or equivalent (optional)

## Alternative Deployments

### Docker Deployment

```bash
# Build image
docker build -t rfp-system:latest .

# Run container
docker run -p 8000:8000 \
  -e GOOGLE_API_KEY=your_api_key \
  -v $(pwd)/data:/app/data \
  rfp-system:latest
```

### Docker Compose (Development)

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f rfp-system

# Stop services
docker-compose down
```

## Troubleshooting Commands

```bash
# Check service status
sudo systemctl status rfp-system

# View detailed logs
sudo journalctl -u rfp-system -n 100

# Check if port is listening
netstat -tlnp | grep 8000

# Test API connectivity
curl -v http://localhost:8000/health

# Monitor resource usage
watch -n 1 'top -u rfp-system -b -n 1'

# Restart service
sudo systemctl restart rfp-system
```

## Important Files Locations

| File | Location | Purpose |
|------|----------|---------|
| Application | `/opt/rfp-system` | Main application code |
| Environment | `/opt/rfp-system/.env` | Configuration and secrets |
| Service | `/etc/systemd/system/rfp-system.service` | Systemd service definition |
| Nginx Config | `/etc/nginx/sites-available/rfp-system` | Reverse proxy configuration |
| Logs | `/var/log/rfp-system/` | Application and system logs |
| Data | `/opt/rfp-system/data/` | FAISS database and cache |

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Service won't start | Check logs: `sudo journalctl -u rfp-system` |
| 502 Bad Gateway | Restart service: `sudo systemctl restart rfp-system` |
| High memory usage | Check FAISS DB size, restart service |
| Slow responses | Increase workers: `API_WORKERS=8` in .env |
| API key error | Verify `GOOGLE_API_KEY` in `.env` is set correctly |

## Monitoring & Support

### Health Check
```bash
./monitor-rfp-system.sh
```

### View Real-Time Logs
```bash
sudo journalctl -u rfp-system -f
```

### API Documentation
- Visit: `http://your-server:8000/docs`
- Swagger UI with all endpoints

## Next Steps

1. **Test deployment** - Run test RFPs through the system
2. **Setup monitoring** - Track performance metrics
3. **Configure backups** - Automate FAISS DB backups
4. **Load test** - Validate performance under load
5. **Production cutover** - Enable monitoring and alerts

---

**Deployment Status**: Ready for Production
**Last Updated**: 2026-02-21
