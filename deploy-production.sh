#!/bin/bash
# ==================== RFP SYSTEM DEPLOYMENT SCRIPT ====================
# Usage: ./deploy-production.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_DIR="/opt/rfp-system"
REPO_URL="https://github.com/yourorg/agentic-rfp-demo.git"
REPO_BRANCH="main"
SERVICE_NAME="rfp-system"
PORT=8000

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}RFP System - Production Deployment${NC}"
echo -e "${YELLOW}========================================${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
   echo -e "${RED}ERROR: This script must be run as root${NC}"
   exit 1
fi

# Step 1: Create system user
echo -e "\n${YELLOW}[1/7] Setting up system user...${NC}"
if ! id -u $SERVICE_NAME > /dev/null 2>&1; then
    useradd -r -s /bin/bash -d $DEPLOY_DIR $SERVICE_NAME
    echo -e "${GREEN}✓ User '$SERVICE_NAME' created${NC}"
else
    echo -e "${GREEN}✓ User '$SERVICE_NAME' already exists${NC}"
fi

# Step 2: Create directories
echo -e "\n${YELLOW}[2/7] Creating directories...${NC}"
mkdir -p $DEPLOY_DIR/data $DEPLOY_DIR/logs
mkdir -p /var/log/rfp-system
chown -R $SERVICE_NAME:$SERVICE_NAME $DEPLOY_DIR /var/log/rfp-system
echo -e "${GREEN}✓ Directories created${NC}"

# Step 3: Clone or update repository
echo -e "\n${YELLOW}[3/7] Cloning/updating repository...${NC}"
if [ -d "$DEPLOY_DIR/.git" ]; then
    cd $DEPLOY_DIR
    sudo -u $SERVICE_NAME git fetch origin
    sudo -u $SERVICE_NAME git checkout $REPO_BRANCH
    sudo -u $SERVICE_NAME git pull origin $REPO_BRANCH
    echo -e "${GREEN}✓ Repository updated${NC}"
else
    git clone -b $REPO_BRANCH $REPO_URL $DEPLOY_DIR
    chown -R $SERVICE_NAME:$SERVICE_NAME $DEPLOY_DIR
    echo -e "${GREEN}✓ Repository cloned${NC}"
fi

# Step 4: Setup Python environment
echo -e "\n${YELLOW}[4/7] Setting up Python virtual environment...${NC}"
cd $DEPLOY_DIR
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Upgrade pip and install dependencies
sudo -u $SERVICE_NAME ./venv/bin/pip install --upgrade pip setuptools wheel
sudo -u $SERVICE_NAME ./venv/bin/pip install -r requirements.txt
sudo -u $SERVICE_NAME ./venv/bin/pip install gunicorn uvicorn

echo -e "${GREEN}✓ Dependencies installed${NC}"

# Step 5: Copy environment file
echo -e "\n${YELLOW}[5/7] Configuring environment...${NC}"
if [ ! -f "$DEPLOY_DIR/.env.production" ]; then
    echo -e "${RED}ERROR: .env.production not found${NC}"
    echo "Please copy .env.production to $DEPLOY_DIR and configure it"
    exit 1
fi
cp $DEPLOY_DIR/.env.production $DEPLOY_DIR/.env
chown $SERVICE_NAME:$SERVICE_NAME $DEPLOY_DIR/.env
chmod 600 $DEPLOY_DIR/.env
echo -e "${GREEN}✓ Environment configured${NC}"

# Step 6: Install systemd service
echo -e "\n${YELLOW}[6/7] Installing systemd service...${NC}"
cp $DEPLOY_DIR/rfp-system.service /etc/systemd/system/
systemctl daemon-reload
echo -e "${GREEN}✓ Service installed${NC}"

# Step 7: Setup nginx (optional)
echo -e "\n${YELLOW}[7/7] Setting up nginx reverse proxy...${NC}"
if command -v nginx &> /dev/null; then
    cp $DEPLOY_DIR/nginx-rfp-system.conf /etc/nginx/sites-available/rfp-system
    if [ ! -L /etc/nginx/sites-enabled/rfp-system ]; then
        ln -s /etc/nginx/sites-available/rfp-system /etc/nginx/sites-enabled/rfp-system
    fi
    nginx -t && systemctl reload nginx
    echo -e "${GREEN}✓ Nginx configured${NC}"
else
    echo -e "${YELLOW}⚠ Nginx not found, skipping${NC}"
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Review and update: $DEPLOY_DIR/.env"
echo "2. Start the service: sudo systemctl start $SERVICE_NAME"
echo "3. Enable on boot: sudo systemctl enable $SERVICE_NAME"
echo "4. Check status: sudo systemctl status $SERVICE_NAME"
echo "5. View logs: sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo -e "${YELLOW}Verify deployment:${NC}"
echo "curl http://localhost:8000/health"
echo ""
