#!/usr/bin/env python3
"""
Seed database with initial data and generate sample transaction CSV files.

This script:
1. Initializes the database schema
2. Creates an admin user
3. Seeds client, project, invoice, and timesheet tables
4. Generates sample CSV files for expense and income transactions
"""

import os
import sys
import csv
import random
from datetime import datetime, timedelta
from decimal import Decimal

from flask import Flask
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from akowe.models import db
from akowe.models.user import User
from akowe.models.client import Client
from akowe.models.project import Project
from akowe.models.invoice import Invoice
from akowe.models.timesheet import Timesheet

# Constants for sample data
CLIENTS = [
    {"name": "Acme Corp", "email": "contact@acmecorp.com", "phone": "555-123-4567", 
     "address": "123 Main St, Anytown, USA", "contact_person": "John Smith"},
    {"name": "TechStart Inc", "email": "info@techstart.io", "phone": "555-987-6543", 
     "address": "456 Innovation Way, Tech City, USA", "contact_person": "Jane Doe"},
    {"name": "Global Services Ltd", "email": "support@globalservices.com", "phone": "555-456-7890", 
     "address": "789 Business Blvd, Enterprise, USA", "contact_person": "Robert Johnson"},
    {"name": "Creative Solutions", "email": "hello@creativesolutions.com", "phone": "555-789-0123", 
     "address": "321 Design Ave, Artville, USA", "contact_person": "Sarah Williams"},
    {"name": "Data Dynamics", "email": "info@datadynamics.com", "phone": "555-234-5678", 
     "address": "567 Analytics Dr, Datatown, USA", "contact_person": "Michael Brown"}
]

PROJECTS = [
    {"name": "Website Redesign", "description": "Complete overhaul of company website", "status": "active", "hourly_rate": 85.00},
    {"name": "Mobile App Development", "description": "Creating a new mobile application", "status": "active", "hourly_rate": 95.00},
    {"name": "Database Migration", "description": "Migrating legacy database to new system", "status": "completed", "hourly_rate": 110.00},
    {"name": "SEO Optimization", "description": "Improving search engine rankings", "status": "active", "hourly_rate": 75.00},
    {"name": "Cloud Infrastructure Setup", "description": "Setting up AWS infrastructure", "status": "active", "hourly_rate": 120.00},
    {"name": "Security Audit", "description": "Comprehensive security review", "status": "completed", "hourly_rate": 150.00},
    {"name": "Content Creation", "description": "Creating marketing content", "status": "active", "hourly_rate": 65.00},
    {"name": "Training Program", "description": "Developing employee training materials", "status": "active", "hourly_rate": 90.00}
]

TIMESHEET_DESCRIPTIONS = [
    "Client meeting to discuss project requirements",
    "Development of core functionality",
    "Bug fixing and code review",
    "Documentation and knowledge transfer",
    "Project planning and architecture design",
    "Testing and quality assurance",
    "Deployment and infrastructure setup",
    "Research and prototyping",
    "UI/UX design and implementation",
    "Performance optimization"
]

EXPENSE_CATEGORIES = [
    "Office Supplies", "Software", "Hardware", "Travel", "Meals", "Rent", 
    "Utilities", "Marketing", "Professional Services", "Miscellaneous"
]

EXPENSE_PAYMENT_METHODS = [
    "Credit Card", "Debit Card", "Cash", "Bank Transfer", "PayPal", "Check"
]

EXPENSE_STATUSES = ["paid", "pending", "reimbursed"]

EXPENSE_VENDORS = [
    "Amazon", "Office Depot", "Dell", "Apple", "Microsoft", "Adobe", 
    "Uber", "Lyft", "Marriott", "Hilton", "Starbucks", "Subway"
]


def init_db():
    """Initialize the database schema."""
    # Create a Flask app with database configuration
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

    with app.app_context():
        try:
            # Create all tables
            db.create_all()
            print("Database schema created/updated successfully!")
            return app
        except SQLAlchemyError as e:
            print(f"Database error: {str(e)}")
            return None


def create_admin(app):
    """Create admin user from environment variables."""
    with app.app_context():
        try:
            # Check if admin user already exists
            admin_username = os.environ.get("ADMIN_USERNAME", "admin")
            admin = User.query.filter_by(username=admin_username).first()

            if admin:
                print(f"Admin user '{admin_username}' already exists.")
                return admin

            # Get admin details from environment
            admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
            admin_password = os.environ.get("ADMIN_PASSWORD", "admin_password")
            admin_first_name = os.environ.get("ADMIN_FIRST_NAME", "Admin")
            admin_last_name = os.environ.get("ADMIN_LAST_NAME", "User")

            # Get hourly rate from environment or use default
            default_hourly_rate = os.environ.get("DEFAULT_HOURLY_RATE", "100.00")

            # Create admin user
            admin = User(
                username=admin_username,
                email=admin_email,
                first_name=admin_first_name,
                last_name=admin_last_name,
                hourly_rate=Decimal(default_hourly_rate),
                is_admin=True,
                is_active=True
            )
            admin.password = admin_password

            # Add to database
            db.session.add(admin)
            db.session.commit()

            print(f"Admin user '{admin_username}' created successfully.")
            return admin
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error creating admin: {str(e)}")
            return None


def seed_clients(app, admin_user):
    """Seed client data."""
    with app.app_context():
        try:
            # Check if clients already exist
            if Client.query.count() > 0:
                print(f"{Client.query.count()} clients already exist.")
                return Client.query.all()

            clients = []
            for client_data in CLIENTS:
                client = Client(
                    name=client_data["name"],
                    email=client_data["email"],
                    phone=client_data["phone"],
                    address=client_data["address"],
                    contact_person=client_data["contact_person"],
                    user_id=admin_user.id
                )
                db.session.add(client)
                clients.append(client)

            db.session.commit()
            print(f"Created {len(clients)} clients.")
            return clients
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error seeding clients: {str(e)}")
            return []


def seed_projects(app, admin_user, clients):
    """Seed project data."""
    with app.app_context():
        try:
            # Check if projects already exist
            if Project.query.count() > 0:
                print(f"{Project.query.count()} projects already exist.")
                return Project.query.all()

            projects = []
            for client in clients:
                # Assign 1-3 projects per client
                num_projects = random.randint(1, 3)
                for i in range(num_projects):
                    project_data = random.choice(PROJECTS)
                    project = Project(
                        name=f"{project_data['name']} for {client.name}",
                        description=project_data["description"],
                        status=project_data["status"],
                        hourly_rate=Decimal(str(project_data["hourly_rate"])),
                        client_id=client.id,
                        user_id=admin_user.id
                    )
                    db.session.add(project)
                    projects.append(project)

            db.session.commit()
            print(f"Created {len(projects)} projects.")
            return projects
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error seeding projects: {str(e)}")
            return []


def seed_invoices(app, admin_user, clients, projects):
    """Seed invoice data."""
    with app.app_context():
        try:
            # Check if invoices already exist
            if Invoice.query.count() > 0:
                print(f"{Invoice.query.count()} invoices already exist.")
                return Invoice.query.all()

            invoices = []
            for client in clients:
                # Create 1-2 invoices per client
                num_invoices = random.randint(1, 2)
                for i in range(num_invoices):
                    # Generate invoice number
                    invoice_number = f"INV-{datetime.now().strftime('%Y%m')}-{random.randint(1000, 9999)}"

                    # Set dates
                    issue_date = datetime.now().date() - timedelta(days=random.randint(1, 30))
                    due_date = issue_date + timedelta(days=30)

                    # Create invoice
                    invoice = Invoice(
                        invoice_number=invoice_number,
                        client_id=client.id,
                        company_name="Your Company Name",
                        issue_date=issue_date,
                        due_date=due_date,
                        notes="Thank you for your business!",
                        subtotal=Decimal("0.00"),  # Will be calculated later
                        tax_rate=Decimal("13.00"),  # 13% tax rate
                        tax_amount=Decimal("0.00"),  # Will be calculated later
                        total=Decimal("0.00"),  # Will be calculated later
                        status=random.choice(["draft", "sent", "paid"]),
                        user_id=admin_user.id
                    )

                    db.session.add(invoice)
                    db.session.flush()  # Get ID without committing

                    invoices.append(invoice)

            db.session.commit()
            print(f"Created {len(invoices)} invoices.")
            return invoices
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error seeding invoices: {str(e)}")
            return []


def seed_timesheets(app, admin_user, clients, projects, invoices):
    """Seed timesheet data."""
    with app.app_context():
        try:
            # Check if timesheets already exist
            if Timesheet.query.count() > 0:
                print(f"{Timesheet.query.count()} timesheet entries already exist.")
                return Timesheet.query.all()

            # First, ensure all projects are attached to the session
            project_ids = [project.id for project in projects]
            fresh_projects = {}
            for project in projects:
                # Create a mapping of project IDs to projects for easy lookup
                fresh_projects[project.id] = project

            timesheets = []

            # Create timesheet entries for each project
            for project_id, project in fresh_projects.items():
                # Create 3-8 timesheet entries per project
                num_entries = random.randint(3, 8)
                for i in range(num_entries):
                    # Set date within last 60 days
                    entry_date = datetime.now().date() - timedelta(days=random.randint(1, 60))

                    # Set hours between 1 and 8
                    hours = Decimal(str(random.randint(1, 8)))

                    # Get hourly rate from project or user
                    hourly_rate = project.hourly_rate or admin_user.hourly_rate or Decimal("100.00")

                    # Randomly assign to an invoice for this client
                    client_invoices = [inv for inv in invoices if inv.client_id == project.client_id]
                    invoice_id = random.choice(client_invoices).id if client_invoices and random.random() > 0.3 else None

                    # Set status based on invoice
                    status = "billed" if invoice_id else "pending"

                    # Create timesheet entry
                    timesheet = Timesheet(
                        date=entry_date,
                        client_id=project.client_id,
                        project_id=project.id,
                        description=random.choice(TIMESHEET_DESCRIPTIONS),
                        hours=hours,
                        hourly_rate=hourly_rate,
                        status=status,
                        invoice_id=invoice_id,
                        user_id=admin_user.id
                    )

                    db.session.add(timesheet)
                    timesheets.append(timesheet)

            # Commit the timesheet entries
            db.session.commit()

            # After commit, refresh all objects to ensure they're bound to the session
            # Refresh projects
            fresh_projects = {p.id: p for p in Project.query.filter(Project.id.in_(project_ids)).all()}

            # Refresh invoices
            invoice_ids = [inv.id for inv in invoices]
            fresh_invoices = Invoice.query.filter(Invoice.id.in_(invoice_ids)).all()

            # Update invoice totals
            # Note: We need to query invoices again after the commit to ensure they're attached to the session
            # This prevents the "Instance is not bound to a Session; attribute refresh operation cannot proceed" error
            # that occurs when trying to access attributes of objects detached from the session
            for invoice in fresh_invoices:
                invoice.calculate_totals()

            # Commit the updated invoice totals
            db.session.commit()

            # Print the number of timesheet entries created
            print(f"Created {len(timesheets)} timesheet entries.")

            # Return the timesheet entries
            return Timesheet.query.all()
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error seeding timesheets: {str(e)}")
            return []


def generate_expense_csv(clients, projects, admin_user):
    """Generate sample expense CSV file."""
    try:
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)

        # Create CSV file
        filename = "data/expense_sample.csv"
        with open(filename, "w", newline="") as csvfile:
            fieldnames = ["date", "title", "amount", "category", "payment_method", "status", "vendor", "user_id"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()

            # Generate 20-30 sample expense records
            num_records = random.randint(20, 30)
            for i in range(num_records):
                # Set date within last 90 days
                expense_date = (datetime.now() - timedelta(days=random.randint(1, 90))).strftime("%Y-%m-%d")

                # Set amount between $10 and $500
                amount = round(random.uniform(10, 500), 2)

                writer.writerow({
                    "date": expense_date,
                    "title": f"Expense for {random.choice(EXPENSE_CATEGORIES).lower()}",
                    "amount": amount,
                    "category": random.choice(EXPENSE_CATEGORIES),
                    "payment_method": random.choice(EXPENSE_PAYMENT_METHODS),
                    "status": random.choice(EXPENSE_STATUSES),
                    "vendor": random.choice(EXPENSE_VENDORS),
                    "user_id": admin_user.id
                })

        print(f"Generated sample expense CSV file: {filename}")
        return filename
    except Exception as e:
        print(f"Error generating expense CSV: {str(e)}")
        return None


def generate_income_csv(clients, projects, admin_user):
    """Generate sample income CSV file."""
    try:
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)

        # Create CSV file
        filename = "data/income_sample.csv"
        with open(filename, "w", newline="") as csvfile:
            fieldnames = ["date", "amount", "client", "project", "invoice", "user_id", "client_id", "project_id"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()

            # Generate 15-25 sample income records
            num_records = random.randint(15, 25)
            for i in range(num_records):
                # Set date within last 90 days
                income_date = (datetime.now() - timedelta(days=random.randint(1, 90))).strftime("%Y-%m-%d")

                # Randomly select client and project
                client = random.choice(clients)
                client_projects = [p for p in projects if p.client_id == client.id]
                project = random.choice(client_projects) if client_projects else None

                # Set amount between $500 and $5000
                amount = round(random.uniform(500, 5000), 2)

                # Generate invoice number
                invoice_number = f"INV-{random.randint(1000, 9999)}"

                writer.writerow({
                    "date": income_date,
                    "amount": amount,
                    "client": client.name,
                    "project": project.name if project else "General Services",
                    "invoice": invoice_number if random.random() > 0.3 else "",
                    "user_id": admin_user.id,
                    "client_id": client.id,
                    "project_id": project.id if project else ""
                })

        print(f"Generated sample income CSV file: {filename}")
        return filename
    except Exception as e:
        print(f"Error generating income CSV: {str(e)}")
        return None


def seed_database():
    """Main function to seed the database and generate sample CSV files."""
    print("Starting database seeding process...")

    # Initialize database
    app = init_db()
    if not app:
        print("Failed to initialize database.")
        return False

    # Create admin user
    admin_user = create_admin(app)
    if not admin_user:
        print("Failed to create admin user.")
        return False

    # Seed clients
    clients = seed_clients(app, admin_user)
    if not clients:
        print("Failed to seed clients.")
        return False

    # Seed projects
    projects = seed_projects(app, admin_user, clients)
    if not projects:
        print("Failed to seed projects.")
        return False

    # Seed invoices
    invoices = seed_invoices(app, admin_user, clients, projects)
    if not invoices:
        print("Failed to seed invoices.")
        return False

    # Seed timesheets
    timesheets = seed_timesheets(app, admin_user, clients, projects, invoices)
    if not timesheets:
        print("Failed to seed timesheets.")
        return False

    # Generate sample expense CSV
    expense_csv = generate_expense_csv(clients, projects, admin_user)
    if not expense_csv:
        print("Failed to generate expense CSV.")
        return False

    # Generate sample income CSV
    income_csv = generate_income_csv(clients, projects, admin_user)
    if not income_csv:
        print("Failed to generate income CSV.")
        return False

    print("\n✅ Database seeding completed successfully!")
    print(f"Sample expense CSV file: {expense_csv}")
    print(f"Sample income CSV file: {income_csv}")
    print("\nTo import these files:")
    print("1. Go to the Import page in the application")
    print("2. Upload the CSV files to import the sample transactions")

    return True


if __name__ == "__main__":
    success = seed_database()
    sys.exit(0 if success else 1)
