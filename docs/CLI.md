# CLI Reference

Command-line interface for deploying scenarios without needing the API server.

## Setup

```bash
cd cyber-range/services/scenario-orchestrator
pip install -r requirements.txt
```

## Commands

```bash
python cli.py deploy <scenario>   # Deploy scenario
python cli.py destroy             # Destroy infrastructure
python cli.py status              # Get current outputs
python cli.py --help              # Show help
```

## Examples

### Deploy Basic Scenario
```bash
python cli.py deploy basic_pentest

# Output:
# 🚀 Deploying scenario: basic_pentest
# ✅ Deployment successful!
# 📋 Outputs:
#   victim_private_ip: 10.0.1.5
#   attacker_private_ip: 10.0.1.10
#   victim_public_ip: 203.0.113.42
```

### Deploy Advanced Scenario
```bash
python cli.py deploy advanced_multi_team

# Deploys 5-VM multi-team scenario (red, blue, victims, monitor)
```

### Check Current Status
```bash
python cli.py status

# Output:
# 📊 Current infrastructure status
#   victim_private_ip: 10.0.1.5
#   attacker_private_ip: 10.0.1.10
```

### Destroy Infrastructure
```bash
python cli.py destroy

# Output:
# 🔥 Destroying infrastructure...
# ✅ Destroy successful!
```

## Configuration

Set environment variables before running:

```bash
export OS_AUTH_URL=https://openstack.example.com:5000/v3
export OS_USERNAME=admin
export OS_PASSWORD=secret
export OS_PROJECT_NAME=cyber-range
export OS_REGION_NAME=RegionOne
```

Or create `.env` file:
```
OS_AUTH_URL=https://openstack.example.com:5000/v3
OS_USERNAME=admin
OS_PASSWORD=secret
OS_PROJECT_NAME=cyber-range
OS_REGION_NAME=RegionOne
```

See `.env.example` for all available variables.

## Available Scenarios

```
templates/
  ├── basic_pentest.yaml         2 VMs (easy)
  └── advanced_multi_team.yaml   5 VMs (hard)
```

## Creating Custom Scenarios

1. Copy existing scenario:
```bash
cp templates/basic_pentest.yaml templates/my_scenario.yaml
```

2. Edit YAML:
```yaml
name: my_scenario
difficulty: easy
network:
  cidr: "10.0.1.0/24"
  name: my_network
vms:
  - name: attacker
    role: attacker
    image: "kali-rolling"
    disk_gb: 20
    public_ip: true
  - name: victim
    role: victim
    image: "metasploitable2"
    disk_gb: 30
    public_ip: true
```

3. Deploy:
```bash
python cli.py deploy my_scenario
```

## Workflow Example

```bash
# 1. Deploy
python cli.py deploy basic_pentest

# 2. Wait for terraform to finish (takes a few minutes)
# 3. Check status
python cli.py status

# 4. SSH into VMs
ssh -i key.pem ubuntu@<victim_public_ip>
ssh -i key.pem kali@<attacker_public_ip>

# 5. Run exercise...

# 6. Destroy when done
python cli.py destroy
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "terraform not found" | Install terraform: https://www.terraform.io/downloads |
| "No such scenario" | Check `templates/` directory |
| "OpenStack auth failed" | Verify environment variables (OS_*) |
| "terraform command failed" | Check Terraform syntax in `infra/terraform/` |

---

**Version:** 0.1.0
