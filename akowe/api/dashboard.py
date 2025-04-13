from flask import Blueprint, render_template
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from decimal import Decimal

from akowe.models.income import Income
from akowe.models.expense import Expense

bp = Blueprint('dashboard', __name__, url_prefix='/')

@bp.route('/', methods=['GET'])
def index():
    # Get current year
    current_year = datetime.now().year
    
    # Calculate total income and expense for the current year
    total_income = Income.query.filter(
        extract('year', Income.date) == current_year
    ).with_entities(
        func.sum(Income.amount)
    ).scalar() or Decimal('0.00')
    
    total_expense = Expense.query.filter(
        extract('year', Expense.date) == current_year
    ).with_entities(
        func.sum(Expense.amount)
    ).scalar() or Decimal('0.00')
    
    # Get recent income and expense records
    recent_income = Income.query.order_by(Income.date.desc()).limit(5).all()
    recent_expenses = Expense.query.order_by(Expense.date.desc()).limit(5).all()
    
    # Get monthly income and expense for the current year
    monthly_income = Income.query.filter(
        extract('year', Income.date) == current_year
    ).with_entities(
        extract('month', Income.date).label('month'),
        func.sum(Income.amount).label('amount')
    ).group_by('month').all()
    
    monthly_expenses = Expense.query.filter(
        extract('year', Expense.date) == current_year
    ).with_entities(
        extract('month', Expense.date).label('month'),
        func.sum(Expense.amount).label('amount')
    ).group_by('month').all()
    
    # Get expenses by category for the current year
    expenses_by_category = Expense.query.filter(
        extract('year', Expense.date) == current_year
    ).with_entities(
        Expense.category,
        func.sum(Expense.amount).label('amount')
    ).group_by(Expense.category).all()
    
    # Calculate profits
    profit = total_income - total_expense
    
    # Format data for charts
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_income_data = [0] * 12
    monthly_expense_data = [0] * 12
    
    for item in monthly_income:
        monthly_income_data[int(item.month) - 1] = float(item.amount)
    
    for item in monthly_expenses:
        monthly_expense_data[int(item.month) - 1] = float(item.amount)
    
    category_labels = [item.category for item in expenses_by_category]
    category_data = [float(item.amount) for item in expenses_by_category]
    
    return render_template('dashboard/index.html',
                          total_income=total_income,
                          total_expense=total_expense,
                          profit=profit,
                          recent_income=recent_income,
                          recent_expenses=recent_expenses,
                          months=months,
                          monthly_income_data=monthly_income_data,
                          monthly_expense_data=monthly_expense_data,
                          category_labels=category_labels,
                          category_data=category_data,
                          current_year=current_year)