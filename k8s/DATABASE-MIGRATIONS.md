# Database Migrations Guide for Akowe

This document explains how to run database migrations for the Akowe application, both in local development and production environments.

## Overview

Akowe uses a consolidated migration approach, where all database schema updates are managed through a single migration script (`run_migrations.py`). This script:

1. Runs all required migrations in sequence
2. Provides detailed logging of migration progress
3. Handles errors gracefully, allowing other migrations to continue if one fails
4. Returns appropriate exit codes for CI/CD pipelines
5. Automatically detects and adapts to PostgreSQL or SQLite databases
6. Uses multiple table detection strategies for maximum reliability
7. Includes robust error handling and fallback mechanisms for each database type

## Current Migrations

The migration script currently handles the following migrations:

1. **Add last_login column to users table**: Adds a timestamp column to track user login times
2. **Add user_id column to expense table**: Links expenses to users who created them

> **Note**: The migration script automatically detects whether tables are in the 'public' schema (e.g., 'public.user', 'public.expense') as in production, or using standard names ('users', 'expense') as in development.

## Running Migrations

### Local Development

To run migrations in your local development environment:

```bash
# Activate your virtual environment
source ~/akowenv/bin/activate

# Navigate to the project directory
cd /path/to/akowe

# Run the consolidated migration script
python run_migrations.py
```

### Production Environment (Kubernetes)

For production deployments, we use a Kubernetes Job to run migrations before updating the application:

1. **Update the Docker image**:
   ```bash
   # Build the Docker image with the latest migrations
   docker build -t your-registry/akowe:version .
   
   # Push the image to your registry
   docker push your-registry/akowe:version
   ```

2. **Run the migration job**:
   ```bash
   # Set environment variables
   export REGISTRY_URL=your-registry
   export IMAGE_TAG=version
   
   # Apply the consolidated migration job
   # This single job replaces all previous individual migration jobs
   envsubst < k8s/migrations-job.yaml | kubectl apply -f -
   ```

> **Important**: The `migrations-job.yaml` job uses the consolidated `run_migrations.py` script which includes all required migrations. The older individual migration jobs (like `add-last-login-migration.yaml` and `add-user-id-to-expense-job.yaml`) are deprecated and should no longer be used.

3. **Monitor the migration job**:
   ```bash
   # Check job status
   kubectl get jobs akowe-database-migrations
   
   # View detailed logs
   kubectl logs job/akowe-database-migrations
   ```

4. **Clean up (optional)**:
   If you need to clean up the job before the TTL expires:
   ```bash
   kubectl delete job akowe-database-migrations
   ```

## Common Issues and Troubleshooting

### Connection Issues

If the migration job fails with connection issues:

1. Verify your database credentials in Kubernetes secrets
2. Check that the database is accessible from the Kubernetes cluster
3. Ensure firewall rules allow the connection

### Permission Issues

If migrations fail due to permission issues:

1. Ensure the database user has ALTER TABLE privileges
2. Verify that the Kubernetes pod has access to the necessary secrets

### Schema and Table Name Issues

If migrations fail due to table name or schema issues:

1. The migration script is designed to automatically detect whether tables use:
   - Production naming: `public.user`, `public.expense`
   - Development naming: `users`, `expense`

2. Check the migration logs to see what tables were detected
3. The updated migration script now uses multiple detection methods:
   - For PostgreSQL: It tries pg_tables catalog, information_schema, and direct table queries
   - For SQLite: It tries direct table existence checks for various naming patterns
   - Each approach has built-in fallbacks for maximum compatibility

4. The improved error handling includes:
   - Schema-aware operations for PostgreSQL 
   - PL/pgSQL blocks with exception handling for robust execution
   - Table verification after each migration step
   - Multiple verification methods with fallbacks
   - Detailed logging at each step for easier troubleshooting

5. If your database still has issues, check the logs to see which detection methods failed and customize as needed

### Concurrent Migrations

To avoid conflicts when multiple instances might run migrations:

1. Run migrations as a separate job before deploying new application versions
2. Use the `IF NOT EXISTS` clause in migrations (already implemented)
3. Wait for migration job completion before deploying application updates

## Adding New Migrations

To add a new migration:

1. Create a migration function in `run_migrations.py` following the existing pattern
2. Add your migration to the `migrations` list in the `run_migrations` function
3. Test locally before deploying to production

Example:

```python
def run_my_new_migration():
    """Apply a new migration."""
    app = create_app()
    with app.app_context():
        logger.info("Starting my new migration")
        
        # Create connection
        conn = db.engine.connect()
        
        # Execute migration SQL
        conn.execute(text("YOUR SQL HERE;"))
        conn.commit()
        
        # Verify success
        # ...
```

## Best Practices

1. Always make migrations idempotent (can be run multiple times without harm)
2. Include verification steps after each migration
3. Use transactions where appropriate
4. Add proper error handling and logging
5. Document new migrations in this file

## Rollback Procedures

If a migration needs to be rolled back:

1. Add a rollback function in the migration script
2. For critical issues, you may need to restore from a database backup
3. Consider the impact on application compatibility when rolling back migrations

Example rollback for the user_id column in expenses:

```sql
-- Drop the foreign key constraint
ALTER TABLE expense DROP CONSTRAINT IF EXISTS fk_expense_user;

-- Drop the column
ALTER TABLE expense DROP COLUMN IF EXISTS user_id;
```