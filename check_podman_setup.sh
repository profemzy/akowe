#!/bin/bash
set -e

echo "Checking Podman setup for Akowe..."
echo ""

# Check if podman is installed
if command -v podman &> /dev/null; then
    PODMAN_VERSION=$(podman --version)
    echo "✅ Podman is installed: $PODMAN_VERSION"
else
    echo "❌ Podman is not installed. Please install Podman first."
    echo "   On Fedora: sudo dnf install podman"
    exit 1
fi

# Check if SELinux is enabled
if command -v getenforce &> /dev/null; then
    SELINUX_STATUS=$(getenforce)
    if [ "$SELINUX_STATUS" == "Enforcing" ] || [ "$SELINUX_STATUS" == "Permissive" ]; then
        echo "✅ SELinux is enabled: $SELINUX_STATUS"
    else
        echo "⚠️ SELinux is disabled. It's recommended to enable SELinux."
        echo "   You may need to adjust the volume settings in the scripts."
    fi
else
    echo "⚠️ Could not determine SELinux status. Make sure SELinux utilities are installed."
    echo "   On Fedora: sudo dnf install policycoreutils-python-utils"
fi

# Check if required directories exist
echo ""
echo "Checking required directories:"
for DIR in "./instance" "./data" "./postgres_data" "./pgadmin_data"; do
    if [ -d "$DIR" ]; then
        echo "✅ Directory exists: $DIR"
    else
        echo "⚠️ Directory does not exist: $DIR (will be created when running the application)"
    fi
done

# Check if .env file exists
echo ""
if [ -f ".env" ]; then
    echo "✅ .env file exists"
else
    echo "⚠️ .env file does not exist. You should create one from .env.example"
    echo "   cp .env.example .env"
fi

# Check if scripts are executable
echo ""
echo "Checking script permissions:"
for SCRIPT in "run_with_podman.sh" "cleanup_podman.sh" "setup_selinux.sh" "monitor_pods.sh"; do
    if [ -f "$SCRIPT" ]; then
        if [ -x "$SCRIPT" ]; then
            echo "✅ Script is executable: $SCRIPT"
        else
            echo "⚠️ Script is not executable: $SCRIPT (run: chmod +x $SCRIPT)"
        fi
    else
        echo "❌ Script does not exist: $SCRIPT"
    fi
done

# Check if podman-compose is installed (optional)
echo ""
if command -v podman-compose &> /dev/null; then
    PODMAN_COMPOSE_VERSION=$(podman-compose --version)
    echo "✅ podman-compose is installed: $PODMAN_COMPOSE_VERSION"
else
    echo "ℹ️ podman-compose is not installed. This is optional but recommended."
    echo "   To install: pip install podman-compose"
fi

echo ""
echo "Setup check completed."
