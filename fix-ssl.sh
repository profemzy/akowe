#!/bin/bash

# This script fixes SSL configuration issues with Nginx
echo "Checking SSL certificate files..."
ls -la ./nginx/ssl/live/akowe-demo.infotitans.ca || {
  echo "ERROR: Certificate files not found!"
  exit 1
}

# Copy the simplified SSL configuration
echo "Applying simplified SSL configuration..."
cp ./nginx/conf.d/simple-ssl.conf ./nginx/conf.d/default.conf

# Reload Nginx to apply changes
echo "Reloading Nginx..."
docker compose -f docker-compose.staging.yml exec nginx nginx -s reload

# Check certificate information
echo "Certificate details:"
docker compose -f docker-compose.staging.yml exec nginx openssl x509 -in /etc/nginx/ssl/live/akowe-demo.infotitans.ca/fullchain.pem -text -noout | grep -A2 Validity
docker compose -f docker-compose.staging.yml exec nginx openssl x509 -in /etc/nginx/ssl/live/akowe-demo.infotitans.ca/fullchain.pem -text -noout | grep -A1 "Subject:"
docker compose -f docker-compose.staging.yml exec nginx openssl x509 -in /etc/nginx/ssl/live/akowe-demo.infotitans.ca/fullchain.pem -issuer -noout

echo "Test SSL connection from the server itself:"
curl -Ik https://localhost 

echo "Troubleshooting commands to run if still having issues:"
echo "1. Check Nginx logs: docker compose -f docker-compose.staging.yml logs nginx"
echo "2. Check if port 443 is open: netstat -tlnp | grep 443"
echo "3. Test from outside: curl -Ikv https://akowe-demo.infotitans.ca"