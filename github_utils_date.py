
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
        print(f"🔧 utils/date.py format_datetime Debug: Retrieved date_format={date_format}")
    except Exception as e:
        print(f"🔧 utils/date.py format_datetime Debug: Error getting org settings: {e}")
        date_format = 'ISO'
    
    # Format mapping
    format_mapping = {
        'US': '%m/%d/%Y %I:%M %p',      # 12/31/2023 11:59 PM
        'EU': '%d/%m/%Y %H:%M',         # 31/12/2023 23:59
        'ISO': '%Y-%m-%d %H:%M',        # 2023-12-31 23:59
        'Long': '%B %d, %Y at %I:%M %p' # December 31, 2023 at 11:59 PM
    }
    
    fmt = format_mapping.get(date_format, '%Y-%m-%d %H:%M')
    
    # Format datetime with proper error handling
    try:
        result = dt.strftime(fmt)
        print(f"🔧 utils/date.py format_datetime Debug: dt={dt}, date_format={date_format}, fmt={fmt}, result={result}")
        return result
    except (ValueError, AttributeError):
        result = dt.strftime("%d/%m/%Y %H:%M") if dt else "N/A"
        print(f"🔧 utils/date.py format_datetime Debug: Error formatting, fallback result={result}")
        return result

def format_org_date(dt, format_override=None):
    """
    Format a date using organization preferences with optional override.
    
    Args:
        dt: datetime object to format
        format_override: Optional format override string
        
    Returns:
        Formatted date string
    """
    if dt is None:
        return "N/A"
    
    if format_override:
        try:
            result = dt.strftime(format_override)
            print(f"🔧 Date Filter Debug: Override format={format_override}, result={result}")
            return result
        except (ValueError, AttributeError):
            pass
    
    return format_date(dt)

def format_org_datetime(dt, format_override=None, include_time=True):
    """
    Format a datetime using organization preferences with timezone support.
    
    Args:
        dt: datetime object to format
        format_override: Optional format override string
        include_time: Whether to include time component
        
    Returns:
        Formatted datetime string
    """
    if dt is None:
        return "N/A"
    
    if format_override:
        try:
            result = dt.strftime(format_override)
            print(f"🔧 DateTime Filter Debug: Override format={format_override}, result={result}")
            return result
        except (ValueError, AttributeError):
            pass
    
    if include_time:
        return format_datetime(dt)
    else:
        return format_date(dt)