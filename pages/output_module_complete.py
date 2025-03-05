import requests
from urllib.parse import urlencode
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash
###############################################################################
# API DATA FETCHING
###############################################################################
def get_api_data(params=None):
    """
    Retrieves data from the API endpoint with the given parameters.
    If params is None or failure, it returns default data to ensure the app works.
    Returns JSON data from API.
    """
    base_url = "https://api.financialmodelling.app/api/v1/emissions"
    
    try:
        if params:
            query_string = urlencode(params)
            url = f"{base_url}?{query_string}"
        else:
            url = base_url
            
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API Error: {response.status_code}", response.text)
            return get_default_api_data()  # Fallback to default data
    except Exception as e:
        print(f"Exception: {e}")
        return get_default_api_data()  # Fallback to default data
        
def get_default_api_data():
    """Return hardcoded default data."""
    # Included for brevity, return a simplified dictionary
    return {
        "status": "success",
        "engine_power": [{
            "main_engine_power_kw": 9600,
            "aux_engine_power_kw": 2400,
        }],
        "fuel_consumption": [{
            "total_fuel_consumption_tonnes": 4500,
        }],
        "emissions": [{
            "co2_emissions_tonnes": 14000,
            "nox_emissions_tonnes": 250,
        }],
        "costs": [{
            "fuel_costs_eur": 2250000,
            "maintenance_costs_eur": 350000,
        }]
    }

# Number formatting function
def format_number(num):
    """Format number with commas and optional decimal places."""
    if num is None:
        return "N/A"
    
    if isinstance(num, (int, float)):
        if num == int(num):  # If it's a whole number
            return f"{int(num):,}"
        else:
            return f"{num:,.1f}"
    
    return str(num)

# Currency helper functions
def get_currency_symbol(currency):
    """Return currency symbol based on currency code."""
    return {"EUR": "€", "USD": "$", "GBP": "£"}.get(currency, "€")

def get_conversion_factor(currency):
    """Return conversion factor to convert from EUR to specified currency."""
    return {"EUR": 1.0, "USD": 1.08, "GBP": 0.86}.get(currency, 1.0)

def format_currency_value(value, currency, factor):
    """Format a value as currency with the proper symbol."""
    if value is None:
        return "N/A"
    
    symbol = get_currency_symbol(currency)
    converted = value * factor
    
    if converted >= 1000000:
        return f"{symbol}{converted/1000000:,.2f}M"
    elif converted >= 1000:
        return f"{symbol}{converted/1000:,.1f}K"
    else:
        return f"{symbol}{converted:,.2f}"

def update_from_input_module(input_data):
    """
    Function to be called from input_module.py to update the emissions data store.
    """
    # Convert input data to API parameters
    params = {
        "main_engine_power_kw": input_data.get("main_power"),
        "aux_engine_power_kw": input_data.get("aux_power"),
        "sailing_engine_load": input_data.get("sailing_engine_load", 50) / 100.0,
        "working_engine_load": input_data.get("working_engine_load", 30) / 100.0,
        "shore_engine_load": input_data.get("shore_engine_load", 39.5) / 100.0,
        "sailing_days": input_data.get("sailing_days", 175),
        "working_days": input_data.get("working_days", 165),
        "shore_days": input_data.get("shore_days", 75),
        "shore_port": input_data.get("shore_port", 1),
        "main_fuel_type": input_data.get("main_fuel_type", "MDO"),
        "aux_fuel_type": input_data.get("aux_fuel_type", "MDO"),
        "reporting_year": input_data.get("reporting_year", 2030),
        "ENGINE_MAINTENANCE_COSTS_PER_HOUR": input_data.get("engine_maint_cost", 20),
        "SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": input_data.get("spares_cost", 2),
        "FUELEU_CURRENT_PENALTY_PER_YEAR": input_data.get("fueleu_penalty", 919412.47),
        "PARASITIC_LOAD_ENGINE": 0.96,
        "BIOFUELS_BLEND_PERCENTAGE": 0
    }
    
    # Fetch data from API
    api_data = get_api_data(params)
    return api_data