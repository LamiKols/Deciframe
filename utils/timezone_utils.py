"""
Timezone utilities for DeciFrame application.
Provides comprehensive timezone-aware display functionality.
"""

import pytz
from datetime import datetime
from typing import Optional, Union
from flask import current_app
from flask_login import current_user


def get_user_timezone() -> str:
    """
    Get the effective timezone for the current user.
    
    Priority:
    1. User's personal timezone setting
    2. Organization's default timezone
    3. UTC as fallback
    
    Returns:
        str: IANA timezone identifier
    """
    try:
        # Try user's personal timezone first
        if hasattr(current_user, 'timezone') and current_user.timezone:
            return current_user.timezone
        
        # Fall back to organization timezone
        from models import OrganizationSettings
        org_settings = OrganizationSettings.get_current()
        if org_settings and org_settings.timezone:
            return org_settings.timezone
            
        # Ultimate fallback to UTC
        return 'UTC'
    except Exception as e:
        current_app.logger.warning(f"Error getting user timezone: {e}")
        return 'UTC'


def get_organization_timezone() -> str:
    """
    Get the organization's default timezone.
    
    Returns:
        str: IANA timezone identifier
    """
    try:
        from models import OrganizationSettings
        org_settings = OrganizationSettings.get_current()
        if org_settings and org_settings.timezone:
            return org_settings.timezone
        return 'UTC'
    except Exception as e:
        current_app.logger.warning(f"Error getting organization timezone: {e}")
        return 'UTC'


def convert_to_user_timezone(dt: Optional[datetime], timezone: Optional[str] = None) -> Optional[datetime]:
    """
    Convert UTC datetime to user's timezone.
    
    Args:
        dt: UTC datetime object (can be None)
        timezone: Optional timezone override
        
    Returns:
        datetime object in user's timezone, or None if input is None
    """
    if dt is None:
        return None
        
    if dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = pytz.UTC.localize(dt)
    
    user_tz = timezone or get_user_timezone()
    
    try:
        target_tz = pytz.timezone(user_tz)
        return dt.astimezone(target_tz)
    except Exception as e:
        current_app.logger.warning(f"Error converting timezone: {e}")
        return dt


def format_datetime_for_user(
    dt: Optional[datetime], 
    timezone: Optional[str] = None,
    date_format: Optional[str] = None,
    time_format: Optional[str] = None,
    include_timezone: bool = False
) -> str:
    """
    Format datetime according to user's preferences.
    
    Args:
        dt: UTC datetime object
        timezone: Optional timezone override
        date_format: Optional date format override
        time_format: Optional time format override
        include_timezone: Whether to include timezone abbreviation
        
    Returns:
        Formatted datetime string
    """
    if dt is None:
        return "Not set"
    
    # Convert to user timezone
    user_dt = convert_to_user_timezone(dt, timezone)
    if user_dt is None:
        return "Invalid date"
    
    # Get format preferences
    if not date_format or not time_format:
        try:
            from models import OrganizationSettings
            org_settings = OrganizationSettings.get_current()
            if org_settings:
                date_format = date_format or org_settings.date_format
                time_format = time_format or org_settings.time_format
        except Exception:
            pass
    
    # Default formats
    date_format = date_format or '%Y-%m-%d'
    time_format = time_format or '%H:%M:%S'
    
    # Format the datetime
    formatted = user_dt.strftime(f"{date_format} {time_format}")
    
    if include_timezone:
        tz_abbr = user_dt.strftime('%Z')
        formatted += f" {tz_abbr}"
    
    return formatted


def format_date_for_user(
    dt: Optional[datetime], 
    timezone: Optional[str] = None,
    date_format: Optional[str] = None
) -> str:
    """
    Format date only according to user's preferences.
    
    Args:
        dt: UTC datetime object
        timezone: Optional timezone override
        date_format: Optional date format override
        
    Returns:
        Formatted date string
    """
    if dt is None:
        return "Not set"
    
    # Convert to user timezone
    user_dt = convert_to_user_timezone(dt, timezone)
    if user_dt is None:
        return "Invalid date"
    
    # Get format preference
    if not date_format:
        try:
            from models import OrganizationSettings
            org_settings = OrganizationSettings.get_current()
            if org_settings:
                date_format = org_settings.date_format
        except Exception:
            pass
    
    # Default format
    date_format = date_format or '%Y-%m-%d'
    
    return user_dt.strftime(date_format)


def format_time_for_user(
    dt: Optional[datetime], 
    timezone: Optional[str] = None,
    time_format: Optional[str] = None,
    include_timezone: bool = False
) -> str:
    """
    Format time only according to user's preferences.
    
    Args:
        dt: UTC datetime object
        timezone: Optional timezone override
        time_format: Optional time format override
        include_timezone: Whether to include timezone abbreviation
        
    Returns:
        Formatted time string
    """
    if dt is None:
        return "Not set"
    
    # Convert to user timezone
    user_dt = convert_to_user_timezone(dt, timezone)
    if user_dt is None:
        return "Invalid time"
    
    # Get format preference
    if not time_format:
        try:
            from models import OrganizationSettings
            org_settings = OrganizationSettings.get_current()
            if org_settings:
                time_format = org_settings.time_format
        except Exception:
            pass
    
    # Default format
    time_format = time_format or '%H:%M:%S'
    
    formatted = user_dt.strftime(time_format)
    
    if include_timezone:
        tz_abbr = user_dt.strftime('%Z')
        formatted += f" {tz_abbr}"
    
    return formatted


def get_current_time_in_timezone(timezone: Optional[str] = None) -> datetime:
    """
    Get current datetime in specified timezone.
    
    Args:
        timezone: IANA timezone identifier (defaults to user timezone)
        
    Returns:
        Current datetime in specified timezone
    """
    target_tz = timezone or get_user_timezone()
    
    try:
        tz = pytz.timezone(target_tz)
        return datetime.now(tz)
    except Exception as e:
        current_app.logger.warning(f"Error getting current time: {e}")
        return datetime.now(pytz.UTC)


def create_timezone_aware_datetime(
    year: int, month: int, day: int, 
    hour: int = 0, minute: int = 0, second: int = 0,
    timezone: Optional[str] = None
) -> datetime:
    """
    Create timezone-aware datetime object.
    
    Args:
        year, month, day, hour, minute, second: datetime components
        timezone: IANA timezone identifier (defaults to user timezone)
        
    Returns:
        Timezone-aware datetime object
    """
    target_tz = timezone or get_user_timezone()
    
    try:
        tz = pytz.timezone(target_tz)
        return tz.localize(datetime(year, month, day, hour, minute, second))
    except Exception as e:
        current_app.logger.warning(f"Error creating timezone-aware datetime: {e}")
        return pytz.UTC.localize(datetime(year, month, day, hour, minute, second))


def relative_time_string(dt: Optional[datetime], timezone: Optional[str] = None) -> str:
    """
    Get relative time string (e.g., "2 hours ago", "in 3 days").
    
    Args:
        dt: UTC datetime object
        timezone: Optional timezone override
        
    Returns:
        Human-readable relative time string
    """
    if dt is None:
        return "Unknown time"
    
    # Convert to user timezone
    user_dt = convert_to_user_timezone(dt, timezone)
    if user_dt is None:
        return "Invalid time"
    
    # Get current time in same timezone
    current_time = get_current_time_in_timezone(timezone)
    
    # Calculate difference
    diff = user_dt - current_time
    total_seconds = diff.total_seconds()
    
    # Convert to human-readable format
    if abs(total_seconds) < 60:
        return "Just now"
    elif abs(total_seconds) < 3600:
        minutes = int(abs(total_seconds) / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} {'ago' if total_seconds < 0 else 'from now'}"
    elif abs(total_seconds) < 86400:
        hours = int(abs(total_seconds) / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} {'ago' if total_seconds < 0 else 'from now'}"
    else:
        days = int(abs(total_seconds) / 86400)
        return f"{days} day{'s' if days != 1 else ''} {'ago' if total_seconds < 0 else 'from now'}"


# Template filter functions for Jinja2
def register_timezone_filters(app):
    """
    Register timezone utility functions as Jinja2 template filters.
    
    Args:
        app: Flask application instance
    """
    app.jinja_env.filters['user_datetime'] = format_datetime_for_user
    app.jinja_env.filters['user_date'] = format_date_for_user
    app.jinja_env.filters['user_time'] = format_time_for_user
    app.jinja_env.filters['relative_time'] = relative_time_string
    app.jinja_env.filters['to_user_tz'] = convert_to_user_timezone