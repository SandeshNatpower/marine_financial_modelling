# callbacks.py

import json
import requests
from urllib.parse import urlencode
import dash
from dash import html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import config
import plotly.graph_objects as go
import numpy as np

# Import only helper functions from power_profiles.py (no callbacks there)
from pages import power_profiles

# Shared UI component: a card builder used by callbacks and layout
def card_component(title, children):
    return dbc.Card([
        dbc.CardHeader(
            html.H4(title, className="card-title mb-0", style=power_profiles.HEADER_TEXT_STYLE),
            style=power_profiles.HEADER_STYLE
        ),
        dbc.CardBody(children)
    ], className="mb-4 shadow-sm rounded")

###########################################################################
# API CALL HELPER FUNCTION
###########################################################################


def get_financial_data(input_params=None, vessel_data_override=None):
    """
    Retrieve financial data from the API using a combination of default parameters,
    vessel data overrides, and direct input parameters. Precedence is as follows:
      fallback_defaults < vessel_data < input_params.
    """
    # 1. Define fallback defaults matching the API's expected parameter names.
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
        "future_main_fuel_type": "Diesel-Bio-diesel",  # Future fuel defaults
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
        "BIOFUELS_BLEND_PERCENTAGE": 0.3,  # Expected as fraction (e.g., 0.3 means 30%)
        "shore_enable": "false",         # API expects a lowercase string
        "inflation_rate": 0.02,
        "npv_rate": 0,
        "CAPEX": 19772750
    }

    # 2. Get vessel data from the override if provided; otherwise, use the default from config.
    vessel_data = vessel_data_override or config.DEFAULT_VESSEL

    # 3. Map vessel data to API parameters (overrides)
    vessel_overrides = {
        "main_engine_power_kw": vessel_data.get("total_engine_power", fallback_defaults["main_engine_power_kw"]),
        "aux_engine_power_kw": vessel_data.get("average_hoteling_kw", fallback_defaults["aux_engine_power_kw"]),
        "main_fuel_type": vessel_data.get("main_fuel_type", fallback_defaults["main_fuel_type"]),
        "aux_fuel_type": vessel_data.get("aux_fuel_type", fallback_defaults["aux_fuel_type"]),
        "reporting_year": vessel_data.get("reporting_year", fallback_defaults["reporting_year"])
    }

    # 4. Combine parameters in order: fallback_defaults < vessel_overrides < input_params.
    final_params = fallback_defaults.copy()
    final_params.update(vessel_overrides)
    if input_params:
        final_params.update(input_params)

    # 5. Process and validate specific parameters.
    # Ensure 'shore_enable' is a lowercase string.
    final_params["shore_enable"] = str(final_params.get("shore_enable", False)).lower()

    # Convert and validate biofuels blend percentage.
    # If 'biofuels_blend' is provided in input_params, convert it (assume percentage if > 1).
    if input_params and "biofuels_blend" in input_params:
        try:
            blend_value = float(input_params["biofuels_blend"])
            final_params["BIOFUELS_BLEND_PERCENTAGE"] = blend_value / 100.0 if blend_value > 1 else blend_value
        except ValueError:
            raise ValueError("Invalid biofuels blend percentage provided.")
    else:
        # Ensure default is float.
        final_params["BIOFUELS_BLEND_PERCENTAGE"] = float(final_params.get("BIOFUELS_BLEND_PERCENTAGE", 0.3))

    # Validate that biofuel blend does not exceed 100% (i.e. a fraction > 1).
    if final_params["BIOFUELS_BLEND_PERCENTAGE"] > 1:
        raise ValueError("Biofuel blend percentage cannot exceed 100%")

    # Validate that operational days are non-negative.
    for key in ["sailing_days", "working_days", "idle_days"]:
        if final_params.get(key, 0) < 0:
            raise ValueError(f"{key} cannot be negative")

    # 6. Build the query string and construct the API URL.
    qs = urlencode(final_params, doseq=True)
    url = f"{config.FINANCIAL_ENDPOINT}?{qs}"
    print(f"Final API URL: {url}")

    # 7. Make the API request.
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
    Process the API response data by merging the main results with their corresponding 
    current and future timeseries data.
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
            "spare_current": current_data.get("total_spare_current_inflated", 0)
        })
    return processed




###########################################################################
# REGISTER ALL DASH CALLBACKS
###########################################################################
def register_callbacks(app):
    """Registers all Dash callbacks for the application."""

    # Callback: Update Vessel Data from Search
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
            return current_data if current_data is not None else config.DEFAULT_VESSEL, "Please enter a search term."
        # Assume get_vessel_details is available from pages.input_module
        from pages.input_module import get_vessel_details
        vessel_data = get_vessel_details(search_term, search_type)
        return vessel_data, f"Found vessel: {vessel_data.get('vessel_name', 'Unknown')}"

    # Callback: Populate Vessel Detail Fields (read-only)
    @app.callback(
        [
            Output('vessel-name', 'value'),
            Output('imo-number', 'value'),
            Output('vessel-category', 'value'),
            Output('gross-tonnage', 'value'),
            Output('year-built', 'value'),
            Output('dwt', 'value')
        ],
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

    # Callback: Update Technical Specifications
    @app.callback(
        [
            Output('main-power', 'value'),
            Output('aux-power', 'value'),
            Output('main-engine-type', 'value'),
            Output('aux-engine-type', 'value'),
            Output('main-fuel-type', 'value'),
            Output('aux-fuel-type', 'value')
        ],
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
            vessel_data.get("main_engine_type", "Unknown"),
            vessel_data.get("aux_engine_type", "Unknown"),
            vessel_data.get("main_fuel_type", "MDO"),
            vessel_data.get("aux_fuel_type", "MDO")
        )

    # Callback: Update Vessel Image and Type Display
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

    # Callback: Update Operational & Maintenance Inputs
    @app.callback(
        [
            Output('sailing-days', 'value'),
            Output('working-days', 'value'),
            Output('idle-days', 'value'),
            Output('shore-days', 'value'),
            Output('sailing-engine-load', 'value'),
            Output('working-engine-load', 'value'),
            Output('shore-engine-load', 'value'),
            Output('engine-maint-cost', 'value'),
            Output('spares-cost', 'value'),
            Output('fueleu-penalty', 'value')
        ],
        Input('vessel-data-store', 'data'),
        prevent_initial_call=True
    )
    def update_operational_and_maintenance_inputs(vessel_data):
        if not vessel_data:
            vessel_data = config.DEFAULT_VESSEL
        return (
            vessel_data.get('sailing_days', 199),
            vessel_data.get('working_days', 40),
            vessel_data.get('idle_days', 126),
            vessel_data.get('shore_days', 0),
            vessel_data.get('sailing_engine_load', 0.5) * 100,
            vessel_data.get('working_engine_load', 0.3) * 100,
            vessel_data.get('shore_engine_load', 0.395) * 100,
            vessel_data.get('ENGINE_MAINTENANCE_COSTS_PER_HOUR', 20),
            vessel_data.get('SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR', 2),
            vessel_data.get('FUELEU_CURRENT_PENALTY_PER_YEAR', 729348.5444)
        )

    # Callback: Calculate Emissions and Switch to Output View
    @app.callback(
        [Output('emissions-data-store', 'data'),
        Output('tab-switch', 'data')],
        Input('calculate-button', 'n_clicks'),
        [
            # Existing States
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
            # Add missing States
            State('shore-port', 'value'),          # Added
            State('reporting-year', 'value'),       # Added
            State('inflation-rate', 'value'),       # Added
            State('vessel-data-store', 'data')
        ],
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
        shore_port, reporting_year, inflation_rate,  # Added parameters
        vessel_data
    ):
        if n_clicks is None or not all([main_power, aux_power, main_fuel_type, aux_fuel_type]):
            return None, "input"
        
        # Handle boolean conversion for shore_enable
        shore_enable_bool = str(shore_enable).strip().lower() in ["yes", "true"]
        
        # Prepare parameters for API call
        params = {
            "main_engine_power_kw": float(main_power),
            "aux_engine_power_kw": float(aux_power),
            "sailing_engine_load": float(sailing_engine_load) / 100.0,
            "working_engine_load": float(working_engine_load) / 100.0,
            "shore_engine_load": float(shore_engine_load) / 100.0,
            "sailing_days": int(sailing_days),
            "working_days": int(working_days),
            "idle_days": int(idle_days),
            "shore_days": int(shore_days),
            "shore_port": int(shore_port),  # From State
            "main_fuel_type": main_fuel_type,
            "aux_fuel_type": aux_fuel_type,
            "future_main_fuel_type": future_main_fuel_type,
            "future_aux_fuel_type": future_aux_fuel_type,
            "reporting_year": int(reporting_year),  # From State
            "ENGINE_MAINTENANCE_COSTS_PER_HOUR": float(engine_maint_cost),
            "SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": float(spares_cost),
            "SHORE_POWER_MAINTENANCE_PER_DAY": float(shore_maint_cost),
            "SHORE_POWER_SPARES_PER_DAY": float(shore_spares_cost),
            "BIOFUELS_SPARES_CONSUMABLES_COSTS_PER_ENGINE_HOUR": float(biofuels_spares_cost),
            "FUELEU_CURRENT_PENALTY_PER_YEAR": float(fueleu_penalty),
            "FUELEU_FUTURE_PENALTY_PER_YEAR": float(fueleu_future_penalty),
            "PARASITIC_LOAD_ENGINE": float(parasitic_load),
            "BIOFUELS_BLEND_PERCENTAGE": float(biofuels_blend) / 100.0,
            "shore_enable": shore_enable_bool,
            "inflation_rate": (float(inflation_rate) / 100.0) if inflation_rate else 0.02,
            "npv_rate": float(npv_rate) / 100.0,
            "CAPEX": float(capex)
        }
        
        # Fetch financial data using updated parameters
        financial_data = get_financial_data(params, vessel_data_override=vessel_data)
        
        if financial_data:
            return financial_data, "output"
        else:
            return None, "input"

    # Callback: Display Emissions Output Tables
    @app.callback(
        Output("output-content", "children"),
        [Input("emissions-data-store", "data"),
         Input("currency-choice", "value"),
         Input("table-selection-dropdown", "value")]
    )
    def display_emissions_output(api_data, currency, selected_tables):
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
        conv_factor = config.CURRENCIES.get(currency, {}).get("conversion", 1.0)
        tables = []
        from pages.output_module import (
            get_current_output_table,
            get_future_output_table,
            get_opex_comparison_table,
            get_emissions_comparison_table,
            format_currency_value,
            create_processed_results_table
        )
        if 'current' in selected_tables:
            tables.append(
                dbc.Card([
                    dbc.CardHeader(html.H4("Current Output Table")),
                    dbc.CardBody(get_current_output_table(api_data, conv_factor, currency))
                ], className="mb-4")
            )
        if 'future' in selected_tables:
            tables.append(
                dbc.Card([
                    dbc.CardHeader(html.H4("Future Output Table")),
                    dbc.CardBody(get_future_output_table(api_data, conv_factor, currency))
                ], className="mb-4")
            )
        if 'opex' in selected_tables:
            tables.append(
                dbc.Card([
                    dbc.CardHeader(html.H4("OPEX Comparison")),
                    dbc.CardBody(get_opex_comparison_table(api_data, currency, conv_factor))
                ], className="mb-4")
            )
        if 'emissions' in selected_tables:
            tables.append(
                dbc.Card([
                    dbc.CardHeader(html.H4("Emissions Comparison")),
                    dbc.CardBody(get_emissions_comparison_table(api_data))
                ], className="mb-4")
            )
        processed_results = process_financial_results(api_data)
        if processed_results:
            summary_table = create_processed_results_table(processed_results, conv_factor, currency)
            tables.append(
                dbc.Card([
                    dbc.CardHeader(html.H4("Financial Results Summary")),
                    dbc.CardBody(summary_table)
                ], className="mb-4")
            )
        return html.Div(tables)

    # Callback: Update Metric Comparison Chart
    @app.callback(
        Output("metric-comparison-chart", "figure"),
        [Input("metric-dropdown", "value"),
         Input("year-range-slider", "value"),
         Input("scenario-filter", "value")]
    )
    def update_metric_comparison_chart(selected_metric, year_range, selected_scenarios):
        years_data, scenarios = power_profiles.load_totex_scenarios()
        start_year, end_year = year_range
        indices = [i for i, yr in enumerate(years_data) if start_year <= yr <= end_year]
        filtered_years = [years_data[i] for i in indices]
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        fig = go.Figure()
        # Add background shading between years
        for i, year in enumerate(filtered_years[:-1]):
            if i % 2 == 0:
                fig.add_shape(
                    type="rect",
                    x0=year - 0.5,
                    x1=filtered_years[i+1] - 0.5,
                    y0=0,
                    y1=1,
                    yref="paper",
                    fillcolor="rgba(240, 240, 240, 0.5)",
                    line_width=0,
                    layer="below"
                )
        display_metric = selected_metric.replace("_", " ").title()
        for idx, (label, scenario) in enumerate(scenarios.items()):
            if selected_scenarios and label not in selected_scenarios:
                continue
            metric_values = scenario.get(selected_metric, [])
            if metric_values:
                filtered_values = [metric_values[i] for i in indices]
                color = colors[idx % len(colors)]
                hover_text = [
                    f"<b>{label}</b><br>Year: {year}<br>{display_metric}: £{val:,.0f}"
                    for year, val in zip(filtered_years, filtered_values)
                ]
                fig.add_trace(go.Scatter(
                    x=filtered_years,
                    y=filtered_values,
                    mode="lines+markers",
                    name=f"{label} {selected_metric}",
                    line=dict(color=color, width=3),
                    marker=dict(size=10, line=dict(width=2, color='white')),
                    hoverinfo="text",
                    hovertext=hover_text,
                    text=[f"£{val:,.0f}" if val > max(filtered_values) * 0.1 else "" for val in filtered_values],
                    textposition="top center",
                    textfont=dict(size=10)
                ))
                for i in range(1, len(filtered_values)):
                    change = filtered_values[i] - filtered_values[i-1]
                    percent_change = (change / filtered_values[i-1] * 100) if filtered_values[i-1] != 0 else 0
                    if abs(percent_change) > 20:
                        fig.add_annotation(
                            x=filtered_years[i],
                            y=filtered_values[i],
                            text=f"{percent_change:+.1f}%",
                            showarrow=True,
                            arrowhead=2,
                            arrowsize=1,
                            arrowwidth=2,
                            arrowcolor="#636363"
                        )
        fig.update_layout(
            title={
                'text': f"<b>{display_metric}</b> Comparison Across Scenarios",
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=24)
            },
            xaxis=dict(
                title="Year",
                tickangle=-45,
                gridcolor='rgba(220, 220, 220, 0.8)',
                showgrid=True
            ),
            yaxis=dict(
                title=f"{display_metric} (£)",
                gridcolor='rgba(220, 220, 220, 0.8)',
                showgrid=True,
                tickformat=",.0f",
                tickprefix="£"
            ),
            template="plotly_white",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.12,
                xanchor="center",
                x=0.5,
                font=dict(size=12),
                bordercolor="Black",
                borderwidth=1
            ),
            margin=dict(l=80, r=80, t=100, b=80),
            hoverlabel=dict(
                bgcolor="white",
                font_size=14,
                font_family="Arial"
            ),
            height=600
        )
        fig.add_annotation(
            text="Financial Analysis Dashboard",
            x=1,
            y=0,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=10, color="lightgrey"),
            xanchor="right",
            yanchor="bottom"
        )
        return fig

    # Callback: Update Detail Power Profile Chart
    @app.callback(
        Output("detail-power-profile-chart", "figure"),
        [Input("detail-peak-power", "value"),
         Input("detail-base-load", "value")]
    )
    def update_power_profile_chart(peak_power, base_load):
        if not peak_power:
            peak_power = 25000
        if not base_load:
            base_load = 40
        hours = np.linspace(0, 24, 100)
        y = base_load + (peak_power - base_load) * 0.5 * (np.sin((hours - 6) / 24 * 2 * np.pi) + 1)
        fig = go.Figure(data=go.Scatter(x=hours, y=y, mode="lines", name="Load Profile"))
        fig.update_layout(
            title="Daily Load Profile (Synthetic)",
            xaxis_title="Hour",
            yaxis_title="Power (kW)",
            template=power_profiles.TEMPLATE_STYLE
        )
        return fig

    # Callback: Update Energy Demand Chart
    @app.callback(
        Output("energy-demand-chart", "figure"),
        [Input("detail-peak-power", "value")]
    )
    def update_energy_demand_chart(peak_power):
        if not peak_power:
            peak_power = 25000
        base_energy = peak_power * 24 * 0.5
        years_proj = list(range(2025, 2051))
        growth_rate = 0.02
        energy_demand = [base_energy * ((1 + growth_rate) ** (year - 2025)) for year in years_proj]
        fig = go.Figure(data=go.Scatter(x=years_proj, y=energy_demand, mode="lines", name="Energy Demand"))
        fig.update_layout(
            title="Projected Energy Demand (Synthetic)",
            xaxis_title="Year",
            yaxis_title="Energy Demand (kWh)",
            template=power_profiles.TEMPLATE_STYLE
        )
        return fig

    # Callback: Update Storage Results Display
    @app.callback(
        Output("detail-storage-results", "children"),
        [Input("detail-storage-type", "value")]
    )
    def update_storage_results(selected_storage):
        if not selected_storage:
            return "No storage option selected."
        return html.Ul([html.Li(f"Option: {option}") for option in selected_storage])

    # Callback: Update Dashboard Charts Container
    @app.callback(
        Output("dashboard-charts-container", "children"),
        [Input("dashboard-chart-selector", "value")]
    )
    def update_dashboard_charts(selected_charts):
        from pages.output_module import get_current_output_table, get_future_output_table, get_opex_comparison_table
        if not selected_charts:
            return html.Div("No charts selected.", style={"text-align": "center", "padding": "20px"})
        charts = []
        if "npv" in selected_charts:
            data = get_financial_data()
            result = data.get("result", [])
            if result:
                years = [entry.get("year") for entry in result]
                npv_data = [entry.get("npv", 0) for entry in result]
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=years, y=npv_data, mode="lines", name="NPV"))
                fig = power_profiles.set_figure_layout(fig, "NPV Comparison", "Year", "NPV (£)")
                charts.append(card_component("NPV Comparison", dcc.Graph(figure=fig, className="chart-container")))
        if "cashflow" in selected_charts:
            charts.append(card_component("Cashflow Analysis (API-based)", dcc.Graph(figure=power_profiles.cashflow_figure(), className="chart-container")))
        if "totex" in selected_charts:
            charts.append(card_component("TOTEX Comparison (API-based)", dcc.Graph(figure=power_profiles.totex_figure(), className="chart-container")))
        if "engine" in selected_charts:
            charts.append(card_component("Engine Power Profile", dcc.Graph(figure=power_profiles.engine_power_profile_figure(), className="chart-container")))
        if "timeseries" in selected_charts:
            charts.append(
                dbc.Card([
                    dbc.CardHeader(html.H4("Timeseries Comparisons", style={"color": "white"}), style=power_profiles.HEADER_STYLE),
                    dbc.CardBody([
                        dcc.Graph(figure=power_profiles.opex_comparison_figure(), className="chart-container"),
                        dcc.Graph(figure=power_profiles.penalty_comparison_figure(), className="chart-container"),
                        dcc.Graph(figure=power_profiles.fuel_comparison_figure(), className="chart-container"),
                        dcc.Graph(figure=power_profiles.maintenance_comparison_figure(), className="chart-container")
                    ])
                ], className="mb-4")
            )
        return charts

if __name__ == "__main__":
    from dash import Dash
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    from pages import power_profiles
    app.layout = power_profiles.layout()
    register_callbacks(app)
    app.run_server(debug=True)
