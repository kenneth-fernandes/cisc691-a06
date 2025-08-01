# Terraform outputs for GKE deployment

output "cluster_name" {
  description = "Name of the GKE cluster"
  value       = google_container_cluster.agentVisa_cluster.name
}

output "cluster_endpoint" {
  description = "Endpoint of the GKE cluster"
  value       = google_container_cluster.agentVisa_cluster.endpoint
  sensitive   = true
}

output "cluster_location" {
  description = "Location of the GKE cluster"
  value       = google_container_cluster.agentVisa_cluster.location
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.agentVisa_repo.repository_id}"
}

output "kubeconfig_command" {
  description = "Command to configure kubectl"
  value       = "gcloud container clusters get-credentials ${google_container_cluster.agentVisa_cluster.name} --zone ${var.zone} --project ${var.project_id}"
}

output "build_and_push_commands" {
  description = "Commands to build and push container images"
  value = {
    api_image = "gcloud builds submit --tag ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.agentVisa_repo.repository_id}/visa-app-api:latest --file Dockerfile.api ."
    web_image = "gcloud builds submit --tag ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.agentVisa_repo.repository_id}/visa-app-web:latest --file Dockerfile.web ."
  }
}

output "cost_optimization_summary" {
  description = "Cost optimization features enabled"
  value = {
    cluster_type        = "Zonal (cheaper than regional)"
    node_type          = "Preemptible (60-80% savings)"
    machine_type       = var.machine_type
    node_count         = "${var.min_node_count}-${var.max_node_count} (autoscaling)"
    storage_type       = "Standard persistent disk"
    registry_type      = "Artifact Registry"
    managed_services   = "None (using pods for DB/Redis)"
    estimated_monthly  = var.estimated_monthly_cost.total_estimated
  }
}

output "ingress_ip" {
  description = "Static IP address for Ingress"
  value       = google_compute_global_address.ingress_ip.address
}

output "access_instructions" {
  description = "Instructions to access the deployed application"
  value = {
    get_kubeconfig   = "gcloud container clusters get-credentials ${google_container_cluster.agentVisa_cluster.name} --zone ${var.zone} --project ${var.project_id}"
    check_pods       = "kubectl get pods -n visa-app"
    get_services     = "kubectl get services -n visa-app"
    ingress_ip       = google_compute_global_address.ingress_ip.address
    setup_dns        = "Point your domain A record to: ${google_compute_global_address.ingress_ip.address}"
  }
}

output "monitoring_commands" {
  description = "Commands to monitor costs and usage"
  value = {
    cluster_cost  = "gcloud billing budgets list --billing-account=YOUR_BILLING_ACCOUNT"
    node_usage    = "kubectl top nodes"
    pod_usage     = "kubectl top pods -n visa-app"
    cluster_info  = "kubectl cluster-info"
  }
}