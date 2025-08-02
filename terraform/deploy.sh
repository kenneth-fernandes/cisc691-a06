# !/bin/bash

# Cost-optimized GKE deployment script for AgentVisa using Terraform
# Estimated monthly cost: ~$102 (with preemptible nodes)

set -e

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

echo -e "${BLUE}🚀 AgentVisa GKE Deployment (Cost-Optimized)${NC}"
echo -e "${YELLOW}💰 Estimated monthly cost: ~$112 with 4x e2-medium nodes (LoadBalancer setup)${NC}"
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
            echo "Please set a project using one of these methods:"
            echo "  gcloud config set project your-gcp-project-id"
            echo "  export GCP_PROJECT_ID='your-gcp-project-id'"
            echo "  export GOOGLE_CLOUD_PROJECT='your-gcp-project-id'"
            exit 1
        fi
    else
        echo -e "${RED}❌ gcloud CLI not found and no PROJECT_ID set${NC}"
        echo "Please set PROJECT_ID: export GCP_PROJECT_ID='your-gcp-project-id'"
        exit 1
    fi
fi

# Get script directory and change to terraform directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check prerequisites
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"

if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform not found. Please install Terraform first.${NC}"
    exit 1
fi

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install Google Cloud SDK first.${NC}"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl not found. Please install kubectl first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites found${NC}"

# Set gcloud project
echo -e "${BLUE}⚙️  Setting up gcloud configuration...${NC}"
gcloud config set project $PROJECT_ID
gcloud auth application-default login --quiet 2>/dev/null || true

# Initialize Terraform
echo -e "${BLUE}🏗️  Initializing Terraform...${NC}"
terraform init

# Check for domain configuration
DOMAIN_NAME=""
echo -e "${BLUE}🌐 SSL/HTTPS Configuration${NC}"
echo ""
read -p "Do you want to set up HTTPS with SSL certificate? (requires domain) (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter your domain name (e.g., app.yourdomain.com): " DOMAIN_NAME
    if [ ! -z "$DOMAIN_NAME" ]; then
        echo -e "${GREEN}✅ Will create HTTPS setup for: $DOMAIN_NAME${NC}"
        echo -e "${YELLOW}⚠️  Remember to point your domain A record to the HTTPS IP after deployment${NC}"
        TERRAFORM_VARS="-var=project_id=$PROJECT_ID -var=region=$REGION -var=zone=$ZONE -var=domain_name=$DOMAIN_NAME"
        HTTPS_SETUP=true
    else
        echo -e "${YELLOW}📋 No domain provided, using HTTP-only LoadBalancer${NC}"
        TERRAFORM_VARS="-var=project_id=$PROJECT_ID -var=region=$REGION -var=zone=$ZONE"
        HTTPS_SETUP=false
    fi
else
    echo -e "${YELLOW}📋 Using HTTP-only LoadBalancer (simple setup)${NC}"
    TERRAFORM_VARS="-var=project_id=$PROJECT_ID -var=region=$REGION -var=zone=$ZONE"
    HTTPS_SETUP=false
fi

# Plan deployment
echo -e "${BLUE}📋 Planning Terraform deployment...${NC}"
terraform plan $TERRAFORM_VARS

# Ask for confirmation
echo ""
echo -e "${YELLOW}⚠️  This will create GKE resources that incur costs (estimated $112/month)${NC}"
echo -e "${YELLOW}Cost breakdown:${NC}"
echo -e "  • GKE cluster management: $74.40/month"
echo -e "  • 4x e2-medium preemptible nodes: $29.36/month"
echo -e "  • Storage (45GB total): $7.00/month (database only)"
echo -e "  • Networking (LoadBalancer service): $1.46/month"
echo -e "  • Note: Using LoadBalancer instead of Ingress (simpler setup)"
echo ""
read -p "Do you want to proceed with deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🛑 Deployment cancelled${NC}"
    exit 0
fi

# Apply Terraform
echo -e "${BLUE}🚀 Deploying infrastructure with Terraform...${NC}"
terraform apply $TERRAFORM_VARS -auto-approve

# Get cluster credentials
echo -e "${BLUE}🔑 Getting cluster credentials...${NC}"
gcloud container clusters get-credentials agentvisa-cluster --zone $ZONE --project $PROJECT_ID

# Build and push container images
echo -e "${BLUE}🏗️  Building and pushing container images...${NC}"
REGISTRY_URL="$REGION-docker.pkg.dev/$PROJECT_ID/agentvisa"

echo "🔧 Configuring gcloud for Kaniko builds..."
gcloud config set builds/use_kaniko True

echo "Building API image with latest code..."
cd ..
cp Dockerfile.api Dockerfile

# Build API image
gcloud builds submit --tag "$REGISTRY_URL/visa-app-api:latest" --no-cache .

# Clean up
rm Dockerfile

echo "Building Web image with latest code..."
cp Dockerfile.web Dockerfile

# Build Web image
gcloud builds submit --tag "$REGISTRY_URL/visa-app-web:latest" --no-cache .

# Clean up
rm Dockerfile
cd terraform


# Update Kubernetes manifests with actual registry URLs
echo -e "${BLUE}⚙️  Updating Kubernetes manifests...${NC}"
sed -i.bak "s|REGION-docker.pkg.dev/PROJECT_ID|$REGISTRY_URL|g" ../k8s/deployments/*.yaml
sed -i.bak "s|PROJECT_ID|$PROJECT_ID|g" ../k8s/deployments/*.yaml
sed -i.bak "s|REGION|$REGION|g" ../k8s/deployments/*.yaml

# Deploy in correct order for dependencies
echo -e "${BLUE}📋 Deploying Kubernetes resources in proper order...${NC}"

# 1. Create namespace first
echo -e "${BLUE}🏗️  Creating namespace...${NC}"
kubectl apply -f ../k8s/namespace.yaml

# 2. Deploy secrets (CRITICAL - with enhanced error handling)
echo -e "${BLUE}🔐 Deploying secrets...${NC}"

# Check if secrets file exists
if [ ! -f "../k8s/secrets/app-secrets.yaml" ]; then
    echo -e "${RED}❌ ERROR: app-secrets.yaml not found!${NC}"
    echo -e "${YELLOW}Creating secrets file from template...${NC}"
    
    if [ -f "../k8s/secrets/app-secrets.yaml.template" ]; then
        cp "../k8s/secrets/app-secrets.yaml.template" "../k8s/secrets/app-secrets.yaml"
        echo -e "${YELLOW}⚠️  IMPORTANT: You must update the secrets file with your actual API keys!${NC}"
        echo -e "${YELLOW}Edit: k8s/secrets/app-secrets.yaml${NC}"
        echo -e "${YELLOW}Replace placeholder values with base64-encoded secrets:${NC}"
        echo -e "  echo -n 'your_password' | base64"
        echo -e "  echo -n 'your_api_key' | base64"
        echo ""
        read -p "Have you updated the secrets file with real values? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo -e "${RED}❌ Please update the secrets file and run the deployment again${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ ERROR: app-secrets.yaml.template not found!${NC}"
        echo -e "${YELLOW}Please create k8s/secrets/app-secrets.yaml with your secrets${NC}"
        exit 1
    fi
fi

# Validate secrets file content
echo -e "${BLUE}🔍 Validating secrets file...${NC}"
if grep -q "REPLACE_WITH_BASE64_ENCODED" "../k8s/secrets/app-secrets.yaml"; then
    echo -e "${RED}❌ ERROR: Secrets file still contains placeholder values!${NC}"
    echo -e "${YELLOW}Please replace all REPLACE_WITH_BASE64_ENCODED values in:${NC}"
    echo -e "${YELLOW}k8s/secrets/app-secrets.yaml${NC}"
    echo ""
    echo -e "${BLUE}💡 Generate base64 values with:${NC}"
    echo -e "  echo -n 'your_actual_password' | base64"
    echo -e "  echo -n 'your_actual_api_key' | base64"
    exit 1
fi

# Apply secrets with comprehensive error handling
echo -e "${BLUE}✅ Applying secrets...${NC}"
if ! kubectl apply -f ../k8s/secrets/app-secrets.yaml; then
    echo -e "${RED}❌ ERROR: Failed to apply secrets!${NC}"
    echo -e "${YELLOW}Common issues and solutions:${NC}"
    echo -e "  1. Invalid YAML syntax - check indentation"
    echo -e "  2. Invalid base64 encoding - regenerate with: echo -n 'value' | base64"
    echo -e "  3. Namespace not ready - wait a moment and retry"
    echo ""
    echo -e "${BLUE}🔧 Debug commands:${NC}"
    echo -e "  kubectl apply --dry-run=client -f ../k8s/secrets/app-secrets.yaml"
    echo -e "  ../k8s/validate-secrets.sh"
    exit 1
fi

echo -e "${GREEN}✅ Secrets deployed successfully${NC}"

# Verify secrets are properly deployed
echo -e "${BLUE}🔍 Verifying secrets deployment...${NC}"
if kubectl get secret app-secrets -n visa-app > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Secrets successfully created in cluster${NC}"
    secret_count=$(kubectl get secret app-secrets -n visa-app -o jsonpath='{.data}' | jq -r 'keys | length' 2>/dev/null || echo "unknown")
    echo -e "${BLUE}📊 Secret contains $secret_count keys${NC}"
else
    echo -e "${RED}❌ ERROR: Secrets not found in cluster after deployment${NC}"
    exit 1
fi

# 3. Deploy config maps
echo -e "${BLUE}⚙️  Deploying config maps...${NC}"
kubectl apply -f ../k8s/configmaps/

# 4. Deploy volumes (database storage only)
echo -e "${BLUE}💾 Setting up persistent volumes...${NC}"

# Check and fix storage classes for GKE compatibility
echo -e "${BLUE}🔍 Checking available storage classes...${NC}"
AVAILABLE_STORAGE_CLASSES=$(kubectl get storageclass -o name | sed 's/storageclass.storage.k8s.io\///')
DEFAULT_STORAGE_CLASS=$(kubectl get storageclass -o jsonpath='{.items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")].metadata.name}')
echo -e "${GREEN}✅ Default storage class: $DEFAULT_STORAGE_CLASS${NC}"

# Deploy remaining volume configurations (if any)
if [ -d "../k8s/volumes" ] && [ "$(ls -A ../k8s/volumes 2>/dev/null)" ]; then
    kubectl apply -f ../k8s/volumes/
else
    echo -e "${BLUE}💾 No additional volumes to deploy${NC}"
fi

# 5. Deploy PostgreSQL and Redis first (databases)
echo -e "${BLUE}🗄️  Deploying databases...${NC}"
kubectl apply -f ../k8s/deployments/postgres.yaml
kubectl apply -f ../k8s/services/postgres-service.yaml
kubectl apply -f ../k8s/deployments/redis.yaml
kubectl apply -f ../k8s/services/redis-service.yaml

# Wait for databases to be ready
echo -e "${BLUE}⏳ Waiting for databases to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=postgres -n visa-app --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n visa-app --timeout=300s

# 6. Deploy API and Web services
echo -e "${BLUE}🚀 Deploying application services...${NC}"
kubectl apply -f ../k8s/deployments/api.yaml
kubectl apply -f ../k8s/services/api-service.yaml
kubectl apply -f ../k8s/deployments/web.yaml
kubectl apply -f ../k8s/services/web-service.yaml

# 7. Deploy autoscaling components (HPA only)
echo -e "${BLUE}🔄 Setting up horizontal pod autoscaling...${NC}"
echo -e "${BLUE}ℹ️  Note: Node autoscaling managed by GKE, VPA not required${NC}"
kubectl apply -f ../k8s/autoscaling/ 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Some autoscaling resources may not be available - continuing deployment${NC}"
    # Apply individual HPA files to avoid issues
    kubectl apply -f ../k8s/autoscaling/api-hpa.yaml 2>/dev/null || true
    kubectl apply -f ../k8s/autoscaling/web-hpa.yaml 2>/dev/null || true
}





# 8. Deploy external access services
echo -e "${BLUE}🌐 Setting up external access services...${NC}"

# Always deploy HTTP LoadBalancer service
kubectl apply -f ../k8s/services/web-lb.yaml

if [ "$HTTPS_SETUP" = true ]; then
    echo -e "${BLUE}🔒 Setting up NodePort service for HTTPS Load Balancer...${NC}"
    kubectl apply -f ../k8s/services/web-nodeport-ssl.yaml
    
    echo -e "${BLUE}⏳ Waiting for HTTPS Load Balancer to be ready...${NC}"
    echo "This may take 5-10 minutes for SSL certificate provisioning..."
    
    # Get HTTPS IP from Terraform output
    HTTPS_IP=$(terraform output -raw https_ip 2>/dev/null || echo "")
    if [ ! -z "$HTTPS_IP" ] && [ "$HTTPS_IP" != "Not created" ]; then
        echo -e "${GREEN}✅ HTTPS Load Balancer IP: $HTTPS_IP${NC}"
        echo -e "${YELLOW}⚠️  IMPORTANT: Point $DOMAIN_NAME A record to: $HTTPS_IP${NC}"
        echo -e "${YELLOW}⏳ SSL certificate will be issued after DNS propagation (5-15 minutes)${NC}"
    fi
else
    echo -e "${BLUE}📋 HTTP-only setup selected${NC}"
fi

echo -e "${BLUE}⏳ Waiting for HTTP LoadBalancer IP to be assigned...${NC}"
echo "This may take 1-2 minutes..."

# Wait for LoadBalancer IP (max 5 minutes)
TIMEOUT=300
COUNTER=0
LB_IP=""

while [ $COUNTER -lt $TIMEOUT ] && [ -z "$LB_IP" ]; do
    sleep 10
    LB_IP=$(kubectl get service web-lb -n visa-app -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)
    COUNTER=$((COUNTER + 10))
    if [ -z "$LB_IP" ]; then
        echo -n "."
    fi
done

echo ""
if [ ! -z "$LB_IP" ]; then
    echo -e "${GREEN}✅ HTTP LoadBalancer IP assigned: $LB_IP${NC}"
else
    echo -e "${YELLOW}⚠️  LoadBalancer IP not yet assigned, check manually with: kubectl get service web-lb -n visa-app${NC}"
fi

# 9. Deploy data collection job and CronJob
echo -e "${BLUE}📊 Deploying visa data collection job...${NC}"
kubectl apply -f ../k8s/jobs/visa-data-collection.yaml

echo -e "${BLUE}⏰ Setting up daily data synchronization CronJob...${NC}"
kubectl apply -f ../k8s/cronjobs/visa-data-sync.yaml

echo -e "${BLUE}🚀 Starting initial data collection...${NC}"
echo "This will populate the database with visa bulletin data from 2020-2025"
echo "Monitor with: kubectl logs job/visa-data-collection -n visa-app -f"

# Force restart deployments to use latest images
echo -e "${BLUE}🔄 Restarting deployments to use latest images...${NC}"
kubectl rollout restart deployment/api -n visa-app
kubectl rollout restart deployment/web -n visa-app

# Wait for application deployments to be ready
echo -e "${BLUE}⏳ Waiting for application deployments to be ready...${NC}"
kubectl rollout status deployment/api -n visa-app --timeout=250s
kubectl rollout status deployment/web -n visa-app --timeout=250s
# kubectl wait --for=condition=ready pod -l app=api -n visa-app --timeout=250s
# kubectl wait --for=condition=ready pod -l app=web -n visa-app --timeout=250s


# Check autoscaling status
echo -e "${BLUE}🔄 Checking autoscaling status...${NC}"
kubectl get hpa -n visa-app

# Verify the web app has the fixed code
echo -e "${BLUE}🔍 Verifying web app has latest code with fixed data status...${NC}"
kubectl exec -n visa-app deployment/web -- python -c "
import sys; sys.path.append('/app/src')
from ui.utils.api_client import get_api_client
api = get_api_client()
db_stats = api.get_database_stats()
total = db_stats.get('total_bulletins', 'N/A')
latest = db_stats.get('database_stats', {}).get('latest_bulletin', 'N/A')
print(f'✅ Web app data status: {total} records available | Latest: {latest}')
if total != 'N/A' and latest != 'N/A':
    print('✅ Fix verified: Web app should now show correct data!')
else:
    print('❌ Fix not working: Web app still shows N/A')
" || echo "⚠️  Could not verify fix - check manually"

# Get deployment status
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo -e "${BLUE}📊 Deployment Status:${NC}"
kubectl get pods -n visa-app
echo ""
kubectl get services -n visa-app
echo ""

# Get LoadBalancer IP for access instructions
echo -e "${BLUE}🔍 Getting access information...${NC}"
FINAL_LB_IP=$(kubectl get service web-lb -n visa-app -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
FINAL_HTTPS_IP=$(terraform output -raw https_ip 2>/dev/null || echo "")

# Display access instructions
echo -e "${GREEN}🌐 Access Instructions:${NC}"

if [ "$HTTPS_SETUP" = true ] && [ ! -z "$FINAL_HTTPS_IP" ] && [ "$FINAL_HTTPS_IP" != "Not created" ]; then
    echo -e "${GREEN}✅ HTTPS Load Balancer IP: $FINAL_HTTPS_IP${NC}"
    echo -e "${GREEN}✅ HTTP LoadBalancer IP: $FINAL_LB_IP${NC}"
    echo ""
    echo -e "${BLUE}🔒 HTTPS URLs (after DNS setup):${NC}"
    echo "   Web Application: https://$DOMAIN_NAME"
    echo "   API Backend: https://$DOMAIN_NAME/api (routes through web service)"
    echo ""
    echo -e "${BLUE}🌐 HTTP URLs (available now):${NC}"
    echo "   Web Application: http://$FINAL_LB_IP"
    echo "   API Backend: http://$FINAL_LB_IP/api (routes through web service)"
    echo ""
    echo -e "${YELLOW}⚠️  HTTPS Setup Required:${NC}"
    echo "   1. Point $DOMAIN_NAME A record to: $FINAL_HTTPS_IP"
    echo "   2. Wait for DNS propagation (1-24 hours)"
    echo "   3. SSL certificate will be issued automatically (5-15 minutes after DNS)"
    echo ""
    echo -e "${BLUE}🔧 SSL Certificate Status:${NC}"
    echo "   • Check status: gcloud compute ssl-certificates describe agentvisa-ssl-cert"
    echo "   • Check load balancer: gcloud compute forwarding-rules list"
    echo "   • Test HTTPS: curl -I https://$DOMAIN_NAME (after DNS setup)"
elif [ ! -z "$FINAL_LB_IP" ]; then
    echo -e "${GREEN}✅ HTTP LoadBalancer IP: $FINAL_LB_IP${NC}"
    echo ""
    echo -e "${BLUE}🌐 Application URLs:${NC}"
    echo "   Web Application: http://$FINAL_LB_IP"
    echo "   API Backend: http://$FINAL_LB_IP/api (routes through web service)"
    echo "   Direct API Access: kubectl port-forward service/api 8000:8000 -n visa-app"
    echo ""
    echo -e "${YELLOW}💡 Note: Using HTTP LoadBalancer (simple and reliable)${NC}"
    echo "   To add HTTPS later, redeploy with domain configuration"
else
    echo -e "${YELLOW}⚠️  LoadBalancer IP not yet assigned. Using port-forward for access:${NC}"
    echo ""
    echo -e "${BLUE}🔧 Port Forward Commands:${NC}"
    echo "   kubectl port-forward service/web 8501:8501 -n visa-app &"
    echo "   kubectl port-forward service/api 8000:8000 -n visa-app &"
    echo "   Then access:"
    echo "   • Web: http://localhost:8501"
    echo "   • API: http://localhost:8000"
    echo ""
    echo -e "${BLUE}🔍 Check LoadBalancer status:${NC}"
    echo "   kubectl get service web-lb -n visa-app"
fi

echo ""
echo -e "${BLUE}🔧 General Troubleshooting:${NC}"
echo "   • Check all services: kubectl get services -n visa-app"
echo "   • Check pods: kubectl get pods -n visa-app"
echo "   • View logs: kubectl logs deployment/web -n visa-app"
echo ""

# Display monitoring commands
echo -e "${GREEN}📊 Data Collection Monitoring:${NC}"
echo "kubectl get jobs -n visa-app                          # Check job status"
echo "kubectl logs job/visa-data-collection -n visa-app -f  # Follow initial data collection"
echo "kubectl get cronjobs -n visa-app                      # Check daily sync schedule"
echo "kubectl get pods -n visa-app -l job-name=visa-data-collection  # Check collection pods"
echo ""
echo -e "${GREEN}💰 Cost Monitoring:${NC}"
echo "kubectl top nodes"
echo "kubectl top pods -n visa-app"
echo "kubectl get hpa -n visa-app  # Check autoscaling status"
echo "kubectl describe nodes      # Check node utilization"
echo "kubectl get nodes -o wide  # Check all nodes"
echo ""

# Note: Ollama removed from GKE deployment for cost optimization
echo -e "${BLUE}📝 For Ollama usage, deploy locally or use external API providers${NC}"
echo ""

# Display cleanup instructions
echo -e "${GREEN}🧹 Cleanup Instructions:${NC}"
echo "To destroy all resources and stop charges:"
echo "terraform destroy -var=\"project_id=$PROJECT_ID\" -var=\"region=$REGION\" -var=\"zone=$ZONE\""
echo ""

echo -e "${GREEN}🎉 AgentVisa is now running on GKE!${NC}"