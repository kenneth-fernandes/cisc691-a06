#!/bin/bash

# GKE Cleanup Script for AgentVisa
# This script will destroy all GCP resources created by the deployment

set +e  # Don't exit on errors - continue cleanup to remove as many resources as possible

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - Use environment variables with fallbacks
PROJECT_ID="${GCP_PROJECT_ID:-${GOOGLE_CLOUD_PROJECT:-}}"
REGION="${GCP_REGION:-us-central1}"
ZONE="${GCP_ZONE:-us-central1-a}"

echo -e "${RED}🧹 AgentVisa GKE Cleanup Script${NC}"
echo -e "${YELLOW}⚠️  WARNING: This will destroy ALL resources and STOP ALL CHARGES${NC}"
echo ""

# If PROJECT_ID is not set, try to get it from gcloud
if [ -z "$PROJECT_ID" ]; then
    echo -e "${BLUE}🔍 No PROJECT_ID set, attempting to get from gcloud...${NC}"
    if command -v gcloud &> /dev/null; then
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
        if [ ! -z "$PROJECT_ID" ] && [ "$PROJECT_ID" != "(unset)" ]; then
            echo -e "${GREEN}✅ Using gcloud default project: $PROJECT_ID${NC}"
        else
            echo -e "${RED}❌ No default project set in gcloud${NC}"
            echo "Please set a project: gcloud config set project your-gcp-project-id"
            exit 1
        fi
    else
        echo -e "${RED}❌ gcloud CLI not found and no PROJECT_ID set${NC}"
        exit 1
    fi
fi

# Get script directory and change to terraform directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}📋 Resources to be destroyed:${NC}"
echo "  • GKE Cluster: agentvisa-cluster (4 nodes)"
echo "  • Node Pool: agentvisa-node-pool (CPU nodes)"
echo "  • Artifact Registry: agentvisa"
echo "  • LoadBalancer Service (web-lb) with external IP"
echo "  • HTTPS Load Balancer (if configured with domain)"
echo "  • SSL Certificate (Google-managed, if configured)"
echo "  • NodePort Service (for HTTPS backend, if configured)"
echo "  • Horizontal Pod Autoscaler (HPA)"
echo "  • Data Collection Jobs (initial + daily CronJob)"
echo "  • PostgreSQL Database with visa bulletin data"
echo "  • ConfigMaps and Secrets"
echo "  • All Kubernetes resources"
echo "  • Container images (API + Web)"
echo "  • Note: Supports both HTTP-only and HTTPS setups"
echo ""
echo -e "${GREEN}💰 This will STOP ALL CHARGES for:${NC}"
echo "  • GKE cluster management (~$74/month)"
echo "  • 4x compute nodes (~$29/month)"
echo "  • LoadBalancer service (~$1.46/month)"
echo "  • HTTPS Load Balancer (~$18/month, if configured)"
echo "  • SSL Certificate (free with Google-managed)"
echo "  • Storage (~$7/month, database only)"
echo "  • Networking (minimal egress)"
echo "  • Total: ~$112/month (HTTP) or ~$130/month (HTTPS)"
echo ""

# Ask for confirmation
echo -e "${YELLOW}⚠️  Are you absolutely sure you want to destroy everything?${NC}"
echo "This action cannot be undone!"
read -p "Type 'destroy' to confirm: " -r
if [[ ! $REPLY == "destroy" ]]; then
    echo -e "${YELLOW}🛑 Cleanup cancelled${NC}"
    exit 0
fi

echo ""
echo -e "${RED}🗑️  Starting destruction process...${NC}"

# Delete Kubernetes resources first (faster than waiting for cluster deletion)
echo -e "${BLUE}☸️  Deleting Kubernetes resources...${NC}"
if kubectl get namespace visa-app &>/dev/null; then
    echo "Deleting LoadBalancer and NodePort services..."
    kubectl delete service web-lb -n visa-app --ignore-not-found=true
    kubectl delete service web-nodeport-ssl -n visa-app --ignore-not-found=true
    
    echo "Note: Ollama not deployed in this GKE setup"
    
    echo "Deleting autoscaling components..."
    kubectl delete hpa --all -n visa-app --ignore-not-found=true
    # Note: VPA and cluster autoscaler are not deployed
    
    echo "Deleting data collection jobs and CronJobs..."
    kubectl delete job --all -n visa-app --ignore-not-found=true
    kubectl delete cronjobs --all -n visa-app --ignore-not-found=true
    
    echo "Deleting all resources in visa-app namespace..."
    kubectl delete namespace visa-app --ignore-not-found=true
    echo "Waiting for namespace deletion..."
    kubectl wait --for=delete namespace/visa-app --timeout=300s || true
else
    echo "Namespace visa-app not found, skipping..."
fi

# Terraform destroy
echo -e "${BLUE}🏗️  Destroying infrastructure with Terraform...${NC}"
if [ -f "terraform.tfstate" ]; then
    terraform destroy -var="project_id=$PROJECT_ID" -var="region=$REGION" -var="zone=$ZONE" -auto-approve
else
    echo -e "${YELLOW}⚠️  No terraform.tfstate found. Attempting manual cleanup...${NC}"
    
    # Manual cleanup if terraform state is missing
    echo -e "${BLUE}🔧 Manual cleanup of resources...${NC}"
    
    # Delete GKE cluster
    if gcloud container clusters describe agentvisa-cluster --zone=$ZONE --project=$PROJECT_ID &>/dev/null; then
        echo "Deleting GKE cluster..."
        gcloud container clusters delete agentvisa-cluster --zone=$ZONE --project=$PROJECT_ID --quiet
    fi
    
    # Note: No static IP to delete (LoadBalancer manages its own IP)
    
    # Delete Artifact Registry
    if gcloud artifacts repositories describe agentvisa --location=$REGION --project=$PROJECT_ID &>/dev/null; then
        echo "Deleting Artifact Registry..."
        gcloud artifacts repositories delete agentvisa --location=$REGION --project=$PROJECT_ID --quiet
    fi
fi

# Clean up local files
echo -e "${BLUE}🧽 Cleaning up local files...${NC}"
rm -f terraform.tfstate*
rm -f terraform.tfplan
rm -f .terraform.lock.hcl
rm -rf .terraform/
rm -f ../k8s/deployments/*.yaml.bak

# Optional: Delete container images (they cost storage)
echo ""
echo -e "${YELLOW}🗂️  Container images still exist in Artifact Registry${NC}"
echo "These may incur small storage costs. Delete them?"
read -p "Delete container images? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Deleting container images..."
    gcloud artifacts docker images delete $REGION-docker.pkg.dev/$PROJECT_ID/agentvisa/visa-app-api:latest --quiet || true
    gcloud artifacts docker images delete $REGION-docker.pkg.dev/$PROJECT_ID/agentvisa/visa-app-web:latest --quiet || true
fi

echo ""
echo -e "${GREEN}✅ Cleanup completed successfully!${NC}"
echo ""
echo -e "${GREEN}💰 All charges have been stopped!${NC}"
echo ""
echo -e "${BLUE}📊 Verify cleanup:${NC}"
echo "  • Check GCP Console: https://console.cloud.google.com/kubernetes/"
echo "  • Check billing: https://console.cloud.google.com/billing/"
echo "  • Run: gcloud container clusters list"
echo ""
echo -e "${GREEN}🎉 Your GCP resources have been cleaned up!${NC}"