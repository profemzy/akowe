#!/bin/bash
set -e

echo "Setting up SELinux context for Akowe volume directories..."

# Create directories if they don't exist
mkdir -p ./instance
mkdir -p ./data
mkdir -p ./postgres_data
mkdir -p ./pgadmin_data

# Set SELinux context for volume directories
echo "Setting SELinux context for volume directories..."
sudo chcon -Rt container_file_t ./instance
sudo chcon -Rt container_file_t ./data
sudo chcon -Rt container_file_t ./postgres_data
sudo chcon -Rt container_file_t ./pgadmin_data

echo "SELinux context set successfully!"
echo ""
echo "You can now run the application with:"
echo "  sudo ./run_with_podman.sh"
echo ""
echo "Or if you have podman-compose installed:"
echo "  sudo podman-compose -f podman-compose.yml up -d"
