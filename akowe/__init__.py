import os
from flask import Flask, redirect, url_for, request, jsonify
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from dotenv import load_dotenv

from akowe.models import db

migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

def create_app(test_config=None):
    # Load environment variables
    load_dotenv()
    
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///akowe.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    
    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Register user loader for Flask-Login
    from akowe.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register models
    from akowe.models import income, expense
    
    # Add a health check endpoint that doesn't require authentication
    @app.route('/ping')
    def ping():
        return {'status': 'ok', 'message': 'Akowe is running'}
    
    # Register authentication blueprint
    from akowe import auth
    app.register_blueprint(auth.bp)
    
    # Register admin blueprint
    from akowe import admin
    app.register_blueprint(admin.bp)
    
    # Register main blueprints
    from akowe.api import income_bp, expense_bp, dashboard_bp, export_bp
    app.register_blueprint(income_bp)
    app.register_blueprint(expense_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(export_bp)
    
    # Register mobile API blueprint
    from akowe.api.mobile_api import bp as mobile_api_bp
    app.register_blueprint(mobile_api_bp)
    
    # Protect all routes
    @app.before_request
    def check_authentication():
        # Define public endpoints that don't require authentication
        public_endpoints = ['auth.login', 'auth.logout', 'static', 'ping', 'api.login']
        
        # Skip authentication check for None endpoints or public endpoints
        if not request.endpoint:
            return None
            
        # Check if the endpoint is public
        is_public = False
        for ep in public_endpoints:
            if request.endpoint == ep or (
                isinstance(request.endpoint, str) and 
                request.endpoint.startswith(ep + '.')
            ):
                is_public = True
                break
        
        # If it's a public endpoint, no need to check authentication
        if is_public:
            return None
            
        # Check if this is an API request
        is_api_request = request.endpoint and isinstance(request.endpoint, str) and request.endpoint.startswith('api.')
        
        # Handle authentication for non-public endpoints
        if not current_user.is_authenticated:
            if is_api_request:
                # Return JSON response for API endpoints
                return jsonify({'message': 'Authentication required'}), 401
            else:
                # Redirect to login for web endpoints
                return redirect(url_for('auth.login'))
    
    return app