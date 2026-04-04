"""
Utility functions for the Coinbase Data Downloader
"""

import re
from datetime import datetime
from typing import Dict

GRANULARITY_SECONDS: Dict[str, int] = {
    'MINUTE': 60,
    'HOUR': 3600,
    'DAILY': 86400
}


def parse_datetime(datetime_str: str) -> datetime:
    """
    Parse a datetime string in format yyyyMMdd-hh:mm:ss.
    
    Args:
        datetime_str: String to parse
    
    Returns:
        Parsed datetime object
    """
    pattern = r'^\d{8}-\d{2}:\d{2}:\d{2}$'
    if not re.match(pattern, datetime_str):
        raise ValueError(
            f"Invalid datetime format: {datetime_str}. "
            f"Expected format: yyyyMMdd-hh:mm:ss (e.g., 20240101-09:30:00)"
        )
    return datetime.strptime(datetime_str, '%Y%m%d-%H:%M:%S')


def parse_iso_datetime(time_str: str) -> datetime:
    """
    Parse an ISO-style datetime string, normalizing UTC Z timezone suffix.
    
    Args:
        time_str: ISO datetime string
    
    Returns:
        Parsed datetime object
    """
    if time_str.endswith('Z'):
        time_str = time_str.replace('Z', '+00:00')
    return datetime.fromisoformat(time_str)


def normalize_symbol(symbol: str) -> str:
    """
    Normalize symbol names for file and folder paths.
    
    Args:
        symbol: Symbol string (e.g., BTC-USD)
    
    Returns:
        Normalized symbol (e.g., btcusd)
    """
    return symbol.lower().replace('-', '')


def validate_datetime_format(datetime_str: str) -> bool:
    """
    Validate that a string matches the required datetime format: yyyyMMdd-hh:mm:ss
    
    Args:
        datetime_str: String to validate
    
    Returns:
        True if format is valid, False otherwise
    """
    pattern = r'^\d{8}-\d{2}:\d{2}:\d{2}$'
    return bool(re.match(pattern, datetime_str))


def validate_symbol_format(symbol: str) -> bool:
    """
    Validate that a symbol matches expected Coinbase format (e.g., BTC-USD)
    
    Args:
        symbol: Symbol string to validate
    
    Returns:
        True if format is valid, False otherwise
    """
    pattern = r'^[A-Z0-9]+-[A-Z]+$'
    return bool(re.match(pattern, symbol))


def format_bytes(bytes_size: float) -> str:
    """
    Format bytes to human-readable format.
    
    Args:
        bytes_size: Size in bytes
    
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024
    return f"{bytes_size:.2f} TB"


def format_number(number: float, decimal_places: int = 2) -> str:
    """
    Format a number with thousand separators.
    
    Args:
        number: Number to format
        decimal_places: Number of decimal places
    
    Returns:
        Formatted string (e.g., "1,234.56")
    """
    return f"{number:,.{decimal_places}f}"


def get_date_range_description(start_dt: datetime, end_dt: datetime) -> str:
    """
    Get a human-readable description of a date range.
    
    Args:
        start_dt: Start datetime
        end_dt: End datetime
    
    Returns:
        Description string (e.g., "5 days, 3 hours")
    """
    delta = end_dt - start_dt
    
    days = delta.days
    seconds = delta.seconds
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days > 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes > 0 and not parts:  # Only show minutes if less than 1 hour
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    
    return ", ".join(parts) if parts else "less than 1 minute"
