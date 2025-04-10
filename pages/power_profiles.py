import json
from altair import value
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
    from pages.input_module import DEFAULT_VESSEL
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
def generate_scenario_progression(initial_values, years=26):
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
def generate_fallback_scenarios():
    """
    Generate synthetic data with the same structure as the API response.
    Each scenario maps to a list of records. Each record is a dict with keys:
    'blend_percentage', 'current', 'future', and 'year'.
    """
    years = list(range(2025, 2051))
    fallback = {}

    # For example, create a fallback for "BIO-DIESEL"
    fallback["BIO-DIESEL"] = []
    for yr in years:
        record = {
            "blend_percentage": 0,
            "current": {
                "compliance_balance": random.uniform(1e6, 2e6),
                "eu_ets": random.uniform(0, 5e6),
                "fuel_price": random.uniform(1e7, 2e7),
                "maintenance": random.uniform(1e5, 5e5),
                "opex": random.uniform(1e7, 2e7),
                "penalty": random.uniform(0, 5e5),
                "spare": random.uniform(5e4, 5e5)
            },
            "future": {
                "compliance_balance": random.uniform(1e6, 2e6),
                "eu_ets": random.uniform(0, 5e6),
                "fuel_price": random.uniform(1e7, 2e7),
                "maintenance": random.uniform(1e5, 5e5),
                "opex": random.uniform(1e7, 2e7),
                "penalty": random.uniform(0, 5e5),
                "spare": random.uniform(5e4, 5e5)
            },
            "year": yr
        }
        fallback["BIO-DIESEL"].append(record)
    return years, fallback

    
def create_fallback_pie(labels, colors):
    """Create fallback pie chart visualization"""
    values = [45, 15, 5, 20, 10, 5]  # Example distribution
    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        marker_colors=colors,
        textinfo="label+percent"
    ))
    fig.update_layout(title="Dwelling at Berth - Sample Distribution")
    return fig

def load_min_future_opex_scenarios(dashboard_data=None):
    """
    Process the nested API structure with current/future breakdown.
    """
    scenarios = {}
    all_years = set()
    
    if dashboard_data and isinstance(dashboard_data, dict):
        for scenario_key, records in dashboard_data.items():
            if not records or not isinstance(records, list):
                continue

            # Sort records by year and filter out records without a year.
            sorted_records = sorted(records, key=lambda r: r.get("year", 0))
            valid_records = [r for r in sorted_records if r.get("year") is not None]
            if not valid_records:
                continue

            # Prepare arrays for future values.
            years = []
            future_opex = []           # future["opex"]
            eu_ets = []                # future["eu_ets"]
            fuel_future_price = []     # future["fuel_price"]
            maintenance_future = []    # future["maintenance"]
            spares_future = []         # future["spare"]
            fuel_eu = []               # future["penalty"]  <-- Changed from "fuel_eu_penalty"

            # Prepare arrays for current values.
            current_opex = []          # current["opex"]
            current_eu_ets = []        # current["eu_ets"]
            fuel_current_price = []    # current["fuel_price"]
            maintenance_current = []   # current["maintenance"]
            spares_current = []        # current["spare"]
            current_compliance = []    # current["compliance_balance"]

            for record in valid_records:
                if not isinstance(record, dict):
                    continue

                # Extract the nested dictionaries.
                future = record.get("future", {}) if isinstance(record, dict) else {}
                current = record.get("current", {}) if isinstance(record, dict) else {}

                # Add year and future values.
                years.append(record["year"])
                future_opex.append(future.get("opex", 0))
                eu_ets.append(future.get("eu_ets", 0))
                fuel_future_price.append(future.get("fuel_price", 0))
                maintenance_future.append(future.get("maintenance", 0))
                spares_future.append(future.get("spare", 0))
                fuel_eu.append(future.get("penalty", 0))  # Changed from "fuel_eu_penalty"

                # Add current values.
                current_opex.append(current.get("opex", 0))
                current_eu_ets.append(current.get("eu_ets", 0))
                fuel_current_price.append(current.get("fuel_price", 0))
                maintenance_current.append(current.get("maintenance", 0))
                spares_current.append(current.get("spare", 0))
                current_compliance.append(current.get("compliance_balance", 0))

                # Add this year to the set of all years
                all_years.add(record["year"])

            # Build a summary structure for the scenario.
            scenarios[scenario_key] = {
                "label": scenario_key,
                "years": years,
                "Future Opex": future_opex,
                "EU ETS": eu_ets,
                "Fuel Future Price": fuel_future_price,
                "Maintenance Future": maintenance_future,
                "Spares Future": spares_future,
                "Fuel EU": fuel_eu,
                "Current Opex": current_opex,
                "Current EU ETS": current_eu_ets,
                "Fuel Current Price": fuel_current_price,
                "Maintenance Current": maintenance_current,
                "Spares Current": spares_current,
                "Current Compliance": current_compliance
            }
        
        if scenarios:
            return sorted(all_years), scenarios

    # Fallback synthetic data if no API data is available.
    return generate_fallback_scenarios()


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
    Create pie charts for cost breakdown visualization for each selected scenario.
    Only shows: Fuel, Maintenance, Spares, EU ETS, and FuelEU (penalty)
    """
    labels = ["Fuel", "Maintenance", "Spares", "EU ETS", "FuelEU"]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
    
    if not selected_scenarios or not dashboard_data:
        return create_fallback_pie(labels, colors)
    
    # Calculate grid layout for subplots.
    max_cols = 3
    total = len(selected_scenarios)
    cols = min(max_cols, total)
    rows = ceil(total / cols)
    fig = make_subplots(
        rows=rows, cols=cols,
        specs=[[{"type": "domain"}] * cols] * rows,
        subplot_titles=selected_scenarios
    )
    
    for i, scenario in enumerate(selected_scenarios):
        records = dashboard_data.get(scenario, [])
        if not records:
            continue
        
        # Sum up values across all records for each cost component.
        totals = {
            "Fuel": 0,
            "Maintenance": 0,
            "Spares": 0,
            "EU ETS": 0,
            "FuelEU": 0
        }
        
        for record in records:
            if not isinstance(record, dict):
                print(f"Warning: found non-dict record in {scenario}: {record}")
                continue
            future = record.get("future", {}) if isinstance(record, dict) else {}
            if isinstance(future, dict):
                totals["Fuel"]         += future.get("fuel_price")  or 0
                totals["Maintenance"]  += future.get("maintenance") or 0
                totals["Spares"]       += future.get("spare")       or 0
                totals["EU ETS"]       += future.get("eu_ets")      or 0
                # Correction - using "penalty" instead of "fuel_eu_penalty"
                totals["FuelEU"]       += future.get("penalty")     or 0
        
        total_sum = sum(totals.values()) or 1  # avoid division by zero
        values = [v / total_sum * 100 for v in totals.values()]
        
        row = (i // cols) + 1
        col = (i % cols) + 1
        
        fig.add_trace(
            go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors,
                textinfo="percent+label",
                hoverinfo="value",
                showlegend=False
            ),
            row=row,
            col=col
        )
    
    fig.update_layout(
        title_text="Dwelling at Berth - Cost Distribution Breakdown",
        height=max(400, rows * 400),
        uniformtext_minsize=12,
        uniformtext_mode="hide"
    )
    return fig

def min_future_opex_figure(dashboard_data=None):
    """
    Create a horizontal bar chart for Future Opex (from future["opex"]) using the latest year for each scenario.
    """
    _, scenarios_data = load_min_future_opex_scenarios(dashboard_data)
    labels = []
    values = []
    for scenario, sc in scenarios_data.items():
        # If the scenario data is a dict, get "Future Opex"; if it's a list, assume it is the opex list.
        if isinstance(sc, dict):
            future_opex_list = sc.get("Future Opex", [])
        elif isinstance(sc, list):
            future_opex_list = sc
        else:
            future_opex_list = []
        
        if future_opex_list and isinstance(future_opex_list, list):
            labels.append(scenario)
            values.append(future_opex_list[-1])
            
    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation="h",
        marker_color="#0A4B8C"
    ))
    set_figure_layout(fig, "Future Opex Comparison", "Future Opex", "Scenario")
    return fig




def create_single_year_stacked_bar(filtered_data, chosen_year):
    """
    Build a grouped stacked bar chart for a single selected year, comparing current versus future costs.
    """
    scenario_labels = []
    curr_components = {"Compliance": [], "Fuel": [], "Maintenance": [], "Opex": [], "Penalty": [], "Spare": [], "EU ETS": []}
    fut_components = {"Compliance": [], "Fuel": [], "Maintenance": [], "Opex": [], "Penalty": [], "Spare": [], "EU ETS": []}

    for scenario, records in filtered_data.items():
        record = next((r for r in records if r.get("year") == chosen_year), None)
        if record:
            scenario_labels.append(scenario)
            curr = record.get("current", {})
            fut = record.get("future", {})
            curr_components["Compliance"].append(curr.get("compliance_balance", 0))
            curr_components["Fuel"].append(curr.get("fuel_price", 0))
            curr_components["Maintenance"].append(curr.get("maintenance", 0))
            curr_components["Opex"].append(curr.get("opex", 0))
            curr_components["Penalty"].append(curr.get("penalty", 0))
            curr_components["Spare"].append(curr.get("spare", 0))
            curr_components["EU ETS"].append(curr.get("eu_ets", 0))
            fut_components["Compliance"].append(fut.get("compliance_balance", 0))
            fut_components["Fuel"].append(fut.get("fuel_price", 0))
            fut_components["Maintenance"].append(fut.get("maintenance", 0))
            fut_components["Opex"].append(fut.get("opex", 0))
            fut_components["Penalty"].append(fut.get("penalty", 0))
            fut_components["Spare"].append(fut.get("spare", 0))
            fut_components["EU ETS"].append(fut.get("eu_ets", 0))
    
    fig = go.Figure()
    colors = {
        "Compliance": "#636EFA",
        "Fuel": "#EF553B",
        "Maintenance": "#00CC96",
        "Opex": "#AB63FA",
        "Penalty": "#FFA15A",
        "Spare": "#19D3F3",
        "EU ETS": "#FF6692"
    }
    for comp in curr_components.keys():
        # Current cost traces
        fig.add_trace(go.Bar(
            x=curr_components[comp],
            y=scenario_labels,
            name=f"Current {comp}",
            orientation="h",
            marker_color=colors.get(comp, "#000000"),
            offsetgroup="current",
            legendgroup=comp,
            hovertemplate=f"Current {comp}: %{{value:.2f}}<extra></extra>"
        ))
        # Future cost traces
        fig.add_trace(go.Bar(
            x=fut_components[comp],
            y=scenario_labels,
            name=f"Future {comp}",
            orientation="h",
            marker_color=colors.get(comp, "#777777"),
            offsetgroup="future",
            legendgroup=comp,
            hovertemplate=f"Future {comp}: %{{value:.2f}}<extra></extra>"
        ))
    fig.update_layout(
        barmode="stack",
        title=f"Current vs Future Cost Breakdown - {chosen_year}",
        xaxis_title="Cost",
        yaxis_title="Scenario"
    )
    return fig

def generate_metric_figure(metric, year_range, selected_scenarios, dashboard_data=None, data_view="future"):
    """
    Generate a line chart for the selected metric over the provided year range.
    data_view parameter controls whether to plot "future", "current", or "both" data
    """
    fig = go.Figure()
    
    if not dashboard_data:
        # Return empty figure if no data
        return fig
    
    start_year, end_year = (2025, 2050) if not year_range or len(year_range) != 2 else year_range
    
    for scenario_label in selected_scenarios:
        if scenario_label not in dashboard_data:
            continue
        
        records = dashboard_data[scenario_label]
        
        # Plot current data if requested
        if data_view in ["current", "both"]:
            x_vals = []
            y_vals = []
            
            for record in records:
                year = record.get("year")
                if not year or not (start_year <= year <= end_year):
                    continue
                
                current_dict = record.get("current", {})
                if metric in current_dict:
                    metric_value = current_dict.get(metric, 0)
                    x_vals.append(year)
                    y_vals.append(metric_value)
            
            if x_vals and y_vals:
                fig.add_trace(go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    mode="lines+markers",
                    name=f"{scenario_label} (Current)",
                    line=dict(dash="dot")
                ))
        
        # Plot future data if requested
        if data_view in ["future", "both"]:
            x_vals = []
            y_vals = []
            
            for record in records:
                year = record.get("year")
                if not year or not (start_year <= year <= end_year):
                    continue
                
                future_dict = record.get("future", {})
                if metric in future_dict:
                    metric_value = future_dict.get(metric, 0)
                    x_vals.append(year)
                    y_vals.append(metric_value)
            
            if x_vals and y_vals:
                fig.add_trace(go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    mode="lines+markers",
                    name=f"{scenario_label} (Future)"
                ))
    
    currency_sym = config.CURRENCIES.get("EUR", {}).get("symbol", "€")
    set_figure_layout(fig, f"{metric.title()} Comparison", "Year", f"{metric.title()} ({currency_sym})")
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
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
import dash
from dash import dcc, html, dash_table, callback_context
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import config  # Assume config.FUEL_OPTIONS and config.CURRENCIES exists

# Define some global styles for headers (adjust as needed)
HEADER_STYLE = {"backgroundColor": "#0A4B8C", "padding": "10px"}
HEADER_TEXT_STYLE = {"color": "white"}

# ----------------------------
# Financial Metrics Layout
# ----------------------------
def financial_metrics_layout():
    """
    Financial Metrics tab layout with view toggle for current/future data.
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
                                    {"label": "Opex", "value": "opex"},
                                    {"label": "EU ETS", "value": "eu_ets"},
                                    {"label": "Fuel Price", "value": "fuel_price"},
                                    {"label": "Maintenance", "value": "maintenance"},
                                    {"label": "Penalty", "value": "penalty"},
                                    {"label": "Spare", "value": "spare"},
                                    {"label": "Compliance Balance", "value": "compliance_balance"}
                                ],
                                value="opex",
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
                                marks={
                                    yr: {"label": str(yr), "style": {"transform": "rotate(45deg)", "whiteSpace": "nowrap"}}
                                    for yr in range(2025, 2051, 5)
                                },
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ], md=6, xs=12),
                        dbc.Col([
                            dbc.Label("Data View"),
                            dcc.RadioItems(
                                id="data-view-selector",
                                options=[
                                    {"label": "Future", "value": "future"},
                                    {"label": "Current", "value": "current"},
                                    {"label": "Both", "value": "both"}
                                ],
                                value="future",
                                inline=True,
                                className="mb-2"
                            )
                        ], md=3, xs=12)
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

# ----------------------------
# Combined Dashboard Layout
# ----------------------------
def financial_metrics_layout():
    """
    Financial Metrics tab layout with view toggle for current/future data.
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
                                    {"label": "Opex", "value": "opex"},
                                    {"label": "EU ETS", "value": "eu_ets"},
                                    {"label": "Fuel Price", "value": "fuel_price"},
                                    {"label": "Maintenance", "value": "maintenance"},
                                    {"label": "Penalty", "value": "penalty"},
                                    {"label": "Spare", "value": "spare"},
                                    {"label": "Compliance Balance", "value": "compliance_balance"}
                                ],
                                value="opex",
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
                                marks={
                                    yr: {"label": str(yr), "style": {"transform": "rotate(45deg)", "whiteSpace": "nowrap"}}
                                    for yr in range(2025, 2051, 5)
                                },
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ], md=6, xs=12),
                        dbc.Col([
                            dbc.Label("Data View"),
                            dcc.RadioItems(
                                id="data-view-selector",
                                options=[
                                    {"label": "Future", "value": "future"},
                                    {"label": "Current", "value": "current"},
                                    {"label": "Both", "value": "both"}
                                ],
                                value="future",
                                inline=True,
                                className="mb-2"
                            )
                        ], md=3, xs=12)
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

# ----------------------------
# Executive Dashboard Layout (Tab 2)
# ----------------------------
def multi_chart_dashboard_layout():
    """
    Redesigned Dashboard layout that provides an executive summary based on the actual data structure.
    Displays financial metrics across years in an engaging and interactive format with additional guidance.
    A separate filter for the cost breakdown year is provided.
    """
    return dbc.Card([
        dbc.CardHeader(
            html.Div([
                html.H4("Executive Dashboard", className="card-title", style=HEADER_TEXT_STYLE),
                html.P("Explore the trends and key financial metrics across years for various scenarios.", 
                       className="text-muted", style={"fontSize": "0.9rem"})
            ]),
            style=HEADER_STYLE
        ),
        dbc.CardBody([
            # Top controls row for time series visualization
            dbc.Row([
                dbc.Col([
                    dbc.Label("Year Range (Time Series)"),
                    dcc.RangeSlider(
                        id="dashboard-year-range",
                        min=2025,
                        max=2050,
                        value=[2025, 2035],
                        marks={yr: {"label": str(yr), "style": {"transform": "rotate(45deg)"}} for yr in range(2025, 2050, 1)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    dbc.Tooltip("Select the range of years to display for time series charts.", target="dashboard-year-range")
                ], md=6, xs=12),
                dbc.Col([
                    dbc.Label("Scenario"),
                    dcc.Dropdown(
                        id="dashboard-scenario-dropdown",
                        options=[],  # Updated dynamically via callback
                        clearable=False,
                        className="custom-dropdown",
                        placeholder="Select scenario"
                    )
                ], md=3, xs=12),
                dbc.Col([
                    dbc.Label("View"),
                    dcc.RadioItems(
                        id="dashboard-view-type",
                        options=[
                            {"label": "Future", "value": "future"},
                            {"label": "Current", "value": "current"},
                            {"label": "Comparison", "value": "both"}
                        ],
                        value="future",
                        inline=True,
                        className="mb-2"
                    ),
                    dbc.Tooltip("Toggle between Future, Current or a comparison of both views.", target="dashboard-view-type")
                ], md=3, xs=12)
            ], className="mb-4"),
            
            # Separate control for selecting the Cost Breakdown Year
            dbc.Row([
                dbc.Col([
                    dbc.Label("Cost Breakdown Year"),
                    dcc.Dropdown(
                        id="dashboard-cost-breakdown-year",
                        options=[],  # Updated dynamically by callback based on available years
                        clearable=False,
                        placeholder="Select cost breakdown year"
                    ),
                    dbc.Tooltip("Select a specific year to display its cost breakdown.", target="dashboard-cost-breakdown-year")
                ], md=4, xs=12)
            ], className="mb-4"),
            
            html.Hr(),
            
            # KPI Cards Row with interactive tooltips
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.H5("Avg. OPEX", className="card-title text-center"),
                                html.I(className="bi bi-currency-euro", style={"fontSize": "1.5rem", "color": "#1F77B4"}),
                                html.H3(id="kpi-avg-opex", className="text-center text-primary"),
                                html.P(id="kpi-opex-trend", className="text-center", style={"fontSize": "0.8rem"})
                            ])
                        ])
                    ], className="h-100 shadow-sm"),
                    md=3, xs=6
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.H5("Compliance Balance", className="card-title text-center"),
                                html.I(className="bi bi-bar-chart-line", style={"fontSize": "1.5rem", "color": "#2CA02C"}),
                                html.H3(id="kpi-compliance", className="text-center text-success"),
                                html.P(id="kpi-compliance-status", className="text-center", style={"fontSize": "0.8rem"})
                            ])
                        ])
                    ], className="h-100 shadow-sm"),
                    md=3, xs=6
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.H5("Penalty Reduction", className="card-title text-center"),
                                html.I(className="bi bi-graph-up", style={"fontSize": "1.5rem", "color": "#D62728"}),
                                html.H3(id="kpi-penalty", className="text-center text-danger"),
                                html.P(id="kpi-penalty-savings", className="text-center", style={"fontSize": "0.8rem"})
                            ])
                        ])
                    ], className="h-100 shadow-sm"),
                    md=3, xs=6
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.H5("Blend Percentage", className="card-title text-center"),
                                html.I(className="bi bi-pie-chart", style={"fontSize": "1.5rem", "color": "#17A2B8"}),
                                html.H3(id="kpi-blend", className="text-center text-info"),
                                html.P(id="kpi-blend-trend", className="text-center", style={"fontSize": "0.8rem"})
                            ])
                        ])
                    ], className="h-100 shadow-sm"),
                    md=3, xs=6
                )
            ], className="mb-4"),
            
            # Charts Grid: Two rows of charts
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader("OPEX Trend"),
                        dbc.CardBody([
                            dcc.Graph(
                                id="dashboard-opex-trend",
                                config={'displayModeBar': False},
                                className="dashboard-chart"
                            )
                        ])
                    ], className="shadow-sm"),
                    md=6, xs=12, className="mb-3"
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader("Compliance Progression"),
                        dbc.CardBody([
                            dcc.Graph(
                                id="dashboard-compliance-chart",
                                config={'displayModeBar': False},
                                className="dashboard-chart"
                            )
                        ])
                    ], className="shadow-sm"),
                    md=6, xs=12, className="mb-3"
                )
            ]),
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader("Cost Breakdown"),
                        dbc.CardBody([
                            dcc.Graph(
                                id="dashboard-cost-breakdown",
                                config={'displayModeBar': False},
                                className="dashboard-chart"
                            )
                        ])
                    ], className="shadow-sm"),
                    md=6, xs=12, className="mb-3"
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader("EU ETS Impact"),
                        dbc.CardBody([
                            dcc.Graph(
                                id="dashboard-eu-ets-chart",
                                config={'displayModeBar': False},
                                className="dashboard-chart"
                            )
                        ])
                    ], className="shadow-sm"),
                    md=6, xs=12, className="mb-3"
                )
            ]),
            
            # Bottom row with annual metrics table
            dbc.Row(
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader("Annual Financial Metrics"),
                        dbc.CardBody([
                            html.Div(id="dashboard-metrics-table")
                        ])
                    ], className="shadow-sm"),
                    className="mb-3"
                )
            )
        ])
    ], className="mb-4")


# ----------------------------
# Main App Layout
# ----------------------------
def layout():
    """
    Top-level layout that includes a global scenario filter and two tabs:
    Financial Metrics and Combined Dashboard.
    """
    return dbc.Container(
        [
            # Global Scenario Filter Row
            dbc.Row([
                dbc.Col(
                    dcc.Dropdown(
                        id="scenario-filter",
                        options=config.FUEL_OPTIONS,
                        multi=True,
                        value=["MDO", "LNG"],  # Preselect example fuels
                        placeholder="Select additional scenarios...",
                        className="mb-2"
                    ),
                    width=8
                ),
                dbc.Col(
                    dbc.Button(
                        "Calculate Scenarios", 
                        id="calculate-scenarios-btn",
                        color="primary",
                        className="w-100"
                    ),
                    width=4
                )
            ], className="mb-4"),

            # Tabs: Financial Metrics and Combined Dashboard
            dbc.Tabs(
                [
                    dbc.Tab(financial_metrics_layout(), label="Financial Metrics"),
                    dbc.Tab(multi_chart_dashboard_layout(), label="Dashboard")
                ]
            ),
            
            # Store component for scenario data
            dcc.Store(id="dashboard-scenarios-store")
        ],
        fluid=True
    )





