from flask import g
from datetime import datetime

def format_date(dt):
    """
    Format date with organization-specific date format.
    
    Args:
        dt: datetime object to format
        
    Returns:
        Formatted date string according to organization settings
    """
    if dt is None:
        return "N/A"
    
    # Get organization from Flask g object
    org = getattr(g, 'current_org', None)
    
    # Determine date format
    if org and org.date_format:
        fmt = org.date_format
    else:
        fmt = "%d/%m/%Y"  # Default to European format
    
    # Handle ISO format special case
    if fmt == 'ISO':
        fmt = "%Y-%m-%d"
    
    # Format date with proper error handling
    try:
        return dt.strftime(fmt)
    except (ValueError, AttributeError):
        return dt.strftime("%d/%m/%Y") if dt else "N/A"

def format_datetime(dt):
    """
    Format datetime with organization-specific date and time formats.
    
    Args:
        dt: datetime object to format
        
    Returns:
        Formatted datetime string according to organization settings
    """
    if dt is None:
        return "N/A"
    
    # Get organization from Flask g object
    org = getattr(g, 'current_org', None)
    
    # Determine formats
    date_fmt = org.date_format if org and org.date_format else "%d/%m/%Y"
    time_fmt = org.time_format if org and org.time_format else "%H:%M:%S"
    
    # Handle ISO format special case
    if date_fmt == 'ISO':
        date_fmt = "%Y-%m-%d"
    
    # Combine date and time formats
    datetime_fmt = f"{date_fmt} {time_fmt}"
    
    # Format datetime with proper error handling
    try:
        return dt.strftime(datetime_fmt)
    except (ValueError, AttributeError):
        return dt.strftime("%d/%m/%Y %H:%M:%S") if dt else "N/A"