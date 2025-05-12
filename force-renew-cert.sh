#!/bin/bash

# This script forces renewal of Let's Encrypt certificates by deleting the existing ones

# Check if Docker is installed
if ! [ -x "$(command -v docker)" ]; then
  echo 'Error: docker is not installed.' >&2
  exit 1
fi

echo "WARNING: This script will delete existing certificates and request new ones."
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  exit 1
fi

# Stop containers first
echo "Stopping containers..."
docker compose -f docker-compose.staging.yml down

# Clean up existing certificates
echo "Removing existing certificates..."
rm -rf ./nginx/ssl/live/akowe-demo.infotitans.ca
rm -rf ./nginx/ssl/archive/akowe-demo.infotitans.ca
rm -rf ./nginx/ssl/renewal/akowe-demo.infotitans.ca.conf

# Create required directories
mkdir -p ./nginx/ssl
mkdir -p ./nginx/acme

# Start with HTTP only first
echo "Starting with HTTP only configuration..."
# Save HTTP-only configuration
cat > ./nginx/conf.d/default.conf << EOF
server {
    listen 80;
    server_name akowe-demo.infotitans.ca;
    
    # Path for Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/acme;
    }
    
    # Proxy settings
    location / {
        proxy_pass http://web:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}
EOF

# Start stack with HTTP-only
docker compose -f docker-compose.staging.yml up -d

echo "Waiting for services to start..."
sleep 20

# Setup challenge directory permissions
echo "Setting up acme-challenge directory..."
docker compose -f docker-compose.staging.yml exec nginx mkdir -p /var/www/acme
docker compose -f docker-compose.staging.yml exec nginx chmod -R 777 /var/www/acme

# Force renewal with verbose output
echo "Requesting new certificate with force renewal and debug mode..."
docker compose -f docker-compose.staging.yml run --rm certbot certonly \
  --webroot --webroot-path=/var/www/acme \
  --email femioladele@infotitans.com --agree-tos --no-eff-email \
  --force-renewal --debug-challenges -v \
  -d akowe-demo.infotitans.ca

# Check if certificate was obtained
if [ -d "./nginx/ssl/live/akowe-demo.infotitans.ca" ] && [ -f "./nginx/ssl/live/akowe-demo.infotitans.ca/fullchain.pem" ]; then
  echo "Certificate obtained successfully!"
  
  # Apply SSL configuration
  echo "Applying SSL configuration..."
  cp ./nginx/conf.d/simple-ssl.conf ./nginx/conf.d/default.conf
  
  # Reload Nginx
  docker compose -f docker-compose.staging.yml exec nginx nginx -s reload
  
  echo "Certificate details:"
  docker compose -f docker-compose.staging.yml exec nginx openssl x509 -in /etc/nginx/ssl/live/akowe-demo.infotitans.ca/fullchain.pem -text -noout | grep -A2 Validity
else
  echo "Failed to obtain certificate."
  echo "Check the output above for errors."
  
  # Print troubleshooting info
  echo "Troubleshooting information:"
  echo "1. Make sure your domain akowe-demo.infotitans.ca points to this server's IP"
  echo "2. Make sure port 80 is open and not blocked by firewall"
  echo "3. Try accessing http://akowe-demo.infotitans.ca/.well-known/acme-challenge/test from outside"
fi