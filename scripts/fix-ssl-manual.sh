#!/bin/bash

# This script fixes SSL configuration issues with manual certificate paths
echo "This script helps manually set up SSL with existing certificates"

# Ask for certificate file paths
read -p "Enter the full path to your certificate file (fullchain.pem): " CERT_PATH
read -p "Enter the full path to your private key file (privkey.pem): " KEY_PATH

# Ensure paths are not empty
if [ -z "$CERT_PATH" ] || [ -z "$KEY_PATH" ]; then
  echo "ERROR: Certificate paths cannot be empty!"
  exit 1
fi

# Check if files exist
if [ ! -f "$CERT_PATH" ] || [ ! -f "$KEY_PATH" ]; then
  echo "ERROR: Certificate files not found at specified paths!"
  exit 1
fi

# Create the SSL directory
mkdir -p ./nginx/ssl/live/akowe-demo.infotitans.ca

# Copy certificates to the expected location
echo "Copying certificates to Nginx directory..."
cp "$CERT_PATH" ./nginx/ssl/live/akowe-demo.infotitans.ca/fullchain.pem
cp "$KEY_PATH" ./nginx/ssl/live/akowe-demo.infotitans.ca/privkey.pem

# Set proper permissions
chmod 644 ./nginx/ssl/live/akowe-demo.infotitans.ca/fullchain.pem
chmod 600 ./nginx/ssl/live/akowe-demo.infotitans.ca/privkey.pem

# Copy the simplified SSL configuration
echo "Applying simplified SSL configuration..."
cp ./nginx/conf.d/simple-ssl.conf ./nginx/conf.d/default.conf

# Reload Nginx to apply changes
echo "Reloading Nginx..."
docker compose -f docker-compose.staging.yml exec nginx nginx -s reload

echo "Waiting for Nginx to reload..."
sleep 5

# Check certificate information
echo "Certificate details:"
docker compose -f docker-compose.staging.yml exec nginx openssl x509 -in /etc/nginx/ssl/live/akowe-demo.infotitans.ca/fullchain.pem -text -noout | head -15

echo "Testing SSL connectivity from server..."
curl -k -I https://localhost

echo "SSL setup complete. Your site should now be accessible via HTTPS."
echo "If you're still having issues, check the Nginx logs:"
echo "docker compose -f docker-compose.staging.yml logs nginx"