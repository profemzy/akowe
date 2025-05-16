# Deploying Akowe to Kubernetes

This guide explains how to deploy the Akowe Financial Tracker application to a Kubernetes cluster using the provided deployment script.

## Prerequisites

- Kubernetes cluster configured and accessible via `kubectl`
- Docker or Podman installed on your system
- Access to the Azure Container Registry (ACR)

## Deployment Script

The `deploy_to_k8s.sh` script automates the process of building, pushing, and deploying the Akowe application to a Kubernetes cluster. The script performs the following steps:

1. Builds the Docker image using the Dockerfile
2. Tags the image with an appropriate version
3. Pushes the image to the Azure Container Registry
4. Updates the Kubernetes deployment file with the new image
5. Applies the updated deployment to the Kubernetes cluster

## Usage

Make sure the script is executable:

```bash
chmod +x deploy_to_k8s.sh
```

### Basic Usage

To deploy with default settings (auto-incrementing the version number):

```bash
./deploy_to_k8s.sh
```

### Advanced Usage

The script supports several command-line options:

```bash
./deploy_to_k8s.sh [OPTIONS]
```

Options:
- `-v, --version VERSION` - Specify a specific version tag (default: auto-increment)
- `-r, --registry REGISTRY` - Specify a different container registry (default: wackopsprodacr.azurecr.io)
- `-n, --namespace NS` - Specify a different Kubernetes namespace (default: wackops)
- `-f, --file FILE` - Specify a different deployment file (default: k8s/02-deployment.yaml)
- `-h, --help` - Display help message

Examples:

```bash
# Deploy with a specific version
./deploy_to_k8s.sh -v v1.0.16

# Deploy to a different namespace
./deploy_to_k8s.sh -n production

# Deploy using a different deployment file
./deploy_to_k8s.sh -f k8s/production-deployment.yaml

# Deploy to a different registry
./deploy_to_k8s.sh -r myregistry.azurecr.io
```

## Monitoring the Deployment

After running the deployment script, you can monitor the status of the deployment using:

```bash
kubectl get pods -n wackops
kubectl describe deployment akowe -n wackops
```

## Troubleshooting

If you encounter issues during deployment:

1. Check that you have the correct credentials for the container registry:
   ```bash
   docker login wackopsprodacr.azurecr.io
   ```
   or
   ```bash
   podman login wackopsprodacr.azurecr.io
   ```

2. Verify that your kubectl context is set to the correct cluster:
   ```bash
   kubectl config current-context
   ```

3. Check the logs of the deployment:
   ```bash
   kubectl logs deployment/akowe -n wackops
   ```

4. Check the events in the namespace:
   ```bash
   kubectl get events -n wackops
   ```

## Rollback

If you need to rollback to a previous version:

```bash
# Get the deployment history
kubectl rollout history deployment/akowe -n wackops

# Rollback to the previous version
kubectl rollout undo deployment/akowe -n wackops

# Rollback to a specific revision
kubectl rollout undo deployment/akowe -n wackops --to-revision=2
```