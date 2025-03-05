from dash import html, dcc
import dash_bootstrap_components as dbc

PRIMARY_COLOR = "#0A4B8C"  # Updated deep navy
TEXT_COLOR = "#212121"

def layout():
    return dbc.Container([
        html.H2("Reporting", className="mb-4", style={"color": PRIMARY_COLOR}),
        html.P(
            "The report can be viewed as an instance of the tool, a nice end-result for users which serves "
            "as future reference. There are three matters that matter most for shipowners – operations, rules "
            "and regulations, and reduction measures. Operational results provide an overview of the current "
            "vessel. Rules and regulations provide an indication of how much the vessel is to decarbonize, "
            "and thus a target for the shipowner to work with."
        ),
        html.P(
            "The reduction measures provide insights into the costs and workings of the prevent and change "
            "measure, as well as some references to other examples and potential suppliers. A single-page "
            "summary highlights all the main results, which includes hyperlinks that direct you quickly to "
            "where you need to be. Everything else is to be put in the appendix. Example reports will be "
            "provided to you."
        ),
        
        # Executive Summary Card
        dbc.Card([
            dbc.CardHeader(
                html.H4("Decarbonizer Premium Report", style={"color": "white"}),
                style={"backgroundColor": PRIMARY_COLOR}
            ),
            dbc.CardBody([
                html.P("Made especially for Client", style={"fontWeight": "bold"}),
                html.H5("EXECUTIVE SUMMARY TABLE OF CONTENTS"),
                html.Ul([
                    html.Li("1.0 OPERATIONAL PROFILE BOATY MCBOATFACE"),
                    html.Li("2.0 KEY UPCOMING RULES AND REGULATIONS"),
                    html.Li("3.0 CARBON REDUCTION MEASURES & COSTS"),
                    html.Li("4.0 APPENDIX I – ASSUMPTIONS AND CALCULATIONS"),
                    html.Li("5.0 APPENDIX II – CASE STUDIES SIMILAR TO BOATY MCBOATFACE"),
                ])
            ])
        ], className="mb-4", style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}),
        
        # Report Generation Section
        dbc.Card([
            dbc.CardHeader(
                html.H4("Generate Compliance Reports", style={"color": "white"}),
                style={"backgroundColor": PRIMARY_COLOR}
            ),
            dbc.CardBody([
                dbc.Form([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label(
                                [
                                    "Report Type",
                                    html.I(className="fas fa-question-circle ms-1", id="report-type-help-icon", style={"color": PRIMARY_COLOR, "cursor": "pointer"})
                                ],
                                style={"color": TEXT_COLOR}
                            ),
                            dcc.Dropdown(
                                id="report-type",
                                options=[
                                    {"label": "CII Compliance", "value": "cii"},
                                    {"label": "EEXI Report", "value": "eexi"},
                                    {"label": "Full Audit", "value": "audit"}
                                ],
                                value="cii",
                                clearable=False
                            )
                        ], md=6, xs=12),
                        dbc.Col([
                            dbc.Label("Time Period", style={"color": TEXT_COLOR}),
                            dcc.DatePickerRange(
                                id="report-dates",
                                start_date="2024-01-01",
                                end_date="2024-12-31"
                            )
                        ], md=6, xs=12)
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Additional Filters", style={"color": TEXT_COLOR}),
                            dbc.Input(
                                id="report-filters",
                                type="text",
                                placeholder="Enter filters (optional)"
                            )
                        ], md=6, xs=12),
                        dbc.Col([
                            dbc.Label("Select Currency", style={"color": TEXT_COLOR}),
                            dcc.Dropdown(
                                id="report-currency",
                                options=[
                                    {"label": "EUR (€)", "value": "EUR"},
                                    {"label": "USD ($)", "value": "USD"},
                                    {"label": "GBP (£)", "value": "GBP"}
                                ],
                                value="EUR",
                                clearable=False
                            )
                        ], md=6, xs=12)
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Generate PDF Report", id="generate-report-button",
                                       color="primary", className="me-2")
                        ], xs=12),
                    ]),
                    
                    html.Div(id="report-status", className="mt-3", style={"color": TEXT_COLOR}),
                ])
            ])
        ], className="mb-4", style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}),
        
        # Generated Report Section
        dbc.Card([
            dbc.CardHeader(
                html.H4("Generated Report", style={"color": "white"}),
                style={"backgroundColor": PRIMARY_COLOR}
            ),
            dbc.CardBody([
                html.Div(
                    id="generated-report-content",
                    children=[html.P("Your report will appear here once generated.")]
                ),
                dcc.Download(id="download-report")
            ])
        ], className="mb-4", style={"boxShadow": "0 2px 10px rgba(0,0,0,0.1)", "borderRadius": "8px"}),
        
        # Hidden store for detailed report content
        dcc.Store(id="detailed-report-store"),
        
        # Tooltip for Report Type
        dbc.Tooltip(
            "Choose the type of report to generate: CII Compliance, EEXI Report, or a Full Audit.",
            target="report-type-help-icon",
            placement="right"
        )
    ], fluid=True, className="py-4")