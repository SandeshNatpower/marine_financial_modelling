import json
from dash import dash_table
import requests
from urllib.parse import urlencode
from datetime import datetime
import pandas as pd
from dash import html, Input, Output, State, callback_context, exceptions
from dash.dcc import send_data_frame
# callbacks.py
from pages import reporting
import io
import json
import smtplib
from email.message import EmailMessage
from dash import Input, Output, State, callback_context, no_update
from dash.dcc import send_bytes

#from reportlab.lib.pagesizes import A4
#from reportlab.pdfgen import canvas
import dash
from dash import html, dcc, Input, Output, State, no_update, callback_context
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import config
import plotly.graph_objects as go
import numpy as np
import pages
import pages.power_profiles
import pages.input_module
from pages.input_module import get_vessel_details, DEFAULT_VESSEL, DEFAULT_PLACES 
from pages.output_module import (
    get_current_output_table,
    get_future_output_table,
    get_opex_comparison_table,
    get_opex_comparison_table_year,
    get_emissions_comparison_table,
    get_emissions_comparison_table_year,
    get_carbon_footprint_table,
    get_vessel_summary_table,
    dashboard_layout,
    get_country_visits_table,
    cashflow_figure,
    min_future_opex_figure,
    maintenance_cost_figure,
    penalty_cost_figure,
    spares_figure,
    opex_cost_figure,
    fuel_consumption_figure,
)
import pages.reporting

###############################################################################
# GLOBAL STYLES & CONSTANTS
###############################################################################
HEADER_STYLE = {"backgroundColor": "#0A4B8C", "padding": "10px"}
HEADER_TEXT_STYLE = {"color": "white", "margin": "0"}
MARGIN_STYLE = dict(l=60, r=30, t=60, b=50)
TEMPLATE_STYLE = "plotly_white"

def card_component(title, children):
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H4(title, className="card-title mb-0", style=HEADER_TEXT_STYLE),
                style=HEADER_STYLE,
            ),
            dbc.CardBody(children),
        ],
        className="mb-4 shadow-sm rounded",
    )

###############################################################################
# HELPER FUNCTIONS
###############################################################################
def merge_vessel_data(vessel_data):
    merged = DEFAULT_VESSEL.copy()
    if vessel_data:
        merged.update(vessel_data)
    return merged

def build_api_url(params, endpoint):
    qs = urlencode(params, doseq=True)
    url = f"{endpoint}?{qs}"
    print(f"Final API URL: {url}")
    return url

# -------------------------------------------------------------------------------
# Dashboard Scenarios:
# -------------------------------------------------------------------------------
def process_scenario_value(scenario_value, default="Diesel-Bio-diesel"):
    """Process the scenario fuel values into a comma-separated list."""
    if not scenario_value:
        return [default]
    if isinstance(scenario_value, str):
        return [s.strip() for s in scenario_value.split(',') if s.strip()]
    elif isinstance(scenario_value, list):
        # Ensure all elements are strings and flatten any nested lists
        return [str(item).strip() for sublist in scenario_value for item in (sublist if isinstance(sublist, list) else [sublist])]
    return [default]

# -------------------------------------------------------------------------------
# Dashboard Scenarios:
# -------------------------------------------------------------------------------
def fetch_dashboard_scenarios(vessel_data, future_data):
    vessel_data = merge_vessel_data(vessel_data)
    future_data = future_data or {}
    
    params = {
        "vessel_id": vessel_data.get("vessel_id", 11111),
        "main_engine_power_kw": float(vessel_data.get("total_engine_power", 10400)),
        "aux_engine_power_kw": float(vessel_data.get("average_hoteling_kw", 2246)),
        "sailing_engine_load": float(vessel_data.get("sailing_engine_load", 50))/100,
        "working_engine_load": float(vessel_data.get("working_engine_load", 30))/100,
        "shore_engine_load": float(vessel_data.get("shore_engine_load", 40))/100,
        "sailing_days": float(vessel_data.get("sailing_days", 0.1)),
        "working_days": float(vessel_data.get("working_days", 0.1)),
        "idle_days": int(vessel_data.get("idle_days", 126)),
        "shore_days": int(vessel_data.get("shore_days", 0)),
        "shore_port": int(vessel_data.get("shore_port", 2)),
        "main_fuel_type": vessel_data.get("main_fuel_type", "MDO"),
        "aux_fuel_type": vessel_data.get("aux_fuel_type", "MDO"),
        "future_main_fuel_type": future_data.get("future-main-fuel-type", "Diesel-Bio-diesel"),
        "future_aux_fuel_type": future_data.get("future-aux-fuel-type", "Diesel-Bio-diesel"),
        "reporting_year": int(vessel_data.get("reporting_year", 2030)),
        "ENGINE_MAINTENANCE_COSTS_PER_HOUR": float(vessel_data.get("ENGINE_MAINTENANCE_COSTS_PER_HOUR", 480)),
        "SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": float(vessel_data.get("SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR", 2)),
        "SHORE_POWER_MAINTENANCE_PER_DAY": float(vessel_data.get("SHORE_POWER_MAINTENANCE_PER_DAY", 480)),
        "SHORE_POWER_SPARES_PER_DAY": float(vessel_data.get("SHORE_POWER_SPARES_PER_DAY", 480)),
        "BIOFUELS_SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": float(future_data.get("biofuels-spares-cost", 3)),
        "PARASITIC_LOAD_ENGINE": float(future_data.get("parasitic-load", 95)/100),
        "BIOFUELS_BLEND_PERCENTAGE": float(future_data.get("biofuels-blend", 30)/100),
        "shore_enable": str(vessel_data.get("shore_enable", False)).lower(),
        "inflation_rate": float(future_data.get("inflation-rate", 2))/100,
        "npv_rate": float(future_data.get("npv-rate", 0)),
        "CAPEX": float(vessel_data.get("CAPEX", 19772750)),
        "MAIN_ENGINE_SPEED": vessel_data.get("MAIN_ENGINE_SPEED", "MEDIUM"),
        "MAIN_ENGINE_TYPE": vessel_data.get("MAIN_ENGINE_TYPE", "4-STROKE"),
        "AUX_ENGINE_SPEED": vessel_data.get("AUX_ENGINE_SPEED", "MEDIUM"),
        "AUX_ENGINE_TYPE": vessel_data.get("AUX_ENGINE_TYPE", "4-STROKE"),
        "price_conversion": float(vessel_data.get("price_conversion", 1)),
    }
    qs = urlencode(params, doseq=True)
    url = f"{config.DASHBOARD_ENDPOINT}?{qs}"
    print(f"Dashboard API URL: {url}")
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Dashboard API Error: {str(e)}")
        return {}

# -------------------------------------------------------------------------------
# Financial Data: Using your first API (penalty parameters removed, scenario omitted)
# -------------------------------------------------------------------------------
def get_financial_data(input_params=None, vessel_data_override=None):
    fallback_defaults = {
        "vessel_id": 48217,
        "main_engine_power_kw": 10400,
        "aux_engine_power_kw": 2246,
        "sailing_engine_load": 0.5,
        "working_engine_load": 0.3,
        "shore_engine_load": 0.395,
        "sailing_days": 199,
        "working_days": 40,
        "idle_days": 126,
        "shore_days": 0,
        "shore_port": 2,
        "main_fuel_type": "MDO",
        "aux_fuel_type": "MDO",
        "future_main_fuel_type": "Diesel-Bio-diesel",
        "future_aux_fuel_type": "Diesel-Bio-diesel",
        "BIOFUELS_SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": 3,
        "PARASITIC_LOAD_ENGINE": 0.95,
        "BIOFUELS_BLEND_PERCENTAGE": 0.3,
        "reporting_year": 2030,
        "ENGINE_MAINTENANCE_COSTS_PER_HOUR": 20,
        "SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": 2,
        "SHORE_POWER_MAINTENANCE_PER_DAY": 480.0,
        "SHORE_POWER_SPARES_PER_DAY": 480.0,
        "shore_enable": "false",
        "inflation_rate": 0.02,
        "npv_rate": 0,
        "CAPEX": 19772750,
        "MAIN_ENGINE_SPEED": "MEDIUM",
        "MAIN_ENGINE_TYPE": "4-Stroke",
        "AUX_ENGINE_SPEED": "MEDIUM",
        "AUX_ENGINE_TYPE": "4-Stroke",
        "price_conversion": 1
    }
    vessel_data = merge_vessel_data(vessel_data_override)
    vessel_overrides = {
        "vessel_id": vessel_data.get("vessel_id", fallback_defaults["vessel_id"]),
        "main_engine_power_kw": vessel_data.get("total_engine_power", fallback_defaults["main_engine_power_kw"]),
        "aux_engine_power_kw": vessel_data.get("average_hoteling_kw", fallback_defaults["aux_engine_power_kw"]),
        "main_fuel_type": vessel_data.get("main_fuel_type", fallback_defaults["main_fuel_type"]),
        "aux_fuel_type": vessel_data.get("aux_fuel_type", fallback_defaults["aux_fuel_type"]),
        "reporting_year": vessel_data.get("reporting_year", fallback_defaults["reporting_year"]),
    }
    final_params = fallback_defaults.copy()
    final_params.update(vessel_overrides)
    if input_params:
        final_params.update(input_params)
    
    final_params["shore_enable"] = str(final_params.get("shore_enable", False)).lower()
    
    if input_params and "biofuels_blend" in input_params:
        try:
            blend_value = float(input_params["biofuels_blend"])
            final_params["BIOFUELS_BLEND_PERCENTAGE"] = (blend_value / 100.0 if blend_value  else 0.3)
        except ValueError:
            raise ValueError("Invalid biofuels blend percentage provided.")
    else:
        final_params["BIOFUELS_BLEND_PERCENTAGE"] = float(final_params.get("BIOFUELS_BLEND_PERCENTAGE", 0.3))
    
    if final_params["BIOFUELS_BLEND_PERCENTAGE"] > 100:
        raise ValueError("Biofuel blend percentage cannot exceed 100%")
    
    for key in ["sailing_days", "working_days", "idle_days"]:
        if final_params.get(key, 0) < 0:
            raise ValueError(f"{key} cannot be negative")
    
    qs = urlencode(final_params, doseq=True)
    url = f"{config.FINANCIAL_ENDPOINT}?{qs}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Financial API Error: {str(e)}")
        return {}

# -------------------------------------------------------------------------------
# Future Inputs Update Callback
# -------------------------------------------------------------------------------
def update_future_inputs_callback(vessel_data, future_data):
    from pages.input_module import (
        DEFAULT_FUTURE_MAIN_FUEL_TYPE,
        DEFAULT_FUTURE_AUX_FUEL_TYPE,
        DEFAULT_BIOFUELS_SPARES_COST,
        DEFAULT_PARASITIC_LOAD,
        DEFAULT_BIOFUELS_BLEND,
        DEFAULT_SHORE_MAINT_COST,
        DEFAULT_SHORE_SPARES_COST,
        DEFAULT_INFLATION_RATE,
        DEFAULT_NPV_RATE,
        DEFAULT_CURRENCY,
    )
    vessel_data = merge_vessel_data(vessel_data)
    future_data = future_data or {}
    return (
        future_data.get("future-main-fuel-type", vessel_data.get("future-main-fuel-type", DEFAULT_FUTURE_MAIN_FUEL_TYPE)),
        future_data.get("future-aux-fuel-type", vessel_data.get("future-aux-fuel-type", DEFAULT_FUTURE_AUX_FUEL_TYPE)),
        float(future_data.get("biofuels-spares-cost", vessel_data.get("biofuels-spares-cost", DEFAULT_BIOFUELS_SPARES_COST))),
        float(future_data.get("parasitic-load", vessel_data.get("parasitic-load", DEFAULT_PARASITIC_LOAD))),
        float(future_data.get("biofuels-blend", vessel_data.get("biofuels-blend", DEFAULT_BIOFUELS_BLEND))),
        float(future_data.get("shore-maint-cost", vessel_data.get("shore-maint-cost", DEFAULT_SHORE_MAINT_COST))),
        float(future_data.get("shore-spares-cost", vessel_data.get("shore-spares-cost", DEFAULT_SHORE_SPARES_COST))),
        float(future_data.get("inflation-rate", vessel_data.get("inflation-rate", DEFAULT_INFLATION_RATE))),
        float(future_data.get("npv-rate", vessel_data.get("npv-rate", DEFAULT_NPV_RATE))),
        future_data.get("currency-choice", vessel_data.get("currency-choice", DEFAULT_CURRENCY))
    )

# -------------------------------------------------------------------------------
# REGISTER CALLBACKS
# -------------------------------------------------------------------------------
def register_callbacks(app):
    """Register all Dash callbacks."""
    
    @app.callback(
        [Output('vessel-data-store', 'data'),
         Output('search-results', 'children')],
        Input('search-button', 'n_clicks'),
        [State('search-type', 'value'),
         State('search-term', 'value'),
         State('vessel-data-store', 'data')],
        prevent_initial_call=True
    )
    def search_vessel_callback(n_clicks, search_type, search_term, current_data):
        if not search_term:
            return current_data or config.DEFAULT_VESSEL, "Please enter a search term."

        try:
            vessel_data, places_summary = get_vessel_details(search_term, search_type)

            # Ensure vessel_data is not empty and is a dictionary
            if isinstance(vessel_data, list) and vessel_data:
                vessel_data = vessel_data[0]  # Extract first vessel if it's a list
            
            if not isinstance(vessel_data, dict):
                vessel_data = config.DEFAULT_VESSEL  # Fallback to default if invalid
                places_summary = config.DEFAULT_PLACES
                return vessel_data, "No vessel found with those search criteria."
            
            # Store places_summary inside vessel_data dictionary for easier data handling
            vessel_data['places_summary'] = places_summary
            
            return vessel_data, f"Found vessel: {vessel_data.get('vessel_name', 'Unknown')}"
            
        except Exception as e:
            print(f"Error in search: {str(e)}")
            return current_data or config.DEFAULT_VESSEL, f"Error searching: {str(e)}"

    @app.callback(
        [Output('vessel-name', 'value'),
         Output('imo-number', 'value'),
         Output('vessel-category', 'value'),
         Output('gross-tonnage', 'value'),
         Output('year-built', 'value'),
         Output('dwt', 'value')],
        Input('vessel-data-store', 'data'),
        prevent_initial_call=True
    )
    def update_vessel_fields_callback(vessel_data):
        vessel_data = vessel_data or config.DEFAULT_VESSEL
        return (
            vessel_data.get('vessel_name', config.DEFAULT_VESSEL["vessel_name"]),
            vessel_data.get('imo', config.DEFAULT_VESSEL["imo"]),
            vessel_data.get('new_vessel_category', config.DEFAULT_VESSEL["vessel_category"]),
            vessel_data.get('gross_tonnage', config.DEFAULT_VESSEL["gross_tonnage"]),
            vessel_data.get('build', config.DEFAULT_VESSEL["build"]),
            vessel_data.get('dwt', config.DEFAULT_VESSEL["dwt"])
        )
    
    @app.callback(
        [Output('main-power', 'value'),
         Output('aux-power', 'value'),
         Output('main-engine-type', 'value'),
         Output('aux-engine-type', 'value'),
         Output('main-fuel-type', 'value'),
         Output('aux-fuel-type', 'value')],
        Input('vessel-data-store', 'data'),
        prevent_initial_call=True
    )
    def update_technical_specs(vessel_data):
        vessel_data = vessel_data or config.DEFAULT_VESSEL
        main_power = vessel_data.get("total_engine_power", config.DEFAULT_VESSEL.get("total_engine_power", 10400))
        aux_power = vessel_data.get("average_hoteling_kw", config.DEFAULT_VESSEL.get("average_hoteling_kw", 2246))
        return (
            main_power,
            aux_power,
            vessel_data.get("main_engine_type", "4-STROKE"),
            vessel_data.get("aux_engine_type", "4-STROKE"),
            vessel_data.get("main_fuel_type", "MDO"),
            vessel_data.get("aux_fuel_type", "MDO")
        )

    # --- Persist user edits back into the store ---
    @app.callback(
        Output('vessel-data-store', 'data', allow_duplicate=True),
        [
            # Vessel info fields
            Input('vessel-name', 'value'),
            Input('imo-number', 'value'),
            Input('vessel-category', 'value'),
            Input('gross-tonnage', 'value'),
            Input('year-built', 'value'),
            Input('dwt', 'value'),
            # Technical specs fields
            Input('main-power', 'value'),
            Input('aux-power', 'value'),
            Input('main-engine-type', 'value'),
            Input('aux-engine-type', 'value'),
            Input('main-fuel-type', 'value'),
            Input('aux-fuel-type', 'value'),
        ],
        State('vessel-data-store', 'data'),
        prevent_initial_call=True
    )
    def persist_vessel_edits(
        name, imo, category, gt, build, dwt,
        main_power, aux_power, main_eng_type, aux_eng_type, main_fuel, aux_fuel,
        current_data
    ):
        # Prevent loops: only run when a field changed
        triggered = callback_context.triggered[0]['prop_id']
        if 'vessel-data-store.data' in triggered:
            return dash.no_update

        # Copy existing data
        data = (current_data or config.DEFAULT_VESSEL).copy()

        # Merge vessel info edits
        data.update({
            'vessel_name': name,
            'imo': imo,
            'new_vessel_category': category,
            'gross_tonnage': gt,
            'build': build,
            'dwt': dwt,
        })

        # Merge technical specs edits
        data.update({
            'total_engine_power': main_power,
            'average_hoteling_kw': aux_power,
            'main_engine_type': main_eng_type,
            'aux_engine_type': aux_eng_type,
            'main_fuel_type': main_fuel,
            'aux_fuel_type': aux_fuel,
        })

        return data

    @app.callback(
        Output('places-summary-table-container', 'children'),
        Input('vessel-data-store', 'data'),
        prevent_initial_call=True
    )
    def update_places_summary_table(vessel_data):
        if not vessel_data:
            return [html.Div("No vessel data available")]
        
        from pages.input_module import get_places_summary_table
        places_summary_table = get_places_summary_table(vessel_data)
        return [places_summary_table]
    
    @app.callback(
        [Output('vessel-image', 'src'),
         Output('vessel-type-display', 'children')],
        Input('vessel-category', 'value'),
        prevent_initial_call=True
    )
    def update_vessel_image(vessel_category):
        if not vessel_category:
            return '/assets/default_vessel.png', "No vessel selected"
        if isinstance(vessel_category, dict):
            vessel_category = vessel_category.get('value', '')
        from pages.input_module import get_vessel_image_path
        image_filename = get_vessel_image_path(vessel_category)
        image_path = f'/assets/{image_filename}'
        vessel_type_display = html.Div([
            html.Strong("Vessel Type: "),
            html.Span(vessel_category)
        ])
        return image_path, vessel_type_display
    
    @app.callback(
        [Output('sailing-days', 'value'),
         Output('working-days', 'value'),
         Output('idle-days', 'value'),
         Output('shore-days', 'value'),
         Output('sailing-engine-load', 'value'),
         Output('working-engine-load', 'value'),
         Output('shore-engine-load', 'value'),
         Output('engine-maint-cost', 'value'),
         Output('spares-cost', 'value')],
        Input('vessel-data-store', 'data'),
        prevent_initial_call=True
    )
    def update_operational_and_maintenance_inputs(vessel_data):
        from pages.input_module import DEFAULT_VESSEL
        if not vessel_data:
            vessel_data = DEFAULT_VESSEL
        else:
            vessel_data = {**DEFAULT_VESSEL, **vessel_data}
        return (
            vessel_data.get('sailing_days', 199),
            vessel_data.get('working_days', 40),
            vessel_data.get('idle_days', 126),
            vessel_data.get('shore_days', 0),
            vessel_data.get('sailing_engine_load', 0.5),
            vessel_data.get('working_engine_load', 0.3),
            vessel_data.get('shore_engine_load', 0.395),
            vessel_data.get('ENGINE_MAINTENANCE_COSTS_PER_HOUR', 20),
            vessel_data.get('SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR', 2)
        )
    
    @app.callback(
        [Output('future-main-fuel-type', 'value'),
         Output('future-aux-fuel-type', 'value'),
         Output('biofuels-spares-cost', 'value'),
         Output('parasitic-load', 'value'),
         Output('biofuels-blend', 'value'),
         Output('shore-maint-cost', 'value'),
         Output('shore-spares-cost', 'value'),
         Output('inflation-rate', 'value'),
         Output('npv-rate', 'value'),
         Output('currency-choice', 'value')],
        [Input('vessel-data-store', 'data'),
         Input('future-data-store', 'data')],
        prevent_initial_call=True
    )
    def update_future_inputs(vessel_data, future_data):
        return update_future_inputs_callback(vessel_data, future_data)
    
    @app.callback(
        Output('dashboard-scenarios-store', 'data'),
        Input('calculate-scenarios-btn', 'n_clicks'),
        [
            State('scenario-filter-global', 'value'),         # User-selected scenario list
            State('vessel-data-store', 'data'),
            State('future-data-store', 'data')
        ],
        prevent_initial_call=True
    )
    def calculate_scenarios(n_clicks, selected_scenarios, vessel_data, future_data):
        if not n_clicks:
            raise PreventUpdate



        # Use the selected scenarios from the dropdown
        scenario_list = selected_scenarios or []
        
        # Process vessel and future data (make sure merge_vessel_data is defined)
        vessel_data = merge_vessel_data(vessel_data)
        future_data = future_data or {}

        main_power = vessel_data.get("total_engine_power", 10400)
        aux_power = vessel_data.get("average_hoteling_kw", 2246)
        main_fuel_type = vessel_data.get("main_fuel_type", "MDO")
        aux_fuel_type = vessel_data.get("aux_fuel_type", "MDO")
        sailing_days = vessel_data.get("sailing_days", 199)
        working_days = vessel_data.get("working_days", 40)
        idle_days = vessel_data.get("idle_days", 126)
        shore_days = vessel_data.get("shore_days", 0)
        sailing_engine_load = vessel_data.get("sailing_engine_load", 50)
        engine_maint_cost = vessel_data.get("ENGINE_MAINTENANCE_COSTS_PER_HOUR", 20)
        spares_cost = vessel_data.get("SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR", 2)
        shore_enable = vessel_data.get("shore_enable", False)
        shore_port = vessel_data.get("shore_port", 2)
        reporting_year = vessel_data.get("reporting_year", 2030)
        capex = vessel_data.get("CAPEX", 19772750)
        main_engine_speed = vessel_data.get("MAIN_ENGINE_SPEED", "MEDIUM")
        main_engine_type = vessel_data.get("MAIN_ENGINE_TYPE", "4-STROKE")
        aux_engine_speed = vessel_data.get("AUX_ENGINE_SPEED", "MEDIUM")
        aux_engine_type = vessel_data.get("AUX_ENGINE_TYPE", "4-STROKE")

        biofuels_spares_cost = future_data.get("biofuels-spares-cost", 3)
        parasitic_load = future_data.get("parasitic-load", 95)
        biofuels_blend = future_data.get("biofuels-blend", 30)
        shore_maint_cost = future_data.get("shore-maint-cost", 480)
        shore_spares_cost = future_data.get("shore-spares-cost", 480)
        inflation_rate = future_data.get("inflation-rate", 2)
        npv_rate = future_data.get("npv-rate", 0)
        currency_choice = future_data.get("currency-choice", "EUR")

        shore_enable_bool = str(shore_enable).strip().lower() in ["yes", "true"]
        price_conversion = config.CURRENCIES.get(currency_choice, {}).get("conversion", 1)

        try:
            blend_value = float(biofuels_blend)
        except (ValueError, TypeError):
            raise ValueError("Invalid biofuels blend percentage provided.")
        if blend_value > 1:
            blend_value /= 100.0

        # Build the parameters for the API call.
        # Notice that we pass the user-selected scenarios as a list.
        params = {
            "vessel_id": vessel_data.get("vessel_id", 48217),
            "main_engine_power_kw": float(main_power),
            "aux_engine_power_kw": float(aux_power),
            "sailing_engine_load": float(sailing_engine_load) / 100,
            "working_days": float(working_days),
            "idle_days": int(idle_days),
            "shore_days": int(shore_days),
            "shore_port": int(shore_port),
            "main_fuel_type": main_fuel_type,
            "aux_fuel_type": aux_fuel_type,
            "BIOFUELS_BLEND_PERCENTAGE": blend_value,
            "reporting_year": int(reporting_year),
            "ENGINE_MAINTENANCE_COSTS_PER_HOUR": float(engine_maint_cost),
            "SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": float(spares_cost),
            "SHORE_POWER_MAINTENANCE_PER_DAY": float(shore_maint_cost),
            "SHORE_POWER_SPARES_PER_DAY": float(shore_spares_cost),
            "BIOFUELS_SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": float(biofuels_spares_cost),
            "PARASITIC_LOAD_ENGINE": float(parasitic_load) / 100 if parasitic_load else 0.95,
            "shore_enable": str(shore_enable_bool).lower(),
            "inflation_rate": float(inflation_rate) / 100 if inflation_rate else 0.02,
            "npv_rate": float(npv_rate) / 100.0,
            "CAPEX": float(capex),
            "MAIN_ENGINE_SPEED": main_engine_speed,
            "MAIN_ENGINE_TYPE": main_engine_type,
            "AUX_ENGINE_SPEED": aux_engine_speed,
            "AUX_ENGINE_TYPE": aux_engine_type,
            "price_conversion": price_conversion,
            "scenario_future_aux_fuel": ",".join(scenario_list) if scenario_list else "Diesel-Bio-diesel",
        }

        qs = urlencode(params, doseq=True)
        url = f"{config.DASHBOARD_ENDPOINT}?{qs}"
        print(f"Final Financial API URL: {url}")
        try:
            response = requests.get(config.DASHBOARD_ENDPOINT, params=params, timeout=60)
            response.raise_for_status()
            scenarios_data_response = response.json()
            print("Dashboard Scenarios API Call Successful")
            # This API response is assumed to contain only the selected scenarios.
            return scenarios_data_response
        except Exception as e:
            print(f"Scenario API Error: {str(e)}")
            return dash.no_update

        
    @app.callback(
        [Output("dashboard-scenario-dropdown", "options"),
         Output("dashboard-scenario-dropdown", "value")],
        [Input("dashboard-scenarios-store", "data"),
         Input("scenario-filter", "value")]
    )
    def update_dashboard_scenario_dropdown(dashboard_data, selected_scenarios):
        if not callback_context.triggered:
            raise PreventUpdate
        triggered_id = callback_context.triggered[0]['prop_id'].split('.')[0]
        if triggered_id == "dashboard-scenarios-store":
            if not dashboard_data:
                raise PreventUpdate
            scenario_options = [{"label": k, "value": k} for k in dashboard_data.keys()]
            default_value = scenario_options[2]["value"] if scenario_options else None
            return scenario_options, default_value
        elif triggered_id == "scenario-filter":
            if not selected_scenarios or len(selected_scenarios) == 0:
                raise PreventUpdate
            scenario_options = [{"label": scenario, "value": scenario} for scenario in selected_scenarios]
            default_value = selected_scenarios[2] if selected_scenarios else None
            return scenario_options, default_value
        raise PreventUpdate

    
    @app.callback(
        [Output('api-data-store', 'data'),
        Output('tab-switch', 'data'),
        Output('future-data-store', 'data')],
        Input('calculate-button', 'n_clicks'),
        [
            State('main-power', 'value'),
            State('aux-power', 'value'),
            State('main-fuel-type', 'value'),
            State('aux-fuel-type', 'value'),
            State('sailing-days', 'value'),
            State('working-days', 'value'),
            State('idle-days', 'value'),
            State('shore-days', 'value'),
            State('sailing-engine-load', 'value'),
            State('working-engine-load', 'value'),
            State('shore-engine-load', 'value'),
            State('engine-maint-cost', 'value'),
            State('spares-cost', 'value'),
            State('future-main-fuel-type', 'value'),
            State('future-aux-fuel-type', 'value'),
            State('biofuels-spares-cost', 'value'),
            State('parasitic-load', 'value'),
            State('biofuels-blend', 'value'),
            State('shore-maint-cost', 'value'),
            State('shore-spares-cost', 'value'),
            State('shore-enable', 'value'),
            State('npv-rate', 'value'),
            State('capex', 'value'),
            State('shore-port', 'value'),
            State('reporting-year', 'value'),
            State('inflation-rate', 'value'),
            State('main-engine-speed', 'value'),
            State('main-engine-type', 'value'),
            State('aux-engine-speed', 'value'),
            State('aux-engine-type', 'value'),
            State('vessel-data-store', 'data'),
            State('future-data-store', 'data'),
            State('currency-choice', 'value')
        ],
        prevent_initial_call=True
    )
    def update_financial_data(n_clicks, *values):
        if n_clicks is None:
            return no_update, "input", no_update
        
        (
            main_power, aux_power, main_fuel_type, aux_fuel_type, 
            sailing_days, working_days, idle_days, shore_days,
            sailing_engine_load, working_engine_load, shore_engine_load,
            engine_maint_cost, spares_cost,
            future_main_fuel_type, future_aux_fuel_type, biofuels_spares_cost,
            parasitic_load, biofuels_blend,
            shore_maint_cost, shore_spares_cost, shore_enable, npv_rate, capex,
            shore_port, reporting_year, inflation_rate,
            main_engine_speed, main_engine_type,
            aux_engine_speed, aux_engine_type, vessel_data,
            existing_future_data, currency_choice
        ) = values
        
        if not all([main_power, aux_power, main_fuel_type, aux_fuel_type]):
            return no_update, "input", no_update
        
        new_future_data = {
            "future-main-fuel-type": future_main_fuel_type,
            "future-aux-fuel-type": future_aux_fuel_type,
            "biofuels-spares-cost": biofuels_spares_cost,
            "parasitic-load": parasitic_load,
            "biofuels-blend": biofuels_blend,
            "shore-maint-cost": shore_maint_cost,
            "shore-spares-cost": shore_spares_cost,
            "inflation-rate": inflation_rate,
            "npv-rate": npv_rate,
            "currency-choice": currency_choice,
            "shore-enable": shore_enable,
            "capex": capex
        }
        updated_future_data = {**(existing_future_data or {}), **new_future_data}
        
        shore_enable_bool = str(shore_enable).strip().lower() in ["yes", "true"]
        price_conversion = config.CURRENCIES.get(currency_choice, {}).get("conversion", 1)
        
        try:
            blend_value = float(biofuels_blend)
        except ValueError:
            raise ValueError("Invalid biofuels blend percentage provided.")
        if blend_value > 1:
            blend_value /= 100.0
        
        params = {
            "vessel_id": vessel_data.get("vessel_id", 48217),
            "main_engine_power_kw": float(main_power),
            "aux_engine_power_kw": float(aux_power),
            "main_fuel_type": main_fuel_type,
            "aux_fuel_type": aux_fuel_type,
            "future_main_fuel_type": future_main_fuel_type,
            "future_aux_fuel_type": future_aux_fuel_type,
            "sailing_days": int(sailing_days),
            "working_days": int(working_days),
            "idle_days": int(idle_days),
            "shore_days": int(shore_days),
            "shore_port": int(shore_port),
            "sailing_engine_load": float(sailing_engine_load)/100 if sailing_engine_load else 0.5,
            "working_engine_load": float(working_engine_load)/100 if working_engine_load else 0.3,
            "shore_engine_load": float(shore_engine_load)/100 if shore_engine_load else 0.4,
            "reporting_year": int(reporting_year),
            "ENGINE_MAINTENANCE_COSTS_PER_HOUR": float(engine_maint_cost),
            "SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": float(spares_cost),
            "SHORE_POWER_MAINTENANCE_PER_DAY": float(shore_maint_cost),
            "SHORE_POWER_SPARES_PER_DAY": float(shore_spares_cost),
            "BIOFUELS_SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": float(biofuels_spares_cost),
            "PARASITIC_LOAD_ENGINE": float(parasitic_load)/100 if parasitic_load else 0.95,
            "BIOFUELS_BLEND_PERCENTAGE": blend_value,
            "shore_enable": shore_enable_bool,
            "inflation_rate": float(inflation_rate)/100 if inflation_rate else 0.02,
            "npv_rate": float(npv_rate) / 100.0,
            "CAPEX": float(capex),
            "MAIN_ENGINE_SPEED": main_engine_speed,
            "MAIN_ENGINE_TYPE": main_engine_type,
            "AUX_ENGINE_SPEED": aux_engine_speed,
            "AUX_ENGINE_TYPE": aux_engine_type,
            "price_conversion": price_conversion,
        }
        
        if params["BIOFUELS_BLEND_PERCENTAGE"] > 1:
            raise ValueError("Biofuel blend percentage cannot exceed 100%")
        for key in ["sailing_days", "working_days", "idle_days"]:
            if params[key] < 0:
                raise ValueError(f"{key} cannot be negative")
        
        qs = urlencode(params, doseq=True)
        url = f"{config.FINANCIAL_ENDPOINT}?{qs}"
        print(f"Final Financial API URL: {url}")
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            financial_data = response.json()
            print("Financial API Call Successful")
        except Exception as e:
            print(f"Financial API Error: {str(e)}")
            financial_data = None
        
        return financial_data, "output", updated_future_data
    

    @app.callback(
        [Output("scenario-filter", "options"),
         Output("scenario-filter", "value")],
        [Input("dashboard-scenarios-store", "data")]
    )
    def update_scenario_filter(dashboard_data):
        if not dashboard_data:
            return [], []
        scenarios = list(dashboard_data.keys())
        options = [{"label": sc, "value": sc} for sc in scenarios]
        default_value = scenarios[:] if len(scenarios) >= 2 else scenarios
        return options, default_value

    @app.callback(
        [Output("min-future-opex", "figure"),
        Output("financial-pie-chart", "figure")],
        [
            Input("dashboard-scenarios-store", "data"),
            Input("scenario-filter", "value"),             # <<--- scenario filter
        ]
    )
    def update_financial_metrics(dashboard_data, selected_scenarios):
        if not dashboard_data or not selected_scenarios:
            no_data_fig = go.Figure().update_layout(title="No scenarios selected")
            return no_data_fig, no_data_fig

        filtered_data = {k: v for k, v in dashboard_data.items() if k in selected_scenarios}
        min_future_opex_fig = pages.power_profiles.min_future_opex_figure(filtered_data)
        financial_pie_fig = pages.power_profiles.dwelling_at_berth_pie_figure(filtered_data, selected_scenarios)
        return min_future_opex_fig, financial_pie_fig


    @app.callback(
        Output("single-year-breakdown", "figure"),
        [
            Input("single-year-dropdown", "value"),
            Input("dashboard-year-range-slider", "value"),      # <-- range slider in
            Input("dashboard-scenarios-store", "data"),
            Input("scenario-filter", "value")
        ]
    )
    def update_single_year_breakdown(single_year, year_range, dashboard_data, selected_scenarios):
        # guard
        if not dashboard_data or not selected_scenarios:
            return go.Figure().update_layout(title="No scenarios selected")

        filtered_data = {
            k: v for k, v in dashboard_data.items()
            if k in selected_scenarios
        }

        # If user wants "all", draw the full-range stacked bar
        if single_year == "all":
            return pages.power_profiles.create_range_stacked_bar(
                filtered_data,
                year_range=tuple(year_range)
            )

        # Otherwise parse a single year
        try:
            yr = int(single_year)
        except (ValueError, TypeError):
            return go.Figure().update_layout(title="Invalid year selected")

        # stack only that year (as a degenerate range)
        return pages.power_profiles.create_range_stacked_bar(
            filtered_data,
            year_range=(yr, yr)
        )



    @app.callback(
        Output("metric-comparison-chart", "figure"),
        [
            Input("metric-dropdown",    "value"),
            Input("year-range-slider",  "value"),
            Input("scenario-filter",    "value"),
            Input("dashboard-scenarios-store", "data"),
        ]
    )
    def update_metric_comparison(metric, year_range, selected_scenarios, dashboard_data):
        if not dashboard_data or not selected_scenarios:
            return go.Figure().update_layout(title="No data to display")

        # Filter only the selected scenarios
        filtered_data = {
            name: data
            for name, data in dashboard_data.items()
            if name in selected_scenarios
        }

        # Call without data_view
        fig = pages.power_profiles.generate_metric_figure(
            metric,
            year_range,
            selected_scenarios,
            filtered_data
        )
        return fig


    
    @app.callback(
        Output("debug-dashboard-data", "children"),
        Input("dashboard-scenarios-store", "data")
    )
    def debug_dashboard_data(dashboard_data):
        if dashboard_data is None:
            return "No dashboard data available."
        try:
            return json.dumps(dashboard_data, indent=2)
        except Exception as e:
            return f"Error formatting dashboard data: {e}"
    

        
    @app.callback(
        Output("dashboard-charts-container", "children"),
        [
            Input("dashboard-chart-selector",    "value"),
            Input("dashboard-metric-dropdown",   "value"),
            Input("dashboard-year-range-slider", "value"),
            Input("dashboard-scenarios-store",   "data"),
            Input("single-year-dropdown",        "value"),
            Input("scenario-filter",             "value"),
        ]
    )
    def update_dashboard_charts(
        selected_charts,
        selected_metric,
        year_range,
        dashboard_data,
        single_year,
        selected_scenarios
    ):
        # Guards
        if not dashboard_data:
            return html.Div("No data available. Please calculate scenarios first.",
                            className="text-center text-danger")
        if not selected_scenarios:
            return html.Div("No scenarios selected. Please select scenarios to display.",
                            className="text-warning")

        filtered = {k: v for k, v in dashboard_data.items() if k in selected_scenarios}
        charts = []

        # 2.1 Metric Comparison
        if "metric" in selected_charts:
            fig = pages.power_profiles.generate_metric_figure(
                selected_metric,
                tuple(year_range),
                selected_scenarios,
                filtered
            )
            # add a unified hovermode for these too
            fig.update_layout(hovermode="y unified")
            charts.append(card_component(
                "Metric Comparison",
                dcc.Graph(figure=fig, className="chart-container")
            ))

        # 2.2 Future Opex
        if "min_future_opex" in selected_charts:
            fig = pages.power_profiles.min_future_opex_figure(
                filtered,
                year_range=tuple(year_range)
            )
            fig.update_layout(hovermode="y unified")
            charts.append(card_component(
                "Future Opex",
                dcc.Graph(figure=fig, className="chart-container")
            ))

        # 2.3 Dwelling Pie
        if "dwelling" in selected_charts:
            fig = pages.power_profiles.dwelling_at_berth_pie_figure(
                filtered,
                selected_scenarios
            )
            charts.append(card_component(
                "Dwelling at Berth",
                dcc.Graph(figure=fig, className="chart-container")
            ))

        # 2.4 Single‑/Multi‑Year Stacked Bar
        if "single_year" in selected_charts:
            # all years → full range
            if single_year == "all":
                fig = pages.power_profiles.create_range_stacked_bar(filtered, year_range=tuple(year_range))
            else:
                try:
                    yr = int(single_year)
                    fig = pages.power_profiles.create_range_stacked_bar(filtered, year_range=(yr, yr))
                except (ValueError, TypeError):
                    fig = go.Figure().update_layout(title="Invalid year selected")
            charts.append(card_component(
                "Cost Breakdown",
                dcc.Graph(figure=fig, className="chart-container")
            ))

        if not charts:
            return html.Div("Please select at least one chart to display.",
                            className="text-warning")

        return html.Div(charts)

    @app.callback(
        [
            Output("kpi-avg-opex",      "children"),
            Output("kpi-opex-trend",    "children"),
            Output("kpi-fuel-price",    "children"),
            Output("kpi-fuel-price-status", "children"),
            Output("kpi-penalty",       "children"),
            Output("kpi-penalty-savings","children"),
            Output("kpi-euets",         "children"),
            Output("kpi-euets-trend",   "children"),
            Output("dashboard-opex-trend",       "figure"),
            Output("dashboard-penalty-trend",    "figure"),
            Output("dashboard-cost-breakdown",   "figure"),
            Output("dashboard-eu-ets-chart",     "figure"),
            Output("dashboard-metrics-table",    "children"),
            Output("dashboard-cost-breakdown-year", "options"),
            Output("dashboard-cost-breakdown-year", "value"),
        ],
        [
            Input("dashboard-year-range",         "value"),
            Input("dashboard-scenario-dropdown",  "value"),
            Input("dashboard-scenarios-store",    "data"),
            Input("dashboard-cost-breakdown-year","value"),
        ]
    )
    def update_executive_dashboard(year_range, selected_scenario, dashboard_data, selected_cb_year_input):
        # Build an empty‐data placeholder
        empty_fig = go.Figure().update_layout(
            xaxis={"visible": False}, yaxis={"visible": False},
            annotations=[{
                "text": "No data available",
                "xref": "paper", "yref": "paper",
                "showarrow": False, "font": {"size": 20}
            }]
        )

        # 1) No data or invalid scenario
        if not dashboard_data or selected_scenario not in dashboard_data:
            return (
                "N/A", "No data",
                "N/A", "No data",
                "N/A", "No data",
                "N/A", "No data",
                empty_fig, empty_fig, empty_fig, empty_fig,
                html.Div("No data available", className="text-center"),
                [], None
            )

        # 2) Filter records by year_range
        records = dashboard_data[selected_scenario]
        filtered = [r for r in records
                    if r.get("year") is not None
                    and year_range[0] <= r["year"] <= year_range[1]]
        if not filtered:
            return (
                "N/A", "No data",
                "N/A", "No data",
                "N/A", "No data",
                "N/A", "No data",
                empty_fig, empty_fig, empty_fig, empty_fig,
                html.Div("No data for selected years", className="text-center"),
                [], None
            )

        # 3) Extract time series
        years      = [r["year"]       for r in filtered]
        opex       = [r["opex"]       for r in filtered]
        fuel_price = [r["fuel_price"] for r in filtered]
        eu_ets     = [r["eu_ets"]     for r in filtered]
        penalty    = [r["penalty"]    for r in filtered]
        eu_ets     = [r["eu_ets"]     for r in filtered]

        # 4) Compute KPIs
        avg_opex        = sum(opex) / len(opex)
        opex_trend      = "Increasing" if opex[-1] > opex[0] else "Decreasing"
        avg_fuel_price  = sum(fuel_price) / len(fuel_price)
        fuel_price_stat = "Increasing" if fuel_price[-1] > fuel_price[0] else "Decreasing"
        avg_penalty  = sum(penalty) / len(penalty) if penalty else 0
        penalty_trend = "Increasing" if penalty[-1] > penalty[0] else "Decreasing"
        latest_penalty  = penalty[-1]
        avg_eu_ets       = sum(eu_ets) / len(eu_ets)
        euets_trend     = (
            "Increasing"  if eu_ets[-1] > eu_ets[0] else
            "Stable"      if eu_ets[-1] == eu_ets[0] else
            "Decreasing"
        )

        # 5) OPEX Trend chart
        opex_fig = go.Figure().add_trace(go.Scatter(
            x=years, y=opex, mode='lines+markers', name='OPEX'
        ))
        opex_fig.update_layout(
            xaxis_title='Year', yaxis_title='OPEX (€)',
            template='plotly_white', height=350
        )

        # 6) Penalty Trend (with flat‐line fix)
        penalty_fig = go.Figure().add_trace(go.Scatter(
            x=years, y=penalty, mode='lines+markers', name='Penalty'
        ))
        penalty_fig.update_layout(
            xaxis_title='Year', yaxis_title='Penalty (€)',
            template='plotly_white', height=350
        )
        # if penalty series is flat, force a tiny y‐range so the line shows
        if penalty and min(penalty) == max(penalty):
            flat  = penalty[0]
            delta = flat * 0.1 if flat else 1
            penalty_fig.update_yaxes(range=[flat - delta, flat + delta])

        # 7) fuel_price Trend
        comp_fig = go.Figure().add_trace(go.Scatter(
            x=years, y=fuel_price, mode='lines+markers', name='fuel_price'
        ))
        comp_fig.update_layout(
            xaxis_title='Year', yaxis_title='fuel_price (€)',
            template='plotly_white', height=350
        )

        # 8) Cost Breakdown for selected_cb_year_input
        unique_years = sorted({r["year"] for r in filtered})
        sel_year     = selected_cb_year_input if selected_cb_year_input in unique_years else unique_years[-1]
        entry        = next(r for r in filtered if r["year"] == sel_year)

        cb_fig = go.Figure()
        for key, label in [
            ("fuel_price",  "Fuel Price"),
            ("maintenance", "Maintenance"),
            ("eu_ets",      "EU ETS"),
            ("penalty",     "Penalty")
        ]:
            cb_fig.add_trace(go.Bar(
                y=[str(sel_year)],
                x=[entry.get(key, 0)],
                name=label,
                orientation='h'
            ))
        cb_fig.update_layout(
            barmode='stack',
            xaxis_title='Cost (€)',
            template='plotly_white',
            height=350
        )

        # 9) EU ETS Impact
        ets_fig = go.Figure().add_trace(go.Bar(
            x=years, y=eu_ets, name='EU ETS'
        ))
        ets_fig.update_layout(
            xaxis_title='Year',
            yaxis_title='EU ETS (€)',
            template='plotly_white',
            height=350
        )

        # 10) Metrics Table
        table_rows = [{
            "Year":       r["year"],
            "Blend %":    f"{r['blend_percentage']*100:.1f}%",
            "OPEX":       f"€{r['opex']:,.2f}",
            "fuel_price": f"€{r['fuel_price']:,.2f}",
            "EU ETS":     f"€{r['eu_ets']:,.2f}",
            "Penalty":    f"€{r['penalty']:,.2f}"
        } for r in filtered]

        metrics_table = dash_table.DataTable(
            columns=[{"name": c, "id": c} for c in ["Year","Blend %","OPEX","fuel_price","EU ETS","Penalty"]],
            data=table_rows,
            style_table={'overflowX':'auto'},
            style_cell={'textAlign':'right','padding':'12px'},
            style_header={'backgroundColor':'rgb(230,230,230)','fontWeight':'bold'}
        )

        return (
            # KPIs
            f"€{avg_opex:,.0f}", opex_trend,
            f"€{avg_fuel_price:,.0f}", fuel_price_stat,
            f"€{avg_penalty:,.0f}", penalty_trend,
            f"{avg_eu_ets:,.0f}", euets_trend,
            # Figures
            opex_fig, penalty_fig, cb_fig, ets_fig,
            # Table + breakdown-year controls
            metrics_table,
            [{"label": str(y), "value": y} for y in unique_years],
            sel_year
        )





    @app.callback(
        [Output("summary-scenario-dropdown", "options"),
         Output("summary-scenario-dropdown", "value")],
        Input("dashboard-scenarios-store", "data")
    )
    def update_summary_scenarios(dashboard_data):
        if not dashboard_data:
            return [], []
        scenarios = list(dashboard_data.keys())
        return ([{"label": s, "value": s} for s in scenarios], scenarios[:2])

    @app.callback(
        [
            Output("chart-opex-stack", "figure"),
            Output("chart-other-stack", "figure"),
            Output("summary-ranking-table", "data"),
            Output("summary-ranking-table", "columns"),
            Output("summary-ranking-table", "style_data_conditional"),
            Output("summary-cost-analysis", "children")
        ],
        [
            Input("dashboard-scenarios-store", "data"),
            Input("summary-scenario-dropdown", "value"),
            Input("summary-year-range", "value")
        ]
    )
    def update_summary(dashboard_data, fuels, year_range):
        if not dashboard_data or not fuels:
            empty = go.Figure().update_layout(
                title="No data available",
                annotations=[{
                    "text": "Please select scenarios to compare",
                    "xref": "paper", "yref": "paper",
                    "x": 0.5, "y": 0.5,
                    "showarrow": False,
                    "font": {"size": 16}
                }]
            )
            return [empty, empty] + [[]] * 3 + [html.Div("No data to analyze")]

        start, end = year_range
        totals = calculate_scenario_totals(dashboard_data, fuels, start, end)
        fig1 = create_opex_chart(fuels, totals, start, end)
        fig2 = create_other_costs_chart(fuels, totals, start, end)
        rows, cols, style = create_ranking_table(fuels, totals)
        analysis = create_cost_analysis(fuels, totals)
        return fig1, fig2, rows, cols, style, analysis


    def calculate_scenario_totals(data, fuels, start, end):
        """
        Calculate scenario totals using pandas for concise aggregation.
        """
        # Flatten data into DataFrame
        records = []
        for scenario, recs in data.items():
            for r in recs:
                records.append({**r, 'scenario': scenario})
        df = pd.DataFrame(records)
        # Filter
        df = df[df['scenario'].isin(fuels) & df['year'].between(start, end)]
        # Sum aggregates
        agg = df.groupby('scenario').agg({
            'opex': 'sum',
            'fuel_price': 'sum',
            'maintenance': 'sum',
            'spare': 'sum',
            'eu_ets': 'sum',
            'penalty': 'sum'
        }).reset_index()
        # Last compliance per scenario
        last_comp = df.sort_values('year').groupby('scenario').last()[['compliance_balance']].reset_index()
        # Merge
        result = pd.merge(agg, last_comp, on='scenario')
        # Convert to dict
        totals = {}
        for _, row in result.iterrows():
            totals[row['scenario']] = {
                'opex': row['opex'],
                'fuel_price': row['fuel_price'],
                'maintenance': row['maintenance'],
                'spare': row['spare'],
                'eu_ets': row['eu_ets'],
                'penalty': row['penalty'],
                'comp': row['compliance_balance']
            }
        return totals


    def create_opex_chart(fuels, totals, start, end):
        """
        OPEX Summary bar chart, sorted by total OPEX (ascending),
        with scenario name as a tiebreaker for identical values.
        """
        # Primary key = opex, secondary key = scenario name
        sorted_fuels = sorted(
            fuels,
            key=lambda f: (totals[f]['opex'], f)
        )
        fig = go.Figure([go.Bar(
            x=sorted_fuels,
            y=[totals[f]['opex'] for f in sorted_fuels],
            name="OPEX Σ"
        )])
        fig.update_layout(
            title=f"OPEX Summary ({start}–{end})",
            xaxis_title="Scenario",
            yaxis_title="€",
            template="plotly_white",
            yaxis_tickformat=",.0f",
            height=400,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        return fig

    def create_other_costs_chart(fuels, totals, start, end, excluded_components=None):
        """
        Stacked chart for "other" costs, sorted by total cost (ascending),
        with scenario name as a tiebreaker. Components stacked from largest to smallest.
        
        Parameters:
        - fuels: list of scenario names
        - totals: dictionary of cost data
        - start, end: years for the title
        - excluded_components: list of component keys to exclude (e.g., ['fuel_price'])
        """
        # Define all possible components and their labels
        all_components = ['fuel_price', 'maintenance', 'spare', 'eu_ets', 'penalty']
        all_labels = ['Fuel', 'Maintenance', 'Spare', 'EU ETS', 'Penalty']
        
        # Create a mapping from component to label
        component_to_label = dict(zip(all_components, all_labels))
        
        # Filter out excluded components if specified
        if excluded_components:
            active_components = [comp for comp in all_components if comp not in excluded_components]
        else:
            active_components = all_components.copy()
        
        # If no active components remain, return an empty figure
        if not active_components:
            fig = go.Figure()
            fig.update_layout(
                title=f"No components selected for display ({start}–{end})",
                template="plotly_white",
                height=400
            )
            return fig
        
        # Compute combined cost per scenario using only active components
        other_totals = {
            f: sum(totals[f][comp] for comp in active_components if comp in totals[f])
            for f in fuels
        }
        
        # Sort scenarios by (other_total, scenario_name)
        sorted_fuels = sorted(
            fuels,
            key=lambda f: (other_totals[f], f)
        )
        
        # Calculate the total for each component across all scenarios
        component_totals = {}
        for comp in active_components:
            component_totals[comp] = sum(totals[f].get(comp, 0) for f in fuels)
        
        # Sort components by their total size (largest first)
        sorted_components = sorted(
            active_components,
            key=lambda comp: component_totals[comp],
            reverse=True  # Largest first
        )
        
        fig = go.Figure()
        # Add traces in order from largest to smallest component
        for comp in sorted_components:
            label = component_to_label[comp]
            fig.add_trace(go.Bar(
                x=sorted_fuels,
                y=[totals[f].get(comp, 0) for f in sorted_fuels],
                name=label
            ))
        
        # Create a title that reflects any exclusions
        title = f"Other Costs Breakdown ({start}–{end})"
        if excluded_components:
            excluded_labels = [component_to_label[comp] for comp in excluded_components if comp in component_to_label]
            if excluded_labels:
                title += f" (excluding {', '.join(excluded_labels)})"
        
        fig.update_layout(
            barmode='stack',
            title=title,
            xaxis_title="Scenario",
            yaxis_title="€",
            template="plotly_white",
            yaxis_tickformat=",.0f",
            height=400,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        return fig



    def create_other_costs_chart(
        fuels, totals, start, end,
        included_components=None,
        sort_by_total=True
    ):
        """
        Stacked chart for costs, with optional total‑based sorting.
        - sort_by_total=True: order by sum of included components (ascending)
        - sort_by_total=False: respect the original 'fuels' order
        """
        all_components = ['fuel_price','maintenance','spare','eu_ets','penalty']
        all_labels     = ['Fuel','Maintenance','Spare','EU ETS','Penalty']
        colors = {
            'Fuel':'#D9D2E9','Maintenance':'#F9CB9C',
            'Spare':'#00CC96','EU ETS':'#6FA8DC','Penalty':'#FF9966'
        }
        comp_to_label = dict(zip(all_components, all_labels))

        # pick which components to show
        active = included_components or all_components
        active = [c for c in all_components if c in active]
        if not active:
            fig = go.Figure().update_layout(
                title=f"No components selected ({start}–{end})",
                template="plotly_white", height=400
            )
            return fig

        # 1) compute per‑scenario total of just the active components
        scenario_totals = {
            f: sum(totals[f].get(c,0) for c in active)
            for f in fuels
        }

        # 2) decide final x‑axis order
        if sort_by_total:
            # stable sort: ties keep dropdown order
            sorted_fuels = sorted(fuels, key=lambda f: scenario_totals[f])
        else:
            sorted_fuels = list(fuels)

        # 3) decide vertical stacking order (smallest on bottom → largest on top)
        comp_totals = {c: sum(totals[f].get(c,0) for f in fuels) for c in active}
        sorted_comps = sorted(active, key=lambda c: comp_totals[c])

        # build the figure
        fig = go.Figure()
        for comp in sorted_comps:
            lbl = comp_to_label[comp]
            fig.add_trace(go.Bar(
                x=sorted_fuels,
                y=[totals[f].get(comp,0) for f in sorted_fuels],
                name=lbl,
                marker_color=colors[lbl]
            ))

        fig.update_layout(
            barmode='stack',
            title=f"Other Costs Breakdown ({start}–{end})",
            xaxis_title="Scenario", yaxis_title="€",
            template="plotly_white", yaxis_tickformat=",.0f",
            height=400, margin=dict(l=50,r=50,t=50,b=50)
        )
        return fig


    def create_ranking_table(fuels, totals):
        """
        Create the scenario ranking table data, sorted by lowest OPEX (which already
        includes all cost components). Compliance is displayed but NOT included in
        the ranking key.
        """
        rows = []
        for f in fuels:
            opex = totals[f]['opex']
            fuel_price = totals[f]['fuel_price']
            maintenance = totals[f]['maintenance']
            spare = totals[f]['spare']
            eu_ets = totals[f]['eu_ets']
            penalty = totals[f]['penalty']

            
            rows.append({
                'Scenario': f,
                '_opex': opex,
                '_fuel_price': fuel_price,
                '_maintenance': maintenance,
                '_spare': spare,
                '_eu_ets': eu_ets,
                '_penalty': penalty,
                
                'OPEX Σ': f"€{opex:,.0f}",
                'Fuel Σ': f"€{fuel_price:,.0f}",
                'Maintenance Σ': f"€{maintenance:,.0f}",
                'Spare Σ': f"€{spare:,.0f}",
                'EU ETS Σ': f"€{eu_ets:,.0f}",
                'Penalty Σ': f"€{penalty:,.0f}",
                
            })

        # Sort by OPEX only
        rows.sort(key=lambda r: r['_opex'])

        # Highlight best/worst in each visible column
        style = []
        for display, raw, invert in [
            ('OPEX Σ', '_opex', False),         # lower is better
            ('Fuel Σ', '_fuel_price', False),   # lower is better
            ('Maintenance Σ', '_maintenance', False), # lower is better
            ('Spare Σ', '_spare', False),       # lower is better
            ('EU ETS Σ', '_eu_ets', False),     # lower is better
            ('Penalty Σ', '_penalty', False)    # lower is better
        ]:
            vals = [r[raw] for r in rows]
            best = min(vals) if not invert else max(vals)
            worst = max(vals) if not invert else min(vals)
            style += [
                {
                'if': {
                    'filter_query': f"{{{raw}}} = {best}",
                    'column_id': display
                },
                'backgroundColor': '#d4edda',
                'fontWeight': 'bold'
                },
                {
                'if': {
                    'filter_query': f"{{{raw}}} = {worst}",
                    'column_id': display
                },
                'backgroundColor': '#f8d7da',
                'fontWeight': 'bold'
                }
            ]

        # Clean out raw helper keys before returning to DataTable
        for r in rows:
            for raw_key in ['_fuel_price', '_maintenance', '_spare', '_eu_ets', '_penalty']:
                r.pop(raw_key)


        # Only two columns now
        columns = [
            {'name': 'Scenario',       'id': 'Scenario'},
            {'name': 'OPEX Σ',         'id': 'OPEX Σ'},
            {'name': 'Fuel Price Σ',         'id': 'Fuel Σ'},
            {'name': 'EU ETS Penalty Σ',       'id': 'EU ETS Σ'},
            {'name': 'Fuel EU Penalty Σ',      'id': 'Penalty Σ'},
            {'name': 'Maintenance Cost Σ',   'id': 'Maintenance Σ'},
            {'name': 'Spare Cost Σ',        'id': 'Spare Σ'},

        ]

        return rows, columns, style



    def create_cost_analysis(fuels, totals):
        total_costs = {f: sum(totals[f][k] for k in ['opex', 'fuel_price', 'maintenance', 'spare', 'eu_ets', 'penalty']) for f in fuels}
        best = min(total_costs, key=total_costs.get)
        worst = max(total_costs, key=total_costs.get)
        return html.Div([
            html.H5("Cost Analysis Summary"),
            html.P(f"Based on the selected range, {best} has the lowest cost (€{total_costs[best]:,.0f}) and {worst} the highest (€{total_costs[worst]:,.0f}).")
        ])


    # ─── 1) Capture report configuration ──────────────────────────────────────────
    @app.callback(
        Output("report-config-store", "data"),
        Input("generate-report-btn", "n_clicks"),
        [
            State("report-scope", "value"),
            State("report-dates", "start_date"),
            State("report-dates", "end_date"),
            State("report-scenarios", "value"),
            State("report-currency", "value"),
        ],
        prevent_initial_call=True
    )
    def collect_report_config(n_clicks, scope, start_date, end_date, scenarios, currency):
        if not n_clicks:
            raise exceptions.PreventUpdate
        return {
            "scope": scope,
            "start_date": start_date,
            "end_date": end_date,
            "scenarios": scenarios or [],
            "currency": currency
        }


    # ─── 2) Render preview of selections ──────────────────────────────────────────
    @app.callback(
        Output("report-preview", "children"),
        Input("report-config-store", "data")
    )
    def render_preview(cfg):
        if not cfg:
            return "Click “Generate Preview” to see your selections here."
        return [
            html.P(f"**Scope**: {cfg['scope'].title()}"),
            html.P(f"**Period**: {cfg['start_date']} → {cfg['end_date']}"),
            html.P(f"**Scenarios**: {', '.join(cfg['scenarios']) or '— none —'}"),
            html.P(f"**Currency**: {cfg['currency']}"),
        ]


    # ─── 3) Download combined CSV ────────────────────────────────────────────────
    @app.callback(
        Output("download-report", "data"),
        Input("download-report-btn", "n_clicks"),
        [
            State("report-config-store", "data"),
            State("vessel-data-store", "data"),
            State("dashboard-scenarios-store", "data")
        ],
        prevent_initial_call=True
    )
    def download_csv(n_clicks, cfg, vessel_data, dash_data):
        if not n_clicks or not cfg:
            raise exceptions.PreventUpdate

        # Combine each selected scenario’s records into one DataFrame
        dfs = []
        for scen in cfg["scenarios"]:
            records = dash_data.get(scen, [])
            df = pd.DataFrame(records)
            df["scenario"] = scen
            dfs.append(df)

        if dfs:
            combined = pd.concat(dfs, ignore_index=True)
        else:
            combined = pd.DataFrame([{"note": "No data for selected scenarios"}])

        # Send it as a CSV
        return send_data_frame(
            combined.to_csv,
            filename=f"report_{cfg['scope']}_{datetime.now():%Y%m%d}.csv",
            index=False
        )

        

    @app.callback(
        Output("report-scenarios", "options"),
        Input("dashboard-scenarios-store", "data")
    )
    def update_scenario_options(scenarios_data):
        if not scenarios_data:
            return []
        return [{'label': scen, 'value': scen} for scen in scenarios_data.keys()]


    @app.callback(
        Output("output-content", "children"),
        [
            Input("api-data-store",           "data"),
            Input("future-data-store",        "data"),
            Input("table-selection-dropdown", "value"),
            Input("timeframe-toggle",         "value")
        ]
    )
    def display_emissions_output(api_data, future_data, selected_tables, timeframe):
        # guard against missing
        api_data    = api_data    or {}
        future_data = future_data or {}

        if not api_data:
            return html.Div(
                dbc.Alert("No data available. Please calculate first.", color="warning"),
                className="mt-4"
            )
        if not selected_tables:
            return html.Div(
                dbc.Alert("Please select at least one table.", color="info"),
                className="mt-4"
            )

        currency = future_data.get("currency-choice", "EUR")
        sections = []

        if 'vessel_summary' in selected_tables:
            sections.append(
                dbc.Card([dbc.CardHeader("Vessel Summary"),
                        dbc.CardBody(get_vessel_summary_table(api_data, currency))],
                        className="mb-4")
            )

        if 'current' in selected_tables:
            sections.append(
                dbc.Card([dbc.CardHeader("Current Output Table"),
                        dbc.CardBody(get_current_output_table(api_data, currency))],
                        className="mb-4")
            )

        if 'future' in selected_tables:
            sections.append(
                dbc.Card([dbc.CardHeader("Future Output Table"),
                        dbc.CardBody(get_future_output_table(api_data, currency))],
                        className="mb-4")
            )

        if 'opex' in selected_tables:
            tbl = (get_opex_comparison_table(api_data, currency)
                if timeframe=="day"
                else get_opex_comparison_table_year(api_data, currency))
            sections.append(
                dbc.Card([dbc.CardHeader("OPEX Comparison"), dbc.CardBody(tbl)],
                        className="mb-4")
            )

        if 'emissions' in selected_tables:
            tbl = (get_emissions_comparison_table(api_data)
                if timeframe=="day"
                else get_emissions_comparison_table_year(api_data))
            sections.append(
                dbc.Card([dbc.CardHeader("Emissions Comparison"), dbc.CardBody(tbl)],
                        className="mb-4")
            )

        if 'carbon_footprint' in selected_tables:
            sections.append(
                dbc.Card([dbc.CardHeader("Carbon Footprint Scope 1–3"),
                        dbc.CardBody(get_carbon_footprint_table(api_data))],
                        className="mb-4")
            )

        if 'country_visits' in selected_tables:
            sections.append(
                dbc.Card([dbc.CardHeader("Country Visits"),
                        dbc.CardBody(get_country_visits_table(api_data, currency))],
                        className="mb-4")
            )

        # finally embed your executive dashboard
        sections.append(
            dbc.Card([dbc.CardHeader("Dashboard"), dbc.CardBody(dashboard_layout(api_data, currency))],
                    className="mb-4")
        )

        return html.Div(sections)
    return app