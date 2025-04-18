-- Direct SQL migrations for Akowe
-- Use this file to run migrations directly against the database outside of Kubernetes

-- Migration 1: Add last_login column to users table
-- PostgreSQL version (production)

-- First run a simple version that checks tables before attempting to modify them
DO $$
DECLARE
    table_exists boolean;
BEGIN
    -- First, check if user table exists (without trying to modify it)
    SELECT EXISTS (
        SELECT FROM pg_tables 
        WHERE schemaname = 'public' AND tablename = 'user'
    ) INTO table_exists;
    
    -- If user table exists, add column
    IF table_exists THEN
        -- Add column to public.user table
        ALTER TABLE public."user" ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;
        RAISE NOTICE 'Added last_login column to public.user table';
    ELSE
        -- Check if users (plural) table exists
        SELECT EXISTS (
            SELECT FROM pg_tables 
            WHERE schemaname = 'public' AND tablename = 'users'
        ) INTO table_exists;
        
        IF table_exists THEN
            RAISE NOTICE 'Found users table instead of user';
            ALTER TABLE public.users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;
            RAISE NOTICE 'Added last_login column to public.users table';
        ELSE
            RAISE NOTICE 'Could not find user or users table';
        END IF;
    END IF;
END $$;

-- SQLite version (development) - uncomment if needed
-- ALTER TABLE users ADD COLUMN last_login TIMESTAMP;

-- Migration 2: Add user_id column to expense table
-- PostgreSQL version (production) - simplified based on error message
DO $$
DECLARE
    table_exists boolean;
BEGIN
    -- First, check if expense table exists (without trying to modify it)
    SELECT EXISTS (
        SELECT FROM pg_tables 
        WHERE schemaname = 'public' AND tablename = 'expense'
    ) INTO table_exists;
    
    -- If expense table exists, add column
    IF table_exists THEN
        -- Add column first (separate from constraint to avoid errors)
        ALTER TABLE public.expense ADD COLUMN IF NOT EXISTS user_id INTEGER;
        RAISE NOTICE 'Added user_id column to public.expense table';
        
        -- Check if user table exists before adding constraint
        SELECT EXISTS (
            SELECT FROM pg_tables 
            WHERE schemaname = 'public' AND tablename = 'user'
        ) INTO table_exists;
        
        IF table_exists THEN
            -- Add constraint with careful error handling
            BEGIN
                -- Try to add constraint (will fail if already exists)
                EXECUTE 'ALTER TABLE public.expense ADD CONSTRAINT fk_expense_user 
                         FOREIGN KEY (user_id) REFERENCES public."user"(id)';
                RAISE NOTICE 'Added foreign key constraint to public.expense referencing public.user';
            EXCEPTION 
                WHEN duplicate_object THEN
                    RAISE NOTICE 'Foreign key constraint already exists on public.expense';
                WHEN others THEN
                    RAISE NOTICE 'Could not add foreign key: %', SQLERRM;
            END;
        ELSE
            RAISE NOTICE 'User table not found as public.user, checking for users table';
            -- Try with users table
            SELECT EXISTS (
                SELECT FROM pg_tables 
                WHERE schemaname = 'public' AND tablename = 'users'
            ) INTO table_exists;
            
            IF table_exists THEN
                BEGIN
                    EXECUTE 'ALTER TABLE public.expense ADD CONSTRAINT fk_expense_user 
                             FOREIGN KEY (user_id) REFERENCES public.users(id)';
                    RAISE NOTICE 'Added foreign key constraint to public.expense referencing public.users';
                EXCEPTION 
                    WHEN duplicate_object THEN
                        RAISE NOTICE 'Foreign key constraint already exists on public.expense';
                    WHEN others THEN
                        RAISE NOTICE 'Could not add foreign key: %', SQLERRM;
                END;
            ELSE
                RAISE NOTICE 'Could not find user or users table';
            END IF;
        END IF;
    ELSE
        -- Check if expenses (plural) table exists
        SELECT EXISTS (
            SELECT FROM pg_tables 
            WHERE schemaname = 'public' AND tablename = 'expenses'
        ) INTO table_exists;
        
        IF table_exists THEN
            RAISE NOTICE 'Found expenses table instead of expense';
            -- Add column first
            ALTER TABLE public.expenses ADD COLUMN IF NOT EXISTS user_id INTEGER;
            RAISE NOTICE 'Added user_id column to public.expenses table';
            
            -- Check for user table
            SELECT EXISTS (
                SELECT FROM pg_tables 
                WHERE schemaname = 'public' AND tablename = 'user'
            ) INTO table_exists;
            
            IF table_exists THEN
                BEGIN
                    EXECUTE 'ALTER TABLE public.expenses ADD CONSTRAINT fk_expenses_user 
                             FOREIGN KEY (user_id) REFERENCES public."user"(id)';
                    RAISE NOTICE 'Added foreign key constraint to public.expenses referencing public.user';
                EXCEPTION 
                    WHEN duplicate_object THEN
                        RAISE NOTICE 'Foreign key constraint already exists on public.expenses';
                    WHEN others THEN
                        RAISE NOTICE 'Could not add foreign key: %', SQLERRM;
                END;
            ELSE
                -- Try with users table
                SELECT EXISTS (
                    SELECT FROM pg_tables 
                    WHERE schemaname = 'public' AND tablename = 'users'
                ) INTO table_exists;
                
                IF table_exists THEN
                    BEGIN
                        EXECUTE 'ALTER TABLE public.expenses ADD CONSTRAINT fk_expenses_user 
                                 FOREIGN KEY (user_id) REFERENCES public.users(id)';
                        RAISE NOTICE 'Added foreign key constraint to public.expenses referencing public.users';
                    EXCEPTION 
                        WHEN duplicate_object THEN
                            RAISE NOTICE 'Foreign key constraint already exists on public.expenses';
                        WHEN others THEN
                            RAISE NOTICE 'Could not add foreign key: %', SQLERRM;
                    END;
                ELSE
                    RAISE NOTICE 'Could not find user or users table';
                END IF;
            END IF;
        ELSE
            RAISE NOTICE 'Could not find expense or expenses table';
        END IF;
    END IF;
END $$;

-- SQLite version (development) - uncomment if needed
-- ALTER TABLE expenses ADD COLUMN user_id INTEGER REFERENCES users(id);

-- Verification queries - run these to check if migrations succeeded
-- For PostgreSQL:
-- SELECT column_name FROM information_schema.columns 
--   WHERE table_schema = 'public' AND table_name='user' AND column_name='last_login';
-- SELECT column_name FROM information_schema.columns 
--   WHERE table_schema = 'public' AND table_name='expense' AND column_name='user_id';

-- Alternative verification using pg_tables and pg_attribute (if information_schema not accessible):
-- SELECT attname FROM pg_attribute JOIN pg_class ON pg_attribute.attrelid = pg_class.oid
--   WHERE relname = 'user' AND attname = 'last_login';
-- SELECT attname FROM pg_attribute JOIN pg_class ON pg_attribute.attrelid = pg_class.oid
--   WHERE relname = 'expense' AND attname = 'user_id';

-- For SQLite:
-- PRAGMA table_info(users); -- Check for last_login column
-- PRAGMA table_info(expenses); -- Check for user_id column