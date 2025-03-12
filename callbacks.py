import dash
import json
import requests
from urllib.parse import urlencode
from dash import html, dcc, no_update, Input, Output, State
import dash_bootstrap_components as dbc
import config
import plotly.graph_objects as go

# Import helper functions from output_module and power_profiles
from pages.input_module import get_vessel_details
from pages.output_module import (
    get_current_output_table,
    get_future_output_table,
    get_opex_comparison_table,
    get_emissions_comparison_table,
    get_conversion_factor,
    format_currency_value,
    style_savings,
    format_number
)
from pages import power_profiles

###########################################################################
# API CALL HELPER FUNCTION
###########################################################################
def get_financial_data(input_params=None):
    """
    Fetch financial data from the API using parameters from input if provided.
    Returns the complete JSON response as a dictionary.
    
    Correct API call example:
    https://natpower-marine-api-dev.azurewebsites.net/marinedata/financialmodelling?main_engine_power_kw=38400&aux_engine_power_kw=2020&...
    """
    # If no parameters are provided, use defaults from the default vessel.
    if input_params is None:
        vessel_data = get_vessel_details(config.DEFAULT_VESSEL["imo"])
        input_params = {
            "main_engine_power_kw": vessel_data.get("total_engine_power", 38400),
            "aux_engine_power_kw": vessel_data.get("average_hoteling_kw", 2020),
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
            "shore_enable": False,
            "inflation_rate": 0.02,
            "npv_rate": 0,
            "CAPEX": 19772750
        }
    qs = urlencode(input_params)
    # Use the FINANCIAL_ENDPOINT from config without appending extra path segments.
    url = f"{config.FINANCIAL_ENDPOINT}?{qs}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print("Error fetching financial data:", e)
        return {}

###########################################################################
# HELPER FUNCTIONS TO PROCESS API RESPONSE
###########################################################################
def process_financial_results(api_data):
    """
    Processes the API response to combine data from 'result', 'current_timeseries',
    and 'future_timeseries' arrays.

    Args:
        api_data (dict): Raw API response containing result and timeseries data.

    Returns:
        list: List of dictionaries with combined financial data per year.
    """
    results = api_data.get("result", [])
    current_timeseries = api_data.get("current_timeseries", [])
    future_timeseries = api_data.get("future_timeseries", [])
    processed = []
    for res in results:
        year = res.get("year")
        current_ts = next((ts for ts in current_timeseries if ts.get("year") == year), {})
        future_ts = next((ts for ts in future_timeseries if ts.get("year") == year), {})
        processed.append({
            "year": year,
            "npv": res.get("npv", 0),
            "cumulative": res.get("cumulative", 0),
            "yearly_result": res.get("result", 0),
            "current_opex": current_ts.get("current_opex", 0),
            "future_opex": future_ts.get("future_opex", 0),
            "current_penalty": current_ts.get("current_penalty", 0),
            "future_penalty": future_ts.get("future_penalty", 0),
            "total_fuel_current_inflated": current_ts.get("total_fuel_current_inflated", 0),
            "total_maintenance_current_inflated": current_ts.get("total_maintenance_current_inflated", 0),
            "total_spare_current_inflated": current_ts.get("total_spare_current_inflated", 0)
        })
    return processed

def create_processed_results_table(processed_data, conv_factor, currency):
    """
    Creates an HTML table from processed financial results with currency conversion.

    Args:
        processed_data (list): List of dictionaries from process_financial_results.
        conv_factor (float): Currency conversion factor.
        currency (str): Selected currency symbol or code.

    Returns:
        dbc.Table: Formatted table displaying financial results.
    """
    header = html.Thead(
        html.Tr([
            html.Th("Year"),
            html.Th("NPV"),
            html.Th("Cumulative"),
            html.Th("Yearly Result"),
            html.Th("Current OPEX"),
            html.Th("Future OPEX"),
            html.Th("Current Penalty"),
            html.Th("Future Penalty"),
            html.Th("Fuel Cost"),
            html.Th("Maintenance"),
            html.Th("Spare")
        ])
    )
    rows = []
    for item in processed_data:
        rows.append(html.Tr([
            html.Td(item.get("year")),
            html.Td(f"{format_currency_value(item.get('npv', 0), conv_factor, currency)}"),
            html.Td(f"{format_currency_value(item.get('cumulative', 0), conv_factor, currency)}"),
            html.Td(f"{format_currency_value(item.get('yearly_result', 0), conv_factor, currency)}"),
            html.Td(f"{format_currency_value(item.get('current_opex', 0), conv_factor, currency)}"),
            html.Td(f"{format_currency_value(item.get('future_opex', 0), conv_factor, currency)}"),
            html.Td(f"{format_currency_value(item.get('current_penalty', 0), conv_factor, currency)}"),
            html.Td(f"{format_currency_value(item.get('future_penalty', 0), conv_factor, currency)}"),
            html.Td(f"{format_currency_value(item.get('total_fuel_current_inflated', 0), conv_factor, currency)}"),
            html.Td(f"{format_currency_value(item.get('total_maintenance_current_inflated', 0), conv_factor, currency)}"),
            html.Td(f"{format_currency_value(item.get('total_spare_current_inflated', 0), conv_factor, currency)}")
        ]))
    table = dbc.Table([header, html.Tbody(rows)], bordered=True, hover=True, responsive=True)
    return table

###########################################################################
# REGISTER ALL CALLBACKS
###########################################################################
def register_callbacks(app):
    """Registers all Dash callbacks for the application."""

    # --- Vessel/Input Module Callbacks ---
    @app.callback(
        [Output('search-results', 'children'),
         Output('vessel-data-store', 'data')],
        Input('search-button', 'n_clicks'),
        [State('search-type', 'value'),
         State('search-term', 'value')],
        prevent_initial_call=True
    )
    def search_vessel_callback(n_clicks, search_type, search_term):
        if not search_term:
            return "Please enter a search term.", config.DEFAULT_VESSEL
        from pages.input_module import get_vessel_details as input_get_vessel_details
        vessel_data = input_get_vessel_details(search_term, search_type)
        return f"Found vessel: {vessel_data.get('vessel_name', 'Unknown')}", vessel_data

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
        # Use the vessel API response values if available (e.g., 'build' for year built)
        if not vessel_data:
            vessel_data = config.DEFAULT_VESSEL
        return (
            vessel_data.get('vessel_name', config.DEFAULT_VESSEL["vessel_name"]),
            vessel_data.get('imo', config.DEFAULT_VESSEL["imo"]),
            vessel_data.get('new_vessel_category', config.DEFAULT_VESSEL["vessel_category"]),
            vessel_data.get('gross_tonnage', config.DEFAULT_VESSEL["gross_tonnage"]),
            vessel_data.get('build', config.DEFAULT_VESSEL["year_built"]),
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
            Output('fueleu-penalty', 'value'),
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
        vessel_data
    ):
        if n_clicks is None or not all([main_power, aux_power, main_fuel_type, aux_fuel_type]):
            return None, "input"
        shore_port = vessel_data.get('shore_port', 1) if isinstance(vessel_data, dict) else 1
        reporting_year = vessel_data.get('reporting_year', 2030) if isinstance(vessel_data, dict) else 2030
        # Convert the shore_enable input to a boolean
        shore_enable_bool = True if str(shore_enable).strip().lower() in ["yes", "true"] else False

        # Build parameters dictionary from inputs.
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
            "BIOFUELS_BLEND_PERCENTAGE": float(biofuels_blend),
            "shore_enable": shore_enable_bool,
            "inflation_rate": 0.02,  # Hardcoded as per API example
            "npv_rate": float(npv_rate),
            "CAPEX": float(capex)
        }
        # Use the input parameters in the API call.
        financial_data = get_financial_data(params)
        if financial_data:
            return financial_data, "output"
        else:
            return None, "input"

    @app.callback(
        Output('output-content', 'children'),
        [Input('emissions-data-store', 'data'),
         Input('currency-choice', 'value'),
         Input('table-selection-dropdown', 'value')]
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
        conv_factor = get_conversion_factor(currency)
        tables = []
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

    # --- Power Profiles Callbacks ---
    @app.callback(
        Output("metric-comparison-chart", "figure"),
        [Input("metric-dropdown", "value"),
         Input("year-range-slider", "value"),
         Input("scenario-filter", "value")]
    )
    def update_metric_comparison_chart(selected_metric, year_range, selected_scenarios):
        try:
            years_data, scenarios = power_profiles.load_totex_scenarios()
            start_year, end_year = year_range
            indices = [i for i, y in enumerate(years_data) if start_year <= y <= end_year]
            filtered_years = [years_data[i] for i in indices]
            
            colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                      '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
            
            fig = go.Figure()
            
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
                        name=label,
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
                    y=1.12,
                    x=0.5,
                    xanchor="center",
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
            
        except Exception as e:
            fig = go.Figure()
            fig.update_layout(
                title={'text': f"Error: {str(e)}", 'font': dict(color='red')},
                template="plotly_white"
            )
            
        return fig

    @app.callback(
        Output('detail-power-profile-chart', 'figure'),
        [Input('detail-peak-power', 'value'),
         Input('detail-base-load', 'value')]
    )
    def update_detail_power_profile(peak_power, base_load):
        try:
            fig = {
                'data': [{
                    'x': ['00:00', '01:00', '02:00', '03:00'],
                    'y': [base_load, base_load + peak_power * 0.1, base_load + peak_power * 0.2, peak_power],
                    'type': 'scatter',
                    'name': 'Load Profile'
                }],
                'layout': {'title': 'Load Profile'}
            }
        except Exception as e:
            fig = {
                'data': [],
                'layout': {
                    'title': 'Error Creating Chart',
                    'annotations': [{
                        'text': f"Error: {str(e)}",
                        'showarrow': False,
                        'font': {'color': 'red'}
                    }]
                }
            }
        return fig

    @app.callback(
        Output('energy-demand-chart', 'figure'),
        [Input('detail-peak-power', 'value'),
         Input('detail-base-load', 'value'),
         Input('detail-storage-type', 'value')]
    )
    def update_energy_demand_chart(peak_power, base_load, storage_options):
        try:
            years_demo = list(range(2025, 2051))
            energy_demand = [peak_power * (base_load / 100) * (1 + 0.02*(y - 2025)) for y in years_demo]
    
            fig = go.Figure(data=go.Scatter(x=years_demo, y=energy_demand, mode='lines+markers'))
            fig.update_layout(
                title="Projected Energy Demand",
                xaxis_title="Year",
                yaxis_title="Energy Demand (kWh)",
                template="plotly_white"
            )
            if storage_options:
                fig.add_annotation(
                    x=years_demo[-1],
                    y=energy_demand[-1],
                    text="Storage: " + ", ".join(storage_options),
                    showarrow=True,
                    arrowhead=1
                )
        except Exception as e:
            fig = {
                'data': [],
                'layout': {
                    'title': 'Error Creating Energy Demand Chart',
                    'annotations': [{
                        'text': f"Error: {str(e)}",
                        'showarrow': False,
                        'font': {'color': 'red'}
                    }]
                }
            }
        return fig

    @app.callback(
        Output("url", "pathname"),
        Input("tab-switch", "data"),
        prevent_initial_call=True
    )
    def redirect_to_output(tab):
        if tab == "output":
            return "/output"
        elif tab == "input":
            return "/input"
        return no_update

    # --- Additional Callbacks (if any) ---
    # Add more callbacks here as needed

    # End of register_callbacks
