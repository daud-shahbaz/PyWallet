"""
Helper functions for PyWallet.
Contains common utility functions used across the application.
"""

import re
from typing import Union
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def format_currency(amount: Union[int, float], currency: str = "PKR") -> str:
    """
    Format a number as currency.
    
    Args:
        amount: The amount to format
        currency: Currency symbol (default: "PKR")
        
    Returns:
        Formatted currency string
    """
    return f"{currency} {amount:,.2f}"


def validate_email(email: str) -> bool:
    """
    Validate an email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def safe_divide(numerator: Union[int, float], denominator: Union[int, float], default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning a default if division by zero.
    
    Args:
        numerator: The numerator
        denominator: The denominator
        default: Default value if denominator is zero
        
    Returns:
        Result of division or default value
    """
    return numerator / denominator if denominator != 0 else default


def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def get_month_name(month: int) -> str:
    """
    Get month name from month number.
    
    Args:
        month: Month number (1-12)
        
    Returns:
        Month name
    """
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    return months[month - 1] if 1 <= month <= 12 else "Invalid"


def get_date_range(date_str: str) -> tuple:
    """
    Parse date string and return (start_date, end_date).
    
    Args:
        date_str: Date string in format "YYYY-MM-DD"
        
    Returns:
        Tuple of (date_object, date_object)
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return (date_obj, date_obj)
    except ValueError:
        return (None, None)
