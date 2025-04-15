from datetime import datetime
from sqlalchemy import Numeric
from . import db


class Invoice(db.Model):
    __tablename__ = 'invoice'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), nullable=False, unique=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    company_name = db.Column(db.String(255), nullable=True)  # Company name on invoice
    issue_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    due_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    subtotal = db.Column(Numeric(10, 2), nullable=False, default=0)
    tax_rate = db.Column(Numeric(5, 2), nullable=False, default=0)  # Percentage (e.g., 13.00 for 13%)
    tax_amount = db.Column(Numeric(10, 2), nullable=False, default=0)
    total = db.Column(Numeric(10, 2), nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default='draft')  # draft, sent, paid, overdue, cancelled
    sent_date = db.Column(db.DateTime, nullable=True)
    paid_date = db.Column(db.DateTime, nullable=True)
    payment_method = db.Column(db.String(50), nullable=True)
    payment_reference = db.Column(db.String(100), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    timesheet_entries = db.relationship('Timesheet', back_populates='invoice', cascade='all, delete-orphan')
    user = db.relationship('User', back_populates='invoices')
    client_ref = db.relationship('Client', back_populates='invoices')

    def calculate_totals(self):
        """Calculate subtotal, tax, and total"""
        # Calculate subtotal from timesheet entries
        self.subtotal = sum(entry.amount for entry in self.timesheet_entries)
        
        # Calculate tax amount
        self.tax_amount = self.subtotal * (self.tax_rate / 100)
        
        # Calculate total
        self.total = self.subtotal + self.tax_amount
        
        return self.total
    
    def __repr__(self):
        client_name = self.client_ref.name if self.client_ref else "Unknown Client"
        return f"<Invoice {self.invoice_number}: ${self.total} to {client_name} ({self.status})>"
