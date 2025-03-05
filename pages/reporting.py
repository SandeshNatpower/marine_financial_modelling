from dash import html, dcc
import dash_bootstrap_components as dbc

PRIMARY_COLOR = "#0A4B8C"  # Deep navy
TEXT_COLOR = "#212121"

def layout():
    return dbc.Container([
        html.H2("Decarbonization Reporting", className="mb-4", style={"color": PRIMARY_COLOR}),
        
        # Descriptive Introduction
        html.Div([
            html.P(
                "Our reporting tool provides comprehensive insights into vessel decarbonization, "
                "focusing on three critical areas: operational performance, regulatory compliance, "
                "and carbon reduction strategies.",
                className="lead text-muted"
            )
        ], className="mb-4"),
        
        # Report Purpose and Structure Card
        dbc.Card([
            dbc.CardHeader(
                html.H4("Report Overview", style={"color": "white"}),
                style={"backgroundColor": PRIMARY_COLOR}
            ),
            dbc.CardBody([
                html.H5("Key Report Sections"),
                html.Ul([
                    html.Li("Operational Profile Analysis"),
                    html.Li("Regulatory Compliance Assessment"),
                    html.Li("Carbon Reduction Strategies"),
                    html.Li("Detailed Technical Appendices"),
                    html.Li("Comparative Case Studies")
                ], className="list-unstyled")
            ])
        ], className="mb-4"),
        
        # Report Configuration Section
        dbc.Card([
            dbc.CardHeader(
                html.H4("Configure Report", style={"color": "white"}),
                style={"backgroundColor": PRIMARY_COLOR}
            ),
            dbc.CardBody([
                dbc.Form([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Report Type", className="mb-2"),
                            dcc.Dropdown(
                                id="report-type",
                                options=[
                                    {"label": "CII Compliance", "value": "cii"},
                                    {"label": "EEXI Assessment", "value": "eexi"},
                                    {"label": "Comprehensive Audit", "value": "audit"}
                                ],
                                value="cii",
                                clearable=False
                            )
                        ], md=6, xs=12),
                        dbc.Col([
                            dbc.Label("Reporting Period", className="mb-2"),
                            dcc.DatePickerRange(
                                id="report-dates",
                                start_date_placeholder_text="Start Date",
                                end_date_placeholder_text="End Date",
                                calendar_orientation="vertical"
                            )
                        ], md=6, xs=12)
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Analysis Filters", className="mb-2"),
                            dbc.Input(
                                id="report-filters",
                                type="text",
                                placeholder="Optional: Add specific analysis filters"
                            )
                        ], md=6, xs=12),
                        dbc.Col([
                            dbc.Label("Currency", className="mb-2"),
                            dcc.Dropdown(
                                id="report-currency",
                                options=[
                                    {"label": "Euro (€)", "value": "EUR"},
                                    {"label": "US Dollar ($)", "value": "USD"},
                                    {"label": "British Pound (£)", "value": "GBP"}
                                ],
                                value="EUR",
                                clearable=False
                            )
                        ], md=6, xs=12)
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Button(
                                "Generate Report", 
                                id="generate-report-button",
                                color="primary", 
                                className="w-100"
                            )
                        ], md=12)
                    ])
                ])
            ])
        ], className="mb-4"),
        
        # Report Preview Section
        dbc.Card([
            dbc.CardHeader(
                html.H4("Report Preview", style={"color": "white"}),
                style={"backgroundColor": PRIMARY_COLOR}
            ),
            dbc.CardBody([
                html.Div(
                    id="report-preview",
                    children=[
                        html.P(
                            "Your report preview will be displayed here. "
                            "Click 'Generate Report' to create a detailed analysis.",
                            className="text-muted"
                        )
                    ]
                )
            ])
        ], className="mb-4"),
        
        # Hidden storage for report data
        dcc.Store(id="report-data-store")
    ], fluid=True, className="p-4")