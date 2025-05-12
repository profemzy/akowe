#!/bin/bash

if ! [ -x "$(command -v docker)" ]; then
  echo 'Error: docker is not installed.' >&2
  exit 1
fi

# Create required directories
mkdir -p ./nginx/ssl
mkdir -p ./nginx/acme

# First, start with HTTP-only configuration to serve the application
echo "Starting initial HTTP-only setup..."
docker compose -f docker-compose.staging.yml up -d nginx web postgres

echo "Waiting for services to start..."
sleep 15

echo "Setting up proper permissions for certbot..."
# Make sure the acme directory is writable
docker compose -f docker-compose.staging.yml exec nginx mkdir -p /var/www/acme
docker compose -f docker-compose.staging.yml exec nginx chmod -R 777 /var/www/acme

echo "Verifying Nginx is working properly..."
curl -v http://localhost:80 || echo "Warning: Couldn't reach Nginx on port 80. Check container logs."

# Debug certbot directly with staging environment first (doesn't hit rate limits)
echo "Testing certbot with Let's Encrypt staging environment..."
docker compose -f docker-compose.staging.yml run --rm certbot certonly \
  --webroot --webroot-path=/var/www/acme \
  --staging \
  --email femioladele@infotitans.com --agree-tos --no-eff-email \
  --debug-challenges \
  -d akowe-demo.infotitans.ca

# Now try production certificate
echo "Attempting to obtain real certificate (this might fail if domain is not correctly configured)..."
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
else
  echo "Certificate acquisition failed."
  echo "This is normal for initial setup on a new server."
  echo "Possible issues:"
  echo "1. The domain akowe-demo.infotitans.ca might not be pointing to this server yet"
  echo "2. DNS propagation may not be complete"
  echo "3. Ports 80/443 might be blocked by firewall or not forwarded properly"
  echo ""
  echo "For initial deployment, you can continue using HTTP only."
  echo "Try to run this script again later when DNS is properly configured."
fi

# Start the complete stack
echo "Starting the complete application stack..."
docker compose -f docker-compose.staging.yml up -d

echo "Setup completed!"
echo "Access your application at http://akowe-demo.infotitans.ca"
echo "When certificates are working, you'll be able to use https://akowe-demo.infotitans.ca"
echo ""
echo "For troubleshooting:"
echo "docker compose -f docker-compose.staging.yml logs nginx"
echo "docker compose -f docker-compose.staging.yml logs certbot"