
# 🛡️ CyberGuard: Cloud-Native Cyber Range

![Status](https://img.shields.io/badge/Status-Active-success)
![Tech](https://img.shields.io/badge/Stack-OpenStack%20%7C%20Terraform%20%7C%20Python-blue)
![UI](https://img.shields.io/badge/Dashboard-Flask%20%2B%20Cytoscape-orange)

**Infrastructure-as-Code system for creating and managing cybersecurity training environments on OpenStack.**

CyberGuard allows educational institutions and security teams to deploy isolated, monitored virtual networks for Red/Blue team exercises with a single click. It features a modern WebUI, dynamic topology visualization, and automated integration with VulnHub for infinite scenario replayability.

---

## 🏗️ Architecture

```mermaid
graph TD
    User([User / Student]) -->|HTTP| WebUI[Mission Control Dashboard]
    WebUI -->|REST API| Orchestrator[Python Orchestrator Service]
    
    subgraph "Core Logic"
        Orchestrator -->|Dynamic Vars| Tofu[OpenTofu / Terraform]
        Orchestrator -->|Query| Glance[OpenStack Glance]
    end
    
    subgraph "Infrastructure (OpenStack)"
        Tofu -->|Provision| Net[Private Network & Router]
        Tofu -->|Deploy| VMs[Attack VM + Victim VM + SOC]
    end
    
    subgraph "Logging & Defense"
        VMs -->|Traffic Mirror| Suricata[Suricata IDS]
        VMs -->|Logs| Wazuh[Wazuh SIEM]
    end
````

## ✨ Key Features

  * **🚀 One-Click Deployment:** Automatic provisioning of complex labs using Terraform/OpenTofu.
  * **🎲 Scenario Randomizer:** Dynamic injection of VulnHub images based on difficulty tags (Easy/Medium/Hard).
  * **🗺️ Live Topology:** Real-time visualization of the network graph and IP assignments using Cytoscape.js.
  * **🛡️ Blue Team Ready:** Pre-configured SOC node with **Wazuh**, **Suricata**, and **MinIO** installed via Cloud-Init.
  * **⚔️ Red Team Ready:** Kali Linux node auto-configured with custom attack scripts and wordlists.
  * **🏢 Multi-Tenancy:** Support for multiple parallel labs (Team A, Team B) using isolated Terraform states on GitLab.

-----

## 📂 Repository Layout

```text
.
├── infra/                  # Infrastructure as Code
│   └── terraform/          # OpenTofu modules (Compute, Network, Security)
├── services/               # Backend Microservices
│   ├── scenario-orchestrator/ # FastAPI backend & Logic
│   └── vulnhub-importer/      # Tool to fetch & tag VulnHub images
├── webui/                  # Frontend Application
│   ├── templates/          # HTML5 Dashboard (Jinja2)
│   └── static/             # CSS/JS (Cytoscape logic)
├── scripts/                # Helper utilities
└── docs/                   # Project documentation
```

-----

## ⚡ Quick Start

### 1\. Prerequisites

  * Access to an **OpenStack** cluster (Keystone V3).
  * **GitLab** account (for Remote Terraform State).
  * **Python 3.10+** and **OpenTofu** (or Terraform) installed.

### 2\. Environment Setup

Clone the repository and configure your credentials.

```bash
git clone [https://gitlab.example.com/cyberguard.git](https://gitlab.example.com/cyberguard.git)
cd cyber-range

# Configure the Backend
cd services/scenario-orchestrator
cp .env.example .env
nano .env
```

**Required `.env` variables:**

  * `OS_AUTH_URL`, `OS_PROJECT_ID`, `OS_USERNAME`, `OS_PASSWORD`
  * `OS_USER_DOMAIN_NAME` (e.g., EDU-ITS)
  * `GITLAB_TOKEN` (Personal Access Token with `api` scope)

### 3\. Run the Platform

You need to run the Backend API and the Frontend WebUI.

**Terminal 1 (Backend):**

```bash
cd services/scenario-orchestrator
pip install -r requirements.txt
python3 api.py
# API will listen on [http://0.0.0.0:8000](http://0.0.0.0:8000)
```

**Terminal 2 (Frontend):**

```bash
cd webui
pip install -r requirements.txt
python3 app.py
# Dashboard will listen on [http://0.0.0.0:5000](http://0.0.0.0:5000)
```

### 4\. Access Mission Control

Open your browser at **`http://localhost:5000`**.

1.  Select a scenario (e.g., *Mr. Robot CTF* or *VulnHub Roulette*).
2.  Click **Initiate Deploy**.
3.  Wait for the infrastructure to provision (\~3-5 mins).
4.  Once active, use the dashboard to access SSH credentials and the Wazuh interface.

-----

## 🛠️ Management Tools

### Import New Victims (Catalog)

To add a new vulnerable machine from VulnHub to the randomizer rotation:

```bash
cd services/vulnhub-importer
python3 auto_catalog.py [https://download.vulnhub.com/breach/breach-1.0.zip](https://download.vulnhub.com/breach/breach-1.0.zip) \
  --name "breach-1" \
  --difficulty easy \
  --desc "Breach 1.0 CTF"
```

### CLI Management

If you prefer the command line over the WebUI:

```bash
# Check status
python3 services/scenario-orchestrator/cli.py status

# Destroy infrastructure manually
python3 services/scenario-orchestrator/cli.py destroy
```
