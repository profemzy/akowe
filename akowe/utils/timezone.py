"""Timezone utilities for the application."""

import os
import datetime
import pytz
from typing import Union, Optional
from functools import wraps
from flask import current_app

DEFAULT_TIMEZONE = "America/Los_Angeles"


def get_timezone() -> pytz.timezone:
    """Get the timezone from the environment or use the default."""
    tz_name = os.environ.get("TIMEZONE", DEFAULT_TIMEZONE)
    try:
        return pytz.timezone(tz_name)
    except pytz.exceptions.UnknownTimeZoneError:
        # Fall back to default if the timezone is invalid
        return pytz.timezone(DEFAULT_TIMEZONE)


def to_local_time(dt: datetime.datetime) -> datetime.datetime:
    """Convert UTC datetime to the local timezone.
    
    Args:
        dt: The UTC datetime to convert
        
    Returns:
        The datetime in the local timezone
    """
    if dt is None:
        return None
    
    # Ensure the input datetime is timezone-aware and in UTC
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    elif dt.tzinfo != pytz.utc:
        dt = dt.astimezone(pytz.utc)
    
    # Convert to local timezone
    return dt.astimezone(get_timezone())


def to_utc(dt: Union[datetime.datetime, datetime.date], time_only: bool = False) -> datetime.datetime:
    """Convert a local datetime or date to UTC.
    
    Args:
        dt: The local datetime or date to convert
        time_only: If True, only the time part of the datetime will be used
        
    Returns:
        The datetime in UTC
    """
    if dt is None:
        return None
    
    # Handle date objects
    if isinstance(dt, datetime.date) and not isinstance(dt, datetime.datetime):
        dt = datetime.datetime.combine(dt, datetime.time())
    
    # Localize the datetime if it's naive
    if dt.tzinfo is None:
        local_tz = get_timezone()
        dt = local_tz.localize(dt)
    
    # Convert to UTC
    return dt.astimezone(pytz.utc)


def get_current_local_datetime() -> datetime.datetime:
    """Get the current datetime in the local timezone.
    
    Returns:
        The current datetime in the local timezone
    """
    return to_local_time(datetime.datetime.now(pytz.utc))


def format_datetime(dt: datetime.datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format a datetime in the local timezone.
    
    Args:
        dt: The datetime to format
        format_str: The format string to use
        
    Returns:
        The formatted datetime string
    """
    if dt is None:
        return ""
    
    # Convert to local time if not already
    if dt.tzinfo != get_timezone():
        dt = to_local_time(dt)
    
    return dt.strftime(format_str)


def format_date(dt: Union[datetime.datetime, datetime.date], format_str: str = "%Y-%m-%d") -> str:
    """Format a date or datetime as a date string.
    
    Args:
        dt: The date or datetime to format
        format_str: The format string to use
        
    Returns:
        The formatted date string
    """
    if dt is None:
        return ""
    
    # If it's a datetime, convert to local time
    if isinstance(dt, datetime.datetime):
        dt = to_local_time(dt).date()
    
    return dt.strftime(format_str)


# Decorators for model operations

def convert_to_utc(func):
    """Decorator that converts local date/datetime inputs to UTC.
    
    This decorator should be used on model create/update methods to ensure
    that any date or datetime values are converted to UTC before saving to database.
    
    Example:
        @convert_to_utc
        def create_invoice(self, form_data):
            # form_data contains local dates that will be converted to UTC
            return Invoice(**form_data)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Process kwargs for datetime fields
        for key, value in kwargs.items():
            if isinstance(value, (datetime.datetime, datetime.date)):
                if isinstance(value, datetime.datetime) and value.tzinfo is not None:
                    # If it's already timezone-aware, just convert to UTC
                    kwargs[key] = value.astimezone(pytz.utc)
                else:
                    # If it's naive or just a date, treat it as local time
                    kwargs[key] = to_utc(value)
        
        return func(*args, **kwargs)
    return wrapper


def convert_from_utc(func):
    """Decorator that converts UTC date/datetime outputs to local timezone.
    
    This decorator should be used on model read methods to ensure
    that any date or datetime values are converted from UTC to local time.
    
    Example:
        @convert_from_utc
        def get_invoice(self, id):
            # Return values with dates converted to local time
            return Invoice.query.get(id)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        
        # Handle single objects
        if hasattr(result, '__dict__'):
            for key, value in result.__dict__.items():
                if isinstance(value, datetime.datetime):
                    setattr(result, key, to_local_time(value))
        
        # Handle lists/iterables
        elif isinstance(result, (list, tuple)) and len(result) > 0:
            for item in result:
                if hasattr(item, '__dict__'):
                    for key, value in item.__dict__.items():
                        if isinstance(value, datetime.datetime):
                            setattr(item, key, to_local_time(value))
        
        return result
    return wrapper


def local_date_input(date_str: str, format_str: str = "%Y-%m-%d") -> datetime.date:
    """Convert a date string in local timezone to a UTC date object.
    
    This function is useful for converting form inputs to database dates.
    
    Args:
        date_str: The date string in local timezone
        format_str: The format string to parse the date
        
    Returns:
        A UTC datetime.date object
    """
    if not date_str:
        return None
    
    # Parse the date string as a local date
    local_date = datetime.datetime.strptime(date_str, format_str).date()
    
    # We don't need to convert dates (without time) to UTC since they don't have timezone
    return local_date


def local_datetime_input(datetime_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime.datetime:
    """Convert a datetime string in local timezone to a UTC datetime object.
    
    This function is useful for converting form inputs to database datetimes.
    
    Args:
        datetime_str: The datetime string in local timezone
        format_str: The format string to parse the datetime
        
    Returns:
        A UTC datetime.datetime object
    """
    if not datetime_str:
        return None
    
    # Parse the datetime string as a local datetime
    local_dt = datetime.datetime.strptime(datetime_str, format_str)
    
    # Convert to UTC
    return to_utc(local_dt)