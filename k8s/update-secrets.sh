#!/bin/bash

# Script to update Kubernetes secrets with your API keys

echo "🔐 Updating Kubernetes secrets with API keys..."
echo ""
echo "This script will help you encode and update your API keys in Kubernetes."
echo "Leave empty if you don't have a particular API key."
echo ""

# Function to base64 encode
encode_secret() {
    if [ -n "$1" ]; then
        echo -n "$1" | base64
    else
        echo ""
    fi
}

# Get API keys from user
read -p "Enter your Google API Key (or press Enter to skip): " GOOGLE_KEY
read -p "Enter your OpenAI API Key (or press Enter to skip): " OPENAI_KEY
read -p "Enter your Anthropic API Key (or press Enter to skip): " ANTHROPIC_KEY

# Encode the keys
GOOGLE_ENCODED=$(encode_secret "$GOOGLE_KEY")
OPENAI_ENCODED=$(encode_secret "$OPENAI_KEY")
ANTHROPIC_ENCODED=$(encode_secret "$ANTHROPIC_KEY")

# Create updated secrets file
cat > k8s/secrets/app-secrets.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: visa-app
type: Opaque
data:
  # Base64 encoded values
  postgres-password: cGFzc3dvcmQ=  # password
  redis-password: cmVkaXNfcGFzc3dvcmQ=  # redis_password
  google-api-key: "$GOOGLE_ENCODED"
  openai-api-key: "$OPENAI_ENCODED"
  anthropic-api-key: "$ANTHROPIC_ENCODED"
EOF

echo ""
echo "✅ Secrets file updated at k8s/secrets/app-secrets.yaml"
echo ""
echo "To apply the updated secrets to your cluster, run:"
echo "   kubectl apply -f k8s/secrets/app-secrets.yaml"