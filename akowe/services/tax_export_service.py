"""Service for exporting financial data in tax preparation formats.

IMPORTANT: This service assumes that all income amounts in the database INCLUDE
applicable GST/HST/QST. When exporting for tax purposes, the service automatically
calculates the tax portion based on the province's tax rates.

For example, in Ontario with 13% HST:
- If a client was invoiced $1,130 (including 13% HST)
- The income record would store $1,130
- The export would show $1,130 as income and $130 as HST collected

This approach ensures accurate tax reporting for GST/HST remittance.
"""

import csv
import io
import json
from datetime import datetime
from typing import Tuple, Dict, List, Optional, Union
from decimal import Decimal

from akowe.models.expense import Expense
from akowe.models.income import Income
from akowe.app.tax_dashboard import CRA_TAX_CATEGORIES, GST_HST_RATES, QST_RATE


class TaxExportService:
    """Service for exporting financial data in formats compatible with tax preparation software."""
    
    # CRA category mappings from internal categories to T2125 form fields
    CRA_CATEGORY_MAPPING = {
        # Capital expenses
        "hardware": "Computer, equipment, and phone costs",
        "software": "Computer, equipment, and phone costs",
        "computer_equipment": "Computer, equipment, and phone costs",
        "furniture": "Capital equipment",
        "vehicle": "Motor vehicle expenses",

        # Operating expenses
        "advertising": "Advertising",
        "marketing": "Advertising",
        "meals_entertainment": "Meals and entertainment",
        "food": "Meals and entertainment",
        "entertainment": "Meals and entertainment",
        "bad_debts": "Bad debts",
        "insurance": "Insurance",
        "interest": "Interest",
        "bank_charges": "Bank charges",
        "business_tax": "Business taxes, fees, licenses, dues",
        "taxes": "Business taxes, fees, licenses, dues",
        "licenses": "Business taxes, fees, licenses, dues",
        "dues": "Business taxes, fees, licenses, dues",
        "office_supplies": "Office expenses",
        "supplies": "Supplies",
        "professional_fees": "Professional fees",
        "professional_services": "Professional fees",
        "legal": "Legal, accounting, and other professional fees",
        "accounting": "Professional fees",
        "rent": "Rent",
        "repairs": "Maintenance and repairs",
        "maintenance": "Maintenance and repairs",
        "salaries": "Salaries, wages, and benefits",
        "travel": "Travel",
        "utilities": "Utilities",
        "telephone": "Telephone and utilities",
        "internet": "Telephone and utilities",
        "vehicle_expenses": "Motor vehicle expenses",
        "fuel": "Motor vehicle expenses",
        "home_office": "Home office expenses",
        "subscription": "Subscriptions",
        "training": "Other expenses",
        "memberships": "Business taxes, fees, licenses, dues",
        "other": "Other expenses",
    }
    
    # Map Akowe categories to TurboTax categories
    TURBOTAX_CATEGORY_MAPPING = {
        # Capital expenses
        "hardware": "Equipment under $500",
        "software": "Software expenses",
        "computer_equipment": "Equipment: Computer hardware",
        "furniture": "Equipment: Office furniture",
        "vehicle": "Motor vehicle expenses",

        # Operating expenses
        "advertising": "Advertising",
        "marketing": "Advertising",
        "meals_entertainment": "Meals and entertainment",
        "food": "Meals and entertainment",
        "entertainment": "Meals and entertainment",
        "bad_debts": "Bad debts",
        "insurance": "Insurance",
        "interest": "Interest",
        "bank_charges": "Business expenses: Bank charges",
        "business_tax": "Licenses, dues, memberships, subscriptions",
        "taxes": "Business taxes, fees",
        "licenses": "Licenses, dues, memberships, subscriptions",
        "dues": "Licenses, dues, memberships, subscriptions",
        "office_supplies": "Office expenses",
        "supplies": "Supplies",
        "professional_fees": "Professional fees",
        "professional_services": "Professional fees",
        "legal": "Legal and professional fees",
        "accounting": "Accounting and legal fees",
        "rent": "Rent",
        "repairs": "Repairs and maintenance",
        "maintenance": "Repairs and maintenance",
        "salaries": "Salaries, wages, and benefits",
        "travel": "Travel expenses",
        "utilities": "Utilities",
        "telephone": "Business expenses: Telephone and utilities",
        "internet": "Business expenses: Internet",
        "vehicle_expenses": "Motor vehicle expenses",
        "fuel": "Motor vehicle expenses: Fuel",
        "home_office": "Business-use-of-home expenses",
        "subscription": "Licenses, dues, memberships, subscriptions",
        "training": "Professional development",
        "memberships": "Licenses, dues, memberships, subscriptions",
        "other": "Other business expenses",
    }
    
    # Map Akowe categories to Wealthsimple Tax categories
    WEALTHSIMPLE_CATEGORY_MAPPING = {
        # Capital expenses
        "hardware": "Capital equipment",
        "software": "Software",
        "computer_equipment": "Capital equipment",
        "furniture": "Capital equipment",
        "vehicle": "Motor vehicle expenses",

        # Operating expenses
        "advertising": "Advertising",
        "marketing": "Advertising",
        "meals_entertainment": "Meals and entertainment",
        "food": "Meals and entertainment",
        "entertainment": "Meals and entertainment",
        "bad_debts": "Bad debts",
        "insurance": "Insurance",
        "interest": "Interest",
        "bank_charges": "Bank charges",
        "business_tax": "Business tax, fees, licenses, dues",
        "taxes": "Business tax, fees, licenses, dues",
        "licenses": "Business tax, fees, licenses, dues",
        "dues": "Business tax, fees, licenses, dues",
        "office_supplies": "Office expenses",
        "supplies": "Supplies",
        "professional_fees": "Professional fees",
        "professional_services": "Professional fees",
        "legal": "Legal expenses",
        "accounting": "Accounting fees",
        "rent": "Rent",
        "repairs": "Repairs and maintenance",
        "maintenance": "Repairs and maintenance",
        "salaries": "Salaries and wages",
        "travel": "Travel",
        "utilities": "Utilities",
        "telephone": "Telephone and internet",
        "internet": "Telephone and internet",
        "vehicle_expenses": "Motor vehicle expenses",
        "fuel": "Motor vehicle expenses",
        "home_office": "Business-use-of-home expenses",
        "subscription": "Subscriptions",
        "training": "Training",
        "memberships": "Membership dues",
        "other": "Other expenses",
    }
    
    @classmethod
    def export_t2125_format(cls, year: int, province: str = "Ontario") -> Tuple[io.BytesIO, str]:
        """Export data formatted specifically for CRA T2125 form.
        
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

        # Write header row with T2125 categories
        tax_column = "GST/HST Paid" if not is_quebec else "GST/QST Paid"
        writer.writerow([
            "Date",
            "Description",
            "Amount",
            "T2125 Category",
            tax_column,
            "Receipt Reference"
        ])
        if is_quebec:
            qst_rate = Decimal(str(QST_RATE))
        else:
            qst_rate = Decimal('0')

        # Query expense records for the year
        expense_records = Expense.query
        if year:
            expense_records = expense_records.filter(
                Expense.date.between(datetime(year, 1, 1), datetime(year, 12, 31))
            )
        expense_records = expense_records.order_by(Expense.date).all()
        
        # Write data rows
        for expense in expense_records:
            # Map internal category to T2125 category
            t2125_category = cls.CRA_CATEGORY_MAPPING.get(expense.category, "Other expenses")
            
            # Calculate estimated GST/HST amount
            # In a real implementation, this might come from the database if tracked separately
            if is_quebec:
                # In Quebec: GST is calculated on the pre-tax amount, QST is calculated on the GST-included amount
                gst_amount = (expense.amount * gst_hst_rate) / (Decimal('1.0') + gst_hst_rate + (gst_hst_rate * qst_rate))
                gst_amount = gst_amount.quantize(Decimal('0.01'))  # Round to 2 decimal places

                # QST is calculated on the GST-included amount but not in this export (would be in a separate column)
                # For simplicity, including it in the GST/HST column for this export
                qst_amount = ((expense.amount + gst_amount) * qst_rate) / (Decimal('1.0') + qst_rate)
                qst_amount = qst_amount.quantize(Decimal('0.01'))  # Round to 2 decimal places

                gst_hst_amount = gst_amount + qst_amount
            else:
                # For all other provinces
                gst_hst_amount = (expense.amount * gst_hst_rate) / (Decimal('1.0') + gst_hst_rate)
                gst_hst_amount = gst_hst_amount.quantize(Decimal('0.01'))  # Round to 2 decimal places
            
            writer.writerow([
                expense.date.strftime("%Y-%m-%d"),
                expense.title,
                f"{expense.amount:.2f}",
                t2125_category,
                f"{gst_hst_amount:.2f}",
                expense.vendor or ""
            ])
        
        # Now add income data
        income_records = Income.query
        if year:
            income_records = income_records.filter(
                Income.date.between(datetime(year, 1, 1), datetime(year, 12, 31))
            )
        income_records = income_records.order_by(Income.date).all()
        
        writer.writerow([])  # Add a blank row as separator
        writer.writerow(["INCOME SECTION"])
        # Reuse is_quebec variable from earlier in the method
        tax_collected_column = "GST/HST Collected" if not is_quebec else "GST/QST Collected"
        writer.writerow([
            "Date",
            "Description",
            "Amount",
            "T2125 Income Type",
            tax_collected_column,
            "Reference"
        ])
        
        for income in income_records:
            # For income, calculate GST/HST included in the total (13% in Ontario by default)
            # The amount in the database is assumed to include taxes

            # Calculate GST/HST included in the income amount
            if is_quebec:
                # For Quebec, calculate GST and QST separately
                # GST is 5% of the pre-tax amount
                # Formula: GST = Amount / (1 + GST + QST) * GST
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

            writer.writerow([
                income.date.strftime("%Y-%m-%d"),
                f"{income.client} - {income.project}",
                f"{income.amount:.2f}",
                "Professional income",
                f"{tax_collected:.2f}",  # GST/HST collected from clients
                income.invoice or ""
            ])
        
        # Convert string buffer to bytes buffer
        bytes_buffer = io.BytesIO()
        bytes_buffer.write(string_buffer.getvalue().encode("utf-8"))
        bytes_buffer.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"T2125_CRA_export_{year}_{timestamp}.csv"
        
        return bytes_buffer, filename
    
    @classmethod
    def export_turbotax_format(cls, year: int, province: str = "Ontario") -> Tuple[io.BytesIO, str]:
        """Export data formatted for TurboTax import.

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

        # TurboTax header - modify header based on province
        tax_column = "GST/HST" if not is_quebec else "GST/QST"
        writer.writerow([
            "Date",
            "Description",
            "Amount",
            "Category",
            tax_column,
            "Tax Form",
            "TurboTax Category"
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
            # Map internal category to TurboTax category
            turbotax_category = cls.TURBOTAX_CATEGORY_MAPPING.get(expense.category, "Other business expenses")
            
            # Calculate GST/HST/QST amount if needed
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
                f"{tax_amount:.2f}",
                "T2125",
                turbotax_category
            ])
        
        # Add income data
        income_records = Income.query
        if year:
            income_records = income_records.filter(
                Income.date.between(datetime(year, 1, 1), datetime(year, 12, 31))
            )
        income_records = income_records.order_by(Income.date).all()
        
        # Write income data rows
        for income in income_records:
            # Calculate GST/HST included in the income amount
            if is_quebec:
                # For Quebec, calculate GST and QST separately
                # GST is 5% of the pre-tax amount
                # Formula: GST = Amount / (1 + GST + QST) * GST
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

            writer.writerow([
                income.date.strftime("%Y-%m-%d"),
                f"{income.client} - {income.project}",
                f"{income.amount:.2f}",
                "Income",
                f"{tax_collected:.2f}",  # GST/HST collected for tax reporting
                "T2125",
                "Self-employment income"
            ])
        
        # Convert string buffer to bytes buffer
        bytes_buffer = io.BytesIO()
        bytes_buffer.write(string_buffer.getvalue().encode("utf-8"))
        bytes_buffer.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"TurboTax_export_{year}_{timestamp}.csv"
        
        return bytes_buffer, filename
    
    @classmethod
    def export_wealthsimple_format(cls, year: int, province: str = "Ontario") -> Tuple[io.BytesIO, str]:
        """Export data formatted for Wealthsimple Tax (SimpleTax) import.

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

        # Wealthsimple Tax header - modify header based on province
        tax_column = "GST/HST" if not is_quebec else "GST/QST"
        writer.writerow([
            "Date",
            "Description",
            "Amount",
            "Category",
            tax_column,
            "Type"
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
            # Map internal category to Wealthsimple category
            wealthsimple_category = cls.WEALTHSIMPLE_CATEGORY_MAPPING.get(expense.category, "Other expenses")
            
            # Calculate GST/HST/QST amount if needed
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
                wealthsimple_category,
                f"{tax_amount:.2f}",
                "Expense"
            ])
        
        # Add income data
        income_records = Income.query
        if year:
            income_records = income_records.filter(
                Income.date.between(datetime(year, 1, 1), datetime(year, 12, 31))
            )
        income_records = income_records.order_by(Income.date).all()
        
        # Write income data rows
        for income in income_records:
            # Calculate GST/HST included in the income amount
            if is_quebec:
                # For Quebec, calculate GST and QST separately
                # GST is 5% of the pre-tax amount
                # Formula: GST = Amount / (1 + GST + QST) * GST
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

            writer.writerow([
                income.date.strftime("%Y-%m-%d"),
                f"{income.client} - {income.project}",
                f"{income.amount:.2f}",
                "Self-employment",
                f"{tax_collected:.2f}",  # GST/HST collected for tax reporting
                "Income"
            ])
        
        # Convert string buffer to bytes buffer
        bytes_buffer = io.BytesIO()
        bytes_buffer.write(string_buffer.getvalue().encode("utf-8"))
        bytes_buffer.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"WealthsimpleTax_export_{year}_{timestamp}.csv"
        
        return bytes_buffer, filename