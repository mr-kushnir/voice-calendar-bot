"""Deployment script for Voice Calendar Bot"""
import os
import sys
import subprocess
from pathlib import Path
from loguru import logger


class Deployer:
    """Deployer for Voice Calendar Bot"""

    def __init__(self, project_root: Path):
        """
        Initialize deployer

        Args:
            project_root: Path to project root
        """
        self.project_root = project_root
        logger.info(f"Deployer initialized (project root: {project_root})")

    def run(self):
        """Run deployment"""
        logger.info("="*60)
        logger.info("🚀 Voice Calendar Bot Deployment")
        logger.info("="*60)

        try:
            # Step 1: Check environment
            logger.info("\n📋 Step 1: Checking environment...")
            self._check_environment()

            # Step 2: Install dependencies
            logger.info("\n📦 Step 2: Installing dependencies...")
            self._install_dependencies()

            # Step 3: Run tests
            logger.info("\n🧪 Step 3: Running tests...")
            self._run_tests()

            # Step 4: Check coverage
            logger.info("\n📊 Step 4: Checking coverage...")
            self._check_coverage()

            # Step 5: Deploy
            logger.info("\n🚀 Step 5: Deploying...")
            self._deploy()

            logger.info("\n" + "="*60)
            logger.info("✅ Deployment completed successfully!")
            logger.info("="*60)

        except Exception as e:
            logger.error(f"\n❌ Deployment failed: {e}")
            sys.exit(1)

    def _check_environment(self):
        """Check environment variables"""
        required_vars = [
            "TELEGRAM_BOT_TOKEN",
            "OPENAI_API_KEY",
            "ELEVENLABS_API_KEY",
            "YANDEX_CALENDAR_LOGIN",
            "YANDEX_CALENDAR_PASSWORD"
        ]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            raise Exception(f"Missing required environment variables: {', '.join(missing_vars)}")

        logger.info("✅ All required environment variables are set")

        # Check Python version
        py_version = sys.version_info
        if py_version.major < 3 or (py_version.major == 3 and py_version.minor < 11):
            raise Exception(f"Python 3.11+ required, found {py_version.major}.{py_version.minor}")

        logger.info(f"✅ Python version: {py_version.major}.{py_version.minor}.{py_version.micro}")

    def _install_dependencies(self):
        """Install dependencies"""
        requirements_file = self.project_root / "requirements.txt"

        if not requirements_file.exists():
            raise Exception("requirements.txt not found")

        logger.info("Installing from requirements.txt...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise Exception(f"Failed to install dependencies: {result.stderr}")

        logger.info("✅ Dependencies installed")

    def _run_tests(self):
        """Run tests"""
        logger.info("Running pytest...")

        result = subprocess.run(
            ["pytest", "tests/unit/", "-v"],
            cwd=str(self.project_root),
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logger.error(f"Tests failed:\n{result.stdout}\n{result.stderr}")
            raise Exception("Tests failed")

        logger.info("✅ All tests passed")

    def _check_coverage(self):
        """Check test coverage"""
        logger.info("Checking coverage...")

        result = subprocess.run(
            ["pytest", "tests/unit/", "--cov=src", "--cov-report=term-missing"],
            cwd=str(self.project_root),
            capture_output=True,
            text=True
        )

        output = result.stdout + result.stderr

        # Extract coverage
        coverage = None
        for line in output.split('\n'):
            if 'TOTAL' in line and '%' in line:
                parts = line.split()
                for part in parts:
                    if '%' in part:
                        coverage = int(part.replace('%', ''))
                        break

        if coverage is None:
            raise Exception("Could not determine coverage")

        logger.info(f"Coverage: {coverage}%")

        if coverage < 80:
            raise Exception(f"Coverage {coverage}% is below threshold of 80%")

        logger.info("✅ Coverage meets threshold")

    def _deploy(self):
        """Deploy application"""
        logger.info("Deploying application...")

        # Create necessary directories
        logs_dir = self.project_root / "logs"
        logs_dir.mkdir(exist_ok=True)

        # Check if bot can be imported
        try:
            import src.main
            logger.info("✅ Main module imports successfully")
        except Exception as e:
            raise Exception(f"Failed to import main module: {e}")

        logger.info("✅ Application ready to run")

        # Print run instructions
        logger.info("\n" + "="*60)
        logger.info("📝 To run the bot:")
        logger.info("   python -m src.main")
        logger.info("\n📝 To run Test Agent:")
        logger.info("   python scripts/run_test_agent.py")
        logger.info("="*60)


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent

    # Check if .env exists
    env_file = project_root / ".env"
    if not env_file.exists():
        logger.error("❌ .env file not found")
        logger.error("Please copy .env.example to .env and fill in your credentials")
        sys.exit(1)

    # Load .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        logger.error("❌ python-dotenv not installed")
        logger.error("Run: pip install python-dotenv")
        sys.exit(1)

    # Run deployment
    deployer = Deployer(project_root)
    deployer.run()


if __name__ == "__main__":
    main()
