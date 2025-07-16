#!/bin/bash

set -e

PROJECT_NAME="energy-well-reports"
ENVIRONMENT="dev"
REGION="us-east-1"
STACK_NAME="EnergyWellReports-${ENVIRONMENT}"

echo -e "🚀 Starting deployment of Energy Well Reports infrastructure...${NC}"

export CDK_DEFAULT_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
export CDK_DEFAULT_REGION=$REGION
export ENVIRONMENT=$ENVIRONMENT

echo -e "📋 Deployment Configuration:${NC}"
echo "  Account: $CDK_DEFAULT_ACCOUNT"
echo "  Region: $CDK_DEFAULT_REGION"
echo "  Environment: $ENVIRONMENT"
echo "  Stack Name: $STACK_NAME"

cd infra
cdk bootstrap aws://$CDK_DEFAULT_ACCOUNT/$CDK_DEFAULT_REGION

echo -e "🔨 Synthesizing CDK stack...${NC}"
cdk synth

echo -e "🚀 Deploying CDK stack...${NC}"
cdk deploy --require-approval never

echo -e "✅ Deployment completed successfully!${NC}"