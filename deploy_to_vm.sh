#!/bin/bash
# Automated deployment to Yandex Cloud VM

set -e

VM_NAME="claude-code-vm"
VM_IP="89.169.131.111"

echo "=== Deploying to Yandex Cloud VM ==="
echo "VM: $VM_NAME ($VM_IP)"
echo ""

# Step 1: Copy files to VM
echo "Step 1: Copying files to VM..."

# Create temp directory on VM
yc compute ssh --name $VM_NAME -- "sudo mkdir -p /tmp/bot-deploy && sudo chmod 777 /tmp/bot-deploy"

# Copy Docker image
echo "  Copying Docker image (this may take a few minutes)..."
scp -o StrictHostKeyChecking=no voice-calendar-bot.tar ubuntu@$VM_IP:/tmp/bot-deploy/

# Copy configs
echo "  Copying configuration files..."
scp -o StrictHostKeyChecking=no .env ubuntu@$VM_IP:/tmp/bot-deploy/
scp -o StrictHostKeyChecking=no docker-compose.yml ubuntu@$VM_IP:/tmp/bot-deploy/

echo "  Files copied successfully!"

# Step 2: Setup on VM
echo ""
echo "Step 2: Setting up application on VM..."

yc compute ssh --name $VM_NAME -- << 'EOF'
set -e

echo "Installing Docker..."
if ! command -v docker &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y docker.io docker-compose
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
fi

echo "Loading Docker image..."
cd /tmp/bot-deploy
sudo docker load -i voice-calendar-bot.tar

echo "Creating application directory..."
sudo mkdir -p /opt/voice-calendar-bot
sudo cp .env /opt/voice-calendar-bot/
sudo cp docker-compose.yml /opt/voice-calendar-bot/
cd /opt/voice-calendar-bot

echo "Starting bot..."
sudo docker-compose down 2>/dev/null || true
sudo docker-compose up -d

echo "Checking status..."
sudo docker-compose ps

echo "Creating systemd service..."
sudo tee /etc/systemd/system/voice-calendar-bot.service > /dev/null <<'SYSTEMD'
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
SYSTEMD

sudo systemctl daemon-reload
sudo systemctl enable voice-calendar-bot

echo "Deployment complete!"
EOF

echo ""
echo "=== Deployment Complete ==="
echo "Bot is running on VM: $VM_IP"
echo ""
echo "To check logs:"
echo "  yc compute ssh --name $VM_NAME -- 'cd /opt/voice-calendar-bot && sudo docker-compose logs -f'"
