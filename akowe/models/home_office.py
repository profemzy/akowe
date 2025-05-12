from datetime import datetime
from decimal import Decimal
from sqlalchemy import Numeric
from . import db


class HomeOffice(db.Model):
    """Model for home office expense calculations.
    
    This model stores both the inputs required for calculating home office deductions
    and the calculated results. It's linked to a user and a tax year.
    """
    __tablename__ = "home_office"

    id = db.Column(db.Integer, primary_key=True)
    
    # Basic home office information
    tax_year = db.Column(db.Integer, nullable=False)  # Year for the tax calculation
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    
    # Home information
    total_home_area = db.Column(Numeric(10, 2), nullable=False)  # Total square footage/meters of home
    office_area = db.Column(Numeric(10, 2), nullable=False)      # Square footage/meters of the office
    area_unit = db.Column(db.String(20), default="sq_ft")        # sq_ft or sq_m
    
    # Home expenses
    rent = db.Column(Numeric(10, 2), default=Decimal('0.00'))
    mortgage_interest = db.Column(Numeric(10, 2), default=Decimal('0.00'))
    property_tax = db.Column(Numeric(10, 2), default=Decimal('0.00'))
    home_insurance = db.Column(Numeric(10, 2), default=Decimal('0.00'))
    utilities = db.Column(Numeric(10, 2), default=Decimal('0.00'))
    maintenance = db.Column(Numeric(10, 2), default=Decimal('0.00'))
    internet = db.Column(Numeric(10, 2), default=Decimal('0.00'))
    phone = db.Column(Numeric(10, 2), default=Decimal('0.00'))
    
    # Business use percentage (calculated)
    business_use_percentage = db.Column(Numeric(5, 2), default=Decimal('0.00'))  # Stored as a decimal (e.g., 0.25 = 25%)
    
    # Deduction eligibility and method
    is_primary_income = db.Column(db.Boolean, default=True)  # Is home office for primary business
    hours_per_week = db.Column(db.Integer, default=0)        # Hours worked from home office per week
    calculation_method = db.Column(db.String(20), default="percentage")  # percentage or simplified
    simplified_rate = db.Column(Numeric(10, 2), default=Decimal('0.00'))  # Rate per square foot for simplified method
    
    # Results (calculated)
    total_deduction = db.Column(Numeric(10, 2), default=Decimal('0.00'))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship("User", backref=db.backref("home_office_claims", lazy="dynamic"))
    
    # Calculated home expense breakdowns (not stored in DB)
    @property
    def deductible_rent(self):
        if self.rent <= 0:
            return Decimal('0.00')
        return (self.rent * (self.business_use_percentage / 100)).quantize(Decimal('0.01'))
    
    @property
    def deductible_mortgage_interest(self):
        if self.mortgage_interest <= 0:
            return Decimal('0.00')
        return (self.mortgage_interest * (self.business_use_percentage / 100)).quantize(Decimal('0.01'))
    
    @property
    def deductible_property_tax(self):
        if self.property_tax <= 0:
            return Decimal('0.00')
        return (self.property_tax * (self.business_use_percentage / 100)).quantize(Decimal('0.01'))
    
    @property
    def deductible_home_insurance(self):
        if self.home_insurance <= 0:
            return Decimal('0.00')
        return (self.home_insurance * (self.business_use_percentage / 100)).quantize(Decimal('0.01'))
    
    @property
    def deductible_utilities(self):
        if self.utilities <= 0:
            return Decimal('0.00')
        return (self.utilities * (self.business_use_percentage / 100)).quantize(Decimal('0.01'))
    
    @property
    def deductible_maintenance(self):
        if self.maintenance <= 0:
            return Decimal('0.00')
        return (self.maintenance * (self.business_use_percentage / 100)).quantize(Decimal('0.01'))
    
    @property
    def deductible_internet(self):
        if self.internet <= 0:
            return Decimal('0.00')
        return (self.internet * (self.business_use_percentage / 100)).quantize(Decimal('0.01'))
    
    @property
    def deductible_phone(self):
        if self.phone <= 0:
            return Decimal('0.00')
        return (self.phone * (self.business_use_percentage / 100)).quantize(Decimal('0.01'))
    
    def __repr__(self):
        return f"<HomeOffice {self.id}: {self.business_use_percentage}% of home for tax year {self.tax_year}>"