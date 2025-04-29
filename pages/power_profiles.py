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
import pages.output_module

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
        last, prev = result[-1], result[-2]
        trend = last - prev
        variation = trend * (1 + np.random.uniform(-0.1, 0.1))
        noise = np.random.normal(0, abs(trend) * 0.1)
        result.append(last + variation + noise)
    return result

def generate_fallback_scenarios():
    """
    Returns (years, fallback_data) where fallback_data matches the flat API:
      each scenario → list of records with flat keys.
    """
    years = list(range(2025, 2051))
    fallback = {}
    for scenario in ["BIO-DIESEL", "MDO", "HVO"]:
        fallback[scenario] = []
        for yr in years:
            fallback[scenario].append({
                "blend_percentage": random.choice([0.0, 0.1, 0.2]),
                "eu_ets":            random.uniform(0, 1e6),
                "fuel_price":        random.uniform(1e7, 2e7),
                "maintenance":       random.uniform(1e5, 5e5),
                "opex":              random.uniform(1e7, 2e7),
                "penalty":           random.uniform(0, 5e5),
                "spare":             random.uniform(5e4, 5e5),
                "year": yr
            })
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
    From flat API data, extract for each scenario:
      - 'years': list of years
      - 'opex': list of opex values
    Returns (sorted_years, {scenario: {'years':…, 'opex':…}, …})
    """
    if not dashboard_data or not isinstance(dashboard_data, dict):
        return generate_fallback_scenarios()

    all_years = set()
    scenarios  = {}
    for scenario, records in dashboard_data.items():
        sorted_recs = sorted([r for r in records if r.get("year") is not None],
                              key=lambda r: r["year"])
        years = [r["year"] for r in sorted_recs]
        opex  = [r.get("opex", 0)     for r in sorted_recs]
        if years:
            scenarios[scenario] = {"years": years, "opex": opex}
            all_years.update(years)

    if scenarios:
        return sorted(all_years), scenarios
    else:
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


###############################################################################
# FIGURE FUNCTIONS
###############################################################################
def dwelling_at_berth_pie_figure(dashboard_data, selected_scenarios=None):
    """
    Create a grid of pie charts showing cost‑component shares per scenario.
    Components: Fuel, Maintenance, Spares, EU ETS, and FuelEU (penalty),
    all summed over every record in each scenario’s list.
    """
    labels = ["Fuel", "Maintenance", "Spares", "EU ETS", "FuelEU"]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

    if not selected_scenarios or not dashboard_data:
        return create_fallback_pie(labels, colors)

    total = len(selected_scenarios)
    cols  = min(3, total)
    rows  = ceil(total / cols)
    fig   = make_subplots(
        rows=rows, cols=cols,
        specs=[[{"type": "domain"}]*cols for _ in range(rows)],
        subplot_titles=selected_scenarios
    )

    for idx, scenario in enumerate(selected_scenarios):
        records = dashboard_data.get(scenario, [])
        # initialize sums
        sums = {lab: 0 for lab in labels}

        for rec in records:
            sums["Fuel"]        += rec.get("fuel_price", 0)
            sums["Maintenance"] += rec.get("maintenance", 0)
            sums["Spares"]      += rec.get("spare", 0)
            sums["EU ETS"]      += rec.get("eu_ets", 0)
            sums["FuelEU"]      += rec.get("penalty", 0)

        total_sum = sum(sums.values()) or 1
        values    = [sums[lab] / total_sum * 100 for lab in labels]

        row = idx // cols + 1
        col = idx % cols  + 1

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
        title_text="Dwelling at Berth – Cost Distribution",
        height=rows * 350,
        uniformtext_minsize=12,
        uniformtext_mode="hide",
        margin=dict(t=80, b=40, l=40, r=40)
    )
    return fig


def min_future_opex_figure(dashboard_data=None, year_range=(2025, 2050)):
    """
    Sum each scenario’s opex over the year_range and plot a horizontal bar chart.
    """
    if not dashboard_data:
        return go.Figure().update_layout(title="No Data Available")

    start, end = year_range
    aggregated = {}
    for scenario, records in dashboard_data.items():
        total = sum(
            rec.get("opex", 0)
            for rec in records
            if rec.get("year") is not None and start <= rec["year"] <= end
        )
        if total:
            aggregated[scenario] = total

    scenarios = list(aggregated.keys())
    totals    = [aggregated[s] for s in scenarios]

    fig = go.Figure(
        go.Bar(
            x=totals,
            y=scenarios,
            orientation="h",
            marker_color="steelblue",
            text=[f"€{v:,.0f}" for v in totals],
            textposition="auto"
        )
    )
    fig.update_layout(
        title=f"Summed Opex per Scenario ({start}–{end})",
        xaxis_title="Total Opex (€)",
        yaxis_title="Scenario",
        margin=dict(l=140, r=40, t=60, b=50)
    )
    return fig




import plotly.graph_objects as go

def create_range_stacked_bar(
    dashboard_data,
    year_range=(2025, 2050),
    currency_symbol="€",
    conversion_rate=1.0
):
    """
    Build a horizontal stacked‐bar of all cost components aggregated
    across the given year_range, for each scenario. Each bar segment
    shows its value directly, and hovering still gives details.

    Args:
        dashboard_data (dict): { scenario_name: [ {year, fuel_price, ...}, ... ], ... }
        year_range (tuple): (start_year, end_year)
        currency_symbol (str): e.g. "€", "$"
        conversion_rate (float): multiply raw values by this to convert into target currency

    Returns:
        plotly.graph_objs.Figure
    """
    components = {
        "Fuel":        "fuel_price",
        "Maintenance": "maintenance",
        "Penalty":     "penalty",
        "Spare":       "spare",
        "EU ETS":      "eu_ets",
    }
    colors = {
        "Fuel":        "#EF553B",
        "Maintenance": "#00CC96",
        "Penalty":     "#FFA15A",
        "Spare":       "#19D3F3",
        "EU ETS":      "#FF6692",
    }

    start, end = year_range

    # 1) aggregate per scenario
    aggregated = {}
    for scenario, records in dashboard_data.items():
        sums = {c: 0.0 for c in components}
        for rec in records:
            yr = rec.get("year")
            if yr is None or yr < start or yr > end:
                continue
            for comp_name, key in components.items():
                raw = rec.get(key, 0) or 0
                sums[comp_name] += raw * conversion_rate
        if any(v != 0 for v in sums.values()):
            aggregated[scenario] = sums

    # 2) handle empty
    if not aggregated:
        return go.Figure().update_layout(
            title=f"No data between {start} and {end}"
        )

    # 3) sort scenarios by total
    scenarios = sorted(
        aggregated.keys(),
        key=lambda sc: sum(aggregated[sc].values()),
        reverse=True
    )

    # 4) rank components by total across all scenarios
    comp_totals = {
        comp: sum(aggregated[sc][comp] for sc in scenarios)
        for comp in components
    }
    sorted_comps = sorted(
        components.keys(),
        key=lambda c: comp_totals[c],
        reverse=True
    )

    # 5) build traces with text displayed
    fig = go.Figure()
    for comp in sorted_comps:
        values = [aggregated[sc][comp] for sc in scenarios]
        fig.add_trace(
            go.Bar(
                y=scenarios,
                x=values,
                name=comp,
                orientation="h",
                marker_color=colors[comp],
                text=[f"{currency_symbol}{v:,.0f}" for v in values],
                textposition="auto",
                hovertemplate=(
                    "Scenario: %{y}<br>"
                    f"{comp}: {currency_symbol}%{{x:,.0f}}<extra></extra>"
                )
            )
        )

    # 6) tidy up layout
    fig.update_layout(
        barmode="stack",
        hovermode="y unified",
        title=f"Cost Breakdown per Scenario ({start}–{end})",
        xaxis=dict(
            title="Cost",
            tickprefix=currency_symbol,
            hoverformat=", .0f"
        ),
        yaxis=dict(title="Scenario"),
        margin=dict(l=140, r=40, t=60, b=50),
        legend=dict(title="Component")
    )

    return fig


def generate_metric_figure(metric, year_range, selected_scenarios, dashboard_data=None):
    """
    Line chart of `metric` (flat key) over year_range for each selected scenario.
    """
    fig = go.Figure()
    if not dashboard_data:
        return fig

    start, end = year_range
    for scenario in selected_scenarios:
        records = dashboard_data.get(scenario, [])
        x_vals, y_vals = [], []
        for rec in records:
            yr = rec.get("year")
            if yr is None or yr < start or yr > end:
                continue
            if metric in rec:
                x_vals.append(yr)
                y_vals.append(rec.get(metric, 0))
        if x_vals:
            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="lines+markers",
                name=scenario
            ))

    fig.update_layout(
        title=f"{metric.replace('_',' ').title()} Comparison",
        xaxis_title="Year",
        yaxis_title=metric.replace("_"," ").title(),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(l=40, r=40, t=60, b=40)
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
    Layout for the Financial Metrics tab with dynamic chart selection.
    """
    HEADER_STYLE = {"backgroundColor": "#f8f9fa"}
    HEADER_TEXT_STYLE = {"color": "#343a40"}

    # Year options for the single-year dropdown
    year_options = [{"label": str(y), "value": str(y)} for y in range(2025, 2051)]

    # Options for selecting which charts to display
    chart_options = [
        {"label": "Metric Comparison", "value": "metric"},
        {"label": "Future Opex",         "value": "min_future_opex"},
        {"label": "Dwelling at Berth",   "value": "dwelling"},
        {"label": "Single or Multiple Year Breakdown", "value": "single_year"},
    ]

    return dbc.Card(
        [
            dbc.CardHeader(
                html.H4("Economic Metrics (2025–2050)",
                        className="card-title",
                        style=HEADER_TEXT_STYLE),
                style=HEADER_STYLE
            ),
            dbc.CardBody(
                [
                    # ─── Filters Row ────────────────────────────────────────
                    dbc.Row(
                        [
                            # Metric dropdown
                            dbc.Col(
                                [
                                    dbc.Label("Metric"),
                                    dcc.Dropdown(
                                        id="dashboard-metric-dropdown",
                                        options=[
                                            {"label": "Opex",                "value": "opex"},
                                            {"label": "EU ETS",              "value": "eu_ets"},
                                            {"label": "Fuel Price",          "value": "fuel_price"},
                                            {"label": "Maintenance",         "value": "maintenance"},
                                            {"label": "Penalty",             "value": "penalty"},
                                            {"label": "Spare",               "value": "spare"}
                                            
                                        ],
                                        value="opex",
                                        clearable=False,
                                        className="custom-dropdown",
                                    )
                                ],
                                md=3, xs=12
                            ),

                            # Year range slider
                            dbc.Col(
                                [
                                    dbc.Label("Year Range"),
                                    dcc.RangeSlider(
                                        id="dashboard-year-range-slider",
                                        min=2025,
                                        max=2050,
                                        value=[2025, 2050],
                                        marks={
                                            yr: {"label": str(yr),
                                                 "style": {"transform": "rotate(45deg)",
                                                           "whiteSpace": "nowrap"}}
                                            for yr in range(2025, 2051, 5)
                                        },
                                        tooltip={"placement": "bottom", "always_visible": True},
                                    )
                                ],
                                md=5, xs=12
                            ),

                            # Scenario filter
                            dbc.Col(
                                [
                                    dbc.Label("Scenario Filter"),
                                    dcc.Dropdown(
                                        id="scenario-filter",
                                        multi=True,
                                        className="custom-dropdown",
                                        placeholder="Select scenarios…",
                                    )
                                ],
                                md=4, xs=12
                            ),
                        ]
                    ),

                    html.Hr(),

                    # ─── Chart Selector Row ──────────────────────────────────
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label("Which charts to show?"),
                                    dcc.Checklist(
                                        id="dashboard-chart-selector",
                                        options=chart_options,
                                        value=["metric", "min_future_opex","dwelling", "single_year"],  # default to metric comparison
                                        inline=True,
                                        inputStyle={"margin-right": "5px", "margin-left": "10px"},
                                    ),
                                ],
                                width=12
                            )
                        ],
                        className="mb-3"
                    ),

                    # ─── Single-Year Dropdown ───────────────────────────────
                    dbc.Row(
                        dbc.Col(
                            [
                                dbc.Label("Select Single Year for Breakdown"),
                                dcc.Dropdown(
                                    id="single-year-dropdown",
                                    options=[{"label": "All Years", "value": "all"}] + year_options,
                                    value="all",
                                    clearable=False,
                                    className="custom-dropdown"
                                )
                            ],
                            md=4, xs=12
                        ),
                        className="mb-4"
                    ),

                    # ─── Dynamic Chart Container ─────────────────────────────
                    html.Div(id="dashboard-charts-container")
                ]
            )
        ],
        className="mb-4"
    )


# ----------------------------
# Executive Dashboard Layout (Tab 2)
# ----------------------------
def multi_chart_dashboard_layout():
    return dbc.Card([
        dbc.CardHeader(
            html.Div([
                html.H4("Executive Dashboard",
                        className="card-title",
                        style=HEADER_TEXT_STYLE),
                html.P(
                    "Explore the trends and key financial metrics across years for various scenarios.",
                    className="text-muted",
                    style={"fontSize": "0.9rem"}
                )
            ]),
            style=HEADER_STYLE
        ),
        dbc.CardBody([
            # Controls: Year Range & Scenario
            dbc.Row([
                dbc.Col([
                    dbc.Label("Year Range (Time Series)"),
                    dcc.RangeSlider(
                        id="dashboard-year-range",
                        min=2025, max=2050,
                        value=[2025, 2035],
                        marks={yr: {"label": str(yr), "style": {"transform": "rotate(45deg)"}} for yr in range(2025, 2051)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    dbc.Tooltip(
                        "Select the range of years to display for time series charts.",
                        target="dashboard-year-range"
                    )
                ], md=6, xs=12),
                dbc.Col([
                    dbc.Label("Scenario"),
                    dcc.Dropdown(
                        id="dashboard-scenario-dropdown",
                        options=[],  # Populated by callback
                        clearable=False,
                        placeholder="Select scenario"
                    )
                ], md=6, xs=12),
            ], className="mb-4"),

            # Cost Breakdown Year
            dbc.Row([
                dbc.Col([
                    dbc.Label("Cost Breakdown Year"),
                    dcc.Dropdown(
                        id="dashboard-cost-breakdown-year",
                        options=[],  # Populated by callback
                        clearable=False,
                        placeholder="Select cost breakdown year"
                    ),
                    dbc.Tooltip(
                        "Select a specific year to display its cost breakdown.",
                        target="dashboard-cost-breakdown-year"
                    )
                ], md=4, xs=12),
            ], className="mb-4"),

            html.Hr(),

            # KPI Cards Row
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody(html.Div([
                    html.H5("Fuel Price", className="card-title text-center"),
                    html.I(className="bi bi-bar-chart-line",
                           style={"fontSize": "1.5rem","color": "#2CA02C"}),
                    html.H3(id="kpi-fuel-price",
                            className="text-center text-success"),
                    html.P(id="kpi-fuel-price-status",
                           className="text-center", style={"fontSize": "0.8rem"})
                ]))), md=3, xs=6),

                dbc.Col(dbc.Card(dbc.CardBody(html.Div([
                    html.H5("Fuel-EU Penalty", className="card-title text-center"),
                    html.I(className="bi bi-graph-up",
                           style={"fontSize": "1.5rem","color": "#D62728"}),
                    html.H3(id="kpi-penalty",
                            className="text-center text-danger"),
                    html.P(id="kpi-penalty-savings",
                           className="text-center", style={"fontSize": "0.8rem"})
                ]))), md=3, xs=6),

                dbc.Col(dbc.Card(dbc.CardBody(html.Div([
                    html.H5("EU ETS Penalty", className="card-title text-center"),
                    html.I(className="bi bi-pie-chart",
                           style={"fontSize": "1.5rem","color": "#17A2B8"}),
                    html.H3(id="kpi-euets",
                            className="text-center text-info"),
                    html.P(id="kpi-euets-trend",
                           className="text-center", style={"fontSize": "0.8rem"})
                ]))), md=3, xs=6),
                                dbc.Col(dbc.Card(dbc.CardBody(html.Div([
                    html.H5("Avg. OPEX", className="card-title text-center"),
                    html.I(className="bi bi-currency-euro",
                           style={"fontSize": "1.5rem","color": "#1F77B4"}),
                    html.H3(id="kpi-avg-opex",
                            className="text-center text-primary"),
                    html.P(id="kpi-opex-trend",
                           className="text-center", style={"fontSize": "0.8rem"})
                ]))), md=3, xs=6),
            ], className="mb-4"),
            

            # Charts
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("OPEX Trend"),
                    dbc.CardBody(dcc.Graph(
                        id="dashboard-opex-trend",
                        config={'displayModeBar': False},
                        className="dashboard-chart"
                    ))
                ]), md=6, xs=12, className="mb-3"),

                dbc.Col(dbc.Card([
                    dbc.CardHeader("Cost Breakdown"),
                    dbc.CardBody(dcc.Graph(
                        id="dashboard-cost-breakdown",
                        config={'displayModeBar': False},
                        className="dashboard-chart"
                    ))
                ]), md=6, xs=12, className="mb-3"),
            ]),

            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("EU ETS Impact"),
                    dbc.CardBody(dcc.Graph(
                        id="dashboard-eu-ets-chart",
                        config={'displayModeBar': False},
                        className="dashboard-chart"
                    ))
                ]), md=6, xs=12, className="mb-3"),
                
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Penalty Trend"),
                    dbc.CardBody(dcc.Graph(
                        id="dashboard-penalty-trend",
                        config={'displayModeBar': False},
                        className="dashboard-chart"
                    ))
                ]), md=6, xs=12, className="mb-3"),    
            ]),

            # Metrics Table
            dbc.Row(dbc.Col(dbc.Card([
                dbc.CardHeader("Annual Financial Metrics"),
                dbc.CardBody(html.Div(id="dashboard-metrics-table"))
            ]), className="mb-3"))
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





