"""Excel file utility functions"""

import pandas as pd


def get_header_and_format_from_excel(file_path):
    """Extract column headers from Excel file
    
    Reads the first row (headers) from the Excel file.
    Creates a mapping of headers to themselves.
    Excludes PROMOTOR and EMAIL columns.
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        tuple: (header_to_metric dict, empty dict for compatibility)
            - header_to_metric: Maps column names to themselves
            - empty dict: For future use or compatibility with format dialogs
        
    Raises:
        Exception: If file cannot be read or is invalid
    """
    try:
        # Read only header row to get column names
        df = pd.read_excel(file_path, nrows=0)
        
        # Columns to exclude from metric mapping
        exclude_columns = {'PROMOTOR', 'EMAIL'}
        
        # Get headers from first row
        headers = df.columns.tolist()
        
        # Create mapping for headers (excluding PROMOTOR and EMAIL)
        header_to_metric = {col: col for col in headers if col not in exclude_columns}
        
        # Return empty format dict - formats will be selected via dialog
        return header_to_metric, {}
    except Exception as e:
        raise Exception(f"Nie można odczytać nagłówków z pliku Excel: {e}")


def get_header_to_metric_from_excel(file_path):
    """Extract column headers from Excel file and create header-to-metric mapping
    
    Reads the first row of the Excel file as column headers and creates a mapping
    where each column header maps to itself. Excludes PROMOTOR and EMAIL columns
    as they are handled separately.
    
    Args:
        file_path (str): Path to the Excel file
        
    Returns:
        dict: Mapping of column names to metric display names
        
    Raises:
        Exception: If file cannot be read or is invalid
    """
    try:
        header_to_metric, _ = get_header_and_format_from_excel(file_path)
        return header_to_metric
    except Exception as e:
        raise Exception(f"Nie można odczytać nagłówków z pliku Excel: {e}")
