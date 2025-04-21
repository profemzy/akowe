import os
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps

from flask import Blueprint, request, jsonify, current_app, g
from flask_login import current_user

from akowe.models import db
from akowe.models.invoice import Invoice
from akowe.models.client import Client
from akowe.models.timesheet import Timesheet
from akowe.models.income import Income
from akowe.api.mobile_api import token_required
from akowe.api.invoice import generate_invoice_number

bp = Blueprint("mobile_invoice", __name__, url_prefix="/api/invoices")


@bp.route("/", methods=["GET"])
@token_required
def get_invoices():
    """Get all invoices with optional filtering"""
    # Get filter parameters
    status = request.args.get("status")
    client_id = request.args.get("client_id")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    
    # Start with base query for current user
    query = Invoice.query.filter_by(user_id=g.current_user.id)
    
    # Apply filters if provided
    if status:
        query = query.filter_by(status=status)
        
    if client_id:
        try:
            query = query.filter_by(client_id=int(client_id))
        except ValueError:
            return jsonify({"message": "Invalid client_id format"}), 400
    
    if from_date:
        try:
            start_date = datetime.strptime(from_date, "%Y-%m-%d").date()
            query = query.filter(Invoice.issue_date >= start_date)
        except ValueError:
            return jsonify({"message": "Invalid from_date format. Use YYYY-MM-DD"}), 400
            
    if to_date:
        try:
            end_date = datetime.strptime(to_date, "%Y-%m-%d").date()
            query = query.filter(Invoice.issue_date <= end_date)
        except ValueError:
            return jsonify({"message": "Invalid to_date format. Use YYYY-MM-DD"}), 400
    
    # Execute query with ordering
    invoices = query.order_by(Invoice.issue_date.desc()).all()
    
    # Format results
    result = []
    for invoice in invoices:
        client_name = invoice.client_ref.name if invoice.client_ref else "Unknown Client"
        result.append({
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "client_id": invoice.client_id,
            "client_name": client_name,
            "issue_date": invoice.issue_date.isoformat(),
            "due_date": invoice.due_date.isoformat(),
            "subtotal": str(invoice.subtotal),
            "tax_rate": str(invoice.tax_rate),
            "tax_amount": str(invoice.tax_amount),
            "total": str(invoice.total),
            "status": invoice.status,
            "sent_date": invoice.sent_date.isoformat() if invoice.sent_date else None,
            "paid_date": invoice.paid_date.isoformat() if invoice.paid_date else None,
            "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
            "updated_at": invoice.updated_at.isoformat() if invoice.updated_at else None,
            "timesheet_count": len(invoice.timesheet_entries)
        })
    
    # Calculate totals
    total_paid = sum(invoice.total for invoice in invoices if invoice.status == "paid")
    total_outstanding = sum(invoice.total for invoice in invoices if invoice.status in ["sent", "overdue"])
    total_draft = sum(invoice.total for invoice in invoices if invoice.status == "draft")
    
    return jsonify({
        "invoices": result,
        "count": len(result),
        "summary": {
            "total_paid": str(total_paid),
            "total_outstanding": str(total_outstanding),
            "total_draft": str(total_draft),
            "total_all": str(total_paid + total_outstanding + total_draft)
        }
    })


@bp.route("/<int:id>", methods=["GET"])
@token_required
def get_invoice(id):
    """Get a specific invoice by ID"""
    invoice = Invoice.query.get_or_404(id)
    
    # Ensure the user can only view their own invoices
    if invoice.user_id != g.current_user.id:
        return jsonify({"message": "Unauthorized access to this invoice"}), 403
    
    # Get client info
    client_name = invoice.client_ref.name if invoice.client_ref else "Unknown Client"
    
    # Get timesheet entries for this invoice
    timesheet_entries = []
    for entry in invoice.timesheet_entries:
        project_name = entry.project_ref.name if entry.project_ref else "Unknown Project"
        timesheet_entries.append({
            "id": entry.id,
            "date": entry.date.isoformat(),
            "client_id": entry.client_id,
            "project_id": entry.project_id,
            "project_name": project_name,
            "description": entry.description,
            "hours": str(entry.hours),
            "hourly_rate": str(entry.hourly_rate),
            "amount": str(entry.amount),
            "status": entry.status
        })
    
    return jsonify({
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "client_id": invoice.client_id,
        "client_name": client_name,
        "company_name": invoice.company_name,
        "issue_date": invoice.issue_date.isoformat(),
        "due_date": invoice.due_date.isoformat(),
        "notes": invoice.notes,
        "subtotal": str(invoice.subtotal),
        "tax_rate": str(invoice.tax_rate),
        "tax_amount": str(invoice.tax_amount),
        "total": str(invoice.total),
        "status": invoice.status,
        "sent_date": invoice.sent_date.isoformat() if invoice.sent_date else None,
        "paid_date": invoice.paid_date.isoformat() if invoice.paid_date else None,
        "payment_method": invoice.payment_method,
        "payment_reference": invoice.payment_reference,
        "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
        "updated_at": invoice.updated_at.isoformat() if invoice.updated_at else None,
        "timesheet_entries": timesheet_entries
    })


@bp.route("/", methods=["POST"])
@token_required
def create_invoice():
    """Create a new invoice"""
    if not request.is_json:
        return jsonify({"message": "Missing JSON data in request"}), 400
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ["client_id", "issue_date", "due_date"]
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"Missing required field: {field}"}), 400
    
    try:
        # Validate client
        client = Client.query.get(data["client_id"])
        if not client or client.user_id != g.current_user.id:
            return jsonify({"message": "Invalid client_id"}), 400
        
        # Parse dates
        try:
            issue_date = datetime.strptime(data["issue_date"], "%Y-%m-%d").date()
            due_date = datetime.strptime(data["due_date"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"message": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Parse tax rate
        tax_rate = Decimal("0")
        if "tax_rate" in data:
            try:
                tax_rate = Decimal(data["tax_rate"])
            except (ValueError, TypeError):
                return jsonify({"message": "Invalid tax_rate format"}), 400
        
        # Generate invoice number
        invoice_number = generate_invoice_number()
        
        # Get company name from environment variable or use default
        company_name = os.environ.get("COMPANY_NAME", "Akowe")
        
        # Create new invoice
        invoice = Invoice(
            invoice_number=invoice_number,
            client_id=client.id,
            company_name=company_name,
            issue_date=issue_date,
            due_date=due_date,
            notes=data.get("notes"),
            tax_rate=tax_rate,
            status="draft",
            user_id=g.current_user.id
        )
        
        db.session.add(invoice)
        db.session.flush()  # Get the ID without committing
        
        # Process selected timesheet entries if provided
        if "timesheet_ids" in data and isinstance(data["timesheet_ids"], list):
            timesheet_ids = data["timesheet_ids"]
            timesheet_entries = Timesheet.query.filter(
                Timesheet.id.in_(timesheet_ids),
                Timesheet.user_id == g.current_user.id,
                Timesheet.status == "pending"
            ).all()
            
            for entry in timesheet_entries:
                entry.invoice_id = invoice.id
                entry.status = "billed"
        
        # Calculate totals
        invoice.calculate_totals()
        
        db.session.commit()
        
        return jsonify({
            "message": "Invoice created successfully",
            "invoice": {
                "id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "client_id": invoice.client_id,
                "client_name": client.name,
                "issue_date": invoice.issue_date.isoformat(),
                "due_date": invoice.due_date.isoformat(),
                "subtotal": str(invoice.subtotal),
                "tax_rate": str(invoice.tax_rate),
                "tax_amount": str(invoice.tax_amount),
                "total": str(invoice.total),
                "status": invoice.status,
                "timesheet_count": len(invoice.timesheet_entries)
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating invoice: {str(e)}")
        return jsonify({"message": f"Error creating invoice: {str(e)}"}), 500


@bp.route("/<int:id>", methods=["PUT"])
@token_required
def update_invoice(id):
    """Update an existing invoice"""
    invoice = Invoice.query.get_or_404(id)
    
    # Ensure the user can only edit their own invoices
    if invoice.user_id != g.current_user.id:
        return jsonify({"message": "Unauthorized access to this invoice"}), 403
    
    # Check if the invoice can be edited
    if invoice.status not in ["draft"]:
        return jsonify({"message": "Cannot edit an invoice that has already been sent or paid"}), 400
    
    if not request.is_json:
        return jsonify({"message": "Missing JSON data in request"}), 400
    
    data = request.get_json()
    
    try:
        # Update client if provided
        if "client_id" in data:
            client = Client.query.get(data["client_id"])
            if not client or client.user_id != g.current_user.id:
                return jsonify({"message": "Invalid client_id"}), 400
            invoice.client_id = data["client_id"]
        
        # Update dates if provided
        if "issue_date" in data:
            try:
                invoice.issue_date = datetime.strptime(data["issue_date"], "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"message": "Invalid issue_date format. Use YYYY-MM-DD"}), 400
                
        if "due_date" in data:
            try:
                invoice.due_date = datetime.strptime(data["due_date"], "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"message": "Invalid due_date format. Use YYYY-MM-DD"}), 400
        
        # Update other fields if provided
        if "notes" in data:
            invoice.notes = data["notes"]
            
        if "tax_rate" in data:
            try:
                invoice.tax_rate = Decimal(data["tax_rate"])
            except (ValueError, TypeError):
                return jsonify({"message": "Invalid tax_rate format"}), 400
        
        # Update timesheet entries if provided
        if "timesheet_ids" in data and isinstance(data["timesheet_ids"], list):
            # Get currently selected entries
            current_entries = {entry.id: entry for entry in invoice.timesheet_entries}
            
            # Get newly selected entries
            new_entry_ids = set(map(int, data["timesheet_ids"]))
            
            # Remove entries that are no longer selected
            for entry_id, entry in current_entries.items():
                if entry_id not in new_entry_ids:
                    entry.invoice_id = None
                    entry.status = "pending"
            
            # Add newly selected entries
            if new_entry_ids:
                # Get eligible entries (unbilled or already on this invoice)
                eligible_entries = Timesheet.query.filter(
                    Timesheet.user_id == g.current_user.id,
                    db.or_(
                        Timesheet.status == "pending",
                        db.and_(Timesheet.status == "billed", Timesheet.invoice_id == invoice.id)
                    )
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
        
        # Get client name for response
        client_name = invoice.client_ref.name if invoice.client_ref else "Unknown Client"
        
        return jsonify({
            "message": "Invoice updated successfully",
            "invoice": {
                "id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "client_id": invoice.client_id,
                "client_name": client_name,
                "issue_date": invoice.issue_date.isoformat(),
                "due_date": invoice.due_date.isoformat(),
                "subtotal": str(invoice.subtotal),
                "tax_rate": str(invoice.tax_rate),
                "tax_amount": str(invoice.tax_amount),
                "total": str(invoice.total),
                "status": invoice.status,
                "timesheet_count": len(invoice.timesheet_entries)
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating invoice: {str(e)}")
        return jsonify({"message": f"Error updating invoice: {str(e)}"}), 500


@bp.route("/<int:id>", methods=["DELETE"])
@token_required
def delete_invoice(id):
    """Delete an invoice"""
    invoice = Invoice.query.get_or_404(id)
    
    # Ensure the user can only delete their own invoices
    if invoice.user_id != g.current_user.id:
        return jsonify({"message": "Unauthorized access to this invoice"}), 403
    
    # Check if the invoice can be deleted
    if invoice.status not in ["draft"]:
        return jsonify({"message": "Cannot delete an invoice that has already been sent or paid"}), 400
    
    try:
        # Update timesheet entries
        for entry in invoice.timesheet_entries:
            entry.invoice_id = None
            entry.status = "pending"
        
        # Delete the invoice
        db.session.delete(invoice)
        db.session.commit()
        return jsonify({"message": "Invoice deleted successfully"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting invoice: {str(e)}")
        return jsonify({"message": f"Error deleting invoice: {str(e)}"}), 500


@bp.route("/<int:id>/mark-sent", methods=["POST"])
@token_required
def mark_sent(id):
    """Mark an invoice as sent"""
    invoice = Invoice.query.get_or_404(id)
    
    # Ensure the user can only update their own invoices
    if invoice.user_id != g.current_user.id:
        return jsonify({"message": "Unauthorized access to this invoice"}), 403
    
    # Check if the invoice can be marked as sent
    if invoice.status != "draft":
        return jsonify({"message": "This invoice is not in draft status"}), 400
    
    try:
        invoice.status = "sent"
        invoice.sent_date = datetime.utcnow()
        db.session.commit()
        return jsonify({"message": "Invoice marked as sent"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error marking invoice as sent: {str(e)}")
        return jsonify({"message": f"Error marking invoice as sent: {str(e)}"}), 500


@bp.route("/<int:id>/mark-paid", methods=["POST"])
@token_required
def mark_paid(id):
    """Mark an invoice as paid"""
    invoice = Invoice.query.get_or_404(id)
    
    # Ensure the user can only update their own invoices
    if invoice.user_id != g.current_user.id:
        return jsonify({"message": "Unauthorized access to this invoice"}), 403
    
    # Check if the invoice can be marked as paid
    if invoice.status not in ["sent", "overdue"]:
        return jsonify({"message": "This invoice cannot be marked as paid"}), 400
    
    if not request.is_json:
        return jsonify({"message": "Missing JSON data in request"}), 400
    
    data = request.get_json()
    
    try:
        invoice.status = "paid"
        payment_date = datetime.utcnow()
        invoice.paid_date = payment_date
        invoice.payment_method = data.get("payment_method", "")
        invoice.payment_reference = data.get("payment_reference", "")
        
        # Update timesheet entries
        for entry in invoice.timesheet_entries:
            entry.status = "paid"
        
        # Create income record associated with this invoice
        # Check if income record for this invoice already exists to avoid duplicates
        existing_income = Income.query.filter_by(invoice_id=invoice.id).first()
        
        if not existing_income:
            # Get client and project information
            client_name = invoice.client_ref.name if invoice.client_ref else "Unknown"
            
            # For project, we'll use the first project from timesheet entries or default value
            project_name = "Invoice Payment"
            project_id = None
            
            if invoice.timesheet_entries:
                first_entry = invoice.timesheet_entries[0]
                if hasattr(first_entry, 'project_ref') and first_entry.project_ref:
                    project_name = first_entry.project_ref.name
                    project_id = first_entry.project_id
            
            # Create income record
            income = Income(
                date=payment_date.date(),
                amount=invoice.total,
                client=client_name,
                project=project_name,
                invoice=invoice.invoice_number,
                client_id=invoice.client_id,
                project_id=project_id,
                invoice_id=invoice.id,
                user_id=invoice.user_id
            )
            db.session.add(income)
        
        db.session.commit()
        return jsonify({
            "message": "Invoice marked as paid",
            "income_created": not existing_income
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error marking invoice as paid: {str(e)}")
        return jsonify({"message": f"Error marking invoice as paid: {str(e)}"}), 500


@bp.route("/unbilled-timesheets", methods=["GET"])
@token_required
def get_unbilled_timesheets():
    """Get all unbilled timesheet entries"""
    # Get filter parameters
    client_id = request.args.get("client_id")
    
    # Start with base query for unbilled entries
    query = Timesheet.query.filter_by(user_id=g.current_user.id, status="pending")
    
    # Apply client filter if provided
    if client_id:
        try:
            query = query.filter_by(client_id=int(client_id))
        except ValueError:
            return jsonify({"message": "Invalid client_id format"}), 400
    
    # Execute query with ordering
    entries = query.order_by(Timesheet.date).all()
    
    # Format results
    result = []
    for entry in entries:
        client_name = entry.client_ref.name if entry.client_ref else "Unknown Client"
        project_name = entry.project_ref.name if entry.project_ref else "Unknown Project"
        
        result.append({
            "id": entry.id,
            "date": entry.date.isoformat(),
            "client_id": entry.client_id,
            "client_name": client_name,
            "project_id": entry.project_id,
            "project_name": project_name,
            "description": entry.description,
            "hours": str(entry.hours),
            "hourly_rate": str(entry.hourly_rate),
            "amount": str(entry.amount)
        })
    
    # Group entries by client
    clients = {}
    for entry in result:
        client_id = entry["client_id"]
        if client_id not in clients:
            clients[client_id] = {
                "client_id": client_id,
                "client_name": entry["client_name"],
                "entries": [],
                "total_hours": Decimal("0"),
                "total_amount": Decimal("0")
            }
        clients[client_id]["entries"].append(entry)
        clients[client_id]["total_hours"] += Decimal(entry["hours"])
        clients[client_id]["total_amount"] += Decimal(entry["amount"])
    
    # Convert to list and format decimal values
    clients_list = []
    for client_data in clients.values():
        clients_list.append({
            "client_id": client_data["client_id"],
            "client_name": client_data["client_name"],
            "entries": client_data["entries"],
            "total_hours": str(client_data["total_hours"]),
            "total_amount": str(client_data["total_amount"]),
            "entry_count": len(client_data["entries"])
        })
    
    # Sort by client name
    clients_list.sort(key=lambda x: x["client_name"])
    
    return jsonify({
        "clients": clients_list,
        "total_entries": len(result),
        "total_hours": str(sum(Decimal(entry["hours"]) for entry in result)),
        "total_amount": str(sum(Decimal(entry["amount"]) for entry in result))
    })


@bp.route("/statuses", methods=["GET"])
@token_required
def get_invoice_statuses():
    """Get available invoice statuses"""
    statuses = ["draft", "sent", "paid", "overdue", "cancelled"]
    return jsonify({"statuses": statuses})
