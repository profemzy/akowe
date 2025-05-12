import os
from dotenv import load_dotenv
from akowe.akowe import create_app
from akowe.models import db
from akowe.models.user import User

def create_admin_user():
    """Create an admin user from environment variables."""
    load_dotenv()  # Load environment variables from .env file
    
    app = create_app()
    with app.app_context():
        # Check if admin user already exists
        admin_user = User.query.filter_by(username=os.environ.get('ADMIN_USERNAME', 'admin')).first()
        
        if admin_user:
            print(f"Admin user '{admin_user.username}' already exists.")
            return
        
        # Create a new admin user
        admin = User(
            username=os.environ.get('ADMIN_USERNAME', 'admin'),
            email=os.environ.get('ADMIN_EMAIL', 'admin@example.com'),
            first_name=os.environ.get('ADMIN_FIRST_NAME', 'Admin'),
            last_name=os.environ.get('ADMIN_LAST_NAME', 'User'),
            is_admin=True,
            is_active=True
        )
        admin.password = os.environ.get('ADMIN_PASSWORD', 'admin')
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"Admin user '{admin.username}' created successfully.")

if __name__ == '__main__':
    create_admin_user()