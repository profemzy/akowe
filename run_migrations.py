"""Consolidated migration script for Akowe.

This script runs all required database migrations in the proper sequence.
"""
import logging
import sys
from decimal import Decimal

from sqlalchemy import text

from akowe.akowe import create_app
from akowe.models import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('migrations')


def run_migrations():
    """Run all migrations in sequence."""
    logger.info("Starting consolidated migrations")

    # List of migrations to run
    migrations = []

    # Check if we should skip the complete schema migration
    skip_complete_schema = os.environ.get('SKIP_COMPLETE_SCHEMA', '').lower() in ('true', '1', 'yes')

    if not skip_complete_schema:
        # Migration to apply the complete schema from db-schema.sql
        migrations.append({
            "name": "Apply complete schema from db-schema.sql",
            "function": run_complete_schema_migration
        })
    else:
        logger.info("Skipping complete schema migration as requested by SKIP_COMPLETE_SCHEMA")

    # Always include the home_office table migration
    migrations.append({
        "name": "Add home_office table",
        "function": run_home_office_migration
    })

    # Keep track of successful migrations
    success_count = 0

    # Run each migration
    for i, migration in enumerate(migrations):
        logger.info(f"Running migration {i + 1}/{len(migrations)}: {migration['name']}")
        try:
            migration["function"]()
            success_count += 1
            logger.info(f"Migration {i + 1}/{len(migrations)} completed successfully")
        except Exception as e:
            logger.error(f"Migration {i + 1}/{len(migrations)} failed: {str(e)}")
            # Continue with next migration even if one fails

    # Report results
    logger.info(f"Migration run completed. {success_count}/{len(migrations)} migrations successful.")

    if success_count < len(migrations):
        logger.warning("Some migrations failed. Check logs for details.")
        return False

    return True


def run_last_login_migration():
    """Apply the migration to add last_login column to users table."""
    app = create_app()
    with app.app_context():
        logger.info("Starting migration to add last_login column to users table")

        # Create connection
        conn = db.engine.connect()

        # Detect database dialect
        dialect = db.engine.dialect.name
        logger.info(f"Database dialect: {dialect}")

        # Initialize variables
        user_table = None

        # Approach based on database dialect
        if dialect == 'postgresql':
            logger.info("Using PostgreSQL-specific approach")

            try:
                # Try to directly modify tables based on common PostgreSQL conventions
                # First, attempt to identify the user table in PostgreSQL
                # Try various methods to detect table existence
                try:
                    # Method 1: Check using pg_tables
                    result = conn.execute(text(
                        "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('users', 'user');"
                    ))
                    tables = [row[0] for row in result]
                    if tables:
                        user_table = tables[0]
                        logger.info(f"Found user table using pg_tables: {user_table}")
                except Exception as e:
                    logger.warning(f"pg_tables check failed: {str(e)}")

                # If first method failed, try another approach    
                if not user_table:
                    try:
                        # Method 2: Try direct ALTER TABLE and catch errors
                        logger.info("Attempting direct table operations for 'user'")
                        conn.execute(text("SELECT 1 FROM public.\"user\" LIMIT 1;"))
                        user_table = 'user'
                        logger.info("Found 'user' table via direct query")
                    except Exception:
                        try:
                            logger.info("Attempting direct table operations for 'users'")
                            conn.execute(text("SELECT 1 FROM public.users LIMIT 1;"))
                            user_table = 'users'
                            logger.info("Found 'users' table via direct query")
                        except Exception as e:
                            logger.warning(f"Direct table query failed: {str(e)}")

                # Apply fallback if detection failed
                if not user_table:
                    logger.warning("Table detection failed, trying both 'user' and 'users'")
                    user_table = 'user'  # Default to 'user' for PostgreSQL production environments

            except Exception as e:
                logger.error(f"PostgreSQL table detection failed: {str(e)}")
                logger.info("Falling back to default user table name")
                user_table = 'user'  # Default for PostgreSQL

        else:
            # For SQLite and other databases
            logger.info("Using standard approach for non-PostgreSQL database")
            try:
                # For SQLite, information_schema doesn't exist, so try direct table checks
                if dialect == 'sqlite':
                    tables = []
                    try:
                        conn.execute(text("SELECT 1 FROM users LIMIT 1;"))
                        tables.append('users')
                    except Exception:
                        pass

                    try:
                        conn.execute(text("SELECT 1 FROM user LIMIT 1;"))
                        tables.append('user')
                    except Exception:
                        pass

                    logger.info(f"Found user tables via direct check: {tables}")
                else:
                    # For other databases, try information_schema
                    result = conn.execute(text(
                        "SELECT table_name FROM information_schema.tables "
                        + "WHERE table_schema = 'public' AND table_name IN ('users', 'user');"
                    ))
                    tables = [row[0] for row in result]
                    logger.info(f"Found user tables in schema: {tables}")

                # Determine correct user table name
                user_table = 'user' if 'user' in tables else 'users'

            except Exception as e:
                logger.warning(f"Table detection failed: {str(e)}")
                logger.info("Falling back to default user table name")
                user_table = 'users'  # Default for SQLite/others

        logger.info("Using user table name: {}".format(user_table))

        # Add the last_login column with appropriate SQL for the dialect
        try:
            if dialect == 'postgresql':
                # PostgreSQL-specific approach with schema handling
                sql = """
                DO $$
                BEGIN
                    -- Try with schema-qualified table
                    BEGIN
                        ALTER TABLE public."user" ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;
                    EXCEPTION WHEN undefined_table THEN
                        -- Try without schema qualification as fallback
                        BEGIN
                            ALTER TABLE "user" ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;
                        EXCEPTION WHEN undefined_table THEN
                            -- Try other table name as last resort
                            ALTER TABLE users 
                            ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;
                        END;
                    END;
                END $$;
                """
            else:
                # Generic SQL for SQLite and others
                sql = "ALTER TABLE {} ADD COLUMN last_login TIMESTAMP;".format(user_table)

            logger.info("Executing SQL: {}".format(sql))
            conn.execute(text(sql))
            conn.commit()
            logger.info("SQL executed successfully")

        except Exception as e:
            logger.error(f"Failed to add last_login column: {str(e)}")
            # Don't raise yet, try to verify if it worked despite errors

        # Verify the column was added using the most reliable method for each dialect
        column_added = False

        try:
            if dialect == 'postgresql':
                # For PostgreSQL, try different verification methods
                try:
                    # Method 1: Check using information_schema if available
                    for table_name in ['user', 'users']:
                        result = conn.execute(text(
                            "SELECT column_name FROM information_schema.columns "
                            + "WHERE table_schema = 'public' AND table_name='{}' ".format(table_name)
                            + "AND column_name='last_login';"
                        ))
                        if result.rowcount > 0:
                            logger.info("Migration verified via information_schema: last_login column found in {}".format(table_name))
                            column_added = True
                            break
                except Exception:
                    pass

                # Method 2: Direct query if information_schema approach failed
                if not column_added:
                    try:
                        for table_name in ['user', 'users']:
                            try:
                                conn.execute(text(
                                    'SELECT last_login FROM public."{}" LIMIT 0;'.format(table_name)
                                ))
                                logger.info("Migration verified via direct query: last_login column found in {}".format(table_name))
                                column_added = True
                                break
                            except Exception:
                                continue
                    except Exception as e:
                        logger.warning(f"Direct column verification failed: {str(e)}")
            else:
                # For SQLite and others, try direct table query
                try:
                    conn.execute(text(f'SELECT last_login FROM {user_table} LIMIT 0;'))
                    logger.info("Migration verified: last_login column found in {}".format(user_table))
                    column_added = True
                except Exception as e:
                    logger.warning(f"Column verification failed: {str(e)}")
                    # Try the other table as fallback
                    other_table = 'users' if user_table == 'user' else 'user'
                    try:
                        conn.execute(text('SELECT last_login FROM {} LIMIT 0;'.format(other_table)))
                        logger.info("Migration verified: last_login column found in {}".format(other_table))
                        column_added = True
                    except Exception:
                        pass

        except Exception as e:
            logger.error(f"Column verification failed: {str(e)}")

        # Final verification result
        if column_added:
            logger.info("Migration successful: last_login column was added to user table")
            return
        else:
            logger.error("Migration failed: last_login column not found after migration")
            raise Exception("Migration verification failed")


def run_complete_schema_migration():
    """Apply the complete schema migration from db-schema.sql."""
    app = create_app()
    with app.app_context():
        logger.info("Starting complete schema migration from db-schema.sql")

        # Create connection
        conn = db.engine.connect()

        # Detect database dialect
        dialect = db.engine.dialect.name
        logger.info(f"Database dialect: {dialect}")

        try:
            # Skip the complete schema migration as requested
            logger.info("Skipping complete schema migration per user request")
            conn.commit()
            logger.info("Complete schema migration skipped successfully")
            return

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

            # Check for PostgreSQL role existence
            role_exists = False
            if dialect == 'postgresql':
                try:
                    # First check if the role exists
                    role_exists = conn.execute(text(
                        "SELECT 1 FROM pg_roles WHERE rolname = 'akowe_user';"
                    )).scalar() is not None

                    if role_exists:
                        conn.execute(text("ALTER TABLE public.users OWNER TO akowe_user;"))
                    else:
                        logger.warning("Role 'akowe_user' does not exist, skipping owner assignment")
                except Exception as e:
                    logger.warning(f"Could not set owner on users table: {str(e)}")
            # No ownership settings needed for SQLite

            # Create indexes
            if dialect == 'sqlite':
                conn.execute(text("CREATE UNIQUE INDEX ix_users_username ON users (username);"))
                conn.execute(text("CREATE UNIQUE INDEX ix_users_email ON users (email);"))
            else:
                conn.execute(text("CREATE UNIQUE INDEX ix_users_username ON public.users (username);"))
                conn.execute(text("CREATE UNIQUE INDEX ix_users_email ON public.users (email);"))

            # Create expense table
            logger.info("Creating expense table")

            if dialect == 'sqlite':
                conn.execute(text("""
                CREATE TABLE expense
                (
                    id                INTEGER PRIMARY KEY AUTOINCREMENT,
                    date              DATE           NOT NULL,
                    title             VARCHAR(255)   NOT NULL,
                    amount            NUMERIC(10, 2) NOT NULL,
                    category          VARCHAR(100)   NOT NULL,
                    payment_method    VARCHAR(50)    NOT NULL,
                    status            VARCHAR(20)    NOT NULL,
                    vendor            VARCHAR(255),
                    receipt_blob_name VARCHAR(255),
                    receipt_url       VARCHAR(1024),
                    created_at        TIMESTAMP,
                    updated_at        TIMESTAMP,
                    user_id           INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
                """))
            else:
                conn.execute(text("""
                CREATE TABLE public.expense
                (
                    id                SERIAL
                        PRIMARY KEY,
                    date              DATE           NOT NULL,
                    title             VARCHAR(255)   NOT NULL,
                    amount            NUMERIC(10, 2) NOT NULL,
                    category          VARCHAR(100)   NOT NULL,
                    payment_method    VARCHAR(50)    NOT NULL,
                    status            VARCHAR(20)    NOT NULL,
                    vendor            VARCHAR(255),
                    receipt_blob_name VARCHAR(255),
                    receipt_url       VARCHAR(1024),
                    created_at        TIMESTAMP,
                    updated_at        TIMESTAMP,
                    user_id           INTEGER
                        CONSTRAINT fk_expense_user
                            REFERENCES public.users
                );
                """))

            # Set owner if role exists
            try:
                if role_exists:
                    conn.execute(text("alter table public.expense owner to akowe_user;"))
            except Exception as e:
                logger.warning(f"Could not set owner on expense table: {str(e)}")

            # Create client table
            logger.info("Creating client table")

            if dialect == 'sqlite':
                conn.execute(text("""
                CREATE TABLE client
                (
                    id             INTEGER PRIMARY KEY AUTOINCREMENT,
                    name           VARCHAR(255) NOT NULL,
                    email          VARCHAR(255),
                    phone          VARCHAR(50),
                    address        TEXT,
                    contact_person VARCHAR(255),
                    notes          TEXT,
                    user_id        INTEGER     NOT NULL,
                    created_at     TIMESTAMP,
                    updated_at     TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );
                """))
            else:
                conn.execute(text("""
                CREATE TABLE public.client
                (
                    id             SERIAL PRIMARY KEY,
                    name           VARCHAR(255) NOT NULL,
                    email          VARCHAR(255),
                    phone          VARCHAR(50),
                    address        TEXT,
                    contact_person VARCHAR(255),
                    notes          TEXT,
                    user_id        INTEGER      NOT NULL REFERENCES public.users(id),
                    created_at     TIMESTAMP,
                    updated_at     TIMESTAMP
                );
                """))

            # Set owner if role exists
            try:
                if role_exists:
                    conn.execute(text("alter table public.client owner to akowe_user;"))
            except Exception as e:
                logger.warning(f"Could not set owner on client table: {str(e)}")

            # Create index
            if dialect == 'sqlite':
                conn.execute(text("CREATE UNIQUE INDEX ix_client_name ON client (name);"))
            else:
                conn.execute(text("CREATE UNIQUE INDEX ix_client_name ON public.client (name);"))

            # Create project table
            logger.info("Creating project table")
            conn.execute(text("""
            create table public.project
            (
                id          serial
                    primary key,
                name        varchar(255) not null,
                description text,
                status      varchar(50),
                hourly_rate numeric(10, 2),
                client_id   integer      not null
                    references public.client,
                user_id     integer      not null
                    references public.users,
                created_at  timestamp,
                updated_at  timestamp
            );
            """))

            # Set owner if role exists
            try:
                if role_exists:
                    conn.execute(text("alter table public.project owner to akowe_user;"))
            except Exception as e:
                logger.warning(f"Could not set owner on project table: {str(e)}")

            # Create index
            conn.execute(text("create index ix_project_name on public.project (name);"))

            # Create invoice table
            logger.info("Creating invoice table")
            conn.execute(text("""
            create table public.invoice
            (
                id                serial
                    primary key,
                invoice_number    varchar(50)    not null
                    unique,
                client_id         integer        not null
                    references public.client,
                company_name      varchar(255),
                issue_date        date           not null,
                due_date          date           not null,
                notes             text,
                subtotal          numeric(10, 2) not null,
                tax_rate          numeric(5, 2)  not null,
                tax_amount        numeric(10, 2) not null,
                total             numeric(10, 2) not null,
                status            varchar(20)    not null,
                sent_date         timestamp,
                paid_date         timestamp,
                payment_method    varchar(50),
                payment_reference varchar(100),
                user_id           integer        not null
                    references public.users,
                created_at        timestamp,
                updated_at        timestamp
            );
            """))

            # Set owner if role exists
            try:
                if role_exists:
                    conn.execute(text("alter table public.invoice owner to akowe_user;"))
            except Exception as e:
                logger.warning(f"Could not set owner on invoice table: {str(e)}")

            # Create income table
            logger.info("Creating income table")
            conn.execute(text("""
            create table public.income
            (
                id         serial
                    primary key,
                date       date           not null,
                amount     numeric(10, 2) not null,
                client     varchar(255)   not null,
                project    varchar(255)   not null,
                invoice    varchar(255),
                user_id    integer        not null
                    references public.users,
                created_at timestamp,
                updated_at timestamp,
                client_id  integer
                    references public.client,
                project_id integer
                    references public.project,
                invoice_id integer
                    references public.invoice
            );
            """))

            # Set owner if role exists
            try:
                if role_exists:
                    conn.execute(text("alter table public.income owner to akowe_user;"))
            except Exception as e:
                logger.warning(f"Could not set owner on income table: {str(e)}")

            # Create timesheet table
            logger.info("Creating timesheet table")
            conn.execute(text("""
            create table public.timesheet
            (
                id          serial
                    primary key,
                date        date           not null,
                client_id   integer        not null
                    references public.client,
                project_id  integer        not null
                    references public.project,
                description text           not null,
                hours       numeric(5, 2)  not null,
                hourly_rate numeric(10, 2) not null,
                status      varchar(20)    not null,
                invoice_id  integer
                    references public.invoice,
                user_id     integer        not null
                    references public.users,
                created_at  timestamp,
                updated_at  timestamp
            );
            """))

            # Set owner if role exists
            try:
                if role_exists:
                    conn.execute(text("alter table public.timesheet owner to akowe_user;"))
            except Exception as e:
                logger.warning(f"Could not set owner on timesheet table: {str(e)}")

            conn.commit()
            logger.info("Complete schema migration executed successfully")
            return

        except Exception as e:
            logger.error(f"Complete schema migration failed: {str(e)}")
            raise Exception(f"Complete schema migration failed: {str(e)}")


def run_home_office_migration():
    """Create the home_office table if it doesn't exist."""
    app = create_app()
    with app.app_context():
        logger.info("Starting home_office table migration")

        # Create connection
        conn = db.engine.connect()

        # Detect database dialect
        dialect = db.engine.dialect.name
        logger.info(f"Database dialect: {dialect}")

        try:
            # Check if the table exists
            table_exists = False

            try:
                if dialect == 'postgresql':
                    result = conn.execute(text(
                        "SELECT 1 FROM information_schema.tables "
                        + "WHERE table_schema = 'public' AND table_name = 'home_office';"
                    ))
                    table_exists = result.scalar() is not None
                else:
                    # For SQLite
                    result = conn.execute(text(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='home_office';"
                    ))
                    table_exists = result.scalar() is not None
            except Exception as e:
                logger.warning(f"Could not check if home_office table exists: {str(e)}")

            if table_exists:
                logger.info("home_office table already exists, skipping creation")
                return

            # Create the home_office table
            logger.info("Creating home_office table")

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

            # This code is no longer needed since we're generating dialect-specific SQL
            # Keeping it commented for reference
            # if dialect == 'sqlite':
            #     create_sql = create_sql.replace('SERIAL', 'INTEGER')
            #     create_sql = create_sql.replace('DEFAULT CURRENT_TIMESTAMP', 'DEFAULT (datetime(\'now\'))')

            conn.execute(text(create_sql))

            if dialect == 'postgresql':
                # Set owner for PostgreSQL if the role exists
                try:
                    # First check if the role exists
                    role_exists = conn.execute(text(
                        "SELECT 1 FROM pg_roles WHERE rolname = 'akowe_user';"
                    )).scalar() is not None

                    if role_exists:
                        conn.execute(text("ALTER TABLE public.home_office OWNER TO akowe_user;"))
                    else:
                        logger.warning("Role 'akowe_user' does not exist, skipping owner assignment")
                except Exception as e:
                    logger.warning(f"Could not set owner on home_office table: {str(e)}")

            conn.commit()
            logger.info("home_office table created successfully")
            return

        except Exception as e:
            logger.error(f"home_office table migration failed: {str(e)}")
            raise Exception(f"home_office table migration failed: {str(e)}")


if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
