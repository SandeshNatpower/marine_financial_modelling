import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import config

# ------------------------------
# GLOBAL STYLES & CONSTANTS
# ------------------------------
HEADER_STYLE = {"backgroundColor": "#0A4B8C", "padding": "10px"}
HEADER_TEXT_STYLE = {"color": "white", "margin": "0"}
MARGIN_STYLE = dict(l=60, r=30, t=60, b=50)
TEMPLATE_STYLE = "plotly_white"

# ------------------------------
# HELPER FUNCTIONS
# ------------------------------
def generate_scenario_progression(initial_values, years=26):
    if len(initial_values) < 2:
        initial_values = initial_values + [initial_values[0]] * (2 - len(initial_values))
    result = initial_values[:2]
    for _ in range(2, years):
        last_value = result[-1]
        prev_last_value = result[-2]
        trend = last_value - prev_last_value
        variation = trend * (1 + np.random.uniform(-0.1, 0.1))
        noise = np.random.normal(0, abs(trend) * 0.1)
        next_value = last_value + variation + noise
        result.append(next_value)
    return result

def generate_load_profile(peak_power, base_load_percent, hours=24):
    base_load = peak_power * base_load_percent / 100.0
    amplitude = peak_power - base_load
    x = np.linspace(0, 24, hours)
    y = base_load + amplitude * np.sin((x - 6) / 24 * 2 * np.pi)
    y = np.maximum(y, base_load)
    return x, y

def load_totex_scenarios(api_data=None):
    """
    Construct financial scenarios using pre-fetched API data if provided;
    otherwise, fall back to simulated data.
    
    Parameters:
        api_data (dict): Pre-fetched API data from callbacks (or dcc.Store).
    
    Returns:
        tuple: (years, scenarios) where scenarios is a dict keyed by scenario labels.
    """
    if api_data and "future_timeseries" in api_data:
        future_ts = api_data.get("future_timeseries", [])
        result_ts = api_data.get("result", [])
        current_ts = api_data.get("current_timeseries", [])
        years = [entry["year"] for entry in future_ts]
        scenarios = {}

        # Future TOTEX scenario
        future_totex = []
        for entry in future_ts:
            total = (
                entry.get("future_opex", 0)
                + entry.get("future_penalty", 0)
                + entry.get("total_fuel_future_inflated", 0)
                + entry.get("total_maintenance_future_inflated", 0)
                + entry.get("total_spare_future_inflated", 0)
            )
            future_totex.append(total)
        scenarios["Future TOTEX"] = {"label": "Future TOTEX", "TOTEX": future_totex}

        # Result Metrics scenario
        if result_ts:
            result_values = [entry.get("result", 0) for entry in result_ts]
            cumulative_values = [entry.get("cumulative", 0) for entry in result_ts]
            npv_values = [entry.get("npv", 0) for entry in result_ts]
            scenarios["Result Metrics"] = {
                "label": "Result Metrics",
                "Result": result_values,
                "Cumulative": cumulative_values,
                "NPV": npv_values
            }

        # Current TOTEX scenario
        current_totex = []
        for entry in current_ts:
            total = (
                entry.get("current_opex", 0)
                + entry.get("current_penalty", 0)
                + entry.get("total_fuel_current_inflated", 0)
                + entry.get("total_maintenance_current_inflated", 0)
                + entry.get("total_spare_current_inflated", 0)
            )
            current_totex.append(total)
        scenarios["Current TOTEX"] = {"label": "Current TOTEX", "TOTEX": current_totex}

        return years, scenarios

    # Fallback: simulated data
    years = list(range(2025, 2051))
    scenario_list = [
        {
            "label": "MDO TOTEX BC",
            "TOTEX": generate_scenario_progression([3877159, 8183338]),
            "Result": generate_scenario_progression([-142168, -124728]),
            "Cumulative": generate_scenario_progression([-142168, -266896]),
            "NPV": generate_scenario_progression([-142168, -266896])
        },
        {
            "label": "Bio Diesel blend Minimum",
            "TOTEX": generate_scenario_progression([4019327, 8450234]),
            "Result": generate_scenario_progression([-3148, 36818]),
            "Cumulative": generate_scenario_progression([-3148, 33670]),
            "NPV": generate_scenario_progression([-3148, 33670])
        },
        {
            "label": "Bio Diesel blend +Shore Power Minimum",
            "TOTEX": generate_scenario_progression([4776659, 9942061]),
            "Result": generate_scenario_progression([-1065102, -1017039]),
            "Cumulative": generate_scenario_progression([-1065102, -2082141]),
            "NPV": generate_scenario_progression([-1065102, -2082141])
        },
        {
            "label": "Methanol power with Bio blend Minimum",
            "TOTEX": generate_scenario_progression([6436373, 13394070]),
            "Result": generate_scenario_progression([-4349, -4523]),
            "Cumulative": generate_scenario_progression([-4349, -8873]),
            "NPV": generate_scenario_progression([-4349, -8873])
        },
        {
            "label": "Methanol power + Shore Power with Bio blend Minimum",
            "TOTEX": generate_scenario_progression([7019286, 14519473]),
            "Result": generate_scenario_progression([-1066423, -1018473]),
            "Cumulative": generate_scenario_progression([-1066423, -2084895]),
            "NPV": generate_scenario_progression([-1066423, -2084895])
        },
        {
            "label": "MDO + Shore Power + Battery (2030)",
            "TOTEX": generate_scenario_progression([4776659, 9942061]),
            "Result": generate_scenario_progression([-1065102, -1017039]),
            "Cumulative": generate_scenario_progression([-1065102, -2082141]),
            "NPV": generate_scenario_progression([-1065102, -2082141])
        }
    ]
    scenarios = {sc["label"]: sc for sc in scenario_list}
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

# ------------------------------
# FIGURE FUNCTIONS
# ------------------------------
def dwelling_at_berth_pie_figure():
    labels = ["Fuel", "Financing", "Maintenance", "Spares/consumables", "EU ETS", "FuelEU"]
    values = [63, 0, 9, 2, 1, 25]
    fig = go.Figure([go.Pie(labels=labels, values=values, hoverinfo="label+percent", textinfo="label+percent")])
    set_figure_layout(fig, "Dwelling at Berth - Biofuel Blend Minimum")
    return fig

def cashflow_figure(api_data=None):
    years, scenarios = load_totex_scenarios(api_data)
    if "Result Metrics" in scenarios and "Cumulative" in scenarios["Result Metrics"]:
        cumulative_values = scenarios["Result Metrics"]["Cumulative"]
    else:
        cumulative_values = [
            -17775770, -15777664, -13778408, -10858568, -7937532, -3757239, 424298,
            4607103, 11223362, 17840941, 25841936, 33844304, 41848073, 51705944,
            61565272, 73135955, 84708154, 96281899, 111453588, 126626886, 143183894,
            159742577, 176302967, 199621906, 222942622, 247328280
        ]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=years, y=cumulative_values, mode='lines', name='Cumulative'))
    npv_values = cumulative_values
    fig.add_trace(go.Scatter(x=years, y=npv_values, mode='lines', name='NPV'))
    set_figure_layout(fig, "Cashflow Analysis", "Year", "Value (£)")
    return fig

import plotly.graph_objects as go

def totex_figure(api_data=None):
    years, scenarios = load_totex_scenarios(api_data)
    totex_labels = []
    totex_values = []
    
    for label, sc in scenarios.items():
        if "TOTEX" in sc:
            totex_labels.append(label)
            totex_values.append(sc["TOTEX"][-1])

    # Sorting in ascending order based on TOTEX values
    sorted_data = sorted(zip(totex_values, totex_labels))
    totex_values, totex_labels = zip(*sorted_data)  # Unzipping sorted data

    fig = go.Figure([go.Bar(x=totex_labels, y=totex_values, text=totex_values, textposition='auto')])
    set_figure_layout(fig, "TOTEX Comparison", "Scenario", "TOTEX (£)")
    
    return fig

def generate_metric_figure(metric, year_range, selected_scenarios, api_data=None):
    years, scenarios = load_totex_scenarios(api_data)
    start_year, end_year = year_range
    indices = [i for i, yr in enumerate(years) if start_year <= yr <= end_year]
    fig = go.Figure()
    for label, sc in scenarios.items():
        if selected_scenarios and label not in selected_scenarios:
            continue
        metric_values = sc.get(metric)
        if metric_values:
            filtered_years = [years[i] for i in indices]
            filtered_values = [metric_values[i] for i in indices]
            fig.add_trace(go.Scatter(x=filtered_years, y=filtered_values, mode='lines', name=label))
    set_figure_layout(fig, f"{metric} Comparison", "Year", f"{metric} (£)")
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
    return fig

def projected_energy_demand_figure():
    x_vals, y_vals = generate_load_profile(peak_power=25000, base_load_percent=40)
    if not x_vals or not y_vals:
        return go.Figure(layout={"title": "No Data Available", "xaxis_title": "Hour", "yaxis_title": "Energy Demand (kW)"})
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode="lines+markers", name="Projected Demand"))
    set_figure_layout(fig, "Projected Energy Demand Over Time", "Hour", "Energy Demand (kW)")
    return fig

# ------------------------------
# CARD COMPONENT (for consistency)
# ------------------------------
def card_component(title, children):
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H4(title, className="card-title mb-0", style=HEADER_TEXT_STYLE),
                style=HEADER_STYLE
            ),
            dbc.CardBody(children)
        ],
        className="mb-4 shadow-sm rounded"
    )

# ------------------------------
# LAYOUT FUNCTIONS
# ------------------------------
def financial_metrics_layout(api_data=None):
    years, scenarios = load_totex_scenarios(api_data)
    scenario_options = [{"label": sc["label"], "value": sc["label"]} for sc in scenarios.values()]
    default_scenarios = [sc["label"] for sc in scenarios.values()]
    return dbc.Card(
        [
            dbc.CardHeader(
                html.H4("TOTEX & Financial Metrics Comparison (2025–2050)", className="card-title", style=HEADER_TEXT_STYLE),
                style=HEADER_STYLE
            ),
            dbc.CardBody(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
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
                                ],
                                md=4, xs=12
                            ),
                            dbc.Col(
                                [
                                    dbc.Label("Year Range"),
                                    dcc.RangeSlider(
                                        id="year-range-slider",
                                        min=2025,
                                        max=2050,
                                        value=[2025, 2050],
                                        marks={yr: str(yr) for yr in range(2025, 2051)}
                                    )
                                ],
                                md=4, xs=12
                            ),
                            dbc.Col(
                                [
                                    dbc.Label("Scenarios"),
                                    dcc.Dropdown(
                                        id="scenario-filter",
                                        options=scenario_options,
                                        value=default_scenarios,
                                        multi=True,
                                        placeholder="Select scenarios",
                                        className="custom-dropdown"
                                    )
                                ],
                                md=4, xs=12
                            )
                        ]
                    ),
                    html.Br(),
                    dcc.Graph(id="metric-comparison-chart", className="chart-container"),
                    html.Hr(),
                    dbc.Row(
                        [
                            dbc.Col(card_component(
                                "Dwelling at Berth - Biofuel Blend Minimum",
                                dcc.Graph(figure=dwelling_at_berth_pie_figure(), className="chart-container")
                            ), md=12, xs=12)
                        ]
                    )
                ]
            )
        ],
        className="mb-4"
    )

def power_demand_layout():
    return html.Div(
        [
            html.H2("Power Demand Analysis", className='page-title'),
            dbc.Row(
                [
                    dbc.Col(
                        card_component(
                            "Load Profile Configuration",
                            [
                                dcc.Graph(id='detail-power-profile-chart', className="chart-container"),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label("Peak Power Demand (kW)"),
                                                dbc.Input(id='detail-peak-power', type='number', value=25000, className="custom-input")
                                            ],
                                            md=4, xs=12
                                        ),
                                        dbc.Col(
                                            [
                                                dbc.Label("Base Load (%)"),
                                                dcc.Slider(
                                                    id='detail-base-load',
                                                    min=20,
                                                    max=80,
                                                    value=40,
                                                    marks={i: f"{i}%" for i in range(20, 81, 10)}
                                                )
                                            ],
                                            md=8, xs=12
                                        )
                                    ]
                                )
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
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(card_component(
                        "Projected Energy Demand Over Time",
                        dcc.Graph(id='energy-demand-chart', className="chart-container")
                    ), xs=12)
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(card_component(
                        "Cashflow Analysis",
                        dcc.Graph(figure=cashflow_figure(), id='cashflow-chart', className="chart-container")
                    ), xs=12)
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(card_component(
                        "TOTEX Comparison",
                        dcc.Graph(figure=totex_figure(), id='totex-chart', className="chart-container")
                    ), xs=12)
                ]
            )
        ]
    )

def multi_chart_dashboard_layout():
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
                                options=[
                                    {"label": "Dwelling at Berth", "value": "dwelling"},
                                    {"label": "NPV Comparison", "value": "npv"},
                                    {"label": "Result Comparison", "value": "result"},
                                    {"label": "Cumulative Comparison", "value": "cumulative"},
                                    {"label": "Cashflow Analysis", "value": "cashflow"},
                                    {"label": "TOTEX Comparison", "value": "totex"}
                                ],
                                value=["dwelling", "npv", "result", "cumulative", "cashflow", "totex"],
                                labelStyle={'display': 'inline-block', 'margin-right': '15px'}
                            ),
                            width=12
                        )
                    ),
                    html.Hr(),
                    html.Div(id="dashboard-charts-container")
                ]
            )
        ],
        className="mb-4"
    )

def layout():
    return dbc.Container(
        [
            dbc.Tabs(
                [
                    dbc.Tab(financial_metrics_layout(), label="Financial Metrics"),
                    dbc.Tab(power_demand_layout(), label="Power Demand Analysis"),
                    dbc.Tab(multi_chart_dashboard_layout(), label="Dashboard")
                ]
            )
        ],
        fluid=True
    )
