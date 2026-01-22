import json
import subprocess
import logging
import os
import shutil
import uuid
import yaml
from pathlib import Path
from typing import Dict, Any, Tuple

from config import (
    TEMPLATES_DIR,
    OS_USERNAME, OS_PASSWORD, OS_PROJECT_ID, OS_AUTH_URL, OS_REGION_NAME,
    KEYPAIR_NAME, VICTIM_IMAGE_NAME
)

# Environment variables with defaults
OS_USER_DOMAIN_NAME = os.getenv("OS_USER_DOMAIN_NAME", "Default")
OS_PROJECT_DOMAIN_NAME = os.getenv("OS_PROJECT_DOMAIN_NAME", "Default")

# Base directories for new architecture
BASE_TERRAFORM_TEMPLATE = Path(os.getenv("TEMPLATE_DIR", "/app/infra/terraform"))
RUNS_DIR = Path(os.getenv("RUNS_DIR", "/app/runs"))
TF_PLUGIN_CACHE_DIR = os.getenv("TF_PLUGIN_CACHE_DIR", "/app/cache/terraform-plugins")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TerraformOrchestrator:
    """
    Refactored Orchestrator with workspace isolation.
    Each deployment gets its own directory under /app/runs/<instance_id>/
    No more shared state - no more zombies!
    """
    
    def __init__(self):
        # Ensure runs directory exists
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Ensure plugin cache exists
        Path(TF_PLUGIN_CACHE_DIR).mkdir(parents=True, exist_ok=True)
        
        # Validate OpenStack credentials
        if not OS_USERNAME:
            logger.error("❌ OS_USERNAME missing. Run 'source setup_env.sh'")
            raise ValueError("Missing OS_USERNAME")
        
        if not OS_PASSWORD:
            logger.error("❌ OS_PASSWORD missing. Set it in environment or .env file")
            raise ValueError("Missing OS_PASSWORD")
        
        self.os_password = OS_PASSWORD
        logger.info("✅ TerraformOrchestrator initialized")

    def create_workspace(self, scenario_name: str) -> Tuple[str, Path]:
        """
        Create isolated workspace for a new deployment.
        
        Returns:
            (instance_id, workspace_path)
        """
        instance_id = str(uuid.uuid4())
        workspace_path = RUNS_DIR / instance_id
        
        logger.info(f"📁 Creating workspace: {instance_id}")
        
        try:
            # Copy entire terraform template to isolated directory
            shutil.copytree(BASE_TERRAFORM_TEMPLATE, workspace_path)
            logger.info(f"✅ Workspace created at: {workspace_path}")
            
            return instance_id, workspace_path
            
        except Exception as e:
            logger.error(f"❌ Failed to create workspace: {e}")
            # Cleanup on failure
            if workspace_path.exists():
                shutil.rmtree(workspace_path)
            raise

    def load_scenario(self, name: str) -> Dict[str, Any]:
        """Load scenario configuration from YAML"""
        path = TEMPLATES_DIR / (f"{name}.yaml" if not name.endswith(".yaml") else name)
        
        if not path.exists():
            raise FileNotFoundError(f"Scenario not found: {path}")
        
        with open(path) as f:
            return yaml.safe_load(f)

    def _init_terraform(self, workspace_path: Path, instance_id: str):
        """
        Initialize Terraform with LOCAL backend.
        No more GitLab - state is stored in workspace directory.
        """
        logger.info(f"⚙️  Initializing Terraform for: {instance_id}")
        
        # Create backend.tf with local backend
        backend_config = f"""terraform {{
  backend "local" {{
    path = "terraform.tfstate"
  }}
}}
"""
        backend_file = workspace_path / "backend.tf"
        with open(backend_file, 'w') as f:
            f.write(backend_config)
        
        # Initialize with plugin cache
        cmd = ["tofu", "init", "-upgrade"]
        
        env = os.environ.copy()
        env['TF_PLUGIN_CACHE_DIR'] = TF_PLUGIN_CACHE_DIR
        
        try:
            result = subprocess.run(
                cmd, 
                cwd=workspace_path, 
                env=env,
                capture_output=True, 
                text=True,
                check=True
            )
            logger.info("✅ Terraform initialized successfully")
            return result
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Terraform init failed: {e.stderr}")
            raise

    def deploy(self, instance_id: str, scenario_name: str, workspace_path: Path) -> Dict:
        """
        Execute terraform apply in isolated workspace.
        
        Args:
            instance_id: Unique deployment ID
            scenario_name: Name of scenario to deploy
            workspace_path: Path to isolated workspace
            
        Returns:
            Dict with success status, outputs, or error
        """
        logger.info(f"🚀 Starting deployment: {scenario_name} -> {instance_id}")
        
        try:
            # Initialize Terraform
            self._init_terraform(workspace_path, instance_id)
            
            # Load scenario configuration
            scenario = self.load_scenario(scenario_name)
            
            # Prepare Terraform variables
            tf_vars = self._prepare_variables(instance_id, scenario)
            
            # Write variables to tfvars file
            self._write_tfvars(workspace_path, tf_vars)
            
            # Execute apply
            result = self._apply(workspace_path, instance_id)
            
            if result['success']:
                # Get outputs
                outputs = self._get_outputs(workspace_path)
                return {
                    "success": True,
                    "outputs": outputs,
                    "error": None
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"❌ Deployment failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "outputs": None
            }

    def _prepare_variables(self, instance_id: str, scenario: Dict) -> Dict[str, str]:
        """Prepare all Terraform variables for deployment"""
        
        tf_vars = {
            # OpenStack credentials
            "os_user_name": OS_USERNAME,
            "os_password": self.os_password,
            "os_tenant_id": OS_PROJECT_ID,
            "os_auth_url": OS_AUTH_URL,
            "os_region": OS_REGION_NAME,
            "os_user_domain": OS_USER_DOMAIN_NAME,
            "os_project_domain": OS_PROJECT_DOMAIN_NAME,
            
            # Instance-specific resources (CRITICAL: unique names per deployment)
            "keypair_name": f"{KEYPAIR_NAME}-{instance_id}",
            "vm_name": f"attack-{instance_id}",
            "log_vm_name": f"soc-{instance_id}",
            "victim_vm_name": f"victim-{instance_id}",
            "net_name": f"net-{instance_id}",
            "subnet_name": f"sub-{instance_id}",
            
            # Image configuration
            "victim_image_name": VICTIM_IMAGE_NAME,
        }
        
        # Add scenario-specific network configuration
        if "network" in scenario and "cidr" in scenario["network"]:
            tf_vars["private_cidr"] = scenario["network"]["cidr"]
        
        return tf_vars

    def _write_tfvars(self, workspace_path: Path, variables: Dict[str, str]):
        """Write variables to terraform.tfvars file"""
        tfvars_path = workspace_path / "terraform.tfvars"
        
        with open(tfvars_path, 'w') as f:
            for key, value in variables.items():
                # Escape special characters in values
                safe_value = str(value).replace('"', '\\"')
                f.write(f'{key} = "{safe_value}"\n')
        
        logger.info(f"📝 Variables written to {tfvars_path}")

    def _apply(self, workspace_path: Path, instance_id: str) -> Dict:
        """Execute terraform apply with streaming output"""
        
        cmd = ["tofu", "apply", "-auto-approve", "-no-color"]
        
        env = os.environ.copy()
        env['TF_PLUGIN_CACHE_DIR'] = TF_PLUGIN_CACHE_DIR
        
        logger.info("⏳ Executing OpenTofu apply... (this may take several minutes)")
        
        output_lines = []
        
        try:
            # Stream output in real-time
            with subprocess.Popen(
                cmd,
                cwd=workspace_path,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            ) as process:
                
                for line in process.stdout:
                    print(line, end='')  # Print to console
                    output_lines.append(line)
                
                process.wait()
                
                if process.returncode == 0:
                    logger.info("✅ Deployment completed successfully!")
                    return {"success": True}
                else:
                    logger.error("❌ Deployment failed")
                    # Return last 20 lines as error context
                    error_msg = "".join(output_lines[-20:])
                    return {
                        "success": False,
                        "error": error_msg
                    }
                    
        except Exception as e:
            logger.error(f"❌ Exception during apply: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def destroy(self, instance_id: str) -> Dict:
        """
        Destroy infrastructure and remove workspace.
        
        Args:
            instance_id: Deployment ID to destroy
            
        Returns:
            Dict with success status
        """
        workspace_path = RUNS_DIR / instance_id
        
        if not workspace_path.exists():
            logger.warning(f"⚠️  Workspace not found: {instance_id}")
            return {
                "success": False,
                "error": "Workspace not found - may already be destroyed"
            }
        
        logger.warning(f"🔥 Destroying deployment: {instance_id}")
        
        try:
            # Re-initialize if needed (in case of server restart)
            if not (workspace_path / ".terraform").exists():
                self._init_terraform(workspace_path, instance_id)
            
            cmd = ["tofu", "destroy", "-auto-approve", "-no-color"]
            
            env = os.environ.copy()
            env['TF_PLUGIN_CACHE_DIR'] = TF_PLUGIN_CACHE_DIR
            
            # Execute destroy
            result = subprocess.run(
                cmd,
                cwd=workspace_path,
                env=env,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode == 0:
                logger.info("✅ Infrastructure destroyed successfully")
            else:
                logger.warning(f"⚠️  Destroy completed with warnings: {result.stderr}")
            
            # Always remove workspace directory after destroy attempt
            logger.info(f"🗑️  Removing workspace: {workspace_path}")
            shutil.rmtree(workspace_path)
            
            return {
                "success": True,
                "error": None
            }
            
        except subprocess.TimeoutExpired:
            logger.error("❌ Destroy timed out")
            return {
                "success": False,
                "error": "Destroy operation timed out"
            }
        except Exception as e:
            logger.error(f"❌ Destroy failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _get_outputs(self, workspace_path: Path) -> Dict:
        """
        Read Terraform outputs from workspace.
        
        Returns:
            Dict of output values (IPs, credentials, etc.)
        """
        try:
            cmd = ["tofu", "output", "-json"]
            
            env = os.environ.copy()
            env['TF_PLUGIN_CACHE_DIR'] = TF_PLUGIN_CACHE_DIR
            
            result = subprocess.run(
                cmd,
                cwd=workspace_path,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            raw_outputs = json.loads(result.stdout)
            
            # Extract actual values from Terraform output format
            outputs = {
                key: value.get("value") 
                for key, value in raw_outputs.items()
            }
            
            logger.info(f"📊 Retrieved {len(outputs)} outputs")
            return outputs
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to get outputs: {e.stderr}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse outputs: {e}")
            return {}
        except Exception as e:
            logger.error(f"❌ Unexpected error getting outputs: {e}")
            return {}

    def get_workspace_status(self, instance_id: str) -> Dict:
        """
        Check if workspace exists and get basic info.
        Useful for recovery after server restart.
        """
        workspace_path = RUNS_DIR / instance_id
        
        if not workspace_path.exists():
            return {
                "exists": False,
                "has_state": False
            }
        
        state_file = workspace_path / "terraform.tfstate"
        
        return {
            "exists": True,
            "has_state": state_file.exists(),
            "path": str(workspace_path)
        }

    def list_workspaces(self) -> list:
        """
        List all existing workspaces.
        Useful for cleanup and monitoring.
        """
        if not RUNS_DIR.exists():
            return []
        
        workspaces = []
        for workspace_dir in RUNS_DIR.iterdir():
            if workspace_dir.is_dir():
                state_file = workspace_dir / "terraform.tfstate"
                workspaces.append({
                    "instance_id": workspace_dir.name,
                    "path": str(workspace_dir),
                    "has_state": state_file.exists(),
                    "created": workspace_dir.stat().st_ctime
                })
        
        return workspaces