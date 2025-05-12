# Home Office Table Fix

This document describes how to fix the missing home_office table issue in production Kubernetes.

## Issue

The application is encountering an error when accessing the `/home-office/` route:

```
[2025-05-12 06:01:23,852] ERROR in app: Exception on /home-office/ [GET]
Traceback (most recent call last):
  File "/usr/local/lib/python3.10/site-packages/sqlalchemy/engine/base.py", line 1964, in _exec_single_context
    self.dialect.do_execute(
  File "/usr/local/lib/python3.10/site-packages/sqlalchemy/engine/default.py", line 945, in do_execute
    cursor.execute(statement, parameters)
psycopg2.errors.UndefinedTable: relation "home_office" does not exist
LINE 2: FROM home_office
```

This occurs because the `home_office` table was not created during the initial database migration.

## Solution

We've created a direct table creation approach that:

1. Creates a specialized migration job that only creates the home_office table
2. Includes proper error handling and checks if the table already exists
3. Sets the right PostgreSQL permissions
4. Creates indexes for better performance
5. Uses the latest application image (v1.0.32)

## Deployment Steps

### Method 1: Using the Direct Migration Job (Recommended)

1. Apply the direct migration job:

```bash
# First, delete any existing migration job
kubectl delete job akowe-database-migrations -n wackops 2>/dev/null || true
kubectl delete job akowe-direct-migrations -n wackops 2>/dev/null || true

# Apply the new direct migration job
kubectl apply -f k8s/direct-migrations-job.yaml
```

2. Monitor the migration job logs:

```bash
# Get the migration pod name
MIGRATION_POD=$(kubectl get pods -n wackops -l component=migration --sort-by=.metadata.creationTimestamp -o jsonpath="{.items[-1].metadata.name}")

# Stream the logs
kubectl logs -f $MIGRATION_POD -n wackops
```

3. Verify the migration completed successfully by checking for messages like:
   - "Checking if home_office table exists"
   - "Creating home_office table directly"
   - "home_office table created successfully"
   - "Migration completed successfully"

### Method 2: Using the SQL Script Directly

If Method 1 fails, you can run the SQL script directly against the database:

1. Connect to the database using kubectl and psql:

```bash
# Get database connection details from k8s config
DB_HOST=$(kubectl get cm akowe-config -n wackops -o jsonpath="{.data.DB_HOST}")
DB_PORT=$(kubectl get cm akowe-config -n wackops -o jsonpath="{.data.DB_PORT}")
DB_NAME=$(kubectl get cm akowe-config -n wackops -o jsonpath="{.data.DB_NAME}")
DB_USER=$(kubectl get secret akowe-secrets -n wackops -o jsonpath="{.data.DB_USER}" | base64 -d)
DB_PASSWORD=$(kubectl get secret akowe-secrets -n wackops -o jsonpath="{.data.DB_PASSWORD}" | base64 -d)

# Run SQL script through psql
kubectl run psql-client --image=postgres:14 -n wackops --rm -i --restart=Never -- \
  psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME" \
  -f- < k8s/create_home_office.sql
```

2. Verify the migration completed successfully by checking for messages:
   - "NOTICE: home_office table created successfully"

### Method 3: Manual Table Creation

If both previous methods fail:

1. Connect to the database server via kubectl:

```bash
# Get database connection details
DB_HOST=$(kubectl get cm akowe-config -n wackops -o jsonpath="{.data.DB_HOST}")
DB_PORT=$(kubectl get cm akowe-config -n wackops -o jsonpath="{.data.DB_PORT}")
DB_NAME=$(kubectl get cm akowe-config -n wackops -o jsonpath="{.data.DB_NAME}")
DB_USER=$(kubectl get secret akowe-secrets -n wackops -o jsonpath="{.data.DB_USER}" | base64 -d)
DB_PASSWORD=$(kubectl get secret akowe-secrets -n wackops -o jsonpath="{.data.DB_PASSWORD}" | base64 -d)

# Run interactive psql shell
kubectl run psql-client --image=postgres:14 -n wackops --rm -it --restart=Never -- \
  psql "postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
```

2. Paste and run the following SQL commands:

```sql
-- Create the home_office table if it doesn't exist
DO $$
BEGIN
    -- Check if table exists
    IF NOT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'home_office'
    ) THEN
        -- Create the table
        CREATE TABLE public.home_office (
            id SERIAL PRIMARY KEY,
            tax_year INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            total_home_area NUMERIC(10, 2) NOT NULL,
            office_area NUMERIC(10, 2) NOT NULL,
            area_unit VARCHAR(20) DEFAULT 'sq_ft',
            rent NUMERIC(10, 2) DEFAULT 0.00,
            mortgage_interest NUMERIC(10, 2) DEFAULT 0.00,
            property_tax NUMERIC(10, 2) DEFAULT 0.00,
            home_insurance NUMERIC(10, 2) DEFAULT 0.00,
            utilities NUMERIC(10, 2) DEFAULT 0.00,
            maintenance NUMERIC(10, 2) DEFAULT 0.00,
            internet NUMERIC(10, 2) DEFAULT 0.00,
            phone NUMERIC(10, 2) DEFAULT 0.00,
            business_use_percentage NUMERIC(5, 2) DEFAULT 0.00,
            is_primary_income BOOLEAN DEFAULT TRUE,
            hours_per_week INTEGER DEFAULT 0,
            calculation_method VARCHAR(20) DEFAULT 'percentage',
            simplified_rate NUMERIC(10, 2) DEFAULT 0.00,
            total_deduction NUMERIC(10, 2) DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES public.users (id)
        );

        -- Add indexes for better query performance
        CREATE INDEX ix_home_office_user_id ON public.home_office (user_id);
        CREATE INDEX ix_home_office_tax_year ON public.home_office (tax_year);

        RAISE NOTICE 'home_office table created successfully';
    ELSE
        RAISE NOTICE 'home_office table already exists, skipping creation';
    END IF;
END $$;
```

## Deploy and Test

After completing any of the migration methods:

1. Deploy the updated application:

```bash
kubectl apply -f k8s/02-deployment.yaml
```

2. Test the home office feature in the application.

## Troubleshooting

If the migration job fails:

1. Check the logs for specific error messages.
2. Common issues might include:
   - Permission problems connecting to the database
   - Syntax errors in the SQL
   - Foreign key constraints failing

Solutions to common errors:

- **Error: cannot create index... duplicate key value violates unique constraint**: The table may partially exist. Use Method 3 to connect to the database and check the existing schema.

- **Error: permission denied for schema public**: Ensure the database user has the correct permissions. You may need to contact your database administrator.

- **Error: relation "users" does not exist**: The foreign key constraint is failing because the users table doesn't exist. Modify the SQL to remove the foreign key constraint if necessary.

## Important Notes

- All methods are designed to be safely rerunnable - they check if the home_office table exists before trying to create it.
- The migrations will not affect existing data.
- If you encounter any issues with the database migration, contact the development team for assistance.