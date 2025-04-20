#!/bin/bash
set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/akowe_backup_${TIMESTAMP}.tar.gz"

echo "Creating backup of Akowe data..."

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if the application is running
if sudo podman pod ps | grep -q "akowe-pod"; then
    echo "Application is running. Stopping pod to ensure data consistency..."
    sudo podman pod stop akowe-pod
    RESTART_AFTER=true
else
    RESTART_AFTER=false
fi

echo "Creating backup archive..."
tar -czf "$BACKUP_FILE" \
    --exclude="postgres_data/pgdata/pg_wal" \
    ./instance \
    ./data \
    ./postgres_data \
    ./pgadmin_data \
    .env

echo "Backup created: $BACKUP_FILE"

# Restart the application if it was running before
if [ "$RESTART_AFTER" = true ]; then
    echo "Restarting application..."
    sudo podman pod start akowe-pod
    echo "Application restarted."
fi

echo "Backup completed successfully!"
echo ""
echo "To restore this backup, run:"
echo "  ./restore_backup.sh $BACKUP_FILE"
