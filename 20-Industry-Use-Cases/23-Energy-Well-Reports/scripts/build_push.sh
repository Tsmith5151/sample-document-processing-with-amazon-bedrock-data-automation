#!/bin/bash -e

SERVICE_DIR=$1
IMAGE_NAME=$2
IMAGE_VERSION=$3
AWS_DEFAULT_REGION=${4:-us-east-1}
DOCKER_PATH="services/$SERVICE_DIR/$IMAGE_NAME/docker/Dockerfile"

# Login to ECR
docker_login(){
    echo "========================================================================="
    echo "Getting AWS Credentials..."
    export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)

    echo "========================================================================="
    echo "Login: $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com ..."
    aws ecr get-login-password --region "${AWS_DEFAULT_REGION}" | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com"
}
docker_login


# == Construct Image Name ==
IMAGE_NAME=${IMAGE_NAME//[_]/-}
echo $IMAGE_NAME

# == Docker Build Args ==
BUILD_ARGS=("LAMBDA_DIR=$IMAGE_NAME", "AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID")
BUILD_ARGS=( "${BUILD_ARGS[@]/#/--build-arg }" ) 
echo  "${BUILD_ARGS[@]}"

echo "========================================================================="
ECR_IMAGE=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_NAME:$IMAGE_VERSION
echo "Image Name: $ECR_IMAGE"
echo "Docker Build Path: $DOCKER_PATH"

echo "========================================================================="
echo "🔨 Build Image..."
docker build -f ${DOCKER_PATH} --platform linux/amd64 ${BUILD_ARGS[@]} --tag $ECR_IMAGE .

# Check if ECR repo exists, if not create it
echo "========================================================================="
aws ecr describe-repositories --repository-names $IMAGE_NAME || aws ecr create-repository--repository-name $IMAGE_NAME --image-scanning-configuration scanOnPush=true --region $AWS_DEFAULT_REGION

echo "========================================================================="
echo "🚀 Push Image..."
docker push $ECR_IMAGE

# Update Lambda Function
#aws lambda update-function-code --function-name $IMAGE_NAME --image-uri ${ECR_IMAGE}