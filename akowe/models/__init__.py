from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models here to make them available after importing the package
from akowe.models import income, expense, user, invoice, timesheet