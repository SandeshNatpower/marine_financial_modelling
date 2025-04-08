import json
import requests
from urllib.parse import urlencode
import random

import dash
from dash import html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import config
import plotly.graph_objects as go
import numpy as np
import math
from math import ceil
from plotly.subplots import make_subplots
import pages.input_module
from pages.input_module import get_vessel_details, DEFAULT_VESSEL

###############################################################################
# GLOBAL STYLES & CONSTANTS
###############################################################################
HEADER_STYLE = {"backgroundColor": "#0A4B8C", "padding": "10px"}
HEADER_TEXT_STYLE = {"color": "white", "margin": "0"}
MARGIN_STYLE = dict(l=60, r=30, t=60, b=50)
TEMPLATE_STYLE = "plotly_white"

###############################################################################
# COMMON CARD COMPONENT
###############################################################################
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

###############################################################################
# SCENARIO DATA LOADING & FALLBACK DATA
###############################################################################

def load_min_future_opex_scenarios(dashboard_data=None):
    if dashboard_data and isinstance(dashboard_data, dict):
        scenarios = {}
        all_years = set()
        
        for scenario_key, data_points in dashboard_data.items():
            # Verify data structure for each scenario
            if not isinstance(data_points, list):
                continue
                
            try:
                # Sort by year and validate entries
                sorted_points = sorted(data_points, key=lambda x: x["year"])
                years = [p["year"] for p in sorted_points]
                values = {
                    "Future Opex": [p["min_future_opex"] for p in sorted_points],
                    "EU ETS": [p["eu_ets_penalty"] for p in sorted_points],
                    "Fuel EU": [p["fuel_eu_penalty"] for p in sorted_points],
                    "Fuel Future Price": [p["fuel_future_price"] for p in sorted_points],
                    "Maintenance Future": [p["maintenance_future"] for p in sorted_points],
                    "Spares Future": [p["spare_future"] for p in sorted_points]
                }
                
                scenarios[scenario_key] = {
                    "label": scenario_key,
                    "years": years,
                    **values
                }
                all_years.update(years)
                
            except KeyError as e:
                print(f"Missing key {e} in scenario {scenario_key}")
                continue
                
        return sorted(all_years), scenarios

    # Fallback synthetic data if no API data is available.
    years = list(range(2025, 2051))
    scenario_list = [
        {
            "label": "MDO",
            "Future Opex": generate_scenario_progression([10, 20]),
            "EU ETS": generate_scenario_progression([10, 20]),
            "Fuel EU": generate_scenario_progression([10, 20]),
            "Fuel Future Price": generate_scenario_progression([10, 20]), 
            "Maintenance Future": generate_scenario_progression([10, 20]),
            "Spares Future": generate_scenario_progression([10, 20])
            
        },
        {
            "label": "LFO",
            "Future Opex": generate_scenario_progression([10, 20]),
            "EU ETS": generate_scenario_progression([10, 20]),
            "Fuel EU": generate_scenario_progression([10, 20]),
            "Fuel Future Price": generate_scenario_progression([10, 20]),
            "Maintenance Future": generate_scenario_progression([10, 20]),
            "Spares Future": generate_scenario_progression([10, 20])
        },
        {
            "label": "HFO",
            "Future Opex": generate_scenario_progression([10, 20]),
            "EU ETS": generate_scenario_progression([10, 20]),
            "Fuel EU": generate_scenario_progression([10, 20]),
            "Fuel Future Price": generate_scenario_progression([10, 20]),
            "Maintenance Future": generate_scenario_progression([10, 20]),
            "Spares Future": generate_scenario_progression([10, 20])
            
        },
        {
            "label": "MDO_With_Shore_Power",
            "Future Opex": generate_scenario_progression([6436373, 13394070]),
            "EU ETS": generate_scenario_progression([10, 20]),
            "Fuel EU": generate_scenario_progression([10, 20]),
            "Fuel Future Price": generate_scenario_progression([10, 20]),
            "Maintenance Future": generate_scenario_progression([10, 20]),
            "Spares Future": generate_scenario_progression([10, 20])
        },
        {
            "label": "HFO_With_Shore_Power",
            "Future Opex": generate_scenario_progression([7019286, 14519473]),
            "EU ETS": generate_scenario_progression([10, 20]),
            "Fuel EU": generate_scenario_progression([10, 20]),
            "Fuel Future Price": generate_scenario_progression([10, 20]),
            "Maintenance Future": generate_scenario_progression([10, 20]),
            "Spares Future": generate_scenario_progression([10, 20])
        },
        {
            "label": "LFO_With_Shore_Power",
            "Future Opex": generate_scenario_progression([4776659, 9942061]),
            "EU ETS": generate_scenario_progression([10, 20]),
            "Fuel EU": generate_scenario_progression([10, 20]),
            "Fuel Future Price": generate_scenario_progression([10, 20]),
            "Maintenance Future": generate_scenario_progression([10, 20]),
            "Spares Future": generate_scenario_progression([10, 20])
        }
    ]
    fallback_scenarios = {}
    for sc in scenario_list:
        sc["years"] = years
        fallback_scenarios[sc["label"]] = sc

    return years, fallback_scenarios

def generate_scenario_progression(initial_values, years=26):
    """
    Generate a synthetic progression of values over 26 data points.
    """
    if len(initial_values) < 2:
        initial_values = initial_values + [initial_values[0]] * (2 - len(initial_values))
    result = initial_values[:2]
    for _ in range(2, years):
        last_value = result[-1]
        prev_value = result[-2]
        trend = last_value - prev_value
        variation = trend * (1 + np.random.uniform(-0.1, 0.1))
        noise = np.random.normal(0, abs(trend) * 0.1)
        next_value = last_value + variation + noise
        result.append(next_value)
    return result

###############################################################################
# FIGURE HELPERS
###############################################################################
def set_figure_layout(fig, title, xaxis_title=None, yaxis_title=None):
    fig.update_layout(
        title=title,
        title_font_color="#0A4B8C",
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        template=TEMPLATE_STYLE,
        margin=MARGIN_STYLE
    )
    return fig

def generate_load_profile(peak_power, base_load_percent, hours=24):
    """
    Generate a sinusoidal load profile for a day.
    """
    base_load = peak_power * (base_load_percent / 100.0)
    amplitude = peak_power - base_load
    x = np.linspace(0, 24, hours)
    y = base_load + amplitude * np.sin((x - 6) / 24 * 2 * np.pi)
    y = np.maximum(y, base_load)
    return x, y


###############################################################################
# FIGURE FUNCTIONS
###############################################################################
def dwelling_at_berth_pie_figure(dashboard_data, selected_scenarios=None):
    """
    Generate pie charts for each scenario using dashboard data.
    For each scenario, compute average values for cost categories over all years.
    The categories are:
      - Fuel (from "fuel_future_price")
      - Financing (not provided in API, so defaults to 0)
      - Maintenance (from "maintenance_future")
      - Spares/consumables (from "spare_future")
      - EU ETS (from "eu_ets_penalty")
      - FuelEU (from "fuel_eu_penalty")
    The average for each category is computed over all records (years) available.
    """
    import math
    from plotly.subplots import make_subplots

    # Define the labels for the pie chart
    labels = ["Fuel", "Financing", "Maintenance", "Spares/consumables", "EU ETS", "FuelEU"]

    # Fallback if no scenarios or dashboard data are provided.
    if not selected_scenarios or not dashboard_data:
        values = [63, 0, 9, 2, 1, 25]
        fig = go.Figure([go.Pie(labels=labels, values=values, textinfo="label+percent", hoverinfo="label+value")])
        fig.update_layout(title="Dwelling at Berth - Biofuel Blend Minimum")
        return fig

    # Determine grid layout based on number of selected scenarios.
    max_cols = 3
    total = len(selected_scenarios)
    cols = min(max_cols, total)
    rows = math.ceil(total / cols)
    specs = [[{"type": "domain"} for _ in range(cols)] for _ in range(rows)]
    
    # Create subplots.
    fig = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=selected_scenarios,
        specs=specs
    )

    # Process each selected scenario.
    for i, scenario in enumerate(selected_scenarios):
        row = (i // cols) + 1
        col = (i % cols) + 1

        records = dashboard_data.get(scenario, [])
        if not records or not isinstance(records, list) or len(records) == 0:
            # If no data, use default fallback values.
            avg_fuel = 10_000_000
            avg_financing = 0
            avg_maintenance = 10_000_000
            avg_spares = 10_000_000
            avg_eu_ets = 10_000_000
            avg_fuel_eu = 10_000_000
        else:
            count = len(records)
            # Compute the average of each category over all years.
            avg_fuel = sum(record.get("fuel_future_price", 0) for record in records) / count
            avg_maintenance = sum(record.get("maintenance_future", 0) for record in records) / count
            avg_spares = sum(record.get("spare_future", 0) for record in records) / count
            avg_eu_ets = sum(record.get("eu_ets_penalty", 0) for record in records) / count
            avg_fuel_eu = sum(record.get("fuel_eu_penalty", 0) for record in records) / count
            avg_financing = 0  # No financing data provided; default to 0

        # Create list of average values.
        values = [avg_fuel, avg_financing, avg_maintenance, avg_spares, avg_eu_ets, avg_fuel_eu]
        total_value = sum(values) or 1
        percentages = [(v / total_value) * 100 for v in values]

        # Add a pie chart trace for this scenario.
        fig.add_trace(
            go.Pie(
                labels=labels,
                values=percentages,
                name=scenario,
                textinfo="label+percent",
                hoverinfo="label+value"
            ),
            row=row,
            col=col
        )

    fig.update_layout(
        title_text="Dwelling at Berth - Cost Distribution",
        height=rows * 400,
        showlegend=False
    )
    
    return fig


def min_future_opex_figure(dashboard_data=None):
    """Horizontal bar chart for Future Opex comparison."""
    # Load scenarios data using our helper.
    # This returns a tuple: (years, scenarios_data)
    _, scenarios_data = load_min_future_opex_scenarios(dashboard_data)

    labels, values = [], []
    for scenario_label, scenario_info in scenarios_data.items():
        # Retrieve the list of future opex values from the key "Future Opex"
        future_opex_list = scenario_info.get("Future Opex", [])
        # Ensure that we have a list and it is not empty.
        if future_opex_list and isinstance(future_opex_list, list):
            # Use the last value in the list (assumed to be the latest year)
            labels.append(scenario_label)
            values.append(future_opex_list[-1])
    
    # Create a horizontal bar chart.
    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color="#0A4B8C"
    ))
    set_figure_layout(fig, "Future Opex Comparison", "Future Opex", "Scenario")
    return fig



def generate_metric_figure(metric, year_range, selected_scenarios, dashboard_data=None):
    """
    Generate a line chart for the selected economic metric over a given year range.
    """
    years_list, scenarios_data = load_min_future_opex_scenarios(dashboard_data)
    start_year, end_year = (2025, 2050) if not year_range or len(year_range) != 2 else year_range
    fig = go.Figure()
    for scenario_label, sc_data in scenarios_data.items():
        if selected_scenarios and scenario_label not in selected_scenarios:
            continue
        scenario_years = sc_data.get("years", [])
        metric_values = sc_data.get(metric, [])
        if not scenario_years or not metric_values:
            continue
        filtered = [(yr, val) for yr, val in zip(scenario_years, metric_values) if start_year <= yr <= end_year]
        if filtered:
            x_vals, y_vals = zip(*filtered)
            fig.add_trace(go.Scatter(x=list(x_vals), y=list(y_vals), mode='lines+markers', name=scenario_label))
    set_figure_layout(fig, f"{metric} Comparison", "Year", f"{metric} (£)")
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
    return fig

###############################################################################
# FILTERING FUNCTION
###############################################################################
def filter_dashboard_data_by_scenarios(dashboard_data, selected_scenarios):
    """
    Filter the dashboard_data to include only the scenarios listed in selected_scenarios.
    """
    if not dashboard_data:
        return {}
    return {scenario: data for scenario, data in dashboard_data.items() if scenario in selected_scenarios}

###############################################################################
# LAYOUT FUNCTIONS
###############################################################################
def financial_metrics_layout():
    """
    Financial Metrics tab layout.
    """
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H4("Economic Metrics (2025–2050)", className="card-title", style=HEADER_TEXT_STYLE),
                style=HEADER_STYLE
            ),
            dbc.CardBody(
                [
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Metric"),
                            dcc.Dropdown(
                                id="metric-dropdown",
                                options=[
                                    {"label": "Future Opex", "value": "Future Opex"},
                                    {"label": "EU ETS", "value": "EU ETS"},
                                    {"label": "Fuel EU", "value": "Fuel EU"},
                                    {"label": "Fuel Future Price", "value": "Fuel Future Price"},
                                    {"label": "Maintenance Future", "value": "Maintenance Future"},
                                    {"label": "Spares Future", "value": "Spares Future"}
                                ],
                                value="Future Opex",
                                clearable=False,
                                className="custom-dropdown"
                            )
                        ], md=3, xs=12),
                        dbc.Col([
                            dbc.Label("Year Range"),
                            dcc.RangeSlider(
                                id="year-range-slider",
                                min=2025,
                                max=2050,
                                value=[2025, 2050],
                                marks={yr: {"label": str(yr), "style": {"transform": "rotate(45deg)", "whiteSpace": "nowrap"}} for yr in range(2025, 2051)},
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ], md=8, xs=12),        
                    ]),
                    html.Br(),
                    dcc.Graph(id="metric-comparison-chart", className="chart-container"),
                    html.Hr(),
                    dcc.Graph(id="min-future-opex", className="chart-container"),
                    html.Hr(),
                    dcc.Graph(id="financial-pie-chart", className="chart-container"),
                    html.Hr(),
                ]
            )
        ],
        className="mb-4"
    )

def multi_chart_dashboard_layout():
    """
    Combined Dashboard layout that aggregates graphs from both Financial Metrics and Power Demand.
    A checklist allows users to select which charts to display.
    """
    options = [
        {"label": "Metric Comparison", "value": "metric"},
        {"label": "Future Opex", "value": "min_future_opex"},
        {"label": "Dwelling at Berth", "value": "dwelling"},
        {"label": "Detail Power Profile", "value": "detail"},
        {"label": "Projected Energy Demand", "value": "energy"}
    ]
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H4("Combined Dashboard", className="card-title", style=HEADER_TEXT_STYLE),
                style=HEADER_STYLE
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        dbc.Col(
                            dcc.Checklist(
                                id="dashboard-chart-selector",
                                options=options,
                                value=[opt["value"] for opt in options],
                                labelStyle={'display': 'inline-block', 'margin-right': '15px'}
                            ),
                            width=12
                        )
                    ),
                    html.Hr(),
                    html.H5("Debug Dashboard Data"),
                    html.Pre(
                        id="debug-dashboard-data",
                        style={"backgroundColor": "#f8f9fa", "padding": "10px", "maxHeight": "200px", "overflowY": "scroll"}
                    ),
                    html.Hr(),
                    html.Div(id="dashboard-charts-container")
                ]
            )
        ],
        className="mb-4"
    )

def layout():
    """
    Top-level layout that includes a global scenario filter and three tabs:
    Financial Metrics, Combined Dashboard, and Power Demand Analysis.
    """
    return dbc.Container(
        [
            # Global Scenario Filter
            dbc.Row(
                dbc.Col(
                    dcc.Dropdown(
                        id="scenario-filter",
                        options=[],  # Will be populated by a callback
                        multi=True,
                        placeholder="Select scenarios",
                        className="custom-dropdown"
                    ),
                    width=12
                ),
                className="mb-3"
            ),
            dbc.Tabs(
                [
                    dbc.Tab(financial_metrics_layout(), label="Financial Metrics"),
                    dbc.Tab(multi_chart_dashboard_layout(), label="Dashboard")
                ]
            ),
        ],
        fluid=True
    )
