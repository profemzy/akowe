"""Script to generate migration for home_office model."""

import os
import sys
from flask import Flask
from flask_migrate import Migrate

# Add the project directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Initialize Flask application
app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY="dev",
    SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///akowe.db"),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

# Initialize SQLAlchemy
from akowe.models import db
db.init_app(app)

# Import models to ensure they're registered with SQLAlchemy
from akowe.models.user import User
from akowe.models.income import Income
from akowe.models.expense import Expense
from akowe.models.invoice import Invoice
from akowe.models.client import Client
from akowe.models.project import Project
from akowe.models.timesheet import Timesheet
from akowe.models.home_office import HomeOffice

# Initialize migrations
migrate = Migrate(app, db, directory=os.path.join(os.path.dirname(app.root_path), "migrations"))

# Run within app context
with app.app_context():
    print("Importing models and setting up migration...")
    print("Models loaded. You can now run 'flask db migrate -m \"Add home_office model\"'")