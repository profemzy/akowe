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
  
  # Handle migrations
  if [ ! -f "/app/migrations/env.py" ]; then
    echo "Initializing migrations from scratch..."
    rm -rf /app/migrations
    export FLASK_APP=app.py
    flask db init
    
    echo "Creating initial migration..."
    flask db migrate -m "Initial migration"
    
    echo "Applying migrations..."
    flask db upgrade
  else
    echo "Using existing migrations directory..."
    export FLASK_APP=app.py
    
    echo "Creating new migration if needed..."
    flask db migrate -m "Migration $(date +%Y%m%d_%H%M%S)"
    
    echo "Applying migrations..."
    flask db upgrade
  fi
  
  # Create admin user
  echo "Creating admin user if needed..."
  python create_docker_admin.py
  
  # Import data if files exist
  if [ -f "/app/data/income_export.csv" ]; then
    echo "Importing income data..."
    python -c "from akowe import create_app; from akowe.services.import_service import ImportService; app = create_app(); with app.app_context(): ImportService.import_income_csv('/app/data/income_export.csv')"
  fi
  
  if [ -f "/app/data/expense_export.csv" ]; then
    echo "Importing expense data..."
    python -c "from akowe import create_app; from akowe.services.import_service import ImportService; app = create_app(); with app.app_context(): ImportService.import_expense_csv('/app/data/expense_export.csv')"
  fi
  
  echo "Database setup complete!"
}

# Main execution
if [ "$1" = "gunicorn" ]; then
  wait_for_postgres
  initialize_db
  echo "Starting Akowe Financial Tracker..."
  exec gunicorn -b 0.0.0.0:5000 --access-logfile - --error-logfile - --workers 4 "app:app"
elif [ "$1" = "init" ]; then
  wait_for_postgres
  initialize_db
  echo "Initialization complete."
else
  exec "$@"
fi