# Automated deployment to Yandex Cloud VM
$ErrorActionPreference = "Stop"

$VM_NAME = "claude-code-vm"
$VM_IP = "89.169.131.111"

Write-Host "=== Deploying to Yandex Cloud VM ===" -ForegroundColor Green
Write-Host "VM: $VM_NAME ($VM_IP)"
Write-Host ""

# Check if Docker image exists
if (!(Test-Path "voice-calendar-bot.tar")) {
    Write-Host "Error: voice-calendar-bot.tar not found" -ForegroundColor Red
    Write-Host "Building Docker image first..."
    docker save voice-calendar-bot:latest -o voice-calendar-bot.tar
}

# Step 1: Install Docker on VM
Write-Host "Step 1: Preparing VM..." -ForegroundColor Cyan

$setupScript = @"
#!/bin/bash
set -e

echo 'Installing Docker if needed...'
if ! command -v docker &> /dev/null; then
    sudo apt-get update -qq
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y docker.io docker-compose
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker ubuntu
    echo 'Docker installed successfully'
else
    echo 'Docker already installed'
fi

sudo mkdir -p /tmp/bot-deploy
sudo chmod 777 /tmp/bot-deploy
"@

$setupScript | Out-File -FilePath "setup_vm.sh" -Encoding ASCII
scp -o StrictHostKeyChecking=no setup_vm.sh "ubuntu@${VM_IP}:/tmp/setup_vm.sh"
ssh -o StrictHostKeyChecking=no "ubuntu@${VM_IP}" "bash /tmp/setup_vm.sh"
Remove-Item "setup_vm.sh"

# Step 2: Copy files to VM
Write-Host ""
Write-Host "Step 2: Copying files to VM..." -ForegroundColor Cyan

Write-Host "  Copying Docker image (this may take a few minutes)..."
scp -o StrictHostKeyChecking=no voice-calendar-bot.tar "ubuntu@${VM_IP}:/tmp/bot-deploy/"

Write-Host "  Copying configuration files..."
scp -o StrictHostKeyChecking=no .env "ubuntu@${VM_IP}:/tmp/bot-deploy/"
scp -o StrictHostKeyChecking=no docker-compose.yml "ubuntu@${VM_IP}:/tmp/bot-deploy/"

Write-Host "  Files copied successfully!" -ForegroundColor Green

# Step 3: Deploy on VM
Write-Host ""
Write-Host "Step 3: Deploying application on VM..." -ForegroundColor Cyan

$deployScript = @"
#!/bin/bash
set -e

echo 'Loading Docker image...'
cd /tmp/bot-deploy
sudo docker load -i voice-calendar-bot.tar

echo 'Creating application directory...'
sudo mkdir -p /opt/voice-calendar-bot
sudo cp .env /opt/voice-calendar-bot/
sudo cp docker-compose.yml /opt/voice-calendar-bot/
cd /opt/voice-calendar-bot

echo 'Stopping old containers...'
sudo docker-compose down 2>/dev/null || true

echo 'Starting bot...'
sudo docker-compose up -d

echo 'Checking status...'
sudo docker-compose ps

echo 'Creating systemd service...'
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

echo ''
echo '=== Deployment Complete ==='
echo 'Bot is running!'
echo ''
echo 'To view logs:'
echo '  sudo docker-compose logs -f'
"@

$deployScript | Out-File -FilePath "deploy.sh" -Encoding ASCII
scp -o StrictHostKeyChecking=no deploy.sh "ubuntu@${VM_IP}:/tmp/deploy.sh"
ssh -o StrictHostKeyChecking=no "ubuntu@${VM_IP}" "bash /tmp/deploy.sh"
Remove-Item "deploy.sh"

Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host "Bot is running on VM: $VM_IP" -ForegroundColor Green
Write-Host ""
Write-Host "To check logs:" -ForegroundColor Yellow
Write-Host "  ssh ubuntu@$VM_IP 'cd /opt/voice-calendar-bot && sudo docker-compose logs -f'"
Write-Host ""
Write-Host "To check status:" -ForegroundColor Yellow
Write-Host "  ssh ubuntu@$VM_IP 'cd /opt/voice-calendar-bot && sudo docker-compose ps'"
