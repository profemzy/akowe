# Akowe with Podman

This document provides detailed information about running Akowe Financial Tracker with Podman on Fedora.

## What is Podman?

Podman is a daemonless container engine for developing, managing, and running OCI Containers on your Linux System. Podman provides a Docker-compatible command line front end that can simply alias the Docker command line interface.

## Why Podman?

- **Rootless Containers**: Podman can run containers as a non-root user, providing better security.
- **Daemonless Architecture**: Unlike Docker, Podman doesn't require a daemon to run containers.
- **Pod Support**: Podman supports pods, which are groups of containers that share resources.
- **SELinux Integration**: Podman works well with SELinux, which is enabled by default on Fedora.

## Prerequisites

- Fedora Linux (or other Linux distribution with Podman installed)
- Podman installed (`sudo dnf install podman`)
- SELinux enabled (default on Fedora)

## Directory Structure

- `./instance`: Flask instance folder (contains SQLite database if used)
- `./data`: Application data files
- `./postgres_data`: PostgreSQL database files
- `./pgadmin_data`: PGAdmin configuration and data
- `./backups`: Backup archives (created by backup_data.sh)

## Scripts

The following scripts are provided to help you manage the application:

### Setup and Configuration

- `setup_selinux.sh`: Sets up SELinux context for volume directories
- `check_podman_setup.sh`: Checks if Podman is properly set up

### Running the Application

- `run_with_podman.sh`: Starts the application using Podman
- `podman-compose.yml`: Alternative way to start the application using podman-compose

### Maintenance

- `monitor_pods.sh`: Shows the status of pods and containers
- `backup_data.sh`: Creates a backup of the application data
- `restore_backup.sh`: Restores a backup of the application data
- `update_app.sh`: Updates the application to the latest version
- `cleanup_podman.sh`: Removes pods and containers
- `seed_demo_data.sh`: Seeds the database with demo data for client demonstrations

## Detailed Usage

### Initial Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/akowe.git
   cd akowe
   ```

2. Create a `.env` file:
   ```bash
   cp .env.example .env
   ```
   
   Edit the `.env` file to set your desired configuration. Make sure to use direct values for the DATABASE_URL:
   ```
   DATABASE_URL=postgresql://akowe_user:akowe_password@postgres:5432/akowe
   ```

3. Make the scripts executable:
   ```bash
   chmod +x *.sh
   ```

4. Set up SELinux context:
   ```bash
   ./setup_selinux.sh
   ```

5. Check Podman setup:
   ```bash
   ./check_podman_setup.sh
   ```

### Running the Application

Using the provided script:
```bash
sudo ./run_with_podman.sh
```

Or using podman-compose (if installed):
```bash
sudo podman-compose -f podman-compose.yml up -d
```

### Monitoring

To check the status of the application:
```bash
./monitor_pods.sh
```

### Backup and Restore

To create a backup:
```bash
./backup_data.sh
```

To restore a backup:
```bash
./restore_backup.sh ./backups/akowe_backup_20250419_123456.tar.gz
```

### Updating

To update the application:
```bash
./update_app.sh
```

### Cleaning Up

To remove pods and containers:
```bash
./cleanup_podman.sh
```

### Seeding Demo Data

To seed the database with demo data for client demonstrations:
```bash
./seed_demo_data.sh
```

This will:
1. Check if the application is running
2. Execute the seed_db.py script inside the container
3. Create sample clients, projects, invoices, timesheets, and transactions

After seeding, you can log in with the admin credentials specified in your .env file.

## Troubleshooting

### SELinux Issues

If you encounter SELinux permission issues, try:

```bash
sudo chcon -Rt container_file_t ./instance ./data ./postgres_data ./pgadmin_data
```

### Database Connection Issues

If the application cannot connect to the database, check:

1. The `.env` file has the correct DATABASE_URL with direct values
2. The PostgreSQL container is running: `sudo podman ps | grep postgres`
3. The database logs: `sudo podman logs akowe-postgres`

### Container Networking Issues

If containers cannot communicate with each other, check:

1. All containers are in the same pod: `sudo podman pod ps`
2. The pod is running: `sudo podman pod inspect akowe-pod`

## Advanced Configuration

### Custom PostgreSQL Configuration

To use a custom PostgreSQL configuration, you can mount a custom `postgresql.conf` file:

```bash
sudo podman run -d --pod akowe-pod \
  --name akowe-postgres \
  --env-file .env \
  --env POSTGRES_USER=${DB_USER:-akowe_user} \
  --env POSTGRES_PASSWORD=${DB_PASSWORD:-akowe_password} \
  --env POSTGRES_DB=${DB_NAME:-akowe} \
  --env PGDATA=/var/lib/postgresql/data/pgdata \
  --volume ./postgres_data:/var/lib/postgresql/data:z \
  --volume ./postgresql.conf:/etc/postgresql/postgresql.conf:z \
  postgres:15-alpine -c 'config_file=/etc/postgresql/postgresql.conf'
```

### Custom Gunicorn Configuration

To use a custom Gunicorn configuration, you can modify the `docker-entrypoint.sh` script or override the CMD in the run command:

```bash
sudo podman run -d --pod akowe-pod \
  --name akowe-web \
  --env-file .env \
  --env DB_HOST=localhost \
  --env DB_PORT=5432 \
  --volume ./instance:/app/instance:z \
  --volume ./data:/app/data:z \
  akowe:latest gunicorn --workers=2 --timeout=60 --bind=0.0.0.0:5000 app:app
```

## References

- [Podman Documentation](https://podman.io/docs)
- [SELinux User's and Administrator's Guide](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/7/html/selinux_users_and_administrators_guide/index)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Gunicorn Documentation](https://docs.gunicorn.org/en/stable/)
