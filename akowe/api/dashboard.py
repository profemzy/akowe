from flask import Blueprint, render_template, request
from sqlalchemy import func, extract, and_, or_
from datetime import datetime, timedelta, date
from decimal import Decimal
from calendar import month_name

from akowe.models.income import Income
from akowe.models.expense import Expense

bp = Blueprint('dashboard', __name__, url_prefix='/')

def get_fiscal_year_bounds(year):
    """Return start and end date for fiscal year (Dec 1 to Nov 30)."""
    start_date = date(year - 1, 12, 1)  # Dec 1 of previous year
    end_date = date(year, 11, 30)       # Nov 30 of current year
    return start_date, end_date

@bp.route('/', methods=['GET'])
def index():
    # Get current year and selected year from query param
    current_year = datetime.now().year
    selected_year = request.args.get('year', type=int, default=current_year)
    
    # Get fiscal year bounds for the selected year
    start_date, end_date = get_fiscal_year_bounds(selected_year)
    fiscal_year_label = f"{selected_year-1}-{selected_year}"
    
    # Calculate total income and expense for all time
    all_time_income = Income.query.with_entities(
        func.sum(Income.amount)
    ).scalar() or Decimal('0.00')
    
    all_time_expense = Expense.query.with_entities(
        func.sum(Expense.amount)
    ).scalar() or Decimal('0.00')
    
    # Calculate income and expense for the selected fiscal year
    fiscal_income = Income.query.filter(
        Income.date.between(start_date, end_date)
    ).with_entities(
        func.sum(Income.amount)
    ).scalar() or Decimal('0.00')
    
    fiscal_expense = Expense.query.filter(
        Expense.date.between(start_date, end_date)
    ).with_entities(
        func.sum(Expense.amount)
    ).scalar() or Decimal('0.00')
    
    # Get recent income and expense records
    recent_income = Income.query.order_by(Income.date.desc()).limit(5).all()
    recent_expenses = Expense.query.order_by(Expense.date.desc()).limit(5).all()
    
    # Get monthly income and expense for the selected fiscal year
    monthly_data = []
    
    # Start from December of previous year
    for month_offset in range(12):
        # Calculate the month (1-12) and year for this offset
        month = ((12 + month_offset) % 12) + 1  # 12, 1, 2, ..., 11
        year = selected_year - 1 if month == 12 else selected_year
        
        # Month start and end dates
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year, month, 31)
        elif month == 2:
            if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):  # Leap year check
                month_end = date(year, month, 29)
            else:
                month_end = date(year, month, 28)
        elif month in [4, 6, 9, 11]:
            month_end = date(year, month, 30)
        else:
            month_end = date(year, month, 31)
        
        # Query for this month's income and expense
        month_income = Income.query.filter(
            Income.date.between(month_start, month_end)
        ).with_entities(
            func.sum(Income.amount)
        ).scalar() or Decimal('0.00')
        
        month_expense = Expense.query.filter(
            Expense.date.between(month_start, month_end)
        ).with_entities(
            func.sum(Expense.amount)
        ).scalar() or Decimal('0.00')
        
        month_name_abbr = month_name[month][:3]
        if month == 12:
            month_name_abbr = f"{month_name_abbr} ({year})"
        
        monthly_data.append({
            'month': month,
            'month_name': month_name_abbr,
            'income': float(month_income),
            'expense': float(month_expense)
        })
    
    # Get expenses by category for the fiscal year
    expenses_by_category = Expense.query.filter(
        Expense.date.between(start_date, end_date)
    ).with_entities(
        Expense.category,
        func.sum(Expense.amount).label('amount')
    ).group_by(Expense.category).all()
    
    # Calculate profits
    all_time_profit = all_time_income - all_time_expense
    fiscal_profit = fiscal_income - fiscal_expense
    
    # Available fiscal years for selection (based on data)
    min_date = None
    max_date = None
    
    min_income_date = Income.query.order_by(Income.date).first()
    min_expense_date = Expense.query.order_by(Expense.date).first()
    
    if min_income_date and min_expense_date:
        min_date = min(min_income_date.date, min_expense_date.date)
    elif min_income_date:
        min_date = min_income_date.date
    elif min_expense_date:
        min_date = min_expense_date.date
    
    max_income_date = Income.query.order_by(Income.date.desc()).first()
    max_expense_date = Expense.query.order_by(Expense.date.desc()).first()
    
    if max_income_date and max_expense_date:
        max_date = max(max_income_date.date, max_expense_date.date)
    elif max_income_date:
        max_date = max_income_date.date
    elif max_expense_date:
        max_date = max_expense_date.date
    
    available_years = []
    if min_date and max_date:
        min_fiscal_year = min_date.year + (1 if min_date.month < 12 else 0)
        max_fiscal_year = max_date.year + (1 if max_date.month >= 12 else 0)
        available_years = list(range(min_fiscal_year, max_fiscal_year + 1))
    
    # Format data for charts
    months = [item['month_name'] for item in monthly_data]
    monthly_income_data = [item['income'] for item in monthly_data]
    monthly_expense_data = [item['expense'] for item in monthly_data]
    
    category_labels = [item.category for item in expenses_by_category]
    category_data = [float(item.amount) for item in expenses_by_category]
    
    return render_template('dashboard/index.html',
                          all_time_income=all_time_income,
                          all_time_expense=all_time_expense,
                          all_time_profit=all_time_profit,
                          fiscal_income=fiscal_income,
                          fiscal_expense=fiscal_expense,
                          fiscal_profit=fiscal_profit,
                          fiscal_year_label=fiscal_year_label,
                          recent_income=recent_income,
                          recent_expenses=recent_expenses,
                          months=months,
                          monthly_income_data=monthly_income_data,
                          monthly_expense_data=monthly_expense_data,
                          category_labels=category_labels,
                          category_data=category_data,
                          selected_year=selected_year,
                          available_years=available_years)