variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
  default     = "k8slab-rg"
}

variable "vnet_cidr" {
  description = "VNet address space"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vnet_cidr, 0))
    error_message = "vnet_cidr must be a valid CIDR, for example 10.0.0.0/16."
  }
}

variable "subnet_cidr" {
  description = "Subnet address prefix"
  type        = string
  default     = "10.0.1.0/24"

  validation {
    condition     = can(cidrhost(var.subnet_cidr, 0))
    error_message = "subnet_cidr must be a valid CIDR, for example 10.0.1.0/24."
  }
}

variable "vm_size" {
  description = "Azure VM size (2 vCPU, 4 GB RAM)"
  type        = string
  default     = "Standard_B2s"
}

variable "admin_username" {
  description = "Admin user created on the VMs"
  type        = string
  default     = "rocky"
}

variable "ssh_public_key" {
  description = "Contents of your public key (k8slab_key.pub)"
  type        = string
}

variable "my_public_ip" {
  description = "Your public IP in CIDR form, for example 203.0.113.10/32"
  type        = string

  validation {
    condition     = can(cidrhost(var.my_public_ip, 0))
    error_message = "my_public_ip must be a valid CIDR, for example 203.0.113.10/32."
  }
}

variable "nodes" {
  description = "Cluster nodes"
  type = map(object({
    hostname   = string
    private_ip = string
  }))
  default = {
    cp1 = {
      hostname   = "k8slab-cp1"
      private_ip = "10.0.1.10"
    }
    w1 = {
      hostname   = "k8slab-w1"
      private_ip = "10.0.1.11"
    }
  }

  validation {
    condition     = alltrue([for n in var.nodes : can(cidrhost("${n.private_ip}/32", 0))])
    error_message = "Every node private_ip must be a valid IPv4 address."
  }
}
