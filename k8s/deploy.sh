#!/bin/bash

# Kubernetes deployment script for AgentVisa
# Make sure minikube is running: minikube start --driver=docker

set -e

echo "🚀 Starting Kubernetes deployment for AgentVisa..."

# Check if minikube is running
if ! minikube status > /dev/null 2>&1; then
    echo "❌ Minikube is not running. Please start it first:"
    echo "   minikube start --driver=docker"
    exit 1
fi

# Use minikube's Docker daemon
echo "🔧 Configuring Docker to use minikube's daemon..."
eval $(minikube docker-env)

# Build Docker images
echo "🏗️  Building Docker images..."
echo "Building API image..."
docker build -f Dockerfile.api -t visa-app-api:latest .

echo "Building Web image..."
docker build -f Dockerfile.web -t visa-app-web:latest .

# Create namespace
echo "📦 Creating namespace..."
kubectl apply -f k8s/namespace.yaml

# Wait for namespace to be ready (with fallback)
echo "⏳ Waiting for namespace to be active..."
if ! kubectl wait --for=condition=Active namespace/visa-app --timeout=30s 2>/dev/null; then
    echo "⚠️  Namespace wait timed out, but continuing (this is usually fine)..."
    sleep 5
fi

# Verify namespace exists
if kubectl get namespace visa-app >/dev/null 2>&1; then
    echo "✅ Namespace visa-app is ready"
else
    echo "❌ Namespace creation failed"
    exit 1
fi

# Deploy secrets (you need to update these with your actual API keys)
echo "🔐 Deploying secrets..."
kubectl apply -f k8s/secrets/app-secrets.yaml

# Deploy config maps
echo "⚙️  Deploying config maps..."
kubectl apply -f k8s/configmaps/app-config.yaml

# Deploy persistent volume claims
echo "💾 Creating storage..."
kubectl apply -f k8s/volumes/postgres-pvc.yaml
kubectl apply -f k8s/volumes/redis-pvc.yaml

# Deploy database first
echo "🗄️  Deploying PostgreSQL..."
kubectl apply -f k8s/deployments/postgres.yaml
kubectl apply -f k8s/services/postgres-service.yaml

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n visa-app --timeout=300s

# Deploy Redis
echo "🔄 Deploying Redis..."
kubectl apply -f k8s/deployments/redis.yaml
kubectl apply -f k8s/services/redis-service.yaml

# Wait for Redis to be ready
echo "⏳ Waiting for Redis to be ready..."
kubectl wait --for=condition=ready pod -l app=redis -n visa-app --timeout=300s

# Deploy API
echo "⚡ Deploying API service..."
kubectl apply -f k8s/deployments/api.yaml
kubectl apply -f k8s/services/api-service.yaml

# Wait for API to be ready
echo "⏳ Waiting for API to be ready..."
if ! kubectl wait --for=condition=ready pod -l app=api -n visa-app --timeout=300s; then
    echo "⚠️  API pods taking longer than expected. Checking status..."
    kubectl get pods -l app=api -n visa-app
    kubectl describe pods -l app=api -n visa-app
    kubectl logs -l app=api -n visa-app --tail=50
    echo "Continuing with deployment..."
fi

# Deploy Web frontend
echo "💻 Deploying Web service..."
kubectl apply -f k8s/deployments/web.yaml
kubectl apply -f k8s/services/web-service.yaml

# Wait for Web to be ready
echo "⏳ Waiting for Web service to be ready..."
if ! kubectl wait --for=condition=ready pod -l app=web -n visa-app --timeout=300s; then
    echo "⚠️  Web pods taking longer than expected. Checking status..."
    kubectl get pods -l app=web -n visa-app
    kubectl describe pods -l app=web -n visa-app
    kubectl logs -l app=web -n visa-app --tail=50
    echo "Deployment may have issues, check logs above..."
fi

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "📊 Checking deployment status..."
kubectl get pods -n visa-app
echo ""
echo "🌐 Services:"
kubectl get services -n visa-app
echo ""
echo "🔗 To access your application:"
echo "   minikube service web -n visa-app"
echo "   Or get URL: minikube service web -n visa-app --url"
echo ""
echo "📝 To view logs:"
echo "   API logs:  kubectl logs -f deployment/api -n visa-app"
echo "   Web logs:  kubectl logs -f deployment/web -n visa-app"
echo "   DB logs:   kubectl logs -f statefulset/postgres -n visa-app"
echo ""
echo "🔍 To check status:"
echo "   kubectl get all -n visa-app"
echo ""
echo "🧹 To cleanup:"
echo "   ./k8s/cleanup.sh"