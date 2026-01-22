import subprocess
import logging
import shutil
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
TF_SOURCE_DIR = BASE_DIR.parent.parent / "infra" / "terraform"
RUNS_DIR = BASE_DIR.parent.parent / "runs" # Target directory for active runtime workspaces


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        RUNS_DIR.mkdir(parents=True, exist_ok=True)

    def _prepare_workspace(self, instance_id: str) -> Path:
        """
        Creates an isolated workspace for the specific instance ID.
        Copies the Terraform templates to a unique directory.
        """
        work_dir = RUNS_DIR / instance_id
        
        # Cleanup existing workspace if retry or restart occurs
        if work_dir.exists():
            logger.warning(f"Workspace {work_dir} exists. Cleaning up before recreation.")
            shutil.rmtree(work_dir)
            
        logger.info(f"Creating isolated workspace: {work_dir}")
        shutil.copytree(TF_SOURCE_DIR, work_dir)
        return work_dir

    def deploy(self, scenario_name: str, instance_id: str, user_vars: dict = None):
        """
        Executes the full deployment pipeline: Init -> Plan -> Apply.
        """
        logger.info(f"[{instance_id}] Starting deployment workflow for scenario: {scenario_name}")
        work_dir = self._prepare_workspace(instance_id)
        
        # 1. Terraform Init
        # Initializes the backend and provider plugins in the isolated directory
        try:
            logger.info(f"[{instance_id}] Initializing Terraform backend...")
            subprocess.run(["tofu", "init"], cwd=work_dir, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"[{instance_id}] Init failed: {e.stderr}")
            return {"success": False, "error": f"Init failed: {e.stderr}"}

        # 2. Variable Preparation
        # Construct CLI arguments to pass unique resource names to OpenStack (prevents name collisions between different labs)
        cmd_vars = [
            "-var", f"vm_name=att-{instance_id[:8]}", 
            "-var", f"victim_vm_name=vic-{instance_id[:8]}",
            "-var", f"keypair_name=key-{instance_id[:8]}"
        ]
        
        # Inject additional user-provided variables if present
        if user_vars:
            for k, v in user_vars.items():
                cmd_vars.extend(["-var", f"{k}={v}"])

        # 3. Terraform Apply
        # Executes the infrastructure creation. 'auto-approve' avoids interactive prompts.
        logger.info(f"[{instance_id}] Executing Terraform Apply...")
        try:
            # capture_output=True captures stdout/stderr for logging instead of printing to console
            subprocess.run(
                ["tofu", "apply", "-auto-approve", "-json"] + cmd_vars,
                cwd=work_dir,
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"[{instance_id}] Apply completed successfully.")
            return {"success": True, "outputs": self._get_outputs(work_dir)}
            
        except subprocess.CalledProcessError as e:
            logger.error(f"[{instance_id}] Apply failed: {e.stderr}")
            return {"success": False, "error": f"Apply failed: {e.stderr}"}

    def destroy(self, instance_id: str):
        """
        Destroys the infrastructure and cleans up the local workspace.
        """
        work_dir = RUNS_DIR / instance_id
        if not work_dir.exists():
            logger.error(f"[{instance_id}] Workspace not found. Cannot destroy.")
            return {"success": False, "error": "Workspace not found"}

        logger.info(f"[{instance_id}] Triggering infrastructure destruction.")
        try:
            # Execute destroy within the isolated workspace
            subprocess.run(
                ["tofu", "destroy", "-auto-approve"],
                cwd=work_dir,
                check=True,
                capture_output=True
            )
            
            # Post-destruction cleanup: remove the directory to free disk space
            logger.info(f"[{instance_id}] Destroy success. Removing workspace files.")
            shutil.rmtree(work_dir)
            return {"success": True}
        except subprocess.CalledProcessError as e:
            logger.error(f"[{instance_id}] Destroy failed: {e.stderr}")
            return {"success": False, "error": str(e)}

    def _get_outputs(self, work_dir: Path):
        """
        Extracts output variables (IPs, credentials) from the Terraform state.
        """
        try:
            res = subprocess.run(
                ["tofu", "output", "-json"],
                cwd=work_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(res.stdout)
        except Exception as e:
            logger.error(f"Failed to parse outputs: {e}")
            return {}