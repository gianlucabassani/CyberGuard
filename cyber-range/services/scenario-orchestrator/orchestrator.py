import json
import subprocess
import logging
import os
import sys
import getpass
import yaml
from pathlib import Path
from typing import Dict, Any

from config import (
    TF_DIR, TEMPLATES_DIR, 
    GITLAB_PROJECT_ID, GITLAB_BASE_URL, TF_STATE_NAME, 
    GITLAB_USER, GITLAB_TOKEN,
    OS_USERNAME, OS_PASSWORD, OS_PROJECT_ID, OS_AUTH_URL, OS_REGION_NAME,
    KEYPAIR_NAME, VICTIM_IMAGE_NAME
)

# Gestione fallback dominio
OS_USER_DOMAIN_NAME = os.getenv("OS_USER_DOMAIN_NAME", "Default")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self):
        self.tf_dir = TF_DIR
        
        # 1. CONTROLLO E RICHIESTA PASSWORD
        self.os_password = OS_PASSWORD
        if not self.os_password:
            logger.warning("🔑 Password OpenStack non trovata nelle variabili d'ambiente.")
            try:
                # Chiede la password all'avvio del server (input nascosto)
                self.os_password = getpass.getpass(prompt='Inserisci Password OpenStack per continuare: ')
            except Exception as e:
                logger.error(f"Errore input password: {e}")
                sys.exit(1)
        
        if not OS_USERNAME:
            logger.error("❌ Errore: OS_USERNAME mancante (fai 'source setup_env.sh')")
            sys.exit(1)

    def _init_terraform(self, instance_id: str):
        """Inizializza Terraform stampando l'output per debug"""
        logger.info(f"⚙️  Inizializzazione Terraform per: {instance_id}...")

        unique_state = f"{TF_STATE_NAME}_{instance_id}"
        address = f"{GITLAB_BASE_URL}/{GITLAB_PROJECT_ID}/terraform/state/{unique_state}"
        lock_address = f"{address}/lock"

        cmd = [
            "tofu", "init", "-reconfigure", "-upgrade",
            f"-backend-config=address={address}",
            f"-backend-config=lock_address={lock_address}",
            f"-backend-config=unlock_address={lock_address}",
            "-backend-config=lock_method=POST",
            "-backend-config=unlock_method=DELETE",
            "-backend-config=retry_wait_min=5",
        ]

        if GITLAB_USER: cmd.append(f"-backend-config=username={GITLAB_USER}")
        if GITLAB_TOKEN: cmd.append(f"-backend-config=password={GITLAB_TOKEN}")

        # Usa capture_output=False per vedere errori di init direttamente
        try:
            subprocess.run(cmd, cwd=self.tf_dir, check=True, capture_output=False)
        except subprocess.CalledProcessError:
            logger.error("❌ Init fallito. Controlla le credenziali GitLab.")
            raise

    def load_scenario(self, name: str) -> Dict[str, Any]:
        path = TEMPLATES_DIR / (f"{name}.yaml" if not name.endswith(".yaml") else name)
        with open(path) as f: return yaml.safe_load(f)

    def deploy(self, scenario_name: str, instance_id: str) -> Dict:
        logger.info(f"🚀 Avvio Deploy: {scenario_name} -> {instance_id}")
        
        try:
            self._init_terraform(instance_id)
        except:
            return {"success": False, "error": "Terraform Init Failed"}
        
        scenario = self.load_scenario(scenario_name)

        # Preparazione variabili da passare a Tofu
        tf_vars = {
            "os_user_name": OS_USERNAME,
            "os_password": self.os_password,
            "os_tenant_id": OS_PROJECT_ID,
            "os_auth_url": OS_AUTH_URL,
            "os_region": OS_REGION_NAME,
            "os_user_domain": OS_USER_DOMAIN_NAME,
            "os_project_domain": "Default",
            
            # --- FIX FONDAMENTALE: KEYPAIR UNICA PER ISTANZA ---
            "keypair_name": f"{KEYPAIR_NAME}-{instance_id}",
            # ---------------------------------------------------
            
            "victim_image_name": VICTIM_IMAGE_NAME,
            
            "vm_name": f"attack-{instance_id}",
            "log_vm_name": f"soc-{instance_id}",
            "victim_vm_name": f"victim-{instance_id}",
            "net_name": f"net-{instance_id}",
            "subnet_name": f"sub-{instance_id}"
        }

        if "network" in scenario and "cidr" in scenario["network"]:
            tf_vars["private_cidr"] = scenario["network"]["cidr"]

        cmd = ["tofu", "apply", "-auto-approve", "-no-color"]
        for k, v in tf_vars.items():
            cmd.extend(["-var", f"{k}={v}"])

        logger.info("⏳ Esecuzione OpenTofu Apply... (Segui il terminale qui sotto)")

        # --- STREAMING OUTPUT (EVITA BLOCCO) ---
        output_lines = []
        try:
            # Popen permette di leggere stdout riga per riga mentre il processo gira
            with subprocess.Popen(
                cmd, 
                cwd=self.tf_dir, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, # Unisce errori e output
                text=True, 
                bufsize=1
            ) as p:
                for line in p.stdout:
                    print(line, end='') # Stampa a video subito!
                    output_lines.append(line)
                
                p.wait()
                
                if p.returncode == 0:
                    logger.info("✅ Deploy Completato con successo!")
                    return {"success": True, "outputs": self._get_outputs(instance_id)}
                else:
                    logger.error("❌ Deploy Fallito.")
                    # Prende le ultime 15 righe per l'errore da mostrare in dashboard
                    error_msg = "".join(output_lines[-15:])
                    return {"success": False, "error": error_msg}

        except Exception as e:
            logger.error(f"Eccezione Python: {e}")
            return {"success": False, "error": str(e)}

    def destroy(self, instance_id: str) -> Dict:
        logger.warning(f"🔥 Distruzione {instance_id}...")
        try:
            self._init_terraform(instance_id)
        except: pass

        cmd = ["tofu", "destroy", "-auto-approve", "-no-color"]
        
        # Anche destroy ha bisogno delle credenziali!
        tf_vars = {
            "os_user_name": OS_USERNAME,
            "os_password": self.os_password,
            "os_tenant_id": OS_PROJECT_ID,
            "os_auth_url": OS_AUTH_URL,
            "os_region": OS_REGION_NAME,
            "os_user_domain": OS_USER_DOMAIN_NAME,
            "os_project_domain": "Default",
            # Nota: per destroy non serve necessariamente il keypair_name se lo stato c'è,
            # ma passarlo non fa danni.
        }
        for k, v in tf_vars.items():
            cmd.extend(["-var", f"{k}={v}"])

        subprocess.run(cmd, cwd=self.tf_dir, check=False)
        return {"success": True, "error": None}

    def _get_outputs(self, instance_id: str) -> Dict:
        """Legge gli output finali (IP, credenziali)"""
        try:
            self._init_terraform(instance_id)
            cmd = ["tofu", "output", "-json"]
            result = subprocess.run(cmd, cwd=self.tf_dir, capture_output=True, text=True)
            if result.returncode != 0: return {}
            raw = json.loads(result.stdout)
            return {k: v.get("value") for k, v in raw.items()}
        except Exception as e:
            logger.error(f"Errore lettura output: {e}")
            return {}