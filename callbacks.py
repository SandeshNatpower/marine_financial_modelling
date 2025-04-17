import json
from dash import dash_table
import requests
from urllib.parse import urlencode

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
    cashflow_figure,
    min_future_opex_figure,
    maintenance_cost_figure,
    penalty_cost_figure,
    spares_figure,
    opex_cost_figure,
    fuel_consumption_figure,
)

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
        "vessel_id": vessel_data.get("imo", 11111),
        "main_engine_power_kw": float(vessel_data.get("total_engine_power", 38400)),
        "aux_engine_power_kw": float(vessel_data.get("average_hoteling_kw", 2020)),
        "sailing_engine_load": float(vessel_data.get("sailing_engine_load", 50))/100,
        "working_engine_load": float(vessel_data.get("working_engine_load", 30))/100,
        "shore_engine_load": float(vessel_data.get("shore_engine_load", 39.5))/100,
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
        "vessel_id": 9803613,
        "main_engine_power_kw": 38400,
        "aux_engine_power_kw": 2020,
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
        "vessel_id": vessel_data.get("imo", fallback_defaults["vessel_id"]),
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
        main_power = vessel_data.get("total_engine_power", config.DEFAULT_VESSEL.get("total_engine_power", 38400))
        aux_power = vessel_data.get("average_hoteling_kw", config.DEFAULT_VESSEL.get("average_hoteling_kw", 2020))
        return (
            main_power,
            aux_power,
            vessel_data.get("main_engine_type", "4-STROKE"),
            vessel_data.get("aux_engine_type", "4-STROKE"),
            vessel_data.get("main_fuel_type", "MDO"),
            vessel_data.get("aux_fuel_type", "MDO")
        )


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

        main_power = vessel_data.get("total_engine_power", 38400)
        aux_power = vessel_data.get("average_hoteling_kw", 2020)
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
            "vessel_id": vessel_data.get("imo", 11111),
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
            default_value = scenario_options[0]["value"] if scenario_options else None
            return scenario_options, default_value
        elif triggered_id == "scenario-filter":
            if not selected_scenarios or len(selected_scenarios) == 0:
                raise PreventUpdate
            scenario_options = [{"label": scenario, "value": scenario} for scenario in selected_scenarios]
            default_value = selected_scenarios[0] if selected_scenarios else None
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
            "vessel_id": vessel_data.get("imo", 9803613),
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
        default_value = scenarios[:2] if len(scenarios) >= 2 else scenarios
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
        Output("total-expenditure", "figure"),
        [
            Input("year-range-slider",  "value"),
            Input("scenario-filter",    "value"),
            Input("dashboard-scenarios-store", "data"),
        ]
    )
    def update_total_expenditure(year_range, selected_scenarios, dashboard_data):
        if not dashboard_data or not selected_scenarios:
            return go.Figure().update_layout(title="No data to display")

        filtered_data = {
            name: data
            for name, data in dashboard_data.items()
            if name in selected_scenarios
        }

        # Call without view parameter
        total_exp_fig = pages.power_profiles.total_expenditure_stacked_bar_chart(
            filtered_data,
            year_range
        )
        return total_exp_fig


    @app.callback(
        Output("single-year-breakdown", "figure"),
        [
            Input("single-year-dropdown", "value"),
            Input("dashboard-scenarios-store", "data"),
            Input("scenario-filter", "value")
        ]
    )
    def update_single_year_breakdown(single_year, dashboard_data, selected_scenarios):
        if not dashboard_data or not selected_scenarios:
            return go.Figure().update_layout(title="No scenarios selected")
        filtered_data = {k: v for k, v in dashboard_data.items() if k in selected_scenarios}
        if single_year == "all":
            return go.Figure().update_layout(title="Single-Year Breakdown: No single year selected")
        try:
            chosen_year = int(single_year)
        except ValueError:
            return go.Figure().update_layout(title="Invalid year selected")
        fig = pages.power_profiles.create_single_year_stacked_bar(filtered_data, chosen_year)
        return fig


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
            Input("dashboard-chart-selector", "value"),
            Input("dashboard-metric-dropdown", "value"),
            Input("dashboard-year-range-slider", "value"),
            Input("dashboard-scenarios-store", "data"),
            Input("single-year-dropdown", "value"),
            Input("scenario-filter", "value")
        ]
    )
    def update_dashboard_charts(selected_charts, selected_metric, year_range, dashboard_data, single_year, selected_scenarios):
        if not dashboard_data:
            return html.Div("No data available. Please calculate scenarios first.", className="text-center text-danger")
        if not selected_scenarios:
            return html.Div("No scenarios selected. Please select scenarios to display.", className="text-warning")

        charts = []
        filtered_data = {k: v for k, v in dashboard_data.items() if k in selected_scenarios}

        if "metric" in selected_charts:
            metric_fig = pages.power_profiles.generate_metric_figure(selected_metric, year_range, selected_scenarios, filtered_data)
            charts.append(card_component("Metric Comparison", dcc.Graph(figure=metric_fig, className="chart-container")))

        if "min_future_opex" in selected_charts:
            opex_fig = pages.power_profiles.min_future_opex_figure(filtered_data, year_range=tuple(year_range))
            charts.append(card_component("Future Opex", dcc.Graph(figure=opex_fig, className="chart-container")))

        if "dwelling" in selected_charts:
            dwelling_fig = pages.power_profiles.dwelling_at_berth_pie_figure(filtered_data, selected_scenarios)
            charts.append(card_component("Dwelling at Berth", dcc.Graph(figure=dwelling_fig, className="chart-container")))

        if "total_expenditure" in selected_charts:
            total_exp_fig = pages.power_profiles.total_expenditure_stacked_bar_chart(filtered_data, year_range)
            charts.append(card_component("Total Expenditure Comparison", dcc.Graph(figure=total_exp_fig, className="chart-container")))

        if "single_year" in selected_charts:
            if single_year == "all":
                single_year_fig = go.Figure().update_layout(title="No single year selected")
            else:
                try:
                    chosen_year = int(single_year)
                except ValueError:
                    chosen_year = None
                if chosen_year is None:
                    single_year_fig = go.Figure().update_layout(title="Invalid year selected")
                else:
                    single_year_fig = pages.power_profiles.create_single_year_stacked_bar(filtered_data, chosen_year)
            charts.append(card_component("Single Year Breakdown", dcc.Graph(figure=single_year_fig, className="chart-container")))

        if not charts:
            return html.Div("Please select at least one chart to display.", className="text-warning")

        return html.Div(charts)


    @app.callback(
        [
            Output("kpi-avg-opex",      "children"),
            Output("kpi-opex-trend",    "children"),
            Output("kpi-compliance",    "children"),
            Output("kpi-compliance-status", "children"),
            Output("kpi-penalty",       "children"),
            Output("kpi-penalty-savings","children"),
            Output("kpi-blend",         "children"),
            Output("kpi-blend-trend",   "children"),
            Output("dashboard-opex-trend",       "figure"),
            Output("dashboard-penalty-trend",    "figure"),
            Output("dashboard-compliance-chart", "figure"),
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
                empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
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
                empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
                html.Div("No data for selected years", className="text-center"),
                [], None
            )

        # 3) Extract time series
        years      = [r["year"]               for r in filtered]
        opex       = [r["opex"]               for r in filtered]
        compliance = [r["compliance_balance"] for r in filtered]
        eu_ets     = [r["eu_ets"]             for r in filtered]
        penalty    = [r["penalty"]            for r in filtered]
        blend_pct  = [r["blend_percentage"]   for r in filtered]

        # 4) Compute KPIs
        avg_opex        = sum(opex) / len(opex)
        opex_trend      = "Increasing" if opex[-1] > opex[0] else "Decreasing"
        avg_compliance  = sum(compliance) / len(compliance)
        compliance_stat = "Positive" if avg_compliance > 0 else "Negative"
        latest_penalty  = penalty[-1]
        avg_blend       = sum(blend_pct) / len(blend_pct)
        blend_trend     = (
            "Increasing"  if blend_pct[-1] > blend_pct[0] else
            "Stable"      if blend_pct[-1] == blend_pct[0] else
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

        # 7) Compliance Trend
        comp_fig = go.Figure().add_trace(go.Scatter(
            x=years, y=compliance, mode='lines+markers', name='Compliance'
        ))
        comp_fig.update_layout(
            xaxis_title='Year', yaxis_title='Compliance (€)',
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
            "Compliance": f"€{r['compliance_balance']:,.2f}",
            "EU ETS":     f"€{r['eu_ets']:,.2f}",
            "Penalty":    f"€{r['penalty']:,.2f}"
        } for r in filtered]

        metrics_table = dash_table.DataTable(
            columns=[{"name": c, "id": c} for c in ["Year","Blend %","OPEX","Compliance","EU ETS","Penalty"]],
            data=table_rows,
            style_table={'overflowX':'auto'},
            style_cell={'textAlign':'right','padding':'12px'},
            style_header={'backgroundColor':'rgb(230,230,230)','fontWeight':'bold'}
        )

        return (
            # KPIs
            f"€{avg_opex:,.0f}", opex_trend,
            f"€{avg_compliance:,.0f}", compliance_stat,
            f"€{latest_penalty:,.0f}", "N/A",
            f"{avg_blend*100:.1f}%", blend_trend,
            # Figures
            opex_fig, penalty_fig, comp_fig, cb_fig, ets_fig,
            # Table + breakdown-year controls
            metrics_table,
            [{"label": str(y), "value": y} for y in unique_years],
            sel_year
        )

    
    @app.callback(
        Output("output-content", "children"),
        [
            Input("api-data-store", "data"),
            Input("future-data-store", "data"),
            Input("table-selection-dropdown", "value"),
            Input("timeframe-toggle", "value")
        ]
    )
    def display_emissions_output(api_data, future_data, selected_tables, timeframe):
        if not api_data:
            return html.Div(
                dbc.Alert("No data available. Please calculate emissions and costs first.", color="warning"),
                className="mt-4"
            )
        if not selected_tables:
            return html.Div(
                dbc.Alert("Please select at least one table to display.", color="info"),
                className="mt-4"
            )
        
        currency = (future_data or {}).get("currency-choice", "EUR")
        conv_factor = config.CURRENCIES.get(currency, {}).get("conversion", 1.0)
        sections = []
        
        
        
        if 'vessel_summary' in selected_tables:
            sections.append(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H4("Vessel Summary")),
                        dbc.CardBody(get_vessel_summary_table(api_data, currency))
                    ],
                    className="mb-4"    
          
                )
            )
        if 'current' in selected_tables:
            sections.append(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H4("Current Output Table")),
                        dbc.CardBody(get_current_output_table(api_data, currency))
                    ],
                    className="mb-4"
                )
            )
        
        if 'future' in selected_tables:
            sections.append(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H4("Future Output Table")),
                        dbc.CardBody(get_future_output_table(api_data, currency))
                    ],
                    className="mb-4"
                )
            )
        
        if 'opex' in selected_tables:
            if timeframe == "day":
                opex_table = get_opex_comparison_table(api_data, currency)
            else:
                opex_table = get_opex_comparison_table_year(api_data, currency)
            sections.append(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H4("OPEX Comparison")),
                        dbc.CardBody(opex_table)
                    ],
                    className="mb-4"
                )
            )
        
        if 'emissions' in selected_tables:
            if timeframe == "day":
                emissions_table = get_emissions_comparison_table(api_data)
            else:
                emissions_table = get_emissions_comparison_table_year(api_data)
            sections.append(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H4("Emissions Comparison")),
                        dbc.CardBody(emissions_table)
                    ],
                    className="mb-4"
                )
            )

        if 'carbon_footprint' in selected_tables:
            sections.append(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H4("Carbon Footprint Scope 1, 2, and 3")),
                        dbc.CardBody(get_carbon_footprint_table(api_data))
                    ],
                    className="mb-4"
                )
            )       
        
        
        dash_layout_content = dashboard_layout(api_data, currency)
        sections.append(
            dbc.Card(
                [
                    dbc.CardHeader(html.H4("Dashboard")),
                    dbc.CardBody(dash_layout_content)
                ],
                className="mb-4"
            )
        )
        
        return html.Div(sections)
    return app


