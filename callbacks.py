import json
import requests
from urllib.parse import urlencode

import dash
from dash import html, dcc, Input, Output, State, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import config
import plotly.graph_objects as go
import numpy as np
import pages
import pages.power_profiles
import pages.input_module
from pages.input_module import get_vessel_details, DEFAULT_VESSEL, DEFAULT_SCENARIO_FUTURE_AUX_FUEL
from pages.output_module import (
    get_current_output_table,
    get_future_output_table,
    get_opex_comparison_table,
    get_opex_comparison_table_year,
    get_emissions_comparison_table,
    get_emissions_comparison_table_year,
    dashboard_layout,
    cashflow_figure,
    totex_figure,
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
# Dashboard Scenarios: include the new parameter scenario_future_aux_fuel.
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
# Dashboard Scenarios: Include the new parameter scenario_future_aux_fuel.
# -------------------------------------------------------------------------------
def fetch_dashboard_scenarios(vessel_data, future_data):
    vessel_data = merge_vessel_data(vessel_data)
    future_data = future_data or {}
    # Process the scenario value into a list then join as a comma-separated string.
    scenario_list = process_scenario_value(future_data.get("scenario-future-aux-fuel"))
    scenario_str = ",".join(scenario_list)  # Now a single string
    
    params = {
        "vessel_id": vessel_data.get("imo", 11111),
        "main_engine_power_kw": float(vessel_data.get("total_engine_power", 38400)),
        "aux_engine_power_kw": float(vessel_data.get("average_hoteling_kw", 2020)),
        "sailing_engine_load": float(vessel_data.get("sailing_engine_load", 0.5)),
        "working_engine_load": float(vessel_data.get("working_engine_load", 0.3)),
        "shore_engine_load": float(vessel_data.get("shore_engine_load", 0.395)),
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
        # Penalty parameters removed
        "PARASITIC_LOAD_ENGINE": float(future_data.get("parasitic-load", 0.95)),
        "BIOFUELS_BLEND_PERCENTAGE": float(future_data.get("biofuels-blend", 0.3)),
        "shore_enable": str(vessel_data.get("shore_enable", False)).lower(),
        "inflation_rate": float(future_data.get("inflation-rate", 0.02)),
        "npv_rate": float(future_data.get("npv-rate", 0)),
        "CAPEX": float(vessel_data.get("CAPEX", 19772750)),
        "MAIN_ENGINE_SPEED": vessel_data.get("MAIN_ENGINE_SPEED", "MEDIUM"),
        "MAIN_ENGINE_TYPE": vessel_data.get("MAIN_ENGINE_TYPE", "4-STROKE"),
        "AUX_ENGINE_SPEED": vessel_data.get("AUX_ENGINE_SPEED", "MEDIUM"),
        "AUX_ENGINE_TYPE": vessel_data.get("AUX_ENGINE_TYPE", "4-STROKE"),
        "price_conversion": float(vessel_data.get("price_conversion", 1)),
        # Now send a single parameter value that is comma-separated.
        "scenario_future_aux_fuel": scenario_str
    }
    qs = urlencode(params, doseq=True)
    url = f"{config.DASHBOARD_ENDPOINT}?{qs}"
    print(f"Dashboard API URL: {url}")
    try:
        response = requests.get(url, timeout=15)
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
        # Penalty parameters removed
        "BIOFUELS_SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": 3,
        "PARASITIC_LOAD_ENGINE": 0.95,
        "BIOFUELS_BLEND_PERCENTAGE": 0.3,
        "reporting_year": 2030,
        "ENGINE_MAINTENANCE_COSTS_PER_HOUR": 20,
        "SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": 2,
        "SHORE_POWER_MAINTENANCE_PER_DAY": 480.0,
        "SHORE_POWER_SPARES_PER_DAY": 480.0,
        # Penalty parameters removed
        "shore_enable": "false",
        "inflation_rate": 0.02,
        "npv_rate": 0,
        "CAPEX": 19772750,
        "MAIN_ENGINE_SPEED": "MEDIUM",
        "MAIN_ENGINE_TYPE": "4-Stroke",
        "AUX_ENGINE_SPEED": "MEDIUM",
        "AUX_ENGINE_TYPE": "4-Stroke",
        "price_conversion": 1,
        "FUTURE_CO2_REDUCTION": 26
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
            final_params["BIOFUELS_BLEND_PERCENTAGE"] = (blend_value / 100.0 if blend_value > 1 else blend_value)
        except ValueError:
            raise ValueError("Invalid biofuels blend percentage provided.")
    else:
        final_params["BIOFUELS_BLEND_PERCENTAGE"] = float(final_params.get("BIOFUELS_BLEND_PERCENTAGE", 0.3))
    
    if final_params["BIOFUELS_BLEND_PERCENTAGE"] > 1:
        raise ValueError("Biofuel blend percentage cannot exceed 100%")
    
    for key in ["sailing_days", "working_days", "idle_days"]:
        if final_params.get(key, 0) < 0:
            raise ValueError(f"{key} cannot be negative")
    
    qs = urlencode(final_params, doseq=True)
    url = f"{config.FINANCIAL_ENDPOINT}?{qs}"
    print(f"Financial API URL: {url}")
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
        DEFAULT_SCENARIO_FUTURE_AUX_FUEL,
        DEFAULT_FUTURE_CO2_REDUCTION
    )
    vessel_data = merge_vessel_data(vessel_data)
    future_data = future_data or {}
    # Process scenario value into a comma-separated string.
    scenario_list = process_scenario_value(future_data.get("scenario-future-aux-fuel"), DEFAULT_SCENARIO_FUTURE_AUX_FUEL)
    scenario_str = ",".join(scenario_list)
    return (
        future_data.get("future-main-fuel-type", vessel_data.get("future-main-fuel-type", DEFAULT_FUTURE_MAIN_FUEL_TYPE)),
        future_data.get("future-aux-fuel-type", vessel_data.get("future-aux-fuel-type", DEFAULT_FUTURE_AUX_FUEL_TYPE)),
        float(future_data.get("biofuels-spares-cost", vessel_data.get("biofuels-spares-cost", DEFAULT_BIOFUELS_SPARES_COST))),
        float(future_data.get("parasitic-load", vessel_data.get("parasitic-load", DEFAULT_PARASITIC_LOAD))),
        float(future_data.get("biofuels-blend", vessel_data.get("biofuels-blend", DEFAULT_BIOFUELS_BLEND))),
        float(future_data.get("shore-maint-cost", vessel_data.get("shore-maint-cost", DEFAULT_SHORE_MAINT_COST))),
        float(future_data.get("shore-spares-cost", vessel_data.get("shore-spares-cost", DEFAULT_SHORE_SPARES_COST))),
        float(future_data.get("inflation-rate", vessel_data.get("inflation-rate", DEFAULT_INFLATION_RATE))),
        float(future_data.get("npv-rate", vessel_data.get("npv-rate", DEFAULT_NPV_RATE))) / 100.0,
        future_data.get("currency-choice", vessel_data.get("currency-choice", DEFAULT_CURRENCY)),
        scenario_str,
        float(future_data.get("FUTURE-CO2-REDUCTION", vessel_data.get("FUTURE-CO2-REDUCTION", DEFAULT_FUTURE_CO2_REDUCTION)))
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
            return (current_data or config.DEFAULT_VESSEL,
                    "Please enter a search term.")
        vessel_data = get_vessel_details(search_term, search_type)
        return vessel_data, f"Found vessel: {vessel_data.get('vessel_name', 'Unknown')}"
    
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
            vessel_data.get('year_built', config.DEFAULT_VESSEL["year_built"]),
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
         Output('currency-choice', 'value'),
         Output('scenario-future-aux-fuel', 'value'),
         Output('FUTURE-CO2-REDUCTION', 'value')],
        [Input('vessel-data-store', 'data'),
         Input('future-data-store', 'data')],
        prevent_initial_call=True
    )
    def update_future_inputs(vessel_data, future_data):
        return update_future_inputs_callback(vessel_data, future_data)
    
    @app.callback(
        [Output('api-data-store', 'data'),
         Output('dashboard-scenarios-store', 'data'),
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
            State('scenario-future-aux-fuel', 'value'),
            State('FUTURE-CO2-REDUCTION', 'value'),
            State('currency-choice', 'value')
        ],
        prevent_initial_call=True
    )
    def update_financial_data(n_clicks, *values):
        if n_clicks is None:
            return no_update, no_update, "input", no_update
        
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
            existing_future_data, scenario_future_aux_fuel, FUTURE_CO2_REDUCTION,
            currency_choice
        ) = values
        
        if not all([main_power, aux_power, main_fuel_type, aux_fuel_type]):
            return no_update, no_update, "input", no_update
        
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
            "scenario-future-aux-fuel": scenario_future_aux_fuel,
            "FUTURE-CO2-REDUCTION": FUTURE_CO2_REDUCTION,
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
        
        # Build Financial API parameters WITHOUT scenario_future_aux_fuel
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
            "sailing_engine_load": float(sailing_engine_load),
            "working_engine_load": float(working_engine_load),
            "shore_engine_load": float(shore_engine_load),
            "reporting_year": int(reporting_year),
            "ENGINE_MAINTENANCE_COSTS_PER_HOUR": float(engine_maint_cost),
            "SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": float(spares_cost),
            "SHORE_POWER_MAINTENANCE_PER_DAY": float(shore_maint_cost),
            "SHORE_POWER_SPARES_PER_DAY": float(shore_spares_cost),
            "BIOFUELS_SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": float(biofuels_spares_cost),
            "PARASITIC_LOAD_ENGINE": float(parasitic_load),
            "BIOFUELS_BLEND_PERCENTAGE": blend_value,
            "shore_enable": shore_enable_bool,
            "inflation_rate": float(inflation_rate) if inflation_rate else 0.02,
            "npv_rate": float(npv_rate) / 100.0,
            "CAPEX": float(capex),
            "MAIN_ENGINE_SPEED": main_engine_speed,
            "MAIN_ENGINE_TYPE": main_engine_type,
            "AUX_ENGINE_SPEED": aux_engine_speed,
            "AUX_ENGINE_TYPE": aux_engine_type,
            "price_conversion": price_conversion,
            "FUTURE_CO2_REDUCTION": float(FUTURE_CO2_REDUCTION) / 100
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
        
        # Dashboard API call uses updated_future_data (which includes scenario)
        dashboard_data = fetch_dashboard_scenarios(vessel_data or config.DEFAULT_VESSEL, updated_future_data or {})
        return financial_data, dashboard_data, "output", updated_future_data
    
    @app.callback(
        [Output("cashflow-graph", "figure"),
         Output("totex-vertical-graph", "figure"),
         Output("totex-horizontal-graph", "figure"),
         Output("dwelling-pie-chart", "figure"),
         Output("scenario-filter", "options"),
         Output("scenario-filter", "value")],
        Input("dashboard-scenarios-store", "data")
    )
    def update_financial_metrics(dashboard_data):
        if not dashboard_data:
            raise no_update
        cashflow = cashflow_figure(dashboard_data)
        totex_vert = totex_figure(dashboard_data)
        totex_horiz = pages.power_profiles.totex_horizontal_figure(dashboard_data)
        dwelling = pages.power_profiles.dwelling_at_berth_pie_figure()
        _, scenarios = pages.power_profiles.load_totex_scenarios(dashboard_data)
        scenario_options = [{"label": k, "value": k} for k in scenarios.keys()]
        default_scenarios = list(scenarios.keys())[:3]
        return cashflow, totex_vert, totex_horiz, dwelling, scenario_options, default_scenarios
    
    @app.callback(
        Output("metric-comparison-chart", "figure"),
        [Input("metric-dropdown", "value"),
         Input("year-range-slider", "value"),
         Input("scenario-filter", "value"),
         Input("dashboard-scenarios-store", "data")]
    )
    def update_metric_comparison(metric, year_range, scenarios, dashboard_data):
        if not all([metric, year_range, scenarios, dashboard_data]):
            raise no_update
        return pages.power_profiles.generate_metric_figure(metric, year_range, scenarios, dashboard_data)
    
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
        Output("detail-power-profile-chart", "figure"),
        [Input("detail-peak-power", "value"),
         Input("detail-base-load", "value")]
    )
    def update_power_profile_chart(peak_power, base_load):
        if not peak_power or not base_load:
            peak_power = 25000
            base_load = 40
        x, y = pages.power_profiles.generate_load_profile(peak_power, base_load)
        fig = go.Figure(data=go.Scatter(x=x, y=y, mode='lines', name="Load Profile"))
        pages.power_profiles.set_figure_layout(fig, "Daily Load Profile", "Hour", "Power (kW)")
        return fig
    
    @app.callback(
        Output('energy-demand-chart', 'figure'),
        [Input('detail-peak-power', 'value'),
         Input('detail-base-load', 'value')]
    )
    def update_energy_demand_chart(peak_power, base_load_percent):
        if peak_power is None or base_load_percent is None:
            return go.Figure(layout={"title": "No Data Available", "xaxis_title": "Hour", "yaxis_title": "Energy Demand (kW)"})
        fig = pages.power_profiles.projected_energy_demand_figure()
        return fig
    
    @app.callback(
        Output("dashboard-charts-container", "children"),
        [Input("dashboard-chart-selector", "value"),
         Input("dashboard-scenarios-store", "data")]
    )
    def update_dashboard_charts(selected_charts, dashboard_data):
        charts = []
        if not dashboard_data:
            dashboard_data = {}
        years_data, processed_scenarios = pages.power_profiles.load_totex_scenarios(dashboard_data) if dashboard_data else ([], {})
        if "dwelling" in selected_charts:
            charts.append(
                card_component("Dwelling at Berth - Biofuel Blend Minimum",
                               dcc.Graph(figure=pages.power_profiles.dwelling_at_berth_pie_figure(), className="chart-container"))
            )
        if "npv" in selected_charts:
            fig = go.Figure()
            for label, sc in processed_scenarios.items():
                if "NPV" in sc and len(sc["NPV"]) == len(years_data):
                    fig.add_trace(go.Scatter(x=years_data, y=sc["NPV"], mode="lines", name=label))
            pages.power_profiles.set_figure_layout(fig, "NPV Comparison", "Year", "NPV (£)")
            fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
            charts.append(card_component("NPV Comparison", dcc.Graph(figure=fig, className="chart-container")))
        if "result" in selected_charts:
            fig = go.Figure()
            for label, sc in processed_scenarios.items():
                if "Result" in sc and len(sc["Result"]) == len(years_data):
                    fig.add_trace(go.Scatter(x=years_data, y=sc["Result"], mode="lines", name=label))
            pages.power_profiles.set_figure_layout(fig, "Result Comparison", "Year", "Result (£)")
            fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
            charts.append(card_component("Result Comparison", dcc.Graph(figure=fig, className="chart-container")))
        if "cumulative" in selected_charts:
            fig = go.Figure()
            for label, sc in processed_scenarios.items():
                if "Cumulative" in sc and len(sc["Cumulative"]) == len(years_data):
                    fig.add_trace(go.Scatter(x=years_data, y=sc["Cumulative"], mode="lines", name=label))
            pages.power_profiles.set_figure_layout(fig, "Cumulative Comparison", "Year", "Cumulative (£)")
            fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
            charts.append(card_component("Cumulative Comparison", dcc.Graph(figure=fig, className="chart-container")))
        if "cashflow" in selected_charts:
            charts.append(
                card_component("Cashflow Analysis", 
                               dcc.Graph(figure=pages.power_profiles.cashflow_figure(dashboard_data), className="chart-container"))
            )
        if "totex" in selected_charts:
            charts.append(
                card_component("TOTEX Comparison", 
                               dcc.Graph(figure=pages.power_profiles.totex_figure(dashboard_data), className="chart-container"))
            )
        return charts
    
    @app.callback(
        Output("output-content", "children"),
        [
            Input("api-data-store", "data"),
            Input("future-data-store", "data"),
            Input("table-selection-dropdown", "value"),
            Input("timeframe-toggle", "value")  # New input for day/year toggle
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
        
        # Use the currency from future data if available, else default to EUR
        currency = (future_data or {}).get("currency-choice", "EUR")
        conv_factor = config.CURRENCIES.get(currency, {}).get("conversion", 1.0)
        sections = []
        
        # Current Output Table remains the same
        if 'current' in selected_tables:
            sections.append(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H4("Current Output Table")),
                        dbc.CardBody(get_current_output_table(api_data, conv_factor))
                    ],
                    className="mb-4"
                )
            )
        
        # Future Output Table remains the same
        if 'future' in selected_tables:
            sections.append(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H4("Future Output Table")),
                        dbc.CardBody(get_future_output_table(api_data, conv_factor))
                    ],
                    className="mb-4"
                )
            )
        
        # For OPEX Comparison, choose daily or yearly based on the toggle
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
        
        # For Emissions Comparison, choose daily or yearly based on the toggle
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
        
        # Dashboard content (if any)
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


