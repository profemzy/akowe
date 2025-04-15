"""Service for exporting financial data to CSV."""

import csv
import io
from datetime import datetime
from typing import Tuple

from akowe.models.expense import Expense
from akowe.models.income import Income


class ExportService:
    """Service for exporting financial data to CSV."""

    @staticmethod
    def export_income_csv(year: int = None) -> Tuple[io.BytesIO, str]:
        """Export income data to CSV.

        Args:
            year: Optional year to filter income records

        Returns:
            Tuple containing the CSV data as BytesIO and the filename
        """
        # Create a string buffer for building the CSV
        string_buffer = io.StringIO()
        writer = csv.writer(string_buffer)

        # Write header row
        writer.writerow(["date", "amount", "client", "project", "invoice"])

        # Query income records, optionally filtered by year
        income_records = Income.query
        if year:
            income_records = income_records.filter(
                Income.date.between(datetime(year, 1, 1), datetime(year, 12, 31))
            )
        income_records = income_records.order_by(Income.date).all()

        # Write data rows
        for income in income_records:
            writer.writerow(
                [
                    income.date.strftime("%Y-%m-%d"),
                    f"{income.amount:.2f}",
                    income.client,
                    income.project,
                    income.invoice or "",
                ]
            )

        # Convert string buffer to bytes buffer
        bytes_buffer = io.BytesIO()
        bytes_buffer.write(string_buffer.getvalue().encode("utf-8"))
        bytes_buffer.seek(0)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        year_suffix = f"_{year}" if year else ""
        filename = f"income_export{year_suffix}_{timestamp}.csv"

        return bytes_buffer, filename

    @staticmethod
    def export_expense_csv(year: int = None, category: str = None) -> Tuple[io.BytesIO, str]:
        """Export expense data to CSV.

        Args:
            year: Optional year to filter expense records
            category: Optional category to filter expense records

        Returns:
            Tuple containing the CSV data as BytesIO and the filename
        """
        # Create a string buffer for building the CSV
        string_buffer = io.StringIO()
        writer = csv.writer(string_buffer)

        # Write header row
        writer.writerow(
            ["date", "title", "amount", "category", "payment_method", "status", "vendor"]
        )

        # Query expense records, optionally filtered by year and category
        expense_records = Expense.query
        if year:
            expense_records = expense_records.filter(
                Expense.date.between(datetime(year, 1, 1), datetime(year, 12, 31))
            )
        if category:
            expense_records = expense_records.filter(Expense.category == category)
        expense_records = expense_records.order_by(Expense.date).all()

        # Write data rows
        for expense in expense_records:
            writer.writerow(
                [
                    expense.date.strftime("%Y-%m-%d"),
                    expense.title,
                    f"{expense.amount:.2f}",
                    expense.category,
                    expense.payment_method,
                    expense.status,
                    expense.vendor or "",
                ]
            )

        # Convert string buffer to bytes buffer
        bytes_buffer = io.BytesIO()
        bytes_buffer.write(string_buffer.getvalue().encode("utf-8"))
        bytes_buffer.seek(0)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        year_suffix = f"_{year}" if year else ""
        category_suffix = f"_{category}" if category else ""
        filename = f"expense_export{year_suffix}{category_suffix}_{timestamp}.csv"

        return bytes_buffer, filename

    @staticmethod
    def export_all_transactions_csv(year: int = None) -> Tuple[io.BytesIO, str]:
        """Export all financial transactions to CSV.

        Args:
            year: Optional year to filter transactions

        Returns:
            Tuple containing the CSV data as BytesIO and the filename
        """
        # Create a string buffer for building the CSV
        string_buffer = io.StringIO()
        writer = csv.writer(string_buffer)

        # Write header row
        writer.writerow(
            [
                "date",
                "type",
                "description",
                "amount",
                "category",
                "payment_method",
                "status",
                "reference",
            ]
        )

        # Query income records, optionally filtered by year
        income_records = Income.query
        if year:
            income_records = income_records.filter(
                Income.date.between(datetime(year, 1, 1), datetime(year, 12, 31))
            )
        income_records = income_records.order_by(Income.date).all()

        # Query expense records, optionally filtered by year
        expense_records = Expense.query
        if year:
            expense_records = expense_records.filter(
                Expense.date.between(datetime(year, 1, 1), datetime(year, 12, 31))
            )
        expense_records = expense_records.order_by(Expense.date).all()

        # Create a combined list of transactions to sort by date
        transactions = []

        for income in income_records:
            transactions.append(
                {
                    "date": income.date,
                    "type": "Income",
                    "description": f"{income.client} - {income.project}",
                    "amount": income.amount,
                    "category": "",
                    "payment_method": "",
                    "status": "received",
                    "reference": income.invoice or "",
                }
            )

        for expense in expense_records:
            transactions.append(
                {
                    "date": expense.date,
                    "type": "Expense",
                    "description": expense.title,
                    "amount": -expense.amount,  # Negative for expenses
                    "category": expense.category,
                    "payment_method": expense.payment_method,
                    "status": expense.status,
                    "reference": expense.vendor or "",
                }
            )

        # Sort transactions by date
        transactions.sort(key=lambda x: x["date"])

        # Write data rows
        for transaction in transactions:
            writer.writerow(
                [
                    transaction["date"].strftime("%Y-%m-%d"),
                    transaction["type"],
                    transaction["description"],
                    f"{transaction['amount']:.2f}",
                    transaction["category"],
                    transaction["payment_method"],
                    transaction["status"],
                    transaction["reference"],
                ]
            )

        # Convert string buffer to bytes buffer
        bytes_buffer = io.BytesIO()
        bytes_buffer.write(string_buffer.getvalue().encode("utf-8"))
        bytes_buffer.seek(0)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        year_suffix = f"_{year}" if year else ""
        filename = f"all_transactions{year_suffix}_{timestamp}.csv"

        return bytes_buffer, filename
