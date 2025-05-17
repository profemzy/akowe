"""Test script to verify that the migration works correctly."""
import sys
import logging
from run_migrations import run_migrations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_migration')

def test_migration():
    """Run the migration and verify that it works correctly."""
    logger.info("Starting migration test")
    
    # Run the migration
    success = run_migrations()
    
    if success:
        logger.info("Migration completed successfully")
        return 0
    else:
        logger.error("Migration failed")
        return 1

if __name__ == "__main__":
    sys.exit(test_migration())