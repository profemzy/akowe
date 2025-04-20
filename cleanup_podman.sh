#!/bin/bash
set -e

echo "Cleaning up Podman environment for Akowe..."

# Stop and remove the pod
echo "Stopping and removing akowe-pod..."
sudo podman pod stop akowe-pod 2>/dev/null || true
sudo podman pod rm akowe-pod 2>/dev/null || true

# Remove individual containers if they exist
for CONTAINER in "akowe-web" "akowe-postgres" "akowe-pgadmin"; do
    if sudo podman ps -a --format "{{.Names}}" | grep -q "^$CONTAINER$"; then
        echo "Removing $CONTAINER container..."
        sudo podman rm -f "$CONTAINER" 2>/dev/null || true
    else
        echo "No $CONTAINER container found."
    fi
done

# Remove the image
echo "Removing akowe:latest image..."
sudo podman rmi akowe:latest 2>/dev/null || true

echo "Cleanup completed."
echo ""
echo "Options:"
echo "1. To also remove data directories (this will DELETE ALL DATA):"
echo "   rm -rf ./postgres_data ./pgadmin_data ./instance ./data"
echo ""
echo "2. To restart the application:"
echo "   ./run_with_podman.sh"
echo "   or"
echo "   podman-compose -f podman-compose.yml up -d"
