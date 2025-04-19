"""Initialize or update the database schema."""

import os
import sys
from decimal import Decimal
from dotenv import load_dotenv

from flask import Flask
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError

from akowe.models import db
from akowe.models.user import User

# Load environment variables from .env file
load_dotenv()


def init_db():
    """Initialize the database schema."""
    # Create a Flask app with database configuration
    app = Flask(__name__)

    # Get database configuration from environment
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")
    db_host = os.environ.get("DB_HOST")
    db_port = os.environ.get("DB_PORT")
    db_name = os.environ.get("DB_NAME")

    # Configure database
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize SQLAlchemy with the Flask app
    db.init_app(app)

    with app.app_context():
        try:
            # Get engine and inspector
            engine = db.engine
            inspector = inspect(engine)

            # Check if the users table exists
            if "users" in inspector.get_table_names():
                # Check if hourly_rate column exists
                columns = [column["name"] for column in inspector.get_columns("users")]
                if "hourly_rate" not in columns:
                    print("Adding hourly_rate column to users table...")
                    try:
                        # Try to add the hourly_rate column
                        with engine.begin() as conn:
                            conn.execute(
                                text(
                                    "ALTER TABLE users ADD COLUMN hourly_rate NUMERIC(10, 2) DEFAULT 0.0"
                                )
                            )
                    except (SQLAlchemyError, ProgrammingError) as e:
                        print(f"Error adding hourly_rate column: {str(e)}")
                        print("Will continue and let create_all handle it...")

            # Create all tables that don't exist yet
            db.create_all()
            print("Database schema created/updated successfully!")
            return True

        except SQLAlchemyError as e:
            print(f"Database error: {str(e)}")
            return False


def create_admin():
    """Create admin user from environment variables."""
    # Create a Flask app with database configuration
    app = Flask(__name__)

    # Get database configuration from environment
    db_user = os.environ.get("DB_USER")
    db_password = os.environ.get("DB_PASSWORD")
    db_host = os.environ.get("DB_HOST")
    db_port = os.environ.get("DB_PORT")
    db_name = os.environ.get("DB_NAME")

    # Configure database
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize SQLAlchemy with the Flask app
    db.init_app(app)

    with app.app_context():
        try:
            # Check if admin user already exists
            admin_username = os.environ.get("ADMIN_USERNAME", "admin")
            if User.query.filter_by(username=admin_username).first():
                print(f"Admin user '{admin_username}' already exists.")
                return True

            # Get admin details from environment
            admin_email = os.environ.get("ADMIN_EMAIL")
            admin_password = os.environ.get("ADMIN_PASSWORD")
            admin_first_name = os.environ.get("ADMIN_FIRST_NAME")
            admin_last_name = os.environ.get("ADMIN_LAST_NAME")

            # Get hourly rate from environment or use default
            default_hourly_rate = os.environ.get("DEFAULT_HOURLY_RATE", "0.00")

            # Validate admin password
            if not admin_password or len(admin_password) < 8:
                print("ERROR: Admin password not set or too short (min 8 characters).")
                print("Please set ADMIN_PASSWORD environment variable.")
                return False

            # Create admin user
            admin = User(
                username=admin_username,
                email=admin_email,
                first_name=admin_first_name,
                last_name=admin_last_name,
                hourly_rate=Decimal(default_hourly_rate),
                is_admin=True,
            )
            admin.password = admin_password

            # Add to database
            db.session.add(admin)
            db.session.commit()

            print(f"Admin user '{admin_username}' created successfully.")
            return True

        except SQLAlchemyError as e:
            print(f"Database error creating admin: {str(e)}")
            return False


if __name__ == "__main__":
    # Initialize the database schema
    if not init_db():
        sys.exit(1)

    # Create admin user
    if not create_admin():
        sys.exit(1)

    sys.exit(0)
