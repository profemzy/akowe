"""Akowe application factory module."""

from flask import Flask, redirect, url_for, request, jsonify, session, render_template
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from decimal import Decimal

# Initialize Flask extensions
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"
csrf = CSRFProtect()


def create_app(test_config=None):
    """Create and configure a Flask app."""
    # Load environment variables
    load_dotenv()

    # Create the Flask app with default configuration
    app = Flask(__name__, instance_relative_config=True)

    # Override template folder if explicitly specified in tests
    if test_config and "TEMPLATE_FOLDER" in test_config:
        app.template_folder = test_config["TEMPLATE_FOLDER"]

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///akowe.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,

        # Security settings
        SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") != "development",  # Secure in non-dev environments
        SESSION_COOKIE_HTTPONLY=True,  # Prevent JavaScript access to session cookie
        SESSION_COOKIE_SAMESITE="Lax",  # CSRF protection
        PERMANENT_SESSION_LIFETIME=timedelta(hours=6),  # Session expires after 6 hours
        WTF_CSRF_ENABLED=True,  # Explicitly enable CSRF protection
        SESSION_ACTIVITY_TIMEOUT=1800,  # 30 minutes of inactivity causes session timeout
        REMEMBER_COOKIE_DURATION=timedelta(days=14),  # "Remember me" lasts for 14 days
        REMEMBER_COOKIE_SECURE=os.environ.get("FLASK_ENV") != "development",
        REMEMBER_COOKIE_HTTPONLY=True,
    )
    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions
    from akowe.models import db
    db.init_app(app)
    migrate.init_app(app, db, directory=os.path.join(os.path.dirname(app.root_path), "migrations"))
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register user loader for Flask-Login
    from akowe.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Global CSRF error handler
    from flask_wtf.csrf import CSRFError

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        """Handle CSRF errors gracefully and inform the user."""
        return render_template('layouts/error.html', 
                              error="CSRF Validation Failed", 
                              message="Your form submission could not be processed. Please try again.",
                              status_code=400), 400

    @app.route("/ping")
    @csrf.exempt
    def ping():
        return {"status": "ok", "message": "Akowe is running"}

    # Session activity timeout check
    @app.before_request
    def check_session_activity():
        if current_user.is_authenticated:
            # Skip for static files and certain routes
            if request.path.startswith('/static/') or request.path == '/ping':
                return

            # Get last activity time from session
            last_activity = session.get('last_activity')
            now = datetime.utcnow()

            # Set current time as last activity
            session['last_activity'] = now.timestamp()

            # If no previous activity or it's been too long, require re-login
            if not last_activity or now.timestamp() - last_activity > app.config.get('SESSION_ACTIVITY_TIMEOUT', 3600):
                # Check for remember cookie
                has_remember_cookie = False
                remember_cookie_name = app.config.get('REMEMBER_COOKIE_NAME', 'remember_token')
                if remember_cookie_name in request.cookies:
                    has_remember_cookie = True

                # Only enforce for non-remembered sessions
                if not has_remember_cookie and session.get('_remember') != 'set':
                    from flask_login import logout_user
                    logout_user()
                    from flask import flash
                    flash("Your session has expired due to inactivity. Please log in again.", "warning")
                    return redirect(url_for('auth.login'))

    # Register authentication blueprint
    from akowe import auth
    app.register_blueprint(auth.bp)

    # Register admin blueprint
    from akowe import admin
    app.register_blueprint(admin.bp)

    # Register main blueprints
    from akowe.app.income import bp as income_bp
    from akowe.app.expense import bp as expense_bp
    from akowe.app.dashboard import bp as dashboard_bp
    from akowe.app.export import bp as export_bp
    from akowe.app.import_ import bp as import_bp
    app.register_blueprint(income_bp)
    app.register_blueprint(expense_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(import_bp)

    # Register tax dashboard blueprint
    from akowe.app.tax_dashboard import bp as tax_dashboard_bp
    from akowe.app.home_office import bp as home_office_bp
    app.register_blueprint(tax_dashboard_bp)
    app.register_blueprint(home_office_bp)

    # Register timesheet, invoice, client, and project blueprints
    from akowe.app.timesheet import bp as timesheet_bp
    from akowe.app.invoice import bp as invoice_bp
    from akowe.app.client import bp as client_bp
    from akowe.app.project import bp as project_bp
    app.register_blueprint(timesheet_bp)
    app.register_blueprint(invoice_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(project_bp)

    # Register mobile API blueprints
    from akowe.api.mobile_api import bp as mobile_api_bp
    from akowe.api.mobile_timesheet_api import bp as mobile_timesheet_bp
    from akowe.api.mobile_client_api import bp as mobile_client_bp
    from akowe.api.mobile_project_api import bp as mobile_project_bp
    from akowe.api.mobile_invoice_api import bp as mobile_invoice_bp
    from akowe.api.mobile_tax_api import bp as mobile_tax_bp
    from akowe.test_api import bp as test_api_bp

    app.register_blueprint(mobile_api_bp)
    app.register_blueprint(mobile_timesheet_bp)
    app.register_blueprint(mobile_client_bp)
    app.register_blueprint(mobile_project_bp)
    app.register_blueprint(mobile_invoice_bp)
    app.register_blueprint(mobile_tax_bp)
    app.register_blueprint(test_api_bp)

    # Exempt mobile API endpoints from CSRF protection
    csrf.exempt(mobile_api_bp)
    csrf.exempt(mobile_timesheet_bp)
    csrf.exempt(mobile_client_bp)
    csrf.exempt(mobile_project_bp)
    csrf.exempt(mobile_invoice_bp)
    csrf.exempt(mobile_tax_bp)
    csrf.exempt(test_api_bp)

    # Initialize timezone settings
    from akowe.utils.timezone_initializer import init_timezone
    init_timezone(app)

    # Add custom template filters
    from akowe.utils.timezone import to_local_time, format_datetime, format_date

    @app.template_filter("to_decimal")
    def to_decimal(value):
        """Convert a float value to Decimal for safe arithmetic operations."""
        if value is None:
            return Decimal("0")
        return Decimal(str(value))

    # Add global functions to template context
    @app.context_processor
    def utility_processor():
        """Add utility functions to template context."""
        return {
            'hasattr': hasattr,  # Add Python's built-in hasattr function
            'datetime': datetime  # Add datetime module for templates
        }

    @app.template_filter("local_datetime")
    def local_datetime_filter(dt):
        """Convert a UTC datetime to local timezone."""
        return to_local_time(dt)

    @app.template_filter("format_datetime")
    def format_datetime_filter(dt, format_str="%Y-%m-%d %H:%M:%S"):
        """Format a datetime in the local timezone."""
        return format_datetime(dt, format_str)

    @app.template_filter("format_date")
    def format_date_filter(dt, format_str="%Y-%m-%d"):
        """Format a date in the local timezone."""
        return format_date(dt, format_str)

    # Protect all routes
    @app.before_request
    def check_authentication():
        # Define public endpoints that don't require authentication
        public_endpoints = ["auth.login", "auth.logout", "static", "ping", "api.login", "api.test_endpoint", "test_api.hello"]
        
        # Skip authentication check for mobile API endpoints that use token_required decorator
        mobile_api_prefixes = [
            "api.", "mobile_timesheet.", "mobile_client.", "mobile_project.", "mobile_invoice.", "mobile_tax."
        ]
        
        if not request.endpoint:
            return None
            
        app.logger.info(f"Request endpoint: {request.endpoint} (type: {type(request.endpoint)})")
        app.logger.info(f"Request headers: {request.headers}")
            
        # Check if the endpoint is public
        is_public = False
        for ep in public_endpoints:
            if request.endpoint == ep or (
                isinstance(request.endpoint, str) and request.endpoint.startswith(ep + ".")
            ):
                is_public = True
                app.logger.info(f"Endpoint {request.endpoint} is public")
                break
                
        # Check if the endpoint is a mobile API endpoint with its own token authentication
        is_mobile_api = False
        for prefix in mobile_api_prefixes:
            if isinstance(request.endpoint, str) and request.endpoint.startswith(prefix):
                is_mobile_api = True
                app.logger.info(f"Endpoint {request.endpoint} is a mobile API endpoint")
                break
                
        # If it's a public endpoint or mobile API endpoint, no need to check authentication
        if is_public or is_mobile_api:
            app.logger.info(f"Skipping authentication check for {request.endpoint}")
            return None
            
        # Check if this is an API request
        is_api_request = (
            request.endpoint
            and isinstance(request.endpoint, str)
            and request.endpoint.startswith("api.")
        )
        
        # Handle authentication for non-public endpoints
        if not current_user.is_authenticated:
            app.logger.warning(f"User not authenticated for {request.endpoint}")
            if is_api_request:
                # Return JSON response for API endpoints
                return jsonify({"message": "Authentication required"}), 401
            else:
                return redirect(url_for("auth.login"))

    return app
