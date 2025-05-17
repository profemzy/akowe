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

alter table public.users
    owner to akowe_user;

create unique index ix_users_username
    on public.users (username);

create unique index ix_users_email
    on public.users (email);

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

alter table public.expense
    owner to akowe_user;

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

alter table public.client
    owner to akowe_user;

create unique index ix_client_name
    on public.client (name);

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

alter table public.project
    owner to akowe_user;

create index ix_project_name
    on public.project (name);

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

alter table public.invoice
    owner to akowe_user;

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

alter table public.income
    owner to akowe_user;

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

alter table public.timesheet
    owner to akowe_user;

