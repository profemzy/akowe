#!/usr/bin/env python3
"""Direct migration script for creating the home_office table in PostgreSQL."""

import os
import sys
import psycopg2
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('direct_migration')

def run_migration():
    """Create the home_office table directly in PostgreSQL."""
    # Get database connection info from environment variables
    db_host = os.environ.get('DB_HOST')
    db_port = os.environ.get('DB_PORT')
    db_name = os.environ.get('DB_NAME')
    db_user = os.environ.get('DB_USER')
    db_password = os.environ.get('DB_PASSWORD')

    logger.info(f"Connecting to database {db_name} on {db_host}:{db_port} as {db_user}")
    
    # Connect to the database
    try:
        conn_string = f'host={db_host} port={db_port} dbname={db_name} user={db_user} password={db_password}'
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if table exists
        logger.info("Checking if home_office table exists")
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'home_office'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            logger.info('home_office table already exists, skipping creation')
        else:
            logger.info('Creating home_office table directly')
            cursor.execute("""
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
            """)
            
            # Try to set owner if role exists
            try:
                # Check if role exists
                cursor.execute("""
                    SELECT 1 FROM pg_roles WHERE rolname = 'akowe_user';
                """)
                role_exists = cursor.fetchone() is not None
                
                if role_exists:
                    cursor.execute("""
                        ALTER TABLE public.home_office OWNER TO akowe_user;
                    """)
                    logger.info('Set table owner to akowe_user')
                else:
                    logger.info('Role akowe_user does not exist, skipping owner assignment')
            except Exception as e:
                logger.warning(f'Could not set owner: {str(e)}')
            
            logger.info('home_office table created successfully')
        
        conn.close()
        logger.info('Migration completed successfully')
        return True
    except Exception as e:
        logger.error(f'Migration failed: {str(e)}')
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)