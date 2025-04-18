# Akowe Financial Tracker

Akowe is a financial tracking application built to help with business expense and income management for tax preparation.

## Features

- Import income and expense data from CSV files
- Track and categorize business expenses
- Upload and manage receipts for expenses using Azure Blob Storage
- Record client income with project tracking
- Time tracking with timesheet system
- Invoice generation from timesheet entries
- Generate financial reports and summaries
- Prepare data for tax season with Canadian tax support
- AI-powered tax category suggestions and optimization
- User authentication and authorization
- Admin portal for user management

## Development Setup

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Initialize the database:
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```
6. Create an admin user: `python create_admin.py`
7. Run the application: `flask run` or `python app.py`

## Using Make

The project includes a Makefile with common tasks:

```bash
make install  # Install dependencies
make setup    # Initialize the database
make run      # Run the application
make test     # Run tests
make lint     # Run linting (flake8)
make format   # Format code (black)
make check    # Run lint and tests
make clean    # Clean up build artifacts
```

## Testing

Run the test suite:

```bash
pytest
```

For coverage report:

```bash
pytest --cov=akowe
```

## Code Quality

We use the following tools to maintain code quality:

- **black** for code formatting
- **flake8** for linting
- **mypy** for type checking

Run all checks:

```bash
make check
```

## Production Deployment with Docker

Akowe can be easily deployed to production using Docker and Docker Compose with optimized multi-stage builds.

### Prerequisites

- Docker and Docker Compose V2 installed
- CSV data files (optional) placed in the `data/` directory

### Development Configuration

1. Copy the example environment file: `cp .env.example .env`
2. Edit the `.env` file with your settings (especially update the SECRET_KEY and passwords)

### Development Deployment

1. Build and start the services including PgAdmin:
   ```
   docker compose up -d
   ```

2. The application will be available at http://localhost:5000

3. PgAdmin (database management) will be available at http://localhost:5050

### Production Deployment

For production environments, use the production-specific configuration:

1. Create a production environment file:
   ```
   cp .env.production.example .env.production
   ```

2. Edit `.env.production` with secure passwords and configuration values

3. Build and deploy using the production compose file:
   ```
   docker compose -f docker-compose.prod.yml up -d
   ```

4. For a secure production setup, consider:
   - Using a reverse proxy (Nginx, Traefik) with HTTPS
   - Setting up monitoring and log aggregation
   - Configuring backups for database volumes
   - Using Docker Swarm or Kubernetes for orchestration

### Scaling in Production

The production docker-compose file supports horizontal scaling:

```bash
# Scale up web services to 4 instances
WEB_REPLICAS=4 docker compose -f docker-compose.prod.yml up -d
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| FLASK_APP | Flask application entry point | app.py |
| FLASK_ENV | Flask environment | production |
| SECRET_KEY | Flask secret key for session security | - |
| DB_USER | PostgreSQL username | akowe_user |
| DB_PASSWORD | PostgreSQL password | akowe_password |
| DB_HOST | PostgreSQL hostname | postgres |
| DB_PORT | PostgreSQL port | 5432 |
| DB_NAME | PostgreSQL database name | akowe |
| ADMIN_USERNAME | Initial admin username | admin |
| ADMIN_EMAIL | Initial admin email | admin@example.com |
| ADMIN_PASSWORD | Initial admin password | - |
| ADMIN_FIRST_NAME | Initial admin first name | Admin |
| ADMIN_LAST_NAME | Initial admin last name | User |
| AZURE_STORAGE_CONNECTION_STRING | Azure Blob Storage connection string | - |
| COMPANY_NAME | Your company name (used on invoices) | Akowe |
| DEFAULT_HOURLY_RATE | Default hourly rate for timesheet entries | 120.00 |

## Kubernetes Deployment

For Kubernetes deployment, see the [k8s directory](./k8s/README.md).

When deploying to Kubernetes, be sure to run the consolidated migration job before deploying the application to ensure the database schema is updated correctly. See the [Database Migrations Guide](k8s/DATABASE-MIGRATIONS.md) for detailed instructions. The migration job is defined in `k8s/migrations-job.yaml`.

## Receipt Upload

Akowe now supports uploading and managing receipts for expense records. See the [detailed documentation](./docs/receipts.md) for setup and usage.

## Timesheet System

Track billable hours and generate invoices with the timesheet system. See the [timesheet documentation](./docs/timesheet.md) for usage details.

## Invoice System

Create professional invoices from timesheet entries. See the [invoice documentation](./docs/invoice.md) for setup and workflow information.

## AI-Powered Tax Features

Akowe includes comprehensive AI-powered tax features to optimize your tax position:

### 1. Smart Tax Categorization

- **Smart Tax Category Recommendations**: Get intelligent suggestions for expense categories based on title and vendor information
- **Tax Implications Analysis**: View CRA tax category mapping, deduction rates, and special tax rules for each expense category
- **Expense Analysis Dashboard**: Access the AI Tax Analysis page to identify potential tax optimization opportunities
- **Missing Receipt Detection**: Automatically identify expenses over $100 missing receipts that could be problematic during audits
- **Tax Optimization Suggestions**: Get personalized recommendations to maximize deductions

Access these features:
- From the expense list page, click the "AI Tax Analysis" button in the top toolbar
- When creating or editing an expense, use the "Get AI Category Suggestions" button 
- Visit `/expense/analyze-expenses` directly to see the full analysis dashboard

### 2. AI Tax Planning & Prediction

- **Income & Expense Projections**: Get year-end projections based on current data
- **Tax Bracket Analysis**: See which federal tax bracket you're in and how close you are to the next one
- **Monthly Breakdown**: View month-by-month income and expense projections
- **Strategic Tax Planning**: Receive timely suggestions for tax optimization strategies
- **Effective Tax Rate Calculation**: Understand your real tax burden percentage

Access these features:
- From the tax dashboard, click the "AI Tax Planning" button (only available for current year)
- Visit `/tax/prediction` directly to see the full planning dashboard

## Mobile API

Akowe includes a comprehensive REST API that can be used to build mobile applications or integrate with other systems. See the [API documentation](./docs/api.md) for details.

## CSV Import Format

### Income CSV Format
```
date,amount,client,project,invoice
2025-03-21,9040.00,SearchLabs (RAVL),P2025001 - Interac Konek,Invoice #INV-202503-0002 - SearchLabs
```

### Expense CSV Format
```
date,title,amount,category,payment_method,status,vendor
2025-04-12,WD Red Plus 12TB NAS Hard Disk Drive,386.37,hardware,credit_card,pending,Newegg
```

## Backup and Restore

### Backup
```
docker exec -t akowe-postgres pg_dumpall -c -U akowe_user > backup/backup_$(date +%Y-%m-%d_%H-%M-%S).sql
```

### Restore
```
cat backup/your_backup_file.sql | docker exec -i akowe-postgres psql -U akowe_user -d akowe
```