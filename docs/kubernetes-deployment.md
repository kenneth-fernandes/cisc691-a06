# Kubernetes Deployment Guide

Complete guide for deploying AgentVisa on Kubernetes/Minikube with troubleshooting and platform-specific instructions.

## 📋 Prerequisites

### Required Software
- [Minikube](https://minikube.sigs.k8s.io/docs/start/) (v1.25+)
- [kubectl](https://kubernetes.io/docs/tasks/tools/) (v1.21+)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (latest)
- Git for cloning the repository

### System Requirements
- **Memory**: 4GB+ available RAM
- **CPU**: 2+ cores
- **Disk**: 10GB+ free space
- **OS**: macOS, Windows, or Linux

## 🚀 Complete Setup and Deployment

### Step 1: Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd cisc691-a06

# Verify prerequisites
minikube version
kubectl version --client
docker --version
```

### Step 2: Start Minikube

```bash
# Start Minikube with Docker driver (recommended)
minikube start --driver=docker

# Verify Minikube is running
minikube status

# Configure shell to use Minikube's Docker daemon
eval $(minikube docker-env)
```

### Step 3: Deploy Application

#### Option A: Automated Deployment (Recommended)
```bash
# Make deployment script executable
chmod +x k8s/deploy.sh

# Run automated deployment
./k8s/deploy.sh
```

#### Option B: Manual Deployment
```bash
# Build Docker images
docker build -f Dockerfile.api -t visa-app-api:latest .
docker build -f Dockerfile.web -t visa-app-web:latest .

# Deploy Kubernetes resources in order
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets/app-secrets.yaml
kubectl apply -f k8s/configmaps/app-config.yaml
kubectl apply -f k8s/volumes/postgres-pvc.yaml
kubectl apply -f k8s/volumes/redis-pvc.yaml

# Deploy database services
kubectl apply -f k8s/deployments/postgres.yaml
kubectl apply -f k8s/services/postgres-service.yaml
kubectl apply -f k8s/deployments/redis.yaml
kubectl apply -f k8s/services/redis-service.yaml

# Wait for database to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n visa-app --timeout=300s

# Deploy application services
kubectl apply -f k8s/deployments/api.yaml
kubectl apply -f k8s/services/api-service.yaml
kubectl apply -f k8s/deployments/web.yaml
kubectl apply -f k8s/services/web-service.yaml
```

### Step 4: Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n visa-app

# Check services
kubectl get services -n visa-app

# View deployment status
kubectl get all -n visa-app
```

## 🌐 Accessing the Application

### Quick Access (Works on All Platforms)
```bash
# Open web application (recommended method)
minikube service web -n visa-app
```

### Platform-Specific Access Methods

#### macOS/Windows (Docker Driver)
The Docker driver creates networking limitations, so direct IP access doesn't work.

**Method 1: Service Tunnel (Recommended)**
```bash
# Start service tunnel (keep terminal open)
minikube service web -n visa-app
# Access the tunnel URL shown (e.g., http://127.0.0.1:xxxxx)
# Browser should open automatically
```

**Method 2: Port Forwarding**
```bash
# Forward web service to localhost
kubectl port-forward service/web 8501:8501 -n visa-app
# Access: http://localhost:8501

# In another terminal, forward API
kubectl port-forward service/api 8000:8000 -n visa-app
# Access: http://localhost:8000
```

#### Linux/VM Drivers
Direct IP access works with VM-based drivers.

```bash
# Get Minikube IP and access directly
MINIKUBE_IP=$(minikube ip)
echo "Web Application: http://$MINIKUBE_IP:30080"
echo "API Backend: http://$MINIKUBE_IP:30081"
echo "API Documentation: http://$MINIKUBE_IP:30081/docs"
```

### Service URLs Overview

| Service | Access Method | URL Pattern | Purpose |
|---------|---------------|-------------|---------|
| **Web UI** | `minikube service web -n visa-app` | `http://127.0.0.1:xxxxx` | Main Streamlit interface |
| **API** | `minikube service api -n visa-app` | `http://127.0.0.1:xxxxx` | REST API endpoints |
| **API Docs** | API URL + `/docs` | `http://127.0.0.1:xxxxx/docs` | Interactive API documentation |
| **Health Check** | API URL + `/health` | `http://127.0.0.1:xxxxx/health` | Service health status |

## 🔧 Execution and Data Collection

### Historical Visa Data Collection

```bash
# Execute data collection inside API pod
kubectl exec -it deployment/api -n visa-app -- python -c "
import sys
sys.path.append('/app/src')
from visa.collection.historical import HistoricalDataCollector

print('🚀 Starting historical data collection...')
collector = HistoricalDataCollector()
results = collector.collect_historical_data(
    start_year=2020,
    end_year=2025,
    max_workers=5,
    verify_urls=True
)

print(f'✅ Collection Status: {results[\"status\"]}')
print(f'📊 Bulletins Collected: {results.get(\"bulletins_collected\", 0)}')
print(f'💾 Bulletins Stored: {results.get(\"bulletins_stored\", 0)}')
"
```

### Check Data Collection Status

```bash
# Check database statistics
kubectl exec -it deployment/api -n visa-app -- python -c "
import sys
sys.path.append('/app/src')
from visa.repository import VisaBulletinRepository

repo = VisaBulletinRepository()
stats = repo.get_statistics()
print(f'📊 Total bulletins: {stats.get(\"bulletin_count\", 0)}')

# Get breakdown by year
for year in range(2020, 2026):
    bulletins = repo.get_bulletins_by_year_range(year, year)
    print(f'{year}: {len(bulletins)} bulletins')
"
```

## 📊 Monitoring and Management

### Pod Management
```bash
# Check pod status
kubectl get pods -n visa-app

# View detailed pod information
kubectl describe pod <pod-name> -n visa-app

# Execute commands in pods
kubectl exec -it <pod-name> -n visa-app -- /bin/bash
```

### Log Monitoring
```bash
# Follow web application logs
kubectl logs -f deployment/web -n visa-app

# Follow API logs
kubectl logs -f deployment/api -n visa-app

# Follow database logs
kubectl logs -f statefulset/postgres -n visa-app

# Follow Redis logs
kubectl logs -f deployment/redis -n visa-app
```

### Service Management
```bash
# Restart deployments
kubectl rollout restart deployment/web -n visa-app
kubectl rollout restart deployment/api -n visa-app

# Scale deployments
kubectl scale deployment api -n visa-app --replicas=3
kubectl scale deployment web -n visa-app --replicas=2

# Check rollout status
kubectl rollout status deployment/api -n visa-app
```

## 🧹 Cleanup and Maintenance

### Complete Cleanup
```bash
# Option 1: Use cleanup script
./k8s/cleanup.sh

# Option 2: Delete namespace (removes everything)
kubectl delete namespace visa-app
```

### Partial Cleanup
```bash
# Remove specific deployments
kubectl delete deployment api web -n visa-app

# Remove services
kubectl delete service api web -n visa-app

# Remove persistent volumes (caution: deletes data)
kubectl delete pvc postgres-pvc redis-pvc -n visa-app
```

### Minikube Cleanup
```bash
# Stop Minikube
minikube stop

# Delete Minikube cluster (complete reset)
minikube delete

# Restart fresh
minikube start --driver=docker
```

## 🛠️ Troubleshooting

### Cannot Access Application

**Problem**: Direct IP URLs (http://192.168.49.2:30080) don't work
**Solution**: Use service tunnel method
```bash
minikube service web -n visa-app
```

**Problem**: Tunnel ports keep changing
**Solution**: Use port forwarding for consistent localhost access
```bash
kubectl port-forward service/web 8501:8501 -n visa-app
```

### Deployment Issues

**Problem**: Pods stuck in Pending/ImagePullBackOff
**Solution**: Check Docker environment and rebuild images
```bash
# Ensure using Minikube's Docker daemon
eval $(minikube docker-env)

# Rebuild images
docker build -f Dockerfile.api -t visa-app-api:latest .
docker build -f Dockerfile.web -t visa-app-web:latest .
```

**Problem**: Database connection failures
**Solution**: Check PostgreSQL pod and configuration
```bash
# Check PostgreSQL pod
kubectl get pods -l app=postgres -n visa-app

# Check PostgreSQL logs
kubectl logs -f statefulset/postgres -n visa-app

# Check database configuration
kubectl describe configmap app-config -n visa-app
```

### Performance Issues

**Problem**: Slow application response
**Solution**: Scale deployments and check resources
```bash
# Scale API for better performance
kubectl scale deployment api -n visa-app --replicas=3

# Check resource usage
kubectl top pods -n visa-app

# Check node resources
kubectl describe node minikube
```

### Data Issues

**Problem**: No visa bulletin data available
**Solution**: Run data collection process
```bash
# Check current data
kubectl exec -it deployment/api -n visa-app -- python -c "
import sys; sys.path.append('/app/src')
from visa.repository import VisaBulletinRepository
repo = VisaBulletinRepository()
print(f'Bulletins: {repo.get_statistics().get(\"bulletin_count\", 0)}')
"

# Run data collection if needed (see Execution section above)
```

## 📁 Kubernetes Resource Structure

```
k8s/
├── namespace.yaml              # Creates visa-app namespace
├── deployments/               # Application workloads
│   ├── postgres.yaml          # PostgreSQL StatefulSet
│   ├── redis.yaml             # Redis deployment
│   ├── api.yaml               # FastAPI backend deployment
│   └── web.yaml               # Streamlit frontend deployment
├── services/                  # Network services
│   ├── postgres-service.yaml  # Database service (ClusterIP)
│   ├── redis-service.yaml     # Cache service (ClusterIP)
│   ├── api-service.yaml       # API service (NodePort:30081)
│   └── web-service.yaml       # Web service (NodePort:30080)
├── configmaps/               # Configuration data
│   └── app-config.yaml       # Application settings
├── secrets/                  # Sensitive data
│   └── app-secrets.yaml      # API keys and passwords (base64 encoded)
├── volumes/                  # Persistent storage
│   ├── postgres-pvc.yaml     # Database storage claim
│   └── redis-pvc.yaml        # Cache storage claim
├── deploy.sh                 # Automated deployment script
├── cleanup.sh               # Cleanup script
└── update-secrets.sh        # API key update utility
```

## 🔐 Security Considerations

### API Keys Management
```bash
# Update API keys in secrets
kubectl edit secret app-secrets -n visa-app

# Or use the update script
./k8s/update-secrets.sh
```

### Network Security
- Database and Redis are ClusterIP (internal only)
- Only API and Web services are exposed via NodePort
- Consider implementing NetworkPolicies for production

### Resource Limits
All deployments include resource requests and limits:
- **API**: 512Mi-1Gi memory, 250m-500m CPU
- **Web**: 256Mi-512Mi memory, 150m-300m CPU
- **PostgreSQL**: 256Mi-512Mi memory, 250m-500m CPU
- **Redis**: 128Mi-256Mi memory, 100m-200m CPU

## ⚡ Performance Optimization

### Scaling Recommendations
```bash
# For high load, scale API pods
kubectl scale deployment api -n visa-app --replicas=3

# Monitor resource usage
kubectl top pods -n visa-app
kubectl top nodes
```

### Resource Monitoring
```bash
# Check cluster resources
kubectl describe node minikube

# Monitor pod resources over time
watch kubectl top pods -n visa-app
```

---

This guide provides complete setup, deployment, execution, and maintenance instructions for running AgentVisa on Kubernetes. For additional architecture details, see the other documentation files in the `docs/` folder.