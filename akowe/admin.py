import os
from datetime import datetime, timedelta
from decimal import Decimal

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import func, extract

from akowe.decorators import admin_required
from akowe.forms import RegistrationForm, UserEditForm
from akowe.models import db
from akowe.models.client import Client
from akowe.models.expense import Expense
from akowe.models.income import Income
from akowe.models.invoice import Invoice
from akowe.models.project import Project
from akowe.models.timesheet import Timesheet
from akowe.models.user import User

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
@login_required
@admin_required
def index():
    """Admin dashboard with system statistics and summaries."""
    # Import datetime at the beginning of the function
    from datetime import datetime
    
    # Get user statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    inactive_users = total_users - active_users
    admins = User.query.filter_by(is_admin=True).count()
    
    # Get system statistics
    total_clients = Client.query.count()
    total_projects = Project.query.count()
    
    # Get transaction statistics
    
    # Recent activity
    recent_registrations = User.query.order_by(User.created_at.desc()).limit(5).all()
    # Check if a User model has the last_login attribute
    recent_logins = []
    if hasattr(User, 'last_login'):
        recent_logins = User.query.filter(User.last_login.isnot(None)).order_by(User.last_login.desc()).limit(5).all()
    
    # Transaction counts
    income_count = Income.query.count()
    expense_count = Expense.query.count()
    invoice_count = Invoice.query.count()
    timesheet_count = Timesheet.query.count()
    
    # Calculate financial summaries
    total_income = db.session.query(func.sum(Income.amount)).scalar() or Decimal('0.00')
    total_expenses = db.session.query(func.sum(Expense.amount)).scalar() or Decimal('0.00')
    total_invoiced = db.session.query(func.sum(Invoice.total)).scalar() or Decimal('0.00')
    
    # Recent transactions
    recent_invoices = Invoice.query.order_by(Invoice.created_at.desc()).limit(5).all()
    recent_income = Income.query.order_by(Income.date.desc()).limit(5).all()
    recent_expenses = Expense.query.order_by(Expense.date.desc()).limit(5).all()
    
    # Monthly financial data
    current_year = datetime.utcnow().year
    monthly_registrations = db.session.query(
        extract('month', User.created_at).label('month'),
        func.count(User.id).label('count')
    ).filter(
        extract('year', User.created_at) == current_year
    ).group_by('month').all()
    
    monthly_income = db.session.query(
        extract('month', Income.date).label('month'),
        func.sum(Income.amount).label('amount')
    ).filter(
        extract('year', Income.date) == current_year
    ).group_by('month').all()
    
    monthly_expenses = db.session.query(
        extract('month', Expense.date).label('month'),
        func.sum(Expense.amount).label('amount')
    ).filter(
        extract('year', Expense.date) == current_year
    ).group_by('month').all()
    
    # Format for charts
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    registration_data = [0] * 12
    income_data = [0] * 12
    expense_data = [0] * 12
    
    for item in monthly_registrations:
        registration_data[int(item.month) - 1] = item.count
    
    for item in monthly_income:
        income_data[int(item.month) - 1] = float(item.amount or 0)
    
    for item in monthly_expenses:
        expense_data[int(item.month) - 1] = float(item.amount or 0)
    
    # System information
    import platform
    
    # Default system info
    system_info = {
        'os': platform.system(),
        'python_version': platform.python_version(),
        'platform': platform.platform(),
        'cpu_percent': 0,
        'memory_percent': 0,
        'disk_percent': 0,
        'uptime': 'Unknown'
    }
    
    # Try to get detailed system info if psutil is available
    try:
        import psutil
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        uptime_hours = uptime.total_seconds() // 3600
        uptime_str = f"{int(uptime_hours // 24)} days, {int(uptime_hours % 24)} hours"
        
        system_info.update({
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'uptime': uptime_str
        })
    except ImportError:
        # If psutil is not available, we'll use default values
        import logging
        logging.warning("psutil module not found. System monitoring metrics will not be available.")
        pass
    
    # Add active users in last 24 hours
    active_today = 0
    if hasattr(User, 'last_login'):
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        active_today = User.query.filter(
            User.last_login >= one_day_ago
        ).count()
    
    return render_template(
        "admin/index.html", 
        title="Admin Dashboard",
        total_users=total_users,
        active_users=active_users,
        inactive_users=inactive_users,
        admins=admins,
        total_clients=total_clients,
        total_projects=total_projects,
        income_count=income_count,
        expense_count=expense_count,
        invoice_count=invoice_count,
        timesheet_count=timesheet_count,
        total_income=total_income,
        total_expenses=total_expenses,
        total_invoiced=total_invoiced,
        active_today=active_today,
        recent_registrations=recent_registrations,
        recent_logins=recent_logins,
        recent_invoices=recent_invoices,
        recent_income=recent_income,
        recent_expenses=recent_expenses,
        months=months,
        registration_data=registration_data,
        income_data=income_data,
        expense_data=expense_data,
        system_info=system_info
    )


@bp.route("/users")
@login_required
@admin_required
def users():
    """User management dashboard."""
    # Add filtering options
    filter_status = request.args.get('status', 'all')
    filter_role = request.args.get('role', 'all')
    search_query = request.args.get('q', '')
    
    users_query = User.query
    
    if filter_status == 'active':
        users_query = users_query.filter_by(is_active=True)
    elif filter_status == 'inactive':
        users_query = users_query.filter_by(is_active=False)
    
    if filter_role == 'admin':
        users_query = users_query.filter_by(is_admin=True)
    elif filter_role == 'user':
        users_query = users_query.filter_by(is_admin=False)
    
    if search_query:
        users_query = users_query.filter(
            (User.username.ilike(f'%{search_query}%') 
             | User.email.ilike(f'%{search_query}%') 
             | User.first_name.ilike(f'%{search_query}%') 
             | User.last_name.ilike(f'%{search_query}%'))
        )
    
    users = users_query.order_by(User.username).all()
    
    # Get statistics for the sidebar
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    admin_users = User.query.filter_by(is_admin=True).count()
    
    return render_template(
        "admin/users.html", 
        users=users, 
        title="User Management",
        filter_status=filter_status,
        filter_role=filter_role,
        search_query=search_query,
        total_users=total_users,
        active_users=active_users,
        admin_users=admin_users
    )


@bp.route("/users/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_user():
    """Create a new user."""
    form = RegistrationForm()

    if form.validate_on_submit():
        # Handle the is_admin boolean explicitly from form data
        is_admin_value = request.form.get('is_admin', '') == 'y'
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            is_admin=is_admin_value,
            hourly_rate=form.hourly_rate.data if hasattr(form, 'hourly_rate') else Decimal('0.00')
        )
        user.password = form.password.data

        db.session.add(user)
        db.session.commit()

        flash(f"User {user.username} has been created.", "success")
        return redirect(url_for("admin.users"))

    return render_template("admin/new_user.html", form=form, title="Create User")


@bp.route("/users/<int:id>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(id):
    """Edit an existing user."""
    user = User.query.get_or_404(id)

    # Don't allow editing the initial admin user
    if user.id == 1 and current_user.id != 1:
        flash("You cannot edit the primary admin user.", "danger")
        return redirect(url_for("admin.users"))

    form = UserEditForm(user=user)

    if request.method == "GET":
        form.email.data = user.email
        form.first_name.data = user.first_name
        form.last_name.data = user.last_name
        form.is_admin.data = user.is_admin
        form.is_active.data = user.is_active
        if hasattr(form, 'hourly_rate') and hasattr(user, 'hourly_rate'):
            form.hourly_rate.data = user.hourly_rate

    if form.validate_on_submit():
        # Handle boolean values explicitly
        is_admin_value = request.form.get('is_admin', '') == 'y'
        is_active_value = request.form.get('is_active', '') == 'y'
        
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.is_admin = is_admin_value
        user.is_active = is_active_value
        
        if hasattr(form, 'hourly_rate') and hasattr(user, 'hourly_rate'):
            user.hourly_rate = form.hourly_rate.data

        db.session.commit()

        flash(f"User {user.username} has been updated.", "success")
        return redirect(url_for("admin.users"))

    # Get user activity data
    user_activity = {}
    
    # Check if models have a user_id field before filtering
    if hasattr(Invoice, 'user_id'):
        user_activity['invoices'] = Invoice.query.filter_by(user_id=user.id).count()
    else:
        user_activity['invoices'] = 0
        
    if hasattr(Timesheet, 'user_id'):
        user_activity['timesheets'] = Timesheet.query.filter_by(user_id=user.id).count()
    else:
        user_activity['timesheets'] = 0
        
    if hasattr(Income, 'user_id'):
        user_activity['incomes'] = Income.query.filter_by(user_id=user.id).count()
    else:
        user_activity['incomes'] = 0
        
    # Expense might be company-wide rather than user-specific
    if hasattr(Expense, 'user_id'):
        user_activity['expenses'] = Expense.query.filter_by(user_id=user.id).count()
    else:
        user_activity['expenses'] = 0  # No user-specific expenses

    return render_template(
        "admin/edit_user.html", 
        form=form, 
        user=user, 
        user_activity=user_activity,
        title="Edit User"
    )


@bp.route("/users/<int:id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(id):
    """Delete a user."""
    user = User.query.get_or_404(id)

    # Don't allow deleting the initial admin user
    if user.id == 1:
        flash("You cannot delete the primary admin user.", "danger")
        return redirect(url_for("admin.users"))

    # Don't allow users to delete themselves
    if user.id == current_user.id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("admin.users"))

    username = user.username
    db.session.delete(user)
    db.session.commit()

    flash(f"User {username} has been deleted.", "success")
    return redirect(url_for("admin.users"))


@bp.route("/users/<int:id>/reset-password", methods=["POST"])
@login_required
@admin_required
def reset_password(id):
    """Reset a user's password."""
    user = User.query.get_or_404(id)

    # Generate a temporary password
    import random
    import string
    
    temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    user.password = temp_password
    db.session.commit()

    flash(f"Password for {user.username} has been reset to: {temp_password}", "success")
    return redirect(url_for("admin.edit_user", id=user.id))


@bp.route("/settings", methods=["GET", "POST"])
@login_required
@admin_required
def settings():
    """Application settings management."""
    # Get environment variables that can be modified
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    env_vars = {}
    
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"\'')
    
    # Handle form submission
    if request.method == "POST":
        # This is just a placeholder - actual implementation would update .env file
        # or a settings table in the database
        flash("Settings have been updated.", "success")
        return redirect(url_for("admin.settings"))
    
    return render_template(
        "admin/settings.html", 
        title="System Settings",
        env_vars=env_vars
    )


@bp.route("/data", methods=["GET"])
@login_required
@admin_required
def data_management():
    """Data management dashboard."""
    # Get database statistics
    income_count = Income.query.count()
    expense_count = Expense.query.count()
    invoice_count = Invoice.query.count()
    timesheet_count = Timesheet.query.count()
    client_count = Client.query.count()
    project_count = Project.query.count()
    
    # Get database size - placeholder, would need a DB-specific approach
    db_size = "Unknown"  # Would need database-specific implementation
    
    # Recent database entries
    recent_entries = {
        'incomes': Income.query.order_by(Income.created_at.desc()).limit(5).all(),
        'expenses': Expense.query.order_by(Expense.created_at.desc()).limit(5).all(),
        'invoices': Invoice.query.order_by(Invoice.created_at.desc()).limit(5).all(),
        'timesheets': Timesheet.query.order_by(Timesheet.created_at.desc()).limit(5).all()
    }
    
    return render_template(
        "admin/data.html", 
        title="Data Management",
        income_count=income_count,
        expense_count=expense_count,
        invoice_count=invoice_count,
        timesheet_count=timesheet_count,
        client_count=client_count,
        project_count=project_count,
        db_size=db_size,
        recent_entries=recent_entries
    )


@bp.route("/logs", methods=["GET"])
@login_required
@admin_required
def logs():
    """View application logs."""
    # This is a placeholder - actual implementation would access log files
    log_entries = []
    
    # In a real implementation, would read from log files
    try:
        log_file = 'application.log'  # Update with actual log file path
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_entries = f.readlines()[-100:]  # Last 100 lines
    except Exception as e:
        flash(f"Error reading log file: {str(e)}", "error")
    
    return render_template(
        "admin/logs.html", 
        title="Application Logs",
        log_entries=log_entries
    )


@bp.route("/stats", methods=["GET"])
@login_required
@admin_required
def stats():
    """System statistics and analytics."""
    # Time period selection
    period = request.args.get('period', 'month')
    
    if period == 'week':
        start_date = datetime.utcnow().date() - timedelta(days=7)
    elif period == 'month':
        start_date = datetime.utcnow().date() - timedelta(days=30)
    elif period == 'year':
        start_date = datetime.utcnow().date() - timedelta(days=365)
    else:
        start_date = datetime.utcnow().date() - timedelta(days=30)  # Default to month
    
    # Get activity counts by date
    income_by_date = db.session.query(
        Income.date, 
        func.count(Income.id).label('count'),
        func.sum(Income.amount).label('amount')
    ).filter(Income.date >= start_date).group_by(Income.date).all()
    
    expense_by_date = db.session.query(
        Expense.date, 
        func.count(Expense.id).label('count'),
        func.sum(Expense.amount).label('amount')
    ).filter(Expense.date >= start_date).group_by(Expense.date).all()
    
    invoice_by_date = db.session.query(
        Invoice.issue_date, 
        func.count(Invoice.id).label('count')
    ).filter(Invoice.issue_date >= start_date).group_by(Invoice.issue_date).all()
    
    # User registration over time
    registrations_by_date = db.session.query(
        func.date(User.created_at).label('date'), 
        func.count(User.id).label('count')
    ).filter(func.date(User.created_at) >= start_date).group_by('date').all()
    
    # Format the data for charts
    date_range = [(start_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range((datetime.utcnow().date() - start_date).days + 1)]
    
    income_data = [0] * len(date_range)
    expense_data = [0] * len(date_range)
    invoice_data = [0] * len(date_range)
    registration_data = [0] * len(date_range)
    
    for i, date_str in enumerate(date_range):
        for entry in income_by_date:
            if entry.date.strftime('%Y-%m-%d') == date_str:
                income_data[i] = float(entry.amount or 0)
                break
                
        for entry in expense_by_date:
            if entry.date.strftime('%Y-%m-%d') == date_str:
                expense_data[i] = float(entry.amount or 0)
                break
                
        for entry in invoice_by_date:
            if entry.issue_date.strftime('%Y-%m-%d') == date_str:
                invoice_data[i] = entry.count
                break
                
        for entry in registrations_by_date:
            if entry.date.strftime('%Y-%m-%d') == date_str:
                registration_data[i] = entry.count
                break
    
    return render_template(
        "admin/stats.html", 
        title="System Statistics",
        period=period,
        date_range=date_range,
        income_data=income_data,
        expense_data=expense_data,
        invoice_data=invoice_data,
        registration_data=registration_data
    )