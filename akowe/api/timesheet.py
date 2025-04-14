from datetime import datetime
from decimal import Decimal
from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask_login import current_user

from akowe.models import db
from akowe.models.timesheet import Timesheet
from akowe.models.invoice import Invoice
from akowe.models.client import Client
from akowe.models.project import Project

bp = Blueprint('timesheet', __name__, url_prefix='/timesheet')

@bp.route('/', methods=['GET'])
def index():
    """Show all timesheet entries"""
    # Get filter parameters
    status = request.args.get('status', 'all')
    client = request.args.get('client', 'all')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    
    # Build query
    query = Timesheet.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    if status != 'all':
        query = query.filter_by(status=status)
    
    if client != 'all':
        query = query.filter_by(client=client)
    
    if from_date:
        try:
            from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
            query = query.filter(Timesheet.date >= from_date)
        except ValueError:
            flash('Invalid from date format', 'error')
    
    if to_date:
        try:
            to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
            query = query.filter(Timesheet.date <= to_date)
        except ValueError:
            flash('Invalid to date format', 'error')
    
    # Get timesheet entries ordered by date (most recent first)
    entries = query.order_by(Timesheet.date.desc()).all()
    
    # Get unique clients for filter dropdown
    clients = db.session.query(Timesheet.client).distinct().all()
    clients = [c[0] for c in clients]
    
    # Calculate totals
    total_hours = sum(entry.hours for entry in entries)
    total_amount = sum(entry.amount for entry in entries)
    unbilled_hours = sum(entry.hours for entry in entries if entry.status == 'pending')
    unbilled_amount = sum(entry.amount for entry in entries if entry.status == 'pending')
    
    return render_template('timesheet/index.html', 
                           entries=entries,
                           clients=clients,
                           status=status,
                           client_filter=client,
                           from_date=from_date,
                           to_date=to_date,
                           total_hours=total_hours,
                           total_amount=total_amount,
                           unbilled_hours=unbilled_hours,
                           unbilled_amount=unbilled_amount)

@bp.route('/new', methods=['GET', 'POST'])
def new():
    """Add a new timesheet entry"""
    if request.method == 'POST':
        try:
            date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            client_id = request.form.get('client_id')
            project_id = request.form.get('project_id')
            description = request.form['description']
            hours = Decimal(request.form['hours'])
            
            # Validate client and project
            if not client_id or not project_id:
                flash('Client and project are required', 'error')
                return redirect(url_for('timesheet.new'))
            
            # Get hourly rate from project if available
            hourly_rate = None
            project = Project.query.get(project_id)
            if project:
                hourly_rate = project.hourly_rate
            
            # If no hourly rate from project, use the one from the form or user default
            if not hourly_rate:
                hourly_rate = Decimal(request.form['hourly_rate'] or current_user.hourly_rate or 0)
            
            # Create new timesheet entry
            entry = Timesheet(
                date=date,
                client_id=client_id,
                project_id=project_id,
                description=description,
                hours=hours,
                hourly_rate=hourly_rate,
                status='pending',
                user_id=current_user.id
            )
            
            db.session.add(entry)
            db.session.commit()
            
            flash('Timesheet entry added successfully!', 'success')
            return redirect(url_for('timesheet.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding timesheet entry: {str(e)}', 'error')
    
    # Get all clients
    clients = Client.query.filter_by(user_id=current_user.id).order_by(Client.name).all()
    
    # Get active projects
    projects = Project.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).order_by(Project.name).all()
    
    return render_template('timesheet/new.html', 
                          clients=clients, 
                          projects=projects,
                          default_hourly_rate=current_user.hourly_rate or "",
                          today_date=datetime.now().strftime('%Y-%m-%d'))

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    """Edit a timesheet entry"""
    entry = Timesheet.query.get_or_404(id)
    
    # Ensure the user can only edit their own entries
    if entry.user_id != current_user.id and not current_user.is_admin:
        flash('You are not authorized to edit this timesheet entry.', 'error')
        return redirect(url_for('timesheet.index'))
    
    # Check if the entry is already billed
    if entry.status != 'pending':
        flash('Cannot edit a timesheet entry that has already been billed or paid.', 'error')
        return redirect(url_for('timesheet.index'))
    
    if request.method == 'POST':
        try:
            entry.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
            
            client_id = request.form.get('client_id')
            project_id = request.form.get('project_id')
            
            # Validate client and project
            if not client_id or not project_id:
                flash('Client and project are required', 'error')
                return render_template('timesheet/edit.html', entry=entry, clients=clients, projects=projects)
            
            entry.client_id = client_id
            entry.project_id = project_id
            
            # Get hourly rate from project if available
            hourly_rate = None
            project = Project.query.get(project_id)
            if project:
                hourly_rate = project.hourly_rate
            
            entry.description = request.form['description']
            entry.hours = Decimal(request.form['hours'])
            
            # Use project hourly rate if available, otherwise use form value
            if hourly_rate:
                entry.hourly_rate = hourly_rate
            else:
                entry.hourly_rate = Decimal(request.form['hourly_rate'])
            
            db.session.commit()
            
            flash('Timesheet entry updated successfully!', 'success')
            return redirect(url_for('timesheet.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating timesheet entry: {str(e)}', 'error')
    
    # Get all clients
    clients = Client.query.filter_by(user_id=current_user.id).order_by(Client.name).all()
    
    # Get all projects
    projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.name).all()
    
    # Get current client and project for pre-selection
    selected_client = None
    if entry.client_id:
        selected_client = Client.query.get(entry.client_id)
    
    selected_project = None
    if entry.project_id:
        selected_project = Project.query.get(entry.project_id)
    
    return render_template('timesheet/edit.html', 
                          entry=entry,
                          clients=clients,
                          projects=projects,
                          selected_client=selected_client,
                          selected_project=selected_project)

@bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    """Delete a timesheet entry"""
    entry = Timesheet.query.get_or_404(id)
    
    # Ensure the user can only delete their own entries
    if entry.user_id != current_user.id and not current_user.is_admin:
        flash('You are not authorized to delete this timesheet entry.', 'error')
        return redirect(url_for('timesheet.index'))
    
    # Check if the entry is already billed
    if entry.status != 'pending':
        flash('Cannot delete a timesheet entry that has already been billed or paid.', 'error')
        return redirect(url_for('timesheet.index'))
    
    try:
        db.session.delete(entry)
        db.session.commit()
        flash('Timesheet entry deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting timesheet entry: {str(e)}', 'error')
    
    return redirect(url_for('timesheet.index'))

@bp.route('/weekly', methods=['GET'])
def weekly():
    """Show weekly timesheet view"""
    # Get the requested week (default to current week)
    week_start_str = request.args.get('week_start')
    
    if week_start_str:
        try:
            week_start = datetime.strptime(week_start_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format for week start', 'error')
            week_start = datetime.now().date()
            # Get to beginning of week (Monday)
            week_start = week_start - timedelta(days=week_start.weekday())
    else:
        # Get current date and adjust to beginning of week (Monday)
        week_start = datetime.now().date()
        week_start = week_start - timedelta(days=week_start.weekday())
    
    # Calculate week end (Sunday)
    from datetime import timedelta
    week_end = week_start + timedelta(days=6)
    
    # Get entries for the week
    entries = Timesheet.query.filter(
        Timesheet.user_id == current_user.id,
        Timesheet.date >= week_start,
        Timesheet.date <= week_end
    ).order_by(Timesheet.date).all()
    
    # Organize entries by day
    days = []
    daily_totals = {}
    
    for i in range(7):
        day_date = week_start + timedelta(days=i)
        day_entries = [e for e in entries if e.date == day_date]
        day_hours = sum(e.hours for e in day_entries)
        
        days.append({
            'date': day_date,
            'entries': day_entries,
            'total_hours': day_hours
        })
        
        daily_totals[day_date.strftime('%Y-%m-%d')] = day_hours
    
    # Get total hours for the week
    total_hours = sum(day['total_hours'] for day in days)
    
    # Get previous and next week dates for navigation
    prev_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)
    
    return render_template('timesheet/weekly.html',
                          week_start=week_start,
                          week_end=week_end,
                          days=days,
                          total_hours=total_hours,
                          prev_week=prev_week,
                          next_week=next_week,
                          daily_totals=daily_totals)

@bp.route('/quick_add', methods=['POST'])
def quick_add():
    """Quickly add a timesheet entry (AJAX)"""
    if not request.is_json:
        return jsonify({'error': 'Invalid request format'}), 400
    
    try:
        data = request.get_json()
        
        date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        client = data['client']
        project = data['project']
        description = data['description']
        hours = Decimal(data['hours'])
        hourly_rate = Decimal(data.get('hourly_rate') or current_user.hourly_rate or 0)
        
        # Create new timesheet entry
        entry = Timesheet(
            date=date,
            client=client,
            project=project,
            description=description,
            hours=hours,
            hourly_rate=hourly_rate,
            status='pending',
            user_id=current_user.id
        )
        
        db.session.add(entry)
        db.session.commit()
        
        return jsonify({
            'id': entry.id,
            'date': entry.date.strftime('%Y-%m-%d'),
            'client': entry.client,
            'project': entry.project,
            'description': entry.description,
            'hours': float(entry.hours),
            'amount': float(entry.amount)
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400