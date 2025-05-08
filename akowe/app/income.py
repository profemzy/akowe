import os
from decimal import Decimal

from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename

from akowe.models import db
from akowe.models.client import Client
from akowe.models.income import Income
from akowe.models.invoice import Invoice
from akowe.models.project import Project
from akowe.services.import_service import ImportService
from akowe.utils.timezone import convert_to_utc, convert_from_utc, local_date_input

bp = Blueprint("income", __name__, url_prefix="/income")


@bp.route("/", methods=["GET"])
@convert_from_utc
def index():
    # Show only current user's incomes
    incomes = Income.query.filter_by(user_id=current_user.id).order_by(Income.date.desc()).all()
    return render_template("income/index.html", incomes=incomes)


@bp.route("/new", methods=["GET", "POST"])
@convert_to_utc
def new():
    if request.method == "POST":
        try:
            date = local_date_input(request.form["date"])
            amount = Decimal(request.form["amount"])
            client_name = request.form["client"]
            project_name = request.form["project"]
            invoice_number = request.form["invoice"]

            # Check if client, project, and invoice IDs are provided in the form
            client_id = request.form.get("client_id")
            project_id = request.form.get("project_id")
            invoice_id = request.form.get("invoice_id")

            # Create income record with relationships if available
            income = Income(
                date=date,
                amount=amount,
                client=client_name,  # Always store the string version
                project=project_name,  # Always store the string version
                invoice=invoice_number,  # Always store the string version
                user_id=current_user.id  # Associate with current user
            )

            # If client_id and project_id are provided, use them for relationships
            if client_id and client_id.isdigit():
                income.client_id = int(client_id)
            
            if project_id and project_id.isdigit():
                income.project_id = int(project_id)

            # If invoice_id is provided, use it for relationship
            if invoice_id and invoice_id.isdigit():
                income.invoice_id = int(invoice_id)
            # Otherwise, try to look up by invoice number
            elif invoice_number:
                invoice = Invoice.query.filter_by(invoice_number=invoice_number).first()
                if invoice:
                    income.invoice_id = invoice.id

            db.session.add(income)
            db.session.commit()

            flash("Income record added successfully!", "success")
            return redirect(url_for("income.index"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding income record: {str(e)}", "error")

    # Get clients, projects, and invoices for dropdowns
    clients = Client.query.order_by(Client.name).all()
    projects = Project.query.order_by(Project.name).all()
    # Get only paid invoices that might be used for income tracking
    invoices = Invoice.query.filter_by(status="paid").order_by(Invoice.issue_date.desc()).all()
    
    return render_template("income/new.html", clients=clients, projects=projects, invoices=invoices)


@bp.route("/edit/<int:id>", methods=["GET", "POST"])
@convert_from_utc
def edit(id):
    income = Income.query.get_or_404(id)

    if request.method == "POST":
        try:
            income.date = local_date_input(request.form["date"])
            income.amount = Decimal(request.form["amount"])
            income.client = request.form["client"]
            income.project = request.form["project"]
            income.invoice = request.form["invoice"]

            # Update relationships if provided
            client_id = request.form.get("client_id")
            project_id = request.form.get("project_id")
            invoice_id = request.form.get("invoice_id")

            if client_id and client_id.isdigit():
                income.client_id = int(client_id)
            else:
                income.client_id = None
            
            if project_id and project_id.isdigit():
                income.project_id = int(project_id)
            else:
                income.project_id = None

            if invoice_id and invoice_id.isdigit():
                income.invoice_id = int(invoice_id)
            else:
                # Try to match by invoice number
                if income.invoice:
                    invoice = Invoice.query.filter_by(invoice_number=income.invoice).first()
                    if invoice:
                        income.invoice_id = invoice.id
                    else:
                        income.invoice_id = None
                else:
                    income.invoice_id = None

            db.session.commit()

            flash("Income record updated successfully!", "success")
            return redirect(url_for("income.index"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating income record: {str(e)}", "error")

    # Get clients, projects and invoices for dropdowns
    clients = Client.query.order_by(Client.name).all()
    
    # If income has a client_id, get projects for that client
    if income.client_id:
        client_projects = Project.query.filter_by(client_id=income.client_id).all()
    else:
        client_projects = Project.query.all()
    
    # Get paid invoices for dropdown
    invoices = Invoice.query.filter_by(status="paid").order_by(Invoice.issue_date.desc()).all()
    
    return render_template(
        "income/edit.html", 
        income=income, 
        clients=clients, 
        projects=client_projects,
        invoices=invoices
    )


@bp.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    income = Income.query.get_or_404(id)

    try:
        db.session.delete(income)
        db.session.commit()
        flash("Income record deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting income record: {str(e)}", "error")

    return redirect(url_for("income.index"))


@bp.route("/import", methods=["GET", "POST"])
def import_csv():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part", "error")
            return redirect(request.url)

        file = request.files["file"]

        if file.filename == "":
            flash("No selected file", "error")
            return redirect(request.url)

        if file:
            try:
                filename = secure_filename(file.filename)
                filepath = os.path.join(current_app.instance_path, filename)
                file.save(filepath)

                records, count = ImportService.import_income_csv(filepath)

                # Clean up the file
                os.remove(filepath)

                flash(f"Successfully imported {count} income records!", "success")
                return render_template("income/import_success.html", records=records, count=count)
            except Exception as e:
                flash(f"Error importing file: {str(e)}", "error")

    return render_template("income/import.html")


@bp.route("/get_projects/<int:client_id>", methods=["GET"])
def get_projects(client_id):
    """Get projects for a specific client for AJAX loading"""
    projects = Project.query.filter_by(client_id=client_id).all()
    return render_template("income/projects_dropdown.html", projects=projects)