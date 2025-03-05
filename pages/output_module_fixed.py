import requests
from urllib.parse import urlencode
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import dash

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
    from pages.output_module import get_api_data
    api_data = get_api_data(params)
    return api_data