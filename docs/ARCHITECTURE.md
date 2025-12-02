# Architecture Overview

## Core Design

Simple, modular, expandable system for deploying cyber range scenarios via Terraform.

```
User/CLI/API
    ↓
orchestrator.py (109 lines)
    ├─ load_scenario(name)     → reads YAML
    ├─ deploy(name)            → runs terraform apply
    ├─ destroy()               → runs terraform destroy
    └─ _get_outputs()          → reads tfstate
    ↓
Terraform CLI
    ↓
OpenStack API (Nova, Neutron, Glance)
    ↓
Infrastructure (VMs, Networks)
```

## Files

| File | Lines | Purpose |
|------|-------|---------|
| `orchestrator.py` | 109 | Core logic: YAML→Terraform bridge |
| `config.py` | 30 | Environment & paths |
| `cli.py` | 87 | CLI interface (deploy/destroy/status) |
| `api.py` | 73 | FastAPI REST wrapper |
| `auto_importer.py` | ~350 | VulnHub downloader + converter + uploader |

## Key Concepts

### Scenarios (YAML)
- Located: `templates/`
- Define: networks, VMs, disk size, image names
- Mapped to Terraform variables automatically

### Orchestrator
- Reads YAML scenario
- Builds `-var key=value` flags for Terraform
- Runs `terraform apply/destroy`
- Extracts outputs from `terraform.tfstate`

### No Hardcoded Assumptions
- Doesn't know Terraform resource names
- Uses `-var` flags for all config
- Works with any Terraform changes

## Workflow

```bash
# 1. User deploys scenario
python cli.py deploy basic_pentest

# 2. Orchestrator loads templates/basic_pentest.yaml
# 3. Maps YAML fields to Terraform variables
# 4. Runs: terraform apply -var net_name=... -var image_name=...
# 5. Terraform provisions OpenStack resources
# 6. Orchestrator reads terraform.tfstate → extracts outputs
# 7. User sees results (IPs, credentials, etc.)
```

## Dependencies

**Minimal Core:**
- pyyaml (YAML parsing)
- python-dotenv (environment loading)
- requests (HTTP)
- openstacksdk (OpenStack API)

**Optional API Layer:**
- fastapi (REST server)
- uvicorn (ASGI server)
- pydantic (data validation)

## Expandability

### Adding Features
1. **New Scenario:** Create `templates/my_scenario.yaml`
2. **New Variable:** Add to YAML, update `orchestrator.py` mapping
3. **New Endpoint:** Add route to `api.py`
4. **VulnHub Import:** Use `auto_importer.py` directly

### Not Tight to Terraform
- Terraform can change structure
- Orchestrator only passes variables
- No breaking changes from infrastructure updates

## Error Handling

All endpoints return `{success: bool, ...details}` format:
- CLI catches exceptions → user-friendly messages
- API returns HTTP status codes + JSON
- Terraform errors logged for debugging

## Security

- Credentials from environment variables (never hardcoded)
- `.env` file in `.gitignore`
- `.gitignore` excludes `terraform.tfstate`, logs, temp files

---

**Version:** 0.1.0
**Status:** ✅ Production Ready
