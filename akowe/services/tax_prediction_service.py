from datetime import datetime, timedelta, date
import calendar
from typing import Dict, List, Tuple, Optional, Any
from decimal import Decimal, ROUND_HALF_UP

from akowe.models.expense import Expense
from akowe.models.income import Income


class TaxPredictionService:
    """Service for providing AI-powered tax planning predictions and insights"""

    # Canadian federal tax brackets for 2023 (approximate)
    FEDERAL_TAX_BRACKETS = [
        {"max": Decimal("53359"), "rate": Decimal("0.15")},
        {"max": Decimal("106717"), "rate": Decimal("0.205")},
        {"max": Decimal("165430"), "rate": Decimal("0.26")},
        {"max": Decimal("235675"), "rate": Decimal("0.29")},
        {"max": None, "rate": Decimal("0.33")},  # No upper limit
    ]
    
    # Provincial tax rates (simplified average)
    PROVINCIAL_TAX_RATES = {
        "Alberta": 0.10,
        "British Columbia": 0.12,
        "Manitoba": 0.12,
        "New Brunswick": 0.14,
        "Newfoundland and Labrador": 0.15,
        "Northwest Territories": 0.12,
        "Nova Scotia": 0.16,
        "Nunavut": 0.12,
        "Ontario": 0.12,
        "Prince Edward Island": 0.14,
        "Quebec": 0.15,
        "Saskatchewan": 0.12,
        "Yukon": 0.09,
    }
    
    # Canadian GST/HST rates by province
    GST_HST_RATES = {
        "Alberta": 0.05,  # GST only
        "British Columbia": 0.05,  # GST only
        "Manitoba": 0.05,  # GST only
        "New Brunswick": 0.15,  # HST
        "Newfoundland and Labrador": 0.15,  # HST
        "Northwest Territories": 0.05,  # GST only
        "Nova Scotia": 0.15,  # HST
        "Nunavut": 0.05,  # GST only
        "Ontario": 0.13,  # HST
        "Prince Edward Island": 0.15,  # HST
        "Quebec": 0.05,  # GST only (QST handled separately)
        "Saskatchewan": 0.05,  # GST only
        "Yukon": 0.05,  # GST only
    }
    
    # Self-employment CPP parameters
    CPP_BASE_EXEMPTION = Decimal("3500")
    CPP_MAXIMUM = Decimal("66600")
    CPP_RATE = Decimal("0.114")  # 11.4% for self-employed
    
    @classmethod
    def predict_tax_obligation(cls, 
                              income_to_date: List[Income], 
                              expenses_to_date: List[Expense], 
                              province: str = "Ontario",
                              year: int = None) -> Dict:
        """
        Predict tax obligation for the current year based on income and expenses to date
        
        Args:
            income_to_date: List of Income objects for the year so far
            expenses_to_date: List of Expense objects for the year so far
            province: Canadian province for tax calculations
            year: Year for prediction (defaults to current year)
            
        Returns:
            Dictionary with tax prediction information
        """
        if year is None:
            year = datetime.now().year
            
        # Calculate totals to date
        income_to_date_sum = sum(income.amount for income in income_to_date)
        expenses_to_date_sum = sum(expense.amount for expense in expenses_to_date)
        net_income_to_date = income_to_date_sum - expenses_to_date_sum
        
        # Get the current date and determine how far into the year we are
        today = datetime.now().date()
        start_of_year = date(year, 1, 1)
        end_of_year = date(year, 12, 31)
        days_in_year = (end_of_year - start_of_year).days + 1
        days_elapsed = (today - start_of_year).days + 1
        
        # Stop projection from going beyond 100% of year
        year_fraction = min(1.0, days_elapsed / days_in_year)
        
        # Project income and expenses for the full year
        # Use months for better seasonal handling
        current_month = datetime.now().month
        
        # Income projection
        # Calculate average monthly income for months with data
        income_by_month = {}
        for income in income_to_date:
            month = income.date.month
            if month not in income_by_month:
                income_by_month[month] = Decimal("0")
            income_by_month[month] += income.amount
            
        # If we have data for the month, use it for the projection
        if len(income_by_month) > 0:
            avg_monthly_income = sum(income_by_month.values()) / len(income_by_month)
        else:
            avg_monthly_income = Decimal("0")
            
        projected_income = income_to_date_sum
        for month in range(current_month + 1, 13):
            # Use the same month from last year if available
            if month in income_by_month:
                projected_income += income_by_month[month]
            else:
                projected_income += avg_monthly_income
        
        # Expense projection (similar approach)
        expense_by_month = {}
        for expense in expenses_to_date:
            month = expense.date.month
            if month not in expense_by_month:
                expense_by_month[month] = Decimal("0")
            expense_by_month[month] += expense.amount
            
        # If we have data for the month, use it for the projection
        if len(expense_by_month) > 0:
            avg_monthly_expense = sum(expense_by_month.values()) / len(expense_by_month)
        else:
            avg_monthly_expense = Decimal("0")
            
        projected_expenses = expenses_to_date_sum
        for month in range(current_month + 1, 13):
            # Use the same month from last year if available
            if month in expense_by_month:
                projected_expenses += expense_by_month[month]
            else:
                projected_expenses += avg_monthly_expense
        
        # Calculate projected net income
        projected_net_income = projected_income - projected_expenses
        
        # Calculate estimated federal income tax
        estimated_federal_tax = cls._calculate_federal_tax(projected_net_income)
        
        # Calculate estimated provincial income tax
        provincial_rate = cls.PROVINCIAL_TAX_RATES.get(province, 0.12)
        estimated_provincial_tax = projected_net_income * Decimal(str(provincial_rate))
        
        # Calculate estimated CPP contributions
        cpp_earnings = min(
            max(projected_net_income - cls.CPP_BASE_EXEMPTION, Decimal("0")), 
            cls.CPP_MAXIMUM - cls.CPP_BASE_EXEMPTION
        )
        estimated_cpp = cpp_earnings * cls.CPP_RATE
        
        # Calculate GST/HST (simplified)
        gst_hst_rate = cls.GST_HST_RATES.get(province, 0.05)
        gst_hst_collected = projected_income * Decimal(str(gst_hst_rate))
        gst_hst_paid = (
            projected_expenses
            * Decimal(str(gst_hst_rate))
            / (Decimal("1") + Decimal(str(gst_hst_rate)))
        )
        gst_hst_owing = gst_hst_collected - gst_hst_paid
        
        # Calculate total estimated tax
        total_estimated_tax = estimated_federal_tax + estimated_provincial_tax + estimated_cpp
        
        # Format all decimals to 2 places
        TWOPLACES = Decimal(10) ** -2
        
        result = {
            "year": year,
            "province": province,
            "as_of_date": today.strftime("%Y-%m-%d"),
            "year_progress": round(year_fraction * 100, 1),
            
            "income_to_date": income_to_date_sum.quantize(TWOPLACES, ROUND_HALF_UP),
            "expenses_to_date": expenses_to_date_sum.quantize(TWOPLACES, ROUND_HALF_UP),
            "net_income_to_date": net_income_to_date.quantize(TWOPLACES, ROUND_HALF_UP),
            
            "projected_income": projected_income.quantize(TWOPLACES, ROUND_HALF_UP),
            "projected_expenses": projected_expenses.quantize(TWOPLACES, ROUND_HALF_UP),
            "projected_net_income": projected_net_income.quantize(TWOPLACES, ROUND_HALF_UP),
            
            "estimated_federal_tax": estimated_federal_tax.quantize(TWOPLACES, ROUND_HALF_UP),
            "estimated_provincial_tax": estimated_provincial_tax.quantize(TWOPLACES, ROUND_HALF_UP),
            "estimated_cpp": estimated_cpp.quantize(TWOPLACES, ROUND_HALF_UP),
            "estimated_total_tax": total_estimated_tax.quantize(TWOPLACES, ROUND_HALF_UP),
            
            "estimated_tax_rate": round((total_estimated_tax / projected_net_income) * 100, 1) if projected_net_income > 0 else 0,
            
            "gst_hst_collected": gst_hst_collected.quantize(TWOPLACES, ROUND_HALF_UP),
            "gst_hst_paid": gst_hst_paid.quantize(TWOPLACES, ROUND_HALF_UP),
            "gst_hst_owing": gst_hst_owing.quantize(TWOPLACES, ROUND_HALF_UP),
            
            "tax_brackets": cls._get_tax_bracket_info(projected_net_income),
            "months_breakdown": cls._get_monthly_breakdown(income_by_month, expense_by_month, year),
            "tax_planning_suggestions": cls._generate_tax_planning_suggestions(
                net_income_to_date, 
                projected_net_income, 
                expenses_to_date, 
                year
            )
        }
        
        return result
    
    @classmethod
    def _calculate_federal_tax(cls, net_income: Decimal) -> Decimal:
        """Calculate federal income tax based on tax brackets"""
        remaining_income = net_income
        federal_tax = Decimal("0")

        for bracket in cls.FEDERAL_TAX_BRACKETS:
            if bracket["max"] is None or remaining_income <= bracket["max"]:
                bracket_tax = remaining_income * bracket["rate"]
                federal_tax += bracket_tax
                break
            else:
                bracket_tax = bracket["max"] * bracket["rate"]
                federal_tax += bracket_tax
                remaining_income -= bracket["max"]

        return federal_tax
    
    @classmethod
    def _get_tax_bracket_info(cls, net_income: Decimal) -> List[Dict]:
        """Generate tax bracket information with the user's position in each bracket"""
        brackets_info = []
        remaining_income = net_income
        
        for i, bracket in enumerate(cls.FEDERAL_TAX_BRACKETS):
            # For the last bracket (no max)
            if bracket["max"] is None:
                amount_in_bracket = remaining_income
                tax_in_bracket = amount_in_bracket * bracket["rate"]
                brackets_info.append({
                    "bracket": f"Over ${cls.FEDERAL_TAX_BRACKETS[i-1]['max']:,.2f}",
                    "rate": f"{float(bracket['rate']) * 100:.1f}%",
                    "amount_in_bracket": amount_in_bracket,
                    "tax_in_bracket": tax_in_bracket,
                    "is_current": True if remaining_income > 0 else False
                })
                break
                
            # Determine how much income falls within this bracket
            if remaining_income <= 0:
                # User doesn't have income in this bracket
                amount_in_bracket = Decimal("0")
                tax_in_bracket = Decimal("0")
                is_current = False
            elif i == 0:
                # First bracket
                amount_in_bracket = min(remaining_income, bracket["max"])
                tax_in_bracket = amount_in_bracket * bracket["rate"]
                is_current = True
            else:
                # Middle brackets
                prev_max = cls.FEDERAL_TAX_BRACKETS[i - 1]["max"]
                amount_in_bracket = min(remaining_income, bracket["max"] - prev_max)
                tax_in_bracket = amount_in_bracket * bracket["rate"]
                is_current = True
                
            # Format the bracket label
            if i == 0:
                bracket_label = f"$0 - ${bracket['max']:,.2f}"
            else:
                prev_max = cls.FEDERAL_TAX_BRACKETS[i - 1]["max"]
                bracket_label = f"${prev_max + Decimal('0.01'):,.2f} - ${bracket['max']:,.2f}"
                
            brackets_info.append({
                "bracket": bracket_label,
                "rate": f"{float(bracket['rate']) * 100:.1f}%",
                "amount_in_bracket": amount_in_bracket,
                "tax_in_bracket": tax_in_bracket,
                "is_current": is_current
            })
            
            remaining_income -= amount_in_bracket
        
        return brackets_info
    
    @classmethod
    def _get_monthly_breakdown(cls, income_by_month: Dict, expense_by_month: Dict, year: int) -> List[Dict]:
        """Generate monthly breakdown of income/expenses with projections"""
        today = datetime.now().date()
        current_month = today.month
        
        months_data = []
        
        for month in range(1, 13):
            month_name = calendar.month_name[month]
            
            # Check if we have actual data for this month
            is_actual = month <= current_month
            
            # Get income for this month (actual or projected)
            income = income_by_month.get(month, Decimal("0"))
            
            # For future months, use projection if no data exists
            if not is_actual and month not in income_by_month and income_by_month:
                # Use average if no specific data
                income = sum(income_by_month.values()) / len(income_by_month)
            
            # Get expenses for this month (actual or projected)
            expenses = expense_by_month.get(month, Decimal("0"))
            
            # For future months, use projection if no data exists
            if not is_actual and month not in expense_by_month and expense_by_month:
                # Use average if no specific data
                expenses = sum(expense_by_month.values()) / len(expense_by_month)
            
            # Calculate net for the month
            net = income - expenses
            
            months_data.append({
                "month": month,
                "month_name": month_name,
                "is_actual": is_actual,
                "income": income,
                "expenses": expenses,
                "net": net
            })
        
        return months_data
    
    @classmethod
    def _generate_tax_planning_suggestions(cls, 
                                         net_income_to_date: Decimal,
                                         projected_net_income: Decimal,
                                         expenses_to_date: List[Expense],
                                         year: int) -> List[Dict]:
        """Generate tax planning suggestions"""
        suggestions = []
        today = datetime.now().date()
        current_month = today.month
        
        # Check expense distribution and suggest balancing if needed
        expense_by_month = {}
        for expense in expenses_to_date:
            month = expense.date.month
            if month not in expense_by_month:
                expense_by_month[month] = []
            expense_by_month[month].append(expense)
            
        # Get expense categories used so far
        categories_used = set(expense.category for expense in expenses_to_date)
        all_categories = {
            "office_supplies", "hardware", "software", "rent", "utilities", 
            "travel", "food", "entertainment", "professional_services", 
            "marketing", "maintenance", "taxes", "insurance"
        }
        
        # 1. Identify missing common expense categories
        missing_categories = all_categories - categories_used
        if missing_categories:
            common_missing = [cat for cat in ["office_supplies", "software", "professional_services"] 
                            if cat in missing_categories]
            if common_missing:
                suggestions.append({
                    "type": "missing_categories",
                    "title": "Potential Missing Expense Categories",
                    "description": f"Consider if you have expenses in these categories: {', '.join(common_missing)}",
                    "benefit": "Ensures you're claiming all eligible deductions",
                    "priority": "medium"
                })
        
        # 2. Check if approaching tax bracket thresholds
        current_bracket = None
        next_bracket = None
        
        for i, bracket in enumerate(cls.FEDERAL_TAX_BRACKETS):
            if bracket["max"] is None:  # Last bracket
                if i > 0 and projected_net_income > cls.FEDERAL_TAX_BRACKETS[i - 1]["max"]:
                    current_bracket = i
                    next_bracket = None
                    break
            elif projected_net_income <= bracket["max"]:
                current_bracket = i
                next_bracket = i + 1 if i + 1 < len(cls.FEDERAL_TAX_BRACKETS) else None
                break
        
        # If within 10% of next bracket, suggest tax planning
        if next_bracket is not None:
            next_bracket_threshold = cls.FEDERAL_TAX_BRACKETS[current_bracket]["max"]
            distance_to_next = next_bracket_threshold - projected_net_income
            
            if distance_to_next > 0 and distance_to_next <= Decimal("5000"):
                current_rate = cls.FEDERAL_TAX_BRACKETS[current_bracket]["rate"] * 100
                next_rate = cls.FEDERAL_TAX_BRACKETS[next_bracket]["rate"] * 100
                
                suggestions.append({
                    "type": "tax_bracket_planning",
                    "title": "Near Higher Tax Bracket",
                    "description": f"You're ${distance_to_next:,.2f} away from the next tax bracket ({current_rate}% to {next_rate}%)",
                    "benefit": f"Consider timing expenses to stay below ${next_bracket_threshold:,.2f} threshold",
                    "priority": "high"
                })
        
        # 3. Check RRSP contribution opportunity
        if projected_net_income > Decimal("50000"):
            suggestions.append({
                "type": "rrsp_contribution",
                "title": "RRSP Contribution Opportunity",
                "description": "Based on projected income, RRSP contributions could reduce your taxable income",
                "benefit": "Reduces current year tax and builds retirement savings",
                "priority": "high"
            })
        
        # 4. Check for quarterly tax installment payments
        quarters = {
            1: {"months": [1, 2, 3], "deadline": f"March 15, {year}"},
            2: {"months": [4, 5, 6], "deadline": f"June 15, {year}"},
            3: {"months": [7, 8, 9], "deadline": f"September 15, {year}"},
            4: {"months": [10, 11, 12], "deadline": f"December 15, {year}"}
        }
        
        current_quarter = (current_month - 1) // 3 + 1
        next_quarter = current_quarter + 1 if current_quarter < 4 else None
        
        if next_quarter:
            suggestions.append({
                "type": "tax_installment",
                "title": f"Q{next_quarter} Tax Installment Planning",
                "description": f"Next quarterly tax installment due {quarters[next_quarter]['deadline']}",
                "benefit": "Avoiding interest charges and penalties on late tax payments",
                "priority": "medium"
            })
        
        # 5. Year-end tax planning for Q4
        if current_month >= 10:  # Q4
            suggestions.append({
                "type": "year_end_planning",
                "title": "Year-End Tax Planning",
                "description": "Consider accelerating expenses or deferring income before December 31",
                "benefit": "Optimize current year tax position",
                "priority": "high"
            })
        
        # 6. Equipment purchase suggestion (CCA)
        if current_month >= 10 and "hardware" not in categories_used:
            suggestions.append({
                "type": "equipment_purchase",
                "title": "Consider Equipment Purchases",
                "description": "If you need computer equipment or software, purchasing before year-end may reduce taxes",
                "benefit": "Immediate deduction via Capital Cost Allowance",
                "priority": "medium"
            })
        
        # 7. Home office deduction reminder
        suggestions.append({
            "type": "home_office",
            "title": "Home Office Expense Documentation",
            "description": "Ensure you're tracking home office expenses (utilities, rent/mortgage, maintenance)",
            "benefit": "Maximize eligible home office deductions",
            "priority": "medium"
        })
            
        return suggestions
