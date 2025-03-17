import json
import requests
from urllib.parse import urlencode
import dash
from dash import html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import config
import plotly.graph_objects as go
import numpy as np

# Import helper functions from power_profiles.py
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
        "CAPEX": 19772750
    }

    vessel_data = vessel_data_override or config.DEFAULT_VESSEL
    vessel_overrides = {
        "main_engine_power_kw": vessel_data.get("total_engine_power", fallback_defaults["main_engine_power_kw"]),
        "aux_engine_power_kw": vessel_data.get("average_hoteling_kw", fallback_defaults["aux_engine_power_kw"]),
        "main_fuel_type": vessel_data.get("main_fuel_type", fallback_defaults["main_fuel_type"]),
        "aux_fuel_type": vessel_data.get("aux_fuel_type", fallback_defaults["aux_fuel_type"]),
        "reporting_year": vessel_data.get("reporting_year", fallback_defaults["reporting_year"])
    }

    final_params = fallback_defaults.copy()
    final_params.update(vessel_overrides)
    if input_params:
        final_params.update(input_params)

    final_params["shore_enable"] = str(final_params.get("shore_enable", False)).lower()

    if input_params and "biofuels_blend" in input_params:
        try:
            blend_value = float(input_params["biofuels_blend"])
            final_params["BIOFUELS_BLEND_PERCENTAGE"] = blend_value / 100.0 if blend_value > 1 else blend_value
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
        from pages.input_module import get_vessel_details
        vessel_data = get_vessel_details(search_term, search_type)
        return vessel_data, f"Found vessel: {vessel_data.get('vessel_name', 'Unknown')}"

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

    @app.callback(
        [Output('emissions-data-store', 'data'),
         Output('tab-switch', 'data')],
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
        shore_port, reporting_year, inflation_rate,
        vessel_data
    ):
        if n_clicks is None or not all([main_power, aux_power, main_fuel_type, aux_fuel_type]):
            return None, "input"
        
        shore_enable_bool = str(shore_enable).strip().lower() in ["yes", "true"]
        
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
            "BIOFUELS_BLEND_PERCENTAGE": float(biofuels_blend) / 100.0,
            "shore_enable": shore_enable_bool,
            "inflation_rate": (float(inflation_rate) / 100.0) if inflation_rate else 0.02,
            "npv_rate": float(npv_rate) / 100.0,
            "CAPEX": float(capex)
        }
        
        financial_data = get_financial_data(params, vessel_data_override=vessel_data)
        
        if financial_data:
            return financial_data, "output"
        else:
            return None, "input"

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

    @app.callback(
        Output("metric-comparison-chart", "figure"),
        [Input("metric-dropdown", "value"),
         Input("year-range-slider", "value"),
         Input("scenario-filter", "value")]
    )
    def update_metric_comparison_chart(selected_metric, year_range, selected_scenarios):
        data = get_financial_data()
        if selected_metric == "NPV":
            # Build chart from the "result" field
            results = data.get("result", [])
            years = [r["year"] for r in results]
            npv_values = [r["npv"] for r in results]
            fig = go.Figure(data=[go.Scatter(x=years, y=npv_values, mode="lines+markers", name="NPV",
                                              line=dict(color="black", width=2), marker=dict(size=6))])
            fig = power_profiles.set_figure_layout(fig, "NPV Comparison", "Year", "NPV (£)")
            return fig
        else:
            # Assume selected_metric is "OPEX" for cumulative OPEX (TOTEX)
            years, scenarios = power_profiles.load_totex_scenarios(data)
            start_year, end_year = year_range
            indices = [i for i, yr in enumerate(years) if start_year <= yr <= end_year]
            filtered_years = [years[i] for i in indices]
            current_cum = np.cumsum([scenarios["Current"]["OPEX"][i] for i in indices]).tolist()
            future_cum = np.cumsum([scenarios["Future"]["OPEX"][i] for i in indices]).tolist()
            fig = go.Figure()
            fig.add_trace(go.Bar(x=filtered_years, y=current_cum, name="Current", marker_color="blue"))
            fig.add_trace(go.Bar(x=filtered_years, y=future_cum, name="Future", marker_color="orange"))
            fig = power_profiles.set_figure_layout(fig, "TOTEX (Cumulative OPEX) Comparison", "Year", "OPEX (£)")
            return fig

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

    @app.callback(
        Output("detail-storage-results", "children"),
        [Input("detail-storage-type", "value")]
    )
    def update_storage_results(selected_storage):
        if not selected_storage:
            return "No storage option selected."
        return html.Ul([html.Li(f"Option: {option}") for option in selected_storage])

    @app.callback(
        Output("dashboard-charts-container", "children"),
        [Input("dashboard-chart-selector", "value")]
    )
    def update_dashboard_charts(selected_charts):
        data = get_financial_data()
        result = data.get("result", [])
        charts = []
        if not data:
            return html.Div("No data available.", style={"text-align": "center", "padding": "20px"})
        if "NPV" in selected_charts:
            years = [entry.get("year") for entry in result]
            npv_data = [entry.get("npv", 0) for entry in result]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=years, y=npv_data, mode="lines", name="NPV"))
            fig = power_profiles.set_figure_layout(fig, "NPV Comparison", "Year", "NPV (£)")
            charts.append(card_component("NPV Comparison", dcc.Graph(figure=fig, className="chart-container")))
        if "cashflow" in selected_charts:
            fig = power_profiles.cashflow_figure(data)
            charts.append(card_component("Cashflow Comparison", dcc.Graph(figure=fig, className="chart-container")))
        if "OPEX" in selected_charts:
            fig = power_profiles.totex_figure(data)
            charts.append(card_component("TOTEX Comparison", dcc.Graph(figure=fig, className="chart-container")))
        if "engine" in selected_charts:
            fig = power_profiles.engine_power_profile_figure(data)
            charts.append(card_component("Engine Power Profile", dcc.Graph(figure=fig, className="chart-container")))
        if "timeseries" in selected_charts:
            charts.append(
                dbc.Card([
                    dbc.CardHeader(html.H4("Timeseries Comparisons", style={"color": "white"}), style=power_profiles.HEADER_STYLE),
                    dbc.CardBody([
                        dcc.Graph(figure=power_profiles.opex_comparison_figure(data), className="chart-container"),
                        dcc.Graph(figure=power_profiles.penalty_comparison_figure(data), className="chart-container"),
                        dcc.Graph(figure=power_profiles.fuel_comparison_figure(data), className="chart-container"),
                        dcc.Graph(figure=power_profiles.maintenance_comparison_figure(data), className="chart-container")
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
