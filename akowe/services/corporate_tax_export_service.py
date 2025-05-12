"""Service for exporting financial data in corporate tax preparation formats."""

import csv
import io
import json
from datetime import datetime
from typing import Tuple, Dict, List, Optional, Union
from decimal import Decimal

from akowe.models.expense import Expense
from akowe.models.income import Income
from akowe.app.tax_dashboard import CRA_TAX_CATEGORIES, GST_HST_RATES, QST_RATE


class CorporateTaxExportService:
    """Service for exporting financial data in formats compatible with corporate tax preparation software."""

    # GIFI code mappings for T2 corporate tax returns
    # These codes are standardized numeric codes required by CRA
    GIFI_CODE_MAPPING = {
        # Balance Sheet - Asset GIFI codes (1000-2599)
        "cash": "1001",               # Cash on hand and in bank deposits
        "accounts_receivable": "1060",  # Trade accounts receivable
        "prepaid_expenses": "1480",   # Prepaid expenses
        "equipment": "1740",          # Production equipment
        "computer_hardware": "1742",  # Computer hardware
        "furniture_fixtures": "1780",  # Furniture and fixtures
        "accumulated_depreciation": "2008",  # Accumulated depreciation
        
        # Balance Sheet - Liability GIFI codes (2600-3499)
        "accounts_payable": "2620",   # Trade accounts payable
        "gst_hst_payable": "2683",    # GST/HST payable
        "income_tax_payable": "2860",  # Income tax payable
        "short_term_loans": "2620",   # Short-term loans

        # Balance Sheet - Equity GIFI codes (3500-3999)
        "common_shares": "3500",      # Common shares
        "retained_earnings": "3840",  # Retained earnings

        # Income Statement - Revenue GIFI codes (8000-8299)
        "sales": "8000",              # Sales
        "professional_income": "8020",  # Professional fees income
        "consulting_fees": "8022",    # Consulting fees income
        "contract_revenue": "8090",   # Contract revenue
        "other_revenue": "8230",      # Other revenue

        # Income Statement - Expense GIFI codes (8300-9369)
        "advertising": "8520",        # Advertising expenses
        "meals_entertainment": "8523",  # Meals and entertainment
        "insurance": "8690",         # Insurance expenses
        "interest": "8710",          # Interest expenses
        "bank_charges": "8760",      # Bank charges
        "office_supplies": "8810",   # Office expenses
        "supplies": "8811",          # Other office expenses
        "professional_fees": "8860",  # Professional fees
        "legal": "8861",             # Legal fees
        "accounting": "8862",        # Accounting fees
        "rent": "8910",              # Rent
        "repairs": "8960",           # Maintenance and repairs
        "maintenance": "8963",       # Building maintenance
        "salaries": "9060",          # Salaries and wages
        "travel": "9200",            # Travel expenses
        "utilities": "9220",         # Utilities
        "telephone": "9225",         # Telephone expenses
        "internet": "9226",          # Internet expenses
        "vehicle": "9281",           # Motor vehicle expenses
        "fuel": "9224",              # Fuel expenses
        "software": "8335",          # Computer software expense
        "hardware": "8331",          # Computer hardware expense
        "subscription": "8811",      # Subscriptions
        "training": "8872",          # Training expenses
        "memberships": "8871",       # Membership fees
        "other": "9270",             # Other expenses
    }

    @classmethod
    def export_t2_gifi_format(cls, year: int, province: str = "Ontario") -> Tuple[io.BytesIO, str]:
        """Export data formatted specifically for T2 corporate tax returns using GIFI codes.
        
        Args:
            year: The tax year to export
            province: Province for GST/HST rate calculation
            
        Returns:
            Tuple containing the CSV data as BytesIO and the filename
        """
        # Create a string buffer for building the CSV
        string_buffer = io.StringIO()
        writer = csv.writer(string_buffer)
        
        # Determine if province is Quebec for special handling
        is_quebec = province == "Quebec"
        
        # Get GST/HST rate for the province and convert to Decimal
        gst_hst_rate_float = GST_HST_RATES.get(province, 0.05)  # Default to 5% if not found
        gst_hst_rate = Decimal(str(gst_hst_rate_float))  # Convert float to Decimal
        
        # For Quebec, also get QST rate
        if is_quebec:
            qst_rate = Decimal(str(QST_RATE))
        else:
            qst_rate = Decimal('0')
            
        # Write header row with GIFI information
        tax_column = "GST/HST Paid" if not is_quebec else "GST/QST Paid"
        writer.writerow([
            "Date",
            "Description",
            "Amount",
            "GIFI Code",
            "GIFI Description",
            tax_column,
            "Reference/Source"
        ])
        
        # Add Income Statement header (GIFI 8000-9369)
        writer.writerow([])
        writer.writerow(["INCOME STATEMENT (GIFI 8000-9369)"])
        writer.writerow([])
        
        # Add Revenue section header (GIFI 8000-8299)
        writer.writerow(["REVENUE (GIFI 8000-8299)"])
        
        # Query income records for the year
        income_records = Income.query
        if year:
            from_date = datetime(year, 1, 1)
            to_date = datetime(year, 12, 31)
            print(f"Querying income records between {from_date} and {to_date}")
            income_records = income_records.filter(
                Income.date.between(from_date, to_date)
            )

        # Debug the query
        print(f"Income query: {income_records}")

        # Get all records
        income_records = income_records.order_by(Income.date).all()

        # Debug found records
        print(f"Found {len(income_records)} income records: {income_records}")
        
        # Write income data rows with GST/HST amounts
        total_revenue = Decimal('0.00')
        total_revenue_tax = Decimal('0.00')
        for income in income_records:
            # Map to appropriate GIFI code or default to 8000
            gifi_code = cls.GIFI_CODE_MAPPING.get("professional_income", "8020")
            gifi_description = "Professional fees income"
            
            # Add to total revenue
            total_revenue += income.amount

            # Calculate GST/HST included in the income amount
            if is_quebec:
                # For Quebec, calculate GST and QST separately
                # GST is 5% of the pre-tax amount
                gst_amount = (income.amount * gst_hst_rate) / (Decimal('1.0') + gst_hst_rate + (gst_hst_rate * qst_rate))
                gst_amount = gst_amount.quantize(Decimal('0.01'))  # Round to 2 decimal places

                # QST is calculated on the GST-included amount
                qst_amount = ((income.amount - gst_amount) * qst_rate) / (Decimal('1.0') + qst_rate)
                qst_amount = qst_amount.quantize(Decimal('0.01'))  # Round to 2 decimal places

                tax_collected = gst_amount + qst_amount
            else:
                # For other provinces, GST/HST is included in the amount
                # Formula: Tax = Amount - (Amount / (1 + Tax Rate))
                pre_tax_amount = income.amount / (Decimal('1.0') + gst_hst_rate)
                tax_collected = income.amount - pre_tax_amount
                tax_collected = tax_collected.quantize(Decimal('0.01'))  # Round to 2 decimal places

                # Ensure we always have a positive tax value for valid GST/HST rates
                if tax_collected <= 0 and gst_hst_rate > 0:
                    # Recalculate using a direct percentage approach as fallback
                    tax_collected = income.amount * (gst_hst_rate / (Decimal('1.0') + gst_hst_rate))
                    tax_collected = tax_collected.quantize(Decimal('0.01'))  # Round to 2 decimal places

            # Add to total revenue tax
            total_revenue_tax += tax_collected

            writer.writerow([
                income.date.strftime("%Y-%m-%d"),
                f"{income.client} - {income.project}",
                f"{income.amount:.2f}",
                gifi_code,
                gifi_description,
                f"{tax_collected:.2f}",  # Include calculated GST/HST
                income.invoice or ""
            ])
        
        # Add Revenue Total with tax amount
        writer.writerow([
            "",
            "TOTAL REVENUE",
            f"{total_revenue:.2f}",
            "8299",
            "Total revenue",
            f"{total_revenue_tax:.2f}",
            ""
        ])
        
        # Add Expense section header (GIFI 8300-9369)
        writer.writerow([])
        writer.writerow(["EXPENSES (GIFI 8300-9369)"])
        
        # Query expense records for the year
        expense_records = Expense.query
        if year:
            expense_records = expense_records.filter(
                Expense.date.between(datetime(year, 1, 1), datetime(year, 12, 31))
            )
        expense_records = expense_records.order_by(Expense.date).all()
        
        # Write expense data rows with GIFI codes
        total_expenses = Decimal('0.00')
        total_tax = Decimal('0.00')
        
        for expense in expense_records:
            # Map internal category to GIFI code & description
            gifi_code = cls.GIFI_CODE_MAPPING.get(expense.category, "9270")  # Default to "Other expenses"
            gifi_description = expense.category.replace("_", " ").title()
            
            # Add to total expenses
            total_expenses += expense.amount
            
            # Calculate GST/HST/QST amount
            if is_quebec:
                # In Quebec: GST is calculated on the pre-tax amount, QST is calculated on the GST-included amount
                gst_amount = (expense.amount * gst_hst_rate) / (Decimal('1.0') + gst_hst_rate + (gst_hst_rate * qst_rate))
                gst_amount = gst_amount.quantize(Decimal('0.01'))  # Round to 2 decimal places
                
                qst_amount = ((expense.amount + gst_amount) * qst_rate) / (Decimal('1.0') + qst_rate)
                qst_amount = qst_amount.quantize(Decimal('0.01'))  # Round to 2 decimal places
                
                tax_amount = gst_amount + qst_amount
            else:
                # For all other provinces
                tax_amount = (expense.amount * gst_hst_rate) / (Decimal('1.0') + gst_hst_rate)
                tax_amount = tax_amount.quantize(Decimal('0.01'))  # Round to 2 decimal places
            
            # Add to total tax
            total_tax += tax_amount
            
            writer.writerow([
                expense.date.strftime("%Y-%m-%d"),
                expense.title,
                f"{expense.amount:.2f}",
                gifi_code,
                gifi_description,
                f"{tax_amount:.2f}",
                expense.vendor or ""
            ])
        
        # Add Expense Total
        writer.writerow([
            "",
            "TOTAL EXPENSES",
            f"{total_expenses:.2f}",
            "9368",
            "Total expenses",
            f"{total_tax:.2f}",
            ""
        ])
        
        # Add Net Income calculation
        net_income = total_revenue - total_expenses
        writer.writerow([])
        writer.writerow([
            "",
            "NET INCOME (LOSS) BEFORE TAXES",
            f"{net_income:.2f}",
            "9369",
            "Net non-farming income",
            "",
            ""
        ])
        
        # Add Schedule 1 information (Income Tax Reconciliation)
        writer.writerow([])
        writer.writerow(["SCHEDULE 1 - INCOME TAX RECONCILIATION"])
        writer.writerow([
            "Item",
            "Description",
            "Amount",
            "Schedule 1 Line",
            "",
            "",
            ""
        ])
        
        # Net income for accounting
        writer.writerow([
            "A",
            "Net income per financial statements",
            f"{net_income:.2f}",
            "Line A",
            "",
            "",
            ""
        ])
        
        # Convert string buffer to bytes buffer
        bytes_buffer = io.BytesIO()
        bytes_buffer.write(string_buffer.getvalue().encode("utf-8"))
        bytes_buffer.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"T2_GIFI_export_{year}_{timestamp}.csv"
        
        return bytes_buffer, filename
    
    @classmethod
    def export_t2_schedule8_format(cls, year: int) -> Tuple[io.BytesIO, str]:
        """Export data formatted for T2 Schedule 8 (Capital Cost Allowance) for corporate tax returns.
        
        Args:
            year: The tax year to export
            
        Returns:
            Tuple containing the CSV data as BytesIO and the filename
        """
        # Create a string buffer for building the CSV
        string_buffer = io.StringIO()
        writer = csv.writer(string_buffer)
        
        # Write header row for Schedule 8 CCA
        writer.writerow([
            "Asset Class",
            "Description",
            "Date Acquired",
            "Cost",
            "CCA Rate",
            "UCC Start of Year",
            "Additions",
            "Dispositions",
            "UCC End of Year",
            "CCA for Year"
        ])
        
        # In a real implementation, we would pull capital assets and CCA data from the database
        # For now, we're creating a placeholder with some sample CCA classes
        
        # Class 8 - Furniture, fixtures, etc. (20%)
        writer.writerow([
            "8",
            "Furniture and fixtures",
            "",
            "",
            "20%",
            "",
            "",
            "",
            "",
            ""
        ])
        
        # Class 10 - Vehicles, general computer hardware (30%)
        writer.writerow([
            "10",
            "Computer hardware and automotive equipment",
            "",
            "",
            "30%",
            "",
            "",
            "",
            "",
            ""
        ])
        
        # Class 12 - Software and small tools (100%)
        writer.writerow([
            "12",
            "Computer software and small tools",
            "",
            "",
            "100%",
            "",
            "",
            "",
            "",
            ""
        ])
        
        # Class 50 - Computer hardware (55%)
        writer.writerow([
            "50",
            "Computer systems and hardware",
            "",
            "",
            "55%",
            "",
            "",
            "",
            "",
            ""
        ])
        
        # Convert string buffer to bytes buffer
        bytes_buffer = io.BytesIO()
        bytes_buffer.write(string_buffer.getvalue().encode("utf-8"))
        bytes_buffer.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"T2_Schedule8_CCA_{year}_{timestamp}.csv"
        
        return bytes_buffer, filename
        
    @classmethod
    def export_corporate_turbotax_format(cls, year: int, province: str = "Ontario") -> Tuple[io.BytesIO, str]:
        """Export data formatted for corporate TurboTax import.
        
        Args:
            year: The tax year to export
            province: Province for GST/HST calculation (default: Ontario)
            
        Returns:
            Tuple containing the CSV data as BytesIO and the filename
        """
        # Create a string buffer for building the CSV
        string_buffer = io.StringIO()
        writer = csv.writer(string_buffer)
        
        # Determine if province is Quebec for special handling
        is_quebec = province == "Quebec"
        
        # Get GST/HST rate for the province and convert to Decimal
        gst_hst_rate_float = GST_HST_RATES.get(province, 0.05)  # Default to 5% if not found
        gst_hst_rate = Decimal(str(gst_hst_rate_float))  # Convert float to Decimal
        
        # For Quebec, also get QST rate
        if is_quebec:
            qst_rate = Decimal(str(QST_RATE))
        else:
            qst_rate = Decimal('0')
            
        # Corporate TurboTax header with GIFI codes
        tax_column = "GST/HST" if not is_quebec else "GST/QST"
        writer.writerow([
            "Date",
            "Description",
            "Amount",
            "Category",
            "GIFI Code",
            tax_column,
            "Tax Form",
            "Reference"
        ])
        
        # Query expense records for the year
        expense_records = Expense.query
        if year:
            expense_records = expense_records.filter(
                Expense.date.between(datetime(year, 1, 1), datetime(year, 12, 31))
            )
        expense_records = expense_records.order_by(Expense.date).all()
        
        # Write expense data rows
        for expense in expense_records:
            # Map internal category to GIFI code
            gifi_code = cls.GIFI_CODE_MAPPING.get(expense.category, "9270")  # Default to "Other expenses"
            
            # Calculate GST/HST/QST amount
            if is_quebec:
                # In Quebec: GST is calculated on the pre-tax amount, QST is calculated on the GST-included amount
                gst_amount = (expense.amount * gst_hst_rate) / (Decimal('1.0') + gst_hst_rate + (gst_hst_rate * qst_rate))
                gst_amount = gst_amount.quantize(Decimal('0.01'))  # Round to 2 decimal places
                
                qst_amount = ((expense.amount + gst_amount) * qst_rate) / (Decimal('1.0') + qst_rate)
                qst_amount = qst_amount.quantize(Decimal('0.01'))  # Round to 2 decimal places
                
                tax_amount = gst_amount + qst_amount
            else:
                # For all other provinces
                tax_amount = (expense.amount * gst_hst_rate) / (Decimal('1.0') + gst_hst_rate)
                tax_amount = tax_amount.quantize(Decimal('0.01'))  # Round to 2 decimal places
                
            writer.writerow([
                expense.date.strftime("%Y-%m-%d"),
                expense.title,
                f"{expense.amount:.2f}",
                expense.category,
                gifi_code,
                f"{tax_amount:.2f}",
                "T2",
                expense.vendor or ""
            ])
        
        # Add income data
        income_records = Income.query
        if year:
            from_date = datetime(year, 1, 1)
            to_date = datetime(year, 12, 31)
            print(f"Querying income records between {from_date} and {to_date}")
            income_records = income_records.filter(
                Income.date.between(from_date, to_date)
            )

        # Debug the query
        print(f"Income query: {income_records}")

        # Get all records
        income_records = income_records.order_by(Income.date).all()

        # Debug found records
        print(f"Found {len(income_records)} income records: {income_records}")
        
        # Initialize the tax total
        total_revenue_tax = Decimal('0.00')

        # Write income data rows - with corporate revenue GIFI code
        for income in income_records:
            # For corporate income, use appropriate GIFI code
            gifi_code = cls.GIFI_CODE_MAPPING.get("professional_income", "8020")
            
            # Calculate GST/HST included in the income amount
            if is_quebec:
                # For Quebec, calculate GST and QST separately
                # GST is 5% of the pre-tax amount
                gst_amount = (income.amount * gst_hst_rate) / (Decimal('1.0') + gst_hst_rate + (gst_hst_rate * qst_rate))
                gst_amount = gst_amount.quantize(Decimal('0.01'))  # Round to 2 decimal places

                # QST is calculated on the GST-included amount
                qst_amount = ((income.amount - gst_amount) * qst_rate) / (Decimal('1.0') + qst_rate)
                qst_amount = qst_amount.quantize(Decimal('0.01'))  # Round to 2 decimal places

                tax_collected = gst_amount + qst_amount
            else:
                # For other provinces, GST/HST is included in the amount
                # Formula: Tax = Amount - (Amount / (1 + Tax Rate))
                pre_tax_amount = income.amount / (Decimal('1.0') + gst_hst_rate)
                tax_collected = income.amount - pre_tax_amount
                tax_collected = tax_collected.quantize(Decimal('0.01'))  # Round to 2 decimal places

                # Ensure we always have a positive tax value for valid GST/HST rates
                if tax_collected <= 0 and gst_hst_rate > 0:
                    # Recalculate using a direct percentage approach as fallback
                    tax_collected = income.amount * (gst_hst_rate / (Decimal('1.0') + gst_hst_rate))
                    tax_collected = tax_collected.quantize(Decimal('0.01'))  # Round to 2 decimal places

            # Add to total revenue tax
            total_revenue_tax += tax_collected

            writer.writerow([
                income.date.strftime("%Y-%m-%d"),
                f"{income.client} - {income.project}",
                f"{income.amount:.2f}",
                "Professional Income",
                gifi_code,
                f"{tax_collected:.2f}",  # Include calculated GST/HST
                "T2",
                income.invoice or ""
            ])
        
        # Convert string buffer to bytes buffer
        bytes_buffer = io.BytesIO()
        bytes_buffer.write(string_buffer.getvalue().encode("utf-8"))
        bytes_buffer.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Corporate_TurboTax_{year}_{timestamp}.csv"
        
        return bytes_buffer, filename