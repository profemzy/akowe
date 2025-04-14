# Kubernetes Deployment for Akowe

This directory contains Kubernetes manifests to deploy the Akowe financial tracker application on a Kubernetes cluster using Azure Database for PostgreSQL.

## Configuration

### Prerequisites

- A Kubernetes cluster with the `wackops` namespace
- Azure Database for PostgreSQL instance
- A container registry where the Docker image will be pushed

### Files

1. **01-config.yaml**: Contains ConfigMap and Secret resources with environment variables
2. **02-deployment.yaml**: Deployment configuration for the web application and PVCs for data
3. **03-service.yaml**: Service definition to expose the application internally
4. **04-ingress.yaml**: Ingress definition to expose the application externally with TLS
5. **05-hpa.yaml**: Horizontal Pod Autoscaler for automatic scaling

## Azure Database Setup

Before deploying, you need to:

1. Create an Azure Database for PostgreSQL instance
2. Create a database named `akowe`
3. Update the database connection details in the ConfigMap and Secret

```bash
# Update the DB_HOST in the ConfigMap
kubectl edit configmap akowe-config -n wackops

# Update the DB_USER and DB_PASSWORD in the Secret
kubectl edit secret akowe-secrets -n wackops
```

## Deployment Steps

1. Build and push the Docker image to your container registry:

```bash
# From the project root
docker build -t your-registry.azurecr.io/akowe:latest .
docker push your-registry.azurecr.io/akowe:latest
```

2. Update the image reference in the deployment and migration job files:

```bash
# Replace ${REGISTRY_URL} with your actual registry URL
sed -i 's/${REGISTRY_URL}/your-registry.azurecr.io/g' k8s/02-deployment.yaml k8s/migrate-job.yaml
```

3. Apply the configuration and run database migrations first:

```bash
kubectl apply -f k8s/01-config.yaml
kubectl apply -f k8s/migrate-job.yaml
```

4. Wait for the migration job to complete:

```bash
kubectl wait --for=condition=complete --timeout=120s job/akowe-migrate-db -n wackops
```

5. Apply the remaining Kubernetes manifests:

```bash
kubectl apply -f k8s/02-deployment.yaml
kubectl apply -f k8s/03-service.yaml
kubectl apply -f k8s/04-ingress.yaml
kubectl apply -f k8s/05-hpa.yaml
```

4. Check the status of the deployment:

```bash
kubectl get pods -n wackops -l app=akowe
kubectl get service -n wackops
kubectl get ingress -n wackops
```

## Environment Variables

The following environment variables are required:

- **Database Configuration**:
  - `DB_HOST`: Hostname of the Azure Database for PostgreSQL
  - `DB_PORT`: Port for PostgreSQL (usually 5432)
  - `DB_NAME`: Database name (default: akowe)
  - `DB_USER`: Database username with @server-name suffix
  - `DB_PASSWORD`: Database password

- **Application Configuration**:
  - `SECRET_KEY`: Flask secret key for sessions
  - `ADMIN_USERNAME`: Initial admin username
  - `ADMIN_PASSWORD`: Initial admin password
  - `ADMIN_EMAIL`: Initial admin email
  - `ADMIN_FIRST_NAME`: Initial admin first name
  - `ADMIN_LAST_NAME`: Initial admin last name

- **Business Configuration**:
  - `COMPANY_NAME`: Your company name (shown on invoices)
  - `DEFAULT_HOURLY_RATE`: Default hourly rate for timesheet entries
  
- **Azure Storage Configuration** (for receipt uploads):
  - `AZURE_STORAGE_CONNECTION_STRING`: Azure Blob Storage connection string

## Accessing the Application

After deployment, the application will be available at:
`https://akowe.example.com` (replace with your actual domain)

## Troubleshooting

Check the logs:
```bash
kubectl logs -f deployment/akowe -n wackops
```

Check the deployment status:
```bash
kubectl describe deployment akowe -n wackops
```