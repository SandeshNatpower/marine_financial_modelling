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
    
    """ # Callback 1: Update Scenario Filter Options and Default Value
    @app.callback(
        [Output("scenario-filter", "options"),
         Output("scenario-filter", "value")],
        [Input("dashboard-scenarios-store", "data")]
    )
    def update_scenario_filter(dashboard_data):
        if not dashboard_data:
            raise PreventUpdate

        _, scenarios = pages.power_profiles.load_min_future_opex_scenarios(dashboard_data)
        scenario_options = [{"label": k, "value": k} for k in scenarios.keys()]
        default_scenarios = list(scenarios.keys())
        return scenario_options, default_scenarios """

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
            Input("year-range-slider", "value"),
            Input("scenario-filter", "value"),            # <<--- scenario filter
            Input("dashboard-scenarios-store", "data"),
            Input("data-view-selector", "value")
        ]
    )
    def update_total_expenditure(year_range, selected_scenarios, dashboard_data, data_view):
        if not dashboard_data or not selected_scenarios:
            return go.Figure().update_layout(title="No scenarios selected")

        filtered_data = {k: v for k, v in dashboard_data.items() if k in selected_scenarios}
        total_exp_fig = pages.power_profiles.total_expenditure_stacked_bar_chart(filtered_data, year_range, view=data_view)
        return total_exp_fig


    @app.callback(
        Output("single-year-breakdown", "figure"),
        [
            Input("single-year-dropdown", "value"),
            Input("dashboard-scenarios-store", "data"),
            Input("scenario-filter", "value")             # <<--- scenario filter
        ]
    )
    def update_single_year_breakdown(single_year, dashboard_data, selected_scenarios):
        # If no data or no scenarios selected, show an empty figure.
        if not dashboard_data or not selected_scenarios:
            return go.Figure().update_layout(title="No scenarios selected")

        # Filter the data to include only the selected scenarios.
        filtered_data = {k: v for k, v in dashboard_data.items() if k in selected_scenarios}

        if single_year == "all":
            return go.Figure().update_layout(title="Single-Year Breakdown: No single year selected")
        
        # Convert user input to an integer year
        try:
            chosen_year = int(single_year)
        except ValueError:
            return go.Figure().update_layout(title="Invalid year selected")

        fig = pages.power_profiles.create_single_year_stacked_bar(filtered_data, chosen_year)
        return fig


    @app.callback(
        Output("metric-comparison-chart", "figure"),
        [
            Input("metric-dropdown", "value"),
            Input("year-range-slider", "value"),
            Input("scenario-filter", "value"),           
            Input("dashboard-scenarios-store", "data"),
            Input("data-view-selector", "value")
        ]
    )
    def update_metric_comparison(metric, year_range, selected_scenarios, dashboard_data, data_view):
        # 1) If there is no data or no selected scenarios, show a "no data" figure
        if not dashboard_data or not selected_scenarios:
            return go.Figure().update_layout(title="No scenarios selected")

        # 2) Filter the data so that only keys that match the user’s scenario selections are included
        filtered_data = {k: v for k, v in dashboard_data.items() if k in selected_scenarios}

        # 3) Generate the figure using only the filtered data
        fig = pages.power_profiles.generate_metric_figure(metric, year_range, selected_scenarios, filtered_data, data_view)
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
        [Input("dashboard-chart-selector", "value"),
        Input("dashboard-metric-dropdown", "value"),
        Input("dashboard-year-range-slider", "value"),
        Input("dashboard-view-selector", "value"),
        Input("dashboard-scenarios-store", "data"),
        Input("single-year-dropdown", "value"),
        Input("scenario-filter", "value")]  # This input was missing from the function params
    )
    def update_dashboard_charts(selected_charts, selected_metric, year_range, data_view, 
                            dashboard_data, single_year, selected_scenarios):
        if not dashboard_data:
            return html.Div("No data available. Please calculate scenarios first.", className="text-center text-danger")
        
        if not selected_scenarios:
            return html.Div("No scenarios selected. Please select scenarios to display.", className="text-warning")
        
        charts = []
        # Use the filtered data based on user-selected scenarios
        filtered_data = {k: v for k, v in dashboard_data.items() if k in selected_scenarios}
        
        # Metric Comparison Chart
        if "metric" in selected_charts:
            metric_fig = pages.power_profiles.generate_metric_figure(selected_metric, year_range, 
                                                                    selected_scenarios, filtered_data, data_view)
            charts.append(
                card_component("Metric Comparison", dcc.Graph(figure=metric_fig, className="chart-container"))
            )
        
        # Min Future OPEX Chart
        if "min_future_opex" in selected_charts:
            opex_fig = pages.power_profiles.min_future_opex_figure(filtered_data, year_range=tuple(year_range))
            charts.append(
                card_component("Future Opex", dcc.Graph(figure=opex_fig, className="chart-container"))
            )
        
        # Dwelling at Berth Pie Chart
        if "dwelling" in selected_charts:
            dwelling_fig = pages.power_profiles.dwelling_at_berth_pie_figure(filtered_data, selected_scenarios)
            charts.append(
                card_component("Dwelling at Berth", dcc.Graph(figure=dwelling_fig, className="chart-container"))
            )
        
        # Total Expenditure Comparison Chart
        if "total_expenditure" in selected_charts:
            total_exp_fig = pages.power_profiles.total_expenditure_stacked_bar_chart(filtered_data, year_range, view=data_view)
            charts.append(
                card_component("Total Expenditure Comparison", dcc.Graph(figure=total_exp_fig, className="chart-container"))
            )
        
        # Single-Year Breakdown Chart - keeping default behavior for the year selection
        if "single_year" in selected_charts:
            if single_year == "all":
                single_year_fig = go.Figure().update_layout(title="No single year selected")
            else:
                chosen_year = int(single_year)
                single_year_fig = pages.power_profiles.create_single_year_stacked_bar(filtered_data, chosen_year)
            charts.append(
                card_component("Single Year Breakdown", dcc.Graph(figure=single_year_fig, className="chart-container"))
            )
        
        if not charts:
            return html.Div("Please select at least one chart to display.", className="text-warning")
        
        return html.Div(charts)

    @app.callback(
        [
            Output("kpi-avg-opex", "children"),
            Output("kpi-opex-trend", "children"),
            Output("kpi-compliance", "children"),
            Output("kpi-compliance-status", "children"),
            Output("kpi-penalty", "children"),
            Output("kpi-penalty-savings", "children"),
            Output("kpi-blend", "children"),
            Output("kpi-blend-trend", "children"),
            Output("dashboard-opex-trend", "figure"),
            Output("dashboard-compliance-chart", "figure"),
            Output("dashboard-cost-breakdown", "figure"),
            Output("dashboard-eu-ets-chart", "figure"),
            Output("dashboard-metrics-table", "children"),
            Output("dashboard-cost-breakdown-year", "options"),
            Output("dashboard-cost-breakdown-year", "value")
        ],
        [
            Input("dashboard-year-range", "value"),
            Input("dashboard-scenario-dropdown", "value"),
            Input("dashboard-view-type", "value"),
            Input("dashboard-scenarios-store", "data"),
            Input("dashboard-cost-breakdown-year", "value")
        ]
    )
    def update_executive_dashboard(year_range, selected_scenario, view_type, dashboard_data, selected_cb_year_input):
        # Handle missing data
        if not dashboard_data or selected_scenario not in dashboard_data:
            empty_fig = go.Figure()
            empty_fig.update_layout(
                xaxis={"visible": False},
                yaxis={"visible": False},
                annotations=[{
                    "text": "No data available. Please calculate scenarios first.",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 20}
                }]
            )
            return (
                "N/A", "No data", "N/A", "No data", "N/A", "No data", "N/A", "No data",
                empty_fig, empty_fig, empty_fig, empty_fig,
                html.Div("No data available", className="text-center"),
                [], None
            )
        
        scenario_data = dashboard_data[selected_scenario]
        filtered_data = [entry for entry in scenario_data if year_range[0] <= entry["year"] <= year_range[1]]
        
        if not filtered_data:
            empty_fig = go.Figure()
            empty_fig.update_layout(
                xaxis={"visible": False},
                yaxis={"visible": False},
                annotations=[{
                    "text": "No data available for the selected year range.",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 20}
                }]
            )
            return (
                "N/A", "No data", "N/A", "No data", "N/A", "No data", "N/A", "No data",
                empty_fig, empty_fig, empty_fig, empty_fig,
                html.Div("No data for selected years", className="text-center"),
                [], None
            )
        
        years = [entry["year"] for entry in filtered_data]
        
        if view_type == "future":
            opex_values = [entry["future"]["opex"] for entry in filtered_data]
            compliance_values = [entry["future"]["compliance_balance"] for entry in filtered_data]
            eu_ets_values = [entry["future"]["eu_ets"] for entry in filtered_data]
            fuel_price = [entry["future"]["fuel_price"] for entry in filtered_data]
            maintenance = [entry["future"]["maintenance"] for entry in filtered_data]
            penalty_values = [entry["future"]["penalty"] for entry in filtered_data]
        elif view_type == "current":
            opex_values = [entry["current"]["opex"] for entry in filtered_data]
            compliance_values = [entry["current"]["compliance_balance"] for entry in filtered_data]
            eu_ets_values = [entry["current"]["eu_ets"] for entry in filtered_data]
            fuel_price = [entry["current"]["fuel_price"] for entry in filtered_data]
            maintenance = [entry["current"]["maintenance"] for entry in filtered_data]
            penalty_values = [entry["current"]["penalty"] for entry in filtered_data]
        else:  # view_type == "both"
            future_opex = [entry["future"]["opex"] for entry in filtered_data]
            current_opex = [entry["current"]["opex"] for entry in filtered_data]
            future_compliance = [entry["future"]["compliance_balance"] for entry in filtered_data]
            current_compliance = [entry["current"]["compliance_balance"] for entry in filtered_data]
            future_eu_ets = [entry["future"]["eu_ets"] for entry in filtered_data]
            current_eu_ets = [entry["current"]["eu_ets"] for entry in filtered_data]
            opex_values = future_opex
            compliance_values = future_compliance
            eu_ets_values = future_eu_ets
            fuel_price = [entry["future"]["fuel_price"] for entry in filtered_data]
            maintenance = [entry["future"]["maintenance"] for entry in filtered_data]
            penalty_values = [entry["future"]["penalty"] for entry in filtered_data]
        
        blend_percentages = [entry["blend_percentage"] for entry in filtered_data]
        avg_blend = sum(blend_percentages) / len(blend_percentages)
        blend_trend = "Increasing" if blend_percentages[-1] > blend_percentages[0] else "Stable" if blend_percentages[-1] == blend_percentages[0] else "Decreasing"
        
        avg_opex = sum(opex_values) / len(opex_values)
        opex_trend = "Increasing" if opex_values[-1] > opex_values[0] else "Decreasing"
        avg_compliance = sum(compliance_values) / len(compliance_values)
        compliance_status = "Positive" if avg_compliance > 0 else "Negative"
        
        if view_type == "both":
            current_penalties = [entry["current"]["penalty"] for entry in filtered_data]
            future_penalties = [entry["future"]["penalty"] for entry in filtered_data]
            total_current_penalty = sum(current_penalties)
            total_future_penalty = sum(future_penalties)
            penalty_reduction = total_current_penalty - total_future_penalty
            penalty_percentage = (penalty_reduction / total_current_penalty * 100) if total_current_penalty > 0 else 0
        else:
            total_penalty = sum(penalty_values)
            penalty_reduction = total_penalty
            penalty_percentage = 100

        total_savings = sum([entry["current"]["opex"] - entry["future"]["opex"] for entry in filtered_data]) if view_type == "both" else None

        # ----- Chart: OPEX Trend -----
        opex_fig = go.Figure()
        if view_type == "both":
            opex_fig.add_trace(go.Scatter(
                x=years, y=current_opex, mode='lines+markers', name='Current OPEX',
                line=dict(color='#FF7F0E', width=2)
            ))
            opex_fig.add_trace(go.Scatter(
                x=years, y=future_opex, mode='lines+markers', name='Future OPEX',
                line=dict(color='#1F77B4', width=2)
            ))
        else:
            opex_fig.add_trace(go.Scatter(
                x=years, y=opex_values, mode='lines+markers', name='OPEX',
                line=dict(color='#1F77B4', width=2)
            ))
        opex_fig.update_layout(
            xaxis_title='Year',
            yaxis_title='OPEX (€)',
            template='plotly_white',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=40, t=40, b=40),
            height=350
        )
        
        # ----- Chart: Compliance Balance -----
        compliance_fig = go.Figure()
        if view_type == "both":
            compliance_fig.add_trace(go.Scatter(
                x=years, y=current_compliance, mode='lines+markers', name='Current Compliance',
                line=dict(color='#FF7F0E', width=2)
            ))
            compliance_fig.add_trace(go.Scatter(
                x=years, y=future_compliance, mode='lines+markers', name='Future Compliance',
                line=dict(color='#1F77B4', width=2)
            ))
        else:
            compliance_fig.add_trace(go.Scatter(
                x=years, y=compliance_values, mode='lines+markers', name='Compliance Balance',
                line=dict(color='#2CA02C', width=2)
            ))
        compliance_fig.update_layout(
            xaxis_title='Year',
            yaxis_title='Compliance Balance (€)',
            template='plotly_white',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=40, t=40, b=40),
            height=350
        )
        
        # ----- Chart: Cost Breakdown -----
        unique_years = sorted(list({entry["year"] for entry in filtered_data}))
        if selected_cb_year_input in unique_years:
            selected_cb_year = selected_cb_year_input
        else:
            selected_cb_year = unique_years[-1]
        matching_entries = [entry for entry in filtered_data if entry["year"] == selected_cb_year]
        if matching_entries:
            cost_breakdown_entry = matching_entries[0]
        else:
            cost_breakdown_entry = filtered_data[-1]
        
        if view_type == "both":
            current_data = cost_breakdown_entry["current"]
            future_data  = cost_breakdown_entry["future"]
            cb_year = cost_breakdown_entry["year"]
            cost_breakdown_fig = go.Figure()
            cost_breakdown_fig.add_trace(go.Bar(
                y=["Current"],
                x=[current_data["fuel_price"]],
                name='Fuel Price',
                orientation='h',
                marker=dict(color='gray')
            ))
            cost_breakdown_fig.add_trace(go.Bar(
                y=["Current"],
                x=[current_data["maintenance"]],
                name='Maintenance',
                orientation='h',
                marker=dict(color='#FF7F0E')
            ))
            cost_breakdown_fig.add_trace(go.Bar(
                y=["Current"],
                x=[current_data["eu_ets"]],
                name='EU ETS',
                orientation='h',
                marker=dict(color='#2CA02C')
            ))
            cost_breakdown_fig.add_trace(go.Bar(
                y=["Current"],
                x=[current_data["penalty"]],
                name='Penalty',
                orientation='h',
                marker=dict(color='#D62728')
            ))
            # Future data:
            cost_breakdown_fig.add_trace(go.Bar(
                y=["Future"],
                x=[future_data["fuel_price"]],
                name='Fuel Price',
                orientation='h',
                marker=dict(color='gray'),
                showlegend=False
            ))
            cost_breakdown_fig.add_trace(go.Bar(
                y=["Future"],
                x=[future_data["maintenance"]],
                name='Maintenance',
                orientation='h',
                marker=dict(color='#FF7F0E'),
                showlegend=False
            ))
            cost_breakdown_fig.add_trace(go.Bar(
                y=["Future"],
                x=[future_data["eu_ets"]],
                name='EU ETS',
                orientation='h',
                marker=dict(color='#2CA02C'),
                showlegend=False
            ))
            cost_breakdown_fig.add_trace(go.Bar(
                y=["Future"],
                x=[future_data["penalty"]],
                name='Penalty',
                orientation='h',
                marker=dict(color='#D62728'),
                showlegend=False
            ))
            barmode = 'group'
        else:
            cb_year = cost_breakdown_entry["year"]
            recent_data = cost_breakdown_entry[view_type]
            cost_breakdown_fig = go.Figure()
            cost_breakdown_fig.add_trace(go.Bar(
                y=[f"{view_type.capitalize()} ({cb_year})"],
                x=[recent_data["fuel_price"]],
                name='Fuel Price',
                orientation='h',
                marker=dict(color='gray')
            ))
            cost_breakdown_fig.add_trace(go.Bar(
                y=[f"{view_type.capitalize()} ({cb_year})"],
                x=[recent_data["maintenance"]],
                name='Maintenance',
                orientation='h',
                marker=dict(color='#FF7F0E')
            ))
            cost_breakdown_fig.add_trace(go.Bar(
                y=[f"{view_type.capitalize()} ({cb_year})"],
                x=[recent_data["eu_ets"]],
                name='EU ETS',
                orientation='h',
                marker=dict(color='#2CA02C')
            ))
            cost_breakdown_fig.add_trace(go.Bar(
                y=[f"{view_type.capitalize()} ({cb_year})"],
                x=[recent_data["penalty"]],
                name='Penalty',
                orientation='h',
                marker=dict(color='#D62728')
            ))
            barmode = 'stack'
        
        cost_breakdown_fig.update_layout(
            barmode=barmode,
            title=f'Cost Breakdown for {cb_year}',
            xaxis=dict(title='Cost (€)'),
            yaxis=dict(title=''),
            template='plotly_white',
            margin=dict(l=40, r=40, t=60, b=40),
            height=350
        )
        
        # ----- Chart: EU ETS Impact -----
        eu_ets_fig = go.Figure()
        if view_type == "both":
            if max(current_eu_ets) == 0 and max(future_eu_ets) == 0:
                eu_ets_fig.add_annotation(
                    text="No EU ETS impact for selected years.",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16, color="grey")
                )
            else:
                eu_ets_fig.add_trace(go.Bar(
                    x=years, y=current_eu_ets, name='Current EU ETS',
                    marker_color='#FF7F0E'
                ))
                eu_ets_fig.add_trace(go.Bar(
                    x=years, y=future_eu_ets, name='Future EU ETS',
                    marker_color='#1F77B4'
                ))
        else:
            if max(eu_ets_values) == 0:
                eu_ets_fig.add_annotation(
                    text="No EU ETS impact for selected years.",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16, color="grey")
                )
            else:
                color_choice = '#1F77B4' if view_type == 'future' else '#FF7F0E'
                name_label   = 'Future EU ETS' if view_type == 'future' else 'Current EU ETS'
                eu_ets_fig.add_trace(go.Bar(
                    x=years, y=eu_ets_values, name=name_label,
                    marker_color=color_choice
                ))
        eu_ets_fig.update_layout(
            xaxis_title='Year',
            yaxis_title='EU ETS (€)',
            template='plotly_white',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=40, t=40, b=40),
            height=350
        )
        
        # ----- Build Metrics Table -----
        headers = ["Year", "Blend %"]
        table_data = []
        if view_type == "both":
            headers.extend(["Current OPEX", "Future OPEX", "Savings"])
            for entry in filtered_data:
                current_opex_val = entry["current"]["opex"]
                future_opex_val = entry["future"]["opex"]
                savings = current_opex_val - future_opex_val
                table_data.append({
                    "Year": entry["year"],
                    "Blend %": f"{entry['blend_percentage'] * 100:.1f}%",
                    "Current OPEX": f"€{current_opex_val:,.2f}",
                    "Future OPEX": f"€{future_opex_val:,.2f}",
                    "Savings": f"€{savings:,.2f}"
                })
        else:
            view_prefix = "Future " if view_type == "future" else "Current "
            headers.extend([f"{view_prefix}OPEX", f"{view_prefix}Compliance", f"{view_prefix}EU ETS", f"{view_prefix}Penalty"])
            for entry in filtered_data:
                dv = entry[view_type]
                table_data.append({
                    "Year": entry["year"],
                    "Blend %": f"{entry['blend_percentage'] * 100:.1f}%",
                    f"{view_prefix}OPEX": f"€{dv['opex']:,.2f}",
                    f"{view_prefix}Compliance": f"€{dv['compliance_balance']:,.2f}",
                    f"{view_prefix}EU ETS": f"€{dv['eu_ets']:,.2f}",
                    f"{view_prefix}Penalty": f"€{dv['penalty']:,.2f}"
                })
        
        metrics_table = dash_table.DataTable(
            id='dashboard-data-table',
            columns=[{"name": col, "id": col} for col in headers],
            data=table_data,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'right',
                'padding': '12px',
                'minWidth': '100px'
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            style_data_conditional=[
                {'if': {'column_id': 'Year'}, 'textAlign': 'center'},
                {'if': {'column_id': 'Blend %'}, 'textAlign': 'center'},
                {'if': {'column_id': 'Savings'}, 'color': 'green'}
            ]
        )
        
        formatted_avg_opex = f"€{avg_opex:,.0f}"
        formatted_compliance = f"€{avg_compliance:,.0f}"
        formatted_penalty = f"€{penalty_reduction:,.0f}"
        formatted_blend = f"{avg_blend * 100:.1f}%"
        if view_type == "both" and total_savings is not None:
            formatted_penalty += f" ({total_savings:,.0f} total savings)"
        
        return (
            formatted_avg_opex, 
            opex_trend,
            formatted_compliance, 
            compliance_status,
            formatted_penalty, 
            f"{penalty_percentage:.1f}% reduction",
            formatted_blend, 
            blend_trend,
            opex_fig, 
            compliance_fig, 
            cost_breakdown_fig, 
            eu_ets_fig,
            metrics_table,
            [{"label": str(y), "value": y} for y in unique_years],
            selected_cb_year
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


