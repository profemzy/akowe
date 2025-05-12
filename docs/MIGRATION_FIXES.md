# Database Migration Fixes for SQLite and PostgreSQL Compatibility

## Overview

This document describes the fixes required to make the database migrations work properly with both SQLite and PostgreSQL databases. These fixes ensure that the migration scripts can run successfully in both development (SQLite) and production (PostgreSQL) environments.

## Issues and Fixes

We encountered several compatibility issues when running migrations:

1. **CASCADE in DROP TABLE statements**
   - **Issue**: SQLite doesn't support the `CASCADE` option in `DROP TABLE` statements.
   - **Fix**: Detect database dialect and use separate code paths:
     - For SQLite: Disable foreign keys, drop tables without CASCADE, then re-enable foreign keys
     - For PostgreSQL: Continue using CASCADE option

2. **Schema names in SQLite**
   - **Issue**: SQLite doesn't support schema names (e.g., `public.users`)
   - **Fix**: Generate different SQL for each dialect:
     - For SQLite: Use plain table names (e.g., `users`)
     - For PostgreSQL: Continue using schema-qualified names (e.g., `public.users`)

3. **SERIAL datatype in SQLite**
   - **Issue**: SQLite doesn't have a `SERIAL` datatype for auto-incrementing fields
   - **Fix**: Use `INTEGER PRIMARY KEY AUTOINCREMENT` in SQLite and `SERIAL PRIMARY KEY` in PostgreSQL

4. **DEFAULT CURRENT_TIMESTAMP in SQLite**
   - **Issue**: SQLite's syntax for default timestamp values is different
   - **Fix**: Use `DEFAULT (datetime('now'))` in SQLite and `DEFAULT CURRENT_TIMESTAMP` in PostgreSQL

5. **Foreign key constraints in SQLite**
   - **Issue**: SQLite's syntax for foreign key constraints is different
   - **Fix**: Use `FOREIGN KEY (column) REFERENCES table(id)` in SQLite
   
6. **Boolean defaults in SQLite**
   - **Issue**: SQLite doesn't have a built-in Boolean type, uses integers instead
   - **Fix**: Use `DEFAULT 1` instead of `DEFAULT TRUE` in SQLite

## Changes Made to run_migrations.py

### 1. Table Dropping Logic

```python
# Drop existing tables if they exist
logger.info("Dropping existing tables if they exist")

# Handle different SQL syntax based on database dialect
if dialect == 'sqlite':
    # SQLite doesn't support CASCADE, so we need to handle foreign keys differently
    # Temporarily disable foreign key constraints
    conn.execute(text("PRAGMA foreign_keys = OFF;"))
    
    # Drop tables without CASCADE
    conn.execute(text("DROP TABLE IF EXISTS timesheet;"))
    conn.execute(text("DROP TABLE IF EXISTS income;"))
    conn.execute(text("DROP TABLE IF EXISTS invoice;"))
    conn.execute(text("DROP TABLE IF EXISTS project;"))
    conn.execute(text("DROP TABLE IF EXISTS client;"))
    conn.execute(text("DROP TABLE IF EXISTS expense;"))
    conn.execute(text("DROP TABLE IF EXISTS users;"))
    
    # Re-enable foreign key constraints
    conn.execute(text("PRAGMA foreign_keys = ON;"))
else:
    # PostgreSQL and others support CASCADE
    conn.execute(text("DROP TABLE IF EXISTS timesheet CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS income CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS invoice CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS project CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS client CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS expense CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
```

### 2. Table Creation Logic

```python
# Create users table
logger.info("Creating users table")

if dialect == 'sqlite':
    # SQLite version without schema name and using INTEGER for id instead of serial
    conn.execute(text("""
    CREATE TABLE users
    (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        username      VARCHAR(64)  NOT NULL,
        email         VARCHAR(120) NOT NULL,
        password_hash VARCHAR(256) NOT NULL,
        first_name    VARCHAR(64),
        last_name     VARCHAR(64),
        hourly_rate   NUMERIC(10, 2),
        is_admin      BOOLEAN,
        is_active     BOOLEAN,
        created_at    TIMESTAMP,
        updated_at    TIMESTAMP,
        last_login    TIMESTAMP
    );
    """))
else:
    # PostgreSQL version with schema name and serial type
    conn.execute(text("""
    CREATE TABLE public.users
    (
        id            SERIAL
            PRIMARY KEY,
        username      VARCHAR(64)  NOT NULL,
        email         VARCHAR(120) NOT NULL,
        password_hash VARCHAR(256) NOT NULL,
        first_name    VARCHAR(64),
        last_name     VARCHAR(64),
        hourly_rate   NUMERIC(10, 2),
        is_admin      BOOLEAN,
        is_active     BOOLEAN,
        created_at    TIMESTAMP,
        updated_at    TIMESTAMP,
        last_login    TIMESTAMP
    );
    """))
```

### 3. Index Creation Logic

```python
# Create indexes
if dialect == 'sqlite':
    conn.execute(text("CREATE UNIQUE INDEX ix_users_username ON users (username);"))
    conn.execute(text("CREATE UNIQUE INDEX ix_users_email ON users (email);"))
else:
    conn.execute(text("CREATE UNIQUE INDEX ix_users_username ON public.users (username);"))
    conn.execute(text("CREATE UNIQUE INDEX ix_users_email ON public.users (email);"))
```

### 4. Home Office Table Creation

```python
if dialect == 'sqlite':
    create_sql = """
    CREATE TABLE home_office (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        is_primary_income BOOLEAN DEFAULT 1,
        hours_per_week INTEGER DEFAULT 0,
        calculation_method VARCHAR(20) DEFAULT 'percentage',
        simplified_rate NUMERIC(10, 2) DEFAULT 0.00,
        total_deduction NUMERIC(10, 2) DEFAULT 0.00,
        created_at TIMESTAMP DEFAULT (datetime('now')),
        updated_at TIMESTAMP DEFAULT (datetime('now')),
        FOREIGN KEY (user_id) REFERENCES users (id)
    );
    """
else:
    create_sql = """
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
    """
```

## Testing the Fixes

After implementing these fixes, the migrations run successfully on both SQLite and PostgreSQL:

1. **PostgreSQL (Production)**: Both migrations complete successfully
2. **SQLite (Development)**: Both migrations complete successfully

## Deployment Recommendations

1. **Run Migrations Separately**: Keep running migrations as a separate step from application deployment
2. **Test in Both Environments**: Always test migrations in both SQLite and PostgreSQL environments before deployment
3. **Keep Conditional Logic**: Maintain dialect-specific SQL for each database type
4. **Future Tables**: Follow the same pattern for any future table additions

## Next Steps

1. Update the CI/CD pipeline to include automated testing of migrations in both SQLite and PostgreSQL environments
2. Consider creating helper functions to generate dialect-specific SQL to reduce code duplication
3. Add more detailed logging to help troubleshoot any future migration issues