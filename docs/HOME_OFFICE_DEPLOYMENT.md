# Home Office Feature Deployment Guide

This document explains how to deploy the Home Office Calculator feature to production, including handling database migrations correctly.

## Overview

The Home Office Calculator feature adds:
1. A new database table (`home_office`)
2. New UI components for creating and managing home office claims
3. Back-end logic for calculating home office deductions

## Pre-Deployment Checks

Before deploying, verify:

- [x] All code changes are committed
- [x] Database migration script includes the home_office table
- [x] Migration script is compatible with both SQLite and PostgreSQL
- [x] UI updates are complete and tested locally

## Database Migration

### Migration Script Fix

We've made the migration script compatible with both PostgreSQL and SQLite. The key issue was handling the `CASCADE` option in `DROP TABLE` statements, which doesn't work in SQLite.

The solution implemented:
- Detects database dialect (SQLite vs PostgreSQL)
- For SQLite: 
  - Temporarily disables foreign key constraints
  - Drops tables without CASCADE
  - Re-enables foreign key constraints
- For PostgreSQL:
  - Uses the standard CASCADE option

### Running Migrations

The deployment process requires two steps:

1. **Run Application Deployment**:
   ```bash
   # This builds and deploys the application
   ./deploy_to_k8s.sh
   ```

2. **Run Database Migrations**:
   ```bash
   # Set environment variables
   export REGISTRY_URL=wackopsprodacr.azurecr.io
   export IMAGE_TAG=vX.Y.Z  # Use the version from the deployment logs
   
   # Apply the migration job
   envsubst < k8s/migrations-job.yaml | kubectl apply -f -
   ```

3. **Monitor Migration Progress**:
   ```bash
   # Check job status
   kubectl get jobs akowe-database-migrations
   
   # View detailed logs
   kubectl logs job/akowe-database-migrations
   ```

### Migration Troubleshooting

If you see errors in the migration logs:

#### SQLite Compatibility Issues

Several SQLite compatibility issues have been fixed in the migration script:

1. **CASCADE with DROP TABLE**
   ```
   Complete schema migration failed: (sqlite3.OperationalError) near "CASCADE": syntax error
   [SQL: DROP TABLE IF EXISTS timesheet CASCADE;]
   ```

2. **Schema names in SQLite**
   ```
   Complete schema migration failed: (sqlite3.OperationalError) unknown database public
   [SQL: create table public.users...]
   ```

3. **SERIAL datatype in SQLite**
   ```
   SQLite doesn't have a SERIAL datatype for auto-incrementing fields
   ```

4. **Timestamp defaults in SQLite**
   ```
   DEFAULT CURRENT_TIMESTAMP isn't compatible with SQLite
   ```

All these issues have been fixed by:
1. Adding dialect detection for SQLite vs PostgreSQL
2. Creating separate SQL for each database type
3. Using SQLite-specific syntax for foreign keys, auto-increment fields, and timestamps

See the full details in [MIGRATION_FIXES.md](../docs/MIGRATION_FIXES.md)

#### Missing Roles in PostgreSQL

Warning message:
```
WARNING: Role 'akowe_user' does not exist, skipping owner assignment
```

This is normal and can be ignored. The migration script already handles this case by checking if the role exists before attempting to assign ownership.

## Verifying the Deployment

After deployment and migrations:

1. **Check Application Status**:
   ```bash
   kubectl get pods -l app=akowe
   ```

2. **Check for UI Issues**:
   - Log in to the application
   - Navigate to the Home Office section
   - Verify tabs are styled correctly
   - Test creating a new home office claim

3. **Check Database Tables**:
   ```bash
   # Get database credentials from config
   DB_HOST=$(kubectl get configmap akowe-config -o jsonpath='{.data.DB_HOST}')
   DB_PORT=$(kubectl get configmap akowe-config -o jsonpath='{.data.DB_PORT}')
   DB_NAME=$(kubectl get configmap akowe-config -o jsonpath='{.data.DB_NAME}')
   DB_USER=$(kubectl get secret akowe-secrets -o jsonpath='{.data.DB_USER}' | base64 --decode)
   
   # Connect and check table existence
   PGPASSWORD=$(kubectl get secret akowe-secrets -o jsonpath='{.data.DB_PASSWORD}' | base64 --decode) \
   psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
   -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'home_office');"
   ```

## Rollback Procedures

If problems occur after deployment:

### Rolling Back Application

```bash
kubectl rollout undo deployment/akowe
```

### Rolling Back Database Changes

```bash
# Connect to the database
PGPASSWORD=$(kubectl get secret akowe-secrets -o jsonpath='{.data.DB_PASSWORD}' | base64 --decode) \
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME

# Drop the table (inside psql)
DROP TABLE IF EXISTS home_office;
```

## Future Considerations

For future migrations:
1. Always test on both SQLite and PostgreSQL
2. Keep migrations idempotent (can be run multiple times safely)
3. Consider adding explicit rollback methods to the migration script
4. Automate the migration process as part of the deployment script