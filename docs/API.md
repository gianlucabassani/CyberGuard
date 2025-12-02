# API Reference

## Overview

REST API for deploying and managing cyber range scenarios.

```
POST   /deploy    - Deploy scenario
DELETE /destroy   - Destroy infrastructure
GET    /status    - Get current outputs
GET    /health    - Health check
```

## Startup

```bash
pip install -r requirements.txt
python api.py

# Runs on http://localhost:8000
# Docs: http://localhost:8000/docs
```

## Endpoints

### POST /deploy
Deploy a scenario in background.

**Request:**
```json
{
  "name": "basic_pentest"
}
```

**Response:**
```json
{
  "status": "deploying",
  "scenario": "basic_pentest"
}
```

**Status Codes:**
- 200: Deployment queued successfully
- 404: Scenario not found
- 500: Server error

### DELETE /destroy
Destroy all infrastructure.

**Response:**
```json
{
  "status": "destroyed"
}
```

**Status Codes:**
- 200: Destruction successful
- 500: Server error

### GET /status
Get current infrastructure status and outputs.

**Response:**
```json
{
  "success": true,
  "outputs": {
    "victim_private_ip": "10.0.1.5",
    "attacker_private_ip": "10.0.1.10",
    "victim_public_ip": "203.0.113.42"
  }
}
```

### GET /health
Health check.

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

## Usage Examples

### cURL
```bash
# Check health
curl http://localhost:8000/health

# Deploy
curl -X POST http://localhost:8000/deploy \
  -H "Content-Type: application/json" \
  -d '{"name": "basic_pentest"}'

# Get status
curl http://localhost:8000/status

# Destroy
curl -X DELETE http://localhost:8000/destroy
```

### Python
```python
import requests

BASE = "http://localhost:8000"

# Deploy
resp = requests.post(f"{BASE}/deploy", json={"name": "basic_pentest"})
print(resp.json())

# Check status
resp = requests.get(f"{BASE}/status")
print(resp.json()["outputs"])

# Destroy
resp = requests.delete(f"{BASE}/destroy")
print(resp.json())
```

### JavaScript/Node
```javascript
const base = "http://localhost:8000";

// Deploy
const deploy = await fetch(`${base}/deploy`, {
  method: "POST",
  headers: {"Content-Type": "application/json"},
  body: JSON.stringify({name: "basic_pentest"})
});
console.log(await deploy.json());

// Status
const status = await fetch(`${base}/status`);
console.log(await status.json());

// Destroy
const destroy = await fetch(`${base}/destroy`, {method: "DELETE"});
console.log(await destroy.json());
```

## Interactive Docs

Open http://localhost:8000/docs in browser for interactive Swagger UI where you can test all endpoints.

## Notes

- Deployments run in background (terraform can take minutes)
- Poll `/status` to check progress
- Outputs appear in `/status` once deployment completes
- All errors return JSON with status code

---

**Version:** 0.1.0
