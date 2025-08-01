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
echo -e "${YELLOW}💰 Estimated monthly cost: ~$116 with 4x e2-medium nodes (no Ollama)${NC}"
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

# Plan deployment
echo -e "${BLUE}📋 Planning Terraform deployment...${NC}"
terraform plan -var="project_id=$PROJECT_ID" -var="region=$REGION" -var="zone=$ZONE"

# Ask for confirmation
echo ""
echo -e "${YELLOW}⚠️  This will create GKE resources that incur costs (estimated $116/month)${NC}"
echo -e "${YELLOW}Cost breakdown:${NC}"
echo -e "  • GKE cluster management: $74.40/month"
echo -e "  • 4x e2-medium preemptible nodes: $29.36/month"
echo -e "  • Storage (45GB total): $7.00/month (database only)"
echo -e "  • Networking (Load Balancer + Ingress): $5.00/month"
echo -e "  • Note: Ollama removed from GKE for cost optimization"
echo ""
read -p "Do you want to proceed with deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🛑 Deployment cancelled${NC}"
    exit 0
fi

# Apply Terraform
echo -e "${BLUE}🚀 Deploying infrastructure with Terraform...${NC}"
terraform apply -var="project_id=$PROJECT_ID" -var="region=$REGION" -var="zone=$ZONE" -auto-approve

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





# 8. Configure and deploy secure Ingress with SSL
echo -e "${BLUE}🔒 Setting up secure Ingress with SSL...${NC}"

# Check for custom domain configuration from terraform.tfvars
CUSTOM_DOMAIN=$(grep '^custom_domain' terraform.tfvars | cut -d'=' -f2 | tr -d ' "')

if [ ! -z "$CUSTOM_DOMAIN" ] && [ "$CUSTOM_DOMAIN" != "" ]; then
    echo -e "${GREEN}🌐 Found custom domain in config: $CUSTOM_DOMAIN${NC}"
    echo -e "${BLUE}🔒 Configuring SSL certificate for domain: $CUSTOM_DOMAIN${NC}"
    
    # Update the ManagedCertificate with the domain
    sed -i.bak "s|# - \"your-domain.com\"  # Replace with your actual domain|- \"$CUSTOM_DOMAIN\"|g" ../k8s/ingress/ingress.yaml
    sed -i.bak "/# IMPORTANT: Replace with your actual domain name/d" ../k8s/ingress/ingress.yaml
    sed -i.bak "/# If you don't have a domain, comment out this section/d" ../k8s/ingress/ingress.yaml
    sed -i.bak "/# and use the static IP directly for access/d" ../k8s/ingress/ingress.yaml
    
    # Add host rule to ingress for the domain
    sed -i.bak "s|  rules:|  rules:\n  - host: $CUSTOM_DOMAIN\n    http:\n      paths:\n      - path: /api/*\n        pathType: ImplementationSpecific\n        backend:\n          service:\n            name: api\n            port:\n              number: 8000\n      - path: /*\n        pathType: ImplementationSpecific\n        backend:\n          service:\n            name: web\n            port:\n              number: 8501|" ../k8s/ingress/ingress.yaml
    
    USING_DOMAIN=true
    DOMAIN_NAME="$CUSTOM_DOMAIN"
    
    echo -e "${YELLOW}⚠️  Remember to set up DNS: Point $CUSTOM_DOMAIN A record to the static IP${NC}"
else
    echo -e "${BLUE}📝 No custom domain configured in terraform.tfvars${NC}"
    
    # Check if user wants to use a custom domain
echo ""
read -p "Do you have a custom domain to use? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter your domain name (e.g., app.yourdomain.com): " DOMAIN_NAME
    if [ ! -z "$DOMAIN_NAME" ]; then
        echo -e "${BLUE}🌐 Configuring SSL certificate for domain: $DOMAIN_NAME${NC}"
        # Update the ManagedCertificate with the domain
        sed -i.bak "s|# - \"your-domain.com\"  # Replace with your actual domain|- \"$DOMAIN_NAME\"|g" ../k8s/ingress/ingress.yaml
        sed -i.bak "/# IMPORTANT: Replace with your actual domain name/d" ../k8s/ingress/ingress.yaml
        sed -i.bak "/# If you don't have a domain, comment out this section/d" ../k8s/ingress/ingress.yaml
        sed -i.bak "/# and use the static IP directly for access/d" ../k8s/ingress/ingress.yaml
        
        # Add host rule to ingress for the domain
        sed -i.bak "s|  rules:|  rules:\n  - host: $DOMAIN_NAME\n    http:\n      paths:\n      - path: /api/*\n        pathType: ImplementationSpecific\n        backend:\n          service:\n            name: api\n            port:\n              number: 8000\n      - path: /*\n        pathType: ImplementationSpecific\n        backend:\n          service:\n            name: web\n            port:\n              number: 8501|" ../k8s/ingress/ingress.yaml
        USING_DOMAIN=true
        
        echo -e "${YELLOW}📝 Tip: Add 'custom_domain = \"$DOMAIN_NAME\"' to terraform.tfvars for future deployments${NC}"
    fi
else
    echo -e "${YELLOW}📋 Using static IP access (no custom domain)${NC}"
    # Remove the ManagedCertificate section since we don't have a domain
    echo -e "${BLUE}🔧 Configuring ingress for IP-based access...${NC}"
    USING_DOMAIN=false
    
    echo -e "${YELLOW}📝 Tip: Add 'custom_domain = \"your-domain.com\"' to terraform.tfvars for automatic domain setup${NC}"
fi

fi

kubectl apply -f ../k8s/ingress/

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

# Check SSL certificate provisioning
echo -e "${BLUE}🔒 Checking SSL certificate provisioning...${NC}"
kubectl get managedcertificate -n visa-app 2>/dev/null || echo -e "${YELLOW}⚠️  ManagedCertificate not found, SSL may not be configured${NC}"

# Get Ingress IP
echo -e "${BLUE}🔍 Getting Ingress information...${NC}"
INGRESS_IP=$(terraform output -raw ingress_ip 2>/dev/null || echo "")

# Display access instructions
echo -e "${GREEN}🌐 Access Instructions:${NC}"
if [ ! -z "$INGRESS_IP" ]; then
    echo -e "${GREEN}✅ Static IP Reserved: $INGRESS_IP${NC}"
    echo ""
    
    if [ "$USING_DOMAIN" = true ] && [ ! -z "$DOMAIN_NAME" ]; then
        echo -e "${BLUE}🌐 Custom Domain URLs:${NC}"
        echo "   Web Application: https://$DOMAIN_NAME"
        echo "   API Backend: https://$DOMAIN_NAME/api"
        echo "   API Health Check: https://$DOMAIN_NAME/api/health"
        echo ""
        echo -e "${YELLOW}⚠️  Important DNS Setup:${NC}"
        echo "   Point your domain A record to: $INGRESS_IP"
        echo "   DNS propagation may take 1-24 hours"
        echo ""
        echo -e "${YELLOW}⏳ SSL Certificate Status:${NC}"
        echo "   Provisioning time: 5-15 minutes after DNS propagation"
        echo "   Check status: kubectl get managedcertificate -n visa-app"
        echo "   Check details: kubectl describe managedcertificate agentvisa-ssl-cert -n visa-app"
        echo ""
        echo -e "${BLUE}🔧 Troubleshooting:${NC}"
        echo "   • Verify DNS: nslookup $DOMAIN_NAME"
        echo "   • Try IP directly: http://$INGRESS_IP (should redirect)"
        echo "   • Check ingress: kubectl get ingress -n visa-app"
    else
        echo -e "${BLUE}🌐 Static IP URLs:${NC}"
        echo "   Web Application: http://$INGRESS_IP"
        echo "   API Backend: http://$INGRESS_IP/api"
        echo "   API Health Check: http://$INGRESS_IP/api/health"
        echo ""
        echo -e "${YELLOW}💡 Note: Using HTTP (no SSL) since no domain was configured${NC}"
        echo "   For HTTPS, set up a custom domain and redeploy"
        echo ""
        echo -e "${BLUE}🔧 Troubleshooting:${NC}"
        echo "   • Check ingress: kubectl get ingress -n visa-app"
        echo "   • Check services: kubectl get svc -n visa-app"
    fi
else
    echo -e "${YELLOW}⚠️  Static IP not found. Using port-forward for access:${NC}"
    echo ""
    echo -e "${BLUE}🔧 Port Forward Commands:${NC}"
    echo "   kubectl port-forward service/web 8501:8501 -n visa-app &"
    echo "   kubectl port-forward service/api 8000:8000 -n visa-app &"
    echo "   Then access:"
    echo "   • Web: http://localhost:8501"
    echo "   • API: http://localhost:8000"
fi
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