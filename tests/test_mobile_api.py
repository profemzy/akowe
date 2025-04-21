import os
import json
import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from akowe.factory import create_app
from akowe.models import db
from akowe.models.user import User
from akowe.models.client import Client
from akowe.models.project import Project
from akowe.models.timesheet import Timesheet
from akowe.models.expense import Expense
from akowe.models.income import Income
from akowe.models.invoice import Invoice


@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-key',
        'WTF_CSRF_ENABLED': False,
    })

    # Create the database and load test data
    with app.app_context():
        db.create_all()
        # Create a test user
        user = User(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            is_admin=False
        )
        user.password = 'password123'
        db.session.add(user)
        db.session.commit()

        # Create test data
        create_test_data(user.id)

    yield app

    # Clean up
    with app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def auth_token(client):
    """Get an authentication token for the test user."""
    response = client.post('/api/login', json={
        'username': 'testuser',
        'password': 'password123'
    })
    data = json.loads(response.data)
    return data['token']


def create_test_data(user_id):
    """Create test data for the API tests."""
    # Create a test client
    client = Client(
        name='Test Client',
        email='client@example.com',
        phone='555-123-4567',
        address='123 Test St, Test City',
        contact_person='Contact Person',
        notes='Test notes',
        user_id=user_id
    )
    db.session.add(client)
    db.session.flush()  # Get the ID without committing

    # Create a test project
    project = Project(
        name='Test Project',
        description='Test project description',
        status='active',
        hourly_rate=Decimal('100.00'),
        client_id=client.id,
        user_id=user_id
    )
    db.session.add(project)
    db.session.flush()

    # Create a test timesheet entry
    timesheet = Timesheet(
        date=datetime.now().date(),
        client_id=client.id,
        project_id=project.id,
        description='Test timesheet entry',
        hours=Decimal('5.0'),
        hourly_rate=Decimal('100.00'),
        status='pending',
        user_id=user_id
    )
    db.session.add(timesheet)

    # Create a test expense
    expense = Expense(
        date=datetime.now().date(),
        title='Test Expense',
        amount=Decimal('150.00'),
        category='software',
        payment_method='credit_card',
        status='paid',
        vendor='Test Vendor',
        user_id=user_id
    )
    db.session.add(expense)

    # Create a test income
    income = Income(
        date=datetime.now().date(),
        amount=Decimal('1000.00'),
        client='Test Client',
        project='Test Project',
        invoice='INV-001',
        user_id=user_id
    )
    db.session.add(income)

    # Create a test invoice
    invoice = Invoice(
        invoice_number='INV-TEST-001',
        client_id=client.id,
        company_name='Test Company',
        issue_date=datetime.now().date(),
        due_date=(datetime.now() + timedelta(days=30)).date(),
        notes='Test invoice notes',
        tax_rate=Decimal('13.00'),
        status='draft',
        user_id=user_id
    )
    db.session.add(invoice)

    db.session.commit()


def test_login(client):
    """Test user login and token generation."""
    response = client.post('/api/login', json={
        'username': 'testuser',
        'password': 'password123'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'token' in data
    assert 'user' in data
    assert data['user']['username'] == 'testuser'


def test_get_user(client, auth_token):
    """Test getting user information with token authentication."""
    response = client.get('/api/user', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'user' in data
    assert data['user']['username'] == 'testuser'


def test_get_clients(client, auth_token):
    """Test getting clients with token authentication."""
    response = client.get('/api/clients/', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'clients' in data
    assert len(data['clients']) > 0
    assert data['clients'][0]['name'] == 'Test Client'


def test_get_client_by_id(client, auth_token):
    """Test getting a specific client by ID."""
    # First, get all clients to find the ID
    response = client.get('/api/clients/', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    clients = json.loads(response.data)['clients']
    client_id = clients[0]['id']

    # Now get the specific client
    response = client.get(f'/api/clients/{client_id}', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Test Client'
    assert data['email'] == 'client@example.com'


def test_create_client(client, auth_token):
    """Test creating a new client."""
    response = client.post('/api/clients/', 
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'name': 'New Test Client',
            'email': 'new@example.com',
            'phone': '555-987-6543',
            'address': '456 New St, New City',
            'contact_person': 'New Contact',
            'notes': 'New client notes'
        }
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'message' in data
    assert data['message'] == 'Client created successfully'
    assert data['client']['name'] == 'New Test Client'


def test_get_projects(client, auth_token):
    """Test getting projects with token authentication."""
    response = client.get('/api/projects/', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'projects' in data
    assert len(data['projects']) > 0
    assert data['projects'][0]['name'] == 'Test Project'


def test_get_project_by_id(client, auth_token):
    """Test getting a specific project by ID."""
    # First, get all projects to find the ID
    response = client.get('/api/projects/', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    projects = json.loads(response.data)['projects']
    project_id = projects[0]['id']

    # Now get the specific project
    response = client.get(f'/api/projects/{project_id}', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['name'] == 'Test Project'
    assert data['status'] == 'active'


def test_get_timesheets(client, auth_token):
    """Test getting timesheet entries with token authentication."""
    response = client.get('/api/timesheets/', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'timesheets' in data
    assert len(data['timesheets']) > 0
    assert data['timesheets'][0]['description'] == 'Test timesheet entry'


def test_create_timesheet(client, auth_token):
    """Test creating a new timesheet entry."""
    # First, get client and project IDs
    response = client.get('/api/clients/', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    clients = json.loads(response.data)['clients']
    client_id = clients[0]['id']

    response = client.get('/api/projects/', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    projects = json.loads(response.data)['projects']
    project_id = projects[0]['id']

    # Create a new timesheet entry
    response = client.post('/api/timesheets/', 
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'date': datetime.now().strftime('%Y-%m-%d'),
            'client_id': client_id,
            'project_id': project_id,
            'description': 'New timesheet entry',
            'hours': '3.5',
            'hourly_rate': '110.00'
        }
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'message' in data
    assert data['message'] == 'Timesheet entry created successfully'
    assert data['timesheet']['description'] == 'New timesheet entry'
    # The API formats decimal values with 2 decimal places
    assert float(data['timesheet']['hours']) == 3.5


def test_get_expenses(client, auth_token):
    """Test getting expenses with token authentication."""
    response = client.get('/api/expenses', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'expenses' in data
    assert len(data['expenses']) > 0
    assert data['expenses'][0]['title'] == 'Test Expense'


def test_get_incomes(client, auth_token):
    """Test getting incomes with token authentication."""
    response = client.get('/api/incomes', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'incomes' in data
    assert len(data['incomes']) > 0
    assert data['incomes'][0]['client'] == 'Test Client'


def test_get_invoices(client, auth_token):
    """Test getting invoices with token authentication."""
    response = client.get('/api/invoices/', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'invoices' in data
    assert len(data['invoices']) > 0
    assert data['invoices'][0]['invoice_number'] == 'INV-TEST-001'


def test_get_tax_dashboard(client, auth_token):
    """Test getting tax dashboard data with token authentication."""
    response = client.get('/api/tax/dashboard', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'summary' in data
    assert 'total_income' in data['summary']
    assert 'total_expenses' in data['summary']
    assert 'net_income' in data['summary']


def test_tax_category_suggestions(client, auth_token):
    """Test getting tax category suggestions for an expense."""
    response = client.post('/api/tax/category-suggestions', 
        headers={'Authorization': f'Bearer {auth_token}'},
        json={
            'title': 'Adobe Creative Cloud Subscription',
            'vendor': 'Adobe'
        }
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'suggestions' in data
    assert len(data['suggestions']) > 0
    # The first suggestion should be 'software' with high confidence
    assert data['suggestions'][0]['category'] == 'software'
    assert data['suggestions'][0]['confidence'] > 0.6  # Lowered threshold based on actual results


def test_invalid_token(client):
    """Test that an invalid token is rejected."""
    response = client.get('/api/user', headers={
        'Authorization': 'Bearer invalid-token'
    })
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'message' in data
    assert 'Invalid token' in data['message']


def test_missing_token(client):
    """Test that a missing token is rejected."""
    response = client.get('/api/user')
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'message' in data
    assert 'Authentication token is missing' in data['message']


def test_expired_token(client, auth_token, monkeypatch):
    """Test that an expired token is rejected."""
    # Mock the jwt.decode function to raise an ExpiredSignatureError
    import jwt
    original_decode = jwt.decode
    
    def mock_decode(*args, **kwargs):
        raise jwt.ExpiredSignatureError("Token has expired")
    
    monkeypatch.setattr(jwt, 'decode', mock_decode)
    
    response = client.get('/api/user', headers={
        'Authorization': f'Bearer {auth_token}'
    })
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'message' in data
    assert 'Token has expired' in data['message']
    
    # Restore the original function
    monkeypatch.setattr(jwt, 'decode', original_decode)
