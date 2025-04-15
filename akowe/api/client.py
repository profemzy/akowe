from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify
from flask_login import current_user, login_required
from sqlalchemy import or_

from akowe.models import db
from akowe.models.client import Client
from akowe.models.invoice import Invoice
from akowe.models.timesheet import Timesheet

bp = Blueprint('client', __name__, url_prefix='/client')


@bp.route('/', methods=['GET'])
@login_required
def index():
    """List all clients"""
    query = Client.query.filter_by(user_id=current_user.id)
    
    # Get search parameter
    search = request.args.get('search', '')
    if search:
        query = query.filter(or_(
            Client.name.ilike(f'%{search}%'),
            Client.email.ilike(f'%{search}%'),
            Client.contact_person.ilike(f'%{search}%')
        ))
    
    # Get clients
    clients = query.order_by(Client.name).all()
    
    return render_template('client/index.html', clients=clients, search=search)


@bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    """Create a new client"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form['name']
            email = request.form.get('email', '')
            phone = request.form.get('phone', '')
            address = request.form.get('address', '')
            contact_person = request.form.get('contact_person', '')
            notes = request.form.get('notes', '')
            
            # Check if client already exists
            existing_client = Client.query.filter_by(
                name=name, 
                user_id=current_user.id
            ).first()
            
            if existing_client:
                flash(f'A client with the name "{name}" already exists.', 'error')
                return render_template('client/new.html')
            
            # Create new client
            client = Client(
                name=name,
                email=email,
                phone=phone,
                address=address,
                contact_person=contact_person,
                notes=notes,
                user_id=current_user.id
            )
            
            db.session.add(client)
            db.session.commit()
            flash('Client created successfully!', 'success')
            return redirect(url_for('client.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating client: {str(e)}', 'error')
    
    return render_template('client/new.html')


@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit a client"""
    client = Client.query.get_or_404(id)
    
    # Ensure the user can only edit their own clients
    if client.user_id != current_user.id and not current_user.is_admin:
        flash('You are not authorized to edit this client.', 'error')
        return redirect(url_for('client.index'))
    
    if request.method == 'POST':
        try:
            # Update client details
            client.name = request.form['name']
            client.email = request.form.get('email', '')
            client.phone = request.form.get('phone', '')
            client.address = request.form.get('address', '')
            client.contact_person = request.form.get('contact_person', '')
            client.notes = request.form.get('notes', '')
            
            db.session.commit()
            flash('Client updated successfully!', 'success')
            return redirect(url_for('client.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating client: {str(e)}', 'error')
    
    return render_template('client/edit.html', client=client)


@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Delete a client"""
    client = Client.query.get_or_404(id)
    
    # Ensure the user can only delete their own clients
    if client.user_id != current_user.id and not current_user.is_admin:
        flash('You are not authorized to delete this client.', 'error')
        return redirect(url_for('client.index'))
    
    # Check if client has any invoices or timesheet entries
    if client.invoices.count() > 0 or client.timesheet_entries.count() > 0:
        flash('Cannot delete client because it has associated invoices or timesheet entries.', 'error')
        return redirect(url_for('client.index'))
    
    try:
        db.session.delete(client)
        db.session.commit()
        flash('Client deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting client: {str(e)}', 'error')
    
    return redirect(url_for('client.index'))


@bp.route('/view/<int:id>', methods=['GET'])
@login_required
def view(id):
    """View a client's details and activity"""
    client = Client.query.get_or_404(id)
    
    # Ensure the user can only view their own clients
    if client.user_id != current_user.id and not current_user.is_admin:
        flash('You are not authorized to view this client.', 'error')
        return redirect(url_for('client.index'))
    
    # Get client's invoices
    invoices = Invoice.query.filter_by(client_id=client.id).order_by(Invoice.issue_date.desc()).all()
    
    # Get client's timesheet entries
    timesheet_entries = Timesheet.query.filter_by(client_id=client.id).order_by(Timesheet.date.desc()).all()
    
    return render_template('client/view.html', 
                          client=client, 
                          invoices=invoices, 
                          timesheet_entries=timesheet_entries)


@bp.route('/api/list', methods=['GET'])
@login_required
def api_list():
    """API endpoint to get a list of clients (for AJAX calls)"""
    clients = Client.query.filter_by(user_id=current_user.id).order_by(Client.name).all()
    return jsonify({
        'clients': [{'id': c.id, 'name': c.name} for c in clients]
    })


@bp.route('/api/create', methods=['POST'])
@login_required
def api_create():
    """API endpoint to create a new client (for AJAX calls)"""
    try:
        data = request.json
        name = data.get('name', '').strip()
        
        if not name:
            return jsonify({'success': False, 'message': 'Client name is required'}), 400
            
        # Check if client already exists
        existing_client = Client.query.filter_by(name=name, user_id=current_user.id).first()
        if existing_client:
            return jsonify({
                'success': False, 
                'message': f'A client with the name "{name}" already exists',
                'client': {'id': existing_client.id, 'name': existing_client.name}
            }), 409
        
        # Create new client
        client = Client(
            name=name,
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            contact_person=data.get('contact_person', ''),
            user_id=current_user.id
        )
        
        db.session.add(client)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Client created successfully',
            'client': {'id': client.id, 'name': client.name}
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500