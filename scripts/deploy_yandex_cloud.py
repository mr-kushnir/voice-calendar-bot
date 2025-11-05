"""Deploy Voice Calendar Bot to Yandex Cloud"""
import os
import sys
import subprocess
import json
import time
from pathlib import Path
from loguru import logger

# Configuration
FOLDER_ID = os.getenv("YC_FOLDER_ID")
SUBNET_ID = os.getenv("YC_SUBNET_ID")
SERVICE_ACCOUNT_ID = os.getenv("YC_SERVICE_ACCOUNT_ID")
VM_NAME = "voice-calendar-bot"
ZONE = "ru-central1-a"
IMAGE_FAMILY = "ubuntu-2204-lts"
PLATFORM = "standard-v3"
CORES = 2
MEMORY = 2  # GB
DISK_SIZE = 20  # GB

# Project root
PROJECT_ROOT = Path(__file__).parent.parent


def run_command(cmd, shell=False, check=True):
    """Run shell command"""
    logger.info(f"Running: {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        shell=shell,
        check=check,
        capture_output=True,
        text=True
    )
    if result.stdout:
        logger.debug(result.stdout)
    if result.stderr and result.returncode != 0:
        logger.error(result.stderr)
    return result


def check_prerequisites():
    """Check if all prerequisites are met"""
    logger.info("Checking prerequisites...")

    # Check yc CLI
    try:
        result = run_command(["yc", "version"], check=False)
        if result.returncode != 0:
            logger.error("Yandex Cloud CLI (yc) is not installed")
            logger.error("Install from: https://cloud.yandex.ru/docs/cli/quickstart")
            sys.exit(1)
        logger.info(f"✅ Yandex Cloud CLI installed: {result.stdout.strip()}")
    except FileNotFoundError:
        logger.error("Yandex Cloud CLI (yc) not found")
        sys.exit(1)

    # Check Docker
    try:
        result = run_command(["docker", "version"], check=False)
        if result.returncode != 0:
            logger.error("Docker is not installed or not running")
            sys.exit(1)
        logger.info("✅ Docker is available")
    except FileNotFoundError:
        logger.error("Docker not found")
        sys.exit(1)

    # Check environment variables
    if not FOLDER_ID:
        logger.error("YC_FOLDER_ID environment variable is not set")
        sys.exit(1)
    logger.info(f"✅ Folder ID: {FOLDER_ID}")

    if not SUBNET_ID:
        logger.error("YC_SUBNET_ID environment variable is not set")
        sys.exit(1)
    logger.info(f"✅ Subnet ID: {SUBNET_ID}")

    # Check .env file
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        logger.error(".env file not found")
        sys.exit(1)
    logger.info("✅ .env file found")


def build_docker_image():
    """Build Docker image"""
    logger.info("Building Docker image...")
    os.chdir(PROJECT_ROOT)
    run_command(["docker", "build", "-t", "voice-calendar-bot:latest", "."])
    logger.info("✅ Docker image built successfully")


def get_existing_vm():
    """Check if VM already exists"""
    logger.info(f"Checking for existing VM: {VM_NAME}")
    result = run_command(
        ["yc", "compute", "instance", "list",
         f"--folder-id={FOLDER_ID}", "--format=json"],
        check=False
    )

    if result.returncode == 0 and result.stdout:
        vms = json.loads(result.stdout)
        for vm in vms:
            if vm.get("name") == VM_NAME:
                vm_id = vm.get("id")
                logger.warning(f"VM {VM_NAME} already exists (ID: {vm_id})")
                return vm_id

    return None


def delete_existing_vm(vm_id):
    """Delete existing VM"""
    logger.info(f"Stopping VM {vm_id}...")
    run_command(
        ["yc", "compute", "instance", "stop", vm_id,
         f"--folder-id={FOLDER_ID}"],
        check=False
    )

    logger.info(f"Deleting VM {vm_id}...")
    run_command(
        ["yc", "compute", "instance", "delete", vm_id,
         f"--folder-id={FOLDER_ID}"]
    )
    logger.info("✅ Existing VM deleted")


def create_cloud_init_config():
    """Create cloud-init configuration"""
    cloud_init = """#cloud-config
package_update: true
package_upgrade: true

packages:
  - docker.io
  - docker-compose

runcmd:
  - systemctl start docker
  - systemctl enable docker
  - usermod -aG docker ubuntu
"""

    cloud_init_file = PROJECT_ROOT / "cloud-init.yaml"
    cloud_init_file.write_text(cloud_init)
    logger.info("✅ Cloud-init config created")
    return cloud_init_file


def create_vm(cloud_init_file):
    """Create VM instance"""
    logger.info("Creating VM instance...")

    ssh_key_path = Path.home() / ".ssh" / "id_rsa.pub"
    if not ssh_key_path.exists():
        logger.error(f"SSH key not found: {ssh_key_path}")
        logger.error("Generate with: ssh-keygen -t rsa -b 4096")
        sys.exit(1)

    cmd = [
        "yc", "compute", "instance", "create",
        f"--name={VM_NAME}",
        f"--folder-id={FOLDER_ID}",
        f"--zone={ZONE}",
        f"--platform={PLATFORM}",
        f"--cores={CORES}",
        f"--memory={MEMORY}GB",
        f"--create-boot-disk=size={DISK_SIZE}GB,image-family={IMAGE_FAMILY}",
        f"--network-interface=subnet-id={SUBNET_ID},nat-ip-version=ipv4",
        f"--ssh-key={ssh_key_path}",
        f"--metadata-from-file=user-data={cloud_init_file}"
    ]

    run_command(cmd)
    logger.info("✅ VM created successfully")


def get_vm_ip():
    """Get VM IP address"""
    logger.info("Getting VM IP address...")
    result = run_command(
        ["yc", "compute", "instance", "list",
         f"--folder-id={FOLDER_ID}", "--format=json"]
    )

    vms = json.loads(result.stdout)
    for vm in vms:
        if vm.get("name") == VM_NAME:
            ip = vm["network_interfaces"][0]["primary_v4_address"]["one_to_one_nat"]["address"]
            logger.info(f"✅ VM IP: {ip}")
            return ip

    logger.error("Could not find VM IP")
    sys.exit(1)


def wait_for_vm(ip, timeout=120):
    """Wait for VM to be ready"""
    logger.info("Waiting for VM to be ready...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        result = run_command(
            ["ssh", "-o", "StrictHostKeyChecking=no",
             "-o", "ConnectTimeout=5",
             f"ubuntu@{ip}", "echo", "ready"],
            check=False
        )

        if result.returncode == 0:
            logger.info("✅ VM is ready")
            return True

        logger.debug("VM not ready yet, waiting...")
        time.sleep(5)

    logger.error(f"VM did not become ready within {timeout} seconds")
    return False


def export_docker_image():
    """Export Docker image"""
    logger.info("Exporting Docker image...")
    image_file = PROJECT_ROOT / "voice-calendar-bot.tar"

    run_command(
        ["docker", "save", "voice-calendar-bot:latest", "-o", str(image_file)]
    )
    logger.info("✅ Docker image exported")
    return image_file


def deploy_to_vm(ip, image_file):
    """Deploy application to VM"""
    logger.info("Deploying application to VM...")

    # Copy files
    logger.info("Copying files to VM...")
    run_command([
        "scp", "-o", "StrictHostKeyChecking=no",
        str(image_file),
        f"ubuntu@{ip}:/tmp/"
    ])

    run_command([
        "scp", "-o", "StrictHostKeyChecking=no",
        str(PROJECT_ROOT / ".env"),
        f"ubuntu@{ip}:/tmp/"
    ])

    run_command([
        "scp", "-o", "StrictHostKeyChecking=no",
        str(PROJECT_ROOT / "docker-compose.yml"),
        f"ubuntu@{ip}:/tmp/"
    ])

    # Setup on VM
    logger.info("Setting up application on VM...")
    setup_script = """
set -e

echo "Loading Docker image..."
cd /tmp
sudo docker load -i voice-calendar-bot.tar

echo "Creating application directory..."
sudo mkdir -p /opt/voice-calendar-bot
sudo mv docker-compose.yml /opt/voice-calendar-bot/
sudo mv .env /opt/voice-calendar-bot/
cd /opt/voice-calendar-bot

echo "Creating systemd service..."
sudo tee /etc/systemd/system/voice-calendar-bot.service > /dev/null <<'EOF'
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

echo "Service status:"
sudo systemctl status voice-calendar-bot --no-pager

echo "Docker containers:"
sudo docker-compose ps
"""

    run_command([
        "ssh", "-o", "StrictHostKeyChecking=no",
        f"ubuntu@{ip}",
        setup_script
    ])

    logger.info("✅ Application deployed successfully")


def cleanup(cloud_init_file, image_file):
    """Cleanup temporary files"""
    logger.info("Cleaning up...")

    if cloud_init_file and cloud_init_file.exists():
        cloud_init_file.unlink()

    if image_file and image_file.exists():
        image_file.unlink()

    logger.info("✅ Cleanup complete")


def main():
    """Main deployment function"""
    logger.info("=" * 60)
    logger.info("Yandex Cloud Deployment Script")
    logger.info("Voice Calendar Telegram Bot")
    logger.info("=" * 60)

    cloud_init_file = None
    image_file = None

    try:
        # Step 1: Check prerequisites
        check_prerequisites()

        # Step 2: Build Docker image
        build_docker_image()

        # Step 3: Export Docker image
        image_file = export_docker_image()

        # Step 4: Check and delete existing VM
        vm_id = get_existing_vm()
        if vm_id:
            delete_existing_vm(vm_id)
            time.sleep(10)

        # Step 5: Create cloud-init config
        cloud_init_file = create_cloud_init_config()

        # Step 6: Create VM
        create_vm(cloud_init_file)

        # Step 7: Wait for VM to start
        time.sleep(30)

        # Step 8: Get VM IP
        vm_ip = get_vm_ip()

        # Step 9: Wait for VM to be ready
        if not wait_for_vm(vm_ip):
            logger.error("VM did not become ready")
            sys.exit(1)

        # Step 10: Deploy to VM
        deploy_to_vm(vm_ip, image_file)

        # Success
        logger.info("=" * 60)
        logger.info("✅ Deployment Complete!")
        logger.info("=" * 60)
        logger.info(f"\nVM IP: {vm_ip}")
        logger.info(f"\nUseful commands:")
        logger.info(f"  SSH:        ssh ubuntu@{vm_ip}")
        logger.info(f"  Logs:       ssh ubuntu@{vm_ip} 'cd /opt/voice-calendar-bot && sudo docker-compose logs -f'")
        logger.info(f"  Restart:    ssh ubuntu@{vm_ip} 'cd /opt/voice-calendar-bot && sudo docker-compose restart'")
        logger.info(f"  Stop:       ssh ubuntu@{vm_ip} 'cd /opt/voice-calendar-bot && sudo docker-compose down'")

    except KeyboardInterrupt:
        logger.warning("\nDeployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        sys.exit(1)
    finally:
        cleanup(cloud_init_file, image_file)


if __name__ == "__main__":
    main()
