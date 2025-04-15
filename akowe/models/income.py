from datetime import datetime
from sqlalchemy import Numeric
from . import db


class Income(db.Model):
    __tablename__ = "income"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    amount = db.Column(Numeric(10, 2), nullable=False)
    client = db.Column(db.String(255), nullable=False)
    project = db.Column(db.String(255), nullable=False)
    invoice = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Income {self.id}: {self.amount} from {self.client} on {self.date}>"
