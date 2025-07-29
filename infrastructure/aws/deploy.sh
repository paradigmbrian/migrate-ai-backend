#!/bin/bash

# AWS Deployment Script for MigrateAI Backend
# This script builds and deploys the application to AWS ECS

set -e

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}
ECR_REPOSITORY="migrate-backend"
ECR_IMAGE_TAG="latest"
CLUSTER_NAME="migrate-cluster"
SERVICE_NAME="migrate-backend-service"

echo "🚀 Starting AWS deployment for MigrateAI Backend..."

# Check AWS CLI and credentials
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo "❌ Error: AWS CLI not configured or credentials not set"
    exit 1
fi

echo "✅ AWS credentials verified"
echo "📊 Account ID: $AWS_ACCOUNT_ID"
echo "🌍 Region: $AWS_REGION"

# Create ECR repository if it doesn't exist
echo "🏗️  Setting up ECR repository..."
aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION > /dev/null 2>&1 || {
    echo "Creating ECR repository: $ECR_REPOSITORY"
    aws ecr create-repository --repository-name $ECR_REPOSITORY --region $AWS_REGION
}

# Get ECR login token
echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build production Docker image
echo "🔨 Building production Docker image..."
docker build -f Dockerfile.prod -t $ECR_REPOSITORY:$ECR_IMAGE_TAG .

# Tag image for ECR
ECR_IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPOSITORY:$ECR_IMAGE_TAG"
docker tag $ECR_REPOSITORY:$ECR_IMAGE_TAG $ECR_IMAGE_URI

# Push image to ECR
echo "📤 Pushing image to ECR..."
docker push $ECR_IMAGE_URI

echo "✅ Image pushed successfully: $ECR_IMAGE_URI"

# Update ECS service (if it exists)
echo "🔄 Updating ECS service..."
if aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION > /dev/null 2>&1; then
    echo "Forcing new deployment..."
    aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --force-new-deployment --region $AWS_REGION
    
    echo "⏳ Waiting for service to stabilize..."
    aws ecs wait services-stable --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION
    echo "✅ Service updated successfully"
else
    echo "⚠️  Service $SERVICE_NAME not found. You may need to create it first."
fi

echo ""
echo "🎉 Deployment completed!"
echo "📊 ECR Image: $ECR_IMAGE_URI"
echo "🔍 Check ECS console: https://console.aws.amazon.com/ecs/home?region=$AWS_REGION#/clusters/$CLUSTER_NAME/services" 