import os
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps

from flask import Blueprint, request, jsonify, current_app, g
from flask_login import current_user
from sqlalchemy import extract

from akowe.models import db
from akowe.models.expense import Expense
from akowe.models.income import Income
from akowe.api.mobile_api import token_required
from akowe.services.tax_prediction_service import TaxPredictionService
from akowe.services.tax_recommendation_service import TaxRecommendationService
from akowe.app.tax_dashboard import CRA_TAX_CATEGORIES, GST_HST_RATES, TAX_QUARTERS, CCA_CLASSES

bp = Blueprint("mobile_tax", __name__, url_prefix="/api/tax")


@bp.route("/dashboard", methods=["GET"])
@token_required
def get_tax_dashboard():
    """Get tax dashboard data"""
    # Get current year and selected year from query param
    current_year = datetime.now().year
    selected_year = request.args.get("year", type=int, default=current_year)
    
    # Get selected province for tax calculations
    selected_province = request.args.get("province", default="Ontario")
    
    # Calculate year date range
    year_start_date = datetime(selected_year, 1, 1).date()
    year_end_date = datetime(selected_year, 12, 31).date()
    
    # Get expenses and income for the year
    yearly_expenses = Expense.query.filter(
        Expense.user_id == g.current_user.id,
        Expense.date >= year_start_date, 
        Expense.date <= year_end_date
    ).all()
    
    yearly_income = Income.query.filter(
        Income.user_id == g.current_user.id,
        Income.date >= year_start_date, 
        Income.date <= year_end_date
    ).all()
    
    # Calculate totals
    total_yearly_expense = sum(expense.amount for expense in yearly_expenses)
    total_yearly_income = sum(income.amount for income in yearly_income)
    yearly_net_income = total_yearly_income - total_yearly_expense
    
    # Get tax prediction data if it's the current year
    tax_prediction = None
    if selected_year == current_year:
        tax_prediction = TaxPredictionService.predict_tax_obligation(
            yearly_income, yearly_expenses, selected_province, selected_year
        )
    
    # Prepare expense data by tax categories for CRA
    cra_expense_categories = {}
    for category, tax_category in CRA_TAX_CATEGORIES.items():
        if tax_category not in cra_expense_categories:
            cra_expense_categories[tax_category] = {
                "amount": Decimal("0"),
                "categories": [],
                "expense_count": 0
            }
        cra_expense_categories[tax_category]["categories"].append(category)
    
    # Populate tax categories with expense data
    for expense in yearly_expenses:
        cra_category = CRA_TAX_CATEGORIES.get(expense.category, "Other Expenses")
        cra_expense_categories[cra_category]["amount"] += expense.amount
        cra_expense_categories[cra_category]["expense_count"] += 1
    
    # Format CRA categories for output
    formatted_cra_categories = []
    for tax_category, data in cra_expense_categories.items():
        if data["expense_count"] > 0:
            formatted_cra_categories.append({
                "tax_category": tax_category,
                "amount": str(data["amount"]),
                "categories": data["categories"],
                "expense_count": data["expense_count"],
                "percentage": str(data["amount"] / total_yearly_expense * 100) if total_yearly_expense else "0"
            })
    
    # Sort by amount (descending)
    formatted_cra_categories.sort(key=lambda x: Decimal(x["amount"]), reverse=True)
    
    # Get quarterly data for GST/HST reporting
    quarterly_data = {}
    for quarter_num, quarter_info in TAX_QUARTERS.items():
        start_month = quarter_info["start_month"]
        end_month = quarter_info["end_month"]
        
        quarter_start = datetime(selected_year, start_month, 1).date()
        if end_month == 12:
            quarter_end = datetime(selected_year, 12, 31).date()
        else:
            quarter_end = datetime(selected_year, end_month + 1, 1).date() - timedelta(days=1)
        
        quarter_expenses = Expense.query.filter(
            Expense.user_id == g.current_user.id,
            Expense.date >= quarter_start, 
            Expense.date <= quarter_end
        ).all()
        
        quarter_income = Income.query.filter(
            Income.user_id == g.current_user.id,
            Income.date >= quarter_start, 
            Income.date <= quarter_end
        ).all()
        
        quarter_expense_total = sum(expense.amount for expense in quarter_expenses)
        quarter_income_total = sum(income.amount for income in quarter_income)
        
        quarterly_data[quarter_info["name"]] = {
            "expenses": str(quarter_expense_total),
            "income": str(quarter_income_total),
            "net": str(quarter_income_total - quarter_expense_total),
            "start_date": quarter_start.isoformat(),
            "end_date": quarter_end.isoformat()
        }
    
    # Calculate GST/HST collected and paid (input tax credits)
    gst_hst_rate = GST_HST_RATES.get(selected_province, 0.05)
    
    # Calculate GST/HST collected on income (simplified)
    gst_hst_collected = total_yearly_income * Decimal(str(gst_hst_rate))
    
    # Calculate GST/HST paid on expenses (input tax credits)
    # This is a simplified calculation - in reality, not all expenses have GST/HST
    gst_hst_paid = (
        total_yearly_expense
        * Decimal(str(gst_hst_rate))
        / (Decimal("1") + Decimal(str(gst_hst_rate)))
    )
    
    # Calculate net GST/HST owing
    gst_hst_owing = gst_hst_collected - gst_hst_paid
    
    # Identify potential Capital Cost Allowance (CCA) items
    cca_items = []
    for expense in yearly_expenses:
        if expense.category in ["hardware", "software"]:
            # Determine CCA class based on expense category and amount
            cca_class = "Class 12"  # Default: software and items under $500
            
            if expense.category == "hardware" and expense.amount > 500:
                cca_class = "Class 50"  # Computer hardware > $500
            
            cca_items.append({
                "id": expense.id,
                "date": expense.date.isoformat(),
                "title": expense.title,
                "amount": str(expense.amount),
                "category": expense.category,
                "cca_class": cca_class,
                "cca_rate": str(CCA_CLASSES[cca_class]["rate"]),
                "deduction": str(expense.amount * Decimal(str(CCA_CLASSES[cca_class]["rate"])))
            })
    
    # Get available years for dropdown
    income_years = [
        year[0]
        for year in Income.query.with_entities(extract("year", Income.date))
        .filter(Income.user_id == g.current_user.id)
        .distinct().all()
    ]
    expense_years = [
        year[0]
        for year in Expense.query.with_entities(extract("year", Expense.date))
        .filter(Expense.user_id == g.current_user.id)
        .distinct().all()
    ]
    
    available_years = sorted(set(income_years + expense_years), reverse=True)
    
    # Tax deadlines and key dates for the selected year
    tax_deadlines = [
        {
            "date": f"April 30, {selected_year + 1}",
            "description": f"Deadline to file and pay {selected_year} personal income taxes",
            "is_passed": datetime.now().date() > datetime(selected_year + 1, 4, 30).date(),
        },
        {
            "date": f"June 15, {selected_year + 1}",
            "description": f"Deadline to file {selected_year} self-employed income taxes (payment still due April 30)",
            "is_passed": datetime.now().date() > datetime(selected_year + 1, 6, 15).date(),
        },
        {
            "date": f"March 15, {selected_year}",
            "description": f"First quarterly tax installment payment for {selected_year}",
            "is_passed": datetime.now().date() > datetime(selected_year, 3, 15).date(),
        },
        {
            "date": f"June 15, {selected_year}",
            "description": f"Second quarterly tax installment payment for {selected_year}",
            "is_passed": datetime.now().date() > datetime(selected_year, 6, 15).date(),
        },
        {
            "date": f"September 15, {selected_year}",
            "description": f"Third quarterly tax installment payment for {selected_year}",
            "is_passed": datetime.now().date() > datetime(selected_year, 9, 15).date(),
        },
        {
            "date": f"December 15, {selected_year}",
            "description": f"Fourth quarterly tax installment payment for {selected_year}",
            "is_passed": datetime.now().date() > datetime(selected_year, 12, 15).date(),
        }
    ]
    
    return jsonify({
        "selected_year": selected_year,
        "available_years": available_years,
        "selected_province": selected_province,
        "provinces": sorted(GST_HST_RATES.keys()),
        "summary": {
            "total_income": str(total_yearly_income),
            "total_expenses": str(total_yearly_expense),
            "net_income": str(yearly_net_income)
        },
        "cra_expense_categories": formatted_cra_categories,
        "quarterly_data": quarterly_data,
        "gst_hst": {
            "rate": str(gst_hst_rate),
            "collected": str(gst_hst_collected),
            "paid": str(gst_hst_paid),
            "owing": str(gst_hst_owing)
        },
        "cca_items": cca_items,
        "tax_deadlines": tax_deadlines,
        "tax_prediction": tax_prediction
    })


@bp.route("/prediction", methods=["GET"])
@token_required
def get_tax_prediction():
    """Get tax prediction data"""
    # Get current year
    current_year = datetime.now().year
    
    # Get selected province for tax calculations
    selected_province = request.args.get("province", default="Ontario")
    
    # Calculate year date range
    year_start_date = datetime(current_year, 1, 1).date()
    year_end_date = datetime(current_year, 12, 31).date()
    
    # Get expenses and income for the year
    yearly_expenses = Expense.query.filter(
        Expense.user_id == g.current_user.id,
        Expense.date >= year_start_date, 
        Expense.date <= year_end_date
    ).all()
    
    yearly_income = Income.query.filter(
        Income.user_id == g.current_user.id,
        Income.date >= year_start_date, 
        Income.date <= year_end_date
    ).all()
    
    # Get tax prediction
    tax_prediction = TaxPredictionService.predict_tax_obligation(
        yearly_income, yearly_expenses, selected_province, current_year
    )
    
    return jsonify({
        "year": current_year,
        "province": selected_province,
        "provinces": sorted(GST_HST_RATES.keys()),
        "prediction": tax_prediction
    })


@bp.route("/category-suggestions", methods=["POST"])
@token_required
def get_category_suggestions():
    """Get AI-powered tax category suggestions for an expense"""
    if not request.is_json:
        return jsonify({"message": "Missing JSON data in request"}), 400
    
    data = request.get_json()
    
    # Validate required fields
    if "title" not in data:
        return jsonify({"message": "Missing required field: title"}), 400
    
    # Get suggestions
    suggestions = TaxRecommendationService.suggest_category(
        data["title"], data.get("vendor")
    )
    
    # Format results
    result = []
    for category, confidence in suggestions:
        tax_implications = TaxRecommendationService.get_tax_implications(category)
        result.append({
            "category": category,
            "confidence": confidence,
            "cra_category": tax_implications["cra_category"],
            "deduction_rate": tax_implications["deduction_rate"],
            "special_rules": tax_implications["special_rules"],
            "documentation_required": tax_implications["documentation_required"]
        })
    
    return jsonify({
        "title": data["title"],
        "vendor": data.get("vendor"),
        "suggestions": result
    })


@bp.route("/analyze-expenses", methods=["GET"])
@token_required
def analyze_expenses():
    """Analyze expenses for tax optimization"""
    # Get current year and selected year from query param
    current_year = datetime.now().year
    selected_year = request.args.get("year", type=int, default=current_year)
    
    # Calculate year date range
    year_start_date = datetime(selected_year, 1, 1).date()
    year_end_date = datetime(selected_year, 12, 31).date()
    
    # Get expenses for the year
    yearly_expenses = Expense.query.filter(
        Expense.user_id == g.current_user.id,
        Expense.date >= year_start_date, 
        Expense.date <= year_end_date
    ).all()
    
    # Analyze expenses
    analysis = TaxRecommendationService.analyze_expenses(yearly_expenses)
    
    # Format results
    formatted_categories = []
    for category, data in analysis["categories"].items():
        formatted_categories.append({
            "category": category,
            "cra_category": data["cra_category"],
            "count": data["count"],
            "amount": str(data["amount"])
        })
    
    # Sort by amount (descending)
    formatted_categories.sort(key=lambda x: Decimal(x["amount"]), reverse=True)
    
    return jsonify({
        "year": selected_year,
        "total_amount": str(analysis["total_amount"]),
        "count": analysis["count"],
        "categories": formatted_categories,
        "recommendations": analysis["recommendations"],
        "missing_receipts": analysis["missing_receipts"],
        "potential_recategorizations": analysis["potential_recategorizations"]
    })


@bp.route("/cra-categories", methods=["GET"])
@token_required
def get_cra_categories():
    """Get CRA tax categories mapping"""
    result = []
    for category, cra_category in CRA_TAX_CATEGORIES.items():
        result.append({
            "category": category,
            "cra_category": cra_category
        })
    
    return jsonify({
        "cra_categories": result
    })


@bp.route("/cca-classes", methods=["GET"])
@token_required
def get_cca_classes():
    """Get Capital Cost Allowance (CCA) classes"""
    result = []
    for cca_class, data in CCA_CLASSES.items():
        result.append({
            "class": cca_class,
            "rate": str(data["rate"]),
            "description": data["description"],
            "examples": data["examples"]
        })
    
    return jsonify({
        "cca_classes": result
    })
