import dash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import requests
from urllib.parse import urlencode
import config

# =============================================================================
# GLOBAL STYLES & CONSTANTS
# =============================================================================
HEADER_STYLE = {"backgroundColor": "#0A4B8C", "padding": "10px"}
HEADER_TEXT_STYLE = {"color": "white", "margin": "0"}
MARGIN_STYLE = dict(l=60, r=30, t=60, b=50)
TEMPLATE_STYLE = "plotly_white"

# =============================================================================
# 1) API HELPERS
# =============================================================================
def get_vessel_data(imo=9419163, mmsi=9419163):
    """
    Fetch vessel details from the first API endpoint.
    Returns the JSON response as a dictionary.
    Correct API request:
    https://natpower-marine-api-dev.azurewebsites.net/marinedata/getvesseldetails_engine?imo=9419163&mmsi=9419163
    """
    url = f"{config.VESSEL_ENDPOINT}?imo={imo}&mmsi={mmsi}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        # Return the first item in the list
        return response.json()[0]
    except requests.RequestException as e:
        print("Error fetching vessel data:", e)
        return {}

def get_default_financial_data():
    """
    Fetch financial data from the second API using parameters from vessel data where possible.
    Returns the complete JSON response as a dictionary.
    Correct API request:
    https://natpower-marine-api-dev.azurewebsites.net/marinedata/financialmodelling?main_engine_power_kw=38400&aux_engine_power_kw=2020&...
    """
    vessel_data = get_vessel_data()
    # Use vessel values if available; otherwise fall back to defaults.
    default_params = {
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
    qs = urlencode(default_params)
    url = f"{config.FINANCIAL_ENDPOINT}?{qs}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print("Error fetching financial data:", e)
        return {}

# =============================================================================
# 2) LOAD TIMESERIES DATA (TOTEX, NPV, SPARES)
# =============================================================================
def load_totex_scenarios():
    """
    Extract timeseries data from the API response for TOTEX, NPV, and SPARES.
    Returns (years, scenarios) where scenarios includes 'Current', 'Future', and 'Project'.
    """
    data = get_default_financial_data()
    current_ts = data.get("current_timeseries", [])
    future_ts = data.get("future_timeseries", [])
    result = data.get("result", [])
    
    if not current_ts or not future_ts or not result:
        years = list(range(2025, 2051))
        current_totex = [0] * len(years)
        future_totex = [0] * len(years)
        project_npv = [0] * len(years)
        current_spares = [0] * len(years)
        future_spares = [0] * len(years)
    else:
        years = [entry.get("year") for entry in current_ts]
        current_opex = [entry.get("current_opex", 0) for entry in current_ts]
        future_opex = [entry.get("future_opex", 0) for entry in future_ts]
        project_npv = [entry.get("npv", 0) for entry in result]
        current_spares = [entry.get("total_spare_current_inflated", 0) for entry in current_ts]
        future_spares = [entry.get("total_spare_future_inflated", 0) for entry in future_ts]
        
        # Calculate cumulative TOTEX (cumulative OPEX)
        current_totex = np.cumsum(current_opex).tolist()
        future_totex = np.cumsum(future_opex).tolist()
    
    scenarios = {
        "Current": {"TOTEX": current_totex, "SPARES": current_spares},
        "Future": {"TOTEX": future_totex, "SPARES": future_spares},
        "Project": {"NPV": project_npv}
    }
    return years, scenarios

# =============================================================================
# 3) FIGURE HELPER
# =============================================================================
def set_figure_layout(fig, title, xaxis_title=None, yaxis_title=None):
    """
    Apply a consistent layout to Plotly figures.
    """
    fig.update_layout(
        title=title,
        title_font_color="#0A4B8C",
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        template=TEMPLATE_STYLE,
        margin=MARGIN_STYLE
    )
    return fig

# =============================================================================
# 4) FIGURE FUNCTIONS
# =============================================================================
def dwelling_at_berth_pie_figure():
    """
    Build a pie chart for cost breakdown using yearly API data for the reporting year.
    """
    data = get_default_financial_data()
    reporting_year = 2030  # From default parameters
    current_ts = data.get("current_timeseries", [])
    yearly_data = next((entry for entry in current_ts if entry.get("year") == reporting_year), {})
    
    labels = ["Fuel", "Maintenance", "Spares", "FuelEU Penalty"]
    values = [
        yearly_data.get("total_fuel_current_inflated", 0),
        yearly_data.get("total_maintenance_current_inflated", 0),
        yearly_data.get("total_spare_current_inflated", 0),
        yearly_data.get("current_penalty", 0)
    ]
    
    fig = go.Figure([go.Pie(labels=labels, values=values, hoverinfo="label+percent", textinfo="label+percent")])
    return set_figure_layout(fig, f"Cost Breakdown for Current Scenario ({reporting_year})")

def cashflow_figure():
    """
    Build a bar and line chart for cumulative savings vs. NPV using API data.
    """
    years, scenarios = load_totex_scenarios()
    project_npv = scenarios["Project"]["NPV"]
    result = get_default_financial_data().get("result", [])
    cumulative_savings = [entry.get("cumulative", 0) for entry in result]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=years, y=cumulative_savings, name="Cumulative Savings", marker_color="blue"))
    fig.add_trace(go.Scatter(
        x=years, y=project_npv, mode="lines+markers", name="NPV",
        line=dict(color="black", width=2), marker=dict(size=6)
    ))
    return set_figure_layout(fig, "Cumulative Savings vs. NPV", "Year", "Amount (£)")

def totex_figure():
    """
    Build a grouped bar chart comparing TOTEX (cumulative OPEX) between Current and Future scenarios.
    """
    years, scenarios = load_totex_scenarios()
    
    fig = go.Figure()
    for label in ["Current", "Future"]:
        fig.add_trace(go.Bar(x=years, y=scenarios[label]["TOTEX"], name=label))
    return set_figure_layout(fig, "TOTEX Comparison (Cumulative OPEX)", "Year", "TOTEX (£)")

def engine_power_profile_figure():
    """
    Build a grouped bar chart comparing engine power profiles using correct API keys.
    """
    data = get_default_financial_data()
    current_table = data.get("current_table", {})
    future_table = data.get("future_output_table", {})
    
    # Using the key "enginge_power" (as per API typo)
    current_eng = current_table.get("enginge_power", [{}])[0]
    future_eng = future_table.get("enginge_power", [{}])[0]
    
    categories = ["Idle", "Sailing", "Working"]
    current_values = [
        current_eng.get("idle_power", 0),
        current_eng.get("sailing_power", 0),
        current_eng.get("working_power", 0)
    ]
    future_values = [
        future_eng.get("idle_power", 0),
        future_eng.get("sailing_power", 0),
        future_eng.get("working_power", 0)
    ]
    
    fig = go.Figure(data=[
        go.Bar(name="Current", x=categories, y=current_values, marker_color="blue"),
        go.Bar(name="Future", x=categories, y=future_values, marker_color="orange")
    ])
    fig.update_layout(
        barmode="group",
        title="Engine Power Profile (kW)",
        xaxis_title="Operating Mode",
        yaxis_title="Power (kW)",
        template=TEMPLATE_STYLE
    )
    return fig

def energy_demand_figure():
    """
    Build a bar chart comparing total daily energy demand (kWh) using correct API keys.
    """
    data = get_default_financial_data()
    current_table = data.get("current_table", {})
    future_table = data.get("future_output_table", {})
    
    # Using "power_calc_day" with the known typo "eneregy"
    cur_pcd = current_table.get("power_calc_day", [{}])[0]
    fut_pcd = future_table.get("power_calc_day", [{}])[0]
    
    cur_total = sum([
        cur_pcd.get("idle_eneregy_req_kwh_day", 0),
        cur_pcd.get("sailing_eneregy_req_kwh_day", 0),
        cur_pcd.get("working_eneregy_req_kwh_day", 0)
    ])
    fut_total = sum([
        fut_pcd.get("idle_eneregy_req_kwh_day", 0),
        fut_pcd.get("sailing_eneregy_req_kwh_day", 0),
        fut_pcd.get("working_eneregy_req_kwh_day", 0)
    ])
    
    fig = go.Figure(data=[
        go.Bar(name="Current", x=["Total Daily Energy (kWh)"], y=[cur_total], marker_color="blue"),
        go.Bar(name="Future", x=["Total Daily Energy (kWh)"], y=[fut_total], marker_color="orange")
    ])
    fig.update_layout(
        barmode="group",
        title="Daily Energy Demand - Current vs. Future",
        template=TEMPLATE_STYLE
    )
    return fig

def spares_figure():
    """
    Build a line chart comparing spares cost over time.
    """
    years, scenarios = load_totex_scenarios()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years,
        y=scenarios["Current"]["SPARES"],
        mode="lines+markers",
        name="Current Spares",
        line=dict(color="blue", width=2),
        marker=dict(size=6)
    ))
    fig.add_trace(go.Scatter(
        x=years,
        y=scenarios["Future"]["SPARES"],
        mode="lines+markers",
        name="Future Spares",
        line=dict(color="orange", width=2),
        marker=dict(size=6)
    ))
    fig.update_layout(
        title="Spares Over Time",
        xaxis_title="Year",
        yaxis_title="Spares (inflated cost)",
        template=TEMPLATE_STYLE
    )
    return fig

# =============================================================================
# 5) LAYOUT HELPERS & FUNCTIONS
# =============================================================================
def card_component(title, children):
    return dbc.Card([
        dbc.CardHeader(
            html.H4(title, className="card-title mb-0", style=HEADER_TEXT_STYLE),
            style=HEADER_STYLE
        ),
        dbc.CardBody(children)
    ], className="mb-4 shadow-sm rounded")

def financial_metrics_layout():
    years_data, scenarios = load_totex_scenarios()
    scenario_options = [
        {"label": "Current Scenario", "value": "Current"},
        {"label": "Future Scenario", "value": "Future"},
        {"label": "Project Savings", "value": "Project"}
    ]
    default_scenarios = ["Current", "Future"]
    return dbc.Card([
        dbc.CardHeader(
            html.H4("TOTEX & Financial Metrics Comparison (2025–2050)",
                    className="card-title", style=HEADER_TEXT_STYLE),
            style=HEADER_STYLE
        ),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Metric"),
                    dcc.Dropdown(
                        id="metric-dropdown",
                        options=[
                            {"label": "TOTEX (Cumulative OPEX)", "value": "TOTEX"},
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
                "Spares Over Time (API-based)",
                dcc.Graph(figure=spares_figure(), className="chart-container")
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
                        options=[
                            {"label": "NPV Comparison", "value": "npv"},
                            {"label": "Cashflow Analysis", "value": "cashflow"},
                            {"label": "TOTEX Comparison", "value": "totex"},
                            {"label": "Engine Power Profile", "value": "engine"}
                        ],
                        value=["npv", "cashflow", "totex", "engine"],
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

# =============================================================================
# 6) DASH APP & CALLBACKS
# =============================================================================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = layout()

# --- Financial Metrics Tab Callback ---
@app.callback(
    Output("metric-comparison-chart", "figure"),
    [Input("metric-dropdown", "value"),
     Input("year-range-slider", "value"),
     Input("scenario-filter", "value")]
)
def update_metric_comparison_chart(selected_metric, year_range, selected_scenarios):
    """
    Update metric comparison chart based on user selection.
    """
    years_data, scenarios = load_totex_scenarios()
    start_year, end_year = year_range
    indices = [i for i, yr in enumerate(years_data) if start_year <= yr <= end_year]
    filtered_years = [years_data[i] for i in indices]
    
    fig = go.Figure()
    for label in selected_scenarios:
        metric_values = scenarios.get(label, {}).get(selected_metric, [])
        if metric_values:
            filtered_values = [metric_values[i] for i in indices]
            fig.add_trace(go.Scatter(
                x=filtered_years,
                y=filtered_values,
                mode="lines+markers",
                name=f"{label} {selected_metric}"
            ))
    fig.update_layout(
        title=f"{selected_metric} Comparison",
        xaxis_title="Year",
        yaxis_title=f"{selected_metric} (£)",
        template=TEMPLATE_STYLE,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
    )
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
        template="plotly_white"
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
        template="plotly_white"
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
    if not selected_charts:
        return html.Div("No charts selected.", style={"text-align": "center", "padding": "20px"})
    years, scenarios = load_totex_scenarios()
    charts = []
    if "npv" in selected_charts:
        fig = go.Figure()
        npv_data = scenarios["Project"]["NPV"]
        fig.add_trace(go.Scatter(x=years, y=npv_data, mode="lines", name="Project NPV"))
        fig.update_layout(
            title="NPV Comparison",
            xaxis_title="Year",
            yaxis_title="NPV (£)",
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )
        charts.append(card_component("NPV Comparison", dcc.Graph(figure=fig, className="chart-container")))
    if "cashflow" in selected_charts:
        charts.append(card_component("Cashflow Analysis", dcc.Graph(figure=cashflow_figure(), className="chart-container")))
    if "totex" in selected_charts:
        charts.append(card_component("TOTEX Comparison", dcc.Graph(figure=totex_figure(), className="chart-container")))
    if "engine" in selected_charts:
        charts.append(card_component("Engine Power Profile", dcc.Graph(figure=engine_power_profile_figure(), className="chart-container")))
    return charts

if __name__ == "__main__":
    app.run_server(debug=True)
