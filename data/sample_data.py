import pandas as pd

def load_regulations(filepath="data/regulations.csv"):
    """
    Load and clean maritime regulations data from a CSV file.

    The CSV file is expected to include columns such as:
    "ID", "Applicable?", "FULL_NAME", "HYPERLINK_SS", "NAME", "Organization", 
    "Impact", "Area", "Status", "In Effect", "Organization Type", "Applicable GT",
    "Base Year", "Hyperlink 1", "Hyperlink 2", "Contact Email", "Contact Phone",
    and various ship type columns (e.g., "RORO_SHIPS", "CONTAINER_SHIP", etc.).

    Parameters:
        filepath (str): Path to the CSV file containing regulations data.

    Returns:
        pd.DataFrame: A cleaned DataFrame with proper data types.
    """
    # Read CSV file into DataFrame
    df = pd.read_csv(filepath)
    
    # Convert 'Effective Date' to datetime
    if "Effective Date" in df.columns:
        df["Effective Date"] = pd.to_datetime(df["Effective Date"], errors="coerce")
    
    # Convert 'Applicable?' column to boolean (if present)
    if "Applicable?" in df.columns:
        df["Applicable?"] = df["Applicable?"].astype(str).str.strip().str.upper().map({"TRUE": True, "FALSE": False})
    
    # Convert columns that should be numeric (remove commas if necessary)
    numeric_cols = ["CO2 Limit (g/kWh)", "NOx Limit (g/kWh)", "Applicable GT", "Base Year"]
    for col in numeric_cols:
        if col in df.columns:
            # Remove commas and convert to numeric values, coercing errors to NaN
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    
    # (Optional) Further cleaning could be done for phone numbers, hyperlinks, etc.
    
    return df
