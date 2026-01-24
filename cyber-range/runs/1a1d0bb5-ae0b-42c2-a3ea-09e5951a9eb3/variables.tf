# -------------------------------------------------------------------
# --- Credenziali OpenStack --- 
# -------------------------------------------------------------------
variable "os_project_domain" {
  description = "Dominio del progetto OpenStack"
  type        = string
  default     = "Default"
}

variable "os_user_name" {
  description = "Username OpenStack"
  type        = string
}

variable "os_user_domain" {
  description = "Dominio utente"
  type        = string
  default     = "EDU-ITS"
}

variable "os_password" {
  description = "Password utente OpenStack"
  type        = string
  sensitive   = true
}

variable "os_auth_url" {
  description = "Keystone v3 URL"
  type        = string
}

variable "os_region" {
  description = "Regione OpenStack"
  type        = string
  default     = "RegionOne"
}

variable "os_insecure" {
  description = "Permetti certificati self-signed"
  type        = bool
  default     = true
}

variable "os_tenant_id" {
  description = "ID del progetto (tenant)"
  type        = string
}

# -------------------------------------------------------------------
# --- Rete --- 
# -------------------------------------------------------------------
variable "external_network_name" {
  description = "Nome rete pubblica (pool FIP)"
  type        = string
  default     = "OPENSTACK_SHARED_PUBLIC"
}

variable "net_name" {
  type    = string
  default = "networkcyberguard"
}

variable "subnet_name" {
  type    = string
  default = "networkcyberguard-subnet"
}

variable "private_cidr" {
  type    = string
  default = "192.168.0.0/24"
}

variable "pool_start" {
  type    = string
  default = "192.168.0.100"
}

variable "pool_end" {
  type    = string
  default = "192.168.0.200"
}

variable "dns_nameservers" {
  type    = list(string)
  default = ["8.8.8.8", "1.1.1.1"]
}

# -------------------------------------------------------------------
# --- VM / Flavor CONFIGURATION --- 
# -------------------------------------------------------------------

# Flavor generica per Kali e Victim (bastano 2GB)
variable "flavor_name" {
  description = "Flavor base (es. t3.small)"
  type        = string
  default     = "t3.small"
}

# NUOVA VARIABILE: Flavor maggiorata per il SOC (Wazuh richiede 4GB+)
variable "soc_flavor_name" {
  description = "Flavor per la macchina SOC (richiede più RAM)"
  type        = string
  default     = "t3.medium"
}

variable "image_name" {
  description = "Nome immagine Kali"
  type        = string
  default     = "kali-linux-2025-cloud"
}

variable "vm_name" {
  description = "Nome della macchina virtuale"
  type        = string
  default     = "cyber_guard-attack"
}

variable "root_volume_gb" {
  description = "Dimensione del volume di root (GB)"
  type        = number
  default     = 30
}

# -------------------------------------------------------------------
# --- VM di log --- 
# -------------------------------------------------------------------
variable "log_image_name" {
  description = "Nome immagine per la macchina di log"
  type        = string
  default     = "ubuntu_cloud"
}

variable "log_vm_name" {
  description = "Nome della macchina virtuale di log"
  type        = string
  default     = "cyber_guard_log"
}

variable "log_root_volume_gb" {
  description = "Dimensione volume root VM di log"
  type        = number
  default     = 40
}

# -------------------------------------------------------------------
# --- VM Victim (Mr Robot) ---
# -------------------------------------------------------------------
variable "victim_image_name" {
  description = "Nome immagine per la VM vittima"
  type        = string
  default     = "mrrobot-fixed"
}

variable "victim_vm_name" {
  description = "Nome della macchina virtuale vittima"
  type        = string
  default     = "cyber_guard_victim"
}

variable "victim_root_volume_gb" {
  description = "Dimensione volume root VM vittima"
  type        = number
  default     = 30
}

# -------------------------------------------------------------------
# --- SSH / Keypair ---
# -------------------------------------------------------------------
variable "keypair_name" {
  description = "Nome della keypair SSH in OpenStack"
  type        = string
  default     = "cyberguard_ssh_key"
}