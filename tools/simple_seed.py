#!/usr/bin/env python3
"""
Simple seed script for Akowe database.
Creates basic demo data without complex relationships.
"""

import os
from datetime import datetime, timedelta
from decimal import Decimal

from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

from akowe.models import db
from akowe.models.user import User
from akowe.models.client import Client
from akowe.models.project import Project
from akowe.models.invoice import Invoice
from akowe.models.expense import Expense
from akowe.models.income import Income

def create_app():
    """Create a Flask app with database configuration."""
    app = Flask(__name__)

    # Get database configuration from environment
    db_user = os.environ.get("DB_USER", "akowe_user")
    db_password = os.environ.get("DB_PASSWORD", "akowe_password")
    db_host = os.environ.get("DB_HOST", "localhost")
    db_port = os.environ.get("DB_PORT", "5432")
    db_name = os.environ.get("DB_NAME", "akowe")

    # Configure database
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize SQLAlchemy with the Flask app
    db.init_app(app)

    return app

def seed_database():
    """Seed the database with demo data."""
    print("Starting simple database seeding process...")

    # Create a Flask app
    app = create_app()

    with app.app_context():
        try:
            # Get admin user
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("Admin user not found. Please create an admin user first.")
                return False

            # Create clients
            clients = []
            client_data = [
                {"name": "Acme Corp", "email": "contact@acmecorp.com", "phone": "555-123-4567"},
                {"name": "TechStart Inc", "email": "info@techstart.io", "phone": "555-987-6543"},
                {"name": "Global Services", "email": "support@globalservices.com", "phone": "555-456-7890"}
            ]

            for data in client_data:
                # Check if client already exists
                existing = Client.query.filter_by(name=data["name"], user_id=admin.id).first()
                if existing:
                    print(f"Client {data['name']} already exists.")
                    clients.append(existing)
                    continue

                client = Client(
                    name=data["name"],
                    email=data["email"],
                    phone=data["phone"],
                    address="123 Business St, City, Country",
                    contact_person="Contact Person",
                    user_id=admin.id
                )
                db.session.add(client)
                clients.append(client)

            db.session.commit()
            print(f"Created/found {len(clients)} clients.")

            # Create projects
            projects = []
            project_data = [
                {"name": "Website Redesign", "hourly_rate": 85.00},
                {"name": "Mobile App Development", "hourly_rate": 95.00},
                {"name": "Database Migration", "hourly_rate": 110.00}
            ]

            for i, data in enumerate(project_data):
                client = clients[i % len(clients)]
                
                # Check if project already exists
                existing = Project.query.filter_by(name=data["name"], client_id=client.id, user_id=admin.id).first()
                if existing:
                    print(f"Project {data['name']} already exists.")
                    projects.append(existing)
                    continue

                project = Project(
                    name=data["name"],
                    description=f"Description for {data['name']}",
                    status="active",
                    hourly_rate=Decimal(str(data["hourly_rate"])),
                    client_id=client.id,
                    user_id=admin.id
                )
                db.session.add(project)
                projects.append(project)

            db.session.commit()
            print(f"Created/found {len(projects)} projects.")

            # Create expenses
            expenses = []
            expense_data = [
                {"title": "Office Supplies", "amount": 125.50, "category": "Office Supplies"},
                {"title": "Software License", "amount": 299.99, "category": "Software"},
                {"title": "Business Lunch", "amount": 85.75, "category": "Meals"},
                {"title": "Travel Expenses", "amount": 450.00, "category": "Travel"},
                {"title": "Hardware Purchase", "amount": 899.99, "category": "Hardware"}
            ]

            for data in expense_data:
                # Set date within last 30 days
                expense_date = datetime.now().date() - timedelta(days=len(expenses) * 3)
                
                expense = Expense(
                    date=expense_date,
                    title=data["title"],
                    amount=Decimal(str(data["amount"])),
                    category=data["category"],
                    payment_method="Credit Card",
                    status="paid",
                    vendor="Vendor Name",
                    user_id=admin.id
                )
                db.session.add(expense)
                expenses.append(expense)

            db.session.commit()
            print(f"Created {len(expenses)} expenses.")

            # Create incomes
            incomes = []
            for i, project in enumerate(projects):
                # Set date within last 30 days
                income_date = datetime.now().date() - timedelta(days=i * 5)
                
                # Set amount between $1000 and $5000
                amount = Decimal(str(1000 + i * 1000))
                
                # Get client name
                client = Client.query.get(project.client_id)
                client_name = client.name if client else "Unknown Client"
                
                income = Income(
                    date=income_date,
                    amount=amount,
                    client=client_name,
                    project=project.name,
                    client_id=project.client_id,
                    project_id=project.id,
                    invoice="INV-" + str(1000 + i),
                    user_id=admin.id
                )
                db.session.add(income)
                incomes.append(income)

            db.session.commit()
            print(f"Created {len(incomes)} incomes.")

            print("\n✅ Simple database seeding completed successfully!")
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error: {str(e)}")
            return False

if __name__ == "__main__":
    success = seed_database()
    exit(0 if success else 1)
