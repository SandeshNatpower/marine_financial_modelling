# pages/output_module.py
import requests
from urllib.parse import urlencode
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from pages import api_functions

# Import API functions for module connection
get_api_data = api_functions.get_api_data
get_default_api_data = api_functions.get_default_api_data
update_from_input_module = api_functions.update_from_input_module

###############################################################################
# HELPER FUNCTIONS
###############################################################################
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