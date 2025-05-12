#!/usr/bin/env bash
# fix_migration_sqlite.sh - Script to fix SQLite CASCADE issue in migrations
#
# This script updates run_migrations.py to add SQLite compatibility for CASCADE clauses
# and commits the changes before deployment

set -e  # Exit immediately if a command exits with a non-zero status

# Colors for prettier output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Fixing SQLite compatibility in migration script...${NC}"

# Check if the file exists
if [ ! -f "run_migrations.py" ]; then
  echo "Error: run_migrations.py not found. Are you in the project root directory?"
  exit 1
fi

# Add SQLite compatibility fix
sed -i.bak '
/logger.info("Dropping existing tables if they exist")/,/conn.execute(text("DROP TABLE IF EXISTS users CASCADE;"))/ c\
            # Drop existing tables if they exist\
            logger.info("Dropping existing tables if they exist")\
            \
            # Handle different SQL syntax based on database dialect\
            if dialect == '\''sqlite'\'':\
                # SQLite doesn'\''t support CASCADE, so we need to handle foreign keys differently\
                # Temporarily disable foreign key constraints\
                conn.execute(text("PRAGMA foreign_keys = OFF;"))\
                \
                # Drop tables without CASCADE\
                conn.execute(text("DROP TABLE IF EXISTS timesheet;"))\
                conn.execute(text("DROP TABLE IF EXISTS income;"))\
                conn.execute(text("DROP TABLE IF EXISTS invoice;"))\
                conn.execute(text("DROP TABLE IF EXISTS project;"))\
                conn.execute(text("DROP TABLE IF EXISTS client;"))\
                conn.execute(text("DROP TABLE IF EXISTS expense;"))\
                conn.execute(text("DROP TABLE IF EXISTS users;"))\
                \
                # Re-enable foreign key constraints\
                conn.execute(text("PRAGMA foreign_keys = ON;"))\
            else:\
                # PostgreSQL and others support CASCADE\
                conn.execute(text("DROP TABLE IF EXISTS timesheet CASCADE;"))\
                conn.execute(text("DROP TABLE IF EXISTS income CASCADE;"))\
                conn.execute(text("DROP TABLE IF EXISTS invoice CASCADE;"))\
                conn.execute(text("DROP TABLE IF EXISTS project CASCADE;"))\
                conn.execute(text("DROP TABLE IF EXISTS client CASCADE;"))\
                conn.execute(text("DROP TABLE IF EXISTS expense CASCADE;"))\
                conn.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
' run_migrations.py

# Check if the changes were applied successfully
if grep -q "SQLite doesn't support CASCADE" run_migrations.py; then
  echo -e "${GREEN}✅ Successfully updated run_migrations.py with SQLite compatibility fixes${NC}"
else
  echo "Error: Failed to update run_migrations.py"
  # Restore from backup
  mv run_migrations.py.bak run_migrations.py
  exit 1
fi

# Clean up backup
rm -f run_migrations.py.bak

echo -e "${GREEN}Migration script has been updated successfully!${NC}"
echo "You can now proceed with deployment and migrations will work correctly on both PostgreSQL and SQLite."
echo ""
echo "Next steps:"
echo "1. Commit the changes to your repository"
echo "2. Run deployment script: ./deploy_to_k8s.sh"
echo "3. Run migrations: kubectl apply -f k8s/migrations-job.yaml"