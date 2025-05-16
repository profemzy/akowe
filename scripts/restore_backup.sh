#!/bin/bash
set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 ./backups/akowe_backup_20250419_123456.tar.gz"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file '$BACKUP_FILE' not found."
    exit 1
fi

echo "Restoring Akowe data from backup: $BACKUP_FILE"
echo "WARNING: This will overwrite your current data!"
echo ""
read -p "Are you sure you want to continue? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

# Check if the application is running
if sudo podman pod ps | grep -q "akowe-pod"; then
    echo "Application is running. Stopping pod to ensure data consistency..."
    sudo podman pod stop akowe-pod
    RESTART_AFTER=true
else
    RESTART_AFTER=false
fi

# Create a temporary directory for extraction
TEMP_DIR=$(mktemp -d)
echo "Extracting backup to temporary directory..."
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Move the extracted files to their proper locations
echo "Restoring data files..."
rm -rf ./instance ./data ./postgres_data ./pgadmin_data
mkdir -p ./instance ./data ./postgres_data ./pgadmin_data

cp -r "$TEMP_DIR"/instance/* ./instance/ 2>/dev/null || true
cp -r "$TEMP_DIR"/data/* ./data/ 2>/dev/null || true
cp -r "$TEMP_DIR"/postgres_data/* ./postgres_data/ 2>/dev/null || true
cp -r "$TEMP_DIR"/pgadmin_data/* ./pgadmin_data/ 2>/dev/null || true

# Restore .env file if it exists in the backup
if [ -f "$TEMP_DIR/.env" ]; then
    echo "Restoring .env file..."
    cp "$TEMP_DIR/.env" ./.env
fi

# Clean up
rm -rf "$TEMP_DIR"

# Set proper SELinux context
echo "Setting SELinux context for restored directories..."
sudo chcon -Rt container_file_t ./instance || true
sudo chcon -Rt container_file_t ./data || true
sudo chcon -Rt container_file_t ./postgres_data || true
sudo chcon -Rt container_file_t ./pgadmin_data || true

# Restart the application if it was running before
if [ "$RESTART_AFTER" = true ]; then
    echo "Restarting application..."
    sudo podman pod start akowe-pod
    echo "Application restarted."
fi

echo "Restore completed successfully!"
