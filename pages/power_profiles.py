import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
from dash.dependencies import Input, Output

# =============================================================================
# GLOBAL STYLES & CONSTANTS
# =============================================================================
HEADER_STYLE = {"backgroundColor": "#0A4B8C", "padding": "10px"}
HEADER_TEXT_STYLE = {"color": "white", "margin": "0"}  # Forces header text to be white
MARGIN_STYLE = dict(l=60, r=30, t=60, b=50)
TEMPLATE_STYLE = "plotly_white"

# =============================================================================
# HELPER FUNCTIONS & DATA LOADING
# =============================================================================
def parse_currency(value_str):
    try:
        return float(value_str.replace("€", "").replace("£", "").replace(",", "").strip())
    except Exception:
        return None

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

def load_totex_scenarios():
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

# Global Data for Cashflow & TOTEX Charts
years = list(range(2025, 2051))
cumulative_values = [
    -17775770, -15777664, -13778408, -10858568, -7937532, -3757239, 424298,
    4607103, 11223362, 17840941, 25841936, 33844304, 41848073, 51705944,
    61565272, 73135955, 84708154, 96281899, 111453588, 126626886, 143183894,
    159742577, 176302967, 199621906, 222942622, 247328280
]
npv_values = cumulative_values[:]  # Using same data as placeholder

totex_labels = [
    "MDO + Shore Power + Battery (2030)",
    "Methanol power + Shore Power with Bio blend Minimum",
    "Methanol power with Bio blend Minimum",
    "Bio Diesel blend +Shore Power Minimum",
    "Bio Diesel blend Minimum",
    "MDO"
]
totex_values = [
    236766710,
    236409592,
    213738389,
    200172194,
    185217874,
    226268243
]

# =============================================================================
# FIGURE HELPER FUNCTION
# =============================================================================
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

# =============================================================================
# FIGURE FUNCTIONS
# =============================================================================
def dwelling_at_berth_pie_figure():
    labels = ["Fuel", "Financing", "Maintenance", "Spares / consumables", "EU ETS", "FuelEU"]
    values = [63, 0, 9, 2, 1, 25]
    fig = go.Figure([go.Pie(labels=labels, values=values, hoverinfo="label+percent", textinfo="label+percent")])
    set_figure_layout(fig, "Dwelling at Berth - Biofuel Blend Minimum")
    return fig

def cashflow_figure():
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=years,
        y=cumulative_values,
        mode='lines',
        name='Cumulative'
    ))
    fig.add_trace(go.Scatter(
        x=years,
        y=npv_values,
        mode='lines',
        name='NPV'
    ))
    set_figure_layout(fig, "Cashflow Analysis", "Year", "Value (£)")
    return fig

def totex_figure():
    fig = go.Figure([go.Bar(
        x=totex_labels,
        y=totex_values,
        text=totex_values,
        textposition='auto'
    )])
    set_figure_layout(fig, "TOTEX Comparison", "Scenario", "TOTEX (£)")
    return fig

# =============================================================================
# ADDITIONAL HELPER: DAILY LOAD PROFILE GENERATOR
# =============================================================================
def generate_load_profile(peak_power, base_load_percent, hours=24):
    base_load = peak_power * base_load_percent / 100.0
    amplitude = peak_power - base_load
    x = np.linspace(0, 24, hours)
    # Create a sinusoidal load profile with a phase shift for a realistic daily variation
    y = base_load + amplitude * np.sin((x - 6) / 24 * 2 * np.pi)
    # Ensure the load does not drop below the base load
    y = np.maximum(y, base_load)
    return x, y

# =============================================================================
# LAYOUT HELPERS
# =============================================================================
def card_component(title, children):
    """Helper to create a card with a consistent header and styling."""
    return dbc.Card([
        dbc.CardHeader(
            html.H4(title, className="card-title mb-0", style=HEADER_TEXT_STYLE),
            style=HEADER_STYLE
        ),
        dbc.CardBody(children)
    ], className="mb-4 shadow-sm rounded")

# =============================================================================
# LAYOUT FUNCTIONS
# =============================================================================
def financial_metrics_layout():
    years_data, scenarios = load_totex_scenarios()
    scenario_options = [{"label": s["label"], "value": s["label"]} for s in scenarios.values()]
    default_scenarios = [s["label"] for s in scenarios.values()]
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
                    "Dwelling at Berth - Biofuel Blend Minimum",
                    dcc.Graph(figure=dwelling_at_berth_pie_figure(), className="chart-container")
                ), md=12, xs=12)
            ]),
        ])
    ], className="mb-4")

def power_demand_layout():
    return html.Div([
        html.H2("Power Demand Analysis", className='page-title'),
        dbc.Row([
            dbc.Col(
                card_component("Load Profile Configuration", [
                    dcc.Graph(id='detail-power-profile-chart', className="chart-container"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Peak Power Demand (kW)"),
                            dbc.Input(id='detail-peak-power', type='number', value=25000, className="custom-input")
                        ], md=4, xs=12),
                        dbc.Col([
                            dbc.Label("Base Load (%)"),
                            dcc.Slider(
                                id='detail-base-load',
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
                ]),
                md=4, xs=12
            )
        ]),
        dbc.Row([
            dbc.Col(card_component(
                "Projected Energy Demand Over Time",
                dcc.Graph(id='energy-demand-chart', className="chart-container")
            ), xs=12)
        ]),
        dbc.Row([
            dbc.Col(card_component(
                "Cashflow Analysis",
                dcc.Graph(figure=cashflow_figure(), id='cashflow-chart', className="chart-container")
            ), xs=12)
        ]),
        dbc.Row([
            dbc.Col(card_component(
                "TOTEX Comparison",
                dcc.Graph(figure=totex_figure(), id='totex-chart', className="chart-container")
            ), xs=12)
        ])
    ])

def multi_chart_dashboard_layout():
    """Dashboard tab to select and display multiple charts."""
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
                            {"label": "Dwelling at Berth", "value": "dwelling"},
                            {"label": "NPV Comparison", "value": "npv"},
                            {"label": "Cashflow Analysis", "value": "cashflow"},
                            {"label": "TOTEX Comparison", "value": "totex"}
                        ],
                        # Default to all available charts
                        value=["dwelling", "npv", "cashflow", "totex"],
                        labelStyle={'display': 'inline-block', 'margin-right': '15px'}
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
# DASH APP & CALLBACKS
# =============================================================================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = layout()

# Callback to update the dynamic financial metrics chart
@app.callback(
    Output("metric-comparison-chart", "figure"),
    [Input("metric-dropdown", "value"),
     Input("year-range-slider", "value"),
     Input("scenario-filter", "value")]
)
def update_metric_comparison_chart(selected_metric, year_range, selected_scenarios):
    years_data, scenarios = load_totex_scenarios()
    start_year, end_year = year_range
    # Identify indices corresponding to the selected year range
    indices = [i for i, yr in enumerate(years_data) if start_year <= yr <= end_year]
    fig = go.Figure()
    for label, sc in scenarios.items():
        if selected_scenarios and label not in selected_scenarios:
            continue
        metric_values = sc.get(selected_metric)
        if metric_values:
            filtered_years = [years_data[i] for i in indices]
            filtered_values = [metric_values[i] for i in indices]
            fig.add_trace(go.Scatter(
                x=filtered_years,
                y=filtered_values,
                mode="lines",
                name=label
            ))
    fig = set_figure_layout(fig, f"{selected_metric} Comparison", "Year", f"{selected_metric} (£)")
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
    return fig

# Callback to update the daily load profile chart
@app.callback(
    Output("detail-power-profile-chart", "figure"),
    [Input("detail-peak-power", "value"),
     Input("detail-base-load", "value")]
)
def update_power_profile_chart(peak_power, base_load):
    if not peak_power or not base_load:
        peak_power = 25000
        base_load = 40
    x, y = generate_load_profile(peak_power, base_load)
    fig = go.Figure(data=go.Scatter(x=x, y=y, mode='lines', name="Load Profile"))
    fig.update_layout(title="Daily Load Profile", xaxis_title="Hour", yaxis_title="Power (kW)", template=TEMPLATE_STYLE)
    return fig

# Callback to update the projected energy demand chart
@app.callback(
    Output("energy-demand-chart", "figure"),
    [Input("detail-peak-power", "value")]
)
def update_energy_demand_chart(peak_power):
    if not peak_power:
        peak_power = 25000
    # Assume the average power is about half the peak and project annual energy consumption with a 2% growth rate
    base_energy = peak_power * 24 * 0.5
    years_proj = list(range(2025, 2051))
    growth_rate = 0.02
    energy_demand = [base_energy * ((1 + growth_rate) ** (year - 2025)) for year in years_proj]
    fig = go.Figure(data=go.Scatter(x=years_proj, y=energy_demand, mode='lines', name="Energy Demand"))
    fig.update_layout(title="Projected Energy Demand Over Time", xaxis_title="Year", yaxis_title="Energy Demand (kWh)", template=TEMPLATE_STYLE)
    return fig

# Callback to update storage options results
@app.callback(
    Output("detail-storage-results", "children"),
    [Input("detail-storage-type", "value")]
)
def update_storage_results(selected_storage):
    if not selected_storage:
        return "No storage option selected."
    return html.Ul([html.Li(f"Option: {option}") for option in selected_storage])

# Callback to update charts in the Multi-Chart Dashboard tab
@app.callback(
    Output("dashboard-charts-container", "children"),
    Input("dashboard-chart-selector", "value")
)
def update_dashboard_charts(selected_charts):
    # If no charts are selected, display a message.
    if not selected_charts:
        return html.Div("No charts selected.", style={"text-align": "center", "padding": "20px"})
    charts = []
    if "dwelling" in selected_charts:
        charts.append(
            card_component("Dwelling at Berth - Biofuel Blend Minimum",
                           dcc.Graph(figure=dwelling_at_berth_pie_figure(), className="chart-container"))
        )
    if "npv" in selected_charts:
        # For the dashboard, the NPV metric can be shown using the dynamic metric chart (with NPV selected)
        # Here we simulate it by loading the NPV values for all scenarios.
        years_data, scenarios = load_totex_scenarios()
        fig = go.Figure()
        for label, sc in scenarios.items():
            if "NPV" in sc and len(sc["NPV"]) == len(years_data):
                fig.add_trace(go.Scatter(
                    x=years_data,
                    y=sc["NPV"],
                    mode="lines",
                    name=label
                ))
        fig = set_figure_layout(fig, "NPV Comparison", "Year", "NPV (£)")
        fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5))
        charts.append(
            card_component("NPV Comparison",
                           dcc.Graph(figure=fig, className="chart-container"))
        )
    if "cashflow" in selected_charts:
        charts.append(
            card_component("Cashflow Analysis",
                           dcc.Graph(figure=cashflow_figure(), className="chart-container"))
        )
    if "totex" in selected_charts:
        charts.append(
            card_component("TOTEX Comparison",
                           dcc.Graph(figure=totex_figure(), className="chart-container"))
        )
    return charts

if __name__ == '__main__':
    app.run_server(debug=True)
