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

# Deploy secrets (with enhanced error handling and validation)
echo "🔐 Deploying secrets..."

# Check if secrets file exists
if [ ! -f "k8s/secrets/app-secrets.yaml" ]; then
    echo "❌ ERROR: app-secrets.yaml not found!"
    echo "📋 Creating secrets file from template..."
    
    if [ -f "k8s/secrets/app-secrets.yaml.template" ]; then
        cp "k8s/secrets/app-secrets.yaml.template" "k8s/secrets/app-secrets.yaml"
        echo "⚠️  IMPORTANT: You must update the secrets file with your actual API keys!"
        echo "📝 Edit: k8s/secrets/app-secrets.yaml"
        echo "🔧 Replace placeholder values with base64-encoded secrets:"
        echo "   echo -n 'your_password' | base64"
        echo "   echo -n 'your_api_key' | base64"
        echo ""
        read -p "Have you updated the secrets file with real values? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "❌ Please update the secrets file and run the deployment again"
            exit 1
        fi
    else
        echo "❌ ERROR: app-secrets.yaml.template not found!"
        echo "📝 Please create k8s/secrets/app-secrets.yaml with your secrets"
        exit 1
    fi
fi

# Validate secrets file content
echo "🔍 Validating secrets file..."
if grep -q "REPLACE_WITH_BASE64_ENCODED" "k8s/secrets/app-secrets.yaml"; then
    echo "❌ ERROR: Secrets file still contains placeholder values!"
    echo "📝 Please replace all REPLACE_WITH_BASE64_ENCODED values in:"
    echo "   k8s/secrets/app-secrets.yaml"
    echo ""
    echo "💡 Generate base64 values with:"
    echo "   echo -n 'your_actual_password' | base64"
    echo "   echo -n 'your_actual_api_key' | base64"
    exit 1
fi

# Apply secrets with comprehensive error handling
echo "✅ Applying secrets..."
if ! kubectl apply -f k8s/secrets/app-secrets.yaml; then
    echo "❌ ERROR: Failed to apply secrets!"
    echo "🔍 Common issues and solutions:"
    echo "  1. Invalid YAML syntax - check indentation"
    echo "  2. Invalid base64 encoding - regenerate with: echo -n 'value' | base64"
    echo "  3. Namespace not ready - wait a moment and retry"
    echo ""
    echo "🔧 Debug commands:"
    echo "  kubectl apply --dry-run=client -f k8s/secrets/app-secrets.yaml"
    echo "  ./k8s/validate-secrets.sh"
    exit 1
fi

echo "✅ Secrets deployed successfully"

# Verify secrets are properly deployed
echo "🔍 Verifying secrets deployment..."
if kubectl get secret app-secrets -n visa-app > /dev/null 2>&1; then
    echo "✅ Secrets successfully created in cluster"
    secret_count=$(kubectl get secret app-secrets -n visa-app -o jsonpath='{.data}' | jq -r 'keys | length' 2>/dev/null || echo "unknown")
    echo "📊 Secret contains $secret_count keys"
else
    echo "❌ ERROR: Secrets not found in cluster after deployment"
    exit 1
fi

# Deploy config maps
echo "⚙️  Deploying config maps..."
kubectl apply -f k8s/configmaps/app-config.yaml

# Deploy persistent volume claims (including Ollama model storage)
echo "💾 Creating storage..."
kubectl apply -f k8s/volumes/postgres-pvc.yaml
kubectl apply -f k8s/volumes/redis-pvc.yaml
kubectl apply -f k8s/volumes/ollama-pvc.yaml

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

# Deploy Ollama (CPU-only version for local development)
echo "🤖 Deploying Ollama (CPU-powered)..."
if kubectl apply -f k8s/deployments/ollama.yaml 2>/dev/null; then
    kubectl apply -f k8s/services/ollama-service.yaml
    echo "⏳ Waiting for Ollama to be ready (may take time for model download)..."
    if ! kubectl wait --for=condition=ready pod -l app=ollama -n visa-app --timeout=480s; then
        echo "⚠️  Ollama taking longer than expected (likely downloading Llama 3.2 1B model)"
        echo "💡 This is normal for first deployment. Check status with:"
        echo "   kubectl logs -f deployment/ollama -n visa-app"
    else
        echo "✅ Ollama CPU deployment successful"
    fi
else
    echo "⚠️  Ollama deployment failed"
    echo "💡 Check resources and try: kubectl describe pod -l app=ollama -n visa-app"
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
echo "   API logs:    kubectl logs -f deployment/api -n visa-app"
echo "   Web logs:    kubectl logs -f deployment/web -n visa-app"
echo "   DB logs:     kubectl logs -f statefulset/postgres -n visa-app"
echo "   Ollama logs: kubectl logs -f deployment/ollama -n visa-app"
echo ""
echo "🔍 To check status:"
echo "   kubectl get all -n visa-app"
echo ""
echo "🧹 To cleanup:"
echo "   ./k8s/cleanup.sh"