"""Service for calculating home office expense deductions for tax purposes."""

from decimal import Decimal
from typing import Dict, Any, Optional, Tuple

from akowe.models.home_office import HomeOffice
from akowe.models import db


class HomeOfficeService:
    """Service for managing home office expense calculations."""
    
    # Simplified method rates by country ($ per square foot)
    SIMPLIFIED_RATES = {
        "CA": {  # Canada
            "2023": Decimal("2.00"),
            "2024": Decimal("2.00"),
            "2025": Decimal("2.00"),
        },
        "US": {  # United States
            "2023": Decimal("5.00"),
            "2024": Decimal("5.00"),
            "2025": Decimal("5.00"),
        }
    }
    
    # Maximum deductible area for simplified method (sq ft)
    MAX_SIMPLIFIED_AREA = {
        "CA": 400,  # Canada
        "US": 300,  # United States
    }
    
    @classmethod
    def create_home_office_claim(cls, user_id: int, data: Dict[str, Any]) -> HomeOffice:
        """Create a new home office claim with initial data.
        
        Args:
            user_id: The ID of the user creating the claim
            data: Dictionary containing home office data
            
        Returns:
            The created HomeOffice instance
        """
        # Create new home office claim
        home_office = HomeOffice(
            user_id=user_id,
            tax_year=int(data.get("tax_year", 0)),
            total_home_area=Decimal(str(data.get("total_home_area", "0"))),
            office_area=Decimal(str(data.get("office_area", "0"))),
            area_unit=data.get("area_unit", "sq_ft"),
            rent=Decimal(str(data.get("rent", "0"))),
            mortgage_interest=Decimal(str(data.get("mortgage_interest", "0"))),
            property_tax=Decimal(str(data.get("property_tax", "0"))),
            home_insurance=Decimal(str(data.get("home_insurance", "0"))),
            utilities=Decimal(str(data.get("utilities", "0"))),
            maintenance=Decimal(str(data.get("maintenance", "0"))),
            internet=Decimal(str(data.get("internet", "0"))),
            phone=Decimal(str(data.get("phone", "0"))),
            is_primary_income=data.get("is_primary_income", True),
            hours_per_week=int(data.get("hours_per_week", 0)),
            calculation_method=data.get("calculation_method", "percentage"),
        )
        
        # Calculate business use percentage
        if home_office.total_home_area > 0:
            home_office.business_use_percentage = (
                (home_office.office_area / home_office.total_home_area) * 100
            ).quantize(Decimal("0.01"))
        
        # Get the simplified rate if using that method
        if home_office.calculation_method == "simplified":
            country_code = data.get("country_code", "CA")
            tax_year = str(home_office.tax_year)
            home_office.simplified_rate = cls.SIMPLIFIED_RATES.get(country_code, {}).get(
                tax_year, Decimal("0.00")
            )
        
        # Calculate total deduction
        home_office.total_deduction = cls.calculate_deduction(home_office, data.get("country_code", "CA"))
        
        # Save to database
        db.session.add(home_office)
        db.session.commit()
        
        return home_office
    
    @classmethod
    def update_home_office_claim(cls, home_office_id: int, data: Dict[str, Any]) -> Optional[HomeOffice]:
        """Update an existing home office claim.
        
        Args:
            home_office_id: The ID of the home office claim to update
            data: Dictionary containing updated home office data
            
        Returns:
            The updated HomeOffice instance or None if not found
        """
        home_office = HomeOffice.query.get(home_office_id)
        if not home_office:
            return None
            
        # Update fields
        if "tax_year" in data:
            home_office.tax_year = int(data["tax_year"])
        if "total_home_area" in data:
            home_office.total_home_area = Decimal(str(data["total_home_area"]))
        if "office_area" in data:
            home_office.office_area = Decimal(str(data["office_area"]))
        if "area_unit" in data:
            home_office.area_unit = data["area_unit"]
        if "rent" in data:
            home_office.rent = Decimal(str(data["rent"]))
        if "mortgage_interest" in data:
            home_office.mortgage_interest = Decimal(str(data["mortgage_interest"]))
        if "property_tax" in data:
            home_office.property_tax = Decimal(str(data["property_tax"]))
        if "home_insurance" in data:
            home_office.home_insurance = Decimal(str(data["home_insurance"]))
        if "utilities" in data:
            home_office.utilities = Decimal(str(data["utilities"]))
        if "maintenance" in data:
            home_office.maintenance = Decimal(str(data["maintenance"]))
        if "internet" in data:
            home_office.internet = Decimal(str(data["internet"]))
        if "phone" in data:
            home_office.phone = Decimal(str(data["phone"]))
        if "is_primary_income" in data:
            home_office.is_primary_income = data["is_primary_income"]
        if "hours_per_week" in data:
            home_office.hours_per_week = int(data["hours_per_week"])
        if "calculation_method" in data:
            home_office.calculation_method = data["calculation_method"]
            
        # Calculate business use percentage
        if home_office.total_home_area > 0:
            home_office.business_use_percentage = (
                (home_office.office_area / home_office.total_home_area) * 100
            ).quantize(Decimal("0.01"))
        
        # Get the simplified rate if using that method
        if home_office.calculation_method == "simplified":
            country_code = data.get("country_code", "CA")
            tax_year = str(home_office.tax_year)
            home_office.simplified_rate = cls.SIMPLIFIED_RATES.get(country_code, {}).get(
                tax_year, Decimal("0.00")
            )
        
        # Calculate total deduction
        home_office.total_deduction = cls.calculate_deduction(home_office, data.get("country_code", "CA"))
        
        # Save to database
        db.session.commit()
        
        return home_office
    
    @classmethod
    def calculate_deduction(cls, home_office: HomeOffice, country_code: str = "CA") -> Decimal:
        """Calculate the total home office deduction.
        
        Args:
            home_office: The HomeOffice instance to calculate deduction for
            country_code: Country code for tax rules (CA or US)
            
        Returns:
            The calculated deduction amount
        """
        if home_office.calculation_method == "simplified":
            return cls.calculate_simplified_deduction(home_office, country_code)
        else:
            return cls.calculate_percentage_deduction(home_office)
    
    @classmethod
    def calculate_percentage_deduction(cls, home_office: HomeOffice) -> Decimal:
        """Calculate home office deduction using the percentage method.
        
        Args:
            home_office: The HomeOffice instance to calculate deduction for
            
        Returns:
            The calculated deduction amount
        """
        # Calculate total eligible expenses
        total_expenses = (
            home_office.rent
            + home_office.mortgage_interest
            + home_office.property_tax
            + home_office.home_insurance
            + home_office.utilities
            + home_office.maintenance
            + home_office.internet
            + home_office.phone
        )
        
        # Apply business use percentage
        business_percentage = home_office.business_use_percentage / 100
        deduction = (total_expenses * business_percentage).quantize(Decimal("0.01"))
        
        return deduction
    
    @classmethod
    def calculate_simplified_deduction(cls, home_office: HomeOffice, country_code: str = "CA") -> Decimal:
        """Calculate home office deduction using the simplified method.
        
        Args:
            home_office: The HomeOffice instance to calculate deduction for
            country_code: Country code for tax rules (CA or US)
            
        Returns:
            The calculated deduction amount
        """
        # Get the maximum deductible area for simplified method
        max_area = cls.MAX_SIMPLIFIED_AREA.get(country_code, 300)
        
        # Calculate deductible area (limited by maximum)
        if home_office.area_unit == "sq_m":
            # Convert from square meters to square feet (1 sq m = 10.764 sq ft)
            office_area_sq_ft = home_office.office_area * Decimal("10.764")
        else:
            office_area_sq_ft = home_office.office_area
            
        deductible_area = min(office_area_sq_ft, Decimal(str(max_area)))
        
        # Calculate deduction based on rate and area
        deduction = (deductible_area * home_office.simplified_rate).quantize(Decimal("0.01"))
        
        return deduction
    
    @classmethod
    def get_home_office_details(cls, home_office_id: int) -> Tuple[Optional[HomeOffice], Dict[str, Any]]:
        """Get detailed information about a home office claim.
        
        Args:
            home_office_id: The ID of the home office claim
            
        Returns:
            Tuple containing the HomeOffice instance and a dictionary of detailed calculations
        """
        home_office = HomeOffice.query.get(home_office_id)
        if not home_office:
            return None, {}
            
        details = {
            "id": home_office.id,
            "tax_year": home_office.tax_year,
            "total_home_area": float(home_office.total_home_area),
            "office_area": float(home_office.office_area),
            "area_unit": home_office.area_unit,
            "business_use_percentage": float(home_office.business_use_percentage),
            "calculation_method": home_office.calculation_method,
            "total_deduction": float(home_office.total_deduction),
            
            # Expense breakdown
            "expenses": {
                "rent": float(home_office.rent),
                "mortgage_interest": float(home_office.mortgage_interest),
                "property_tax": float(home_office.property_tax),
                "home_insurance": float(home_office.home_insurance),
                "utilities": float(home_office.utilities),
                "maintenance": float(home_office.maintenance),
                "internet": float(home_office.internet),
                "phone": float(home_office.phone),
            },
            
            # Deductible breakdown
            "deductible": {
                "rent": float(home_office.deductible_rent),
                "mortgage_interest": float(home_office.deductible_mortgage_interest),
                "property_tax": float(home_office.deductible_property_tax),
                "home_insurance": float(home_office.deductible_home_insurance),
                "utilities": float(home_office.deductible_utilities),
                "maintenance": float(home_office.deductible_maintenance),
                "internet": float(home_office.deductible_internet),
                "phone": float(home_office.deductible_phone),
            }
        }
        
        if home_office.calculation_method == "simplified":
            details["simplified_rate"] = float(home_office.simplified_rate)
        
        return home_office, details