# AgentVisa Deployment Guide

Complete guide for deploying AgentVisa across all environments: Local, Kubernetes, and Production.

## 📋 Table of Contents

1. [Environment Setup](#-environment-setup)
2. [Local Development](#-local-development)
3. [Kubernetes Deployment](#️-kubernetes-deployment)
4. [Production Features](#-production-features)
5. [Monitoring & Scaling](#-monitoring--scaling)
6. [Cost Optimization](#-cost-optimization)

## 🔧 Environment Setup

### Environment Variables Flow
```
Local Development:
.env file → docker-compose.yml → Application

Kubernetes:
ConfigMap + Secrets → Pod environment → Application

Terraform:
terraform.tfvars → Terraform → Kubernetes resources → Application
```

### Create Local .env File
```bash
# .env (for local development)
# LLM Provider Configuration
LLM_PROVIDER=google
GOOGLE_API_KEY=your_google_api_key_here
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Database Configuration  
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=visa_app
POSTGRES_USER=admin
POSTGRES_PASSWORD=your_password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# Application Configuration
DEBUG=true
LOG_LEVEL=DEBUG
```

## 🏠 Local Development

Run with Docker Compose:
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## ☸️ Kubernetes Deployment

### Transfer .env to Kubernetes Secrets
```bash
# Method 1: Manual secret creation
kubectl create secret generic app-secrets \
  --from-literal=postgres-password="your_password" \
  --from-literal=redis-password="your_redis_password" \
  --from-literal=google-api-key="your_google_api_key" \
  --from-literal=openai-api-key="your_openai_key" \
  --from-literal=anthropic-api-key="your_anthropic_key" \
  -n visa-app

# Method 2: From .env file directly
source .env
kubectl create secret generic app-secrets \
  --from-literal=postgres-password="$POSTGRES_PASSWORD" \
  --from-literal=redis-password="$REDIS_PASSWORD" \
  --from-literal=google-api-key="$GOOGLE_API_KEY" \
  --from-literal=openai-api-key="$OPENAI_API_KEY" \
  --from-literal=anthropic-api-key="$ANTHROPIC_API_KEY" \
  -n visa-app
```

### Deploy to Kubernetes
```bash
# Deploy all components
kubectl apply -f k8s/

# Check status
kubectl get pods -n visa-app
kubectl get services -n visa-app
kubectl get ingress -n visa-app
```

## 🎯 Production Features

### High Availability Configuration
- **Minimum 2 replicas** for API and Web services
- **Multi-node cluster** (2-5 nodes with autoscaling)
- **Anti-affinity rules** to distribute pods across nodes
- **Enhanced health checks** with proper timeouts

### Auto-scaling Setup

#### API Service (FastAPI)
```yaml
HPA Configuration:
- Min Replicas: 1
- Max Replicas: 2
- CPU Threshold: 70%
- Memory Threshold: 80%
- Scale Up: +2 pods max, 60s stabilization
- Scale Down: -1 pod max, 300s stabilization

Resources:
- Request: 512Mi memory, 200m CPU
- Limit: 1Gi memory, 500m CPU
```

#### Web Service (Streamlit)
```yaml
HPA Configuration:
- Min Replicas: 1
- Max Replicas: 2
- CPU Threshold: 75%
- Memory Threshold: 85%
- Scale Up: +1 pod max, 120s stabilization
- Scale Down: -1 pod max, 300s stabilization

Resources:
- Request: 256Mi memory, 100m CPU
- Limit: 512Mi memory, 300m CPU
```

#### Node Autoscaling
```yaml
Cluster Configuration:
- Min Nodes: 2 (high availability)
- Max Nodes: 4 (cost control)
- Machine Type: e2-medium (4GB RAM)
- Preemptible: Yes (60-80% cost savings)
- Auto-repair: Enabled
- Auto-upgrade: Enabled
```

### Health Check Strategy
```yaml
API Service:
- Startup Probe: 10s initial, 10s interval, 12 failures (2min total)
- Readiness Probe: 15s initial, 10s interval, 5s timeout
- Liveness Probe: 45s initial, 15s interval, 10s timeout

Web Service:
- Startup Probe: 15s initial, 10s interval, 10 failures (100s startup)
- Readiness Probe: 20s initial, 10s interval, 5s timeout  
- Liveness Probe: 45s initial, 15s interval, 10s timeout
```

## 🚀 Production Deployment

### Full Terraform Deployment
```bash
cd terraform/

# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Deploy infrastructure
terraform apply

# Get kubeconfig
gcloud container clusters get-credentials agentvisa-cluster \
  --zone us-central1-a --project your-project-id

# Deploy applications
kubectl apply -f ../k8s/
```

### Quick Deploy Script
```bash
cd terraform/
./deploy.sh
```

## 📊 Monitoring & Scaling

### Monitor Auto-scaling
```bash
# Watch HPA scaling in real-time
kubectl get hpa -n visa-app -w

# Monitor node scaling
kubectl get nodes -w

# Check resource usage
kubectl top pods -n visa-app
kubectl top nodes
```

### View Scaling Events
```bash
# HPA scaling decisions
kubectl describe hpa api-hpa -n visa-app
kubectl describe hpa web-hpa -n visa-app

# Cluster autoscaler logs
kubectl logs deployment/cluster-autoscaler -n kube-system --tail=50

# Recent scaling events
kubectl get events -n visa-app --field-selector reason=SuccessfulCreate
kubectl get events -n visa-app --field-selector reason=Killing
```

### Performance Metrics
```bash
# Pod resource utilization
kubectl top pods -n visa-app

# HPA status and metrics
kubectl get hpa -n visa-app

# Node utilization
kubectl top nodes

# Application access
kubectl get ingress -n visa-app
```

### Manual Scaling Override
```bash
# Scale for expected high load
kubectl scale deployment api --replicas=4 -n visa-app
kubectl scale deployment web --replicas=3 -n visa-app

# Scale down for maintenance
kubectl scale deployment api --replicas=1 -n visa-app
kubectl scale deployment web --replicas=1 -n visa-app

# Adjust HPA thresholds
kubectl patch hpa api-hpa -n visa-app --patch='{"spec":{"metrics":[{"type":"Resource","resource":{"name":"cpu","target":{"type":"Utilization","averageUtilization":50}}}]}}'
```

## 💰 Cost Optimization

### Monthly Cost Breakdown (~$115.76)
```
GKE Management: $74.40 (fixed)
4x e2-medium (preemptible): $29.36
Storage (45GB): $7.00
Networking: $5.00
```

### Cost Optimization Features
1. **Preemptible Nodes**: 60-80% savings vs regular instances
2. **Auto-scaling**: Only pay for resources you use
3. **Right-sized Resources**: No over-provisioning
4. **Zonal Cluster**: Cheaper than regional
5. **Minimal Logging/Monitoring**: Reduced costs

### Cost Optimization Strategies

#### High Traffic Scenarios
1. **Increase max replicas**: Raise HPA max to 4-6 for API
2. **Lower CPU thresholds**: Scale at 60% instead of 70%
3. **Add more nodes**: Increase cluster max to 5-7 nodes
4. **Consider regional cluster**: For highest availability

#### Cost Reduction Scenarios
1. **Reduce min replicas**: Set API min to 1 during low usage
2. **Higher thresholds**: Scale at 80% CPU instead of 70%
3. **Scheduled scaling**: Use CronJobs to pre-scale for known peaks
4. **Mixed node pools**: Critical workloads on standard nodes

## 🛡️ Security Features

Current security implementations:
- ✅ Workload Identity enabled
- ✅ Shielded GKE nodes
- ✅ Private container registry
- ✅ Secrets management
- ✅ RBAC enabled

## 🎯 Performance Targets

- **API Response Time**: < 2s for standard queries
- **Web UI Load Time**: < 5s initial load
- **Pod Startup Time**: < 2 minutes for API, < 100s for Web
- **Auto-scaling Response**: < 60s for scale-up, < 5min for scale-down

## 🔄 Automated Setup Script

Create a unified deployment script:

```bash
#!/bin/bash
# setup-deployment.sh

echo "🚀 Setting up AgentVisa deployment..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create one first."
    exit 1
fi

# Source .env file
source .env

echo "☸️ Creating Kubernetes secrets..."
kubectl create secret generic app-secrets \
  --from-literal=postgres-password="$POSTGRES_PASSWORD" \
  --from-literal=redis-password="$REDIS_PASSWORD" \
  --from-literal=google-api-key="$GOOGLE_API_KEY" \
  --from-literal=openai-api-key="$OPENAI_API_KEY" \
  --from-literal=anthropic-api-key="$ANTHROPIC_API_KEY" \
  -n visa-app \
  --dry-run=client -o yaml | kubectl apply -f -

echo "🏗️ Deploying to Kubernetes..."
kubectl apply -f k8s/

echo "✅ Deployment complete!"
echo "📝 Next steps:"
echo "   Check status: kubectl get pods -n visa-app"
echo "   Get ingress IP: kubectl get ingress -n visa-app"
echo "   Monitor scaling: kubectl get hpa -n visa-app -w"
```

## 📋 Environment Comparison

| Environment | Config Method | Secrets Method | Auto-reload | Best For |
|-------------|---------------|----------------|-------------|-----------|
| **Local** | `.env` file | `.env` file | ✅ Yes | Development |
| **Kubernetes** | ConfigMap | Secrets | ❌ No* | Production |
| **Terraform** | Variables | TF Variables | ✅ Yes | Infrastructure |

*Kubernetes pods need restart for config changes

## 🎯 Best Practices

1. **Keep one source of truth**: Maintain your `.env` file for local development
2. **Use scripts**: Automate the transfer of variables to Kubernetes
3. **Separate sensitive data**: Use Secrets for API keys, ConfigMaps for non-sensitive config
4. **Version control**: Never commit `.env` or `terraform.tfvars` with real secrets
5. **Monitor costs**: Use GCP billing alerts and resource quotas
6. **Regular updates**: Keep Kubernetes versions and images updated
7. **Backup strategy**: Implement regular backups for persistent data

Your existing `.env` file is the single source of truth - use scripts to deploy values to different environments!