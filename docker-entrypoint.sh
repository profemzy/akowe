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
  
  # Remove migrations directory completely
  rm -rf /app/migrations
  
  # Create tables directly without migrations
  python -c "
from akowe import create_app
from akowe.models import db
from akowe.models.income import Income
from akowe.models.expense import Expense
from akowe.models.user import User

app = create_app()
with app.app_context():
    db.create_all()
    print('Database tables created successfully!')
  "
  
  # Create admin user
  echo "Creating admin user..."
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
}

# Check if database is already set up
check_db() {
  python -c "
from akowe import create_app
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
  exec gunicorn -b 0.0.0.0:5000 --access-logfile - --error-logfile - --workers 4 "app:app"
elif [ "$1" = "init" ]; then
  wait_for_postgres
  initialize_db_fresh
  echo "Initialization complete."
else
  exec "$@"
fi