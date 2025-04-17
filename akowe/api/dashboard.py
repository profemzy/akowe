from datetime import datetime
from decimal import Decimal

from flask import Blueprint, render_template, request
from sqlalchemy import func, extract

from akowe.models.expense import Expense
from akowe.models.income import Income

bp = Blueprint("dashboard", __name__, url_prefix="/")


@bp.route("/", methods=["GET"])
def index():
    # Get current year and selected year from query param
    current_year = datetime.now().year
    selected_year = request.args.get("year", type=int, default=current_year)

    # Calculate total income and expense (all years)
    all_time_income = Income.query.with_entities(func.sum(Income.amount)).scalar() or Decimal(
        "0.00"
    )

    all_time_expense = Expense.query.with_entities(func.sum(Expense.amount)).scalar() or Decimal(
        "0.00"
    )

    # Calculate income and expense for the selected year
    year_income = Income.query.filter(extract("year", Income.date) == selected_year).with_entities(
        func.sum(Income.amount)
    ).scalar() or Decimal("0.00")

    year_expense = Expense.query.filter(
        extract("year", Expense.date) == selected_year
    ).with_entities(func.sum(Expense.amount)).scalar() or Decimal("0.00")

    # Get recent income and expense records
    recent_income = Income.query.order_by(Income.date.desc()).limit(5).all()
    recent_expenses = Expense.query.order_by(Expense.date.desc()).limit(5).all()

    # Get monthly income and expense for the selected year
    monthly_income = (
        Income.query.filter(extract("year", Income.date) == selected_year)
        .with_entities(
            extract("month", Income.date).label("month"), func.sum(Income.amount).label("amount")
        )
        .group_by("month")
        .all()
    )

    monthly_expenses = (
        Expense.query.filter(extract("year", Expense.date) == selected_year)
        .with_entities(
            extract("month", Expense.date).label("month"), func.sum(Expense.amount).label("amount")
        )
        .group_by("month")
        .all()
    )

    # Get expenses by category for the selected year
    expenses_by_category = (
        Expense.query.filter(extract("year", Expense.date) == selected_year)
        .with_entities(Expense.category, func.sum(Expense.amount).label("amount"))
        .group_by(Expense.category)
        .all()
    )

    # Calculate profits
    all_time_profit = all_time_income - all_time_expense
    year_profit = year_income - year_expense

    # Get available years for dropdown
    income_years = [
        year[0]
        for year in Income.query.with_entities(extract("year", Income.date)).distinct().all()
    ]
    expense_years = [
        year[0]
        for year in Expense.query.with_entities(extract("year", Expense.date)).distinct().all()
    ]

    available_years = sorted(set(income_years + expense_years), reverse=True)

    # Format data for charts
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_income_data = [0] * 12
    monthly_expense_data = [0] * 12

    for item in monthly_income:
        monthly_income_data[int(item.month) - 1] = float(item.amount)

    for item in monthly_expenses:
        monthly_expense_data[int(item.month) - 1] = float(item.amount)

    category_labels = [item.category for item in expenses_by_category]
    category_data = [float(item.amount) for item in expenses_by_category]

    return render_template(
        "dashboard/index.html",
        all_time_income=all_time_income,
        all_time_expense=all_time_expense,
        all_time_profit=all_time_profit,
        year_income=year_income,
        year_expense=year_expense,
        year_profit=year_profit,
        recent_income=recent_income,
        recent_expenses=recent_expenses,
        months=months,
        monthly_income_data=monthly_income_data,
        monthly_expense_data=monthly_expense_data,
        category_labels=category_labels,
        category_data=category_data,
        selected_year=selected_year,
        available_years=available_years,
    )
