from datetime import datetime
from sqlalchemy import Numeric
from . import db


class Expense(db.Model):
    __tablename__ = 'expense'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    amount = db.Column(Numeric(10, 2), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    vendor = db.Column(db.String(255), nullable=True)
    receipt_blob_name = db.Column(db.String(255), nullable=True)
    receipt_url = db.Column(db.String(1024), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Expense {self.id}: {self.amount} for {self.title} on {self.date}>"
        
    def has_receipt(self) -> bool:
        """Check if the expense has a receipt attached"""
        return bool(self.receipt_blob_name)
