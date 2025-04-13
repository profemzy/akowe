import os
from flask import Flask
from flask_migrate import Migrate
from dotenv import load_dotenv

from akowe.models import db

migrate = Migrate()

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
    
    # Initialize database
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register models
    from akowe.models import income, expense
    
    # Register blueprints
    from akowe.api import income_bp, expense_bp, dashboard_bp
    app.register_blueprint(income_bp)
    app.register_blueprint(expense_bp)
    app.register_blueprint(dashboard_bp)
    
    @app.route('/ping')
    def ping():
        return {'status': 'ok', 'message': 'Akowe is running'}
    
    return app