#!/usr/bin/env python3
"""
Samsara Sync Helper Utilities

Common utilities for syncing data between Samsara and your system.
"""

from typing import Dict, Optional, Tuple
import re


def parse_formatted_address(formatted_address: str) -> Dict[str, Optional[str]]:
    """
    Parse Samsara's formattedAddress into components.
    
    Args:
        formatted_address: Address string like "123 Main St, City, ST 12345"
    
    Returns:
        Dictionary with address1, city, state, zip_code
    """
    parts = [p.strip() for p in formatted_address.split(',')]
    
    if len(parts) < 3:
        return {
            'address1': formatted_address,
            'city': None,
            'state': None,
            'zip_code': None
        }
    
    address1 = parts[0]
    city = parts[1]
    state_zip = parts[2]
    
    # Match "ST 12345" or "ST 12345-6789"
    match = re.match(r'([A-Z]{2})\s+(\d{5}(?:-\d{4})?)', state_zip)
    
    if match:
        state = match.group(1)
        zip_code = match.group(2)
    else:
        state = None
        zip_code = None
    
    return {
        'address1': address1,
        'city': city,
        'state': state,
        'zip_code': zip_code
    }


def format_address(
    address1: str,
    city: Optional[str] = None,
    state: Optional[str] = None,
    zip_code: Optional[str] = None
) -> str:
    """
    Format address components into Samsara's formattedAddress format.
    
    Returns:
        Formatted address string
    """
    parts = [address1]
    
    if city:
        parts.append(city)
    
    if state and zip_code:
        parts.append(f"{state} {zip_code}")
    
    return ', '.join(parts)


def map_samsara_status(samsara_state: str) -> str:
    """
    Map Samsara stop state to your system's status.
    
    Args:
        samsara_state: Samsara stop state (scheduled, en route, etc.)
    
    Returns:
        Mapped status for your system
    """
    mapping = {
        'scheduled': 'PENDING',
        'en route': 'ENROUTE',
        'en_route': 'ENROUTE',
        'arrived': 'ARRIVED',
        'departed': 'COMPLETED',
        'completed': 'COMPLETED',
        'skipped': 'CANCELLED'
    }
    
    return mapping.get(samsara_state, 'PENDING')


def map_local_status(local_status: str) -> str:
    """
    Map your system's status to Samsara stop state.
    
    Args:
        local_status: Your system's status
    
    Returns:
        Samsara stop state
    """
    mapping = {
        'PENDING': 'scheduled',
        'ENROUTE': 'en route',
        'ARRIVED': 'arrived',
        'COMPLETED': 'completed',
        'CANCELLED': 'skipped'
    }
    
    return mapping.get(local_status, 'scheduled')


def should_guard_status_update(
    current_status: str,
    new_status: str
) -> Tuple[bool, Optional[str]]:
    """
    Determine if a status update should be prevented to avoid regression.
    
    Args:
        current_status: Current status in your system
        new_status: New status from Samsara
    
    Returns:
        Tuple of (should_prevent, reason)
    """
    # Don't revert completed status
    if current_status == 'COMPLETED' and new_status != 'COMPLETED':
        return True, "Preventing completed status regression"
    
    # Don't revert cancelled to anything else (business rule example)
    if current_status == 'CANCELLED' and new_status not in ['COMPLETED', 'CANCELLED']:
        return True, "Preventing cancelled status change"
    
    return False, None


def extract_external_id(external_ids: Optional[Dict], key: str = 'cmc') -> Optional[str]:
    """
    Safely extract external ID from Samsara's externalIds object.
    
    Args:
        external_ids: Samsara externalIds dictionary
        key: Key to extract
    
    Returns:
        External ID value or None
    """
    if not external_ids:
        return None
    
    return external_ids.get(key)


def build_external_ids(*pairs: Tuple[str, str]) -> Dict[str, str]:
    """
    Build externalIds object for Samsara API.
    
    Args:
        *pairs: Tuples of (key, value)
    
    Returns:
        Dictionary suitable for Samsara's externalIds field
    """
    return {key: value for key, value in pairs if value}


def is_excluded_driver(driver_name: str, exclusions: list = None) -> bool:
    """
    Check if a driver should be excluded from sync.
    
    Args:
        driver_name: Driver's name
        exclusions: List of excluded terms (default: ['test', 'demo', 'inactive'])
    
    Returns:
        True if driver should be excluded
    """
    if not driver_name:
        return True
    
    if exclusions is None:
        exclusions = ['test', 'demo', 'inactive']
    
    name_lower = driver_name.lower()
    return any(term in name_lower for term in exclusions)


def calculate_sync_window(days_back: int = 7, days_forward: int = 30) -> Tuple[str, str]:
    """
    Calculate ISO timestamp window for syncing routes.
    
    Args:
        days_back: Days in the past to sync
        days_forward: Days in the future to sync
    
    Returns:
        Tuple of (start_time, end_time) as ISO strings
    """
    from datetime import datetime, timedelta
    
    now = datetime.utcnow()
    start = now - timedelta(days=days_back)
    end = now + timedelta(days=days_forward)
    
    return (
        start.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z',
        end.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat() + 'Z'
    )


# Example usage
if __name__ == "__main__":
    # Test address parsing
    address = "123 Main St, Greenville, SC 29607"
    parsed = parse_formatted_address(address)
    print(f"Parsed: {parsed}")
    
    # Test address formatting
    formatted = format_address(
        "456 Oak Ave",
        "Charlotte",
        "NC",
        "28202"
    )
    print(f"Formatted: {formatted}")
    
    # Test status mapping
    status = map_samsara_status("en route")
    print(f"Mapped status: {status}")
    
    # Test status guard
    should_prevent, reason = should_guard_status_update("COMPLETED", "PENDING")
    print(f"Should prevent: {should_prevent}, Reason: {reason}")
    
    # Test external IDs
    ext_ids = build_external_ids(
        ('cmc', 'action_123'),
        ('tms', 'delivery_456')
    )
    print(f"External IDs: {ext_ids}")
    
    # Test sync window
    start, end = calculate_sync_window()
    print(f"Sync window: {start} to {end}")
