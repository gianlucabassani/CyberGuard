"""
FastAPI REST Layer - Multi-Scenario Orchestrator API
"""
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import json
import os
import logging
from orchestrator import Orchestrator

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Cyber Range Orchestrator")
orchestrator = Orchestrator()

# --- DATABASE (JSON FILE) ---
DB_FILE = "deployments.json"

def get_db():
    if not os.path.exists(DB_FILE): return {}
    try:
        with open(DB_FILE, "r") as f: return json.load(f)
    except json.JSONDecodeError: return {}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=2)

# --- MODELS ---
class DeployRequest(BaseModel):
    scenario: str
    instance_id: str

# --- BACKGROUND TASKS ---
def run_deploy(scenario_name: str, instance_id: str):
    logger.info(f"Starting background deploy: {scenario_name} -> {instance_id}")
    res = orchestrator.deploy(scenario_name, instance_id)
    
    db = get_db()
    if res["success"]:
        db[instance_id]["status"] = "active"
        db[instance_id]["outputs"] = res["outputs"]
    else:
        db[instance_id]["status"] = "failed"
        db[instance_id]["error"] = res.get("error")
    save_db(db)

def run_destroy(instance_id):
    logger.info(f"Starting background destroy: {instance_id}")
    
    # 1. Try to destroy infrastructure (Best Effort)
    orchestrator.destroy(instance_id)
    
    # 2. ALWAYS remove from Dashboard database
    db = get_db()
    if instance_id in db:
        del db[instance_id]
        save_db(db)
        logger.info(f"Removed {instance_id} from database")

# --- ENDPOINTS ---

@app.get("/deployments")
def list_deployments():
    """List all labs"""
    return get_db()

@app.post("/deploy")
async def deploy(req: DeployRequest, bg: BackgroundTasks):
    """Start deployment"""
    db = get_db()
    if req.instance_id in db:
        raise HTTPException(400, "Instance ID already exists")
    
    # Initialize record
    db[req.instance_id] = {
        "status": "deploying", 
        "scenario": req.scenario,
        "outputs": {}
    }
    save_db(db)
    
    bg.add_task(run_deploy, req.scenario, req.instance_id)
    return {"status": "accepted", "instance_id": req.instance_id}

@app.delete("/destroy/{instance_id}")
async def destroy(instance_id: str, bg: BackgroundTasks):
    """Start destruction"""
    db = get_db()
    if instance_id not in db:
        raise HTTPException(404, "Instance not found")
    
    db[instance_id]["status"] = "destroying"
    save_db(db)
    
    bg.add_task(run_destroy, instance_id)
    return {"status": "accepted"}

@app.get("/status/{instance_id}")
def get_status(instance_id: str):
    """Get status for specific lab"""
    db = get_db()
    if instance_id not in db:
        raise HTTPException(404, "Instance not found")
    return db[instance_id]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)