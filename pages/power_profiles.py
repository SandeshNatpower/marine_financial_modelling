# pages/power_profiles.py

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import config

# =============================================================================
# GLOBAL STYLES & CONSTANTS
# =============================================================================
HEADER_STYLE = {"backgroundColor": "#0A4B8C", "padding": "10px"}
HEADER_TEXT_STYLE = {"color": "white", "margin": "0"}
MARGIN_STYLE = dict(l=60, r=30, t=60, b=50)
TEMPLATE_STYLE = "plotly_white"

# =============================================================================
# UI COMPONENT
# =============================================================================
def card_component(title, children):
    return dbc.Card([
        dbc.CardHeader(
            html.H4(title, className="card-title mb-0", style=HEADER_TEXT_STYLE),
            style=HEADER_STYLE
        ),
        dbc.CardBody(children)
    ], className="mb-4 shadow-sm rounded")

# =============================================================================
# HELPER FUNCTIONS TO PROCESS DATA & CREATE FIGURES
# =============================================================================
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

def load_totex_scenarios():
    # Normally this would fetch API data.
    # For demonstration, we use dummy data.
    data = {}  # Replace with actual API call
    current_ts = data.get("current_timeseries", [])
    future_ts = data.get("future_timeseries", [])
    if not current_ts or not future_ts:
        years = list(range(2025, 2051))
        scenarios = {
            "Current": {"OPEX": [0]*len(years), "Penalty": [0]*len(years), "Fuel": [0]*len(years),
                        "Maintenance": [0]*len(years), "SPARES": [0]*len(years)},
            "Future": {"OPEX": [0]*len(years), "Penalty": [0]*len(years), "Fuel": [0]*len(years),
                       "Maintenance": [0]*len(years), "SPARES": [0]*len(years)}
        }
        return years, scenarios

    years = [entry.get("year") for entry in current_ts]
    scenarios = {
        "Current": {
            "OPEX": [entry.get("current_opex", 0) for entry in current_ts],
            "Penalty": [entry.get("current_penalty", 0) for entry in current_ts],
            "Fuel": [abs(entry.get("total_fuel_current_inflated", 0)) for entry in current_ts],
            "Maintenance": [entry.get("total_maintenance_current_inflated", 0) for entry in current_ts],
            "SPARES": [entry.get("total_spare_current_inflated", 0) for entry in current_ts]
        },
        "Future": {
            "OPEX": [entry.get("future_opex", 0) for entry in future_ts],
            "Penalty": [entry.get("future_penalty", 0) for entry in future_ts],
            "Fuel": [abs(entry.get("total_fuel_future_inflated", 0)) for entry in future_ts],
            "Maintenance": [entry.get("total_maintenance_future_inflated", 0) for entry in future_ts],
            "SPARES": [entry.get("total_spare_current_inflated", 0) for entry in current_ts]
        }
    }
    return years, scenarios

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

def cashflow_figure():
    # Dummy implementation for a combined bar and line chart.
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[2025, 2026, 2027], y=[1000, 2000, 3000], name="Cumulative Savings", marker_color="blue"))
    fig.add_trace(go.Scatter(x=[2025, 2026, 2027], y=[1500, 2500, 3500], mode="lines+markers", name="NPV",
                             line=dict(color="black", width=2), marker=dict(size=6)))
    return set_figure_layout(fig, "Cumulative Savings vs. NPV", "Year", "Amount (£)")

def totex_figure():
    years, scenarios = load_totex_scenarios()
    current_cum = np.cumsum(scenarios["Current"]["OPEX"]).tolist()
    future_cum = np.cumsum(scenarios["Future"]["OPEX"]).tolist()
    fig = go.Figure(data=[
        go.Bar(name="Current", x=years, y=current_cum, marker_color="blue"),
        go.Bar(name="Future", x=years, y=future_cum, marker_color="orange")
    ])
    return set_figure_layout(fig, "Cumulative OPEX Comparison", "Year", "Cumulative OPEX (£)")

def engine_power_profile_figure():
    fig = go.Figure(data=[
        go.Bar(name="Current", x=["Idle", "Sailing", "Working"], y=[0, 0, 0], marker_color="blue"),
        go.Bar(name="Future", x=["Idle", "Sailing", "Working"], y=[0, 0, 0], marker_color="orange")
    ])
    return set_figure_layout(fig, "Engine Power Profile (kW)", "Operating Mode", "Power (kW)")

def energy_demand_figure():
    fig = go.Figure(data=[
        go.Bar(name="Current", x=["Total Daily Energy (kWh)"], y=[0], marker_color="blue"),
        go.Bar(name="Future", x=["Total Daily Energy (kWh)"], y=[0], marker_color="orange")
    ])
    return set_figure_layout(fig, "Daily Energy Demand Comparison", "", "Energy (kWh)")

def spares_figure():
    years, scenarios = load_totex_scenarios()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years,
        y=scenarios["Current"].get("SPARES", [0]*len(years)),
        mode="lines+markers",
        name="Current Spares",
        line=dict(color="blue", width=2),
        marker=dict(size=6)
    ))
    fig.add_trace(go.Scatter(
        x=years,
        y=scenarios["Future"].get("SPARES", [0]*len(years)),
        mode="lines+markers",
        name="Future Spares",
        line=dict(color="orange", width=2),
        marker=dict(size=6)
    ))
    return set_figure_layout(fig, "Spares Cost Comparison", "Year", "Spares Cost (£)")

def timeseries_field_comparison(processed_data, field_current, field_future, title, yaxis_title):
    years = [item["year"] for item in processed_data]
    current_values = [item.get(field_current, 0) for item in processed_data]
    future_values = [item.get(field_future, 0) for item in processed_data]
    fig = go.Figure(data=[
        go.Bar(name="Current", x=years, y=current_values, marker_color="blue"),
        go.Bar(name="Future", x=years, y=future_values, marker_color="orange")
    ])
    return set_figure_layout(fig, title, "Year", yaxis_title)

def opex_comparison_figure():
    data = {}  # Replace with actual API data
    processed = process_financial_results(data)
    return timeseries_field_comparison(processed, "current_opex", "future_opex", "OPEX Comparison", "OPEX (£)")

def penalty_comparison_figure():
    data = {}
    processed = process_financial_results(data)
    return timeseries_field_comparison(processed, "current_penalty", "future_penalty", "Penalty Comparison", "Penalty (£)")

def fuel_comparison_figure():
    data = {}
    processed = process_financial_results(data)
    return timeseries_field_comparison(processed, "fuel_current", "fuel_future", "Fuel Cost Comparison", "Fuel Cost (£)")

def maintenance_comparison_figure():
    data = {}
    processed = process_financial_results(data)
    return timeseries_field_comparison(processed, "maintenance_current", "maintenance_future", "Maintenance Cost Comparison", "Maintenance (£)")

def dwelling_at_berth_pie_figure():
    # Dummy pie chart for cost breakdown.
    labels = ["Fuel", "Maintenance", "Spares", "Penalty"]
    values = [100, 200, 50, 75]
    fig = go.Figure([go.Pie(labels=labels, values=values, hoverinfo="label+percent", textinfo="label+percent")])
    return set_figure_layout(fig, "Cost Breakdown for Current Scenario (2030)")

# =============================================================================
# LAYOUT HELPERS & APP LAYOUT
# =============================================================================
def financial_metrics_layout():
    scenario_options = [
        {"label": "Current Scenario", "value": "Current"},
        {"label": "Future Scenario", "value": "Future"}
    ]
    default_scenarios = ["Current", "Future"]
    years_data, _ = load_totex_scenarios()
    return dbc.Card([
        dbc.CardHeader(
            html.H4("TOTEX & Financial Metrics Comparison (2025–2050)", className="card-title", style=HEADER_TEXT_STYLE),
            style=HEADER_STYLE
        ),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Metric"),
                    dcc.Dropdown(
                        id="metric-dropdown",
                        options=[{"label": "TOTEX (Cumulative OPEX)", "value": "TOTEX"},
                                 {"label": "NPV", "value": "NPV"}],
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
                        options=scenario_options,
                        value=default_scenarios,
                        multi=True,
                        placeholder="Select scenarios",
                        className="custom-dropdown"
                    )
                ], md=4, xs=12)
            ]),
            html.Br(),
            dcc.Graph(id="metric-comparison-chart", className="chart-container"),
            html.Hr(),
            dbc.Row([
                dbc.Col(card_component(
                    "Cost Breakdown for Current Scenario (2030)",
                    dcc.Graph(figure=dwelling_at_berth_pie_figure(), className="chart-container")
                ), md=12, xs=12)
            ]),
        ])
    ], className="mb-4")

def power_demand_layout():
    return html.Div([
        html.H2("Power Demand Analysis", className="page-title"),
        dbc.Row([
            dbc.Col(
                card_component("Load Profile Configuration (Synthetic)", [
                    dcc.Graph(id="detail-power-profile-chart", className="chart-container"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Peak Power Demand (kW)"),
                            dbc.Input(id="detail-peak-power", type="number", value=25000, className="custom-input")
                        ], md=4, xs=12),
                        dbc.Col([
                            dbc.Label("Base Load (%)"),
                            dcc.Slider(
                                id="detail-base-load",
                                min=20,
                                max=80,
                                value=40,
                                marks={i: f"{i}%" for i in range(20, 81, 10)}
                            )
                        ], md=8, xs=12)
                    ])
                ]),
                md=8, xs=12
            ),
            dbc.Col(
                card_component("Energy Storage Options", [
                    dcc.Dropdown(
                        id="detail-storage-type",
                        options=[
                            {"label": "Lithium-Ion Battery", "value": "li-ion"},
                            {"label": "Fuel Cells", "value": "fuel-cell"},
                            {"label": "Supercapacitors", "value": "capacitor"}
                        ],
                        multi=True,
                        placeholder="Select storage options",
                        className="custom-dropdown"
                    ),
                    html.Div(id="detail-storage-results", className="mt-3")
                ]),
                md=4, xs=12
            )
        ]),
        html.Br(),
        dbc.Row([
            dbc.Col(card_component(
                "Projected Energy Demand Over Time (Synthetic Example)",
                dcc.Graph(id="energy-demand-chart", className="chart-container")
            ), xs=12)
        ]),
        html.Br(),
        dbc.Row([
            dbc.Col(card_component(
                "Cashflow Analysis (API-based)",
                dcc.Graph(id="cashflow-chart", figure=cashflow_figure(), className="chart-container")
            ), xs=12)
        ]),
        html.Br(),
        dbc.Row([
            dbc.Col(card_component(
                "TOTEX Comparison (API-based)",
                dcc.Graph(id="totex-chart", figure=totex_figure(), className="chart-container")
            ), xs=12)
        ]),
        html.Br(),
        dbc.Row([
            dbc.Col(card_component(
                "Daily Energy Demand (API-based)",
                dcc.Graph(figure=energy_demand_figure(), className="chart-container")
            ), xs=12)
        ]),
        html.Br(),
        dbc.Row([
            dbc.Col(card_component(
                "Spares Cost Comparison (API-based)",
                dcc.Graph(figure=spares_figure(), className="chart-container")
            ), xs=12)
        ]),
        html.Br(),
        dbc.Row([
            dbc.Col(card_component(
                "Timeseries Comparisons",
                html.Div([
                    dcc.Graph(figure=opex_comparison_figure(), className="chart-container"),
                    dcc.Graph(figure=penalty_comparison_figure(), className="chart-container"),
                    dcc.Graph(figure=fuel_comparison_figure(), className="chart-container"),
                    dcc.Graph(figure=maintenance_comparison_figure(), className="chart-container")
                ])
            ), xs=12)
        ])
    ])

def multi_chart_dashboard_layout():
    return dbc.Card([
        dbc.CardHeader(
            html.H4("Multi-Chart Dashboard", className="card-title", style=HEADER_TEXT_STYLE),
            style=HEADER_STYLE
        ),
        dbc.CardBody([
            dbc.Row([
                dbc.Col(
                    dcc.Checklist(
                        id="dashboard-chart-selector",
                        options=[{"label": "NPV Comparison", "value": "npv"},
                                 {"label": "Cashflow Analysis", "value": "cashflow"},
                                 {"label": "TOTEX Comparison", "value": "totex"},
                                 {"label": "Engine Power Profile", "value": "engine"},
                                 {"label": "Timeseries Comparisons", "value": "timeseries"}],
                        value=["npv", "cashflow", "totex", "engine", "timeseries"],
                        labelStyle={"display": "inline-block", "margin-right": "15px"}
                    ),
                    width=12
                )
            ]),
            html.Hr(),
            html.Div(id="dashboard-charts-container")
        ])
    ], className="mb-4")

def layout():
    return dbc.Container([
        dbc.Tabs([
            dbc.Tab(financial_metrics_layout(), label="Financial Metrics"),
            dbc.Tab(power_demand_layout(), label="Power Demand Analysis"),
            dbc.Tab(multi_chart_dashboard_layout(), label="Dashboard")
        ])
    ], fluid=True)
