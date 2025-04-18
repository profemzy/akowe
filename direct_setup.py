#!/usr/bin/env python3
"""
Direct database setup script that doesn't rely on Alembic.
This creates all tables directly using SQLAlchemy create_all().
"""

import os
import sys
from sqlalchemy import text

from akowe import create_app
from akowe.models import db
from akowe.models.income import Income
from akowe.models.user import User

def setup_db():
    """Set up the database directly with SQLAlchemy."""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        print("Creating all database tables...")
        db.create_all()
        print("✅ Tables created")
        
        # Check if we need to add user_id to income table
        print("Checking for user_id column in income table...")
        try:
            # Try to query incomes with user_id
            result = Income.query.filter(Income.user_id != None).first()
            print("✅ user_id column exists")
        except Exception as e:
            if "user_id" in str(e):
                print("❌ user_id column doesn't exist in income table")
                
                # Try to add the column with direct SQL
                print("Adding user_id column to income table...")
                try:
                    # Get session connection
                    connection = db.session.connection()
                    
                    # Add user_id column
                    connection.execute(text("ALTER TABLE income ADD COLUMN user_id INTEGER"))
                    print("✅ Added user_id column")
                    
                    # Get admin user id or first user
                    admin = User.query.filter_by(is_admin=True).first()
                    user_id = admin.id if admin else User.query.first().id
                    
                    # Update income records
                    connection.execute(
                        text(f"UPDATE income SET user_id = {user_id} WHERE user_id IS NULL")
                    )
                    print(f"✅ Updated income records with user_id = {user_id}")
                    
                    # Make user_id non-nullable
                    connection.execute(text("ALTER TABLE income ALTER COLUMN user_id SET NOT NULL"))
                    print("✅ Made user_id column non-nullable")
                    
                    # Add foreign key
                    connection.execute(
                        text("ALTER TABLE income ADD CONSTRAINT fk_income_user_id FOREIGN KEY (user_id) REFERENCES users(id)")
                    )
                    print("✅ Added foreign key constraint")
                    
                    # Commit changes
                    db.session.commit()
                    print("✅ Changes committed")
                except Exception as migration_error:
                    db.session.rollback()
                    print(f"❌ Error during migration: {str(migration_error)}")
        
        print("\n✅ Database setup complete!")
        print("To create an admin user, run: python create_admin.py")
        print("To start the application, run: python app.py")


if __name__ == "__main__":
    setup_db()