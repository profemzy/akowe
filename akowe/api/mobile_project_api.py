import os
from datetime import datetime
from decimal import Decimal
from functools import wraps

from flask import Blueprint, request, jsonify, current_app, g
from flask_login import current_user

from akowe.models import db
from akowe.models.project import Project
from akowe.models.client import Client
from akowe.api.mobile_api import token_required

bp = Blueprint("mobile_project", __name__, url_prefix="/api/projects")


@bp.route("/", methods=["GET"])
@token_required
def get_projects():
    """Get all projects with optional filtering"""
    # Get query parameters for filtering
    name = request.args.get("name")
    client_id = request.args.get("client_id")
    status = request.args.get("status")
    
    # Start with base query for current user
    query = Project.query.filter_by(user_id=g.current_user.id)
    
    # Apply filters if provided
    if name:
        query = query.filter(Project.name.ilike(f"%{name}%"))
        
    if client_id:
        try:
            query = query.filter_by(client_id=int(client_id))
        except ValueError:
            return jsonify({"message": "Invalid client_id format"}), 400
            
    if status:
        query = query.filter_by(status=status)
    
    # Execute query with ordering
    projects = query.order_by(Project.name).all()
    
    # Format results
    result = []
    for project in projects:
        client_name = project.client.name if project.client else "Unknown Client"
        result.append({
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "hourly_rate": str(project.hourly_rate) if project.hourly_rate else None,
            "client_id": project.client_id,
            "client_name": client_name,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
            "timesheet_count": project.timesheet_entries.count()
        })
    
    return jsonify({
        "projects": result,
        "count": len(result)
    })


@bp.route("/<int:id>", methods=["GET"])
@token_required
def get_project(id):
    """Get a specific project by ID"""
    project = Project.query.get_or_404(id)
    
    # Ensure the user can only view their own projects
    if project.user_id != g.current_user.id:
        return jsonify({"message": "Unauthorized access to this project"}), 403
    
    # Get client info
    client_name = project.client.name if project.client else "Unknown Client"
    
    # Get recent timesheet entries for this project
    timesheet_entries = []
    for entry in project.timesheet_entries.order_by(db.desc("date")).limit(10):
        timesheet_entries.append({
            "id": entry.id,
            "date": entry.date.isoformat(),
            "description": entry.description,
            "hours": str(entry.hours),
            "hourly_rate": str(entry.hourly_rate),
            "amount": str(entry.amount),
            "status": entry.status,
            "invoice_id": entry.invoice_id
        })
    
    # Calculate project statistics
    total_hours = sum(entry.hours for entry in project.timesheet_entries)
    total_amount = sum(entry.amount for entry in project.timesheet_entries)
    unbilled_hours = sum(entry.hours for entry in project.timesheet_entries if entry.status == "pending")
    unbilled_amount = sum(entry.amount for entry in project.timesheet_entries if entry.status == "pending")
    
    return jsonify({
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "hourly_rate": str(project.hourly_rate) if project.hourly_rate else None,
        "client_id": project.client_id,
        "client_name": client_name,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        "recent_timesheet_entries": timesheet_entries,
        "statistics": {
            "total_hours": str(total_hours),
            "total_amount": str(total_amount),
            "unbilled_hours": str(unbilled_hours),
            "unbilled_amount": str(unbilled_amount),
            "timesheet_count": project.timesheet_entries.count()
        }
    })


@bp.route("/", methods=["POST"])
@token_required
def create_project():
    """Create a new project"""
    if not request.is_json:
        return jsonify({"message": "Missing JSON data in request"}), 400
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ["name", "client_id"]
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"Missing required field: {field}"}), 400
    
    try:
        # Validate client
        client = Client.query.get(data["client_id"])
        if not client or client.user_id != g.current_user.id:
            return jsonify({"message": "Invalid client_id"}), 400
        
        # Check if project with this name already exists for this client
        existing_project = Project.query.filter_by(
            name=data["name"], client_id=data["client_id"], user_id=g.current_user.id
        ).first()
        
        if existing_project:
            return jsonify({"message": "A project with this name already exists for this client"}), 400
        
        # Parse hourly rate if provided
        hourly_rate = None
        if "hourly_rate" in data and data["hourly_rate"]:
            try:
                hourly_rate = Decimal(data["hourly_rate"])
            except (ValueError, TypeError):
                return jsonify({"message": "Invalid hourly_rate format"}), 400
        
        # Create new project
        project = Project(
            name=data["name"],
            description=data.get("description"),
            status=data.get("status", "active"),
            hourly_rate=hourly_rate,
            client_id=data["client_id"],
            user_id=g.current_user.id
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            "message": "Project created successfully",
            "project": {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "hourly_rate": str(project.hourly_rate) if project.hourly_rate else None,
                "client_id": project.client_id,
                "client_name": client.name
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating project: {str(e)}")
        return jsonify({"message": f"Error creating project: {str(e)}"}), 500


@bp.route("/<int:id>", methods=["PUT"])
@token_required
def update_project(id):
    """Update an existing project"""
    project = Project.query.get_or_404(id)
    
    # Ensure the user can only edit their own projects
    if project.user_id != g.current_user.id:
        return jsonify({"message": "Unauthorized access to this project"}), 403
    
    if not request.is_json:
        return jsonify({"message": "Missing JSON data in request"}), 400
    
    data = request.get_json()
    
    try:
        # Check if client_id is being changed and if it's valid
        if "client_id" in data and data["client_id"] != project.client_id:
            client = Client.query.get(data["client_id"])
            if not client or client.user_id != g.current_user.id:
                return jsonify({"message": "Invalid client_id"}), 400
            
            project.client_id = data["client_id"]
        
        # Check if name is being changed and if it would conflict
        if "name" in data and data["name"] != project.name:
            existing_project = Project.query.filter_by(
                name=data["name"], 
                client_id=project.client_id, 
                user_id=g.current_user.id
            ).first()
            
            if existing_project and existing_project.id != project.id:
                return jsonify({"message": "A project with this name already exists for this client"}), 400
            
            project.name = data["name"]
        
        # Update other fields if provided
        if "description" in data:
            project.description = data["description"]
            
        if "status" in data:
            project.status = data["status"]
            
        if "hourly_rate" in data:
            if data["hourly_rate"] is None:
                project.hourly_rate = None
            else:
                try:
                    project.hourly_rate = Decimal(data["hourly_rate"])
                except (ValueError, TypeError):
                    return jsonify({"message": "Invalid hourly_rate format"}), 400
        
        db.session.commit()
        
        # Get client name for response
        client_name = project.client.name if project.client else "Unknown Client"
        
        return jsonify({
            "message": "Project updated successfully",
            "project": {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "status": project.status,
                "hourly_rate": str(project.hourly_rate) if project.hourly_rate else None,
                "client_id": project.client_id,
                "client_name": client_name
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating project: {str(e)}")
        return jsonify({"message": f"Error updating project: {str(e)}"}), 500


@bp.route("/<int:id>", methods=["DELETE"])
@token_required
def delete_project(id):
    """Delete a project"""
    project = Project.query.get_or_404(id)
    
    # Ensure the user can only delete their own projects
    if project.user_id != g.current_user.id:
        return jsonify({"message": "Unauthorized access to this project"}), 403
    
    # Check if project has related timesheet entries
    if project.timesheet_entries.count() > 0:
        return jsonify({
            "message": "Cannot delete project with related timesheet entries",
            "timesheet_count": project.timesheet_entries.count()
        }), 400
    
    try:
        db.session.delete(project)
        db.session.commit()
        return jsonify({"message": "Project deleted successfully"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting project: {str(e)}")
        return jsonify({"message": f"Error deleting project: {str(e)}"}), 500


@bp.route("/<int:id>/timesheets", methods=["GET"])
@token_required
def get_project_timesheets(id):
    """Get all timesheet entries for a specific project"""
    project = Project.query.get_or_404(id)
    
    # Ensure the user can only view their own projects
    if project.user_id != g.current_user.id:
        return jsonify({"message": "Unauthorized access to this project"}), 403
    
    # Get client info
    client_name = project.client.name if project.client else "Unknown Client"
    
    # Get timesheet entries for this project
    entries = []
    for entry in project.timesheet_entries.order_by(db.desc("date")):
        entries.append({
            "id": entry.id,
            "date": entry.date.isoformat(),
            "description": entry.description,
            "hours": str(entry.hours),
            "hourly_rate": str(entry.hourly_rate),
            "amount": str(entry.amount),
            "status": entry.status,
            "invoice_id": entry.invoice_id,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "updated_at": entry.updated_at.isoformat() if entry.updated_at else None
        })
    
    # Calculate totals
    total_hours = sum(entry.hours for entry in project.timesheet_entries)
    total_amount = sum(entry.amount for entry in project.timesheet_entries)
    unbilled_hours = sum(entry.hours for entry in project.timesheet_entries if entry.status == "pending")
    unbilled_amount = sum(entry.amount for entry in project.timesheet_entries if entry.status == "pending")
    
    return jsonify({
        "project_id": project.id,
        "project_name": project.name,
        "client_id": project.client_id,
        "client_name": client_name,
        "timesheet_entries": entries,
        "count": len(entries),
        "summary": {
            "total_hours": str(total_hours),
            "total_amount": str(total_amount),
            "unbilled_hours": str(unbilled_hours),
            "unbilled_amount": str(unbilled_amount)
        }
    })


@bp.route("/statuses", methods=["GET"])
@token_required
def get_project_statuses():
    """Get available project statuses"""
    statuses = ["active", "completed", "archived"]
    return jsonify({"statuses": statuses})
