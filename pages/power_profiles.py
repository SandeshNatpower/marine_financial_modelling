import json
import requests
from urllib.parse import urlencode

import dash
from dash import html, dcc, Input, Output, State, no_update
import dash_bootstrap_components as dbc
import config
import plotly.graph_objects as go
import numpy as np
import pages
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
def load_totex_scenarios(dashboard_data=None):
    """
    Transform raw API dashboard_data into a tuple (years, scenarios).

    The API response (e.g. keys "HFO", "LFO", "MDO") is expected to include:
      - "year"
      - "min_future_opex" (used as TOTEX)
    Other economic metrics (NPV, Result, Cumulative) default to 0 if not available.

    Returns:
      years: sorted list of all distinct years.
      scenarios: dict mapping each scenario key to a dict with:
         "label", "years", "TOTEX", "NPV", "Result", "Cumulative"
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
    Generate a synthetic progression of values (for TOTEX, NPV, etc.) over 26 data points.
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
# ----- Economic / Financial Figures -----
def dwelling_at_berth_pie_figure():
    labels = ["Fuel", "Financing", "Maintenance", "Spares/consumables", "EU ETS", "FuelEU"]
    values = [63, 0, 9, 2, 1, 25]
    fig = go.Figure([go.Pie(labels=labels, values=values, hoverinfo="label+percent", textinfo="label+percent")])
    set_figure_layout(fig, "Dwelling at Berth - Biofuel Blend Minimum")
    return fig

def cashflow_figure(dashboard_data=None):
    """Create cashflow figure from live data"""
    years, scenarios = load_totex_scenarios(dashboard_data)
    fig = go.Figure()
    
    for label, sc in scenarios.items():
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
    """Vertical bar chart for TOTEX comparison from live dashboard data.

    Expects `dashboard_data` to be a dict where each key (scenario) maps to a list of records.
    Each record should have a "min_future_opex" field (which may be null).
    """
    if dashboard_data is None:
        fig = go.Figure().update_layout(title="No Data Available")
        return fig

    labels = []
    values = []
    # Iterate over each scenario (e.g. "MDO", "MDO_With_Shore_Power", etc.)
    for scenario, records in dashboard_data.items():
        # Sum min_future_opex across all records, treating None as 0
        total_opex = sum(record.get("min_future_opex") or 0 for record in records)
        labels.append(scenario)
        values.append(total_opex)

    fig = go.Figure([go.Bar(x=labels, y=values)])
    # Use the shared layout function (assumed defined elsewhere) to set layout
    set_figure_layout(fig, "TOTEX Comparison (Vertical)", "Scenario", "TOTEX")
    return fig


def totex_horizontal_figure(dashboard_data=None):
    """Horizontal bar chart from live data"""
    _, scenarios = load_totex_scenarios(dashboard_data)
    labels, values = [], []
    
    for label, sc in scenarios.items():
        if sc.get("TOTEX"):
            labels.append(label)
            values.append(sc["TOTEX"][-1])
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color="#0A4B8C"
    ))
    set_figure_layout(fig, "TOTEX Comparison (Horizontal)", "TOTEX", "Scenario")
    return fig

def generate_metric_figure(metric, year_range, selected_scenarios, dashboard_data=None):
    """
    Generate a line chart for a selected economic metric (TOTEX, NPV, Result, or Cumulative)
    over a given year range and for the chosen scenarios.
    """
    years_list, scenarios = load_totex_scenarios(dashboard_data)
    if not year_range or len(year_range) != 2:
        start_year, end_year = 2025, 2050
    else:
        start_year, end_year = year_range

    fig = go.Figure()
    for scenario_label, sc_data in scenarios.items():
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

# ----- Energy / Power Demand Figures -----
def load_profile_figure(peak_power=25000, base_load_percent=40):
    """
    Create a line chart for the load profile.
    """
    x_vals, y_vals = generate_load_profile(peak_power, base_load_percent)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode="lines+markers", name="Load Profile"))
    set_figure_layout(fig, "Daily Load Profile", "Hour", "Power (kW)")
    return fig

def projected_energy_demand_figure():
    """
    Create a line chart for projected energy demand.
    """
    x_vals, y_vals = generate_load_profile(peak_power=25000, base_load_percent=40)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode="lines+markers", name="Projected Demand"))
    set_figure_layout(fig, "Projected Energy Demand", "Hour", "Energy Demand (kW)")
    return fig

###############################################################################
# LAYOUT FUNCTIONS
###############################################################################
def financial_metrics_layout():
    """
    Financial Metrics tab with dynamic graphs
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
                        ], md=4, xs=12),
                        dbc.Col([
                            dbc.Label("Scenarios"),
                            dcc.Dropdown(
                                id="scenario-filter",
                                options=[],  # Will be populated by callback
                                multi=True,
                                placeholder="Select scenarios",
                                className="custom-dropdown"
                            )
                        ], md=4, xs=12)
                    ]),
                    html.Br(),
                    dcc.Graph(id="metric-comparison-chart", className="chart-container"),
                    html.Hr(),
                    dcc.Graph(id="totex-horizontal-graph", className="chart-container"),
                    html.Hr(),
                    card_component("Dwelling at Berth - Biofuel Blend Minimum Static values",
                                  dcc.Graph(id="dwelling-pie-chart", className="chart-container")),
                                        dcc.Graph(id="cashflow-graph", className="chart-container"),
                    html.Hr(),
                    dcc.Graph(id="totex-vertical-graph", className="chart-container"),
                    html.Hr(),
                ]
            )
        ],
        className="mb-4"
    )


def power_demand_layout():
    """
    Layout for the Power Demand Analysis tab (energy graphs only).
    """
    return html.Div(
        [
            html.H2("Power Demand Analysis", className='page-title'),
            dbc.Row([
                dbc.Col(
                    card_component(
                        "Load Profile Configuration",
                        [
                            dcc.Graph(id='detail-power-profile-chart', figure=load_profile_figure(), className="chart-container"),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Peak Power Demand (kW)"),
                                    dbc.Input(id='detail-peak-power', type='number', value=25000, className="custom-input")
                                ], md=4, xs=12),
                                dbc.Col([
                                    dbc.Label("Base Load (%)"),
                                    dcc.Slider(
                                        id='detail-base-load',
                                        min=20, max=80, value=40,
                                        marks={i: f"{i}%" for i in range(20, 81, 10)}
                                    )
                                ], md=8, xs=12)
                            ])
                        ]
                    ),
                    md=8, xs=12
                ),
                dbc.Col(
                    card_component(
                        "Energy Storage Options",
                        [
                            dcc.Dropdown(
                                id='detail-storage-type',
                                options=[
                                    {'label': 'Lithium-Ion Battery', 'value': 'li-ion'},
                                    {'label': 'Fuel Cells', 'value': 'fuel-cell'},
                                    {'label': 'Supercapacitors', 'value': 'capacitor'}
                                ],
                                multi=True,
                                placeholder="Select storage options",
                                className="custom-dropdown"
                            ),
                            html.Div(id='detail-storage-results', className='mt-3')
                        ]
                    ),
                    md=4, xs=12
                )
            ]),
            html.Br(),
            dbc.Row(
                dbc.Col(
                    card_component("Projected Energy Demand",
                                   dcc.Graph(id='energy-demand-chart', figure=projected_energy_demand_figure(), className="chart-container")),
                    xs=12
                )
            )
        ]
    )

def multi_chart_dashboard_layout():
    """
    Layout for the Dashboard tab which aggregates all graphs from both the Financial and Power Demand sections.
    The user can select which graphs to display from a checklist, and a debug box is provided.
    """
    # Define checklist options for all available graphs.
    options = [
        {"label": "Metric Comparison", "value": "metric"},
        {"label": "Cashflow Analysis", "value": "cashflow"},
        {"label": "TOTEX (Vertical)", "value": "totex"},
        {"label": "TOTEX (Horizontal)", "value": "totex_horizontal"},
        {"label": "Dwelling at Berth", "value": "dwelling"},
        {"label": "Load Profile", "value": "load_profile"},
        {"label": "Projected Energy Demand", "value": "energy"}
    ]

    return dbc.Card(
        [
            dbc.CardHeader(
                html.H4("Multi-Chart Dashboard", className="card-title", style=HEADER_TEXT_STYLE),
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
    Top-level layout with three tabs.
    Tab order: Dashboard, Financial Metrics, Power Demand Analysis.
    """
    return dbc.Container(
        [
            dbc.Tabs(
                [
                    dbc.Tab(financial_metrics_layout(), label="Financial Metrics"),
                    dbc.Tab(multi_chart_dashboard_layout(), label="Dashboard"),
                    dbc.Tab(power_demand_layout(), label="Power Demand Analysis")
                ]
            )
        ],
        fluid=True
    )
