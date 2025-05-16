#!/usr/bin/env bash
# deploy_to_k8s.sh - Script to build, push, and deploy Akowe to Kubernetes
#
# This script automates the process of building the Akowe application,
# pushing it to Azure Container Registry, and deploying it to a Kubernetes cluster.

set -e  # Exit immediately if a command exits with a non-zero status

# Configuration
REGISTRY="wackopsprodacr.azurecr.io"
REGISTRY_NAME="wackopsprodacr"  # ACR name without domain
IMAGE_NAME="akowe"
NAMESPACE="wackops"
DEPLOYMENT_FILE="k8s/02-deployment.yaml"
SCRIPT_VERSION="1.1.0"  # Script version for tracking changes
SKIP_DEPLOYMENT_UPDATE=false  # Skip updating the deployment file

# Function to display usage information
usage() {
  echo "Usage: $0 [OPTIONS]"
  echo "Options:"
  echo "  -v, --version VERSION   Specify version tag (default: auto-increment)"
  echo "  -r, --registry REGISTRY Specify container registry (default: $REGISTRY)"
  echo "  -n, --namespace NS      Specify Kubernetes namespace (default: $NAMESPACE)"
  echo "  -f, --file FILE         Specify deployment file (default: $DEPLOYMENT_FILE)"
  echo "  -s, --skip-update       Skip updating the deployment file"
  echo "  -h, --help              Display this help message"
  exit 1
}

# Function to log messages
log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if already logged in to registry
check_registry_login() {
  local registry="$1"
  local cmd="$2"
  
  log "Checking if already logged in to $registry..."
  
  if [ "$cmd" = "docker" ]; then
    # For Docker, check if we can pull a small image from the registry
    if docker pull "$registry/hello-world:latest" &>/dev/null; then
      return 0  # Already logged in
    fi
  elif [ "$cmd" = "podman" ]; then
    # For Podman, check auth status
    if podman login --get-login "$registry" &>/dev/null; then
      return 0  # Already logged in
    fi
  fi
  
  return 1  # Not logged in
}

# Function to check kubectl connection to cluster
check_kubectl_connection() {
  log "Checking connection to Kubernetes cluster..."
  if ! kubectl get nodes &>/dev/null; then
    log "Error: Cannot connect to Kubernetes cluster. Please check your kubeconfig."
    exit 1
  fi
  
  # Check if namespace exists
  if ! kubectl get namespace "$NAMESPACE" &>/dev/null; then
    log "Warning: Namespace $NAMESPACE does not exist. Creating it..."
    kubectl create namespace "$NAMESPACE" || {
      log "Error: Failed to create namespace $NAMESPACE"
      exit 1
    }
  fi
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
    -s|--skip-update)
      SKIP_DEPLOYMENT_UPDATE=true
      shift
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

# Check kubectl connection to the cluster
check_kubectl_connection

# Display deployment summary
log "Deployment Summary:"
log "  - Container Engine: $CONTAINER_CMD"
log "  - Registry: $REGISTRY"
log "  - Image: $IMAGE_NAME:$VERSION"
log "  - Kubernetes Namespace: $NAMESPACE"
log "  - Deployment File: $DEPLOYMENT_FILE"
log "  - Skip Deployment Update: $SKIP_DEPLOYMENT_UPDATE"
log ""
log "Starting deployment process..."

# Check if already logged in to registry
if check_registry_login "$REGISTRY" "$CONTAINER_CMD"; then
  log "Already logged in to $REGISTRY, skipping login step."
else
  # Check if Azure CLI is installed
  if ! command -v az &> /dev/null; then
    log "Warning: Azure CLI is not installed. Will attempt direct login to registry."
    # Direct login to container registry
    log "Logging in to container registry $REGISTRY..."
    if [ "$CONTAINER_CMD" = "docker" ]; then
      docker login "$REGISTRY" || { log "Error: Failed to login to container registry"; exit 1; }
    else
      podman login "$REGISTRY" || { log "Error: Failed to login to container registry"; exit 1; }
    fi
  else
    # Check Azure CLI version
    AZ_VERSION=$(az version --query '"azure-cli"' -o tsv 2>/dev/null)
    log "Using Azure CLI version $AZ_VERSION"
    
    # Login using Azure CLI
    log "Logging in to Azure Container Registry $REGISTRY_NAME using Azure CLI..."
    
    # Get ACR credentials using Azure CLI
    if [ "$CONTAINER_CMD" = "docker" ]; then
      az acr login --name "$REGISTRY_NAME" || { 
        log "Error: Failed to login to ACR using Azure CLI. Attempting direct login..."; 
        docker login "$REGISTRY" || { log "Error: Direct login also failed"; exit 1; }
      }
    else
      # For Podman, we need to get the credentials and use them with podman login
      # Get access token for the registry
      log "Getting ACR credentials for Podman..."
      
      # Get username and password from Azure CLI
      ACR_USERNAME=$(az acr credential show --name "$REGISTRY_NAME" --query "username" -o tsv 2>/dev/null)
      ACR_PASSWORD=$(az acr credential show --name "$REGISTRY_NAME" --query "passwords[0].value" -o tsv 2>/dev/null)
      
      if [ -n "$ACR_USERNAME" ] && [ -n "$ACR_PASSWORD" ]; then
        # Use credentials with podman
        echo "$ACR_PASSWORD" | podman login "$REGISTRY" --username "$ACR_USERNAME" --password-stdin || {
          log "Error: Failed to login to ACR using credentials. Attempting direct login...";
          podman login "$REGISTRY" || { log "Error: Direct login also failed"; exit 1; }
        }
      else
        log "Warning: Could not get ACR credentials from Azure CLI. Attempting direct login..."
        podman login "$REGISTRY" || { log "Error: Failed to login to container registry"; exit 1; }
      fi
    fi
  fi
fi

# Build the image
log "Building image $IMAGE_NAME:latest..."
if [ "$CONTAINER_CMD" = "podman" ]; then
  # Use --format docker for better compatibility
  podman build --format docker -t "$IMAGE_NAME:latest" -f Dockerfile --target runtime . || { log "Error: Failed to build image"; exit 1; }
else
  docker build -t "$IMAGE_NAME:latest" -f Dockerfile --target runtime . || { log "Error: Failed to build image"; exit 1; }
fi

# Tag the image with version
log "Tagging image as $FULL_IMAGE_NAME..."
$CONTAINER_CMD tag "$IMAGE_NAME:latest" "$FULL_IMAGE_NAME" || { log "Error: Failed to tag image"; exit 1; }

# Push the image to registry
log "Pushing image to registry..."
if [ "$CONTAINER_CMD" = "podman" ]; then
  # For Podman, ensure TLS verification is properly set
  podman push --tls-verify=true "$FULL_IMAGE_NAME" || { log "Error: Failed to push image"; exit 1; }
else
  docker push "$FULL_IMAGE_NAME" || { log "Error: Failed to push image"; exit 1; }
fi

# Update the deployment file with the new image tag if not skipped
if [ "$SKIP_DEPLOYMENT_UPDATE" = "true" ]; then
  log "Skipping deployment file update as requested..."
else
  # Create a backup of the original deployment file
  BACKUP_FILE="${DEPLOYMENT_FILE}.$(date +%Y%m%d%H%M%S).bak"
  log "Creating backup of deployment file at $BACKUP_FILE..."
  cp "$DEPLOYMENT_FILE" "$BACKUP_FILE" || { log "Warning: Failed to create backup of deployment file"; }

  # Update the deployment file with the new image
  log "Updating deployment file with new image version..."
  sed -i.bak "s|image: $REGISTRY/$IMAGE_NAME:[^ ]*|image: $FULL_IMAGE_NAME|g" "$DEPLOYMENT_FILE" || { log "Error: Failed to update deployment file"; exit 1; }

  # Verify the image tag was updated correctly
  if grep -q "image: $FULL_IMAGE_NAME" "$DEPLOYMENT_FILE"; then
    log "Successfully updated image tag in deployment file to $FULL_IMAGE_NAME"
  else
    log "Error: Failed to update image tag in deployment file. Restoring from backup..."
    cp "$BACKUP_FILE" "$DEPLOYMENT_FILE" || { log "Error: Failed to restore deployment file from backup"; exit 1; }
    exit 1
  fi
fi

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

# Print completion message with instructions for verification
log "============================================================"
log "✅ DEPLOYMENT COMPLETE"
log "============================================================"
log "To verify the deployment:"
log "  kubectl get pods -n $NAMESPACE"
log "  kubectl get deployment $IMAGE_NAME -n $NAMESPACE"
log ""
log "To view application logs:"
log "  kubectl logs -f deployment/$IMAGE_NAME -n $NAMESPACE"
log ""
log "To rollback if needed:"
log "  kubectl rollout undo deployment/$IMAGE_NAME -n $NAMESPACE"
log "============================================================"
