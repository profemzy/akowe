#!/bin/bash

if ! [ -x "$(command -v docker)" ]; then
  echo 'Error: docker is not installed.' >&2
  exit 1
fi

# Create required directories
mkdir -p ./nginx/ssl/live/akowe-demo.infotitans.ca
mkdir -p ./nginx/acme

# First, start with HTTP-only configuration and get certificates
echo "Starting initial HTTP-only setup..."
docker compose -f docker-compose.staging.yml up -d nginx web

echo "Waiting for services to start..."
sleep 10

# Request certificate
echo "Requesting Let's Encrypt certificate..."
docker compose -f docker-compose.staging.yml run --rm certbot certonly \
  --webroot --webroot-path=/var/www/acme \
  --email femioladele@infotitans.com --agree-tos --no-eff-email \
  --force-renewal -d akowe-demo.infotitans.ca

# Check if certificate was obtained successfully
if [ -f "./nginx/ssl/live/akowe-demo.infotitans.ca/fullchain.pem" ]; then
  echo "Certificate obtained successfully! Configuring HTTPS..."

  # Replace the Nginx configuration with HTTPS config
  cp ./nginx/https.conf.template ./nginx/conf.d/default.conf

  # Reload Nginx to apply new config
  docker compose -f docker-compose.staging.yml exec nginx nginx -s reload

  echo "HTTPS configured successfully!"
else
  echo "Certificate acquisition failed. Check the Certbot logs for more details."
  echo "Continuing with HTTP only for now. You can try again later."
fi

# Start the complete stack
echo "Starting the complete application stack..."
docker compose -f docker-compose.staging.yml up -d

echo "Setup completed!"
echo "Access your application at https://akowe-demo.infotitans.ca"
echo ""
echo "If HTTPS is not working, check the certbot logs with:"
echo "docker compose -f docker-compose.staging.yml logs certbot"