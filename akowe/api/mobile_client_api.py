import os
from datetime import datetime
from functools import wraps

from flask import Blueprint, request, jsonify, current_app, g
from flask_login import current_user

from akowe.models import db
from akowe.models.client import Client
from akowe.api.mobile_api import token_required

bp = Blueprint("mobile_client", __name__, url_prefix="/api/clients")


@bp.route("/", methods=["GET"])
@token_required
def get_clients():
    """Get all clients with optional filtering"""
    # Get query parameters for filtering
    name = request.args.get("name")
    
    # Start with base query for current user
    query = Client.query.filter_by(user_id=g.current_user.id)
    
    # Apply filters if provided
    if name:
        query = query.filter(Client.name.ilike(f"%{name}%"))
    
    # Execute query with ordering
    clients = query.order_by(Client.name).all()
    
    # Format results
    result = []
    for client in clients:
        result.append({
            "id": client.id,
            "name": client.name,
            "email": client.email,
            "phone": client.phone,
            "address": client.address,
            "contact_person": client.contact_person,
            "notes": client.notes,
            "created_at": client.created_at.isoformat() if client.created_at else None,
            "updated_at": client.updated_at.isoformat() if client.updated_at else None,
            "project_count": client.projects.count(),
            "invoice_count": client.invoices.count(),
            "timesheet_count": client.timesheet_entries.count()
        })
    
    return jsonify({
        "clients": result,
        "count": len(result)
    })


@bp.route("/<int:id>", methods=["GET"])
@token_required
def get_client(id):
    """Get a specific client by ID"""
    client = Client.query.get_or_404(id)
    
    # Ensure the user can only view their own clients
    if client.user_id != g.current_user.id:
        return jsonify({"message": "Unauthorized access to this client"}), 403
    
    # Get projects for this client
    projects = []
    for project in client.projects:
        projects.append({
            "id": project.id,
            "name": project.name,
            "status": project.status,
            "hourly_rate": str(project.hourly_rate) if project.hourly_rate else None
        })
    
    # Get recent invoices for this client
    invoices = []
    for invoice in client.invoices.order_by(db.desc("issue_date")).limit(5):
        invoices.append({
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "issue_date": invoice.issue_date.isoformat(),
            "due_date": invoice.due_date.isoformat(),
            "total": str(invoice.total),
            "status": invoice.status
        })
    
    # Get recent timesheet entries for this client
    timesheet_entries = []
    for entry in client.timesheet_entries.order_by(db.desc("date")).limit(5):
        project_name = entry.project_ref.name if entry.project_ref else "Unknown Project"
        timesheet_entries.append({
            "id": entry.id,
            "date": entry.date.isoformat(),
            "project": project_name,
            "description": entry.description,
            "hours": str(entry.hours),
            "amount": str(entry.amount),
            "status": entry.status
        })
    
    return jsonify({
        "id": client.id,
        "name": client.name,
        "email": client.email,
        "phone": client.phone,
        "address": client.address,
        "contact_person": client.contact_person,
        "notes": client.notes,
        "created_at": client.created_at.isoformat() if client.created_at else None,
        "updated_at": client.updated_at.isoformat() if client.updated_at else None,
        "projects": projects,
        "recent_invoices": invoices,
        "recent_timesheet_entries": timesheet_entries
    })


@bp.route("/", methods=["POST"])
@token_required
def create_client():
    """Create a new client"""
    if not request.is_json:
        return jsonify({"message": "Missing JSON data in request"}), 400
    
    data = request.get_json()
    
    # Validate required fields
    if "name" not in data or not data["name"]:
        return jsonify({"message": "Client name is required"}), 400
    
    try:
        # Check if client with this name already exists for this user
        existing_client = Client.query.filter_by(
            name=data["name"], user_id=g.current_user.id
        ).first()
        
        if existing_client:
            return jsonify({"message": "A client with this name already exists"}), 400
        
        # Create new client
        client = Client(
            name=data["name"],
            email=data.get("email"),
            phone=data.get("phone"),
            address=data.get("address"),
            contact_person=data.get("contact_person"),
            notes=data.get("notes"),
            user_id=g.current_user.id
        )
        
        db.session.add(client)
        db.session.commit()
        
        return jsonify({
            "message": "Client created successfully",
            "client": {
                "id": client.id,
                "name": client.name,
                "email": client.email,
                "phone": client.phone,
                "address": client.address,
                "contact_person": client.contact_person,
                "notes": client.notes
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating client: {str(e)}")
        return jsonify({"message": f"Error creating client: {str(e)}"}), 500


@bp.route("/<int:id>", methods=["PUT"])
@token_required
def update_client(id):
    """Update an existing client"""
    client = Client.query.get_or_404(id)
    
    # Ensure the user can only edit their own clients
    if client.user_id != g.current_user.id:
        return jsonify({"message": "Unauthorized access to this client"}), 403
    
    if not request.is_json:
        return jsonify({"message": "Missing JSON data in request"}), 400
    
    data = request.get_json()
    
    try:
        # Check if name is being changed and if it would conflict
        if "name" in data and data["name"] != client.name:
            existing_client = Client.query.filter_by(
                name=data["name"], user_id=g.current_user.id
            ).first()
            
            if existing_client and existing_client.id != client.id:
                return jsonify({"message": "A client with this name already exists"}), 400
            
            client.name = data["name"]
        
        # Update other fields if provided
        if "email" in data:
            client.email = data["email"]
            
        if "phone" in data:
            client.phone = data["phone"]
            
        if "address" in data:
            client.address = data["address"]
            
        if "contact_person" in data:
            client.contact_person = data["contact_person"]
            
        if "notes" in data:
            client.notes = data["notes"]
        
        db.session.commit()
        
        return jsonify({
            "message": "Client updated successfully",
            "client": {
                "id": client.id,
                "name": client.name,
                "email": client.email,
                "phone": client.phone,
                "address": client.address,
                "contact_person": client.contact_person,
                "notes": client.notes
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating client: {str(e)}")
        return jsonify({"message": f"Error updating client: {str(e)}"}), 500


@bp.route("/<int:id>", methods=["DELETE"])
@token_required
def delete_client(id):
    """Delete a client"""
    client = Client.query.get_or_404(id)
    
    # Ensure the user can only delete their own clients
    if client.user_id != g.current_user.id:
        return jsonify({"message": "Unauthorized access to this client"}), 403
    
    # Check if client has related records
    if client.projects.count() > 0 or client.invoices.count() > 0 or client.timesheet_entries.count() > 0:
        return jsonify({
            "message": "Cannot delete client with related projects, invoices, or timesheet entries",
            "project_count": client.projects.count(),
            "invoice_count": client.invoices.count(),
            "timesheet_count": client.timesheet_entries.count()
        }), 400
    
    try:
        db.session.delete(client)
        db.session.commit()
        return jsonify({"message": "Client deleted successfully"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting client: {str(e)}")
        return jsonify({"message": f"Error deleting client: {str(e)}"}), 500


@bp.route("/<int:id>/projects", methods=["GET"])
@token_required
def get_client_projects(id):
    """Get all projects for a specific client"""
    client = Client.query.get_or_404(id)
    
    # Ensure the user can only view their own clients
    if client.user_id != g.current_user.id:
        return jsonify({"message": "Unauthorized access to this client"}), 403
    
    # Get projects for this client
    projects = []
    for project in client.projects:
        projects.append({
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "hourly_rate": str(project.hourly_rate) if project.hourly_rate else None,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            "timesheet_count": project.timesheet_entries.count()
        })
    
    return jsonify({
        "client_id": client.id,
        "client_name": client.name,
        "projects": projects,
        "count": len(projects)
    })


@bp.route("/<int:id>/invoices", methods=["GET"])
@token_required
def get_client_invoices(id):
    """Get all invoices for a specific client"""
    client = Client.query.get_or_404(id)
    
    # Ensure the user can only view their own clients
    if client.user_id != g.current_user.id:
        return jsonify({"message": "Unauthorized access to this client"}), 403
    
    # Get invoices for this client
    invoices = []
    for invoice in client.invoices.order_by(db.desc("issue_date")):
        invoices.append({
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "issue_date": invoice.issue_date.isoformat(),
            "due_date": invoice.due_date.isoformat(),
            "subtotal": str(invoice.subtotal),
            "tax_amount": str(invoice.tax_amount),
            "total": str(invoice.total),
            "status": invoice.status,
            "sent_date": invoice.sent_date.isoformat() if invoice.sent_date else None,
            "paid_date": invoice.paid_date.isoformat() if invoice.paid_date else None
        })
    
    return jsonify({
        "client_id": client.id,
        "client_name": client.name,
        "invoices": invoices,
        "count": len(invoices)
    })


@bp.route("/<int:id>/timesheets", methods=["GET"])
@token_required
def get_client_timesheets(id):
    """Get all timesheet entries for a specific client"""
    client = Client.query.get_or_404(id)
    
    # Ensure the user can only view their own clients
    if client.user_id != g.current_user.id:
        return jsonify({"message": "Unauthorized access to this client"}), 403
    
    # Get timesheet entries for this client
    entries = []
    for entry in client.timesheet_entries.order_by(db.desc("date")):
        project_name = entry.project_ref.name if entry.project_ref else "Unknown Project"
        entries.append({
            "id": entry.id,
            "date": entry.date.isoformat(),
            "project_id": entry.project_id,
            "project_name": project_name,
            "description": entry.description,
            "hours": str(entry.hours),
            "hourly_rate": str(entry.hourly_rate),
            "amount": str(entry.amount),
            "status": entry.status,
            "invoice_id": entry.invoice_id
        })
    
    # Calculate totals
    total_hours = sum(entry.hours for entry in client.timesheet_entries)
    total_amount = sum(entry.amount for entry in client.timesheet_entries)
    unbilled_hours = sum(entry.hours for entry in client.timesheet_entries if entry.status == "pending")
    unbilled_amount = sum(entry.amount for entry in client.timesheet_entries if entry.status == "pending")
    
    return jsonify({
        "client_id": client.id,
        "client_name": client.name,
        "timesheet_entries": entries,
        "count": len(entries),
        "summary": {
            "total_hours": str(total_hours),
            "total_amount": str(total_amount),
            "unbilled_hours": str(unbilled_hours),
            "unbilled_amount": str(unbilled_amount)
        }
    })
