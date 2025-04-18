"""Consolidated migration script for Akowe.

This script runs all required database migrations in the proper sequence.
"""
import logging
import importlib
import sys
import os
from sqlalchemy import text, inspect
from akowe import create_app
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
        # Migration to add last_login column to users table
        {
            "name": "Add last_login column to users table",
            "function": run_last_login_migration
        },
        # Migration to add user_id column to expense table
        {
            "name": "Add user_id column to expense table",
            "function": run_expense_user_id_migration
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
                        "SELECT table_name FROM information_schema.tables " +
                        "WHERE table_schema = 'public' AND table_name IN ('users', 'user');"
                    ))
                    tables = [row[0] for row in result]
                    logger.info(f"Found user tables in schema: {tables}")
                    
                # Determine correct user table name
                user_table = 'user' if 'user' in tables else 'users'
                
            except Exception as e:
                logger.warning(f"Table detection failed: {str(e)}")
                logger.info("Falling back to default user table name")
                user_table = 'users'  # Default for SQLite/others
        
        logger.info(f"Using user table name: {user_table}")
        
        # Add the last_login column with appropriate SQL for the dialect
        try:
            if dialect == 'postgresql':
                # PostgreSQL-specific approach with schema handling
                sql = f"""
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
                sql = f"""
                ALTER TABLE {user_table} ADD COLUMN last_login TIMESTAMP;
                """
                
            logger.info(f"Executing SQL: {sql}")
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
                            f"SELECT column_name FROM information_schema.columns " +
                            f"WHERE table_schema = 'public' AND table_name='{table_name}' " +
                            f"AND column_name='last_login';"
                        ))
                        if result.rowcount > 0:
                            logger.info(f"Migration verified via information_schema: last_login column found in {table_name}")
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
                                    f'SELECT last_login FROM public."{table_name}" LIMIT 0;'
                                ))
                                logger.info(f"Migration verified via direct query: last_login column found in {table_name}")
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
                    logger.info(f"Migration verified: last_login column found in {user_table}")
                    column_added = True
                except Exception as e:
                    logger.warning(f"Column verification failed: {str(e)}")
                    # Try the other table as fallback
                    other_table = 'users' if user_table == 'user' else 'user'
                    try:
                        conn.execute(text(f'SELECT last_login FROM {other_table} LIMIT 0;'))
                        logger.info(f"Migration verified: last_login column found in {other_table}")
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

def run_expense_user_id_migration():
    """Apply the migration to add user_id column to expense table."""
    app = create_app()
    with app.app_context():
        logger.info("Starting migration to add user_id column to expense table")
        
        # Create connection
        conn = db.engine.connect()
        
        # Detect database dialect
        dialect = db.engine.dialect.name
        logger.info(f"Database dialect: {dialect}")
        
        # Initialize variables
        expense_table = None
        user_table = None
        
        # Approach based on database dialect
        if dialect == 'postgresql':
            logger.info("Using PostgreSQL-specific approach")
            
            # Try to detect expense and user tables in PostgreSQL
            try:
                # Method 1: Check using pg_tables
                try:
                    result = conn.execute(text(
                        "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('expense', 'expenses');"
                    ))
                    tables = [row[0] for row in result]
                    if tables:
                        expense_table = tables[0]
                        logger.info(f"Found expense table using pg_tables: {expense_table}")
                except Exception as e:
                    logger.warning(f"pg_tables check for expense failed: {str(e)}")
                
                try:
                    result = conn.execute(text(
                        "SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('user', 'users');"
                    ))
                    tables = [row[0] for row in result]
                    if tables:
                        user_table = tables[0]
                        logger.info(f"Found user table using pg_tables: {user_table}")
                except Exception as e:
                    logger.warning(f"pg_tables check for user failed: {str(e)}")
                    
                # Method 2: Direct table query if pg_tables failed
                if not expense_table:
                    try:
                        logger.info("Attempting direct table operations for 'expense'")
                        conn.execute(text("SELECT 1 FROM public.expense LIMIT 1;"))
                        expense_table = 'expense'
                        logger.info("Found 'expense' table via direct query")
                    except Exception:
                        try:
                            logger.info("Attempting direct table operations for 'expenses'")
                            conn.execute(text("SELECT 1 FROM public.expenses LIMIT 1;"))
                            expense_table = 'expenses'
                            logger.info("Found 'expenses' table via direct query")
                        except Exception as e:
                            logger.warning(f"Direct expense table query failed: {str(e)}")
                            
                if not user_table:
                    try:
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
                            logger.warning(f"Direct user table query failed: {str(e)}")
                
                # Apply fallbacks if detection failed
                if not expense_table:
                    logger.warning("Expense table detection failed, defaulting to 'expense'")
                    expense_table = 'expense'  # Default to 'expense' in PostgreSQL
                
                if not user_table:
                    logger.warning("User table detection failed, defaulting to 'user'")
                    user_table = 'user'  # Default to 'user' in PostgreSQL
                
            except Exception as e:
                logger.error(f"PostgreSQL table detection failed: {str(e)}")
                logger.info("Falling back to default table names")
                expense_table = 'expense'  # Default for PostgreSQL
                user_table = 'user'  # Default for PostgreSQL
                
        else:
            # For SQLite and other databases
            logger.info("Using standard approach for non-PostgreSQL database")
            try:
                # For SQLite, information_schema doesn't exist, try direct table checks
                if dialect == 'sqlite':
                    # Check expense tables
                    expense_tables = []
                    try:
                        conn.execute(text("SELECT 1 FROM expense LIMIT 1;"))
                        expense_tables.append('expense')
                    except Exception:
                        pass
                        
                    try:
                        conn.execute(text("SELECT 1 FROM expenses LIMIT 1;"))
                        expense_tables.append('expenses')
                    except Exception:
                        pass
                        
                    # Check user tables
                    user_tables = []
                    try:
                        conn.execute(text("SELECT 1 FROM user LIMIT 1;"))
                        user_tables.append('user')
                    except Exception:
                        pass
                        
                    try:
                        conn.execute(text("SELECT 1 FROM users LIMIT 1;"))
                        user_tables.append('users')
                    except Exception:
                        pass
                        
                    logger.info(f"Found expense tables via direct check: {expense_tables}")
                    logger.info(f"Found user tables via direct check: {user_tables}")
                    
                    # Determine table names
                    expense_table = expense_tables[0] if expense_tables else 'expenses'
                    user_table = user_tables[0] if user_tables else 'users'
                    
                else:
                    # For other databases, try information_schema
                    try:
                        expense_result = conn.execute(text(
                            "SELECT table_name FROM information_schema.tables " +
                            "WHERE table_schema = 'public' AND table_name IN ('expense', 'expenses');"
                        ))
                        
                        user_result = conn.execute(text(
                            "SELECT table_name FROM information_schema.tables " +
                            "WHERE table_schema = 'public' AND table_name IN ('user', 'users');"
                        ))
                        
                        expense_tables = [row[0] for row in expense_result]
                        user_tables = [row[0] for row in user_result]
                        
                        logger.info(f"Found expense tables in schema: {expense_tables}")
                        logger.info(f"Found user tables in schema: {user_tables}")
                        
                        # Determine correct table names
                        expense_table = 'expense' if 'expense' in expense_tables else 'expenses'
                        user_table = 'user' if 'user' in user_tables else 'users'
                    except Exception as e:
                        logger.warning(f"Information schema query failed: {str(e)}")
                        # Fallback to defaults
                        expense_table = 'expenses'
                        user_table = 'users'
                    
            except Exception as e:
                logger.warning(f"Table detection failed: {str(e)}")
                logger.info("Falling back to default table names")
                expense_table = 'expenses'  # Default for SQLite
                user_table = 'users'  # Default for SQLite
        
        logger.info(f"Using expense table name: {expense_table}")
        logger.info(f"Using user table name: {user_table}")
        
        # Add the user_id column with appropriate SQL for the dialect
        try:
            if dialect == 'postgresql':
                # PostgreSQL-specific approach with schema handling and robust error handling
                sql = f"""
                DO $$
                BEGIN
                    -- Try to add column to expense table with schema qualification
                    BEGIN
                        ALTER TABLE public.expense ADD COLUMN IF NOT EXISTS user_id INTEGER;
                    EXCEPTION WHEN undefined_table THEN
                        -- Try without schema qualification
                        BEGIN
                            ALTER TABLE expense ADD COLUMN IF NOT EXISTS user_id INTEGER;
                        EXCEPTION WHEN undefined_table THEN
                            -- Try other table name as last resort
                            ALTER TABLE expenses 
                            ADD COLUMN IF NOT EXISTS user_id INTEGER;
                        END;
                    END;
                    
                    -- Try to add the foreign key constraint with schema qualification
                    BEGIN
                        ALTER TABLE public.expense DROP CONSTRAINT IF EXISTS fk_expense_user;
                        ALTER TABLE public.expense ADD CONSTRAINT fk_expense_user 
                        FOREIGN KEY (user_id) REFERENCES public."user"(id);
                    EXCEPTION WHEN undefined_table OR undefined_column THEN
                        -- Try without schema qualification
                        BEGIN
                            ALTER TABLE expense DROP CONSTRAINT IF EXISTS fk_expense_user;
                            ALTER TABLE expense ADD CONSTRAINT fk_expense_user 
                            FOREIGN KEY (user_id) REFERENCES "user"(id);
                        EXCEPTION WHEN undefined_table OR undefined_column THEN
                            -- Try other table names as last resort
                            ALTER TABLE expenses 
                            DROP CONSTRAINT IF EXISTS fk_expense_user;
                            ALTER TABLE expenses 
                            ADD CONSTRAINT fk_expense_user 
                            FOREIGN KEY (user_id) REFERENCES users(id);
                        END;
                    END;
                END $$;
                """
            else:
                # Generic SQL for SQLite and others
                # Note: SQLite has limited ALTER TABLE support
                sql = f"""
                ALTER TABLE {expense_table} ADD COLUMN user_id INTEGER REFERENCES {user_table}(id);
                """
                
            logger.info(f"Executing SQL: {sql}")
            conn.execute(text(sql))
            conn.commit()
            logger.info("SQL executed successfully")
            
        except Exception as e:
            logger.error(f"Failed to add user_id column: {str(e)}")
            # Don't raise yet, try to verify if it worked despite errors
        
        # Verify the column was added using the most reliable method for each dialect
        column_added = False
        
        try:
            if dialect == 'postgresql':
                # For PostgreSQL, try different verification methods
                try:
                    # Method 1: Check using information_schema if available
                    for table_name in ['expense', 'expenses']:
                        result = conn.execute(text(
                            f"SELECT column_name FROM information_schema.columns " +
                            f"WHERE table_schema = 'public' AND table_name='{table_name}' " +
                            f"AND column_name='user_id';"
                        ))
                        if result.rowcount > 0:
                            logger.info(f"Migration verified via information_schema: user_id column found in {table_name}")
                            column_added = True
                            break
                except Exception:
                    pass
                    
                # Method 2: Direct query if information_schema approach failed
                if not column_added:
                    try:
                        for table_name in ['expense', 'expenses']:
                            try:
                                conn.execute(text(
                                    f'SELECT user_id FROM public."{table_name}" LIMIT 0;'
                                ))
                                logger.info(f"Migration verified via direct query: user_id column found in {table_name}")
                                column_added = True
                                break
                            except Exception:
                                continue
                    except Exception as e:
                        logger.warning(f"Direct column verification failed: {str(e)}")
            else:
                # For SQLite and others, try direct table query
                try:
                    conn.execute(text(f'SELECT user_id FROM {expense_table} LIMIT 0;'))
                    logger.info(f"Migration verified: user_id column found in {expense_table}")
                    column_added = True
                except Exception as e:
                    logger.warning(f"Column verification failed: {str(e)}")
                    # Try the other table as fallback
                    other_table = 'expenses' if expense_table == 'expense' else 'expense'
                    try:
                        conn.execute(text(f'SELECT user_id FROM {other_table} LIMIT 0;'))
                        logger.info(f"Migration verified: user_id column found in {other_table}")
                        column_added = True
                    except Exception:
                        pass
                        
        except Exception as e:
            logger.error(f"Column verification failed: {str(e)}")
            
        # Final verification result
        if column_added:
            logger.info("Migration successful: user_id column was added to expense table")
            return
        else:
            logger.error("Migration failed: user_id column not found after migration")
            raise Exception("Migration verification failed")
    
if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)  # Exit with appropriate code for CI/CD systems