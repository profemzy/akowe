from datetime import datetime
from . import db


class Client(db.Model):
    __tablename__ = 'client'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True, index=True)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    address = db.Column(db.Text, nullable=True)
    contact_person = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('clients', lazy='dynamic'))
    invoices = db.relationship('Invoice', back_populates='client_ref', lazy='dynamic')
    timesheet_entries = db.relationship('Timesheet', back_populates='client_ref', lazy='dynamic')
    projects = db.relationship('Project', back_populates='client', lazy='dynamic')
    
    def __repr__(self):
        return f"<Client {self.name}>"
