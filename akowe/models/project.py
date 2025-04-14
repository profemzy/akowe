from datetime import datetime
from . import db

class Project(db.Model):
    __tablename__ = 'project'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='active')  # active, completed, archived
    hourly_rate = db.Column(db.Numeric(10, 2), nullable=True)  # Default project rate
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Project owner
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    client = db.relationship('Client', back_populates='projects')
    user = db.relationship('User', back_populates='projects')
    timesheet_entries = db.relationship('Timesheet', back_populates='project_ref', lazy='dynamic')
    
    def __repr__(self):
        return f"<Project {self.name} for {self.client.name}>"
