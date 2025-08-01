# Terraform variables for cost-optimized GKE deployment

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"  # Cheapest region
}

variable "zone" {
  description = "The GCP zone for zonal cluster (cheaper than regional)"
  type        = string
  default     = "us-central1-a"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "machine_type" {
  description = "Machine type for GKE nodes"
  type        = string
  default     = "e2-standard-2"  # 2 vCPU, 8GB RAM - balanced cost/performance
  validation {
    condition = contains([
      "e2-medium",     # 2 vCPU, 4GB RAM - $24.45/month
      "e2-standard-2", # 2 vCPU, 8GB RAM - $48.90/month
      "e2-standard-4"  # 4 vCPU, 16GB RAM - $97.81/month
    ], var.machine_type)
    error_message = "Machine type must be cost-effective e2 series with adequate resources."
  }
}

variable "node_count" {
  description = "Initial number of nodes in the cluster"
  type        = number
  default     = 4  # Updated to 4 nodes
  validation {
    condition     = var.node_count >= 1 && var.node_count <= 5
    error_message = "Node count must be between 1 and 5 for cost optimization."
  }
}

variable "max_node_count" {
  description = "Maximum number of nodes for autoscaling"
  type        = number
  default     = 4  # Updated to 4 nodes
}

variable "min_node_count" {
  description = "Minimum number of nodes for autoscaling"
  type        = number
  default     = 2  # Ensure high availability
}

variable "preemptible" {
  description = "Use preemptible instances for 60-80% cost savings"
  type        = bool
  default     = true
}

variable "disk_size_gb" {
  description = "Disk size in GB for each node"
  type        = number
  default     = 20  # Minimum for cost savings
}

variable "artifact_registry_location" {
  description = "Location for Artifact Registry"
  type        = string
  default     = "us-central1"
}

variable "custom_domain" {
  description = "Custom domain for the application (leave empty for IP-only access)"
  type        = string
  default     = "app.myagentvisa.com"  # Set to your domain like 'myapp.example.com' to enable HTTPS
}

# Cost estimation variables (no Ollama deployment)
# Ollama removed from GKE for cost optimization

variable "estimated_monthly_cost" {
  description = "Estimated monthly cost breakdown (no Ollama, 3 nodes)"
  type = object({
    cluster_management = string
    nodes_preemptible  = string  
    storage           = string
    networking        = string
    total_estimated   = string
  })
  default = {
    cluster_management = "$74.40"    # GKE cluster management fee
    nodes_preemptible  = "$22.02"    # 3x e2-medium preemptible nodes
    storage           = "$7.00"      # Persistent disks (database only, no Ollama)
    networking        = "$5.00"      # Load balancer + egress
    total_estimated   = "$88.42"     # Total monthly estimate (no Ollama, 3 nodes)
  }
}