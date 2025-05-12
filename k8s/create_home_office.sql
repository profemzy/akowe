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
        
        -- Set owner if the role exists
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'akowe_user') THEN
                EXECUTE 'ALTER TABLE public.home_office OWNER TO akowe_user';
            END IF;
        EXCEPTION WHEN OTHERS THEN
            -- Ignore owner setting errors
            RAISE NOTICE 'Could not set owner: %', SQLERRM;
        END;
        
        RAISE NOTICE 'home_office table created successfully';
    ELSE
        RAISE NOTICE 'home_office table already exists, skipping creation';
    END IF;
END $$;