"""Initialize timezone settings for the application."""

import os
import pytz
import logging
from datetime import datetime
from flask import Flask

from akowe.utils.timezone import DEFAULT_TIMEZONE, get_timezone


def init_timezone(app: Flask):
    """Set up timezone configuration for the Flask app.
    
    Args:
        app: The Flask application instance
    """
    # Get timezone from environment
    tz_name = os.environ.get("TIMEZONE", DEFAULT_TIMEZONE)
    
    # Verify the timezone is valid
    try:
        tz = pytz.timezone(tz_name)
        app.config["TIMEZONE"] = tz_name
        
        # Log the timezone configuration
        app.logger.info(f"Timezone set to {tz_name}")
        
        # Add timezone information to app context
        @app.context_processor
        def inject_timezone():
            """Make timezone available in all templates."""
            now_utc = datetime.now(pytz.utc)
            now_local = now_utc.astimezone(tz)
            
            return {
                "timezone": tz_name,
                "timezone_abbr": now_local.strftime("%Z"),
                "timezone_offset": now_local.strftime("%z"),
                "current_time": now_local
            }
        
    except pytz.exceptions.UnknownTimeZoneError:
        app.logger.error(f"Invalid timezone: {tz_name}. Using default: {DEFAULT_TIMEZONE}")
        app.config["TIMEZONE"] = DEFAULT_TIMEZONE