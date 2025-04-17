from typing import Dict, List, Tuple, Optional
import re
from decimal import Decimal

from akowe.models.expense import Expense


class TaxRecommendationService:
    """Service for providing AI-powered tax category recommendations"""

    # Mapping of common keywords to recommended tax categories
    KEYWORD_CATEGORY_MAPPING = {
        # Office Supplies
        "paper": "office_supplies",
        "pen": "office_supplies",
        "stapler": "office_supplies",
        "ink": "office_supplies",
        "toner": "office_supplies",
        "printer paper": "office_supplies",
        "notebook": "office_supplies",
        "binder": "office_supplies",
        "folder": "office_supplies",
        "stationery": "office_supplies",
        "office depot": "office_supplies",
        "staples": "office_supplies",
        
        # Hardware
        "computer": "hardware",
        "laptop": "hardware",
        "monitor": "hardware",
        "keyboard": "hardware",
        "mouse": "hardware",
        "router": "hardware",
        "server": "hardware",
        "hard drive": "hardware",
        "ssd": "hardware",
        "usb": "hardware",
        "ipad": "hardware",
        "tablet": "hardware",
        "phone": "hardware",
        "dell": "hardware",
        "hp": "hardware",
        "lenovo": "hardware",
        "apple": "hardware",
        
        # Software
        "software": "software",
        "license": "software",
        "subscription": "software",
        "adobe": "software",
        "microsoft": "software",
        "windows": "software",
        "office 365": "software",
        "photoshop": "software",
        "aws": "software",
        "azure": "software",
        "saas": "software",
        "app store": "software",
        "google workspace": "software",
        "zoom": "software",
        "dropbox": "software",
        
        # Rent
        "rent": "rent",
        "lease": "rent",
        "office space": "rent",
        "coworking": "rent",
        "wework": "rent",
        "regus": "rent",
        
        # Utilities
        "electric": "utilities",
        "electricity": "utilities",
        "water": "utilities",
        "gas": "utilities",
        "heating": "utilities",
        "internet": "utilities",
        "phone bill": "utilities",
        "cell phone": "utilities",
        "mobile": "utilities",
        
        # Travel
        "flight": "travel",
        "airline": "travel",
        "hotel": "travel",
        "air canada": "travel",
        "westjet": "travel",
        "airbnb": "travel",
        "taxi": "travel",
        "uber": "travel",
        "lyft": "travel",
        "rental car": "travel",
        "train": "travel",
        "railway": "travel",
        "via rail": "travel",
        "parking": "travel",
        "mileage": "travel",
        
        # Food & Entertainment
        "restaurant": "food",
        "meal": "food",
        "lunch": "food",
        "dinner": "food",
        "coffee": "food",
        "starbucks": "food",
        "tim hortons": "food",
        "mcdonald": "food",
        "ticket": "entertainment",
        "movie": "entertainment",
        "concert": "entertainment",
        "theater": "entertainment",
        "sporting event": "entertainment",
        "game": "entertainment",
        
        # Professional Services
        "lawyer": "professional_services",
        "attorney": "professional_services",
        "legal": "professional_services",
        "accountant": "professional_services",
        "accounting": "professional_services",
        "consultant": "professional_services",
        "consulting": "professional_services",
        "advisor": "professional_services",
        
        # Marketing
        "advertising": "marketing",
        "ad": "marketing",
        "facebook ad": "marketing",
        "google ad": "marketing",
        "linkedin": "marketing",
        "seo": "marketing",
        "promotion": "marketing",
        "flyer": "marketing",
        "business card": "marketing",
        "brochure": "marketing",
        "logo": "marketing",
        "design": "marketing",
        
        # Maintenance
        "repair": "maintenance",
        "maintenance": "maintenance",
        "cleaning": "maintenance",
        "janitor": "maintenance",
        
        # Taxes
        "tax": "taxes",
        "filing fee": "taxes",
        "registration fee": "taxes",
        "license fee": "taxes",
        "permit": "taxes",
        
        # Insurance
        "insurance": "insurance",
        "liability": "insurance",
        "business insurance": "insurance",
        "health insurance": "insurance",
    }

    # CRA Tax categories mapping (from tax_dashboard.py)
    CRA_TAX_CATEGORIES = {
        "office_supplies": "Office Expenses",
        "hardware": "Capital Cost Allowance (CCA)",
        "software": "Capital Cost Allowance (CCA)",
        "rent": "Rent",
        "utilities": "Utilities",
        "travel": "Travel Expenses",
        "food": "Meals and Entertainment (50% deductible)",
        "entertainment": "Meals and Entertainment (50% deductible)",
        "professional_services": "Professional Fees",
        "marketing": "Advertising and Promotion",
        "maintenance": "Maintenance and Repairs",
        "taxes": "Taxes, Licenses and Dues",
        "insurance": "Insurance",
        "other": "Other Expenses",
    }

    # Special tax rules by category
    TAX_RULES = {
        "food": "50% deductible for business meals",
        "entertainment": "50% deductible for business entertainment",
        "hardware": "May be eligible for Capital Cost Allowance (CCA) deduction",
        "software": "May be 100% deductible in year of purchase if under $500",
        "travel": "Must be primarily for business purposes to be deductible",
        "home_office": "Deductible based on percentage of home used for business",
    }

    @classmethod
    def suggest_category(cls, title: str, vendor: Optional[str] = None) -> List[Tuple[str, float]]:
        """
        Suggests tax categories based on expense title and vendor
        
        Args:
            title: Title of the expense
            vendor: Vendor name (optional)
            
        Returns:
            List of tuples containing (category, confidence_score)
        """
        search_text = f"{title} {vendor}".lower() if vendor else title.lower()
        suggestions = []
        
        # First pass: Look for exact matches
        for keyword, category in cls.KEYWORD_CATEGORY_MAPPING.items():
            if keyword.lower() in search_text:
                # Calculate confidence based on keyword length vs search text length
                # Longer keyword matches get higher confidence
                confidence = min(0.95, 0.5 + (len(keyword) / len(search_text)) * 0.5) 
                suggestions.append((category, confidence))
        
        # Second pass: Look for partial matches if no strong matches found
        if not suggestions or max(conf for _, conf in suggestions) < 0.7:
            for keyword, category in cls.KEYWORD_CATEGORY_MAPPING.items():
                # Use word boundaries to avoid partial word matches
                if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', search_text):
                    # Partial matches get lower confidence
                    confidence = 0.6
                    suggestions.append((category, confidence))
        
        # Default to "other" with low confidence if no matches
        if not suggestions:
            suggestions.append(("other", 0.3))
        
        # Group by category, keeping highest confidence score
        category_scores = {}
        for category, confidence in suggestions:
            if category not in category_scores or confidence > category_scores[category]:
                category_scores[category] = confidence
        
        # Convert back to list of tuples and sort by confidence (descending)
        final_suggestions = [(category, score) for category, score in category_scores.items()]
        final_suggestions.sort(key=lambda x: x[1], reverse=True)
        
        return final_suggestions[:3]  # Return top 3 suggestions

    @classmethod
    def get_tax_implications(cls, category: str) -> Dict:
        """
        Get tax implications for a given expense category
        
        Args:
            category: Expense category
            
        Returns:
            Dictionary with tax information and recommendations
        """
        cra_category = cls.CRA_TAX_CATEGORIES.get(category, "Other Expenses")
        
        result = {
            "cra_category": cra_category,
            "deduction_rate": "100%" if category not in ["food", "entertainment"] else "50%",
            "special_rules": cls.TAX_RULES.get(category, "No special rules"),
            "documentation_required": False,
        }
        
        # Set documentation requirements based on category
        if category in ["travel", "hardware", "software", "professional_services"]:
            result["documentation_required"] = True
            result["documentation_note"] = "Keep detailed receipts with business purpose noted"
        
        # Add CCA information for capital expenses
        if category in ["hardware", "software"]:
            if category == "hardware":
                result["cca_class"] = "Class 50 (55% rate) for computer equipment"
            else:
                result["cca_class"] = "Class 12 (100% rate) if under $500, otherwise amortized"
        
        return result

    @classmethod
    def get_optimization_suggestions(cls, expense: Expense) -> List[Dict]:
        """
        Get suggestions for optimizing tax deductions for an expense
        
        Args:
            expense: Expense object
            
        Returns:
            List of suggestion dictionaries
        """
        suggestions = []
        
        # Hardware/software special cases
        if expense.category in ["hardware", "software"]:
            suggestions.append({
                "type": "documentation",
                "message": "Ensure you have a receipt that shows the item purchased and business purpose",
                "benefit": "Supports CCA deduction claim in case of CRA audit"
            })
            
            # Suggest splitting personal/business use
            suggestions.append({
                "type": "allocation",
                "message": "If used for both personal and business, allocate percentage for business use only",
                "benefit": "Proper allocation avoids issues in case of audit"
            })
            
            # Software under $500 is fully deductible
            if expense.category == "software" and expense.amount < 500:
                suggestions.append({
                    "type": "categorization",
                    "message": "Software under $500 is 100% deductible in year of purchase (Class 12)",
                    "benefit": "Immediate deduction versus amortization"
                })
                
        # Meals and entertainment are 50% deductible
        if expense.category in ["food", "entertainment"]:
            suggestions.append({
                "type": "documentation",
                "message": "Note business purpose and attendees on receipt",
                "benefit": "Supports 50% deduction claim in case of audit"
            })
            
            # For client entertainment, suggest proper documentation
            if expense.title and any(word in expense.title.lower() for word in ["client", "customer", "prospect"]):
                suggestions.append({
                    "type": "documentation",
                    "message": "For client entertainment, record client names and business discussion topics",
                    "benefit": "Strengthens deduction claim in case of audit"
                })
                
        # Travel expenses
        if expense.category == "travel":
            suggestions.append({
                "type": "documentation",
                "message": "Record business purpose of trip and keep all receipts",
                "benefit": "Supports deduction claim in case of audit"
            })
            
        # Home office
        if expense.category in ["rent", "utilities"]:
            suggestions.append({
                "type": "allocation",
                "message": "If working from home, consider home office deduction",
                "benefit": "Additional deduction opportunity"
            })
            
        # Generic suggestions
        if not expense.receipt_blob_name:
            suggestions.append({
                "type": "documentation",
                "message": "Attach receipt to maximize deduction eligibility",
                "benefit": "Provides evidence for deduction claim"
            })
            
        return suggestions


    @classmethod
    def analyze_expenses(cls, expenses: List[Expense]) -> Dict:
        """
        Analyze a list of expenses and provide optimization recommendations
        
        Args:
            expenses: List of Expense objects
            
        Returns:
            Dictionary with analysis results and recommendations
        """
        results = {
            "total_amount": sum(expense.amount for expense in expenses),
            "count": len(expenses),
            "categories": {},
            "recommendations": [],
            "missing_receipts": [],
            "potential_recategorizations": []
        }
        
        # Analyze by category
        for expense in expenses:
            cat = expense.category
            if cat not in results["categories"]:
                results["categories"][cat] = {
                    "count": 0,
                    "amount": Decimal("0"),
                    "cra_category": cls.CRA_TAX_CATEGORIES.get(cat, "Other Expenses")
                }
            
            results["categories"][cat]["count"] += 1
            results["categories"][cat]["amount"] += expense.amount
            
            # Check for receipt
            if not expense.receipt_blob_name and expense.amount > 100:
                results["missing_receipts"].append({
                    "id": expense.id,
                    "title": expense.title,
                    "amount": expense.amount,
                    "date": expense.date.isoformat()
                })
            
            # Check for potential recategorization
            if expense.title and expense.vendor:
                suggestions = cls.suggest_category(expense.title, expense.vendor)
                top_suggestion = suggestions[0] if suggestions else (None, 0)
                
                if top_suggestion[0] != expense.category and top_suggestion[1] > 0.7:
                    # Only suggest if confidence is high and it's a different category
                    current_tax_cat = cls.CRA_TAX_CATEGORIES.get(expense.category, "Other Expenses")
                    suggested_tax_cat = cls.CRA_TAX_CATEGORIES.get(top_suggestion[0], "Other Expenses")
                    
                    if current_tax_cat != suggested_tax_cat:
                        results["potential_recategorizations"].append({
                            "id": expense.id,
                            "title": expense.title,
                            "vendor": expense.vendor,
                            "amount": expense.amount,
                            "current_category": expense.category,
                            "suggested_category": top_suggestion[0],
                            "confidence": top_suggestion[1],
                            "current_tax_category": current_tax_cat,
                            "suggested_tax_category": suggested_tax_cat,
                            "reason": f"Based on '{expense.vendor}' and '{expense.title}'"
                        })
        
        # Global recommendations
        if results["missing_receipts"]:
            results["recommendations"].append({
                "type": "documentation",
                "message": f"Add receipts for {len(results['missing_receipts'])} expenses over $100",
                "impact": "high",
                "reason": "CRA requires receipts for expenses over $100"
            })
            
        if results["potential_recategorizations"]:
            results["recommendations"].append({
                "type": "categorization",
                "message": f"Review {len(results['potential_recategorizations'])} expenses that may be miscategorized",
                "impact": "medium",
                "reason": "Proper categorization ensures maximum tax benefits"
            })
            
        # Look for neglected categories
        common_categories = ["office_supplies", "software", "professional_services", "marketing"]
        missing_categories = [cat for cat in common_categories if cat not in results["categories"]]
        
        if missing_categories:
            results["recommendations"].append({
                "type": "completeness",
                "message": f"Consider if you have unclaimed expenses in: {', '.join(missing_categories)}",
                "impact": "medium",
                "reason": "Many businesses under-report certain expense categories"
            })
            
        # Check if meals/entertainment exceeds 10% of total expenses
        food_entertainment = Decimal("0")
        for cat in ["food", "entertainment"]:
            if cat in results["categories"]:
                food_entertainment += results["categories"][cat]["amount"]
                
        if food_entertainment > results["total_amount"] * Decimal("0.1"):
            results["recommendations"].append({
                "type": "audit_risk",
                "message": "Meals and entertainment expenses exceed 10% of total expenses",
                "impact": "medium",
                "reason": "High percentage may increase audit risk"
            })
            
        return results