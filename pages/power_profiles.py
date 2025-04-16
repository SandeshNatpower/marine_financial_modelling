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
    Expects each key in dashboard_data to contain a list of records.
    Each record should include:
      - year
      - nested dictionaries "current" and "future" holding cost components.
    """
    scenarios = {}
    all_years = set()
    
    if dashboard_data and isinstance(dashboard_data, dict):
        for scenario_key, records in dashboard_data.items():
            if not records or not isinstance(records, list):
                continue

            # Sort records by year and filter out records without a valid year.
            sorted_records = sorted(records, key=lambda r: r.get("year", 0))
            valid_records = [r for r in sorted_records if r.get("year") is not None]
            if not valid_records:
                continue

            years = []
            # Future values arrays.
            future_opex = []
            eu_ets = []
            fuel_future_price = []
            maintenance_future = []
            spares_future = []
            fuel_eu = []  # We use the "penalty" key as Fuel EU cost here.

            # Current values arrays.
            current_opex = []
            current_eu_ets = []
            fuel_current_price = []
            maintenance_current = []
            spares_current = []
            current_compliance = []
            
            for record in valid_records:
                year = record["year"]
                years.append(year)
                all_years.add(year)
                future = record.get("future", {})
                current = record.get("current", {})

                future_opex.append(future.get("opex", 0))
                eu_ets.append(future.get("eu_ets", 0))
                fuel_future_price.append(future.get("fuel_price", 0))
                maintenance_future.append(future.get("maintenance", 0))
                spares_future.append(future.get("spare", 0))
                fuel_eu.append(future.get("penalty", 0))
                
                current_opex.append(current.get("opex", 0))
                current_eu_ets.append(current.get("eu_ets", 0))
                fuel_current_price.append(current.get("fuel_price", 0))
                maintenance_current.append(current.get("maintenance", 0))
                spares_current.append(current.get("spare", 0))
                current_compliance.append(current.get("compliance_balance", 0))
            
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


def total_expenditure_stacked_bar_chart(dashboard_data, year_range, view="future"):
    """
    Create a stacked horizontal bar chart comparing Total Expenditure for each scenario
    over the selected year range. Total Expenditure is defined as the sum of:
      fuel_price + maintenance + penalty + spare + eu_ets
    for the chosen view ("current", "future", or "both").

    Expects `dashboard_data` to be a dictionary where each key (scenario name)
    maps to a list of records. Each record is a dict that contains:
      - "year" (an integer)
      - "current": dict with keys "fuel_price", "maintenance", "penalty", "spare", "eu_ets"
      - "future": dict with keys "fuel_price", "maintenance", "penalty", "spare", "eu_ets"
    """
    aggregated_data = {}
    # Loop over each scenario in dashboard_data
    for scenario, records in dashboard_data.items():
        current_total = 0
        future_total = 0
        # Process each record for this scenario.
        for rec in records:
            rec_year = rec.get("year")
            if rec_year is None:
                continue  # Skip records without a valid year.
            # Only include records within the selected year range.
            if year_range[0] <= rec_year <= year_range[1]:
                current_rec = rec.get("current", {})
                future_rec = rec.get("future", {})
                # Sum up the expenditure items for the current view.
                current_total += (current_rec.get("fuel_price", 0) +
                                  current_rec.get("maintenance", 0) +
                                  current_rec.get("penalty", 0) +
                                  current_rec.get("spare", 0) +
                                  current_rec.get("eu_ets", 0))
                future_total += (future_rec.get("fuel_price", 0) +
                                 future_rec.get("maintenance", 0) +
                                 future_rec.get("penalty", 0) +
                                 future_rec.get("spare", 0) +
                                 future_rec.get("eu_ets", 0))
        # Only add the scenario if at least one of the totals is non-zero.
        if current_total != 0 or future_total != 0:
            aggregated_data[scenario] = {"current": current_total, "future": future_total}

    scenario_labels = list(aggregated_data.keys())
    current_vals = [aggregated_data[sc]["current"] for sc in scenario_labels]
    future_vals = [aggregated_data[sc]["future"] for sc in scenario_labels]

    fig = go.Figure()
    if view in ["current", "both"]:
        fig.add_trace(go.Bar(
            x=current_vals,
            y=scenario_labels,
            orientation="h",
            name="Current Total Expenditure",
            marker_color="blue"
        ))
    if view in ["future", "both"]:
        fig.add_trace(go.Bar(
            x=future_vals,
            y=scenario_labels,
            orientation="h",
            name="Future Total Expenditure",
            marker_color="orange"
        ))

    fig.update_layout(
        barmode="stack",
        title=f"Total Expenditure Comparison ({view.capitalize()} View) for Years {year_range[0]}-{year_range[1]}",
        xaxis_title="Total Expenditure",
        yaxis_title="Scenario"
    )
    return fig



def min_future_opex_figure(dashboard_data=None, year_range=(2025, 2050)):
    # Step 1: Load or process the scenario data
    if not dashboard_data:
        # Optionally handle empty data by returning an empty figure
        return go.Figure().update_layout(title="No Data Available")

    _, scenarios_data = load_min_future_opex_scenarios(dashboard_data)
    if not scenarios_data:
        return go.Figure().update_layout(title="No scenario data available")

    start_year, end_year = year_range

    # Step 2: Accumulate the sum of Future Opex in the given year range
    scenario_labels = []
    scenario_totals = []
    for scenario, sc_info in scenarios_data.items():
        # Ensure we have both "years" and "Future Opex"
        years_list = sc_info.get("years", [])
        future_opex_list = sc_info.get("Future Opex", [])

        if not years_list or not future_opex_list:
            # Skip scenarios lacking the needed structure
            continue

        # Sum Opex only for years that fall into [start_year, end_year]
        total_opex = 0
        for yr, val in zip(years_list, future_opex_list):
            if start_year <= yr <= end_year:
                total_opex += val

        # Keep track of scenario label and total
        scenario_labels.append(scenario)
        scenario_totals.append(total_opex)

    # Step 3: Build a horizontal bar chart
    fig = go.Figure(
        go.Bar(
            x=scenario_totals,
            y=scenario_labels,
            orientation="h",
            marker_color="#0A4B8C",
            text=[f"{val:,.0f}" for val in scenario_totals],  # optional: display with commas
            textposition="auto"  # place text automatically
        )
    )

    # Step 4: Customize layout 
    # (Replace set_figure_layout with your own or just inline the config)
    fig.update_layout(
        title=f"Future Opex (Summed {start_year}–{end_year})",
        xaxis_title="Total Future Opex",
        yaxis_title="Scenario",
        margin=dict(l=140, r=40, t=60, b=50),  # widen left margin for scenario labels
    )

    return fig



def create_single_year_stacked_bar(filtered_data, chosen_year):
    """
    Build a grouped stacked bar chart for a single selected year, comparing current versus future costs.
    Expects filtered_data to be a dictionary where each key (scenario) maps to a list of records.
    Each record is a dict with:
      - "year": an integer,
      - "current": dict with cost components (e.g. "compliance_balance", "fuel_price", etc.),
      - "future": dict with cost components.
    """
    # Define the components
    components = {
        "Compliance": "compliance_balance",
        "Fuel": "fuel_price",
        "Maintenance": "maintenance",
        "Opex": "opex",
        "Penalty": "penalty",
        "Spare": "spare",
        "EU ETS": "eu_ets"
    }
    
    # Define colors for components
    colors = {
        "Compliance": {"Future": "#636EFA", "Current": "#3B46C4"},  # Blue shades
        "Fuel": {"Future": "#EF553B", "Current": "#BA2E19"},        # Red shades
        "Maintenance": {"Future": "#00CC96", "Current": "#00A377"}, # Green shades
        "Opex": {"Future": "#AB63FA", "Current": "#8A3BD8"},        # Purple shades
        "Penalty": {"Future": "#FFA15A", "Current": "#E67F35"},     # Orange shades
        "Spare": {"Future": "#19D3F3", "Current": "#06A6C2"},       # Cyan shades
        "EU ETS": {"Future": "#FF6692", "Current": "#D93B63"}       # Pink shades
    }

    # Collect scenarios with data for the chosen year
    scenarios_data = {}
    
    for scenario, records in filtered_data.items():
        # Look for a record with the matching chosen_year
        record = next((r for r in records if r.get("year") == chosen_year), None)
        if record:
            scenarios_data[scenario] = {
                "current": record.get("current", {}),
                "future": record.get("future", {})
            }
    
    # If no scenarios have matching records, return an empty figure
    if not scenarios_data:
        return go.Figure().update_layout(title=f"No data available for year {chosen_year}")
    
    # Create the figure
    fig = go.Figure()
    
    # Process each scenario
    for scenario in scenarios_data:
        # Add grouped bars for each cost component, showing current and future values
        for period in ["Current", "Future"]:
            period_lower = period.lower()
            
            # Add bars for each component in this period (stacked)
            for comp_name, comp_key in components.items():
                value = scenarios_data[scenario][period_lower].get(comp_key, 0)
                
                # Skip components with zero value to reduce clutter
                if abs(value) < 0.01:
                    continue
                
                fig.add_trace(go.Bar(
                    y=[scenario],  # For horizontal bars, categories go on y-axis
                    x=[value],     # Values on x-axis
                    name=f"{period} {comp_name}",
                    orientation="h",
                    marker_color=colors[comp_name][period],
                    legendgroup=f"{period}_{comp_name}",
                    offsetgroup=period_lower,  # Group bars by period (current/future)
                    hovertemplate=f"{period} {comp_name}: %{{x:.2f}}<extra></extra>"
                ))
    
    # Update layout
    fig.update_layout(
        barmode="stack",  # Stack bars within each group
        title=f"Current vs Future Cost Breakdown - {chosen_year}",
        xaxis_title="Cost",
        yaxis_title="Scenario",
        legend_traceorder="reversed",  # Reverse legend order to match stacking order
        bargap=0.15,  # Gap between different scenarios
        bargroupgap=0.1,  # Gap between current and future groups
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
    Layout for the Financial Metrics tab with various filters and graphs.
    Note: A new dcc.Dropdown with id "single-year-dropdown" has been added
    for selecting the year for the single-year breakdown.
    """
    HEADER_STYLE = {"backgroundColor": "#f8f9fa"}
    HEADER_TEXT_STYLE = {"color": "#343a40"}

    # Create options for the dropdown. In this example we include an "all" option plus years 2025-2050.
    year_options = [{"label": "All", "value": "all"}] + [
        {"label": str(year), "value": str(year)} for year in range(2025, 2051)
    ]

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
                        ], md=4, xs=12),
                        dbc.Col([
                            dbc.Label("Scenario Filter"),
                            dcc.Dropdown(
                                id="scenario-filter",
                                multi=True,
                                className="custom-dropdown"
                            )
                        ], md=3, xs=12),
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
                        ], md=2, xs=12)
                    ]),
                    html.Br(),
                    dbc.Row(
                        dbc.Col([
                            # Single-Year Dropdown added to support the associated callback.
                            dbc.Label("Select Single Year for Breakdown"),
                            dcc.Dropdown(
                                id="single-year-dropdown",
                                options=year_options,
                                value="2026",
                                clearable=False,
                                className="custom-dropdown"
                            )
                        ], md=4, xs=12)
                    ),
                    html.Br(),
                    dcc.Graph(id="metric-comparison-chart", className="chart-container"),
                    html.Hr(),
                    dcc.Graph(id="min-future-opex", className="chart-container"),
                    html.Hr(),
                    dcc.Graph(id="financial-pie-chart", className="chart-container"),
                    html.Hr(),
                    dcc.Graph(id="total-expenditure", className="chart-container"),
                    html.Hr(),
                    dcc.Graph(id="single-year-breakdown", className="chart-container"),
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
                )

            ]),
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader("Fuel EU Penalty"),
                        dbc.CardBody([
                            dcc.Graph(
                                id="dashboard-compliance-chart",
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
                        id="scenario-filter-global",
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
                    dbc.Tab(multi_chart_dashboard_layout(), label="Financial Dashboard")
                ]
            ),
            
            # Store component for scenario data
            dcc.Store(id="dashboard-scenarios-store")
        ],
        fluid=True
    )





