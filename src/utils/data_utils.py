"""Data processing and validation utility functions"""

import pandas as pd


def is_empty_value(value):
    """Check if a value is empty or None
    
    Args:
        value: Value to check
        
    Returns:
        bool: True if value is empty, False otherwise
    """
    if value is None:
        return True
    if isinstance(value, float) and pd.isna(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    # Check if numeric value is 0
    try:
        num_val = float(value)
        if num_val == 0:
            return True
    except (ValueError, TypeError):
        pass
    return False


def filter_empty_values(data_dict, metric_names=None):
    """Remove entries with empty values from data dictionary
    
    Args:
        data_dict: Dictionary of metric names to values
        metric_names: Optional set of metric names to include (for column ordering)
        
    Returns:
        dict: Dictionary with empty values removed, preserving order
    """
    filtered_data = {}
    
    for key, value in data_dict.items():
        if not is_empty_value(value):
            filtered_data[key] = value
    
    return filtered_data


def parse_format_type(format_string):
    """Parse format type from Excel row 2 format string
    
    Recognizes special prefixes:
    - "zł" or "currency" or "PLN" -> currency format
    - "%" or "percent" -> percentage format
    - "number" or "num" -> standard number format
    - empty/other -> auto-detect based on context
    
    Args:
        format_string: Format string from Excel row 2
        
    Returns:
        dict: Format specification with 'type' and optional metadata
    """
    if not format_string or is_empty_value(format_string):
        return {'type': 'auto'}
    
    format_lower = str(format_string).lower().strip()
    
    # Currency formats
    if any(x in format_lower for x in ['zł', 'pln', 'currency', 'zl']):
        return {
            'type': 'currency',
            'symbol': 'zł',
            'decimal_places': 2,
            'thousands_separator': ' '
        }
    
    # Percentage formats
    if any(x in format_lower for x in ['%', 'percent', 'pct']):
        return {
            'type': 'percentage',
            'multiply_by_100': True,
            'decimal_places': 2
        }
    
    # Standard number
    if any(x in format_lower for x in ['number', 'num', 'numeric']):
        return {
            'type': 'number',
            'decimal_places': 2
        }
    
    # If it looks like Excel format code, preserve it as is for later parsing
    if any(x in format_lower for x in ['0', '#', '.', ',']):
        return {
            'type': 'excel_format',
            'format_code': format_string
        }
    
    return {
        'type': 'auto',
        'original_format': format_string
    }


def apply_format_to_value(value, format_spec):
    """Apply format specification to a value
    
    Args:
        value: The numeric value to format
        format_spec: Dictionary with format information from parse_format_type()
                    or from format dialog (can contain 'decimal_places' key)
        
    Returns:
        str: Formatted value as string
    """
    if is_empty_value(value):
        return ""
    
    try:
        value_num = float(value)
    except (ValueError, TypeError):
        return str(value)
    
    format_type = format_spec.get('type', 'auto')
    decimal_places = format_spec.get('decimal_places', 2)
    
    # Ensure decimal_places is an integer
    try:
        decimal_places = int(decimal_places)
    except (ValueError, TypeError):
        decimal_places = 2
    
    # Currency format
    if format_type == 'currency':
        symbol = format_spec.get('symbol', 'zł')
        sep = format_spec.get('thousands_separator', ' ')
        
        formatted = f"{value_num:,.{decimal_places}f}".replace(',', '|').replace('.', ',').replace('|', sep)
        return f"{formatted} {symbol}"
    
    # Percentage format
    elif format_type == 'percentage':
        if format_spec.get('multiply_by_100', False):
            value_num = value_num * 100
        
        if value_num == int(value_num) and decimal_places == 0:
            return f"{int(value_num)} %"
        return f"{value_num:.{decimal_places}f}".replace('.', ',') + " %"
    
    # Standard number
    elif format_type == 'number':
        return f"{value_num:,.{decimal_places}f}".replace(',', '|').replace('.', ',').replace('|', ' ')
    
    # Auto-detect or unknown
    else:
        return str(value)
