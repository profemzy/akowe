from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required
from decimal import Decimal
from sqlalchemy import or_

from akowe.models import db
from akowe.models.project import Project
from akowe.models.client import Client
from akowe.models.timesheet import Timesheet

bp = Blueprint('project', __name__, url_prefix='/project')


@bp.route('/', methods=['GET'])
@login_required
def index():
    """List all projects"""
    # Get filter parameters
    client_id = request.args.get('client_id', 'all')
    status = request.args.get('status', 'all')
    search = request.args.get('search', '')
    
    # Build query
    query = Project.query.filter_by(user_id=current_user.id)
    
    # Apply filters
    if client_id != 'all':
        query = query.filter_by(client_id=client_id)
        
    if status != 'all':
        query = query.filter_by(status=status)
        
    if search:
        query = query.filter(or_(
            Project.name.ilike(f'%{search}%'),
            Project.description.ilike(f'%{search}%')
        ))
    
    # Get projects
    projects = query.order_by(Project.name).all()
    
    # Get clients for filter dropdown
    clients = Client.query.filter_by(user_id=current_user.id).order_by(Client.name).all()
    
    return render_template('project/index.html', 
                          projects=projects, 
                          clients=clients,
                          client_id=client_id,
                          status=status,
                          search=search)


@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    """Create a new project"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form['name']
            client_id = request.form['client_id']
            description = request.form.get('description', '')
            status = request.form.get('status', 'active')
            
            # Get hourly rate if provided
            hourly_rate = None
            if request.form.get('hourly_rate'):
                hourly_rate = Decimal(request.form['hourly_rate'])
            
            # Check if client exists
            client = Client.query.get(client_id)
            if not client or client.user_id != current_user.id:
                flash('Invalid client selected', 'error')
                return redirect(url_for('project.new'))
            
            # Check if project name already exists for this client
            existing_project = Project.query.filter_by(
                name=name,
                client_id=client_id,
                user_id=current_user.id
            ).first()
            
            if existing_project:
                flash(f'A project with the name "{name}" already exists for this client', 'error')
                clients = Client.query.filter_by(user_id=current_user.id).order_by(Client.name).all()
                return render_template('project/new.html', clients=clients)
            
            # Create new project
            project = Project(
                name=name,
                client_id=client_id,
                description=description,
                status=status,
                hourly_rate=hourly_rate,
                user_id=current_user.id
            )
            
            db.session.add(project)
            db.session.commit()
            
            flash('Project created successfully!', 'success')
            return redirect(url_for('project.index'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating project: {str(e)}', 'error')
    
    # Get clients for dropdown
    clients = Client.query.filter_by(user_id=current_user.id).order_by(Client.name).all()
    
    # Check if we have any clients
    if not clients:
        flash('You need to create a client before creating a project', 'warning')
        return redirect(url_for('client.new'))
    
    return render_template('project/new.html', clients=clients)


@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit a project"""
    project = Project.query.get_or_404(id)
    
    # Ensure the user can only edit their own projects
    if project.user_id != current_user.id and not current_user.is_admin:
        flash('You are not authorized to edit this project', 'error')
        return redirect(url_for('project.index'))
    
    if request.method == 'POST':
        try:
            # Update project details
            project.name = request.form['name']
            project.client_id = request.form['client_id']
            project.description = request.form.get('description', '')
            project.status = request.form.get('status', 'active')
            
            # Update hourly rate if provided
            if request.form.get('hourly_rate'):
                project.hourly_rate = Decimal(request.form['hourly_rate'])
            else:
                project.hourly_rate = None
            
            db.session.commit()
            flash('Project updated successfully!', 'success')
            return redirect(url_for('project.index'))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating project: {str(e)}', 'error')
    
    # Get clients for dropdown
    clients = Client.query.filter_by(user_id=current_user.id).order_by(Client.name).all()
    
    return render_template('project/edit.html', project=project, clients=clients)


@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Delete a project"""
    project = Project.query.get_or_404(id)
    
    # Ensure the user can only delete their own projects
    if project.user_id != current_user.id and not current_user.is_admin:
        flash('You are not authorized to delete this project', 'error')
        return redirect(url_for('project.index'))
    
    # Check if project has any timesheet entries
    if project.timesheet_entries.count() > 0:
        flash('Cannot delete project because it has associated timesheet entries', 'error')
        return redirect(url_for('project.index'))
    
    try:
        db.session.delete(project)
        db.session.commit()
        flash('Project deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting project: {str(e)}', 'error')
    
    return redirect(url_for('project.index'))


@bp.route('/view/<int:id>', methods=['GET'])
@login_required
def view(id):
    """View a project's details and activity"""
    project = Project.query.get_or_404(id)
    
    # Ensure the user can only view their own projects
    if project.user_id != current_user.id and not current_user.is_admin:
        flash('You are not authorized to view this project', 'error')
        return redirect(url_for('project.index'))
    
    # Get project's timesheet entries
    timesheet_entries = Timesheet.query.filter_by(
        project_id=project.id
    ).order_by(Timesheet.date.desc()).all()
    
    # Calculate project metrics
    total_hours = sum(entry.hours for entry in timesheet_entries)
    unbilled_hours = sum(entry.hours for entry in timesheet_entries if entry.status == 'pending')
    billed_hours = sum(entry.hours for entry in timesheet_entries if entry.status == 'billed')
    paid_hours = sum(entry.hours for entry in timesheet_entries if entry.status == 'paid')
    
    return render_template('project/view.html',
                          project=project,
                          timesheet_entries=timesheet_entries,
                          total_hours=total_hours,
                          unbilled_hours=unbilled_hours,
                          billed_hours=billed_hours,
                          paid_hours=paid_hours)


@bp.route('/api/list', methods=['GET'])
@login_required
def api_list():
    """API endpoint to get a list of projects (for AJAX calls)"""
    client_id = request.args.get('client_id')
    
    # If client_id is provided, filter projects by client
    if client_id:
        projects = Project.query.filter_by(
            user_id=current_user.id,
            client_id=client_id,
            status='active'  # Only show active projects
        ).order_by(Project.name).all()
    else:
        projects = Project.query.filter_by(
            user_id=current_user.id,
            status='active'
        ).order_by(Project.name).all()
    
    return jsonify({
        'projects': [{'id': p.id, 'name': p.name, 'client_id': p.client_id, 'hourly_rate': float(p.hourly_rate) if p.hourly_rate else None} for p in projects]
    })


@bp.route('/api/create', methods=['POST'])
@login_required
def api_create():
    """API endpoint to create a new project (for AJAX calls)"""
    try:
        data = request.json
        name = data.get('name', '').strip()
        client_id = data.get('client_id')
        
        if not name:
            return jsonify({'success': False, 'message': 'Project name is required'}), 400
        
        if not client_id:
            return jsonify({'success': False, 'message': 'Client is required'}), 400
        
        # Check if client exists
        client = Client.query.get(client_id)
        if not client or client.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Invalid client selected'}), 400
        
        # Check if project already exists for this client
        existing_project = Project.query.filter_by(
            name=name,
            client_id=client_id,
            user_id=current_user.id
        ).first()
        
        if existing_project:
            return jsonify({
                'success': False,
                'message': f'A project with the name "{name}" already exists for this client',
                'project': {'id': existing_project.id, 'name': existing_project.name}
            }), 409
        
        # Get hourly rate if provided
        hourly_rate = None
        if 'hourly_rate' in data and data['hourly_rate']:
            hourly_rate = Decimal(str(data['hourly_rate']))
        
        # Create new project
        project = Project(
            name=name,
            client_id=client_id,
            description=data.get('description', ''),
            status='active',
            hourly_rate=hourly_rate,
            user_id=current_user.id
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Project created successfully',
            'project': {
                'id': project.id,
                'name': project.name,
                'client_id': project.client_id,
                'hourly_rate': float(project.hourly_rate) if project.hourly_rate else None
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
