def format_currency(amount, currency_code=None, include_symbol=True):
    """
    Format currency amount with organization-specific currency symbol.
    
    Args:
        amount: Numeric value to format
        currency_code: Optional currency code override
        include_symbol: Whether to include currency symbol
        
    Returns:
        Formatted currency string (e.g., "$1,234.56", "€1,234.56")
    """
    if amount is None:
        return "N/A"
    
    # Get organization settings from database
    try:
        from models import OrganizationSettings
        org_settings = OrganizationSettings.get_organization_settings()
        currency_code = currency_code or (org_settings.currency if org_settings else 'USD')
        print(f"🔧 utils/currency.py Debug: Retrieved currency_code={currency_code} from org_settings")
    except Exception as e:
        print(f"🔧 utils/currency.py Debug: Error getting org settings: {e}")
        currency_code = currency_code or 'USD'
    
    # Currency symbol mapping
    symbol_map = {
        'USD': '$',
        'GBP': '£',
        'EUR': '€',
        'CAD': 'C$',
        'NGN': '₦',
        'AUD': 'A$',
        'JPY': '¥',
        'CNY': '¥',
        'INR': '₹'
    }
    
    # Determine currency symbol
    symbol = symbol_map.get(currency_code.upper() if currency_code else 'USD', '$')
    
    # Format amount with proper number formatting
    try:
        if include_symbol:
            result = f"{symbol}{amount:,.2f}"
        else:
            result = f"{amount:,.2f}"
        print(f"🔧 utils/currency.py Debug: amount={amount}, currency_code={currency_code}, symbol={symbol}, result={result}")
        return result
    except (ValueError, TypeError):
        fallback = f"{symbol}0.00" if include_symbol else "0.00"
        print(f"🔧 utils/currency.py Debug: Error formatting amount={amount}, returning={fallback}")
        return fallback

def get_currency_symbol(currency_code=None):
    """
    Get currency symbol for organization or specified currency.
    
    Args:
        currency_code: Optional currency code override
        
    Returns:
        Currency symbol string
    """
    try:
        from models import OrganizationSettings
        org_settings = OrganizationSettings.get_organization_settings()
        currency_code = currency_code or (org_settings.currency if org_settings else 'USD')
    except Exception:
        currency_code = currency_code or 'USD'
    
    symbol_map = {
        'USD': '$',
        'GBP': '£',
        'EUR': '€',
        'CAD': 'C$',
        'NGN': '₦',
        'AUD': 'A$',
        'JPY': '¥',
        'CNY': '¥',
        'INR': '₹'
    }
    
    return symbol_map.get(currency_code.upper() if currency_code else 'USD', '$')