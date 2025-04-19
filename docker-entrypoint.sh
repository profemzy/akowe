#!/bin/bash
set -e

# Function to wait for PostgreSQL to be ready
wait_for_postgres() {
  echo "Waiting for PostgreSQL..."
  while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
    sleep 1
  done
  echo "PostgreSQL is ready!"
}

# Initialize the database from scratch
initialize_db_fresh() {
  echo "Initializing database from scratch..."

  # Use the Python script to initialize or update the database schema
  python init_db.py

  if [ $? -ne 0 ]; then
    echo "Database initialization failed!"
    exit 1
  fi

  # Import data if files exist
  if [ -f "/app/data/income_export.csv" ]; then
    echo "Importing income data..."
    python -c "
from akowe.akowe import create_app
from akowe.services.import_service import ImportService
from akowe.models.user import User

app = create_app()
with app.app_context():
    # Get admin user ID
    admin = User.query.filter_by(username='admin').first()
    if admin:
        ImportService.import_income_csv('/app/data/income_export.csv', admin.id)
    else:
        ImportService.import_income_csv('/app/data/income_export.csv')
"
  else
    echo "No income data file found to import"
  fi

  if [ -f "/app/data/expense_export.csv" ]; then
    echo "Importing expense data..."
    python -c "
from akowe.akowe import create_app
from akowe.services.import_service import ImportService
from akowe.models.user import User

app = create_app()
with app.app_context():
    # Get admin user ID
    admin = User.query.filter_by(username='admin').first()
    if admin:
        ImportService.import_expense_csv('/app/data/expense_export.csv', admin.id)
    else:
        ImportService.import_expense_csv('/app/data/expense_export.csv')
"
  else
    echo "No expense data file found to import"
  fi
}

# Check if database is already set up
check_db() {
  python -c "
from akowe.akowe import create_app
from akowe.models import db
from akowe.models.user import User

app = create_app()
with app.app_context():
    try:
        # Try to query users table
        user_count = User.query.count()
        print(f'Database already set up with {user_count} users')
        exit(0)  # Success - tables exist
    except Exception as e:
        print(f'Database not set up: {str(e)}')
        exit(1)  # Failure - tables don't exist
  "
}

# Main execution
if [ "$1" = "gunicorn" ]; then
  wait_for_postgres

  # Check if database needs to be initialized
  if check_db; then
    echo "Database already set up, skipping initialization"
  else
    echo "Database not set up, initializing..."
    initialize_db_fresh
  fi

  echo "Starting Akowe Financial Tracker..."
  # Calculate optimal number of workers based on CPU cores
  WORKERS=${GUNICORN_WORKERS:-$(( 2 * $(nproc) + 1 ))}

  # Use environment variables if provided
  BIND=${GUNICORN_BIND:-0.0.0.0:5000}
  TIMEOUT=${GUNICORN_TIMEOUT:-120}

  echo "Starting Gunicorn with $WORKERS workers on $BIND..."
  exec gunicorn -b $BIND --access-logfile - --error-logfile - --workers $WORKERS --timeout $TIMEOUT "app:app"
elif [ "$1" = "init" ]; then
  wait_for_postgres
  initialize_db_fresh
  echo "Initialization complete."
elif [ "$1" = "seed" ]; then
  wait_for_postgres

  # Check if database is set up
  if check_db; then
    echo "Running database seed script..."
    python tools/seed_db.py
    if [ $? -eq 0 ]; then
      echo "Database seeding completed successfully!"
    else
      echo "Database seeding failed!"
      exit 1
    fi
  else
    echo "Database not set up. Please run 'init' command first."
    exit 1
  fi
else
  exec "$@"
fi
