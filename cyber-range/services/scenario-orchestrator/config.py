"""Configuration - Load from environment"""
import os
from pathlib import Path
from dotenv import load_dotenv # Assicurati di avere python-dotenv installato

# Paths
BASE_DIR = Path(__file__).parent
# Root del progetto (cyber-range)
ROOT_DIR = BASE_DIR.parent.parent 
TF_DIR = (BASE_DIR.parent.parent / "infra" / "terraform").resolve()
TEMPLATES_DIR = BASE_DIR / "templates"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# CARICAMENTO .ENV DALLA ROOT
dotenv_path = ROOT_DIR / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)
else:
    # Fallback: prova a caricarlo dalla cartella corrente se esiste
    load_dotenv()

# OpenStack Credentials
OS_USERNAME = os.getenv("OS_USERNAME")
OS_PASSWORD = os.getenv("OS_PASSWORD")
OS_PROJECT_ID = os.getenv("OS_PROJECT_ID") or os.getenv("OS_TENANT_ID")
OS_AUTH_URL = os.getenv("OS_AUTH_URL")
OS_REGION_NAME = os.getenv("OS_REGION_NAME", "RegionOne")
OS_USER_DOMAIN_NAME = os.getenv("OS_USER_DOMAIN_NAME", "Default") # Aggiunto default

# GitLab / Terraform Backend Config
GITLAB_PROJECT_ID = os.getenv("GITLAB_PROJECT_ID", "82")
GITLAB_BASE_URL = os.getenv("GITLAB_BASE_URL", "https://gitlab.spinforward.it/api/v4/projects")
TF_STATE_NAME = os.getenv("TF_STATE_NAME", "cyber_range_dev")
GITLAB_USER = os.getenv("GITLAB_USER")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")

# Project Defaults
KEYPAIR_NAME = os.getenv("KEYPAIR_NAME", "cyberguard_ssh_key")
VICTIM_IMAGE_NAME = os.getenv("VICTIM_IMAGE_NAME", "mrrobot-fixed")