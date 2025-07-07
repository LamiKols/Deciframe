"""
Organization and User Preference Utilities
Provides centralized access to organization-level settings and user preferences
"""

from flask import current_app, g
from flask_login import current_user
from models import OrganizationSettings, User


def get_org_preferences():
    """
    Get organization-level preferences with fallbacks to application defaults
    Returns a dictionary containing timezone, currency, and date format settings
    """
    try:
        # Try to get organization settings
        org_settings = OrganizationSettings.get_organization_settings()
        
        # Build preferences dictionary with fallbacks
        preferences = {
            'currency': getattr(org_settings, 'currency', current_app.config.get('DEFAULT_CURRENCY', 'USD')),
            'date_format': getattr(org_settings, 'date_format', current_app.config.get('DEFAULT_DATE_FORMAT', '%Y-%m-%d')),
            'timezone': getattr(org_settings, 'timezone', current_app.config.get('DEFAULT_TIMEZONE', 'UTC')),
            'time_format': getattr(org_settings, 'time_format', '%H:%M:%S'),
            'default_theme': getattr(org_settings, 'default_theme', 'light')
        }
        
        return preferences
    except Exception:
        # Fallback to application defaults if database is unavailable
        return {
            'currency': current_app.config.get('DEFAULT_CURRENCY', 'USD'),
            'date_format': current_app.config.get('DEFAULT_DATE_FORMAT', '%Y-%m-%d'),
            'timezone': current_app.config.get('DEFAULT_TIMEZONE', 'UTC'),
            'time_format': '%H:%M:%S',
            'default_theme': 'light'
        }


def get_user_preferences():
    """
    Get user-level preferences with fallbacks to organization defaults
    Returns a dictionary containing user-specific overrides or organization defaults
    """
    org_prefs = get_org_preferences()
    
    if not current_user.is_authenticated:
        return org_prefs
    
    try:
        user = current_user
        
        # User-level overrides (if implemented in the future)
        user_prefs = {
            'currency': org_prefs['currency'],  # Use org currency for now
            'date_format': org_prefs['date_format'],  # Use org date format for now  
            'timezone': getattr(user, 'timezone', None) or org_prefs['timezone'],
            'time_format': org_prefs['time_format'],
            'theme': getattr(user, 'theme', None) or org_prefs['default_theme']
        }
        
        return user_prefs
    except Exception:
        # Fallback to organization preferences
        return org_prefs


def get_currency_symbol(currency_code=None):
    """
    Get currency symbol for a given currency code or current organization currency
    """
    if not currency_code:
        prefs = get_org_preferences()
        currency_code = prefs['currency']
    
    currency_symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'CAD': 'C$',
        'AUD': 'A$',
        'JPY': '¥',
        'CNY': '¥',
        'INR': '₹'
    }
    
    return currency_symbols.get(currency_code, currency_code)


def format_currency_value(value, currency_code=None, include_symbol=True):
    """
    Format a numeric value as currency with appropriate symbol and formatting
    """
    if value is None:
        return "N/A"
    
    try:
        # Convert to float
        amount = float(value)
        
        # Get currency symbol
        if include_symbol:
            symbol = get_currency_symbol(currency_code)
            return f"{symbol}{amount:,.2f}"
        else:
            return f"{amount:,.2f}"
    except (ValueError, TypeError):
        return str(value)


def format_date_value(value, format_override=None):
    """
    Format a date/datetime value using organization preferences
    """
    if not value:
        return "N/A"
    
    try:
        prefs = get_org_preferences()
        fmt = format_override or prefs['date_format']
        
        # Handle 'ISO' format specially
        if fmt == 'ISO':
            fmt = '%Y-%m-%d'
        
        return value.strftime(fmt)
    except (AttributeError, ValueError):
        return str(value)


def format_datetime_value(value, format_override=None, include_time=True):
    """
    Format a datetime value using organization preferences with timezone support
    """
    if not value:
        return "N/A"
    
    try:
        import pytz
        from datetime import datetime
        
        prefs = get_org_preferences()
        
        # Handle timezone conversion
        org_timezone = pytz.timezone(prefs['timezone'])
        
        # Convert to organization timezone if value is timezone-aware
        if hasattr(value, 'astimezone') and value.tzinfo:
            value = value.astimezone(org_timezone)
        elif hasattr(value, 'replace') and not value.tzinfo:
            # Assume UTC if no timezone info
            utc_value = pytz.UTC.localize(value)
            value = utc_value.astimezone(org_timezone)
        
        # Format the date/time
        date_fmt = format_override or prefs['date_format']
        if date_fmt == 'ISO':
            date_fmt = '%Y-%m-%d'
        
        if include_time:
            time_fmt = prefs['time_format']
            full_fmt = f"{date_fmt} {time_fmt}"
        else:
            full_fmt = date_fmt
        
        return value.strftime(full_fmt)
    except Exception:
        # Fallback to simple string conversion
        return str(value)