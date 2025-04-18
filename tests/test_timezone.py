"""Tests for timezone utilities."""

import os
import pytest
import pytz
from datetime import datetime, date, timedelta
from unittest.mock import patch

from akowe.utils.timezone import (
    get_timezone,
    to_local_time,
    to_utc,
    get_current_local_datetime,
    format_date,
    format_datetime,
    local_date_input,
    local_datetime_input,
    convert_to_utc,
    convert_from_utc,
)


def test_get_timezone_default():
    """Test that the default timezone is used when not specified."""
    # Mock environment without TIMEZONE set
    with patch.dict(os.environ, {}, clear=True):
        tz = get_timezone()
        assert tz.zone == "America/Los_Angeles"


def test_get_timezone_from_env():
    """Test that timezone from environment variable is used."""
    # Mock environment with TIMEZONE set
    with patch.dict(os.environ, {"TIMEZONE": "America/New_York"}, clear=True):
        tz = get_timezone()
        assert tz.zone == "America/New_York"


def test_to_local_time():
    """Test conversion from UTC to local time."""
    # Use a fixed UTC time
    utc_time = datetime(2025, 4, 17, 12, 0, 0, tzinfo=pytz.UTC)  # Noon UTC
    
    # Test with America/Los_Angeles (should be early morning)
    with patch.dict(os.environ, {"TIMEZONE": "America/Los_Angeles"}, clear=True):
        local_time = to_local_time(utc_time)
        assert local_time.hour < 12  # Should be morning in LA
    
    # Test with Asia/Tokyo (should be night)
    with patch.dict(os.environ, {"TIMEZONE": "Asia/Tokyo"}, clear=True):
        local_time = to_local_time(utc_time)
        assert local_time.hour > 12  # Should be evening in Tokyo


def test_to_utc():
    """Test conversion from local time to UTC."""
    # Create a naive datetime (assumed to be in local timezone)
    local_naive = datetime(2025, 4, 17, 12, 0, 0)  # Noon local
    
    # Test with America/Los_Angeles
    with patch.dict(os.environ, {"TIMEZONE": "America/Los_Angeles"}, clear=True):
        utc_time = to_utc(local_naive)
        # LA is behind UTC, so UTC hour should be later
        assert utc_time.hour > local_naive.hour or utc_time.day > local_naive.day
    
    # Test with a date object
    local_date = date(2025, 4, 17)
    utc_time = to_utc(local_date)
    assert utc_time.date() == local_date


def test_format_date():
    """Test date formatting in local timezone."""
    test_date = date(2025, 4, 17)
    formatted = format_date(test_date)
    assert formatted == "2025-04-17"
    
    # Test custom format
    formatted = format_date(test_date, "%m/%d/%Y")
    assert formatted == "04/17/2025"


def test_format_datetime():
    """Test datetime formatting in local timezone."""
    utc_time = datetime(2025, 4, 17, 12, 0, 0, tzinfo=pytz.UTC)
    formatted = format_datetime(utc_time)
    
    # Make sure it's formatted in the expected format
    # We can't check the exact hour due to timezone conversion
    assert "2025-04-17" in formatted
    assert ":" in formatted  # Time separator


def test_local_date_input():
    """Test parsing local date input."""
    date_str = "2025-04-17"
    parsed = local_date_input(date_str)
    assert parsed == date(2025, 4, 17)


def test_local_datetime_input():
    """Test parsing local datetime input."""
    datetime_str = "2025-04-17 13:45:00"
    
    with patch.dict(os.environ, {"TIMEZONE": "America/Los_Angeles"}, clear=True):
        parsed = local_datetime_input(datetime_str)
        
        # Check conversion to UTC
        assert parsed.tzinfo == pytz.UTC  # Should be in UTC
        # LA is behind UTC, so UTC hour should be later than 13
        assert parsed.hour > 13 or parsed.day > 17


def test_convert_to_utc_decorator():
    """Test the convert_to_utc decorator."""
    # Define a test function that uses the decorator
    @convert_to_utc
    def test_func(dt):
        return dt
    
    # Test with a naive datetime
    local_naive = datetime(2025, 4, 17, 12, 0, 0)
    result = test_func(dt=local_naive)
    
    assert result.tzinfo == pytz.UTC
    
    # Test with a date object
    local_date = date(2025, 4, 17)
    result = test_func(dt=local_date)
    
    assert result.tzinfo == pytz.UTC
    assert result.date() == local_date


def test_convert_from_utc_decorator():
    """Test the convert_from_utc decorator."""
    # Define a test class with a datetime attribute
    class TestObj:
        def __init__(self):
            self.created_at = datetime(2025, 4, 17, 12, 0, 0, tzinfo=pytz.UTC)
    
    # Define a test function that uses the decorator
    @convert_from_utc
    def test_func():
        obj = TestObj()
        return obj
    
    with patch.dict(os.environ, {"TIMEZONE": "America/Los_Angeles"}, clear=True):
        result = test_func()
        
        # Should be converted to local time
        assert result.created_at.tzinfo.zone == "America/Los_Angeles"