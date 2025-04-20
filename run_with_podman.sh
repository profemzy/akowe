#!/bin/bash
set -e

echo "Setting SELinux context for volume directories..."
mkdir -p ./instance ./data ./postgres_data ./pgadmin_data
sudo chcon -Rt container_file_t ./instance ./data ./postgres_data ./pgadmin_data || true

echo "Creating Akowe pod..."
sudo podman pod create --name akowe-pod -p 5000:5000 -p 5050:80 -p 5432:5432

echo "Building application image..."
sudo podman build -t akowe:latest -f Dockerfile --target runtime .

echo "Starting PostgreSQL container..."
sudo podman run -d --pod akowe-pod \
  --name akowe-postgres \
  --env-file .env \
  --env POSTGRES_USER=${DB_USER:-akowe_user} \
  --env POSTGRES_PASSWORD=${DB_PASSWORD:-akowe_password} \
  --env POSTGRES_DB=${DB_NAME:-akowe} \
  --env PGDATA=/var/lib/postgresql/data/pgdata \
  --volume ./postgres_data:/var/lib/postgresql/data:z \
  postgres:15-alpine

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until sudo podman exec akowe-postgres pg_isready -U ${DB_USER:-akowe_user} -d ${DB_NAME:-akowe} -h localhost; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 2
done

echo "Starting Akowe application container..."
sudo podman run -d --pod akowe-pod \
  --name akowe-web \
  --env-file .env \
  --env DB_HOST=localhost \
  --env DB_PORT=5432 \
  --volume ./instance:/app/instance:z \
  --volume ./data:/app/data:z \
  akowe:latest

echo "Starting PGAdmin container..."
sudo podman run -d --pod akowe-pod \
  --name akowe-pgadmin \
  --env PGADMIN_DEFAULT_EMAIL=${PGADMIN_EMAIL:-admin@example.com} \
  --env PGADMIN_DEFAULT_PASSWORD=${PGADMIN_PASSWORD:-admin} \
  --env PGADMIN_CONFIG_SERVER_MODE=False \
  --volume ./pgadmin_data:/var/lib/pgadmin:z \
  dpage/pgadmin4

echo "Akowe application is now running!"
echo "Web application: http://localhost:5000"
echo "PGAdmin: http://localhost:5050"
echo ""
echo "To stop the application run: podman pod stop akowe-pod"
echo "To start the application again run: podman pod start akowe-pod"
echo "To remove the pod and containers run: podman pod rm -f akowe-pod"
