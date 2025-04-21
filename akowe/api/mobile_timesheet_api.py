import os
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps

from flask import Blueprint, request, jsonify, current_app, g
from flask_login import current_user

from akowe.models import db
from akowe.models.timesheet import Timesheet
from akowe.models.client import Client
from akowe.models.project import Project
from akowe.api.mobile_api import token_required
from akowe.utils.timezone import to_utc, to_local_time, local_date_input

bp = Blueprint("mobile_timesheet", __name__, url_prefix="/api/timesheets")


@bp.route("/", methods=["GET"])
@token_required
def get_timesheets():
    """Get all timesheet entries with optional filtering"""
    # Get filter parameters
    status = request.args.get("status")
    client_id = request.args.get("client_id")
    project_id = request.args.get("project_id")
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    
    # Start with base query for current user
    query = Timesheet.query.filter_by(user_id=g.current_user.id)
    
    # Apply filters if provided
    if status:
        query = query.filter_by(status=status)
        
    if client_id:
        try:
            query = query.filter_by(client_id=int(client_id))
        except ValueError:
            return jsonify({"message": "Invalid client_id format"}), 400
            
    if project_id:
        try:
            query = query.filter_by(project_id=int(project_id))
        except ValueError:
            return jsonify({"message": "Invalid project_id format"}), 400
    
    if from_date:
        try:
            start_date = datetime.strptime(from_date, "%Y-%m-%d").date()
            query = query.filter(Timesheet.date >= start_date)
        except ValueError:
            return jsonify({"message": "Invalid from_date format. Use YYYY-MM-DD"}), 400
            
    if to_date:
        try:
            end_date = datetime.strptime(to_date, "%Y-%m-%d").date()
            query = query.filter(Timesheet.date <= end_date)
        except ValueError:
            return jsonify({"message": "Invalid to_date format. Use YYYY-MM-DD"}), 400
    
    # Execute query with ordering
    entries = query.order_by(Timesheet.date.desc()).all()
    
    # Format results
    result = []
    for entry in entries:
        # Get client and project names
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
            "amount": str(entry.amount),
            "status": entry.status,
            "invoice_id": entry.invoice_id,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
        })
    
    # Calculate totals
    total_hours = sum(entry.hours for entry in entries)
    total_amount = sum(entry.amount for entry in entries)
    unbilled_hours = sum(entry.hours for entry in entries if entry.status == "pending")
    unbilled_amount = sum(entry.amount for entry in entries if entry.status == "pending")
    
    return jsonify({
        "timesheets": result,
        "summary": {
            "total_hours": str(total_hours),
            "total_amount": str(total_amount),
            "unbilled_hours": str(unbilled_hours),
            "unbilled_amount": str(unbilled_amount),
            "count": len(entries)
        }
    })


@bp.route("/<int:id>", methods=["GET"])
@token_required
def get_timesheet(id):
    """Get a specific timesheet entry by ID"""
    entry = Timesheet.query.get_or_404(id)
    
    # Ensure the user can only view their own entries
    if entry.user_id != g.current_user.id:
        return jsonify({"message": "Unauthorized access to this timesheet entry"}), 403
    
    # Get client and project names
    client_name = entry.client_ref.name if entry.client_ref else "Unknown Client"
    project_name = entry.project_ref.name if entry.project_ref else "Unknown Project"
    
    return jsonify({
        "id": entry.id,
        "date": entry.date.isoformat(),
        "client_id": entry.client_id,
        "client_name": client_name,
        "project_id": entry.project_id,
        "project_name": project_name,
        "description": entry.description,
        "hours": str(entry.hours),
        "hourly_rate": str(entry.hourly_rate),
        "amount": str(entry.amount),
        "status": entry.status,
        "invoice_id": entry.invoice_id,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
    })


@bp.route("/", methods=["POST"])
@token_required
def create_timesheet():
    """Create a new timesheet entry"""
    if not request.is_json:
        return jsonify({"message": "Missing JSON data in request"}), 400
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ["date", "client_id", "project_id", "description", "hours"]
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"Missing required field: {field}"}), 400
    
    try:
        # Parse date
        try:
            date = datetime.strptime(data["date"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"message": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        # Validate client and project
        client = Client.query.get(data["client_id"])
        if not client or client.user_id != g.current_user.id:
            return jsonify({"message": "Invalid client_id"}), 400
            
        project = Project.query.get(data["project_id"])
        if not project or project.user_id != g.current_user.id:
            return jsonify({"message": "Invalid project_id"}), 400
        
        # Get hourly rate from project if available, otherwise use provided rate or user default
        hourly_rate = None
        if project and project.hourly_rate:
            hourly_rate = project.hourly_rate
        elif "hourly_rate" in data and data["hourly_rate"]:
            hourly_rate = Decimal(data["hourly_rate"])
        else:
            hourly_rate = g.current_user.hourly_rate or Decimal("0")
        
        # Create new timesheet entry
        entry = Timesheet(
            date=date,
            client_id=data["client_id"],
            project_id=data["project_id"],
            description=data["description"],
            hours=Decimal(data["hours"]),
            hourly_rate=hourly_rate,
            status="pending",
            user_id=g.current_user.id,
        )
        
        db.session.add(entry)
        db.session.commit()
        
        # Get client and project names for response
        client_name = entry.client_ref.name if entry.client_ref else "Unknown Client"
        project_name = entry.project_ref.name if entry.project_ref else "Unknown Project"
        
        return jsonify({
            "message": "Timesheet entry created successfully",
            "timesheet": {
                "id": entry.id,
                "date": entry.date.isoformat(),
                "client_id": entry.client_id,
                "client_name": client_name,
                "project_id": entry.project_id,
                "project_name": project_name,
                "description": entry.description,
                "hours": str(entry.hours),
                "hourly_rate": str(entry.hourly_rate),
                "amount": str(entry.amount),
                "status": entry.status,
            }
        }), 201
        
    except ValueError as e:
        return jsonify({"message": f"Invalid data: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating timesheet: {str(e)}")
        return jsonify({"message": f"Error creating timesheet entry: {str(e)}"}), 500


@bp.route("/<int:id>", methods=["PUT"])
@token_required
def update_timesheet(id):
    """Update an existing timesheet entry"""
    entry = Timesheet.query.get_or_404(id)
    
    # Ensure the user can only edit their own entries
    if entry.user_id != g.current_user.id:
        return jsonify({"message": "Unauthorized access to this timesheet entry"}), 403
    
    # Check if the entry is already billed
    if entry.status != "pending":
        return jsonify({"message": "Cannot edit a timesheet entry that has already been billed or paid"}), 400
    
    if not request.is_json:
        return jsonify({"message": "Missing JSON data in request"}), 400
    
    data = request.get_json()
    
    try:
        # Update fields if provided
        if "date" in data:
            try:
                entry.date = datetime.strptime(data["date"], "%Y-%m-%d").date()
            except ValueError:
                return jsonify({"message": "Invalid date format. Use YYYY-MM-DD"}), 400
        
        if "client_id" in data:
            client = Client.query.get(data["client_id"])
            if not client or client.user_id != g.current_user.id:
                return jsonify({"message": "Invalid client_id"}), 400
            entry.client_id = data["client_id"]
            
        if "project_id" in data:
            project = Project.query.get(data["project_id"])
            if not project or project.user_id != g.current_user.id:
                return jsonify({"message": "Invalid project_id"}), 400
            entry.project_id = data["project_id"]
            
            # Update hourly rate from project if available
            if project and project.hourly_rate and "hourly_rate" not in data:
                entry.hourly_rate = project.hourly_rate
        
        if "description" in data:
            entry.description = data["description"]
            
        if "hours" in data:
            entry.hours = Decimal(data["hours"])
            
        if "hourly_rate" in data:
            entry.hourly_rate = Decimal(data["hourly_rate"])
        
        db.session.commit()
        
        # Get client and project names for response
        client_name = entry.client_ref.name if entry.client_ref else "Unknown Client"
        project_name = entry.project_ref.name if entry.project_ref else "Unknown Project"
        
        return jsonify({
            "message": "Timesheet entry updated successfully",
            "timesheet": {
                "id": entry.id,
                "date": entry.date.isoformat(),
                "client_id": entry.client_id,
                "client_name": client_name,
                "project_id": entry.project_id,
                "project_name": project_name,
                "description": entry.description,
                "hours": str(entry.hours),
                "hourly_rate": str(entry.hourly_rate),
                "amount": str(entry.amount),
                "status": entry.status,
            }
        })
        
    except ValueError as e:
        return jsonify({"message": f"Invalid data: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating timesheet: {str(e)}")
        return jsonify({"message": f"Error updating timesheet entry: {str(e)}"}), 500


@bp.route("/<int:id>", methods=["DELETE"])
@token_required
def delete_timesheet(id):
    """Delete a timesheet entry"""
    entry = Timesheet.query.get_or_404(id)
    
    # Ensure the user can only delete their own entries
    if entry.user_id != g.current_user.id:
        return jsonify({"message": "Unauthorized access to this timesheet entry"}), 403
    
    # Check if the entry is already billed
    if entry.status != "pending":
        return jsonify({"message": "Cannot delete a timesheet entry that has already been billed or paid"}), 400
    
    try:
        db.session.delete(entry)
        db.session.commit()
        return jsonify({"message": "Timesheet entry deleted successfully"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting timesheet: {str(e)}")
        return jsonify({"message": f"Error deleting timesheet entry: {str(e)}"}), 500


@bp.route("/weekly", methods=["GET"])
@token_required
def get_weekly_timesheet():
    """Get weekly timesheet data"""
    # Get the requested week (default to current week)
    week_start_str = request.args.get("week_start")
    
    if week_start_str:
        try:
            week_start = datetime.strptime(week_start_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"message": "Invalid date format for week_start. Use YYYY-MM-DD"}), 400
    else:
        # Get current date and adjust to beginning of week (Monday)
        week_start = datetime.now().date()
        week_start = week_start - timedelta(days=week_start.weekday())
    
    # Calculate week end (Sunday)
    week_end = week_start + timedelta(days=6)
    
    # Get entries for the week
    entries = (
        Timesheet.query.filter(
            Timesheet.user_id == g.current_user.id,
            Timesheet.date >= week_start,
            Timesheet.date <= week_end,
        )
        .order_by(Timesheet.date)
        .all()
    )
    
    # Organize entries by day
    days = []
    daily_totals = {}
    
    for i in range(7):
        day_date = week_start + timedelta(days=i)
        day_entries = [e for e in entries if e.date == day_date]
        
        # Format entries for this day
        formatted_entries = []
        for entry in day_entries:
            client_name = entry.client_ref.name if entry.client_ref else "Unknown Client"
            project_name = entry.project_ref.name if entry.project_ref else "Unknown Project"
            
            formatted_entries.append({
                "id": entry.id,
                "client_id": entry.client_id,
                "client_name": client_name,
                "project_id": entry.project_id,
                "project_name": project_name,
                "description": entry.description,
                "hours": str(entry.hours),
                "hourly_rate": str(entry.hourly_rate),
                "amount": str(entry.amount),
                "status": entry.status,
            })
        
        day_hours = sum(e.hours for e in day_entries)
        
        days.append({
            "date": day_date.isoformat(),
            "day_of_week": day_date.strftime("%A"),
            "entries": formatted_entries,
            "total_hours": str(day_hours)
        })
        
        daily_totals[day_date.isoformat()] = str(day_hours)
    
    # Get total hours for the week
    total_hours = sum(Decimal(day["total_hours"]) for day in days)
    
    # Get previous and next week dates for navigation
    prev_week = (week_start - timedelta(days=7)).isoformat()
    next_week = (week_start + timedelta(days=7)).isoformat()
    
    return jsonify({
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "days": days,
        "total_hours": str(total_hours),
        "prev_week": prev_week,
        "next_week": next_week,
        "daily_totals": daily_totals
    })
