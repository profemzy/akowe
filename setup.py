import os
import shutil
from flask_migrate import upgrade
from akowe import create_app, db
from akowe.models.income import Income
from akowe.models.expense import Expense
from akowe.services.import_service import ImportService

def setup_db():
    """Set up the database and import initial data."""
    app = create_app()
    
    with app.app_context():
        # Create the database tables
        db.create_all()
        
        # Try to import initial data if CSV files exist
        try:
            if os.path.exists('income_export.csv'):
                ImportService.import_income_csv('income_export.csv')
                print("✅ Imported income data")
            
            if os.path.exists('expense_export.csv'):
                ImportService.import_expense_csv('expense_export.csv')
                print("✅ Imported expense data")
            
            print("\n✅ Database setup complete!")
            print("To start the application, run: python app.py")
        except Exception as e:
            print(f"❌ Error importing data: {str(e)}")
            raise

if __name__ == '__main__':
    setup_db()