"""Test the timesheet functionality."""
import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from flask import session

from akowe.models import db
from akowe.models.timesheet import Timesheet


def test_timesheet_index_requires_login(client):
    """Test that the timesheet index page requires login."""
    response = client.get('/timesheet/')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_timesheet_index(client, auth, test_user, sample_timesheet):
    """Test that the timesheet index page shows timesheet entries."""
    auth.login()
    response = client.get('/timesheet/')
    assert response.status_code == 200
    
    # Check that all timesheet entries are displayed
    for entry in sample_timesheet:
        assert entry.client.encode() in response.data
        assert entry.project.encode() in response.data
        assert f"{entry.hours:.2f}".encode() in response.data


def test_timesheet_new_form(client, auth, test_user):
    """Test that the new timesheet form is accessible."""
    auth.login()
    response = client.get('/timesheet/new')
    assert response.status_code == 200
    assert b'New Timesheet Entry' in response.data
    
    # Check for form elements
    assert b'<form' in response.data
    assert b'name="date"' in response.data
    assert b'name="client"' in response.data
    assert b'name="project"' in response.data
    assert b'name="description"' in response.data
    assert b'name="hours"' in response.data
    assert b'name="hourly_rate"' in response.data


def test_timesheet_create(client, auth, test_user, app):
    """Test creating a new timesheet entry."""
    auth.login()
    
    # Submit new timesheet entry
    response = client.post('/timesheet/new', data={
        'date': '2025-04-18',
        'client': 'NewClient',
        'project': 'Test Project',
        'description': 'Testing timesheet functionality',
        'hours': '4.25',
        'hourly_rate': '100.00'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Timesheet entry added successfully!' in response.data
    
    # Verify entry was created in database
    with app.app_context():
        entry = Timesheet.query.filter_by(client='NewClient').first()
        assert entry is not None
        assert entry.date == date(2025, 4, 18)
        assert entry.project == 'Test Project'
        assert entry.description == 'Testing timesheet functionality'
        assert entry.hours == Decimal('4.25')
        assert entry.hourly_rate == Decimal('100.00')
        assert entry.status == 'pending'
        assert entry.user_id == test_user.id


def test_timesheet_edit(client, auth, sample_timesheet, app):
    """Test editing a timesheet entry."""
    auth.login()
    
    # Get the first timesheet entry
    entry_id = sample_timesheet[0].id
    
    # Check edit form
    response = client.get(f'/timesheet/edit/{entry_id}')
    assert response.status_code == 200
    assert b'Edit Timesheet Entry' in response.data
    
    # Submit edit
    response = client.post(f'/timesheet/edit/{entry_id}', data={
        'date': '2025-04-20',
        'client': 'UpdatedClient',
        'project': 'Updated Project',
        'description': 'Updated description',
        'hours': '5.75',
        'hourly_rate': '130.00'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Timesheet entry updated successfully!' in response.data
    
    # Verify changes in database
    with app.app_context():
        updated_entry = Timesheet.query.get(entry_id)
        assert updated_entry.date == date(2025, 4, 20)
        assert updated_entry.client == 'UpdatedClient'
        assert updated_entry.project == 'Updated Project'
        assert updated_entry.description == 'Updated description'
        assert updated_entry.hours == Decimal('5.75')
        assert updated_entry.hourly_rate == Decimal('130.00')


def test_timesheet_delete(client, auth, sample_timesheet, app):
    """Test deleting a timesheet entry."""
    auth.login()
    
    # Get the first timesheet entry
    entry_id = sample_timesheet[0].id
    
    # Delete the entry
    response = client.post(f'/timesheet/delete/{entry_id}', follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Timesheet entry deleted successfully!' in response.data
    
    # Verify entry was deleted
    with app.app_context():
        entry = Timesheet.query.get(entry_id)
        assert entry is None


def test_timesheet_weekly_view(client, auth, sample_timesheet):
    """Test the weekly timesheet view."""
    auth.login()
    
    # Get current week
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    
    response = client.get(f'/timesheet/weekly?week_start={monday.strftime("%Y-%m-%d")}')
    assert response.status_code == 200
    
    # Check for weekly view elements
    assert b'Weekly Timesheet' in response.data
    assert monday.strftime('%B %d, %Y').encode() in response.data
    
    # Quick add form should be present
    assert b'Quick Add Timesheet Entry' in response.data


def test_timesheet_quick_add(client, auth, test_user, app):
    """Test the timesheet quick add functionality."""
    auth.login()
    
    # Submit via AJAX
    response = client.post('/timesheet/quick_add', 
                         json={
                             'date': '2025-04-19',
                             'client': 'QuickClient',
                             'project': 'Quick Project',
                             'description': 'Quick add test',
                             'hours': '2.5',
                             'hourly_rate': '95.00'
                         },
        content_type='application/json')
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['client'] == 'QuickClient'
    assert data['hours'] == 2.5
    
    # Verify entry was created in database
    with app.app_context():
        entry = Timesheet.query.filter_by(client='QuickClient').first()
        assert entry is not None
        assert entry.project == 'Quick Project'
        assert entry.hours == Decimal('2.5')


def test_cant_edit_billed_timesheet(client, auth, app, test_user, sample_invoice):
    """Test that billed timesheet entries cannot be edited."""
    auth.login()
    
    # Get a billed timesheet entry
    with app.app_context():
        billed_entry = Timesheet.query.filter_by(status='billed').first()
        assert billed_entry is not None
        
        entry_id = billed_entry.id
    
    # Try to edit
    response = client.post(f'/timesheet/edit/{entry_id}', data={
        'date': '2025-04-20',
        'client': 'UpdatedClient',
        'project': 'Updated Project',
        'description': 'Updated description',
        'hours': '5.75',
        'hourly_rate': '130.00'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Cannot edit a timesheet entry that has already been billed or paid' in response.data
    
    # Verify entry was not changed
    with app.app_context():
        entry = Timesheet.query.get(entry_id)
        assert entry.client != 'UpdatedClient'
        assert entry.status == 'billed'


def test_cant_delete_billed_timesheet(client, auth, app, test_user, sample_invoice):
    """Test that billed timesheet entries cannot be deleted."""
    auth.login()
    
    # Get a billed timesheet entry
    with app.app_context():
        billed_entry = Timesheet.query.filter_by(status='billed').first()
        assert billed_entry is not None
        
        entry_id = billed_entry.id
    
    # Try to delete
    response = client.post(f'/timesheet/delete/{entry_id}', follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Cannot delete a timesheet entry that has already been billed or paid' in response.data
    
    # Verify entry was not deleted
    with app.app_context():
        entry = Timesheet.query.get(entry_id)
        assert entry is not None