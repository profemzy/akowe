import pandas as pd
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Tuple

from akowe.models import db
from akowe.models.income import Income
from akowe.models.expense import Expense
from akowe.models.client import Client
from akowe.models.project import Project
from flask_login import current_user


class ImportService:
    @staticmethod
    def import_income_csv(file_path: str) -> Tuple[List[Dict[str, Any]], int]:
        """Import income data from CSV file.

        Args:
            file_path: Path to the CSV file

        Returns:
            Tuple containing list of imported records and count of successfully imported records
        """
        try:
            df = pd.read_csv(file_path)
            records = []
            count = 0

            for _, row in df.iterrows():
                # Get or create client and project
                client_name = row["client"]
                project_name = row["project"]
                
                client, client_id = ImportService.get_or_create_client(client_name)
                project, project_id = ImportService.get_or_create_project(project_name, client_id)
                
                income = Income(
                    date=datetime.strptime(row["date"], "%Y-%m-%d").date(),
                    amount=Decimal(str(row["amount"])),
                    client=client_name,
                    project=project_name,
                    invoice=row["invoice"],
                    client_id=client_id,
                    project_id=project_id,
                    user_id=current_user.id
                )
                db.session.add(income)
                records.append(
                    {
                        "date": row["date"],
                        "amount": row["amount"],
                        "client": client_name,
                        "project": project_name,
                        "invoice": row["invoice"],
                    }
                )
                count += 1

            db.session.commit()
            return records, count
        except Exception as e:
            db.session.rollback()
            raise e

    @staticmethod
    def import_expense_csv(file_path: str) -> Tuple[List[Dict[str, Any]], int]:
        """Import expense data from CSV file.

        Args:
            file_path: Path to the CSV file

        Returns:
            Tuple containing list of imported records and count of successfully imported records
        """
        try:
            df = pd.read_csv(file_path)
            records = []
            count = 0

            for _, row in df.iterrows():
                expense = Expense(
                    date=datetime.strptime(row["date"], "%Y-%m-%d").date(),
                    title=row["title"],
                    amount=Decimal(str(row["amount"])),
                    category=row["category"],
                    payment_method=row["payment_method"],
                    status=row["status"],
                    vendor=(
                        row["vendor"] if "vendor" in row and not pd.isna(row["vendor"]) else None
                    ),
                    user_id=current_user.id
                )
                db.session.add(expense)
                records.append(
                    {
                        "date": row["date"],
                        "title": row["title"],
                        "amount": row["amount"],
                        "category": row["category"],
                        "payment_method": row["payment_method"],
                        "status": row["status"],
                        "vendor": (
                            row["vendor"]
                            if "vendor" in row and not pd.isna(row["vendor"])
                            else None
                        ),
                    }
                )
                count += 1

            db.session.commit()
            return records, count
        except Exception as e:
            db.session.rollback()
            raise e
            
    @staticmethod
    def get_or_create_client(client_name):
        """Get or create a client by name.
        
        Args:
            client_name: The name of the client
            
        Returns:
            Client object and its ID
        """
        # Try to find client first
        client = Client.query.filter_by(name=client_name, user_id=current_user.id).first()
        
        # If not found, create a new one
        if client is None:
            client = Client(
                name=client_name,
                user_id=current_user.id
            )
            db.session.add(client)
            db.session.flush()  # Get ID without committing
            
        return client, client.id
    
    @staticmethod
    def get_or_create_project(project_name, client_id):
        """Get or create a project by name.
        
        Args:
            project_name: The name of the project
            client_id: The client ID this project belongs to
            
        Returns:
            Project object and its ID
        """
        # Try to find project first
        project = Project.query.filter_by(name=project_name, client_id=client_id, user_id=current_user.id).first()
        
        # If not found, create a new one
        if project is None:
            project = Project(
                name=project_name,
                client_id=client_id,
                user_id=current_user.id,
                status="active"
            )
            db.session.add(project)
            db.session.flush()  # Get ID without committing
            
        return project, project.id
    
    @staticmethod
    def import_all_transactions_csv(file_path: str) -> Tuple[Dict[str, Any], int]:
        """Import all transaction data from the combined transaction CSV export.
        
        This is used to recover from a backup of 'export all transactions' file.
        Supports multiple import formats including:
        1. Standard export format: type,date,description,amount,category,payment_method,status,reference
        2. Custom input format: date,type,description,amount,category,payment_method,status,reference
        
        Args:
            file_path: Path to the CSV file

        Returns:
            Tuple containing stats and count of successfully imported records
        """
        try:
            # Read the CSV and handle various formats
            df = pd.read_csv(file_path)
            income_count = 0
            expense_count = 0
            income_records = []
            expense_records = []
            
            # Determine the format based on columns
            columns = df.columns.tolist()
            
            # Choose import strategy based on column structure
            if 'type' in columns and 'date' in columns and 'description' in columns:
                # This is the main transaction export format
                # Format: date,type,description,amount,category,payment_method,status,reference
                income_df = df[df['type'].str.lower() == 'income'].copy()
                expense_df = df[df['type'].str.lower() == 'expense'].copy()
                
                # Process income records
                for _, row in income_df.iterrows():
                    # Parse description into client and project
                    description_parts = row["description"].split(" - ", 1)
                    client_name = description_parts[0]
                    project_name = description_parts[1] if len(description_parts) > 1 else "General"
                    
                    # Extract reference/invoice
                    reference = row.get("reference", "")
                    if pd.isna(reference):
                        reference = ""
                    
                    # Get or create client and project
                    client, client_id = ImportService.get_or_create_client(client_name)
                    project, project_id = ImportService.get_or_create_project(project_name, client_id)
                    
                    income = Income(
                        date=datetime.strptime(row["date"], "%Y-%m-%d").date(),
                        amount=Decimal(str(row["amount"])),
                        client=client_name,
                        project=project_name,
                        invoice=reference,
                        client_id=client_id,
                        project_id=project_id,
                        user_id=current_user.id
                    )
                    
                    db.session.add(income)
                    income_count += 1
                    income_records.append({
                        "date": row["date"],
                        "amount": row["amount"],
                        "client": client_name,
                        "project": project_name
                    })
                
                # Process expense records
                for _, row in expense_df.iterrows():
                    # Expense amounts may be stored as negative
                    amount_val = row["amount"]
                    if isinstance(amount_val, str) and amount_val.startswith('-'):
                        amount = abs(Decimal(amount_val))
                    else:
                        amount = abs(Decimal(str(amount_val)))
                    
                    title = row["description"]
                    category = row.get("category", "Other")
                    if pd.isna(category):
                        category = "Other"
                        
                    payment_method = row.get("payment_method", "Other")
                    if pd.isna(payment_method):
                        payment_method = "Other"
                        
                    status = row.get("status", "paid")
                    if pd.isna(status):
                        status = "paid"
                        
                    reference = row.get("reference", "")
                    if pd.isna(reference):
                        reference = ""
                    
                    expense = Expense(
                        date=datetime.strptime(row["date"], "%Y-%m-%d").date(),
                        title=title,
                        amount=amount,
                        category=category,
                        payment_method=payment_method,
                        status=status,
                        vendor=reference,
                        user_id=current_user.id
                    )
                    
                    db.session.add(expense)
                    expense_count += 1
                    expense_records.append({
                        "date": row["date"],
                        "title": title,
                        "amount": amount,
                        "category": category
                    })
                
            elif all(col in columns for col in ['type', 'date', 'client', 'amount']):
                # This is the sample_combined.csv format with client/vendor
                # Format: type,date,amount,client,vendor,project,category,tax_deductible,notes,invoice
                
                # Split into income and expense dataframes
                income_df = df[df['type'].str.lower() == 'income'].copy()
                expense_df = df[df['type'].str.lower() == 'expense'].copy()
                
                # Process income records
                for _, row in income_df.iterrows():
                    client_name = row.get("client", "")
                    if pd.isna(client_name):
                        client_name = "Unknown Client"
                    
                    project_name = row.get("project", "")
                    if pd.isna(project_name):
                        project_name = "General"
                    
                    invoice_num = row.get("invoice", "")
                    if pd.isna(invoice_num):
                        invoice_num = ""
                    
                    # Get or create client and project
                    client, client_id = ImportService.get_or_create_client(client_name)
                    project, project_id = ImportService.get_or_create_project(project_name, client_id)
                    
                    income = Income(
                        date=datetime.strptime(row["date"], "%Y-%m-%d").date(),
                        amount=Decimal(str(row["amount"])),
                        client=client_name,
                        project=project_name,
                        invoice=invoice_num,
                        client_id=client_id,
                        project_id=project_id,
                        user_id=current_user.id
                    )
                    
                    db.session.add(income)
                    income_count += 1
                    income_records.append({
                        "date": row["date"],
                        "amount": row["amount"],
                        "client": client_name,
                        "project": project_name
                    })
                
                # Process expense records
                for _, row in expense_df.iterrows():
                    vendor_name = row.get("vendor", "")
                    if pd.isna(vendor_name):
                        vendor_name = "Unknown Vendor"
                    
                    category = row.get("category", "Other")
                    if pd.isna(category):
                        category = "Other"
                    
                    notes = row.get("notes", "")
                    if pd.isna(notes):
                        notes = ""
                    
                    # We don't use tax_deductible since the field doesn't exist in the model
                    # Just read it for future reference
                    is_tax_deductible = row.get("tax_deductible", False)
                    if pd.isna(is_tax_deductible):
                        is_tax_deductible = False
                    
                    # Expense amounts may already be negative
                    amount_val = row["amount"]
                    if isinstance(amount_val, str) and amount_val.startswith('-'):
                        amount = abs(Decimal(amount_val))
                    else:
                        amount = abs(Decimal(str(amount_val)))
                    
                    expense = Expense(
                        date=datetime.strptime(row["date"], "%Y-%m-%d").date(),
                        title=notes or category,  # Use notes if available, otherwise category
                        amount=amount,
                        category=category,
                        payment_method="other",  # Default
                        status="paid",  # Default
                        vendor=vendor_name,
                        user_id=current_user.id
                    )
                    
                    db.session.add(expense)
                    expense_count += 1
                    expense_records.append({
                        "date": row["date"],
                        "title": notes or category,
                        "amount": amount,
                        "category": category
                    })
            else:
                # Unknown format - try a best effort approach
                # Look for type indicator
                type_col = next((col for col in ['type', 'transaction_type'] if col in columns), None)
                date_col = next((col for col in ['date', 'transaction_date'] if col in columns), None)
                amount_col = next((col for col in ['amount', 'value'] if col in columns), None)
                
                if not all([type_col, date_col, amount_col]):
                    raise ValueError("Could not determine CSV format - missing required columns")
                
                # Create default client and project for imports
                default_client, default_client_id = ImportService.get_or_create_client("Import Client")
                default_project, default_project_id = ImportService.get_or_create_project("Import Project", default_client_id)
                
                # Very basic processing by type
                for _, row in df.iterrows():
                    # Determine if income or expense
                    transaction_type = str(row[type_col]).lower()
                    is_income = ('income' in transaction_type or 
                                transaction_type == 'i' or 
                                (amount_col in row and float(row[amount_col]) > 0))
                    
                    amount_val = row[amount_col]
                    if isinstance(amount_val, str) and amount_val.startswith('-'):
                        amount = abs(Decimal(amount_val))
                    else:
                        amount = abs(Decimal(str(amount_val)))
                    
                    if is_income:
                        # Create simple income record
                        income = Income(
                            date=datetime.strptime(row[date_col], "%Y-%m-%d").date(),
                            amount=amount,
                            client="Import Client",
                            project="Import Project",
                            invoice="",
                            client_id=default_client_id,
                            project_id=default_project_id,
                            user_id=current_user.id
                        )
                        
                        db.session.add(income)
                        income_count += 1
                        income_records.append({
                            "date": row[date_col],
                            "amount": amount,
                            "client": "Import Client",
                            "project": "Import Project"
                        })
                    else:
                        # Create simple expense record
                        expense = Expense(
                            date=datetime.strptime(row[date_col], "%Y-%m-%d").date(),
                            title="Imported Expense",
                            amount=amount,
                            category="Other",
                            payment_method="other",
                            status="paid",
                            vendor="Imported",
                            user_id=current_user.id
                        )
                        
                        db.session.add(expense)
                        expense_count += 1
                        expense_records.append({
                            "date": row[date_col],
                            "title": "Imported Expense",
                            "amount": amount,
                            "category": "Other"
                        })
            
            db.session.commit()
            total_count = income_count + expense_count
            
            return {
                "income_count": income_count,
                "expense_count": expense_count,
                "income_records": income_records[:10],  # Show first 10 records
                "expense_records": expense_records[:10],  # Show first 10 records
                "total_count": total_count
            }, total_count
        except Exception as e:
            db.session.rollback()
            raise e