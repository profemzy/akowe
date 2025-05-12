# Akowe Production Deployment Guide

This guide covers deploying Akowe to a production or staging server with Docker Compose, Nginx, and HTTPS.

## Prerequisites

- Ubuntu server (20.04 LTS or newer)
- Docker and Docker Compose installed
- Domain name pointing to your server (akowe-demo.infotitans.ca)
- Ports 80 and 443 open in your firewall

## Deployment Steps

### 1. Prepare the Server

```bash
# Update package lists
sudo apt update

# Install required packages
sudo apt install -y docker.io docker-compose curl openssl

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to the docker group (optional)
sudo usermod -aG docker $USER
# Log out and back in for this to take effect
```

### 2. Configure Firewall

Ensure ports 80 and 443 are open:

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### 3. Clone Repository

```bash
git clone https://github.com/your-username/akowe.git
cd akowe
```

### 4. Set Up Environment Variables

Create a `.env` file based on the sample:

```bash
cp sample.env .env
# Edit the .env file with your preferred editor
nano .env
```

Be sure to set secure values for `DB_PASSWORD` and `SECRET_KEY`.

### 5. Run the Deployment Script

```bash
chmod +x deploy.sh
./deploy.sh
```

This script will:
- Create necessary directories
- Set up HTTP-only configuration initially
- Start all services (Postgres, Web app, Nginx)
- Create scripts for enabling HTTPS later

### 6. Enable HTTPS

After DNS has propagated and your domain points to your server, you can enable HTTPS:

```bash
./enable-https.sh
```

This will:
- Stop Nginx temporarily
- Obtain Let's Encrypt certificates
- Configure Nginx with HTTPS
- Restart Nginx

If Let's Encrypt fails, you can use self-signed certificates for testing:

```bash
./use-self-signed.sh
```

## Maintenance

### Certificate Renewal

Let's Encrypt certificates expire after 90 days. Set up a cron job to renew them:

```bash
# Edit crontab
crontab -e

# Add this line to run renewal monthly
0 0 1 * * /path/to/akowe/renew-cert.sh >> /path/to/akowe/cert-renewal.log 2>&1
```

### Backup Database

Run regular backups of your database:

```bash
docker compose -f docker-compose.staging.yml exec postgres pg_dump -U $DB_USER $DB_NAME > backup_$(date +%Y%m%d).sql
```

### Update Application

To update the application:

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker compose -f docker-compose.staging.yml up -d --build
```

## Troubleshooting

### Check container status
```bash
docker compose -f docker-compose.staging.yml ps
```

### View logs
```bash
# All logs
docker compose -f docker-compose.staging.yml logs

# Specific service logs
docker compose -f docker-compose.staging.yml logs nginx
docker compose -f docker-compose.staging.yml logs web
```

### Test HTTP/HTTPS
```bash
# Test HTTP
curl -I http://akowe-demo.infotitans.ca

# Test HTTPS
curl -k -I https://akowe-demo.infotitans.ca
```