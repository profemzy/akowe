# Staging Deployment Guide

This guide covers deploying Akowe to a staging server with Ubuntu, Docker, and HTTPS.

## Prerequisites

- Ubuntu server (20.04 LTS or newer)
- Docker and Docker Compose installed
- Domain name pointing to your server (akowe-demo.infotitans.ca)
- Ports 80 and 443 open in firewall

## Setup Steps

### 1. Prepare Environment File

Create a `.env` file in the project root with required variables:

```
# Database settings
DB_USER=your_db_user
DB_PASSWORD=your_secure_password
DB_NAME=akowe
DB_HOST=postgres

# Application settings
SECRET_KEY=your_secure_secret_key
PORT=5000
FLASK_ENV=staging

# Performance settings
GUNICORN_WORKERS=4
GUNICORN_TIMEOUT=120

# Optional storage settings
AZURE_STORAGE_CONNECTION_STRING=your_connection_string_if_needed
```

### 2. Clone Repository and Deploy

```bash
# Clone repository
git clone https://github.com/yourusername/akowe.git
cd akowe

# Copy your prepared .env file to the server
# scp .env user@your-server:/path/to/akowe/

# Deploy with HTTPS
./init-letsencrypt.sh
docker-compose -f docker-compose.staging.yml up -d
```

The `init-letsencrypt.sh` script will:
1. Create required directories
2. Set up temporary SSL certificates
3. Start Nginx
4. Obtain Let's Encrypt certificates
5. Reload Nginx with the real certificates

### 3. Verify Deployment

1. Access the application at https://akowe-demo.infotitans.ca
2. Check container status with `docker-compose -f docker-compose.staging.yml ps`
3. View logs with `docker-compose -f docker-compose.staging.yml logs -f`

### 4. Maintenance

#### SSL Certificate Renewal

Certificates will auto-renew via the certbot container. To manually renew:

```bash
docker-compose -f docker-compose.staging.yml run --rm certbot renew
docker-compose -f docker-compose.staging.yml exec nginx nginx -s reload
```

#### Database Backups

Run periodic backups with:

```bash
docker-compose -f docker-compose.staging.yml exec postgres pg_dump -U $DB_USER $DB_NAME > backup_$(date +%Y%m%d).sql
```

#### Updating Application

To deploy updates:

```bash
git pull
docker-compose -f docker-compose.staging.yml build web
docker-compose -f docker-compose.staging.yml up -d
```

## Troubleshooting

### SSL Issues
- Check Nginx logs: `docker-compose -f docker-compose.staging.yml logs nginx`
- Check certbot logs: `docker-compose -f docker-compose.staging.yml logs certbot`
- Verify certificate paths in `nginx/conf.d/default.conf`

### Application Issues
- Check application logs: `docker-compose -f docker-compose.staging.yml logs web`
- Verify environment variables are correctly set
- Check database connection: `docker-compose -f docker-compose.staging.yml exec web python -c "from akowe.factory import create_app; app=create_app(); from flask import current_app; print('Database URI:', current_app.config['SQLALCHEMY_DATABASE_URI'])"`

### Database Issues
- Check database logs: `docker-compose -f docker-compose.staging.yml logs postgres`
- Connect to database: `docker-compose -f docker-compose.staging.yml exec postgres psql -U $DB_USER -d $DB_NAME`