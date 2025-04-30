# pages/reporting.py

import io
import pandas as pd
from datetime import datetime
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dcc import send_data_frame

# Currency symbols for display
CURRENCY_SYMBOLS = {'EUR': '€', 'USD': '$', 'GBP': '£'}

def layout():
    return dbc.Container([
        dcc.Store(id='report-config-store'),
        dcc.Download(id='download-report'),

        html.H2("Generate Compliance Report", className="mb-4 text-primary"),

        # ─── Configuration Card ────────────────────────────────────────────────
        dbc.Card([
            dbc.CardHeader("Report Configuration", className="bg-primary text-white"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Report Scope"),
                        dcc.Dropdown(
                            id='report-scope',
                            options=[
                                {'label': 'Technical Summary', 'value': 'technical'},
                                {'label': 'Financial Analysis', 'value': 'financial'},
                                {'label': 'Full Compliance Report', 'value': 'full'}
                            ],
                            value='technical'
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Scenarios"),
                        dcc.Dropdown(
                            id='report-scenarios',
                            options=[],  # to be populated from callbacks
                            multi=True
                        )
                    ], md=8)
                ], className="mb-3"),

                dbc.Row([
                    dbc.Col([
                        dbc.Label("Date Range"),
                        dcc.DatePickerRange(
                            id='report-dates',
                            start_date=datetime.now().date(),
                            end_date=datetime.now().date()
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Label("Currency"),
                        dcc.Dropdown(
                            id='report-currency',
                            options=[
                                {'label': 'Euro (€)', 'value': 'EUR'},
                                {'label': 'US Dollar ($)', 'value': 'USD'},
                                {'label': 'British Pound (£)', 'value': 'GBP'}
                            ],
                            value='EUR'
                        )
                    ], md=4),
                    dbc.Col([
                        dbc.Button("Generate Preview", id='generate-report-btn',
                                   color="primary", className="w-100")
                    ], md=2),
                    dbc.Col([
                        dbc.Button("Download CSV", id='download-report-btn',
                                   color="success", className="w-100")
                    ], md=2),
                ]),
            ])
        ], className="mb-4"),

        # ─── Preview Card ──────────────────────────────────────────────────────
        dbc.Card([
            dbc.CardHeader("Report Preview"),
            dbc.CardBody(html.Div(id='report-preview', className="report-preview"))
        ])
    ], fluid=True)
