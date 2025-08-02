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
  min_master_version = var.kubernetes_version
  
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

# SSL Certificate for HTTPS Load Balancer
resource "google_compute_managed_ssl_certificate" "agentvisa_ssl" {
  name = "agentvisa-ssl-cert"
  
  managed {
    domains = [var.domain_name]
  }
  
  # Only create if domain is provided
  count = var.domain_name != "" ? 1 : 0
}

# Static IP for HTTPS Load Balancer
resource "google_compute_global_address" "https_lb_ip" {
  name        = "agentvisa-https-ip"
  description = "Static IP for HTTPS Load Balancer"
  
  # Only create if domain is provided
  count = var.domain_name != "" ? 1 : 0
}

# Get instance group for backend service
data "google_compute_instance_group" "agentvisa_ig" {
  name = split("/", google_container_node_pool.agentVisa_nodes.instance_group_urls[0])[length(split("/", google_container_node_pool.agentVisa_nodes.instance_group_urls[0])) - 1]
  zone = var.zone
  
  # Only create if domain is provided
  count = var.domain_name != "" ? 1 : 0
}

# Backend service pointing to GKE nodes
resource "google_compute_backend_service" "agentvisa_backend" {
  name                    = "agentvisa-backend"
  protocol                = "HTTP"
  port_name               = "http"
  load_balancing_scheme   = "EXTERNAL"
  timeout_sec             = 30
  enable_cdn              = false
  
  backend {
    group = data.google_compute_instance_group.agentvisa_ig[0].self_link
    balancing_mode = "RATE"
    max_rate_per_instance = 100
  }
  
  health_checks = [google_compute_health_check.agentvisa_health[0].id]
  
  # Only create if domain is provided
  count = var.domain_name != "" ? 1 : 0
  
  depends_on = [data.google_compute_instance_group.agentvisa_ig]
}

# Health check for backend service
resource "google_compute_health_check" "agentvisa_health" {
  name               = "agentvisa-health-check"
  check_interval_sec = 10
  timeout_sec        = 5
  healthy_threshold  = 2
  unhealthy_threshold = 3
  
  http_health_check {
    port               = 30001  # NodePort for web service
    request_path       = "/_stcore/health"
    proxy_header       = "NONE"
  }
  
  # Only create if domain is provided
  count = var.domain_name != "" ? 1 : 0
}

# URL map for routing
resource "google_compute_url_map" "agentvisa_url_map" {
  name            = "agentvisa-url-map"
  default_service = google_compute_backend_service.agentvisa_backend[0].id
  
  # Only create if domain is provided
  count = var.domain_name != "" ? 1 : 0
}

# HTTPS proxy
resource "google_compute_target_https_proxy" "agentvisa_https_proxy" {
  name    = "agentvisa-https-proxy"
  url_map = google_compute_url_map.agentvisa_url_map[0].id
  ssl_certificates = [google_compute_managed_ssl_certificate.agentvisa_ssl[0].id]
  
  # Only create if domain is provided
  count = var.domain_name != "" ? 1 : 0
}

# HTTP proxy for redirect
resource "google_compute_target_http_proxy" "agentvisa_http_proxy" {
  name    = "agentvisa-http-proxy"
  url_map = google_compute_url_map.agentvisa_redirect[0].id
  
  # Only create if domain is provided
  count = var.domain_name != "" ? 1 : 0
}

# URL map for HTTP to HTTPS redirect
resource "google_compute_url_map" "agentvisa_redirect" {
  name = "agentvisa-redirect"
  
  default_url_redirect {
    https_redirect = true
    strip_query    = false
  }
  
  # Only create if domain is provided
  count = var.domain_name != "" ? 1 : 0
}

# HTTPS forwarding rule
resource "google_compute_global_forwarding_rule" "agentvisa_https" {
  name       = "agentvisa-https-forwarding-rule"
  target     = google_compute_target_https_proxy.agentvisa_https_proxy[0].id
  port_range = "443"
  ip_address = google_compute_global_address.https_lb_ip[0].address
  
  # Only create if domain is provided
  count = var.domain_name != "" ? 1 : 0
}

# HTTP forwarding rule (for redirect)
resource "google_compute_global_forwarding_rule" "agentvisa_http" {
  name       = "agentvisa-http-forwarding-rule"
  target     = google_compute_target_http_proxy.agentvisa_http_proxy[0].id
  port_range = "80"
  ip_address = google_compute_global_address.https_lb_ip[0].address
  
  # Only create if domain is provided
  count = var.domain_name != "" ? 1 : 0
}

# Note: Also keeping simple LoadBalancer service for non-SSL access

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