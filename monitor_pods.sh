#!/bin/bash
set -e

echo "Akowe Podman Environment Monitor"
echo ""
echo "Current time: $(date)"
echo ""

# Check pod status
echo "===== Pod Status ====="
echo ""
if sudo podman pod ps | grep -q "akowe-pod"; then
    sudo podman pod ps | grep "akowe-pod"
else
    echo "❌ akowe-pod does not exist"
fi

# Check container status
echo ""
echo "===== Container Status ====="
echo ""
for CONTAINER in "akowe-postgres" "akowe-web" "akowe-pgadmin"; do
    if sudo podman ps -a | grep -q "$CONTAINER"; then
        STATUS=$(sudo podman inspect --format '{{.State.Status}}' "$CONTAINER")
        if [ "$STATUS" == "running" ]; then
            echo "✅ $CONTAINER is running"
        else
            echo "⚠️ $CONTAINER is $STATUS"
        fi
    else
        echo "❌ $CONTAINER container does not exist"
    fi
done

# List all running containers
echo ""
echo "===== Running Containers ====="
echo ""
sudo podman ps

# Show resource usage
echo ""
echo "===== Resource Usage ====="
echo ""
echo "Container CPU and Memory Usage:"
sudo podman stats --no-stream

# Show volume information
echo ""
echo "===== Volume Information ====="
echo ""
echo "Data directories:"
du -sh ./postgres_data ./pgadmin_data ./instance ./data 2>/dev/null || echo "Data directories not found"

# Show network information
echo ""
echo "===== Network Information ====="
echo ""
echo "Pod ports:"
if sudo podman pod ps | grep -q "akowe-pod"; then
    sudo podman pod inspect akowe-pod | grep -A 10 "PortMappings"
else
    echo "Pod not found"
fi

# Show logs
echo ""
echo "===== Recent Logs ====="
echo ""
echo "Web application logs (last 5 lines):"
if sudo podman ps | grep -q "akowe-web"; then
    sudo podman logs --tail 5 akowe-web
else
    echo "No logs available"
fi

echo ""
echo "Database logs (last 5 lines):"
if sudo podman ps | grep -q "akowe-postgres"; then
    sudo podman logs --tail 5 akowe-postgres
else
    echo "No logs available"
fi

echo ""
echo "For more detailed logs use:"
echo "podman logs akowe-web"
echo "podman logs akowe-postgres"
echo "podman logs akowe-pgadmin"
echo ""
echo "Monitor completed at $(date)"
