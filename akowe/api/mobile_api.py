import os
from datetime import datetime
from decimal import Decimal
from functools import wraps
import jwt
from flask import Blueprint, request, jsonify, current_app, g
from werkzeug.security import check_password_hash

from akowe.models import db
from akowe.models.user import User
from akowe.models.expense import Expense
from akowe.models.income import Income
from akowe.services.storage_service import StorageService

bp = Blueprint('api', __name__, url_prefix='/api')

# Constants
RECEIPT_CONTAINER = 'receipts'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Authentication token is missing'}), 401
        
        try:
            # Decode token
            secret_key = current_app.config.get('SECRET_KEY', 'dev')
            data = jwt.decode(token, secret_key, algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
            
            # Store user in g object for use in route functions
            g.current_user = current_user
            
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    
    return decorated

# Authentication endpoints
@bp.route('/login', methods=['POST'])
def login():
    auth = request.json
    
    if not auth or not auth.get('username') or not auth.get('password'):
        return jsonify({'message': 'Missing username or password'}), 400
    
    user = User.query.filter_by(username=auth.get('username')).first()
    
    if not user:
        return jsonify({'message': 'Invalid credentials'}), 401
    
    if check_password_hash(user.password_hash, auth.get('password')):
        # Generate token
        secret_key = current_app.config.get('SECRET_KEY', 'dev')
        token = jwt.encode(
            {'user_id': user.id, 'exp': datetime.utcnow() + datetime.timedelta(hours=24)},
            secret_key,
            algorithm='HS256'
        )
        
        return jsonify({
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_admin': user.is_admin
            }
        })
    
    return jsonify({'message': 'Invalid credentials'}), 401

# User endpoints
@bp.route('/user', methods=['GET'])
@token_required
def get_user():
    return jsonify({
        'user': {
            'id': g.current_user.id,
            'username': g.current_user.username,
            'email': g.current_user.email,
            'first_name': g.current_user.first_name,
            'last_name': g.current_user.last_name,
            'is_admin': g.current_user.is_admin
        }
    })

@bp.route('/user/password', methods=['PUT'])
@token_required
def change_password():
    data = request.json
    
    if not data or not data.get('current_password') or not data.get('new_password'):
        return jsonify({'message': 'Missing current or new password'}), 400
    
    user = g.current_user
    
    if not check_password_hash(user.password_hash, data.get('current_password')):
        return jsonify({'message': 'Current password is incorrect'}), 401
    
    user.password = data.get('new_password')
    db.session.commit()
    
    return jsonify({'message': 'Password changed successfully'})

# Expense endpoints
@bp.route('/expenses', methods=['GET'])
@token_required
def get_expenses():
    # Get query parameters for filtering
    category = request.args.get('category')
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Start with base query
    query = Expense.query
    
    # Apply filters if provided
    if category:
        query = query.filter(Expense.category == category)
    if status:
        query = query.filter(Expense.status == status)
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Expense.date >= start)
        except ValueError:
            pass
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Expense.date <= end)
        except ValueError:
            pass
    
    # Execute query with ordering
    expenses = query.order_by(Expense.date.desc()).all()
    
    # Format results
    result = []
    for expense in expenses:
        result.append({
            'id': expense.id,
            'date': expense.date.isoformat(),
            'title': expense.title,
            'amount': str(expense.amount),
            'category': expense.category,
            'payment_method': expense.payment_method,
            'status': expense.status,
            'vendor': expense.vendor,
            'has_receipt': bool(expense.receipt_blob_name),
            'created_at': expense.created_at.isoformat() if expense.created_at else None,
            'updated_at': expense.updated_at.isoformat() if expense.updated_at else None
        })
    
    return jsonify({'expenses': result})

@bp.route('/expenses/<int:id>', methods=['GET'])
@token_required
def get_expense(id):
    expense = Expense.query.get_or_404(id)
    
    # If receipt exists, generate SAS URL
    receipt_url = None
    if expense.receipt_blob_name:
        try:
            receipt_url = StorageService.generate_sas_url(
                expense.receipt_blob_name, 
                RECEIPT_CONTAINER
            )
        except Exception as e:
            current_app.logger.error(f"Error generating receipt URL: {str(e)}")
    
    return jsonify({
        'id': expense.id,
        'date': expense.date.isoformat(),
        'title': expense.title,
        'amount': str(expense.amount),
        'category': expense.category,
        'payment_method': expense.payment_method,
        'status': expense.status,
        'vendor': expense.vendor,
        'has_receipt': bool(expense.receipt_blob_name),
        'receipt_url': receipt_url,
        'created_at': expense.created_at.isoformat() if expense.created_at else None,
        'updated_at': expense.updated_at.isoformat() if expense.updated_at else None
    })

@bp.route('/expenses', methods=['POST'])
@token_required
def create_expense():
    # Check if request is multipart (with file) or JSON
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        # Get form data
        data = request.form
        receipt_file = request.files.get('receipt')
    else:
        # Get JSON data
        data = request.json
        receipt_file = None
    
    try:
        # Validate required fields
        required_fields = ['date', 'title', 'amount', 'category', 'payment_method', 'status']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'Missing required field: {field}'}), 400
        
        # Parse date
        try:
            date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Create expense object
        expense = Expense(
            date=date,
            title=data['title'],
            amount=Decimal(data['amount']),
            category=data['category'],
            payment_method=data['payment_method'],
            status=data['status'],
            vendor=data.get('vendor')
        )
        
        # Handle receipt upload if present
        if receipt_file and receipt_file.filename and allowed_file(receipt_file.filename):
            # Check file size
            receipt_file.seek(0, os.SEEK_END)
            file_size = receipt_file.tell()
            receipt_file.seek(0)
            
            if file_size > MAX_CONTENT_LENGTH:
                return jsonify({'message': 'Receipt file is too large. Maximum size is 5MB.'}), 400
            
            try:
                # Upload file to Azure Blob Storage
                blob_name, blob_url = StorageService.upload_file(receipt_file, RECEIPT_CONTAINER)
                
                # Store blob info in the expense record
                expense.receipt_blob_name = blob_name
                expense.receipt_url = blob_url
                
            except Exception as e:
                return jsonify({'message': f'Error uploading receipt: {str(e)}'}), 500
        
        # Save expense to database
        db.session.add(expense)
        db.session.commit()
        
        return jsonify({
            'message': 'Expense created successfully',
            'expense': {
                'id': expense.id,
                'date': expense.date.isoformat(),
                'title': expense.title,
                'amount': str(expense.amount),
                'category': expense.category,
                'payment_method': expense.payment_method,
                'status': expense.status,
                'vendor': expense.vendor,
                'has_receipt': bool(expense.receipt_blob_name)
            }
        }), 201
        
    except ValueError as e:
        return jsonify({'message': f'Invalid data: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error creating expense: {str(e)}'}), 500

@bp.route('/expenses/<int:id>', methods=['PUT'])
@token_required
def update_expense(id):
    expense = Expense.query.get_or_404(id)
    
    # Check if request is multipart (with file) or JSON
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        # Get form data
        data = request.form
        receipt_file = request.files.get('receipt')
    else:
        # Get JSON data
        data = request.json
        receipt_file = None
    
    try:
        # Update fields if provided
        if 'date' in data:
            try:
                expense.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        if 'title' in data:
            expense.title = data['title']
        
        if 'amount' in data:
            expense.amount = Decimal(data['amount'])
        
        if 'category' in data:
            expense.category = data['category']
        
        if 'payment_method' in data:
            expense.payment_method = data['payment_method']
        
        if 'status' in data:
            expense.status = data['status']
        
        if 'vendor' in data:
            expense.vendor = data['vendor']
        
        # Handle receipt upload if present
        if receipt_file and receipt_file.filename and allowed_file(receipt_file.filename):
            # Check file size
            receipt_file.seek(0, os.SEEK_END)
            file_size = receipt_file.tell()
            receipt_file.seek(0)
            
            if file_size > MAX_CONTENT_LENGTH:
                return jsonify({'message': 'Receipt file is too large. Maximum size is 5MB.'}), 400
            
            try:
                # Delete old receipt if it exists
                if expense.receipt_blob_name:
                    StorageService.delete_file(expense.receipt_blob_name, RECEIPT_CONTAINER)
                
                # Upload new file to Azure Blob Storage
                blob_name, blob_url = StorageService.upload_file(receipt_file, RECEIPT_CONTAINER)
                
                # Store blob info in the expense record
                expense.receipt_blob_name = blob_name
                expense.receipt_url = blob_url
                
            except Exception as e:
                return jsonify({'message': f'Error uploading receipt: {str(e)}'}), 500
        
        # Handle receipt deletion if requested
        if data.get('delete_receipt') == 'true' and expense.receipt_blob_name:
            try:
                StorageService.delete_file(expense.receipt_blob_name, RECEIPT_CONTAINER)
                expense.receipt_blob_name = None
                expense.receipt_url = None
            except Exception as e:
                return jsonify({'message': f'Error deleting receipt: {str(e)}'}), 500
        
        # Save changes
        db.session.commit()
        
        return jsonify({
            'message': 'Expense updated successfully',
            'expense': {
                'id': expense.id,
                'date': expense.date.isoformat(),
                'title': expense.title,
                'amount': str(expense.amount),
                'category': expense.category,
                'payment_method': expense.payment_method,
                'status': expense.status,
                'vendor': expense.vendor,
                'has_receipt': bool(expense.receipt_blob_name)
            }
        })
        
    except ValueError as e:
        return jsonify({'message': f'Invalid data: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating expense: {str(e)}'}), 500

@bp.route('/expenses/<int:id>', methods=['DELETE'])
@token_required
def delete_expense(id):
    expense = Expense.query.get_or_404(id)
    
    try:
        # Delete receipt if it exists
        if expense.receipt_blob_name:
            try:
                StorageService.delete_file(expense.receipt_blob_name, RECEIPT_CONTAINER)
            except Exception as e:
                current_app.logger.error(f"Error deleting receipt: {str(e)}")
        
        # Delete expense
        db.session.delete(expense)
        db.session.commit()
        
        return jsonify({'message': 'Expense deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting expense: {str(e)}'}), 500

# Income endpoints
@bp.route('/incomes', methods=['GET'])
@token_required
def get_incomes():
    # Get query parameters for filtering
    client = request.args.get('client')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Start with base query
    query = Income.query
    
    # Apply filters if provided
    if client:
        query = query.filter(Income.client.ilike(f'%{client}%'))
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Income.date >= start)
        except ValueError:
            pass
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Income.date <= end)
        except ValueError:
            pass
    
    # Execute query with ordering
    incomes = query.order_by(Income.date.desc()).all()
    
    # Format results
    result = []
    for income in incomes:
        result.append({
            'id': income.id,
            'date': income.date.isoformat(),
            'amount': str(income.amount),
            'client': income.client,
            'project': income.project,
            'invoice': income.invoice,
            'created_at': income.created_at.isoformat() if income.created_at else None,
            'updated_at': income.updated_at.isoformat() if income.updated_at else None
        })
    
    return jsonify({'incomes': result})

@bp.route('/incomes/<int:id>', methods=['GET'])
@token_required
def get_income(id):
    income = Income.query.get_or_404(id)
    
    return jsonify({
        'id': income.id,
        'date': income.date.isoformat(),
        'amount': str(income.amount),
        'client': income.client,
        'project': income.project,
        'invoice': income.invoice,
        'created_at': income.created_at.isoformat() if income.created_at else None,
        'updated_at': income.updated_at.isoformat() if income.updated_at else None
    })

@bp.route('/incomes', methods=['POST'])
@token_required
def create_income():
    data = request.json
    
    try:
        # Validate required fields
        required_fields = ['date', 'amount', 'client']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'Missing required field: {field}'}), 400
        
        # Parse date
        try:
            date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Create income object
        income = Income(
            date=date,
            amount=Decimal(data['amount']),
            client=data['client'],
            project=data.get('project'),
            invoice=data.get('invoice')
        )
        
        # Save income to database
        db.session.add(income)
        db.session.commit()
        
        return jsonify({
            'message': 'Income created successfully',
            'income': {
                'id': income.id,
                'date': income.date.isoformat(),
                'amount': str(income.amount),
                'client': income.client,
                'project': income.project,
                'invoice': income.invoice
            }
        }), 201
        
    except ValueError as e:
        return jsonify({'message': f'Invalid data: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error creating income: {str(e)}'}), 500

@bp.route('/incomes/<int:id>', methods=['PUT'])
@token_required
def update_income(id):
    income = Income.query.get_or_404(id)
    data = request.json
    
    try:
        # Update fields if provided
        if 'date' in data:
            try:
                income.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        if 'amount' in data:
            income.amount = Decimal(data['amount'])
        
        if 'client' in data:
            income.client = data['client']
        
        if 'project' in data:
            income.project = data['project']
        
        if 'invoice' in data:
            income.invoice = data['invoice']
        
        # Save changes
        db.session.commit()
        
        return jsonify({
            'message': 'Income updated successfully',
            'income': {
                'id': income.id,
                'date': income.date.isoformat(),
                'amount': str(income.amount),
                'client': income.client,
                'project': income.project,
                'invoice': income.invoice
            }
        })
        
    except ValueError as e:
        return jsonify({'message': f'Invalid data: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating income: {str(e)}'}), 500

@bp.route('/incomes/<int:id>', methods=['DELETE'])
@token_required
def delete_income(id):
    income = Income.query.get_or_404(id)
    
    try:
        # Delete income
        db.session.delete(income)
        db.session.commit()
        
        return jsonify({'message': 'Income deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting income: {str(e)}'}), 500

# Dashboard endpoints
@bp.route('/dashboard', methods=['GET'])
@token_required
def get_dashboard():
    # Get time period from query parameters (default to current year)
    period = request.args.get('period', 'year')
    
    current_date = datetime.utcnow().date()
    
    if period == 'month':
        # Current month data
        start_date = datetime(current_date.year, current_date.month, 1).date()
        
        # For month, we need a different calculation for end date
        if current_date.month == 12:
            end_date = datetime(current_date.year + 1, 1, 1).date()
        else:
            end_date = datetime(current_date.year, current_date.month + 1, 1).date()
    elif period == 'quarter':
        # Current quarter data
        current_quarter = (current_date.month - 1) // 3 + 1
        start_date = datetime(current_date.year, 3 * current_quarter - 2, 1).date()
        
        if current_quarter == 4:
            end_date = datetime(current_date.year + 1, 1, 1).date()
        else:
            end_date = datetime(current_date.year, 3 * current_quarter + 1, 1).date()
    else:
        # Default to yearly data
        start_date = datetime(current_date.year, 1, 1).date()
        end_date = datetime(current_date.year + 1, 1, 1).date()
    
    # Get expenses for the period
    expenses = Expense.query.filter(
        Expense.date >= start_date,
        Expense.date < end_date
    ).all()
    
    # Get incomes for the period
    incomes = Income.query.filter(
        Income.date >= start_date,
        Income.date < end_date
    ).all()
    
    # Calculate totals
    total_expense = sum(expense.amount for expense in expenses)
    total_income = sum(income.amount for income in incomes)
    net_income = total_income - total_expense
    
    # Calculate expense breakdown by category
    expense_by_category = {}
    for expense in expenses:
        if expense.category in expense_by_category:
            expense_by_category[expense.category] += expense.amount
        else:
            expense_by_category[expense.category] = expense.amount
    
    # Format the expense categories for output
    category_breakdown = []
    for category, amount in expense_by_category.items():
        category_breakdown.append({
            'category': category,
            'amount': str(amount),
            'percentage': str(amount / total_expense * 100) if total_expense else '0'
        })
    
    # Calculate income breakdown by client
    income_by_client = {}
    for income in incomes:
        if income.client in income_by_client:
            income_by_client[income.client] += income.amount
        else:
            income_by_client[income.client] = income.amount
    
    # Format the income by client for output
    client_breakdown = []
    for client, amount in income_by_client.items():
        client_breakdown.append({
            'client': client,
            'amount': str(amount),
            'percentage': str(amount / total_income * 100) if total_income else '0'
        })
    
    # Get recent expenses and incomes for the dashboard
    recent_expenses = Expense.query.order_by(Expense.date.desc()).limit(5).all()
    recent_incomes = Income.query.order_by(Income.date.desc()).limit(5).all()
    
    # Format recent expenses
    recent_expense_list = []
    for expense in recent_expenses:
        recent_expense_list.append({
            'id': expense.id,
            'date': expense.date.isoformat(),
            'title': expense.title,
            'amount': str(expense.amount),
            'category': expense.category
        })
    
    # Format recent incomes
    recent_income_list = []
    for income in recent_incomes:
        recent_income_list.append({
            'id': income.id,
            'date': income.date.isoformat(),
            'amount': str(income.amount),
            'client': income.client
        })
    
    # Return dashboard data
    return jsonify({
        'period': period,
        'start_date': start_date.isoformat(),
        'end_date': (end_date - datetime.timedelta(days=1)).isoformat(),
        'summary': {
            'total_income': str(total_income),
            'total_expense': str(total_expense),
            'net_income': str(net_income)
        },
        'expense_breakdown': category_breakdown,
        'income_breakdown': client_breakdown,
        'recent_expenses': recent_expense_list,
        'recent_incomes': recent_income_list
    })

# Export endpoints
@bp.route('/export/expenses', methods=['GET'])
@token_required
def export_expenses():
    # Get query parameters for filtering
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Start with base query
    query = Expense.query
    
    # Apply filters if provided
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Expense.date >= start)
        except ValueError:
            pass
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Expense.date <= end)
        except ValueError:
            pass
    
    # Execute query with ordering
    expenses = query.order_by(Expense.date).all()
    
    # Format CSV data
    csv_data = "date,title,amount,category,payment_method,status,vendor\n"
    for expense in expenses:
        vendor = expense.vendor or ""
        csv_data += f"{expense.date.isoformat()},{expense.title},{expense.amount},{expense.category},{expense.payment_method},{expense.status},{vendor}\n"
    
    return jsonify({'csv_data': csv_data})

@bp.route('/export/incomes', methods=['GET'])
@token_required
def export_incomes():
    # Get query parameters for filtering
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Start with base query
    query = Income.query
    
    # Apply filters if provided
    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Income.date >= start)
        except ValueError:
            pass
    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Income.date <= end)
        except ValueError:
            pass
    
    # Execute query with ordering
    incomes = query.order_by(Income.date).all()
    
    # Format CSV data
    csv_data = "date,amount,client,project,invoice\n"
    for income in incomes:
        project = income.project or ""
        invoice = income.invoice or ""
        csv_data += f"{income.date.isoformat()},{income.amount},{income.client},{project},{invoice}\n"
    
    return jsonify({'csv_data': csv_data})

# Reference data endpoints
@bp.route('/references/categories', methods=['GET'])
@token_required
def get_categories():
    from akowe.api.expense import CATEGORIES
    return jsonify({'categories': CATEGORIES})

@bp.route('/references/payment-methods', methods=['GET'])
@token_required
def get_payment_methods():
    from akowe.api.expense import PAYMENT_METHODS
    return jsonify({'payment_methods': PAYMENT_METHODS})

@bp.route('/references/statuses', methods=['GET'])
@token_required
def get_statuses():
    from akowe.api.expense import STATUSES
    return jsonify({'statuses': STATUSES})