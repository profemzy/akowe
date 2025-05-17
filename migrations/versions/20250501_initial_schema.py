"""Initial schema migration

Revision ID: 20250501_initial_schema
Create Date: 2025-05-01
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

# revision identifiers
revision = "20250501_initial_schema"
down_revision = None  # This is the first migration, so no down_revision

def upgrade():
    # Execute the SQL from db-schema.sql
    conn = op.get_bind()
    
    # Drop existing tables if they exist
    conn.execute(text("DROP TABLE IF EXISTS timesheet CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS income CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS invoice CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS project CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS client CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS expense CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
    
    # Create users table
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

def downgrade():
    # Drop all tables in reverse order
    op.drop_table("timesheet")
    op.drop_table("income")
    op.drop_table("invoice")
    op.drop_table("project")
    op.drop_table("client")
    op.drop_table("expense")
    op.drop_table("users")