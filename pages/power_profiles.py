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

def load_profile_figure():
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[1, 2, 3], y=[10, 20, 30], mode='lines', name='Power Profile'))
    fig.update_layout(title='Power Profile')
    return fig

def load_totex_scenarios(dashboard_data=None):
    """
    Transform raw API dashboard_data into a tuple (years, scenarios).

    Expects each key (e.g. "HFO", "LFO", "MDO") to have a list of data points,
    each including "year" and "min_future_opex" (used as TOTEX).
    """
    scenarios = {}
    all_years = set()

    if dashboard_data and isinstance(dashboard_data, dict):
        for scenario_key, data_points in dashboard_data.items():
            if not data_points or not isinstance(data_points, list):
                continue
            sorted_points = sorted(data_points, key=lambda pt: pt.get("year", 0))
            valid_points = [pt for pt in sorted_points if "year" in pt]
            if not valid_points:
                continue
            scenario_years = [pt["year"] for pt in valid_points]
            all_years.update(scenario_years)
            totex_values = [pt.get("min_future_opex", 0) for pt in valid_points]
            npv_values = [pt.get("npv", 0) for pt in valid_points]
            result_values = [pt.get("result", 0) for pt in valid_points]
            cumulative_values = [pt.get("cumulative", 0) for pt in valid_points]

            scenarios[scenario_key] = {
                "label": scenario_key,
                "years": scenario_years,
                "TOTEX": totex_values,
                "NPV": npv_values,
                "Result": result_values,
                "Cumulative": cumulative_values
            }
        if scenarios:
            return sorted(all_years), scenarios

    # Fallback synthetic data if no API data is available.
    years = list(range(2025, 2051))
    scenario_list = [
        {
            "label": "MDO",
            "TOTEX": generate_scenario_progression([10, 20]),
            "NPV": generate_scenario_progression([-142168, -124728]),
            "Result": generate_scenario_progression([-142168, -266896]),
            "Cumulative": generate_scenario_progression([-142168, -266896])
        },
        {
            "label": "LFO",
            "TOTEX": generate_scenario_progression([10, 20]),
            "NPV": generate_scenario_progression([-3148, 36818]),
            "Result": generate_scenario_progression([-3148, 33670]),
            "Cumulative": generate_scenario_progression([-3148, 33670])
        },
        {
            "label": "HFO",
            "TOTEX": generate_scenario_progression([10, 20]),
            "NPV": generate_scenario_progression([-1065102, -1017039]),
            "Result": generate_scenario_progression([-1065102, -2082141]),
            "Cumulative": generate_scenario_progression([-1065102, -2082141])
        },
        {
            "label": "MDO_With_Shore_Power",
            "TOTEX": generate_scenario_progression([6436373, 13394070]),
            "NPV": generate_scenario_progression([-4349, -4523]),
            "Result": generate_scenario_progression([-4349, -8873]),
            "Cumulative": generate_scenario_progression([-4349, -8873])
        },
        {
            "label": "HFO_With_Shore_Power",
            "TOTEX": generate_scenario_progression([7019286, 14519473]),
            "NPV": generate_scenario_progression([-1066423, -1018473]),
            "Result": generate_scenario_progression([-1066423, -2082141]),
            "Cumulative": generate_scenario_progression([-1066423, -2082141])
        },
        {
            "label": "LFO_With_Shore_Power",
            "TOTEX": generate_scenario_progression([4776659, 9942061]),
            "NPV": generate_scenario_progression([-1065102, -1017039]),
            "Result": generate_scenario_progression([-1065102, -2082141]),
            "Cumulative": generate_scenario_progression([-1065102, -2082141])
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

def projected_energy_demand_figure():
    """
    Create a line chart for projected energy demand.
    Uses a default peak power of 25000 and base load of 40%.
    """
    x_vals, y_vals = generate_load_profile(peak_power=25000, base_load_percent=40)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode="lines+markers", name="Projected Demand"))
    set_figure_layout(fig, "Projected Energy Demand", "Hour", "Energy Demand (kW)")
    return fig

###############################################################################
# FIGURE FUNCTIONS
###############################################################################
def dwelling_at_berth_pie_figure(dashboard_data, selected_scenarios=None):
    """
    Generate pie charts for each scenario using dashboard data.
    """
    labels = ["Fuel", "Financing", "Maintenance", "Spares/consumables", "EU ETS", "FuelEU"]

    # Handle missing data.
    if not selected_scenarios or len(selected_scenarios) == 0 or not dashboard_data:
        values = [63, 0, 9, 2, 1, 25]
        fig = go.Figure([go.Pie(labels=labels, values=values, textinfo="label+percent", hoverinfo="label+value")])
        fig.update_layout(title="Dwelling at Berth - Biofuel Blend Minimum")
        return fig

    # Determine grid layout based on number of scenarios.
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

        scenario_data = dashboard_data.get(scenario, [])
        base_data = scenario_data[0] if scenario_data else {}
        min_opex = base_data.get("min_future_opex", 10_000_000)
        values = [
            min_opex * 0.60,
            min_opex * 0.00,
            min_opex * 0.15,
            min_opex * 0.05,
            min_opex * 0.05,
            min_opex * 0.15
        ]
        total_value = sum(values) or 1
        percentages = [(v / total_value) * 100 for v in values]

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
        title_text="Dwelling at Berth - Cost Distribution (Dummy Data)",
        height=rows * 400,
        showlegend=False
    )
    
    return fig

def cashflow_figure(dashboard_data=None):
    """Create cashflow figure from live data."""
    years, scenarios_data = load_totex_scenarios(dashboard_data)
    fig = go.Figure()
    for label, sc in scenarios_data.items():
        fig.add_trace(go.Scatter(
            x=sc["years"], y=sc.get("Cumulative", []),
            mode='lines', name=f"{label} - Cumulative"
        ))
        fig.add_trace(go.Scatter(
            x=sc["years"], y=sc.get("NPV", []),
            mode='lines', name=f"{label} - NPV"
        ))
    set_figure_layout(fig, "Cashflow Analysis", "Year", "Value")
    return fig

def totex_figure(dashboard_data=None):
    """
    Vertical bar chart for TOTEX comparison.
    """
    if not dashboard_data or not dashboard_data.keys():
        return go.Figure().update_layout(title="No Data Available")
    labels = []
    values = []
    for scenario, records in dashboard_data.items():
        total_opex = sum(record.get("min_future_opex") or 0 for record in records)
        labels.append(scenario)
        values.append(total_opex)
    fig = go.Figure([go.Bar(x=labels, y=values)])
    set_figure_layout(fig, "TOTEX Comparison (Vertical)", "Scenario", "TOTEX")
    return fig

def totex_horizontal_figure(dashboard_data=None):
    """Horizontal bar chart for TOTEX comparison."""
    _, scenarios_data = load_totex_scenarios(dashboard_data)
    labels, values = [], []
    for label, sc in scenarios_data.items():
        if sc.get("TOTEX"):
            labels.append(label)
            values.append(sc["TOTEX"][-1])
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h", marker_color="#0A4B8C"))
    set_figure_layout(fig, "TOTEX Comparison (Horizontal)", "TOTEX", "Scenario")
    return fig

def generate_metric_figure(metric, year_range, selected_scenarios, dashboard_data=None):
    """
    Generate a line chart for the selected economic metric over a given year range.
    """
    years_list, scenarios_data = load_totex_scenarios(dashboard_data)
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
                                    {"label": "TOTEX", "value": "TOTEX"},
                                    {"label": "Result", "value": "Result"},
                                    {"label": "Cumulative", "value": "Cumulative"},
                                    {"label": "NPV", "value": "NPV"}
                                ],
                                value="TOTEX",
                                clearable=False,
                                className="custom-dropdown"
                            )
                        ], md=4, xs=12),
                        dbc.Col([
                            dbc.Label("Year Range"),
                            dcc.RangeSlider(
                                id="year-range-slider",
                                min=2025,
                                max=2050,
                                value=[2025, 2050],
                                marks={yr: str(yr) for yr in range(2025, 2051)}
                            )
                        ], md=4, xs=12)
                    ]),
                    html.Br(),
                    dcc.Graph(id="metric-comparison-chart", className="chart-container"),
                    html.Hr(),
                    dcc.Graph(id="totex-horizontal-graph", className="chart-container"),
                    html.Hr(),
                    dcc.Graph(id="financial-pie-chart", className="chart-container"),
                    html.Hr(),
                    dcc.Graph(id="cashflow-graph", className="chart-container"),
                    html.Hr(),
                    dcc.Graph(id="totex-vertical-graph", className="chart-container"),
                    html.Hr(),
                ]
            )
        ],
        className="mb-4"
    )

def power_demand_tab_layout():
    """
    Power Demand Analysis tab layout.
    """
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H4("Power Demand Analysis", className="card-title", style=HEADER_TEXT_STYLE),
                style=HEADER_STYLE
            ),
            dbc.CardBody(
                [
                    dcc.Graph(id="detail-power-profile-chart", className="chart-container", figure=projected_energy_demand_figure()),
                    html.Br(),
                    dcc.Graph(id="energy-demand-chart", className="chart-container", figure=projected_energy_demand_figure())
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
        {"label": "Cashflow Analysis", "value": "cashflow"},
        {"label": "TOTEX (Vertical)", "value": "totex"},
        {"label": "TOTEX (Horizontal)", "value": "totex_horizontal"},
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
                    dbc.Tab(multi_chart_dashboard_layout(), label="Dashboard"),
                    dbc.Tab(power_demand_tab_layout(), label="Power Demand Analysis")
                ]
            ),
        ],
        fluid=True
    )
