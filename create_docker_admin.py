import os
import sys
from akowe import create_app
from akowe.models import db
from akowe.models.user import User

def create_admin_from_env():
    """Create admin user from environment variables."""
    app = create_app()
    
    with app.app_context():
        # Check if admin user already exists
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        if User.query.filter_by(username=admin_username).first():
            print(f"Admin user '{admin_username}' already exists.")
            return
        
        # Get admin details from environment
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        admin_first_name = os.environ.get('ADMIN_FIRST_NAME', 'Admin')
        admin_last_name = os.environ.get('ADMIN_LAST_NAME', 'User')
        
        # Validate admin password
        if not admin_password or len(admin_password) < 8:
            print("ERROR: Admin password not set or too short (min 8 characters).")
            print("Please set ADMIN_PASSWORD environment variable.")
            sys.exit(1)
        
        # Create the admin user
        admin = User(
            username=admin_username,
            email=admin_email,
            first_name=admin_first_name,
            last_name=admin_last_name,
            is_admin=True
        )
        admin.password = admin_password
        
        # Add to database
        db.session.add(admin)
        db.session.commit()
        
        print(f"Admin user '{admin_username}' created successfully.")

if __name__ == "__main__":
    create_admin_from_env()