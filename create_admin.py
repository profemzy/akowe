from getpass import getpass

from akowe import create_app
from akowe.models import db
from akowe.models.user import User


def create_admin_user():
    """Create the initial admin user."""
    app = create_app()

    with app.app_context():
        # Check if any user exists
        if User.query.count() > 0:
            print("Users already exist in the database.")
            print("If you need to create another admin user, use the web interface.")
            return

        print("Creating initial admin user...")
        username = input("Username (default: admin): ") or "admin"
        email = input("Email: ")
        first_name = input("First name: ")
        last_name = input("Last name: ")

        # Get password securely
        while True:
            password = getpass("Password (min 8 characters): ")
            if len(password) >= 8:
                confirm_password = getpass("Confirm password: ")
                if password == confirm_password:
                    break
                else:
                    print("Passwords do not match. Try again.")
            else:
                print("Password must be at least 8 characters long.")

        # Create the admin user
        admin = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_admin=True,
        )
        admin.password = password

        # Add to database
        db.session.add(admin)
        db.session.commit()

        print(f"\nAdmin user '{username}' created successfully!")
        print("You can now log in to the application.")


if __name__ == "__main__":
    create_admin_user()
