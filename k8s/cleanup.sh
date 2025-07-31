#!/bin/bash

# Kubernetes cleanup script for Visa Bulletin AI Agent

set -e

echo "🧹 Starting cleanup of Kubernetes resources..."

# Delete all resources in the visa-app namespace
echo "🗑️  Deleting all application resources..."
kubectl delete all --all -n visa-app

# Delete persistent volume claims
echo "💾 Deleting storage..."
kubectl delete pvc --all -n visa-app

# Delete config maps and secrets
echo "⚙️  Deleting configuration..."
kubectl delete configmap --all -n visa-app
kubectl delete secret --all -n visa-app

# Delete namespace
echo "📦 Deleting namespace..."
kubectl delete namespace visa-app

echo ""
echo "✅ Cleanup completed successfully!"
echo ""
echo "🔍 Remaining resources (should be empty):"
kubectl get all -n visa-app 2>/dev/null || echo "Namespace visa-app no longer exists."