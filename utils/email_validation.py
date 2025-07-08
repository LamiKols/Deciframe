"""
Email domain validation utilities for business email enforcement
"""

import re
import socket
from typing import Tuple

# Common personal email providers to block
PERSONAL_EMAIL_DOMAINS = {
    'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'live.com',
    'aol.com', 'icloud.com', 'me.com', 'mac.com', 'protonmail.com',
    'yandex.com', 'mail.com', 'gmx.com', 'zoho.com', 'fastmail.com',
    'tutanota.com', 'guerrillamail.com', '10minutemail.com', 'tempmail.org'
}

# Suspicious domain patterns that might be personal
SUSPICIOUS_PATTERNS = {
    r'^\d+\w*\.com$',  # Numbers followed by letters like 123abc.com
    r'^[a-z]{1,3}\.com$',  # Very short domains like xy.com
    r'.*temp.*\.com$',  # Anything with 'temp' in it
    r'.*test.*\.com$',  # Anything with 'test' in it
}

def extract_domain(email: str) -> str:
    """Extract domain from email address"""
    if '@' not in email:
        return ''
    return email.split('@')[1].lower().strip()

def is_personal_email_domain(domain: str):
    """Check if domain is in personal email provider list"""
    return domain.lower() in PERSONAL_EMAIL_DOMAINS

def is_suspicious_domain(domain: str):
    """Check if domain matches suspicious patterns"""
    domain_lower = domain.lower()
    for pattern in SUSPICIOUS_PATTERNS:
        if re.match(pattern, domain_lower):
            return True
    return False

def has_mx_record(domain: str):
    """Check if domain has MX records (indicates business email capability)"""
    try:
        mx_records = socket.getaddrinfo(domain, None)
        return len(mx_records) > 0
    except (socket.gaierror, socket.herror):
        try:
            # Try alternative DNS lookup
            import dns.resolver
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(mx_records) > 0
        except:
            # If DNS checks fail, assume it's valid (conservative approach)
            return True

def validate_business_email(email: str) -> Tuple[bool, str]:
    """
    Validate if email appears to be a business email
    Returns (is_valid, error_message)
    """
    if not email or '@' not in email:
        return False, "Please enter a valid email address"
    
    domain = extract_domain(email)
    
    if not domain:
        return False, "Please enter a valid email address"
    
    # Check if it's a known personal email provider
    if is_personal_email_domain(domain):
        return False, f"Please use your business email address. Personal email providers like {domain} are not allowed."
    
    # Check for suspicious patterns
    if is_suspicious_domain(domain):
        return False, "Please use a valid business email address from your organization's domain."
    
    # Basic domain format validation
    if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', domain):
        return False, "Please enter a valid business email domain."
    
    # All checks passed
    return True, ""

def is_new_organization_domain(domain: str):
    """Check if this domain represents a new organization"""
    from models import Organization
    existing_org = Organization.query.filter_by(domain=domain).first()
    return existing_org is None

def get_domain_suggestions(email: str) -> list:
    """Suggest alternative domains if current one is invalid"""
    if not email or '@' not in email:
        return []
    
    username = email.split('@')[0]
    suggestions = [
        f"{username}@yourcompany.com",
        f"{username}@yourorg.com", 
        f"{username}@company.co"
    ]
    return suggestions