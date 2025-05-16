#!/bin/bash

echo "Starting Akowe deployment process..."

# 1. Create required directories
mkdir -p nginx/conf.d nginx/ssl nginx/acme

# 2. Start with HTTP-only configuration
echo "Setting up HTTP-only configuration first..."
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
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
    
    # Static files
    location /static/ {
        proxy_pass http://web:5000/static/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
}
EOF

# 3. Start services
echo "Starting services with HTTP only..."
docker compose -f docker-compose.staging.yml up -d

# 4. Wait for services to be up
echo "Waiting for services to start..."
sleep 20

# 5. Create script for obtaining a certificate later
cat > ./enable-https.sh << 'EOF'
#!/bin/bash
# This script enables HTTPS with Let's Encrypt certificates

echo "Preparing to enable HTTPS..."

# Create required directories
mkdir -p nginx/ssl nginx/acme

# Prepare ACME challenge directory
echo "Setting up directories and permissions..."
docker compose -f docker-compose.staging.yml exec nginx mkdir -p /var/www/acme
docker compose -f docker-compose.staging.yml exec nginx chmod -R 777 /var/www/acme

# Request certificate using standalone mode
echo "Stopping Nginx temporarily to free up port 80..."
docker compose -f docker-compose.staging.yml stop nginx

echo "Requesting Let's Encrypt certificate..."
docker run --rm -it \
  -v ./nginx/ssl:/etc/letsencrypt \
  -v ./nginx/acme:/var/www/acme \
  -p 80:80 \
  certbot/certbot certonly --standalone \
  --preferred-challenges http \
  -d akowe-demo.infotitans.ca \
  --email femioladele@infotitans.com --agree-tos --no-eff-email

# Check if certificate was obtained
if [ -d "./nginx/ssl/live/akowe-demo.infotitans.ca" ] && [ -f "./nginx/ssl/live/akowe-demo.infotitans.ca/fullchain.pem" ]; then
    echo "Certificate obtained successfully! Configuring HTTPS..."
    
    # Update to HTTPS configuration
    cat > ./nginx/conf.d/default.conf << 'EOFMARKER'
server {
    listen 80;
    server_name akowe-demo.infotitans.ca;
    
    # Path for Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/acme;
    }
    
    # Redirect all other HTTP traffic to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name akowe-demo.infotitans.ca;
    
    # SSL certificates
    ssl_certificate /etc/nginx/ssl/live/akowe-demo.infotitans.ca/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/live/akowe-demo.infotitans.ca/privkey.pem;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    
    # Proxy settings
    location / {
        proxy_pass http://web:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
    
    # Static files
    location /static/ {
        proxy_pass http://web:5000/static/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
}
EOFMARKER
    
    # Start Nginx again with the new configuration
    echo "Starting Nginx with HTTPS configuration..."
    docker compose -f docker-compose.staging.yml start nginx
    
    echo "HTTPS setup complete! Your site should be accessible at https://akowe-demo.infotitans.ca"
    
    # Create a renewal script
    cat > ./renew-cert.sh << 'RENEWEOF'
#!/bin/bash
# This script renews the Let's Encrypt certificates

echo "Stopping Nginx to free port 80..."
docker compose -f docker-compose.staging.yml stop nginx

echo "Renewing certificates..."
docker run --rm \
  -v ./nginx/ssl:/etc/letsencrypt \
  -v ./nginx/acme:/var/www/acme \
  -p 80:80 \
  certbot/certbot renew

echo "Starting Nginx again..."
docker compose -f docker-compose.staging.yml start nginx

echo "Certificate renewal process completed!"
RENEWEOF
    chmod +x ./renew-cert.sh
    
    echo "Created renewal script: ./renew-cert.sh"
    echo "You should set up a cron job to run this script monthly."
else
    echo "Certificate acquisition failed."
    echo "Please check that:"
    echo "1. The domain akowe-demo.infotitans.ca points to this server's IP"
    echo "2. Port 80 is open and not blocked by firewall"
    echo "3. DNS propagation is complete"
    
    # Start Nginx again with HTTP only
    docker compose -f docker-compose.staging.yml start nginx
    
    echo "Continuing with HTTP only. Try again later with:"
    echo "./enable-https.sh"
fi
EOF

chmod +x ./enable-https.sh

# 6. Create a self-signed certificate script as fallback
cat > ./use-self-signed.sh << 'EOF'
#!/bin/bash
# This script sets up self-signed SSL certificates

echo "Setting up self-signed certificates..."

# Create required directories
mkdir -p nginx/ssl/live/akowe-demo.infotitans.ca

# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ./nginx/ssl/live/akowe-demo.infotitans.ca/privkey.pem \
  -out ./nginx/ssl/live/akowe-demo.infotitans.ca/fullchain.pem \
  -subj "/CN=akowe-demo.infotitans.ca" \
  -addext "subjectAltName = DNS:akowe-demo.infotitans.ca"

# Set permissions
chmod 644 ./nginx/ssl/live/akowe-demo.infotitans.ca/fullchain.pem
chmod 600 ./nginx/ssl/live/akowe-demo.infotitans.ca/privkey.pem

# Update Nginx configuration
cat > ./nginx/conf.d/default.conf << 'EOFMARKER'
server {
    listen 80;
    server_name akowe-demo.infotitans.ca;
    
    # Path for Let's Encrypt verification
    location /.well-known/acme-challenge/ {
        root /var/www/acme;
    }
    
    # Redirect all other HTTP traffic to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name akowe-demo.infotitans.ca;
    
    # SSL certificates
    ssl_certificate /etc/nginx/ssl/live/akowe-demo.infotitans.ca/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/live/akowe-demo.infotitans.ca/privkey.pem;
    
    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    
    # Proxy settings
    location / {
        proxy_pass http://web:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
    
    # Static files
    location /static/ {
        proxy_pass http://web:5000/static/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
}
EOFMARKER

# Restart Nginx with new configuration
docker compose -f docker-compose.staging.yml restart nginx

echo "Self-signed certificate setup complete!"
echo "Your site should now be accessible via HTTPS (with browser warning)."
echo "When ready for a real certificate, run: ./enable-https.sh"
EOF

chmod +x ./use-self-signed.sh

echo "Deployment complete! Your site is running with HTTP at http://akowe-demo.infotitans.ca"
echo ""
echo "To enable HTTPS with Let's Encrypt certificates, run:"
echo "./enable-https.sh"
echo ""
echo "Or to use self-signed certificates for testing, run:"
echo "./use-self-signed.sh"