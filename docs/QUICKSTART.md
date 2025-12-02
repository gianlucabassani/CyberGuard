# Quick Start

5-minute setup to deploy your first scenario.

## 1. Prerequisites

- Terraform >= 1.5
- Python >= 3.8
- OpenStack credentials

## 2. Configure Credentials

Create `.env` file in `cyber-range/services/scenario-orchestrator/`:

```bash
cd cyber-range/services/scenario-orchestrator
cp .env.example .env
# Edit .env with your OpenStack credentials
```

Or set environment variables:
```bash
export OS_AUTH_URL=https://your-openstack:5000/v3
export OS_USERNAME=admin
export OS_PASSWORD=secret
export OS_PROJECT_NAME=cyber-range
export OS_REGION_NAME=RegionOne
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Deploy Scenario

```bash
# CLI approach
python cli.py deploy basic_pentest

# Check status
python cli.py status
```

Or start API and use REST:
```bash
# Terminal 1: Start API server
python api.py

# Terminal 2: Deploy via API
curl -X POST http://localhost:8000/deploy \
  -H "Content-Type: application/json" \
  -d '{"name": "basic_pentest"}'

# Check status
curl http://localhost:8000/status
```

## 5. Verify Deployment

Check OpenStack console:
- Navigate to **Project > Compute > Instances**
- Should see 2 new VMs (victim, attacker)
- Wait for "Active" status

Or check via CLI:
```bash
python cli.py status
# Shows IP addresses and outputs
```

## 6. Access VMs

```bash
# Get IPs from status output
python cli.py status

# SSH into attacker (Kali)
ssh -i key.pem kali@<victim_public_ip>

# SSH into victim
ssh -i key.pem ubuntu@<attacker_public_ip>
```

## 7. Cleanup

```bash
python cli.py destroy
```

---

## Next Steps

- Read [CLI.md](CLI.md) for all CLI commands
- Read [API.md](API.md) for REST API usage
- Read [ARCHITECTURE.md](ARCHITECTURE.md) for design details
- Create custom scenarios (copy `templates/basic_pentest.yaml`)

---

**Time:** ~5 min setup + Terraform deploy (5-15 min depending on OpenStack)
