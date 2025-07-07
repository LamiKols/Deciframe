def format_currency(amount):
    """
    Format currency amount with organization-specific currency symbol.
    
    Args:
        amount: Numeric value to format
        
    Returns:
        Formatted currency string (e.g., "$1,234.56", "€1,234.56")
    """
    if amount is None:
        return "N/A"
    
    # Get organization settings from database
    try:
        from models import OrganizationSettings
        org_settings = OrganizationSettings.get_organization_settings()
        currency_code = org_settings.currency if org_settings else 'USD'
        print(f"🔧 utils/currency.py Debug: Retrieved currency_code={currency_code} from org_settings")
    except Exception as e:
        print(f"🔧 utils/currency.py Debug: Error getting org settings: {e}")
        currency_code = 'USD'
    
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
        result = f"{symbol}{amount:,.2f}"
        print(f"🔧 utils/currency.py Debug: amount={amount}, currency_code={currency_code}, symbol={symbol}, result={result}")
        return result
    except (ValueError, TypeError):
        result = f"{symbol}0.00"
        print(f"🔧 utils/currency.py Debug: Error formatting amount={amount}, returning={result}")
        return result
