import os

from flask_migrate import init, migrate, upgrade

from akowe import create_app
from akowe.services.import_service import ImportService


def setup_db():
    """Set up the database and import initial data."""
    app = create_app()

    with app.app_context():
        # Initialize migrations directory if it doesn't exist
        if not os.path.exists("migrations"):
            print("Initializing database migrations...")
            init()

        # Create a migration for current models
        print("Creating migration for current models...")
        migrate(message="Initial migration")

        # Apply migrations
        print("Applying migrations...")
        upgrade()

        # Try to import initial data if CSV files exist
        try:
            if os.path.exists("income_export.csv"):
                ImportService.import_income_csv("income_export.csv")
                print("✅ Imported income data")

            if os.path.exists("expense_export.csv"):
                ImportService.import_expense_csv("expense_export.csv")
                print("✅ Imported expense data")

            print("\n✅ Database setup complete!")
            print("To create an admin user, run: python create_admin.py")
            print("To start the application, run: python app.py")
        except Exception as e:
            print(f"❌ Error importing data: {str(e)}")
            raise


if __name__ == "__main__":
    setup_db()
