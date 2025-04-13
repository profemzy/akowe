from datetime import datetime, timedelta
from decimal import Decimal
from flask import Blueprint, render_template, request
from sqlalchemy import func, extract

from akowe.models.expense import Expense
from akowe.models.income import Income

bp = Blueprint('tax_dashboard', __name__, url_prefix='/tax')

# Define Canadian tax categories
CRA_TAX_CATEGORIES = {
    'office_supplies': 'Office Expenses',
    'hardware': 'Capital Cost Allowance (CCA)',
    'software': 'Capital Cost Allowance (CCA)',
    'rent': 'Rent',
    'utilities': 'Utilities',
    'travel': 'Travel Expenses',
    'food': 'Meals and Entertainment (50% deductible)',
    'entertainment': 'Meals and Entertainment (50% deductible)',
    'professional_services': 'Professional Fees',
    'marketing': 'Advertising and Promotion',
    'maintenance': 'Maintenance and Repairs',
    'taxes': 'Taxes, Licenses and Dues',
    'insurance': 'Insurance',
    'other': 'Other Expenses'
}

# Define Canadian GST/HST rates by province
GST_HST_RATES = {
    'Alberta': 0.05,  # GST only
    'British Columbia': 0.05,  # GST only
    'Manitoba': 0.05,  # GST only
    'New Brunswick': 0.15,  # HST
    'Newfoundland and Labrador': 0.15,  # HST
    'Northwest Territories': 0.05,  # GST only
    'Nova Scotia': 0.15,  # HST
    'Nunavut': 0.05,  # GST only
    'Ontario': 0.13,  # HST
    'Prince Edward Island': 0.15,  # HST
    'Quebec': 0.05,  # GST only (QST handled separately)
    'Saskatchewan': 0.05,  # GST only
    'Yukon': 0.05,  # GST only
}

# Define QST rates (Quebec only)
QST_RATE = 0.09975  # Quebec Sales Tax rate

# Define Canadian quarterly tax periods
TAX_QUARTERS = {
    1: {'start_month': 1, 'end_month': 3, 'name': 'Q1 (Jan-Mar)'},
    2: {'start_month': 4, 'end_month': 6, 'name': 'Q2 (Apr-Jun)'},
    3: {'start_month': 7, 'end_month': 9, 'name': 'Q3 (Jul-Sep)'},
    4: {'start_month': 10, 'end_month': 12, 'name': 'Q4 (Oct-Dec)'},
}

# Define CCA classes for capital expenses (simplified subset)
CCA_CLASSES = {
    'Class 8': {
        'rate': 0.20,  # 20%
        'description': 'Furniture, appliances, tools costing > $500',
        'examples': ['office furniture', 'tools', 'equipment'],
    },
    'Class 10': {
        'rate': 0.30,  # 30%
        'description': 'Automotive equipment, some general-purpose electronic devices',
        'examples': ['vehicles', 'general computer hardware'],
    },
    'Class 12': {
        'rate': 1.00,  # 100%
        'description': 'Tools, instruments costing < $500, software',
        'examples': ['small tools', 'software', 'tablets, smartphones'],
    },
    'Class 50': {
        'rate': 0.55,  # 55%
        'description': 'Computer hardware & systems software',
        'examples': ['servers', 'desktops', 'laptops', 'operating systems'],
    }
}

@bp.route('/', methods=['GET'])
def index():
    # Get current year and selected year from query param
    current_year = datetime.now().year
    selected_year = request.args.get('year', type=int, default=current_year)
    
    # Get selected province for tax calculations
    selected_province = request.args.get('province', default='Ontario')
    
    # Calculate year date range
    year_start_date = datetime(selected_year, 1, 1).date()
    year_end_date = datetime(selected_year, 12, 31).date()
    
    # Get expenses and income for the year
    yearly_expenses = Expense.query.filter(
        Expense.date >= year_start_date,
        Expense.date <= year_end_date
    ).all()
    
    yearly_income = Income.query.filter(
        Income.date >= year_start_date,
        Income.date <= year_end_date
    ).all()
    
    # Calculate totals
    total_yearly_expense = sum(expense.amount for expense in yearly_expenses)
    total_yearly_income = sum(income.amount for income in yearly_income)
    yearly_net_income = total_yearly_income - total_yearly_expense
    
    # Prepare expense data by tax categories for CRA
    cra_expense_categories = {}
    for category, tax_category in CRA_TAX_CATEGORIES.items():
        if tax_category not in cra_expense_categories:
            cra_expense_categories[tax_category] = {
                'amount': Decimal('0'),
                'categories': [],
                'expenses': []
            }
        cra_expense_categories[tax_category]['categories'].append(category)
    
    # Populate tax categories with expense data
    for expense in yearly_expenses:
        cra_category = CRA_TAX_CATEGORIES.get(expense.category, 'Other Expenses')
        cra_expense_categories[cra_category]['amount'] += expense.amount
        cra_expense_categories[cra_category]['expenses'].append(expense)
    
    # Get quarterly data for GST/HST reporting
    quarterly_data = {}
    for quarter_num, quarter_info in TAX_QUARTERS.items():
        start_month = quarter_info['start_month']
        end_month = quarter_info['end_month']
        
        quarter_start = datetime(selected_year, start_month, 1).date()
        if end_month == 12:
            quarter_end = datetime(selected_year, 12, 31).date()
        else:
            quarter_end = datetime(selected_year, end_month + 1, 1).date() - timedelta(days=1)
        
        quarter_expenses = Expense.query.filter(
            Expense.date >= quarter_start,
            Expense.date <= quarter_end
        ).all()
        
        quarter_income = Income.query.filter(
            Income.date >= quarter_start,
            Income.date <= quarter_end
        ).all()
        
        quarter_expense_total = sum(expense.amount for expense in quarter_expenses)
        quarter_income_total = sum(income.amount for income in quarter_income)
        
        quarterly_data[quarter_info['name']] = {
            'expenses': quarter_expense_total,
            'income': quarter_income_total,
            'net': quarter_income_total - quarter_expense_total,
            'start_date': quarter_start,
            'end_date': quarter_end
        }
    
    # Calculate GST/HST collected and paid (input tax credits)
    gst_hst_rate = GST_HST_RATES.get(selected_province, 0.05)
    qst_rate = QST_RATE if selected_province == 'Quebec' else 0
    
    # Calculate GST/HST collected on income (simplified)
    gst_hst_collected = total_yearly_income * Decimal(str(gst_hst_rate))
    qst_collected = total_yearly_income * Decimal(str(qst_rate)) if selected_province == 'Quebec' else Decimal('0')
    
    # Calculate GST/HST paid on expenses (input tax credits)
    # This is a simplified calculation - in reality, not all expenses have GST/HST
    gst_hst_paid = total_yearly_expense * Decimal(str(gst_hst_rate)) / (1 + Decimal(str(gst_hst_rate)))
    qst_paid = total_yearly_expense * Decimal(str(qst_rate)) / (1 + Decimal(str(qst_rate))) if selected_province == 'Quebec' else Decimal('0')
    
    # Calculate net GST/HST and QST owing
    gst_hst_owing = gst_hst_collected - gst_hst_paid
    qst_owing = qst_collected - qst_paid
    
    # Identify potential Capital Cost Allowance (CCA) items
    # In this simplified version, we'll assume hardware and software are the only CCA items
    cca_items = []
    for expense in yearly_expenses:
        if expense.category in ['hardware', 'software']:
            # Determine CCA class based on expense category and amount
            cca_class = 'Class 12'  # Default: software and items under $500
            
            if expense.category == 'hardware' and expense.amount > 500:
                cca_class = 'Class 50'  # Computer hardware > $500
            
            cca_items.append({
                'id': expense.id,
                'date': expense.date,
                'title': expense.title,
                'amount': expense.amount,
                'category': expense.category,
                'cca_class': cca_class,
                'cca_rate': CCA_CLASSES[cca_class]['rate'],
                'deduction': expense.amount * Decimal(str(CCA_CLASSES[cca_class]['rate']))
            })
    
    # Calculate income tax using simplified Canadian tax brackets
    # Federal brackets for 2023 (approximate)
    federal_tax_brackets = [
        {'max': Decimal('53359'), 'rate': Decimal('0.15')},
        {'max': Decimal('106717'), 'rate': Decimal('0.205')},
        {'max': Decimal('165430'), 'rate': Decimal('0.26')},
        {'max': Decimal('235675'), 'rate': Decimal('0.29')},
        {'max': None, 'rate': Decimal('0.33')}  # No upper limit
    ]
    
    # Calculate federal income tax (simplified)
    remaining_income = yearly_net_income
    estimated_federal_tax = Decimal('0')
    
    for bracket in federal_tax_brackets:
        if bracket['max'] is None or remaining_income <= bracket['max']:
            bracket_tax = remaining_income * bracket['rate']
            estimated_federal_tax += bracket_tax
            break
        else:
            if remaining_income > bracket['max']:
                bracket_tax = bracket['max'] * bracket['rate']
                estimated_federal_tax += bracket_tax
                remaining_income -= bracket['max']
            else:
                bracket_tax = remaining_income * bracket['rate']
                estimated_federal_tax += bracket_tax
                break
    
    # Provincial tax rates (simplified average)
    provincial_tax_rates = {
        'Alberta': 0.10,
        'British Columbia': 0.12,
        'Manitoba': 0.12,
        'New Brunswick': 0.14,
        'Newfoundland and Labrador': 0.15,
        'Northwest Territories': 0.12,
        'Nova Scotia': 0.16,
        'Nunavut': 0.12,
        'Ontario': 0.12,
        'Prince Edward Island': 0.14,
        'Quebec': 0.15,
        'Saskatchewan': 0.12,
        'Yukon': 0.09,
    }
    
    # Simple provincial tax estimate
    provincial_rate = provincial_tax_rates.get(selected_province, 0.12)
    estimated_provincial_tax = yearly_net_income * Decimal(str(provincial_rate))
    
    # Total estimated tax
    estimated_total_tax = estimated_federal_tax + estimated_provincial_tax
    
    # Self-employment CPP contributions (simplified)
    # 2023 CPP rate is 11.4% on earnings between $3,500 and $66,600
    cpp_base_exemption = Decimal('3500')
    cpp_maximum = Decimal('66600')
    cpp_rate = Decimal('0.114')  # 11.4% for self-employed
    
    cpp_earnings = min(max(yearly_net_income - cpp_base_exemption, Decimal('0')), cpp_maximum - cpp_base_exemption)
    estimated_cpp = cpp_earnings * cpp_rate
    
    # Get available years for dropdown
    income_years = [year[0] for year in Income.query.with_entities(
        extract('year', Income.date)).distinct().all()]
    expense_years = [year[0] for year in Expense.query.with_entities(
        extract('year', Expense.date)).distinct().all()]
    
    available_years = sorted(set(income_years + expense_years), reverse=True)
    
    # Tax deadlines and key dates for the selected year
    tax_deadlines = [
        {
            'date': f'April 30, {selected_year + 1}',
            'description': f'Deadline to file and pay {selected_year} personal income taxes',
            'is_passed': datetime.now().date() > datetime(selected_year + 1, 4, 30).date()
        },
        {
            'date': f'June 15, {selected_year + 1}',
            'description': f'Deadline to file {selected_year} self-employed income taxes (payment still due April 30)',
            'is_passed': datetime.now().date() > datetime(selected_year + 1, 6, 15).date()
        },
        {
            'date': f'March 15, {selected_year}',
            'description': f'First quarterly tax installment payment for {selected_year}',
            'is_passed': datetime.now().date() > datetime(selected_year, 3, 15).date()
        },
        {
            'date': f'June 15, {selected_year}',
            'description': f'Second quarterly tax installment payment for {selected_year}',
            'is_passed': datetime.now().date() > datetime(selected_year, 6, 15).date()
        },
        {
            'date': f'September 15, {selected_year}',
            'description': f'Third quarterly tax installment payment for {selected_year}',
            'is_passed': datetime.now().date() > datetime(selected_year, 9, 15).date()
        },
        {
            'date': f'December 15, {selected_year}',
            'description': f'Fourth quarterly tax installment payment for {selected_year}',
            'is_passed': datetime.now().date() > datetime(selected_year, 12, 15).date()
        },
        {
            'date': f'February 28, {selected_year + 1}',
            'description': f'Deadline to issue T4A slips to contractors for {selected_year}',
            'is_passed': datetime.now().date() > datetime(selected_year + 1, 2, 28).date()
        }
    ]
    
    # GST/HST deadlines
    for quarter_num, quarter_info in TAX_QUARTERS.items():
        if quarter_num < 4:
            month = quarter_info['end_month'] + 1
            year = selected_year
        else:
            month = 1
            year = selected_year + 1
        
        # GST/HST return is due one month after quarter end
        gst_deadline = datetime(year, month, 30).date()
        tax_deadlines.append({
            'date': gst_deadline.strftime('%B %d, %Y'),
            'description': f'GST/HST return due for {quarter_info["name"]} {selected_year}',
            'is_passed': datetime.now().date() > gst_deadline
        })
    
    return render_template('tax_dashboard/index.html',
                         selected_year=selected_year,
                         available_years=available_years,
                         total_income=total_yearly_income,
                         total_expenses=total_yearly_expense,
                         net_income=yearly_net_income,
                         cra_expense_categories=cra_expense_categories,
                         quarterly_data=quarterly_data,
                         gst_hst_collected=gst_hst_collected,
                         gst_hst_paid=gst_hst_paid,
                         gst_hst_owing=gst_hst_owing,
                         qst_collected=qst_collected,
                         qst_paid=qst_paid,
                         qst_owing=qst_owing,
                         selected_province=selected_province,
                         provinces=sorted(GST_HST_RATES.keys()),
                         gst_hst_rate=gst_hst_rate,
                         qst_rate=qst_rate,
                         cca_items=cca_items,
                         cca_classes=CCA_CLASSES,
                         estimated_federal_tax=estimated_federal_tax,
                         estimated_provincial_tax=estimated_provincial_tax,
                         estimated_total_tax=estimated_total_tax,
                         estimated_cpp=estimated_cpp,
                         tax_deadlines=tax_deadlines)