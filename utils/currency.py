from flask import g

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
    
    # Get organization from Flask g object
    org = getattr(g, 'current_org', None)
    
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
    if org and org.currency:
        symbol = symbol_map.get(org.currency.upper(), org.currency)
    else:
        symbol = '$'  # Default to USD
    
    # Format amount with proper number formatting
    try:
        return f"{symbol}{amount:,.2f}"
    except (ValueError, TypeError):
        return f"{symbol}0.00"