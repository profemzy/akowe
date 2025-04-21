#!/bin/bash
# deploy_to_k8s.sh - Script to build, push and deploy Akowe to Kubernetes
# 
# This script automates the process of building the Akowe application,
# pushing it to Azure Container Registry, and deploying it to a Kubernetes cluster.

set -e  # Exit immediately if a command exits with a non-zero status

# Configuration
REGISTRY="wackopsprodacr.azurecr.io"
IMAGE_NAME="akowe"
NAMESPACE="wackops"
DEPLOYMENT_FILE="k8s/02-deployment.yaml"

# Function to display usage information
usage() {
  echo "Usage: $0 [OPTIONS]"
  echo "Options:"
  echo "  -v, --version VERSION   Specify version tag (default: auto-increment)"
  echo "  -r, --registry REGISTRY Specify container registry (default: $REGISTRY)"
  echo "  -n, --namespace NS      Specify Kubernetes namespace (default: $NAMESPACE)"
  echo "  -f, --file FILE         Specify deployment file (default: $DEPLOYMENT_FILE)"
  echo "  -h, --help              Display this help message"
  exit 1
}

# Function to log messages
log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -v|--version)
      VERSION="$2"
      shift 2
      ;;
    -r|--registry)
      REGISTRY="$2"
      shift 2
      ;;
    -n|--namespace)
      NAMESPACE="$2"
      shift 2
      ;;
    -f|--file)
      DEPLOYMENT_FILE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown option: $1"
      usage
      ;;
  esac
done

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
  log "Error: kubectl is not installed. Please install kubectl first."
  exit 1
fi

# Check if docker/podman is installed
if command -v docker &> /dev/null; then
  CONTAINER_CMD="docker"
elif command -v podman &> /dev/null; then
  CONTAINER_CMD="podman"
else
  log "Error: Neither docker nor podman is installed. Please install one of them first."
  exit 1
fi

log "Using $CONTAINER_CMD for container operations"

# Check if deployment file exists
if [ ! -f "$DEPLOYMENT_FILE" ]; then
  log "Error: Deployment file $DEPLOYMENT_FILE not found."
  exit 1
fi

# Auto-increment version if not specified
if [ -z "$VERSION" ]; then
  # Extract current version from deployment file
  CURRENT_VERSION=$(grep -oP "image: $REGISTRY/$IMAGE_NAME:\K[^\s]+" "$DEPLOYMENT_FILE" | head -1)
  
  if [ -z "$CURRENT_VERSION" ]; then
    log "Error: Could not determine current version from deployment file."
    exit 1
  fi
  
  # Parse version components (assuming format vX.Y.Z)
  if [[ $CURRENT_VERSION =~ v([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
    MAJOR="${BASH_REMATCH[1]}"
    MINOR="${BASH_REMATCH[2]}"
    PATCH="${BASH_REMATCH[3]}"
    
    # Increment patch version
    PATCH=$((PATCH + 1))
    VERSION="v$MAJOR.$MINOR.$PATCH"
    
    log "Auto-incremented version from $CURRENT_VERSION to $VERSION"
  else
    log "Error: Current version format not recognized: $CURRENT_VERSION"
    exit 1
  fi
fi

# Full image name with tag
FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME:$VERSION"

# Login to container registry
log "Logging in to container registry $REGISTRY..."
if [ "$CONTAINER_CMD" = "docker" ]; then
  docker login "$REGISTRY" || { log "Error: Failed to login to container registry"; exit 1; }
else
  podman login "$REGISTRY" || { log "Error: Failed to login to container registry"; exit 1; }
fi

# Build the image
log "Building image $IMAGE_NAME:latest..."
$CONTAINER_CMD build -t "$IMAGE_NAME:latest" -f Dockerfile --target runtime . || { log "Error: Failed to build image"; exit 1; }

# Tag the image with version
log "Tagging image as $FULL_IMAGE_NAME..."
$CONTAINER_CMD tag "$IMAGE_NAME:latest" "$FULL_IMAGE_NAME" || { log "Error: Failed to tag image"; exit 1; }

# Push the image to registry
log "Pushing image to registry..."
$CONTAINER_CMD push "$FULL_IMAGE_NAME" || { log "Error: Failed to push image"; exit 1; }

# Update the deployment file with the new image
log "Updating deployment file with new image version..."
sed -i.bak "s|image: $REGISTRY/$IMAGE_NAME:[^ ]*|image: $FULL_IMAGE_NAME|g" "$DEPLOYMENT_FILE" || { log "Error: Failed to update deployment file"; exit 1; }

# Apply the deployment
log "Applying deployment to Kubernetes cluster..."
kubectl apply -f "$DEPLOYMENT_FILE" -n "$NAMESPACE" || { log "Error: Failed to apply deployment"; exit 1; }

# Check deployment status
log "Checking deployment status..."
kubectl rollout status deployment/"$IMAGE_NAME" -n "$NAMESPACE" || { log "Warning: Deployment may not be complete"; }

log "Deployment completed successfully!"
log "Image: $FULL_IMAGE_NAME"
log "Namespace: $NAMESPACE"

# Cleanup
rm -f "$DEPLOYMENT_FILE.bak"

log "Done!"