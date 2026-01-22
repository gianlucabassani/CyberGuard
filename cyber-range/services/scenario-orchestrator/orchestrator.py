import subprocess
import logging
import shutil
import json
import os
import time
import random
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TF_SOURCE_DIR = BASE_DIR.parent.parent / "infra" / "terraform"
RUNS_DIR = BASE_DIR.parent.parent / "runs"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        self.mock_mode = os.getenv("MOCK_MODE", "false").lower() == "true"

    def _prepare_workspace(self, instance_id: str) -> Path:
        work_dir = RUNS_DIR / instance_id
        if work_dir.exists(): shutil.rmtree(work_dir)
        shutil.copytree(TF_SOURCE_DIR, work_dir)
        return work_dir

    def deploy(self, scenario_name: str, instance_id: str, user_vars: dict = None):
        logger.info(f"[{instance_id}] Starting deployment (Mock Mode: {self.mock_mode})")
        
        if self.mock_mode:
            logger.info(f"[{instance_id}] 🎭 SIMULATING DEPLOY...")
            time.sleep(2)
            
            # --- MOCK DATA MATCHING DASHBOARD.HTML ---
            fake_outputs = {
                "soc_dashboard_url": "https://192.168.1.50:443",
                "soc_credentials": {"username": "admin", "password": "SecretPassword!"},
                "log_vm_ssh_command": f"ssh ubuntu@192.168.1.50",
                "log_vm_private_ip": "192.168.0.5",
                "log_vm_floating_ip": "192.168.1.50",
                
                "attack_vm_ssh_command": f"ssh kali@192.168.1.80",
                "attack_vm_private_ip": "192.168.50.10",
                "attack_vm_floating_ip": "192.168.1.80",
                
                "victim_vm_private_ip": "192.168.0.10",
                "victim_vm_floating_ip": "192.168.1.60"
            }
            return {"success": True, "outputs": fake_outputs}

        # REAL LOGIC
        work_dir = self._prepare_workspace(instance_id)
        try:
            subprocess.run(["tofu", "init"], cwd=work_dir, check=True, capture_output=True)
            cmd = ["tofu", "apply", "-auto-approve", "-json"]
            cmd.extend(["-var", f"vm_name=att-{instance_id[:5]}"])
            
            subprocess.run(cmd, cwd=work_dir, check=True, capture_output=True)
            return {"success": True, "outputs": self._get_outputs(work_dir)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def destroy(self, instance_id: str):
        if self.mock_mode: return {"success": True}
        work_dir = RUNS_DIR / instance_id
        if work_dir.exists(): shutil.rmtree(work_dir)
        return {"success": True}

    def _get_outputs(self, work_dir: Path):
        try:
            res = subprocess.run(["tofu", "output", "-json"], cwd=work_dir, capture_output=True, text=True)
            return json.loads(res.stdout)
        except: return {}