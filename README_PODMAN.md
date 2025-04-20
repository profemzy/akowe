# Running Akowe with Podman

This guide explains how to run the Akowe Financial Tracker application using Podman on Fedora.

## Prerequisites

- Podman installed on your Fedora system
- SELinux enabled (default on Fedora)

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/akowe.git
   cd akowe
   ```

2. Create a `.env` file with your configuration:
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

## Running the Application

To start the application, run:

```bash
sudo ./run_with_podman.sh
```

This script will:
1. Create necessary directories with proper SELinux context
2. Create a pod for the application
3. Build the application image
4. Start PostgreSQL container
5. Start the Akowe web application container
6. Start PGAdmin container

Once started, you can access:
- Web application: http://localhost:5000
- PGAdmin: http://localhost:5050 (default credentials: admin@example.com / admin)

## Managing the Application

- To stop the application:
  ```bash
  sudo podman pod stop akowe-pod
  ```

- To start the application again:
  ```bash
  sudo podman pod start akowe-pod
  ```

- To remove the pod and containers:
  ```bash
  sudo ./cleanup_podman.sh
  ```

- To monitor the status of the application:
  ```bash
  sudo ./monitor_pods.sh
  ```

- To seed the database with demo data (for client demos):
  ```bash
  sudo ./seed_demo_data.sh
  ```

## Volumes and Data Persistence

The application uses the following volumes for data persistence:

- `./postgres_data`: PostgreSQL database files
- `./pgadmin_data`: PGAdmin configuration and data
- `./instance`: Flask instance folder (contains SQLite database if used)
- `./data`: Application data files

## Troubleshooting

### SELinux Issues

If you encounter SELinux permission issues, the `run_with_podman.sh` script attempts to set the correct context for volume directories. If you still have issues, you can try:

```bash
sudo chcon -Rt container_file_t ./instance ./data ./postgres_data ./pgadmin_data
```

### Database Connection Issues

If the application cannot connect to the database, check:

1. The `.env` file has the correct DATABASE_URL with direct values (not using variable substitution)
2. The PostgreSQL container is running: `sudo podman ps | grep postgres`
3. The database logs: `sudo podman logs akowe-postgres`

### Viewing Logs

- Application logs: `sudo podman logs akowe-web`
- Database logs: `sudo podman logs akowe-postgres`
- PGAdmin logs: `sudo podman logs akowe-pgadmin`
