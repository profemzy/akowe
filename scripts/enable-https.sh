#!/bin/bash

# This script enables HTTPS for an already running Akowe instance
# Run this after DNS is properly configured and Let's Encrypt can verify your domain

# Check if Docker is installed
if ! [ -x "$(command -v docker)" ]; then
  echo 'Error: docker is not installed.' >&2
  exit 1
fi

# Create SSL directories if they don't exist
mkdir -p ./nginx/ssl
mkdir -p ./nginx/acme

# Ensure nginx is running and acme directory is properly set up
echo "Setting up proper permissions for certbot..."
docker compose -f docker-compose.staging.yml exec nginx mkdir -p /var/www/acme
docker compose -f docker-compose.staging.yml exec nginx chmod -R 777 /var/www/acme

# Test if the server is reachable on HTTP
echo "Testing HTTP connectivity..."
curl -I http://akowe-demo.infotitans.ca || {
  echo "WARNING: Cannot reach http://akowe-demo.infotitans.ca"
  echo "Make sure your DNS is properly configured before continuing."
  read -p "Continue anyway? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
}

# Request certificate from Let's Encrypt
echo "Requesting Let's Encrypt certificate..."
docker compose -f docker-compose.staging.yml run --rm certbot certonly \
  --webroot --webroot-path=/var/www/acme \
  --email femioladele@infotitans.com --agree-tos --no-eff-email \
  -d akowe-demo.infotitans.ca

# Check if certificate was obtained successfully
if [ -d "./nginx/ssl/live/akowe-demo.infotitans.ca" ] && [ -f "./nginx/ssl/live/akowe-demo.infotitans.ca/fullchain.pem" ]; then
  echo "Certificate obtained successfully! Configuring HTTPS..."
  
  # Replace the Nginx configuration with HTTPS config
  cp ./nginx/https.conf.template ./nginx/conf.d/default.conf
  
  # Reload Nginx to apply new config
  docker compose -f docker-compose.staging.yml exec nginx nginx -s reload
  
  echo "HTTPS configured successfully!"
  echo "Your application is now accessible at https://akowe-demo.infotitans.ca"
else
  echo "Certificate acquisition failed."
  echo "Possible issues:"
  echo "1. The domain akowe-demo.infotitans.ca might not be pointing to this server"
  echo "2. DNS propagation may not be complete"
  echo "3. Ports 80/443 might be blocked by firewall or not forwarded properly"
  echo ""
  echo "Try again later when DNS is properly configured."
fi