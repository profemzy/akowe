from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models here to ensure they are registered with SQLAlchemy
# The import order matters for relationships - import parent models first
from . import user, income, expense
from . import client
from . import project
from . import timesheet, invoice