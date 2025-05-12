"""Tests for the home office calculator functionality."""

import pytest
from decimal import Decimal
from datetime import date

from akowe.models.home_office import HomeOffice
from akowe.services.home_office_service import HomeOfficeService


def test_home_office_model(app):
    """Test the HomeOffice model and its properties."""
    with app.app_context():
        # Create a test home office instance
        home_office = HomeOffice(
            tax_year=2025,
            user_id=1,
            total_home_area=Decimal("1000.00"),
            office_area=Decimal("200.00"),
            area_unit="sq_ft",
            rent=Decimal("12000.00"),
            mortgage_interest=Decimal("0.00"),
            property_tax=Decimal("2400.00"),
            home_insurance=Decimal("1200.00"),
            utilities=Decimal("3600.00"),
            maintenance=Decimal("1000.00"),
            internet=Decimal("1200.00"),
            phone=Decimal("600.00"),
            business_use_percentage=Decimal("20.00"),
            is_primary_income=True,
            hours_per_week=40,
            calculation_method="percentage",
        )

        # Test business use percentage
        assert home_office.business_use_percentage == Decimal("20.00")
        
        # Test deductible property calculations
        assert home_office.deductible_rent == Decimal("2400.00")  # 12000 * 0.2
        assert home_office.deductible_mortgage_interest == Decimal("0.00")
        assert home_office.deductible_property_tax == Decimal("480.00")  # 2400 * 0.2
        assert home_office.deductible_home_insurance == Decimal("240.00")  # 1200 * 0.2
        assert home_office.deductible_utilities == Decimal("720.00")  # 3600 * 0.2
        assert home_office.deductible_maintenance == Decimal("200.00")  # 1000 * 0.2
        assert home_office.deductible_internet == Decimal("240.00")  # 1200 * 0.2
        assert home_office.deductible_phone == Decimal("120.00")  # 600 * 0.2
        
        # Test string representation
        assert "HomeOffice" in str(home_office)
        assert "20.00%" in str(home_office)
        assert "2025" in str(home_office)


def test_percentage_calculation(app):
    """Test the percentage method calculation."""
    with app.app_context():
        # Create a test home office instance with percentage method
        home_office = HomeOffice(
            tax_year=2025,
            user_id=1,
            total_home_area=Decimal("1000.00"),
            office_area=Decimal("150.00"),
            area_unit="sq_ft",
            rent=Decimal("12000.00"),  # $1000/month
            mortgage_interest=Decimal("0.00"),
            property_tax=Decimal("3000.00"),
            home_insurance=Decimal("1200.00"),
            utilities=Decimal("2400.00"),
            maintenance=Decimal("1000.00"),
            internet=Decimal("1200.00"),
            phone=Decimal("600.00"),
            business_use_percentage=Decimal("15.00"),  # 150 sq ft / 1000 sq ft
            is_primary_income=True,
            hours_per_week=40,
            calculation_method="percentage",
        )
        
        # Calculate total deduction using the service
        deduction = HomeOfficeService.calculate_percentage_deduction(home_office)
        
        # Expected deduction: 15% of total expenses
        total_expenses = (
            Decimal("12000.00")  # rent
            + Decimal("0.00")    # mortgage_interest
            + Decimal("3000.00")  # property_tax
            + Decimal("1200.00")  # home_insurance
            + Decimal("2400.00")  # utilities
            + Decimal("1000.00")  # maintenance
            + Decimal("1200.00")  # internet
            + Decimal("600.00")   # phone
        )
        expected_deduction = total_expenses * Decimal("0.15")
        expected_deduction = expected_deduction.quantize(Decimal("0.01"))
        
        assert deduction == expected_deduction
        assert deduction == Decimal("3210.00")  # 15% of $21,400


def test_simplified_calculation_canada(app):
    """Test the simplified method calculation for Canada."""
    with app.app_context():
        # Create a test home office instance with simplified method
        home_office = HomeOffice(
            tax_year=2025,
            user_id=1,
            total_home_area=Decimal("1000.00"),
            office_area=Decimal("200.00"),
            area_unit="sq_ft",
            is_primary_income=True,
            hours_per_week=40,
            calculation_method="simplified",
            simplified_rate=Decimal("2.00"),  # $2 per sq ft (Canada)
        )
        
        # Calculate deduction using the service for Canada
        deduction = HomeOfficeService.calculate_simplified_deduction(home_office, "CA")
        
        # Expected deduction: 200 sq ft * $2 per sq ft = $400
        expected_deduction = Decimal("400.00")
        
        assert deduction == expected_deduction


def test_simplified_calculation_us(app):
    """Test the simplified method calculation for US."""
    with app.app_context():
        # Create a test home office instance with simplified method
        home_office = HomeOffice(
            tax_year=2025,
            user_id=1,
            total_home_area=Decimal("1000.00"),
            office_area=Decimal("400.00"),  # Exceeds US max of 300
            area_unit="sq_ft",
            is_primary_income=True,
            hours_per_week=40,
            calculation_method="simplified",
            simplified_rate=Decimal("5.00"),  # $5 per sq ft (US)
        )
        
        # Calculate deduction using the service for US
        deduction = HomeOfficeService.calculate_simplified_deduction(home_office, "US")
        
        # Expected deduction: 300 sq ft (max) * $5 per sq ft = $1500
        expected_deduction = Decimal("1500.00")
        
        assert deduction == expected_deduction


def test_area_unit_conversion(app):
    """Test the area unit conversion for sq meters to sq feet."""
    with app.app_context():
        # Create a test home office instance with area in square meters
        home_office = HomeOffice(
            tax_year=2025,
            user_id=1,
            total_home_area=Decimal("100.00"),
            office_area=Decimal("20.00"),
            area_unit="sq_m",  # Square meters
            is_primary_income=True,
            hours_per_week=40,
            calculation_method="simplified",
            simplified_rate=Decimal("2.00"),  # $2 per sq ft (Canada)
        )
        
        # Calculate deduction using the service for Canada
        deduction = HomeOfficeService.calculate_simplified_deduction(home_office, "CA")
        
        # Expected conversion: 20 sq m = 215.28 sq ft
        # Max area in Canada is 400 sq ft, so all 215.28 sq ft are deductible
        # Expected deduction: 215.28 sq ft * $2 per sq ft = $430.56
        expected_conversion = Decimal("20.00") * Decimal("10.764")
        expected_deduction = expected_conversion * Decimal("2.00")
        expected_deduction = expected_deduction.quantize(Decimal("0.01"))
        
        assert deduction == expected_deduction
        assert deduction == Decimal("430.56")


def test_home_office_service_create(app, test_user):
    """Test the create_home_office_claim method of HomeOfficeService."""
    with app.app_context():
        # Create test data
        data = {
            "tax_year": "2025",
            "country_code": "CA",
            "calculation_method": "percentage",
            "area_unit": "sq_ft",
            "total_home_area": "1000.00",
            "office_area": "200.00",
            "is_primary_income": True,
            "hours_per_week": "40",
            "rent": "12000.00",
            "mortgage_interest": "0.00",
            "property_tax": "2400.00",
            "home_insurance": "1200.00",
            "utilities": "3600.00",
            "maintenance": "1000.00",
            "internet": "1200.00",
            "phone": "600.00",
        }
        
        # Create home office claim
        home_office = HomeOfficeService.create_home_office_claim(test_user.id, data)
        
        # Verify the claim was created correctly
        assert home_office.tax_year == 2025
        assert home_office.user_id == test_user.id
        assert home_office.total_home_area == Decimal("1000.00")
        assert home_office.office_area == Decimal("200.00")
        assert home_office.area_unit == "sq_ft"
        assert home_office.business_use_percentage == Decimal("20.00")
        assert home_office.calculation_method == "percentage"
        
        # Verify the deduction was calculated correctly
        expected_deduction = Decimal("4400.00")  # 20% of $22,000 total expenses
        assert home_office.total_deduction == expected_deduction
        
        # Clean up
        from akowe.models import db
        db.session.delete(home_office)
        db.session.commit()


def test_home_office_model_creation(app):
    """Test that the HomeOffice model can be created and saved to the database."""
    with app.app_context():
        # Import the models and db
        from akowe.models.home_office import HomeOffice
        from akowe.models import db

        # Create a home office record
        home_office = HomeOffice(
            tax_year=2025,
            user_id=1,
            total_home_area=Decimal("1000.00"),
            office_area=Decimal("200.00"),
            area_unit="sq_ft",
            rent=Decimal("12000.00"),
            mortgage_interest=Decimal("0.00"),
            property_tax=Decimal("2400.00"),
            home_insurance=Decimal("1200.00"),
            utilities=Decimal("3600.00"),
            maintenance=Decimal("1000.00"),
            internet=Decimal("1200.00"),
            phone=Decimal("600.00"),
            business_use_percentage=Decimal("20.00"),
            is_primary_income=True,
            hours_per_week=40,
            calculation_method="percentage",
            total_deduction=Decimal("4400.00"),
        )

        # Add to database
        db.session.add(home_office)
        db.session.commit()

        # Verify it was saved
        saved_home_office = HomeOffice.query.get(home_office.id)
        assert saved_home_office is not None
        assert saved_home_office.tax_year == 2025
        assert saved_home_office.business_use_percentage == Decimal("20.00")
        assert saved_home_office.total_deduction == Decimal("4400.00")

        # Clean up
        db.session.delete(home_office)
        db.session.commit()
    
