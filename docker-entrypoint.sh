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

# Initialize the database
initialize_db() {
  echo "Setting up the database..."
  
  # Run migrations
  flask db init || true
  flask db migrate -m "Initial migration"
  flask db upgrade
  
  # Create admin user
  python create_docker_admin.py
  
  # Import data if files exist
  if [ -f "/app/data/income_export.csv" ]; then
    echo "Importing income data..."
    python -c "from akowe.services.import_service import ImportService; ImportService.import_income_csv('/app/data/income_export.csv')"
  fi
  
  if [ -f "/app/data/expense_export.csv" ]; then
    echo "Importing expense data..."
    python -c "from akowe.services.import_service import ImportService; ImportService.import_expense_csv('/app/data/expense_export.csv')"
  fi
  
  echo "Database setup complete!"
}

# Main execution
if [ "$1" = "gunicorn" ]; then
  wait_for_postgres
  initialize_db
  echo "Starting Akowe Financial Tracker..."
  exec gunicorn -b 0.0.0.0:5000 --access-logfile - --error-logfile - "app:app"
elif [ "$1" = "init" ]; then
  wait_for_postgres
  initialize_db
  echo "Initialization complete."
else
  exec "$@"
fi