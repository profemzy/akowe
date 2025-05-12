"""Home office expense calculator routes."""

from datetime import datetime
from decimal import Decimal

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app, g
from flask_login import login_required, current_user

from akowe.models import db
from akowe.models.home_office import HomeOffice
from akowe.services.home_office_service import HomeOfficeService

# Create blueprint
bp = Blueprint("home_office", __name__, url_prefix="/home-office")


@bp.route("/", methods=["GET"])
@login_required
def index():
    """Home office calculator landing page."""
    # Get all home office claims for current user
    home_office_claims = HomeOffice.query.filter_by(user_id=current_user.id).order_by(
        HomeOffice.tax_year.desc()
    ).all()
    
    return render_template("home_office/index.html", home_office_claims=home_office_claims)


@bp.route("/new", methods=["GET"])
@login_required
def new():
    """Display form to create a new home office claim."""
    return render_template("home_office/new.html")


@bp.route("/create", methods=["POST"])
@login_required
def create():
    """Create a new home office claim based on form submission."""
    try:
        # Process form data
        data = {
            # Basic Information
            "tax_year": request.form.get("tax_year", datetime.now().year),
            "country_code": request.form.get("country_code", "CA"),
            
            # Calculation Method
            "calculation_method": request.form.get("calculation_method", "percentage"),
            
            # Home Information
            "area_unit": request.form.get("area_unit", "sq_ft"),
            "total_home_area": request.form.get("total_home_area", "0"),
            "office_area": request.form.get("office_area", "0"),
            "is_primary_income": request.form.get("is_primary_income") == "true",
            "hours_per_week": request.form.get("hours_per_week", "0"),
            
            # Home Expenses (only used if calculation_method is percentage)
            "rent": request.form.get("rent", "0"),
            "mortgage_interest": request.form.get("mortgage_interest", "0"),
            "property_tax": request.form.get("property_tax", "0"),
            "home_insurance": request.form.get("home_insurance", "0"),
            "utilities": request.form.get("utilities", "0"),
            "maintenance": request.form.get("maintenance", "0"),
            "internet": request.form.get("internet", "0"),
            "phone": request.form.get("phone", "0"),
        }
        
        # Create home office claim
        home_office = HomeOfficeService.create_home_office_claim(current_user.id, data)
        
        flash("Home office claim created successfully!", "success")
        return redirect(url_for("home_office.view", id=home_office.id))
    
    except Exception as e:
        current_app.logger.error(f"Error creating home office claim: {str(e)}")
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for("home_office.new"))


@bp.route("/<int:id>", methods=["GET"])
@login_required
def view(id):
    """View a specific home office claim."""
    # Get home office claim and details
    home_office, details = HomeOfficeService.get_home_office_details(id)
    
    # Check if claim exists and belongs to current user
    if home_office is None or home_office.user_id != current_user.id:
        flash("Home office claim not found", "danger")
        return redirect(url_for("home_office.index"))
    
    return render_template("home_office/view.html", claim=home_office, details=details)


@bp.route("/<int:id>/edit", methods=["GET"])
@login_required
def edit(id):
    """Display form to edit an existing home office claim."""
    # Get home office claim
    home_office = HomeOffice.query.get(id)
    
    # Check if claim exists and belongs to current user
    if home_office is None or home_office.user_id != current_user.id:
        flash("Home office claim not found", "danger")
        return redirect(url_for("home_office.index"))
    
    return render_template("home_office/edit.html", claim=home_office)


@bp.route("/<int:id>/update", methods=["POST"])
@login_required
def update(id):
    """Update an existing home office claim based on form submission."""
    # Get home office claim
    home_office = HomeOffice.query.get(id)
    
    # Check if claim exists and belongs to current user
    if home_office is None or home_office.user_id != current_user.id:
        flash("Home office claim not found", "danger")
        return redirect(url_for("home_office.index"))
    
    try:
        # Process form data
        data = {
            # Basic Information
            "tax_year": request.form.get("tax_year"),
            "country_code": request.form.get("country_code"),
            
            # Calculation Method
            "calculation_method": request.form.get("calculation_method"),
            
            # Home Information
            "area_unit": request.form.get("area_unit"),
            "total_home_area": request.form.get("total_home_area"),
            "office_area": request.form.get("office_area"),
            "is_primary_income": request.form.get("is_primary_income") == "true",
            "hours_per_week": request.form.get("hours_per_week"),
            
            # Home Expenses (only used if calculation_method is percentage)
            "rent": request.form.get("rent"),
            "mortgage_interest": request.form.get("mortgage_interest"),
            "property_tax": request.form.get("property_tax"),
            "home_insurance": request.form.get("home_insurance"),
            "utilities": request.form.get("utilities"),
            "maintenance": request.form.get("maintenance"),
            "internet": request.form.get("internet"),
            "phone": request.form.get("phone"),
        }
        
        # Update home office claim
        home_office = HomeOfficeService.update_home_office_claim(id, data)
        
        flash("Home office claim updated successfully!", "success")
        return redirect(url_for("home_office.view", id=home_office.id))
    
    except Exception as e:
        current_app.logger.error(f"Error updating home office claim: {str(e)}")
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for("home_office.edit", id=id))


@bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete(id):
    """Delete a home office claim."""
    # Get home office claim
    home_office = HomeOffice.query.get(id)
    
    # Check if claim exists and belongs to current user
    if home_office is None or home_office.user_id != current_user.id:
        flash("Home office claim not found", "danger")
        return redirect(url_for("home_office.index"))
    
    try:
        # Delete home office claim
        db.session.delete(home_office)
        db.session.commit()
        
        flash("Home office claim deleted successfully!", "success")
    except Exception as e:
        current_app.logger.error(f"Error deleting home office claim: {str(e)}")
        flash(f"An error occurred: {str(e)}", "danger")
    
    return redirect(url_for("home_office.index"))


# API Endpoints for AJAX requests

@bp.route("/api/calculate", methods=["POST"])
@login_required
def api_calculate():
    """API endpoint to calculate home office deduction without saving."""
    try:
        # Get JSON data
        data = request.json
        
        # Create a temporary home office object
        home_office = HomeOffice(
            user_id=current_user.id,
            tax_year=int(data.get("tax_year", datetime.now().year)),
            total_home_area=Decimal(str(data.get("total_home_area", "0"))),
            office_area=Decimal(str(data.get("office_area", "0"))),
            area_unit=data.get("area_unit", "sq_ft"),
            calculation_method=data.get("calculation_method", "percentage"),
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
        )
        
        # Calculate business use percentage
        if home_office.total_home_area > 0:
            home_office.business_use_percentage = (
                (home_office.office_area / home_office.total_home_area) * 100
            ).quantize(Decimal("0.01"))
        
        # Calculate deduction
        country_code = data.get("country_code", "CA")
        
        # Get the simplified rate if using that method
        if home_office.calculation_method == "simplified":
            tax_year = str(home_office.tax_year)
            home_office.simplified_rate = HomeOfficeService.SIMPLIFIED_RATES.get(country_code, {}).get(
                tax_year, Decimal("0.00")
            )
        
        # Calculate total deduction
        total_deduction = HomeOfficeService.calculate_deduction(home_office, country_code)
        
        # Return calculation result
        return jsonify({
            "success": True,
            "business_use_percentage": float(home_office.business_use_percentage),
            "total_deduction": float(total_deduction),
            "calculation_method": home_office.calculation_method,
        })
        
    except Exception as e:
        current_app.logger.error(f"Error calculating home office deduction: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400