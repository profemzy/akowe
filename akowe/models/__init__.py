from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models here to ensure they are registered with SQLAlchemy
from . import user, income, expense, timesheet, invoice, client

# Import models here to make them available after importing the package
from akowe.models import income, expense, user, invoice, timesheet