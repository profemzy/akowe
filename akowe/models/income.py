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
    invoice = db.Column(db.String(255), nullable=True)  # Keep for backward compatibility
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Optional foreign key relationships
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoice.id"), nullable=True)

    # Relationship definitions
    client_ref = db.relationship("Client", backref=db.backref("incomes", lazy="dynamic"))
    project_ref = db.relationship("Project", backref=db.backref("incomes", lazy="dynamic"))
    invoice_ref = db.relationship("Invoice", backref=db.backref("income_records", lazy="dynamic"))
    user = db.relationship("User", backref=db.backref("incomes", lazy="dynamic"))

    def __repr__(self):
        return f"<Income {self.id}: {self.amount} from {self.client} on {self.date}>"