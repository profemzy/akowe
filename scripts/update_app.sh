#!/bin/bash
set -e

echo "Updating Akowe application..."

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Error: git is not installed. Please install git first."
    echo "On Fedora: sudo dnf install git"
    exit 1
fi

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "Error: This doesn't appear to be a git repository."
    echo "This script is intended to be run from a git clone of the Akowe repository."
    exit 1
fi

# Check if the application is running
if sudo podman pod ps | grep -q "akowe-pod"; then
    echo "Application is running. Stopping pod before update..."
    sudo podman pod stop akowe-pod
    RESTART_AFTER=true
else
    RESTART_AFTER=false
fi

# Create a backup before updating
echo "Creating backup before update..."
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/akowe_backup_before_update_${TIMESTAMP}.tar.gz"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "Creating backup archive..."
tar -czf "$BACKUP_FILE" \
    --exclude="postgres_data/pgdata/pg_wal" \
    ./instance \
    ./data \
    ./postgres_data \
    ./pgadmin_data \
    .env

echo "Backup created: $BACKUP_FILE"

# Pull latest changes
echo "Pulling latest changes from git repository..."
git pull

# Rebuild the application
echo "Rebuilding application image..."
sudo podman build -t akowe:latest -f Dockerfile --target runtime .

# Restart the application if it was running before
if [ "$RESTART_AFTER" = true ]; then
    echo "Restarting application..."
    sudo podman pod start akowe-pod
    
    # Remove and recreate the web container with the new image
    echo "Updating web container with new image..."
    sudo podman stop akowe-web
    sudo podman rm akowe-web
    
    # Run the application container
    sudo podman run -d --pod akowe-pod \
      --name akowe-web \
      --env-file .env \
      --env DB_HOST=localhost \
      --env DB_PORT=5432 \
      --volume ./instance:/app/instance:z \
      --volume ./data:/app/data:z \
      akowe:latest
      
    echo "Application restarted with updated image."
fi

echo "Update completed successfully!"
echo ""
echo "If you encounter any issues, you can restore the backup with:"
echo "  ./restore_backup.sh $BACKUP_FILE"
