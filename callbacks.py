import json
import requests
from urllib.parse import urlencode

import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import config
import plotly.graph_objects as go
import numpy as np

# =============================================================================
# GLOBAL STYLES & CONSTANTS
# =============================================================================
HEADER_STYLE = {"backgroundColor": "#0A4B8C", "padding": "10px"}
HEADER_TEXT_STYLE = {"color": "white", "margin": "0"}
MARGIN_STYLE = dict(l=60, r=30, t=60, b=50)
TEMPLATE_STYLE = "plotly_white"

from pages.output_module import (
    get_current_output_table,
    get_future_output_table,
    get_opex_comparison_table,
    get_emissions_comparison_table,
    dashboard_layout,
    cashflow_figure,
    totex_figure,
    engine_power_profile_figure,
    energy_demand_figure,
    spares_figure
)

def card_component(title, children):
    """Return a styled Bootstrap card component."""
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

###########################################################################
# API CALL HELPER FUNCTION
###########################################################################
def get_financial_data(input_params=None, vessel_data_override=None):
    """
    Retrieve financial data from the external API.
    
    Parameters:
        input_params (dict): Additional input parameters.
        vessel_data_override (dict): Vessel details to override defaults.
    
    Returns:
        dict: JSON response from the API or an empty dict if an error occurs.
    """
    fallback_defaults = {
        "main_engine_power_kw": 38400,
        "aux_engine_power_kw": 2020,
        "sailing_engine_load": 0.5,
        "working_engine_load": 0.3,
        "shore_engine_load": 0.395,
        "sailing_days": 199,
        "working_days": 40,
        "idle_days": 126,
        "shore_days": 0,
        "shore_port": 1,
        "main_fuel_type": "MDO",
        "aux_fuel_type": "MDO",
        "future_main_fuel_type": "Diesel-Bio-diesel",
        "future_aux_fuel_type": "Diesel-Bio-diesel",
        "reporting_year": 2030,
        "ENGINE_MAINTENANCE_COSTS_PER_HOUR": 20,
        "SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": 2,
        "SHORE_POWER_MAINTENANCE_PER_DAY": 45.486,
        "SHORE_POWER_SPARES_PER_DAY": 45.486,
        "BIOFUELS_SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": 3,
        "FUELEU_CURRENT_PENALTY_PER_YEAR": 729348.5444,
        "FUELEU_FUTURE_PENALTY_PER_YEAR": 0,
        "PARASITIC_LOAD_ENGINE": 0.95,
        "BIOFUELS_BLEND_PERCENTAGE": 0.3,
        "shore_enable": "false",
        "inflation_rate": 0.02,
        "npv_rate": 0,
        "CAPEX": 19772750,
        "MAIN_ENGINE_SPEED": "MEDIUM",
        "MAIN_ENGINE_TYPE": "4-STROKE",
        "AUX_ENGINE_SPEED": "MEDIUM",
        "AUX_ENGINE_TYPE": "4-STROKE",
    }

    vessel_data = vessel_data_override or config.DEFAULT_VESSEL
    vessel_overrides = {
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

    # Ensure shore_enable is a lowercase string
    final_params["shore_enable"] = str(final_params.get("shore_enable", False)).lower()

    # Process biofuels blend percentage
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

    # Validate day counts
    for key in ["sailing_days", "working_days", "idle_days"]:
        if final_params.get(key, 0) < 0:
            raise ValueError(f"{key} cannot be negative")

    qs = urlencode(final_params, doseq=True)
    url = f"{config.FINANCIAL_ENDPOINT}?{qs}"
    print(f"Final API URL: {url}")

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        print(f"API Response: {json.dumps(data, indent=2)}")
        return data
    except Exception as e:
        print(f"API Error: {str(e)}")
        return {}


def process_financial_results(api_data):
    """
    Process API data by merging current and future timeseries information.
    
    Parameters:
        api_data (dict): The API response data.
    
    Returns:
        list: Processed list of yearly results.
    """
    results = api_data.get("result", [])
    current_ts = api_data.get("current_timeseries", [])
    future_ts = api_data.get("future_timeseries", [])
    processed = []
    for res in results:
        year = res.get("year")
        current_data = next((ts for ts in current_ts if ts.get("year") == year), {})
        future_data = next((ts for ts in future_ts if ts.get("year") == year), {})
        processed.append({
            "year": year,
            "npv": res.get("npv", 0),
            "cumulative": res.get("cumulative", 0),
            "yearly_result": res.get("result", 0),
            "current_opex": current_data.get("current_opex", 0),
            "future_opex": future_data.get("future_opex", 0),
            "current_penalty": current_data.get("current_penalty", 0),
            "future_penalty": future_data.get("future_penalty", 0),
            "fuel_current": abs(current_data.get("total_fuel_current_inflated", 0)),
            "fuel_future": abs(future_data.get("total_fuel_future_inflated", 0)),
            "maintenance_current": current_data.get("total_maintenance_current_inflated", 0),
            "maintenance_future": future_data.get("total_maintenance_future_inflated", 0),
            "spare_current": current_data.get("total_spare_current_inflated", 0),
        })
    return processed


###########################################################################
# REGISTER CALLBACKS
###########################################################################
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
            return (current_data if current_data is not None else config.DEFAULT_VESSEL,
                    "Please enter a search term.")
        from pages.input_module import get_vessel_details
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
        if not vessel_data:
            vessel_data = config.DEFAULT_VESSEL
        return (
            vessel_data.get('vessel_name', config.DEFAULT_VESSEL["vessel_name"]),
            vessel_data.get('imo', config.DEFAULT_VESSEL["imo"]),
            vessel_data.get('vessel_category', config.DEFAULT_VESSEL["vessel_category"]),
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
        if not vessel_data:
            vessel_data = config.DEFAULT_VESSEL
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
        Output('spares-cost', 'value'),
        Output('fueleu-penalty', 'value')],
        Input('vessel-data-store', 'data'),
        prevent_initial_call=True
    )
    def update_operational_and_maintenance_inputs(vessel_data):
        from pages.input_module import DEFAULT_VESSEL
        # Merge fetched vessel details with defaults so that dynamic values override defaults.
        if not vessel_data:
            vessel_data = DEFAULT_VESSEL
        else:
            vessel_data = {**DEFAULT_VESSEL, **vessel_data}
        return (
            vessel_data.get('sailing_days', 199),
            vessel_data.get('working_days', 40),
            vessel_data.get('idle_days', 126),
            vessel_data.get('shore_days', 0),
            vessel_data.get('sailing_engine_load', 0.5),  # Already a percentage (e.g. 50)
            vessel_data.get('working_engine_load', 0.3),   # (e.g. 30)
            vessel_data.get('shore_engine_load', 0.4),     # (e.g. 39.5)
            vessel_data.get('ENGINE_MAINTENANCE_COSTS_PER_HOUR', 20),
            vessel_data.get('SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR', 2),
            vessel_data.get('FUELEU_CURRENT_PENALTY_PER_YEAR', 729348.5444)
        )


    @app.callback(
        [Output('api-data-store', 'data'),
        Output('tab-switch', 'data')],
        Input('calculate-button', 'n_clicks'),
        [State('main-power', 'value'),
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
        State('fueleu-penalty', 'value'),
        State('future-main-fuel-type', 'value'),
        State('future-aux-fuel-type', 'value'),
        State('biofuels-spares-cost', 'value'),
        State('fueleu-future-penalty', 'value'),
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
        State('vessel-data-store', 'data')],
        prevent_initial_call=True
    )
    def update_emissions_data_callback(
        n_clicks, main_power, aux_power, main_fuel_type, aux_fuel_type,
        sailing_days, working_days, idle_days, shore_days,
        sailing_engine_load, working_engine_load, shore_engine_load,
        engine_maint_cost, spares_cost, fueleu_penalty,
        future_main_fuel_type, future_aux_fuel_type, biofuels_spares_cost,
        fueleu_future_penalty, parasitic_load, biofuels_blend,
        shore_maint_cost, shore_spares_cost,
        shore_enable, npv_rate, capex,
        shore_port, reporting_year, inflation_rate,
        main_engine_speed, main_engine_type,
        aux_engine_speed, aux_engine_type,
        vessel_data
    ):
        if n_clicks is None or not all([main_power, aux_power, main_fuel_type, aux_fuel_type]):
            return None, "input"

        shore_enable_bool = str(shore_enable).strip().lower() in ["yes", "true"]

        params = {
            "main_engine_power_kw": float(main_power),
            "aux_engine_power_kw": float(aux_power),
            # Convert engine loads from percentage to fraction (0-1)
            "sailing_engine_load": float(sailing_engine_load),
            "working_engine_load": float(working_engine_load),
            "shore_engine_load": float(shore_engine_load),
            "sailing_days": int(sailing_days),
            "working_days": int(working_days),
            "idle_days": int(idle_days),
            "shore_days": int(shore_days),
            "shore_port": int(shore_port),
            "main_fuel_type": main_fuel_type,
            "aux_fuel_type": aux_fuel_type,
            "future_main_fuel_type": future_main_fuel_type,
            "future_aux_fuel_type": future_aux_fuel_type,
            "reporting_year": int(reporting_year),
            "ENGINE_MAINTENANCE_COSTS_PER_HOUR": float(engine_maint_cost),
            "SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": float(spares_cost),
            "SHORE_POWER_MAINTENANCE_PER_DAY": float(shore_maint_cost),
            "SHORE_POWER_SPARES_PER_DAY": float(shore_spares_cost),
            "BIOFUELS_SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": float(biofuels_spares_cost),
            "FUELEU_CURRENT_PENALTY_PER_YEAR": float(fueleu_penalty),
            "FUELEU_FUTURE_PENALTY_PER_YEAR": float(fueleu_future_penalty),
            "PARASITIC_LOAD_ENGINE": float(parasitic_load),
            # Convert biofuels blend from percentage to fraction
            "BIOFUELS_BLEND_PERCENTAGE": float(biofuels_blend) / 100.0,
            "shore_enable": shore_enable_bool,
            "inflation_rate": (float(inflation_rate) / 100.0) if inflation_rate else 0.02,
            "npv_rate": float(npv_rate) / 100.0,
            "CAPEX": float(capex),
            "MAIN_ENGINE_SPEED": main_engine_speed,
            "MAIN_ENGINE_TYPE": main_engine_type,
            "AUX_ENGINE_SPEED": aux_engine_speed,
            "AUX_ENGINE_TYPE": aux_engine_type,
        }

        financial_data = get_financial_data(params, vessel_data_override=vessel_data)
        if financial_data:
            return financial_data, "output"
        else:
            return None, "input"


    @app.callback(
        Output("output-content", "children"),
        [Input("api-data-store", "data"),
         Input("currency-choice", "value"),
         Input("table-selection-dropdown", "value")]
    )
    def display_emissions_output(api_data, currency, selected_tables):
        if not api_data:
            return html.Div(
                dbc.Alert(
                    "No data available. Please calculate emissions and costs first.",
                    color="warning"
                ),
                className="mt-4"
            )
        if not selected_tables:
            return html.Div(
                dbc.Alert("Please select at least one table to display.", color="info"),
                className="mt-4"
            )

        conv_factor = config.CURRENCIES.get(currency, {}).get("conversion", 1.0)
        sections = []

        from pages.output_module import (
            get_current_output_table,
            get_future_output_table,
            get_opex_comparison_table,
            get_emissions_comparison_table,
            dashboard_layout
        )

        if 'current' in selected_tables:
            sections.append(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H4("Current Output Table")),
                        dbc.CardBody(get_current_output_table(api_data, conv_factor, currency))
                    ],
                    className="mb-4"
                )
            )
        if 'future' in selected_tables:
            sections.append(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H4("Future Output Table")),
                        dbc.CardBody(get_future_output_table(api_data, conv_factor, currency))
                    ],
                    className="mb-4"
                )
            )
        if 'opex' in selected_tables:
            sections.append(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H4("OPEX Comparison")),
                        dbc.CardBody(get_opex_comparison_table(api_data, currency, conv_factor))
                    ],
                    className="mb-4"
                )
            )
        if 'emissions' in selected_tables:
            sections.append(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H4("Emissions Comparison")),
                        dbc.CardBody(get_emissions_comparison_table(api_data))
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
