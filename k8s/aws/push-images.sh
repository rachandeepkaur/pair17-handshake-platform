#!/usr/bin/env bash
# Build the 9 p17 images, create their ECR repositories if needed, and push them.
#
#   AWS_REGION=us-east-1 VERSION=1.0.0 k8s/aws/push-images.sh
#
# Authenticates with a short-lived token (aws ecr get-login-password); no keys are stored.
set -euo pipefail
cd "$(dirname "$0")/../.."

AWS_REGION=${AWS_REGION:-$(aws configure get region 2>/dev/null || true)}
: "${AWS_REGION:?set AWS_REGION, e.g. export AWS_REGION=us-east-1}"
export AWS_REGION
VERSION=${VERSION:-1.0.0}
ACCOUNT_ID=${ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}
ECR="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
IMAGES=(p17-student-service p17-company-service p17-job-service p17-application-service p17-event-service
        p17-assistant-service p17-frontend p17-kafka-worker p17-db-seed)

for img in "${IMAGES[@]}"; do
  aws ecr describe-repositories --region "$AWS_REGION" --repository-names "$img" >/dev/null 2>&1 \
    || aws ecr create-repository --region "$AWS_REGION" --repository-name "$img" \
         --image-scanning-configuration scanOnPush=true >/dev/null
done

# EKS nodes are x86_64; build for that even on an Apple Silicon Mac.
export DOCKER_DEFAULT_PLATFORM=linux/amd64
docker compose build
docker compose --profile seed build p17-db-seed

aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR"
for img in "${IMAGES[@]}"; do
  docker tag "${img}:latest" "${ECR}/${img}:${VERSION}"
  docker push "${ECR}/${img}:${VERSION}"
done

echo
aws ecr describe-images --region "$AWS_REGION" --repository-name p17-job-service --query 'imageDetails[].imageTags' --output text
echo "Pushed ${#IMAGES[@]} images to ${ECR} with tag ${VERSION}"
