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
