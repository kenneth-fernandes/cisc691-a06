#!/bin/bash

# Secrets validation script for AgentVisa
# This script helps validate and troubleshoot secrets configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 AgentVisa Secrets Validation${NC}"
echo ""

SECRETS_FILE="k8s/secrets/app-secrets.yaml"
TEMPLATE_FILE="k8s/secrets/app-secrets.yaml.template"

# Check if secrets file exists
if [ ! -f "$SECRETS_FILE" ]; then
    echo -e "${RED}❌ Secrets file not found: $SECRETS_FILE${NC}"
    
    if [ -f "$TEMPLATE_FILE" ]; then
        echo -e "${YELLOW}📋 Template file found. Creating secrets file...${NC}"
        cp "$TEMPLATE_FILE" "$SECRETS_FILE"
        echo -e "${YELLOW}✅ Created $SECRETS_FILE from template${NC}"
        echo -e "${YELLOW}⚠️  You must now edit this file with your actual values${NC}"
    else
        echo -e "${RED}❌ Template file not found: $TEMPLATE_FILE${NC}"
        exit 1
    fi
fi

echo -e "${BLUE}🔍 Checking secrets file content...${NC}"

# Check for placeholder values
if grep -q "REPLACE_WITH_BASE64_ENCODED" "$SECRETS_FILE"; then
    echo -e "${RED}❌ Found placeholder values in secrets file${NC}"
    echo -e "${YELLOW}Please replace the following placeholders:${NC}"
    grep -n "REPLACE_WITH_BASE64_ENCODED" "$SECRETS_FILE" | while read line; do
        echo -e "${YELLOW}  Line: $line${NC}"
    done
    echo ""
    echo -e "${BLUE}💡 Generate base64 values with:${NC}"
    echo -e "  echo -n 'your_password' | base64"
    echo -e "  echo -n 'your_api_key' | base64"
    echo ""
    exit 1
fi

# Validate YAML syntax
echo -e "${BLUE}🔍 Validating YAML syntax...${NC}"
if ! kubectl apply --dry-run=client -f "$SECRETS_FILE" > /dev/null 2>&1; then
    echo -e "${RED}❌ Invalid YAML syntax in secrets file${NC}"
    echo -e "${YELLOW}Run the following command to see detailed errors:${NC}"
    echo -e "  kubectl apply --dry-run=client -f $SECRETS_FILE"
    exit 1
fi

# Check if base64 values are valid
echo -e "${BLUE}🔍 Validating base64 encoding...${NC}"
SECRET_KEYS=("postgres-password" "redis-password" "google-api-key" "openai-api-key" "anthropic-api-key")

for key in "${SECRET_KEYS[@]}"; do
    # Extract base64 value from YAML
    base64_value=$(yq eval ".data.\"$key\"" "$SECRETS_FILE" 2>/dev/null || echo "null")
    
    if [ "$base64_value" = "null" ] || [ -z "$base64_value" ]; then
        echo -e "${YELLOW}⚠️  Key '$key' not found or empty${NC}"
        continue
    fi
    
    # Test if it's valid base64
    if echo "$base64_value" | base64 -d > /dev/null 2>&1; then
        decoded_length=$(echo "$base64_value" | base64 -d | wc -c)
        if [ "$decoded_length" -gt 0 ]; then
            echo -e "${GREEN}✅ $key: valid base64 (${decoded_length} chars when decoded)${NC}"
        else
            echo -e "${YELLOW}⚠️  $key: valid base64 but empty when decoded${NC}"
        fi
    else
        echo -e "${RED}❌ $key: invalid base64 encoding${NC}"
        echo -e "${YELLOW}   Current value: $base64_value${NC}"
        echo -e "${YELLOW}   Re-encode with: echo -n 'your_value' | base64${NC}"
    fi
done

# Test kubectl apply
echo -e "${BLUE}🔍 Testing kubectl apply...${NC}"
if kubectl apply --dry-run=server -f "$SECRETS_FILE" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Secrets file is valid and ready to deploy${NC}"
else
    echo -e "${RED}❌ kubectl apply test failed${NC}"
    echo -e "${YELLOW}Run for details: kubectl apply --dry-run=server -f $SECRETS_FILE${NC}"
    exit 1
fi

# Check if already deployed
if kubectl get secret app-secrets -n visa-app > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Secrets already deployed to cluster${NC}"
    
    # Compare deployed vs file
    echo -e "${BLUE}🔍 Checking if deployed secrets match file...${NC}"
    if kubectl apply --dry-run=server -f "$SECRETS_FILE" | grep -q "unchanged"; then
        echo -e "${GREEN}✅ Deployed secrets match the file${NC}"
    else
        echo -e "${YELLOW}⚠️  Deployed secrets differ from file${NC}"
        echo -e "${YELLOW}   Run: kubectl apply -f $SECRETS_FILE to update${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Secrets not yet deployed to cluster${NC}"
    echo -e "${YELLOW}   Run: kubectl apply -f $SECRETS_FILE${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Secrets validation completed!${NC}"
echo ""
echo -e "${BLUE}📋 Useful commands:${NC}"
echo -e "  Apply secrets:    kubectl apply -f $SECRETS_FILE"
echo -e "  View secrets:     kubectl get secret app-secrets -n visa-app -o yaml"
echo -e "  Delete secrets:   kubectl delete secret app-secrets -n visa-app"
echo -e "  Test decode:      kubectl get secret app-secrets -n visa-app -o jsonpath='{.data.postgres-password}' | base64 -d"