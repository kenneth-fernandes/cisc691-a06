# Cost-Optimized GKE Deployment for AgentVisa

Deploy AgentVisa to Google Kubernetes Engine (GKE) with maximum cost optimization using Terraform.

## 💰 Cost Optimization Features

- **Preemptible Nodes**: 60-80% cost savings ($14.67/month vs $73.35/month)
- **Zonal Cluster**: Cheaper than regional clusters
- **Right-sized Resources**: e2-medium instances with minimal resource requests
- **Artifact Registry**: More cost-effective than Container Registry
- **Pod-based Services**: No managed Cloud SQL/Redis costs
- **Standard Storage**: pd-standard disks instead of SSD

**Estimated Monthly Cost: ~$124**

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Install required tools
brew install terraform
brew install --cask google-cloud-sdk
brew install kubectl

# Authenticate with Google Cloud
gcloud auth login
gcloud auth application-default login
```

### 2. Configure Project

```bash
# Copy and edit configuration
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars and set your project_id
```

### 3. Deploy

```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment (will prompt for confirmation)
./deploy.sh
```

## 📋 Manual Deployment Steps

If you prefer manual control:

### 1. Initialize Terraform

```bash
cd terraform/
terraform init
```

### 2. Plan Deployment

```bash
terraform plan -var="project_id=YOUR_PROJECT_ID"
```

### 3. Apply Infrastructure

```bash
terraform apply -var="project_id=YOUR_PROJECT_ID"
```

### 4. Build and Push Images

```bash
# Get the registry URL from Terraform output
REGISTRY=$(terraform output -raw artifact_registry_repository)

# Build and push images
gcloud builds submit --tag $REGISTRY/visa-app-api:latest --file Dockerfile.api .
gcloud builds submit --tag $REGISTRY/visa-app-web:latest --file Dockerfile.web .
```

### 5. Update Kubernetes Manifests

```bash
# Update image references
sed -i "s|REGION-docker.pkg.dev/PROJECT_ID|$REGISTRY|g" ../k8s/deployments/*.yaml
```

### 6. Deploy Application

```bash
# Get cluster credentials
gcloud container clusters get-credentials agentVisa-cluster --zone us-central1-a --project YOUR_PROJECT_ID

# Deploy Kubernetes resources
kubectl apply -f ../k8s/
```

## 🌐 Accessing the Application

### Port Forwarding (Recommended)

```bash
# Web application (Streamlit)
kubectl port-forward service/web 8501:8501 -n visa-app
# Visit: http://localhost:8501

# API backend (FastAPI)
kubectl port-forward service/api 8000:8000 -n visa-app  
# Visit: http://localhost:8000/docs
```

### Load Balancer (Additional Cost)

Modify services to use `type: LoadBalancer` for external access (adds ~$5/month per service).

## 💰 Cost Monitoring

### Monitor Resource Usage

```bash
# Node resource usage
kubectl top nodes

# Pod resource usage  
kubectl top pods -n visa-app

# Cluster information
kubectl cluster-info
```

### Set Up Billing Alerts

```bash
# Create billing alert (replace with your billing account)
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT \
  --display-name="AgentVisa GKE Budget" \
  --budget-amount=150 \
  --threshold-rule=percent=80 \
  --threshold-rule=percent=100
```

## 🔧 Scaling for Cost Optimization

### Scale Down for Development

```bash
# Scale to minimum for cost savings
kubectl scale deployment api --replicas=1 -n visa-app
kubectl scale deployment web --replicas=1 -n visa-app

# Scale nodes to minimum
gcloud container clusters resize agentVisa-cluster --num-nodes=1 --zone=us-central1-a
```

### Scale Up for Production

```bash
# Increase replicas for high availability
kubectl scale deployment api --replicas=3 -n visa-app
kubectl scale deployment web --replicas=2 -n visa-app
```

## 🛡️ Security Best Practices

- Workload Identity enabled for secure Pod-to-GCP communication
- Shielded GKE nodes with secure boot and integrity monitoring
- Private cluster option available (uncomment in main.tf)
- Network policies configurable for additional isolation

## 🧹 Cleanup

### Destroy All Resources

```bash
# This will delete everything and stop all charges
terraform destroy -var="project_id=YOUR_PROJECT_ID"
```

### Partial Cleanup

```bash
# Delete just the application
kubectl delete namespace visa-app

# Scale cluster to zero nodes
gcloud container clusters resize agentVisa-cluster --num-nodes=0 --zone=us-central1-a
```

## 📊 Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │     FastAPI     │
│   (Web UI)      │◄──►│   (Backend)     │
│   Port: 8501    │    │   Port: 8000    │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌─────────────────┬─────────────────┐
         │                 │                 │
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   PostgreSQL    │ │     Redis       │ │   Persistent    │
│   (Database)    │ │    (Cache)      │ │    Storage      │
│   Port: 5432    │ │   Port: 6379    │ │  (20GB/node)    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

## 🔍 Troubleshooting

### Common Issues

1. **Image Pull Errors**: Ensure Artifact Registry is properly configured and images are built
2. **Pod Crashes**: Check resource limits and adjust if needed
3. **Database Connection Issues**: Verify PostgreSQL pod is running and credentials are correct

### Debug Commands

```bash
# Check pod status
kubectl get pods -n visa-app

# View pod logs
kubectl logs deployment/api -n visa-app
kubectl logs deployment/web -n visa-app

# Describe problematic pods
kubectl describe pod POD_NAME -n visa-app

# Check events
kubectl get events -n visa-app --sort-by='.lastTimestamp'
```

## 📈 Cost Optimization Tips

1. **Use Preemptible Nodes**: 60-80% savings, but pods may be interrupted
2. **Right-size Resources**: Monitor usage and adjust requests/limits
3. **Enable Cluster Autoscaler**: Automatically scale nodes based on demand
4. **Schedule Workloads**: Use node affinity to pack pods efficiently
5. **Monitor Costs**: Set up billing alerts and review usage regularly

## 🎯 Production Considerations

For production deployment, consider:

- **Regional Clusters**: Higher availability but more expensive
- **Standard Nodes**: More reliable than preemptible
- **Managed Services**: Cloud SQL and MemoryStore for production reliability
- **Ingress Controllers**: For better traffic management
- **Monitoring**: Full observability with Cloud Operations