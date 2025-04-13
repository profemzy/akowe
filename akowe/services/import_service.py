import pandas as pd
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Tuple

from akowe.models import db
from akowe.models.income import Income
from akowe.models.expense import Expense

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
                income = Income(
                    date=datetime.strptime(row['date'], '%Y-%m-%d').date(),
                    amount=Decimal(str(row['amount'])),
                    client=row['client'],
                    project=row['project'],
                    invoice=row['invoice']
                )
                db.session.add(income)
                records.append({
                    'date': row['date'],
                    'amount': row['amount'],
                    'client': row['client'],
                    'project': row['project'],
                    'invoice': row['invoice']
                })
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
                    date=datetime.strptime(row['date'], '%Y-%m-%d').date(),
                    title=row['title'],
                    amount=Decimal(str(row['amount'])),
                    category=row['category'],
                    payment_method=row['payment_method'],
                    status=row['status'],
                    vendor=row['vendor'] if 'vendor' in row and not pd.isna(row['vendor']) else None
                )
                db.session.add(expense)
                records.append({
                    'date': row['date'],
                    'title': row['title'],
                    'amount': row['amount'],
                    'category': row['category'],
                    'payment_method': row['payment_method'],
                    'status': row['status'],
                    'vendor': row['vendor'] if 'vendor' in row and not pd.isna(row['vendor']) else None
                })
                count += 1
            
            db.session.commit()
            return records, count
        except Exception as e:
            db.session.rollback()
            raise e