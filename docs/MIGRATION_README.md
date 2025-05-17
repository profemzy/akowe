# Database Migration System

This document describes the database migration system for the Akowe project.

## Overview

The migration system has been updated to use a single migration that implements the complete database schema defined in `db-schema.sql`. This approach ensures that the database schema is always in sync with the schema defined in the SQL file.

## Changes Made

1. Created a new Alembic migration (`migrations/versions/20250501_initial_schema.py`) that implements the complete schema from `db-schema.sql`.
2. Disabled existing migrations by renaming them with a `.bak` extension.
3. Updated `run_migrations.py` to use a single migration function that applies the complete schema.

## How to Use

### Running Migrations

To apply the database schema, you can use one of the following methods:

1. Run the migration script directly:
   ```
   python run_migrations.py
   ```

2. Use the test script to verify that the migration works correctly:
   ```
   python test_migration.py
   ```

### Making Schema Changes

If you need to make changes to the database schema:

1. Update the `db-schema.sql` file with your changes.
2. Run the migration script to apply the changes.

This approach ensures that the `db-schema.sql` file is always the source of truth for the database schema.

## Reverting to the Old Migration System

If you need to revert to the old migration system:

1. Rename the `.bak` files in the `migrations/versions` directory to remove the `.bak` extension.
2. Restore the original `run_migrations.py` file.

## Troubleshooting

If you encounter issues with the migration:

1. Check the logs for error messages.
2. Verify that the database connection settings are correct.
3. Ensure that the database user has the necessary permissions to create and modify tables.