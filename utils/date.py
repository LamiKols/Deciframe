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
    
    # Get organization settings from database
    try:
        from models import OrganizationSettings
        org_settings = OrganizationSettings.get_organization_settings()
        date_format = org_settings.date_format if org_settings else 'ISO'
        print(f"🔧 utils/date.py format_date Debug: Retrieved date_format={date_format}")
    except Exception as e:
        print(f"🔧 utils/date.py format_date Debug: Error getting org settings: {e}")
        date_format = 'ISO'
    
    # Format mapping
    format_mapping = {
        'US': '%m/%d/%Y',      # 12/31/2023
        'EU': '%d/%m/%Y',      # 31/12/2023
        'ISO': '%Y-%m-%d',     # 2023-12-31
        'Long': '%B %d, %Y'    # December 31, 2023
    }
    
    fmt = format_mapping.get(date_format, '%Y-%m-%d')
    
    # Format date with proper error handling
    try:
        result = dt.strftime(fmt)
        print(f"🔧 utils/date.py format_date Debug: dt={dt}, date_format={date_format}, fmt={fmt}, result={result}")
        return result
    except (ValueError, AttributeError):
        result = dt.strftime("%d/%m/%Y") if dt else "N/A"
        print(f"🔧 utils/date.py format_date Debug: Error formatting, fallback result={result}")
        return result

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
    
    # Get organization settings from database
    try:
        from models import OrganizationSettings
        org_settings = OrganizationSettings.get_organization_settings()
        date_format = org_settings.date_format if org_settings else 'ISO'
        timezone_name = org_settings.timezone if org_settings else 'UTC'
        print(f"🔧 utils/date.py format_datetime Debug: Retrieved date_format={date_format}, timezone={timezone_name}")
    except Exception as e:
        print(f"🔧 utils/date.py format_datetime Debug: Error getting org settings: {e}")
        date_format = 'ISO'
        timezone_name = 'UTC'
    
    # Handle timezone conversion
    try:
        import pytz
        if dt.tzinfo is None:
            # Assume UTC if no timezone info
            dt = pytz.UTC.localize(dt)
        
        # Convert to org timezone
        org_tz = pytz.timezone(timezone_name)
        dt = dt.astimezone(org_tz)
    except Exception as e:
        print(f"🔧 utils/date.py format_datetime Debug: Timezone conversion error: {e}")
        # Continue with original datetime
    
    # Format mapping
    format_mapping = {
        'US': '%m/%d/%Y',      # 12/31/2023
        'EU': '%d/%m/%Y',      # 31/12/2023
        'ISO': '%Y-%m-%d',     # 2023-12-31
        'Long': '%B %d, %Y'    # December 31, 2023
    }
    
    date_fmt = format_mapping.get(date_format, '%Y-%m-%d')
    time_fmt = '%I:%M %p'  # 12-hour format with AM/PM
    datetime_fmt = f"{date_fmt} {time_fmt}"
    
    # Format datetime with proper error handling
    try:
        result = dt.strftime(datetime_fmt)
        print(f"🔧 utils/date.py format_datetime Debug: dt={dt}, date_format={date_format}, result={result}")
        return result
    except (ValueError, AttributeError):
        result = dt.strftime("%d/%m/%Y %H:%M:%S") if dt else "N/A"
        print(f"🔧 utils/date.py format_datetime Debug: Error formatting, fallback result={result}")
        return result