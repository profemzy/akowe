#!/bin/bash
set -e

echo "Seeding Akowe database with demo data..."

# Check if the application is running
if ! sudo podman ps | grep -q "akowe-web"; then
    echo "Error: Akowe application is not running."
    echo "Please start the application first with: ./run_with_podman.sh"
    exit 1
fi

echo "Copying seed script to container..."
sudo podman cp tools/simple_seed.py akowe-web:/app/simple_seed.py

echo "Running simple seed script inside the container..."
sudo podman exec akowe-web python /app/simple_seed.py

echo ""
echo "Demo data has been seeded successfully!"
echo ""
echo "You can now log in to the application with:"
echo "  Username: ${ADMIN_USERNAME:-admin}"
echo "  Password: ${ADMIN_PASSWORD:-secure-admin-password}"
echo ""
echo "The application is available at: http://localhost:5000"
