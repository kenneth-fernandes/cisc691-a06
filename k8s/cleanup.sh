#!/bin/bash

# Kubernetes cleanup script for AgentVisa (CPU-only deployment)
# Continue on errors to ensure all resources are attempted for deletion

set +e  # Don't exit on errors - continue cleanup

echo "🧹 Starting cleanup of Kubernetes resources..."

# Note: Ollama resources removed from GKE deployment
echo "📝 Ollama not deployed in this GKE setup (cost optimization)"

# Delete autoscaling resources
echo "🔄 Deleting autoscaling resources..."
kubectl delete hpa --all -n visa-app --ignore-not-found=true 2>/dev/null || echo "  ⚠️  No HPAs found or already deleted"
# Note: VPA and cluster autoscaler are not deployed in this configuration

# Delete all remaining resources in the visa-app namespace
echo "🗑️  Deleting all application resources..."
kubectl delete all --all -n visa-app --ignore-not-found=true 2>/dev/null || echo "  ⚠️  Some resources may not exist"

# Delete persistent volume claims (any remaining)
echo "💾 Deleting remaining storage..."
kubectl delete pvc --all -n visa-app --ignore-not-found=true 2>/dev/null || echo "  ⚠️  No PVCs found"

# Delete config maps and secrets
echo "⚙️  Deleting configuration..."
kubectl delete configmap --all -n visa-app --ignore-not-found=true 2>/dev/null || echo "  ⚠️  No ConfigMaps found"
kubectl delete secret --all -n visa-app --ignore-not-found=true 2>/dev/null || echo "  ⚠️  No Secrets found"

# Delete ingress resources
echo "🌐 Deleting ingress resources..."
kubectl delete ingress --all -n visa-app --ignore-not-found=true 2>/dev/null || echo "  ⚠️  No Ingress resources found"
kubectl delete managedcertificate --all -n visa-app --ignore-not-found=true 2>/dev/null || echo "  ⚠️  No ManagedCertificates found"

# Delete namespace
echo "📦 Deleting namespace..."
kubectl delete namespace visa-app --ignore-not-found=true 2>/dev/null || echo "  ⚠️  Namespace may not exist"

echo ""
echo "✅ Cleanup completed! (Some warnings above are normal)"
echo ""
echo "🔍 Remaining resources (should be empty):"
kubectl get all -n visa-app 2>/dev/null || echo "  ✅ Namespace visa-app no longer exists."
echo ""
echo "📊 Cleaned up resources:"
echo "  • API and Web services"
echo "  • PostgreSQL and Redis databases"  
echo "  • All persistent storage"
echo "  • Load balancer and ingress"
echo "  • Autoscaling policies"
echo "  • Note: Ollama was not deployed in GKE"