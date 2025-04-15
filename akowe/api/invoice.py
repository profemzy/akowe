import os
from datetime import datetime, timedelta
from decimal import Decimal

from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import current_user
from sqlalchemy import and_, or_

from akowe.models import db
from akowe.models.client import Client
from akowe.models.invoice import Invoice
from akowe.models.timesheet import Timesheet

bp = Blueprint("invoice", __name__, url_prefix="/invoice")


def generate_invoice_number():
    """Generate a unique invoice number"""
    # Format: INV-YYYYMM-XXXX where XXXX is a sequential number
    today = datetime.now()
    year_month = today.strftime("%Y%m")

    # Get the last invoice number for this year/month
    last_invoice = (
        Invoice.query.filter(Invoice.invoice_number.like(f"INV-{year_month}-%"))
        .order_by(Invoice.invoice_number.desc())
        .first()
    )

    if last_invoice:
        # Extract the sequence number
        try:
            seq_number = int(last_invoice.invoice_number.split("-")[-1])
            next_seq = seq_number + 1
        except (ValueError, IndexError):
            next_seq = 1
    else:
        next_seq = 1

    # Format with leading zeros (e.g., INV-202504-0001)
    return f"INV-{year_month}-{next_seq:04d}"


@bp.route("/", methods=["GET"])
def index():
    """List all invoices"""
    # Get filter parameters
    status = request.args.get("status", "all")
    client = request.args.get("client", "all")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    # Build query
    query = Invoice.query.filter_by(user_id=current_user.id)

    # Apply filters
    if status != "all":
        query = query.filter_by(status=status)

    if client != "all":
        # Try to find client by ID first, then fallback to name
        try:
            client_id = int(client)
            query = query.filter_by(client_id=client_id)
        except ValueError:
            # Legacy support - look up client by name
            client_obj = Client.query.filter_by(name=client, user_id=current_user.id).first()
            if client_obj:
                query = query.filter_by(client_id=client_obj.id)

    if from_date:
        try:
            from_date = datetime.strptime(from_date, "%Y-%m-%d").date()
            query = query.filter(Invoice.issue_date >= from_date)
        except ValueError:
            flash("Invalid from date format", "error")

    if to_date:
        try:
            to_date = datetime.strptime(to_date, "%Y-%m-%d").date()
            query = query.filter(Invoice.issue_date <= to_date)
        except ValueError:
            flash("Invalid to date format", "error")

    # Get invoices ordered by issue date (most recent first)
    invoices = query.order_by(Invoice.issue_date.desc()).all()

    # Get unique clients for filter dropdown from Client model
    clients = Client.query.filter_by(user_id=current_user.id).order_by(Client.name).all()

    # Calculate totals
    total_paid = sum(inv.total for inv in invoices if inv.status == "paid")
    total_outstanding = sum(inv.total for inv in invoices if inv.status in ["sent", "overdue"])
    total_draft = sum(inv.total for inv in invoices if inv.status == "draft")

    return render_template(
        "invoice/index.html",
        invoices=invoices,
        clients=clients,
        status=status,
        client_filter=client,
        from_date=from_date,
        to_date=to_date,
        total_paid=total_paid,
        total_outstanding=total_outstanding,
        total_draft=total_draft,
    )


@bp.route("/new", methods=["GET", "POST"])
def new():
    """Create a new invoice"""
    if request.method == "POST":
        try:
            # Get data from form
            client_id = request.form["client"]
            issue_date = datetime.strptime(request.form["issue_date"], "%Y-%m-%d").date()
            due_date = datetime.strptime(request.form["due_date"], "%Y-%m-%d").date()
            notes = request.form["notes"]
            tax_rate = Decimal(request.form["tax_rate"])

            # Get client
            client = Client.query.get(client_id)
            if not client:
                flash("Selected client not found", "error")
                return redirect(url_for("invoice.new"))

            # Get custom line items
            custom_items_json = request.form.get("custom_items", "[]")

            # Generate invoice number
            invoice_number = generate_invoice_number()

            # Get company name from environment variable or use default
            company_name = os.environ.get("COMPANY_NAME", "Akowe")

            # Create invoice
            invoice = Invoice(
                invoice_number=invoice_number,
                client_id=client.id,
                company_name=company_name,
                issue_date=issue_date,
                due_date=due_date,
                notes=notes,
                tax_rate=tax_rate,
                status="draft",
                user_id=current_user.id,
            )

            db.session.add(invoice)
            db.session.flush()  # Get the ID without committing

            # Process selected timesheet entries
            timesheet_ids = request.form.getlist("timesheet_entries")
            if timesheet_ids:
                timesheet_entries = Timesheet.query.filter(
                    Timesheet.id.in_(timesheet_ids),
                    Timesheet.user_id == current_user.id,
                    Timesheet.status == "pending",
                ).all()

                for entry in timesheet_entries:
                    entry.invoice_id = invoice.id
                    entry.status = "billed"

            # Process custom line items
            import json

            try:
                custom_items = json.loads(custom_items_json)
                if custom_items and isinstance(custom_items, list):
                    for item in custom_items:
                        # Create timesheet entry for each custom item
                        if "description" in item and "hours" in item and "rate" in item:
                            custom_entry = Timesheet(
                                date=issue_date,  # Use invoice date
                                client_id=client.id,  # New foreign key
                                project="Custom Item",
                                description=item["description"],
                                hours=Decimal(str(item["hours"])),
                                hourly_rate=Decimal(str(item["rate"])),
                                status="billed",
                                invoice_id=invoice.id,
                                user_id=current_user.id,
                            )
                            db.session.add(custom_entry)
            except (json.JSONDecodeError, ValueError) as e:
                flash(f"Warning: Could not process custom items: {str(e)}", "warning")

            # Calculate totals
            invoice.calculate_totals()

            db.session.commit()
            flash("Invoice created successfully!", "success")
            return redirect(url_for("invoice.view", id=invoice.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating invoice: {str(e)}", "error")

    # Get unbilled timesheet entries
    unbilled_entries = (
        Timesheet.query.filter_by(user_id=current_user.id, status="pending")
        .order_by(Timesheet.date)
        .all()
    )

    # Group entries by client
    clients = {}
    for entry in unbilled_entries:
        client_name = entry.client_ref.name if entry.client_ref else "Unknown Client"
        client_id = entry.client_id
        # Use client_id as key to avoid duplicates with different names
        if client_id not in clients:
            clients[client_id] = {"name": client_name, "entries": []}
        clients[client_id]["entries"].append(entry)

    # Get all clients from Client model
    clients_list = Client.query.filter_by(user_id=current_user.id).order_by(Client.name).all()

    # Default hourly rate
    default_hourly_rate = current_user.hourly_rate or Decimal("0.00")

    # Default due date (30 days from today)
    today = datetime.now().date()
    default_due_date = today + timedelta(days=30)

    # Reformat clients data for the template
    client_entries = {}
    for client_id, data in clients.items():
        client_entries[data["name"]] = data["entries"]

    return render_template(
        "invoice/new.html",
        clients=client_entries,
        clients_list=clients_list,
        unbilled_entries=unbilled_entries,
        issue_date=today,
        due_date=default_due_date,
        default_hourly_rate=default_hourly_rate,
    )


@bp.route("/view/<int:id>", methods=["GET"])
def view(id):
    """View an invoice"""
    invoice = Invoice.query.get_or_404(id)

    # Ensure the user can only view their own invoices
    if invoice.user_id != current_user.id and not current_user.is_admin:
        flash("You are not authorized to view this invoice.", "error")
        return redirect(url_for("invoice.index"))

    return render_template("invoice/view.html", invoice=invoice)


@bp.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    """Edit an invoice"""
    invoice = Invoice.query.get_or_404(id)

    # Ensure the user can only edit their own invoices
    if invoice.user_id != current_user.id and not current_user.is_admin:
        flash("You are not authorized to edit this invoice.", "error")
        return redirect(url_for("invoice.index"))

    # Check if the invoice can be edited
    if invoice.status not in ["draft"]:
        flash("Cannot edit an invoice that has already been sent or paid.", "error")
        return redirect(url_for("invoice.view", id=invoice.id))

    if request.method == "POST":
        try:
            # Update invoice details
            invoice.client = request.form["client"]
            invoice.issue_date = datetime.strptime(request.form["issue_date"], "%Y-%m-%d").date()
            invoice.due_date = datetime.strptime(request.form["due_date"], "%Y-%m-%d").date()
            invoice.notes = request.form["notes"]
            invoice.tax_rate = Decimal(request.form["tax_rate"])

            # Get currently selected entries
            current_entries = {entry.id: entry for entry in invoice.timesheet_entries}

            # Get newly selected entries
            new_entry_ids = set(map(int, request.form.getlist("timesheet_entries")))

            # Remove entries that are no longer selected
            for entry_id, entry in current_entries.items():
                if entry_id not in new_entry_ids:
                    entry.invoice_id = None
                    entry.status = "pending"

            # Add newly selected entries
            if new_entry_ids:
                # Get eligible entries (unbilled or already on this invoice)
                eligible_entries = Timesheet.query.filter(
                    Timesheet.user_id == current_user.id,
                    or_(
                        Timesheet.status == "pending",
                        and_(Timesheet.status == "billed", Timesheet.invoice_id == invoice.id),
                    ),
                ).all()

                eligible_entries_dict = {entry.id: entry for entry in eligible_entries}

                for entry_id in new_entry_ids:
                    if entry_id in eligible_entries_dict:
                        entry = eligible_entries_dict[entry_id]
                        entry.invoice_id = invoice.id
                        entry.status = "billed"

            # Recalculate totals
            invoice.calculate_totals()

            db.session.commit()
            flash("Invoice updated successfully!", "success")
            return redirect(url_for("invoice.view", id=invoice.id))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating invoice: {str(e)}", "error")

    # Get all unbilled entries
    unbilled_entries = (
        Timesheet.query.filter_by(user_id=current_user.id, status="pending")
        .order_by(Timesheet.date)
        .all()
    )

    # Get entries already on this invoice
    invoice_entries = (
        Timesheet.query.filter_by(invoice_id=invoice.id).order_by(Timesheet.date).all()
    )

    # Combine entries
    all_available_entries = unbilled_entries + invoice_entries

    # Group entries by client
    clients = {}
    for entry in all_available_entries:
        if entry.client not in clients:
            clients[entry.client] = []
        clients[entry.client].append(entry)

    return render_template(
        "invoice/edit.html", invoice=invoice, clients=clients, all_entries=all_available_entries
    )


@bp.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    """Delete an invoice"""
    invoice = Invoice.query.get_or_404(id)

    # Ensure the user can only delete their own invoices
    if invoice.user_id != current_user.id and not current_user.is_admin:
        flash("You are not authorized to delete this invoice.", "error")
        return redirect(url_for("invoice.index"))

    # Check if the invoice can be deleted
    if invoice.status not in ["draft"]:
        flash("Cannot delete an invoice that has already been sent or paid.", "error")
        return redirect(url_for("invoice.view", id=invoice.id))

    try:
        # Update timesheet entries
        for entry in invoice.timesheet_entries:
            entry.invoice_id = None
            entry.status = "pending"

        # Delete the invoice
        db.session.delete(invoice)
        db.session.commit()
        flash("Invoice deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting invoice: {str(e)}", "error")

    return redirect(url_for("invoice.index"))


@bp.route("/mark_sent/<int:id>", methods=["POST"])
def mark_sent(id):
    """Mark an invoice as sent"""
    invoice = Invoice.query.get_or_404(id)

    # Ensure the user can only update their own invoices
    if invoice.user_id != current_user.id and not current_user.is_admin:
        flash("You are not authorized to update this invoice.", "error")
        return redirect(url_for("invoice.index"))

    # Check if the invoice can be marked as sent
    if invoice.status != "draft":
        flash("This invoice is not in draft status.", "error")
        return redirect(url_for("invoice.view", id=invoice.id))

    try:
        invoice.status = "sent"
        invoice.sent_date = datetime.utcnow()
        db.session.commit()
        flash("Invoice marked as sent!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating invoice: {str(e)}", "error")

    return redirect(url_for("invoice.view", id=invoice.id))


@bp.route("/mark_paid/<int:id>", methods=["POST"])
def mark_paid(id):
    """Mark an invoice as paid"""
    invoice = Invoice.query.get_or_404(id)

    # Ensure the user can only update their own invoices
    if invoice.user_id != current_user.id and not current_user.is_admin:
        flash("You are not authorized to update this invoice.", "error")
        return redirect(url_for("invoice.index"))

    # Check if the invoice can be marked as paid
    if invoice.status not in ["sent", "overdue"]:
        flash("This invoice cannot be marked as paid.", "error")
        return redirect(url_for("invoice.view", id=invoice.id))

    try:
        invoice.status = "paid"
        invoice.paid_date = datetime.utcnow()
        invoice.payment_method = request.form.get("payment_method", "")
        invoice.payment_reference = request.form.get("payment_reference", "")

        # Update timesheet entries
        for entry in invoice.timesheet_entries:
            entry.status = "paid"

        db.session.commit()
        flash("Invoice marked as paid!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating invoice: {str(e)}", "error")

    return redirect(url_for("invoice.view", id=invoice.id))


@bp.route("/print/<int:id>", methods=["GET"])
def print_invoice(id):
    """Print-friendly view of an invoice"""
    invoice = Invoice.query.get_or_404(id)

    # Ensure the user can only view their own invoices
    if invoice.user_id != current_user.id and not current_user.is_admin:
        flash("You are not authorized to view this invoice.", "error")
        return redirect(url_for("invoice.index"))

    return render_template("invoice/print.html", invoice=invoice)
