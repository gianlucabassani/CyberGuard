import os
import logging
from celery import Celery
from database import Database
from orchestrator import Orchestrator

# Broker Configuration
# Connects to Redis running on localhost by default
REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

# Initialize Celery app
app = Celery('cyberguard', broker=REDIS_URL, backend=REDIS_URL)

# Celery Optimization Settings
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    task_track_started=True, # Allows tracking "started" state in addition to "pending/success"
    worker_concurrency=4,    # Number of concurrent worker threads (CPU)
)

logger = logging.getLogger(__name__)

@app.task(name="deploy_lab", bind=True)
def deploy_lab(self, instance_id, scenario_name, user_id, variables=None):
    """
    Async Task: Deploys a laboratory environment.
    bind=True allows access to the task instance (e.g., self.request.id).
    """
    db = Database()
    orch = Orchestrator()
    
    logger.info(f"[{instance_id}] Task received. Scenario: {scenario_name}")
    
    # 1. Update DB: Set status to deploying
    db.update_deployment(instance_id, status="deploying")
    
    # 2. Execute Deployment
    result = orch.deploy(scenario_name, instance_id, variables)
    
    # 3. Handle Result
    if result["success"]:
        logger.info(f"[{instance_id}] Deployment successful. Updating DB.")
        db.update_deployment(instance_id, status="active", outputs=result["outputs"])
    else:
        logger.error(f"[{instance_id}] Deployment failed. Error: {result['error']}")
        db.update_deployment(instance_id, status="failed", error=result["error"])
        
    return result

@app.task(name="destroy_lab")
def destroy_lab(instance_id):
    """
    Async Task: Destroys a laboratory environment.
    """
    db = Database()
    orch = Orchestrator()
    
    logger.info(f"[{instance_id}] Destroy task received.")
    
    # Update DB status before starting operation
    db.update_deployment(instance_id, status="destroying")
    
    result = orch.destroy(instance_id)
    
    if result["success"]:
        db.update_deployment(instance_id, status="destroyed")
    else:
        db.update_deployment(instance_id, status="error_destroying", error=result["error"])
        
    return result