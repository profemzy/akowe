#!/bin/bash

if ! [ -x "$(command -v docker)" ]; then
  echo 'Error: docker is not installed.' >&2
  exit 1
fi

# Create required directories
mkdir -p ./nginx/ssl/live/akowe-demo.infotitans.ca
mkdir -p ./nginx/acme

# Set up dummy certificate for Nginx to start
openssl req -x509 -nodes -newkey rsa:4096 -days 1 \
  -keyout ./nginx/ssl/live/akowe-demo.infotitans.ca/privkey.pem \
  -out ./nginx/ssl/live/akowe-demo.infotitans.ca/fullchain.pem \
  -subj "/CN=akowe-demo.infotitans.ca"

# Start nginx service only
docker compose -f docker-compose.staging.yml up -d nginx

# Request certificate
docker compose -f docker-compose.staging.yml run --rm certbot certonly \
  --webroot --webroot-path=/var/www/acme \
  --email femioladele@infotitans.com --agree-tos --no-eff-email \
  --force-renewal -d akowe-demo.infotitans.ca

# Reload nginx to use the new certificate
docker compose -f docker-compose.staging.yml exec nginx nginx -s reload

echo "Setup completed!"
echo "Now start the complete stack with: docker compose -f docker-compose.staging.yml up -d"