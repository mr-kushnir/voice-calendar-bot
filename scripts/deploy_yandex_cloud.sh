#!/bin/bash
# Deploy Voice Calendar Bot to Yandex Cloud

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================="
echo "Yandex Cloud Deployment Script"
echo "Voice Calendar Telegram Bot"
echo "=================================="
echo ""

# Check if yc CLI is installed
if ! command -v yc &> /dev/null; then
    echo -e "${RED}ERROR: Yandex Cloud CLI (yc) is not installed${NC}"
    echo "Install it from: https://cloud.yandex.ru/docs/cli/quickstart"
    exit 1
fi

# Configuration
FOLDER_ID="${YC_FOLDER_ID:-}"
VM_NAME="voice-calendar-bot"
ZONE="ru-central1-a"
SUBNET_ID="${YC_SUBNET_ID:-}"
SERVICE_ACCOUNT_ID="${YC_SERVICE_ACCOUNT_ID:-}"
IMAGE_FAMILY="ubuntu-2204-lts"
PLATFORM="standard-v3"
CORES=2
MEMORY=2
DISK_SIZE=20

# Check required environment variables
if [ -z "$FOLDER_ID" ]; then
    echo -e "${RED}ERROR: YC_FOLDER_ID environment variable is not set${NC}"
    exit 1
fi

if [ -z "$SUBNET_ID" ]; then
    echo -e "${RED}ERROR: YC_SUBNET_ID environment variable is not set${NC}"
    exit 1
fi

echo -e "${GREEN}Step 1: Building Docker image${NC}"
docker build -t voice-calendar-bot:latest .

echo ""
echo -e "${GREEN}Step 2: Exporting Docker image${NC}"
docker save voice-calendar-bot:latest -o voice-calendar-bot.tar

echo ""
echo -e "${GREEN}Step 3: Compressing Docker image${NC}"
gzip -f voice-calendar-bot.tar

echo ""
echo -e "${GREEN}Step 4: Checking if VM exists${NC}"
VM_ID=$(yc compute instance list --folder-id=$FOLDER_ID --format=json | \
    jq -r ".[] | select(.name==\"$VM_NAME\") | .id")

if [ -n "$VM_ID" ]; then
    echo -e "${YELLOW}VM $VM_NAME already exists (ID: $VM_ID)${NC}"
    echo -e "${YELLOW}Stopping existing VM...${NC}"
    yc compute instance stop $VM_ID --folder-id=$FOLDER_ID
    echo -e "${YELLOW}Deleting existing VM...${NC}"
    yc compute instance delete $VM_ID --folder-id=$FOLDER_ID
fi

echo ""
echo -e "${GREEN}Step 5: Creating VM instance${NC}"

# Create cloud-init config
cat > cloud-init.yaml <<EOF
#cloud-config
package_update: true
package_upgrade: true

packages:
  - docker.io
  - docker-compose

runcmd:
  - systemctl start docker
  - systemctl enable docker
  - usermod -aG docker ubuntu
EOF

# Create VM
yc compute instance create \
    --name=$VM_NAME \
    --folder-id=$FOLDER_ID \
    --zone=$ZONE \
    --platform=$PLATFORM \
    --cores=$CORES \
    --memory=${MEMORY}GB \
    --create-boot-disk size=${DISK_SIZE}GB,image-family=$IMAGE_FAMILY \
    --network-interface subnet-id=$SUBNET_ID,nat-ip-version=ipv4 \
    --ssh-key ~/.ssh/id_rsa.pub \
    --metadata-from-file user-data=cloud-init.yaml

echo ""
echo -e "${GREEN}Step 6: Waiting for VM to start${NC}"
sleep 30

# Get VM IP
VM_IP=$(yc compute instance list --folder-id=$FOLDER_ID --format=json | \
    jq -r ".[] | select(.name==\"$VM_NAME\") | .network_interfaces[0].primary_v4_address.one_to_one_nat.address")

echo -e "${GREEN}VM IP Address: $VM_IP${NC}"

echo ""
echo -e "${GREEN}Step 7: Copying files to VM${NC}"
scp -o StrictHostKeyChecking=no voice-calendar-bot.tar.gz ubuntu@$VM_IP:/tmp/
scp -o StrictHostKeyChecking=no .env ubuntu@$VM_IP:/tmp/
scp -o StrictHostKeyChecking=no docker-compose.yml ubuntu@$VM_IP:/tmp/

echo ""
echo -e "${GREEN}Step 8: Setting up application on VM${NC}"
ssh -o StrictHostKeyChecking=no ubuntu@$VM_IP << 'ENDSSH'
set -e

echo "Loading Docker image..."
cd /tmp
gunzip voice-calendar-bot.tar.gz
sudo docker load -i voice-calendar-bot.tar

echo "Creating application directory..."
sudo mkdir -p /opt/voice-calendar-bot
sudo mv docker-compose.yml /opt/voice-calendar-bot/
sudo mv .env /opt/voice-calendar-bot/
cd /opt/voice-calendar-bot

echo "Creating systemd service..."
sudo tee /etc/systemd/system/voice-calendar-bot.service > /dev/null <<EOF
[Unit]
Description=Voice Calendar Telegram Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/voice-calendar-bot
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

echo "Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable voice-calendar-bot
sudo systemctl start voice-calendar-bot

echo "Checking service status..."
sudo systemctl status voice-calendar-bot --no-pager

echo "Checking Docker containers..."
sudo docker-compose ps
ENDSSH

echo ""
echo -e "${GREEN}=================================="
echo -e "✅ Deployment Complete!"
echo -e "==================================${NC}"
echo ""
echo -e "${GREEN}VM Information:${NC}"
echo -e "  Name: $VM_NAME"
echo -e "  IP: $VM_IP"
echo ""
echo -e "${GREEN}Useful commands:${NC}"
echo -e "  SSH to VM:    ssh ubuntu@$VM_IP"
echo -e "  View logs:    ssh ubuntu@$VM_IP 'cd /opt/voice-calendar-bot && sudo docker-compose logs -f'"
echo -e "  Restart bot:  ssh ubuntu@$VM_IP 'cd /opt/voice-calendar-bot && sudo docker-compose restart'"
echo -e "  Stop bot:     ssh ubuntu@$VM_IP 'cd /opt/voice-calendar-bot && sudo docker-compose down'"
echo ""

# Cleanup
rm -f cloud-init.yaml voice-calendar-bot.tar.gz

echo -e "${GREEN}Done!${NC}"
