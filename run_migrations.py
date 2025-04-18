"""Consolidated migration script for Akowe.

This script runs all required database migrations in the proper sequence.
"""
import logging
import sys

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
    migrations = [
        # Migration to apply the complete schema from db-schema.sql
        {
            "name": "Apply complete schema from db-schema.sql",
            "function": run_complete_schema_migration
        }
    ]

    # Keep track of successful migrations
    success_count = 0

    # Run each migration
    for i, migration in enumerate(migrations):
        logger.info(f"Running migration {i+1}/{len(migrations)}: {migration['name']}")
        try:
            migration["function"]()
            success_count += 1
            logger.info(f"Migration {i+1}/{len(migrations)} completed successfully")
        except Exception as e:
            logger.error(f"Migration {i+1}/{len(migrations)} failed: {str(e)}")
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
            # Drop existing tables if they exist
            logger.info("Dropping existing tables if they exist")
            conn.execute(text("DROP TABLE IF EXISTS timesheet CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS income CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS invoice CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS project CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS client CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS expense CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS users CASCADE;"))

            # Create users table
            logger.info("Creating users table")
            conn.execute(text("""
            create table public.users
            (
                id            serial
                    primary key,
                username      varchar(64)  not null,
                email         varchar(120) not null,
                password_hash varchar(256) not null,
                first_name    varchar(64),
                last_name     varchar(64),
                hourly_rate   numeric(10, 2),
                is_admin      boolean,
                is_active     boolean,
                created_at    timestamp,
                updated_at    timestamp,
                last_login    timestamp
            );
            """))

            # Set owner
            conn.execute(text("alter table public.users owner to akowe_user;"))

            # Create indexes
            conn.execute(text("create unique index ix_users_username on public.users (username);"))
            conn.execute(text("create unique index ix_users_email on public.users (email);"))

            # Create expense table
            logger.info("Creating expense table")
            conn.execute(text("""
            create table public.expense
            (
                id                serial
                    primary key,
                date              date           not null,
                title             varchar(255)   not null,
                amount            numeric(10, 2) not null,
                category          varchar(100)   not null,
                payment_method    varchar(50)    not null,
                status            varchar(20)    not null,
                vendor            varchar(255),
                receipt_blob_name varchar(255),
                receipt_url       varchar(1024),
                created_at        timestamp,
                updated_at        timestamp,
                user_id           integer
                    constraint fk_expense_user
                        references public.users
            );
            """))

            # Set owner
            conn.execute(text("alter table public.expense owner to akowe_user;"))

            # Create client table
            logger.info("Creating client table")
            conn.execute(text("""
            create table public.client
            (
                id             serial
                    primary key,
                name           varchar(255) not null,
                email          varchar(255),
                phone          varchar(50),
                address        text,
                contact_person varchar(255),
                notes          text,
                user_id        integer      not null
                    references public.users,
                created_at     timestamp,
                updated_at     timestamp
            );
            """))

            # Set owner
            conn.execute(text("alter table public.client owner to akowe_user;"))

            # Create index
            conn.execute(text("create unique index ix_client_name on public.client (name);"))

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

            # Set owner
            conn.execute(text("alter table public.project owner to akowe_user;"))

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

            # Set owner
            conn.execute(text("alter table public.invoice owner to akowe_user;"))

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

            # Set owner
            conn.execute(text("alter table public.income owner to akowe_user;"))

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

            # Set owner
            conn.execute(text("alter table public.timesheet owner to akowe_user;"))

            conn.commit()
            logger.info("Complete schema migration executed successfully")
            return

        except Exception as e:
            logger.error(f"Complete schema migration failed: {str(e)}")
            raise Exception(f"Complete schema migration failed: {str(e)}")


if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
