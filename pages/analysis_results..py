# pages/analysis_results.py
from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
from components.charts import create_emissions_barchart, create_power_profile_chart
from calculations.economics import calculate_baseline_emissions

def layout():
    return html.Div([
        html.H2("Analysis Results", className='page-title'),
        
        # First row with emissions and cost analysis
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Emissions Reduction Potential"),
                        dcc.Graph(id='emissions-chart', figure={})
                    ])
                ])
            ], md=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Cost-Benefit Analysis"),
                        dcc.Graph(id='cost-chart', figure={})
                    ])
                ])
            ], md=6)
        ]),
        
        # Second row with power profile and storage options
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Power Demand Analysis"),
                        dcc.Graph(id='main-power-profile-chart', figure={}),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Peak Power Demand (kW)"),
                                dbc.Input(id='main-peak-power', type='number', value=25000)
                            ], md=4),
                            dbc.Col([
                                dbc.Label("Base Load (%)"),
                                dcc.Slider(id='main-base-load', min=20, max=80, value=40)
                            ], md=8)
                        ])
                    ])
                ])
            ], md=8),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Energy Storage Options"),
                        dcc.Dropdown(
                            id='storage-type',
                            options=[
                                {'label': 'Lithium-Ion Battery', 'value': 'li-ion'},
                                {'label': 'Fuel Cells', 'value': 'fuel-cell'},
                                {'label': 'Supercapacitors', 'value': 'capacitor'}
                            ],
                            multi=True
                        ),
                        html.Div(id='storage-results', className='mt-3')
                    ])
                ])
            ], md=4)
        ]),
        
        # Compliance status row
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4("Compliance Status"),
                        html.Div(id='main-compliance-badges', className='badge-container')
                    ])
                ])
            ])
        ], className='mt-4')
    ])

@callback(
    [Output('emissions-chart', 'figure'),
     Output('cost-chart', 'figure')],
    Input('emissions-data-store', 'data')
)
def update_emissions_chart(data):
    if not data:
        return {}, {}
    
    co2_ttw = data.get('co2_emission_ttw', [{}])[0]
    nox_ttw = data.get('nox_emission_ttw', [{}])[0]
    sox_ttw = data.get('sox_emission_ttw', [{}])[0]
    
    baseline = [
        co2_ttw.get('prop_co2_emission_ttw', 0),
        nox_ttw.get('prop_nox_emission_ttw', 0),
        sox_ttw.get('prop_sox_emission_ttw', 0)
    ]
    optimized = [val * 0.8 for val in baseline]
    
    emissions_fig = create_emissions_barchart(baseline, optimized)
    cost_fig = {
        'data': [{
            'values': [45, 30, 25],
            'labels': ['CAPEX', 'OPEX', 'Savings'],
            'type': 'pie'
        }],
        'layout': {'title': 'Cost Breakdown', 'template': 'plotly_white'}
    }
    
    return emissions_fig, cost_fig

@callback(
    [Output('main-power-profile-chart', 'figure'),
     Output('main-compliance-badges', 'children')],
    [Input('main-peak-power', 'value'),
     Input('main-base-load', 'value'),
     Input('vessel-store', 'data')]
)
def update_main_power_profile_and_compliance(peak_power, base_load, data):
    if not data:
        data = {}
    
    # Update Power Profile Chart
    power_profile_fig = create_power_profile_chart(peak_power, base_load)
    
    # Update Compliance Badges
    power = data.get('main_power', 25000)
    operating_hours = data.get('operating_hours', 5000)
    load_factor = data.get('load_factor', 0.8)
    fuel_type = data.get('fuel_type', 'mdo').lower()
    
    try:
        baseline_emissions = calculate_baseline_emissions(power, fuel_type, operating_hours, load_factor)
    except Exception:
        baseline_emissions = {'cii_rating': 'N/A', 'eexi_compliance': False}
    
    cii_rating = baseline_emissions.get('cii_rating', 'N/A')
    eexi_compliance = baseline_emissions.get('eexi_compliance', False)
    
    rating_color = {
        'A': 'success',
        'B': 'success',
        'C': 'warning',
        'D': 'warning',
        'E': 'danger',
        'N/A': 'secondary'
    }.get(cii_rating, 'secondary')
    
    compliance_color = "success" if eexi_compliance else "danger"
    
    cii_badge = dbc.Badge(f"CII Rating: {cii_rating}", color=rating_color, className="me-1")
    eexi_badge = dbc.Badge(
        "EEXI Compliant" if eexi_compliance else "EEXI Non-Compliant",
        color=compliance_color,
        className="me-1"
    )
    
    compliance_badges = dbc.Row([dbc.Col(cii_badge), dbc.Col(eexi_badge)])
    
    return power_profile_fig, compliance_badges
