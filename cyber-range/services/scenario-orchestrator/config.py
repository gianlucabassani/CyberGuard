import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# DIRECTORIES - New Architecture
BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "scenarios"
BASE_TERRAFORM_TEMPLATE = BASE_DIR / "infra" / "terraform"

# Runtime directories (inside Docker containers)
RUNS_DIR = Path(os.getenv("RUNS_DIR", "/app/runs"))
DATA_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
KEYS_DIR = Path(os.getenv("KEYS_DIR", "/app/keys"))
CACHE_DIR = Path(os.getenv("CACHE_DIR", "/app/cache"))

# OPENSTACK CREDENTIALS
OS_USERNAME = os.getenv("OS_USERNAME")
OS_PASSWORD = os.getenv("OS_PASSWORD")
OS_PROJECT_ID = os.getenv("OS_PROJECT_ID", os.getenv("OS_TENANT_ID"))
OS_AUTH_URL = os.getenv("OS_AUTH_URL")
OS_REGION_NAME = os.getenv("OS_REGION_NAME", "RegionOne")
OS_USER_DOMAIN_NAME = os.getenv("OS_USER_DOMAIN_NAME", "Default")
OS_PROJECT_DOMAIN_NAME = os.getenv("OS_PROJECT_DOMAIN_NAME", "Default")

# OPENSTACK RESOURCES
KEYPAIR_NAME = os.getenv("KEYPAIR_NAME", "cyberguard-key")
VICTIM_IMAGE_NAME = os.getenv("VICTIM_IMAGE_NAME", "Ubuntu-22.04")
ATTACKER_IMAGE_NAME = os.getenv("ATTACKER_IMAGE_NAME", "Kali-Linux")
SOC_IMAGE_NAME = os.getenv("SOC_IMAGE_NAME", "Ubuntu-22.04")

# Flavor (VM size) defaults
ATTACKER_FLAVOR = os.getenv("ATTACKER_FLAVOR", "m1.medium")
VICTIM_FLAVOR = os.getenv("VICTIM_FLAVOR", "m1.small")
SOC_FLAVOR = os.getenv("SOC_FLAVOR", "m1.medium")

# CELERY & REDIS (NEW)
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# DATABASE (NEW)
DATABASE_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "deployments.db"))

# TERRAFORM CONFIGURATION
TF_PLUGIN_CACHE_DIR = os.getenv("TF_PLUGIN_CACHE_DIR", str(CACHE_DIR / "terraform-plugins"))

# API CONFIGURATION
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "5000"))
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

# WORKER CONFIGURATION
WORKER_CONCURRENCY = int(os.getenv("WORKER_CONCURRENCY", "3"))  # Max 3 concurrent deploys
WORKER_LOG_LEVEL = os.getenv("WORKER_LOG_LEVEL", "INFO")

# VALIDATION
def validate_config():
    """Validate required configuration on startup"""
    errors = []
    
    # Check OpenStack credentials
    if not OS_USERNAME:
        errors.append("OS_USERNAME is required")
    if not OS_PASSWORD:
        errors.append("OS_PASSWORD is required")
    if not OS_PROJECT_ID:
        errors.append("OS_PROJECT_ID (or OS_TENANT_ID) is required")
    if not OS_AUTH_URL:
        errors.append("OS_AUTH_URL is required")
    
    # Check directories exist (or can be created)
    for dir_name, dir_path in [
        ("TEMPLATES_DIR", TEMPLATES_DIR),
        ("BASE_TERRAFORM_TEMPLATE", BASE_TERRAFORM_TEMPLATE)
    ]:
        if not dir_path.exists():
            errors.append(f"{dir_name} does not exist: {dir_path}")
    
    if errors:
        error_msg = "Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ValueError(error_msg)
    
    # Create runtime directories if they don't exist
    for dir_path in [RUNS_DIR, DATA_DIR, KEYS_DIR, CACHE_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)


# for any old scripts that might reference it:
TF_DIR = BASE_TERRAFORM_TEMPLATE  # Deprecated: use BASE_TERRAFORM_TEMPLATE

if __name__ == "__main__":
    # Test configuration
    try:
        validate_config()
        print("✅ Configuration valid!")
        print(f"\nOpenStack User: {OS_USERNAME}")
        print(f"OpenStack Project: {OS_PROJECT_ID}")
        print(f"Auth URL: {OS_AUTH_URL}")
        print(f"Region: {OS_REGION_NAME}")
        print(f"\nTemplates: {TEMPLATES_DIR}")
        print(f"Terraform Template: {BASE_TERRAFORM_TEMPLATE}")
        print(f"Runs Directory: {RUNS_DIR}")
        print(f"Database: {DATABASE_PATH}")
    except ValueError as e:
        print(f"❌ {e}")