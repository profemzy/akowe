"""Integration tests for timezone handling in API endpoints."""

import os
import pytest
import json
import pytz
from datetime import datetime, date, timedelta
from decimal import Decimal
from unittest.mock import patch

from akowe.models import db
from akowe.models.invoice import Invoice
from akowe.models.timesheet import Timesheet
from akowe.models.client import Client
from akowe.models.project import Project

# Simple test for timezone utility in app context
def test_timezone_init(app):
    """Test that timezone initialization works in application context."""
    from akowe.utils.timezone import get_timezone, get_current_local_datetime
    
    with app.app_context():
        # Test that we can get the timezone
        tz = get_timezone()
        assert tz is not None
        
        # Test that we can get the current time
        local_time = get_current_local_datetime()
        assert local_time is not None
        assert local_time.tzinfo is not None

# Test datetime conversion in database context
def test_datetime_conversion(app):
    """Test datetime conversion functions in app context."""
    from akowe.utils.timezone import to_local_time, to_utc, local_date_input
    
    with app.app_context():
        # Test timezone conversion
        now_utc = datetime.now(pytz.UTC)
        local_time = to_local_time(now_utc)
        
        # Should be different times but same absolute moment
        assert now_utc.hour != local_time.hour or now_utc.day != local_time.day
        
        # Test converting back
        back_to_utc = to_utc(local_time)
        # Should be same hour in UTC
        assert now_utc.hour == back_to_utc.hour
        assert now_utc.day == back_to_utc.day
        
        # Test date parsing
        today = date.today()
        parsed_date = local_date_input(today.strftime("%Y-%m-%d"))
        assert parsed_date == today

# Test model operations with timezones
def test_model_timezone_handling(app):
    """Test that models properly handle timezone conversion."""
    from akowe.utils.timezone import to_local_time
    
    with app.app_context(), patch.dict(os.environ, {"TIMEZONE": "America/Los_Angeles"}, clear=True):
        # Create a user for testing
        from akowe.models.user import User
        user = User(
            username="timezone_test",
            email="timezone_test@example.com",
            first_name="Timezone",
            last_name="Test",
            hourly_rate=Decimal("120.00"),
        )
        user.password = "password"
        db.session.add(user)
        db.session.flush()
        
        # Create a client for testing
        client = Client(
            name="Test Client",
            email="test@example.com",
            contact_person="Test Contact",
            user_id=user.id
        )
        db.session.add(client)
        db.session.flush()
        
        # Create a project for testing
        project = Project(
            name="Test Project",
            description="Test project for timezone testing",
            client_id=client.id,
            user_id=user.id
        )
        db.session.add(project)
        db.session.flush()
        
        # Create a timesheet entry with today's date
        today = date.today()
        entry = Timesheet(
            date=today,
            client_id=client.id,
            project_id=project.id,
            description="Testing timezone handling",
            hours=Decimal("4.5"),
            hourly_rate=Decimal("120.00"),
            status="pending",
            user_id=user.id
        )
        db.session.add(entry)
        db.session.commit()
        
        # Verify the date is stored correctly
        saved_entry = Timesheet.query.filter_by(description="Testing timezone handling").first()
        assert saved_entry is not None
        assert saved_entry.date == today
        
        # Create an invoice with timesheet entry
        invoice = Invoice(
            invoice_number="TST-001",
            client_id=client.id,
            issue_date=today,
            due_date=today + timedelta(days=30),
            notes="Test invoice",
            tax_rate=Decimal("10.00"),
            status="draft",
            user_id=user.id
        )
        db.session.add(invoice)
        db.session.commit()
        
        # Verify the dates
        saved_invoice = Invoice.query.filter_by(invoice_number="TST-001").first()
        assert saved_invoice is not None
        assert saved_invoice.issue_date == today
        
        # Test datetime field with timezone conversion
        # Mark as sent to set sent_date (which is a datetime)
        saved_invoice.status = "sent"
        saved_invoice.sent_date = datetime.utcnow()
        db.session.commit()
        
        # Reload and verify
        saved_invoice = Invoice.query.filter_by(invoice_number="TST-001").first()
        assert saved_invoice.sent_date is not None
        # Note: The tzinfo will be None for database-loaded datetimes, which is expected
        # The important test is that we can convert it with our timezone utilities
        
        # Convert to local time for display
        local_sent_date = to_local_time(saved_invoice.sent_date)
        assert local_sent_date.tzinfo.zone == "America/Los_Angeles"
        
        # Clean up
        db.session.delete(invoice)
        db.session.delete(entry)
        db.session.delete(project)
        db.session.delete(client)
        db.session.delete(user)
        db.session.commit()


# Test template filter
def test_template_filters(app):
    """Test that template filters format dates correctly."""
    with app.app_context():
        # Get the filter functions
        format_date_filter = app.jinja_env.filters["format_date"]
        format_datetime_filter = app.jinja_env.filters["format_datetime"]
        local_datetime_filter = app.jinja_env.filters["local_datetime"]
        
        # Test date formatting
        test_date = date(2025, 4, 17)
        formatted = format_date_filter(test_date)
        assert formatted == "2025-04-17"
        
        # Test datetime formatting
        test_datetime = datetime(2025, 4, 17, 14, 30, 0, tzinfo=pytz.UTC)
        formatted = format_datetime_filter(test_datetime)
        assert "2025-04-17" in formatted
        assert ":" in formatted  # Time separator
        
        # Test local datetime conversion
        local_dt = local_datetime_filter(test_datetime)
        assert local_dt.tzinfo is not None
        assert local_dt.tzinfo != pytz.UTC  # Should be converted from UTC


# Test template context processor
def test_timezone_context_processor(app):
    """Test that timezone information is injected into template context."""
    with app.app_context():
        # Initialize app with timezone
        from akowe.utils.timezone_initializer import init_timezone
        init_timezone(app)
        
        # Create a test request context
        with app.test_request_context():
            # Get context processor
            context_processors = app.template_context_processors[None]
            
            # Run all context processors and combine their results
            context = {}
            for processor in context_processors:
                context.update(processor())
            
            # Check for timezone related variables in context
            assert "timezone" in context
            assert "timezone_abbr" in context
            assert "timezone_offset" in context
            assert "current_time" in context
            
            # Verify the timezone information
            assert context["timezone"] in pytz.all_timezones
            assert context["current_time"].tzinfo is not None