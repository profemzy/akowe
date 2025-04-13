# Akowe Financial Tracker

Akowe is a financial tracking application built to help with business expense and income management for tax preparation.

## Features

- Import income and expense data from CSV files
- Track and categorize business expenses
- Upload and manage receipts for expenses using Azure Blob Storage
- Record client income with project tracking
- Generate financial reports and summaries
- Prepare data for tax season
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

Akowe can be easily deployed to production using Docker and Docker Compose.

### Prerequisites

- Docker and Docker Compose installed
- CSV data files (optional) placed in the `data/` directory

### Configuration

1. Copy the example environment file: `cp .env.example .env`
2. Edit the `.env` file with your production settings (especially update the SECRET_KEY and passwords)

### Deployment Steps

1. Build and start the services:
   ```
   docker-compose up -d
   ```

2. The application will be available at http://localhost:5000

3. PgAdmin (database management) will be available at http://localhost:5050

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

## Kubernetes Deployment

For Kubernetes deployment, see the [k8s directory](./k8s/README.md).

## Receipt Upload

Akowe now supports uploading and managing receipts for expense records. See the [detailed documentation](./docs/receipts.md) for setup and usage.

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