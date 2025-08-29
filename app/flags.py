"""
Feature flags for safe deployment and feature rollout
"""
import os

def is_enabled(flag: str, default=False):
    """Check if a feature flag is enabled"""
    v = os.getenv(flag) or os.getenv(flag.upper())
    if v is None:
        return default
    return str(v).lower() in ("1", "true", "on", "enabled")

# Executive dashboard feature flag
def is_exec_dashboard_enabled():
    return is_enabled("FEATURE_EXEC_DASHBOARD", default=True)

# Onboarding wizard feature flag (default OFF for safety)
def is_onboarding_enabled():
    return is_enabled("ENABLE_ONBOARDING_FLOW", default=False)

# Platform hardening features
def is_platform_hardening_enabled():
    return is_enabled("FEATURE_PLATFORM_HARDENING", default=True)

# Rate limiting feature
def is_rate_limiting_enabled():
    return is_enabled("FEATURE_RATE_LIMITING", default=True)