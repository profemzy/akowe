from datetime import datetime
from sqlalchemy import Numeric
from . import db


class Timesheet(db.Model):
    __tablename__ = 'timesheet'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    hours = db.Column(Numeric(5, 2), nullable=False)  # Up to 999.99 hours
    hourly_rate = db.Column(Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, billed, paid
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    invoice = db.relationship('Invoice', back_populates='timesheet_entries')
    user = db.relationship('User', back_populates='timesheet_entries')
    client_ref = db.relationship('Client', back_populates='timesheet_entries')
    project_ref = db.relationship('Project', back_populates='timesheet_entries')
    
    @property
    def amount(self):
        """Calculate the total amount for this timesheet entry"""
        return self.hours * self.hourly_rate
    
    def __repr__(self):
        client_name = self.client_ref.name if self.client_ref else "Unknown Client"
        return f"<Timesheet {self.id}: {self.hours} hours for {client_name} on {self.date.strftime('%Y-%m-%d')}>"
