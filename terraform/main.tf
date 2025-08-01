# Cost-optimized GKE deployment for AgentVisa
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }
}

# Configure the Google Cloud Provider
provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "container.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "compute.googleapis.com"  # Required for GPU node pools
  ])
  
  project = var.project_id
  service = each.value
  
  disable_dependent_services = false
  disable_on_destroy        = false
}

# Artifact Registry for container images (cheaper than Container Registry)
resource "google_artifact_registry_repository" "agentVisa_repo" {
  location      = var.region
  repository_id = "agentvisa"
  description   = "AgentVisa container images"
  format        = "DOCKER"
  
  depends_on = [google_project_service.required_apis]
}

# Cost-optimized GKE cluster with preemptible nodes
resource "google_container_cluster" "agentVisa_cluster" {
  name     = "agentvisa-cluster"
  location = var.zone  # Zonal cluster is cheaper than regional
  
  # Minimum version for security
  min_master_version = "1.32.6-gke.1096000"
  
  # Allow deletion for cleanup
  deletion_protection = false
  
  # Remove default node pool (we'll create our own optimized one)
  remove_default_node_pool = true
  initial_node_count       = 1
  
  # Network configuration
  network    = "default"
  subnetwork = "default"
  
  # Enable workload identity for security
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }
  
  # Disable logging and monitoring for cost savings (enable only what you need)
  logging_config {
    enable_components = ["SYSTEM_COMPONENTS"]  # Minimal logging
  }
  
  monitoring_config {
    enable_components = ["SYSTEM_COMPONENTS"]  # Minimal monitoring
  }
  
  # Network policy for security
  network_policy {
    enabled = false  # Disable for cost savings
  }
  
  # Disable binary authorization for cost savings
  binary_authorization {
    evaluation_mode = "DISABLED"
  }
  
  depends_on = [google_project_service.required_apis]
}

# Cost-optimized node pool with preemptible instances
resource "google_container_node_pool" "agentVisa_nodes" {
  name       = "agentvisa-node-pool"
  location   = var.zone
  cluster    = google_container_cluster.agentVisa_cluster.name
  node_count = var.node_count
  
  # Auto-scaling configuration for availability and cost optimization
  autoscaling {
    min_node_count = var.min_node_count  # Ensure availability
    max_node_count = var.max_node_count  # Allow scaling for high load
  }
  
  # Management configuration
  management {
    auto_repair  = true
    auto_upgrade = true
  }
  
  node_config {
    # Use balanced cost-performance machine type
    machine_type = var.machine_type  # e2-standard-2 for better performance
    
    # Use preemptible instances for 60-80% cost savings
    preemptible = var.preemptible
    
    # Minimum disk size
    disk_size_gb = 20
    disk_type    = "pd-standard"  # Cheaper than SSD
    
    # OAuth scopes
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    
    # Resource labels for cost tracking
    labels = {
      environment = var.environment
      app         = "agentVisa"
    }
    
    # Workload identity
    workload_metadata_config {
      mode = "GKE_METADATA"
    }
    
    # Shielded instance features for security (free)
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
  }
  
  # Upgrade settings
  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }
}

# Configure Kubernetes provider
provider "kubernetes" {
  host                   = "https://${google_container_cluster.agentVisa_cluster.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.agentVisa_cluster.master_auth.0.cluster_ca_certificate)
}

data "google_client_config" "default" {}

# Reserve static IP for Ingress
resource "google_compute_global_address" "ingress_ip" {
  name         = "agentvisa-ingress-ip"
  description  = "Static IP for AgentVisa Ingress"
  
  depends_on = [google_project_service.required_apis]
}

# Create namespace
resource "kubernetes_namespace" "agentVisa" {
  metadata {
    name = "visa-app"
    labels = {
      name        = "visa-app"
      environment = var.environment
    }
  }
  
  depends_on = [google_container_node_pool.agentVisa_nodes]
}

# Note: GPU node pool removed - using CPU-only Ollama deployment
# Ollama will run on regular CPU nodes in the main node pool